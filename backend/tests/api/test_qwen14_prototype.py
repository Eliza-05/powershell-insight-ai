"""Prototype integration, entirely mocked; never contacts a real model or ledger."""
from copy import deepcopy
import json
import os
from pathlib import Path
import socket

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.api.application import create_app
from app.services.llm.qwen14 import MODEL, Qwen14Transport
from app.services.llm import qwen14_prototype as q
from app.services.pipelines.context import canonical, sha
from app.services.pipelines.resources import InferenceGate, OperationalFailure
from app.services.pipelines.service import AnalysisService

GIB = 1024 ** 3
ROOT = Path(__file__).resolve().parents[3]


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    monkeypatch.delenv("PSI_PIPELINE_SETTINGS", raising=False)
    monkeypatch.setattr(socket, "create_connection", lambda *a, **k: pytest.fail("Real network forbidden"))


class Server:
    def __init__(self):
        self.calls = []
        self.residents = []
        self.error = None
        self.wrong_evidence = False

    def json(self, endpoint, payload=None):
        self.calls.append((endpoint, deepcopy(payload)))
        if self.error:
            raise OperationalFailure(self.error, "SIMULATED " + self.error)
        if endpoint == "version": return {"version": "0.40.13"}
        if endpoint == "tags": return {"models": [{"name": MODEL, "digest": q.DIGEST}]}
        if endpoint == "ps": return {"models": deepcopy(self.residents)}
        if endpoint == "show": return {"capabilities": ["completion"]}
        assert endpoint == "chat"
        assert payload["model"] == MODEL
        assert "think" not in payload
        report = {"behaviors": [], "obfuscation_techniques": [], "recovered_content": [],
            "risk_label": "unknown", "risk_rationale": "SIMULATED static uncertainty",
            "uncertainty": {"level": "high", "notes": "SIMULATED", "uninterpretable_fragments": []},
            "prompt_injection": {"detected": False, "snippets": [], "notes": "SIMULATED"},
            "limitations": ["SIMULATED; no empirical inference"]}
        if self.wrong_evidence:
            report["behaviors"] = [{"behavior_id": "B05", "confidence": "low", "explanation": "SIMULATED",
                "evidence": [{"source_id": "T9999", "snippet": "fabricated evidence"}]}]
        self.residents = [{"digest": q.DIGEST, "context_length": 8192, "size_vram": 0}]
        return {"model": MODEL, "done": True, "done_reason": "stop", "message": {"content": json.dumps(report)},
            "prompt_eval_count": 1200, "eval_count": 200}

    def cancel(self): pass


def setup(tmp_path, free=20 * GIB):
    server = Server()
    settings = q.load_settings()
    sampler = lambda: {"available_bytes": free, "commit_available_bytes": 25 * GIB,
                       "commit_limit_bytes": 50 * GIB, "physical_total_bytes": 32 * GIB}
    adapter = q.PrototypeAdapter(settings, transport_factory=lambda: server, sampler=sampler,
        gate_factory=lambda: InferenceGate(tmp_path / "prototype.lock"))
    service = AnalysisService(settings, adapter=adapter)
    app = create_app(service=service, frontend_dir=tmp_path / "no-dist")
    return TestClient(app, base_url="http://127.0.0.1"), server


def test_default_app_adopts_qwen14_without_network_or_generation():
    app = create_app()
    with TestClient(app, base_url="http://127.0.0.1") as client:
        caps = client.get("/api/capabilities").json()
        meta = client.get("/api/metadata").json()
        assert client.get("/api/health").status_code == 200
    assert caps["model"] == MODEL and caps["expected_digest"] == q.DIGEST
    assert caps["fallback_enabled"] is False and caps["generation_on_startup"] is False
    assert caps["think_parameter_sent"] is False
    assert meta["model_selection"] == "adopted_for_local_exploration"
    assert meta["scientific_selection_passed"] is False and not meta["phase4_started"]
    assert meta["hypotheses"] == {"H1": "not_established", "H2": "not_established"}
    assert meta["human_adjudications_pending"] == 8


def test_profile_matches_diagnostic_parameters_without_reusing_ledger():
    frozen = json.loads((ROOT / "artifacts/qwen25_coder14b/plan/configuration.json").read_text(encoding="utf-8"))
    settings = q.load_settings()
    assert settings.model_dump(mode="json") == frozen["settings"]


@pytest.mark.parametrize("bad", [{"model": "qwen3.5:4b-q4_K_M"}, {"model": "gemma4:12b"},
                                  {"model": "gemini"}, {"expected_digest": "0" * 64}, {"port": 1234}])
def test_stale_or_foreign_settings_fail_without_fallback(bad):
    with pytest.raises(ValidationError): q.PrototypeSettings.model_validate(bad)


def test_environment_config_does_not_silently_fall_back(tmp_path, monkeypatch):
    path = tmp_path / "settings.json"
    path.write_text('{"model":"qwen3.5:4b-q4_K_M"}', encoding="utf-8")
    monkeypatch.setenv("PSI_PIPELINE_SETTINGS", str(path))
    with pytest.raises(ValidationError): create_app()


def test_A_is_independent_even_when_provider_is_offline(tmp_path):
    client, server = setup(tmp_path)
    server.error = "ollama_unavailable"
    data = client.post("/api/analyze/A", json={"script": "Get-Process"}).json()
    assert data["status"] == "completed" and data["deterministic"]["behaviors"] == ["B05"]
    assert not server.calls and data["llm"] is None


def test_metadata_and_status_never_generate(tmp_path):
    client, server = setup(tmp_path)
    for path in ("health", "metadata", "capabilities", "provider/status", "ollama/status"):
        assert client.get("/api/" + path).status_code == 200
    assert server.calls and all(e != "chat" for e, _ in server.calls)


def test_B_C_use_same_profile_and_never_receive_references_or_previous_answers(tmp_path):
    client, server = setup(tmp_path)
    script = (ROOT / "artifacts/qwen25_coder14b/plan/scripts/Q14-02.ps1.txt").read_text(encoding="utf-8")
    data = client.post("/api/compare", json={"script": script}).json()
    assert [r["configuration"] for r in data["results"]] == ["A", "B", "C"]
    b, c = [p for e, p in server.calls if e == "chat"]
    assert {k: v for k, v in b.items() if k != "messages"} == {k: v for k, v in c.items() if k != "messages"}
    assert b["messages"][0] == c["messages"][0]
    assert len(b["messages"]) == len(c["messages"]) == 2
    assert set(json.loads(b["messages"][1]["content"])) == {"original"}
    assert set(json.loads(c["messages"][1]["content"])) == {"original", "deterministic_recovery"}
    assert all(r["configuration"] == "A" or r["llm"] is not None for r in data["results"])


@pytest.mark.parametrize("condition", ["memory", "ollama_unavailable"])
def test_unavailable_states_dispatch_no_chat_and_do_not_fallback(tmp_path, condition):
    client, server = setup(tmp_path, free=GIB if condition == "memory" else 20 * GIB)
    if condition != "memory": server.error = condition
    status = client.get("/api/ollama/status").json()
    assert not status.get("ready_for_inference", False)
    data = client.post("/api/analyze/B", json={"script": "Write-Output 42"}).json()
    assert data["status"] == "unavailable" and data["llm"] is None and not data["evidence"]
    assert data["errors"][0]["code"] == ("insufficient_memory" if condition == "memory" else condition)
    assert all(e != "chat" for e, _ in server.calls)


def test_rejected_provenance_never_publishes_findings(tmp_path):
    client, server = setup(tmp_path); server.wrong_evidence = True
    data = client.post("/api/analyze/C", json={"script": "Get-Process"}).json()
    assert data["status"] == "error" and data["llm"] is None and data["evidence"] == []
    assert data["risk_label"] == "unknown" and data["errors"][0]["code"] == "invalid_response"
    assert "fabricated evidence" in data["operational"]["response"]["message"]["content"]
    assert len([e for e, _ in server.calls if e == "chat"]) == 1


def test_interactive_transport_timeout_and_owned_dispatch(monkeypatch, tmp_path):
    observed = []
    monkeypatch.setattr(Qwen14Transport, "json", lambda self, endpoint, payload=None: observed.append((endpoint, self.timeout)))
    transport = q.PrototypeTransport(180)
    transport.json("version"); transport.json("chat", {"model": MODEL}); transport.json("ps")
    assert observed == [("version", 3), ("chat", 180), ("ps", 3)]
    marker = tmp_path / "owned.json"
    monkeypatch.setattr(q, "InferenceGate", lambda: type("Gate", (), {"marker": marker})())
    payload = {"model": MODEL}
    with pytest.raises(OperationalFailure): q.authorize_interactive_dispatch(payload)
    marker.write_text(json.dumps({"pid": os.getpid(), "state": "dispatch_intent", "request_sha256": sha(canonical(payload))}), encoding="utf-8")
    q.authorize_interactive_dispatch(payload)
    with pytest.raises(OperationalFailure): q.authorize_interactive_dispatch({"model": "other"})

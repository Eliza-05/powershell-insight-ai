"""Development authorization and split isolation; no real inference."""
import json

import pytest

from experiments.model_readiness.diagnostics import build_plan, reserve, spent_ids
from app.services.pipelines.resources import OperationalFailure
from app.services.pipelines.resources import InferenceGate
from app.services.pipelines.config import DIGEST, GIB, MODEL


def test_plan_24_new_development_calls_and_no_reference_leakage():
    plan = build_plan()
    assert len(plan["calls"]) == plan["budget_cap"] == 24
    assert len({c["id"] for c in plan["calls"]}) == 24
    for call in plan["calls"]:
        payload = call["payload"]
        assert call["split"] == "new_synthetic_development"
        assert "reference_labels_reviewer_only" not in json.dumps(payload)
        assert "deterministic" not in payload.get("options", {})
        assert payload["truncate"] is False and payload["shift"] is False
        assert payload["options"]["num_gpu"] == 0
        budget = sum(len(m["content"].encode()) for m in payload["messages"]) + 512
        assert budget + payload["options"]["num_predict"] <= 8192, call["id"]
    c = plan["calls"][0]
    data = json.loads(c["payload"]["messages"][-1]["content"])
    assert data["deterministic_recovery"]["verified_texts"]
    assert "behaviors" not in data and "risk_label" not in data


def test_diagnostic_intent_is_spent_across_restart_and_never_retried(tmp_path):
    call = {"id": "01-test", "request_sha256": "a" * 64}
    reserve(call, "b" * 64, tmp_path)
    assert spent_ids(tmp_path) == {"01-test"}
    with pytest.raises(OperationalFailure, match="Dispatched"):
        reserve(call, "b" * 64, tmp_path)


def test_diagnostic_budget_cannot_reset_by_new_call_id(tmp_path):
    for index in range(24):
        reserve({"id": str(index), "request_sha256": "a" * 64}, "b" * 64, tmp_path)
    with pytest.raises(OperationalFailure, match="exhausted"):
        reserve({"id": "25", "request_sha256": "a" * 64}, "b" * 64, tmp_path)


@pytest.mark.parametrize("mode", ["memory", "interrupted", "success", "postflight"])
def test_diagnostic_runner_faults_budget_raw_and_own_unload(tmp_path, monkeypatch, mode):
    from experiments.model_readiness import diagnostics as module
    plan = build_plan()
    plan["calls"] = [plan["calls"][2]]  # fresh synthetic Write-Output, no reserved source
    (tmp_path / "plan.json").write_text(json.dumps(plan))
    calls = []
    loaded = []
    postflight_failed = []
    class Client:
        last_response = None
        def __init__(self, **kwargs):
            pass
        def cancel(self):
            calls.append("cancel")
        def json(self, endpoint, payload=None):
            calls.append((endpoint, payload))
            if endpoint == "tags":
                if mode == "postflight" and loaded and not postflight_failed:
                    postflight_failed.append(True)
                    self.last_response = {"raw_utf8": "wrong state endpoint"}
                    raise OperationalFailure("ollama_unavailable", "synthetic postflight failure")
                return {"models": [{"name": MODEL, "digest": DIGEST}]}
            if endpoint == "ps":
                return {"models": list(loaded)}
            if endpoint == "version":
                return {"version": "synthetic"}
            if endpoint == "show":
                return {"thinking": {"values": [False, True]}}
            self.last_response = {"raw_utf8": "synthetic raw prefix"}
            if payload.get("keep_alive") == 0:
                loaded.clear()
                return {"done": True, "done_reason": "unload"}
            if mode == "interrupted":
                raise OperationalFailure("timeout", "synthetic interruption")
            loaded.append({"digest": DIGEST, "context_length": 8192, "size_vram": 0})
            report = {"obfuscation_techniques": [], "recovered_content": [], "behaviors": [],
                "risk_label": "unknown", "risk_rationale": "Static fixture.",
                "uncertainty": {"level": "medium", "uninterpretable_fragments": [], "notes": "Static."},
                "prompt_injection": {"detected": False, "snippets": [], "notes": "None."}, "limitations": []}
            return {"model": MODEL, "done": True, "done_reason": "stop", "prompt_eval_count": 100,
                    "eval_count": 50, "message": {"content": json.dumps(report)}}
    monkeypatch.setattr(module, "OUT", tmp_path)
    monkeypatch.setattr(module, "prepare", lambda: plan)
    monkeypatch.setattr(module, "spent_ids", lambda out=tmp_path: spent_ids(out))
    monkeypatch.setattr(module, "reserve", lambda call, plan_hash: reserve(call, plan_hash, tmp_path))
    monkeypatch.setattr(module, "InferenceGate", lambda: InferenceGate(tmp_path / "gate.lock"))
    monkeypatch.setattr(module, "LocalTransport", Client)
    monkeypatch.setattr(module, "snapshot", lambda: {"available_bytes": (4 if mode == "memory" else 20) * GIB,
                                                    "commit_available_bytes": 20 * GIB})
    result = module.run()
    assert result["total_budget_consumed"] == (0 if mode == "memory" else 1)
    chat = [p for e, p in calls if e == "chat"]
    assert len(chat) == {"memory": 0, "interrupted": 1, "success": 2, "postflight": 2}[mode]
    if mode == "interrupted":
        assert (tmp_path / "gate.blocked").exists()
        output = json.loads(next((tmp_path / "results").glob("*.json")).read_text())
        assert output["transport_response"]["raw_utf8"] == "synthetic raw prefix"
        with pytest.raises(OperationalFailure, match="Previous interrupted"):
            module.run()
    if mode == "postflight":
        output = json.loads(next((tmp_path / "results").glob("*.json")).read_text())
        assert output["transport_response"]["raw_utf8"] == "synthetic raw prefix"
        assert output["error"]["code"] == "ollama_unavailable"
    if mode in {"success", "postflight"}:
        assert chat[-1]["messages"] == [] and chat[-1]["keep_alive"] == 0
        assert list((tmp_path / "controls").glob("*.json"))
        assert not (tmp_path / "gate.blocked").exists()

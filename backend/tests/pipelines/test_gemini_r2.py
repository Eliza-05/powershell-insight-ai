"""R2 control tests: mocked official SDK, fixed cases, no real API requests."""
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import json

import httpx
import pytest

pytest.importorskip("google.genai")
from experiments import gemini_r2 as r2
from app.services.llm.gemini import FreeTierConfirmation, GeminiAdapter, GeminiSettings
from app.services.llm.gemini_budget import MetadataRetryAuthorization, RequestBudget
from tests.pipelines.test_pipelines import report


@pytest.fixture
def rig(tmp_path, monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "synthetic-r2-test-credential")
    output, initial = tmp_path / "output", tmp_path / "initial"
    output.mkdir()
    initial.mkdir()
    monkeypatch.setattr(r2, "ROOT", tmp_path)
    monkeypatch.setattr(r2, "OUTPUT", output)
    monkeypatch.setattr(r2, "INITIAL", initial)
    plan = r2.prospective_plan()
    path = tmp_path / "plan.json"
    path.write_text(json.dumps(plan), encoding="utf-8")
    monkeypatch.setattr(r2, "PLAN", path)
    budget = RequestBudget(initial / "requests.jsonl")
    budget.reserve("models.list", "metadata")
    budget.reserve("models.list", "metadata", metadata_retry=MetadataRetryAuthorization(True,
        hashlib.sha256(budget.path.read_bytes()).hexdigest(), datetime.now(timezone.utc).isoformat(), "explicit_owner_authorization"))
    quota = FreeTierConfirmation("gemini-3.8-flash", datetime.now(timezone.utc).isoformat(),
                                "owner_ai_studio_confirmation", rpm=5, tpm=250000, rpd=20, remaining_rpd=20)
    quota_path = tmp_path / "quota.json"
    quota_path.write_text(json.dumps(asdict(quota)), encoding="utf-8")
    contexts = [{"context_sha256": r2.context_for(c).context_sha256,
                 "total_token_reserve": r2.input_bound(r2.context_for(c)) + 4096} for c in plan["cases"]]
    binding = {"plan_sha256": r2.digest(path), "runtime_hashes": {}, "quota_sha256": r2.digest(quota_path),
               "initial_ledger_sha256": r2.digest(budget.path), "contexts": contexts}
    (output / "binding.json").write_text(json.dumps(binding))
    (output / "generation_authorization.json").write_text(json.dumps({"authorized": True,
        "binding_sha256": r2.digest(output / "binding.json"), "quota_file": "quota.json"}))
    monkeypatch.setattr(r2, "wait_for_quota", lambda *a: None)
    return output, budget, plan, monkeypatch


def sdk_response(value=None, **changes):
    body = {"candidates": [{"content": {"role": "model", "parts": [{"text": json.dumps(report() if value is None else value)}]},
                            "finishReason": "STOP"}], "modelVersion": "gemini-3.8-flash", "responseId": "synthetic-response",
            "usageMetadata": {"promptTokenCount": 100, "candidatesTokenCount": 100, "totalTokenCount": 200}}
    body.update(changes)
    return httpx.Response(200, json=body)


def install_fake(rig, handler):
    _, _, _, monkeypatch = rig
    monkeypatch.setattr(r2, "GeminiAdapter", lambda **kw: GeminiAdapter(**kw, inner_transport=httpx.MockTransport(handler)))


def test_fixed_ten_sequence_no_metadata_no_detector_or_reference_leak_and_no_replay(rig):
    output, budget, plan, monkeypatch = rig
    calls = []
    def handler(request):
        assert request.method == "POST" and request.url.path.endswith("/gemini-3.8-flash:generateContent")
        data = json.loads(request.content)
        calls.append(data)
        context = json.loads(data["contents"][0]["parts"][0]["text"])
        assert set(context) <= {"original", "deterministic_recovery"}
        assert context["original"] == plan["cases"][len(calls)-1]["script"]
        assert "synthetic-r2-test-credential" not in request.content.decode()
        return sdk_response()
    monkeypatch.setattr("app.services.behavior_detection.engine.analyze_behaviors", lambda *a, **k: pytest.fail("detector forbidden"))
    install_fake(rig, handler)
    r2.run()
    assert len(calls) == 10 and len(budget.entries()) == 12
    for first, second in [(calls[0], calls[1]), (calls[2], calls[3])]:
        assert {k:v for k,v in first.items() if k != "contents"} == {k:v for k,v in second.items() if k != "contents"}
    summary = r2.load(output / "summary.json")
    assert summary["generations_dispatched"] == 10 and summary["stop_reason"] is None
    assert all(r["http_status"] == 200 for r in summary["results"])
    with pytest.raises(Exception):
        r2.run()
    assert len(calls) == 10


@pytest.mark.parametrize("failure", ["quota", "authentication", "transport", "safety"])
def test_operational_or_safety_failure_stops_and_keeps_evidence(rig, failure):
    output, budget, _, _ = rig
    calls = []
    def handler(request):
        calls.append(1)
        if failure == "quota":
            return httpx.Response(429, json={"error": {"code": 429, "message": "sensitive error context"}})
        if failure == "authentication":
            return httpx.Response(403, json={"error": {"code": 403, "message": "sensitive error context"}})
        if failure == "transport":
            raise httpx.ConnectError("sensitive error context", request=request)
        return sdk_response(candidates=[], promptFeedback={"blockReason": "SAFETY"})
    install_fake(rig, handler)
    r2.run()
    assert len(calls) == 1 and len(budget.entries()) == 3
    summary = r2.load(output / "summary.json")
    assert summary["stop_reason"] and len(summary["not_executed"]) == 9
    raw = (output / "G03_B.json").read_text()
    assert "sensitive error context" not in raw
    if failure == "safety":
        assert "raw_response_utf8" in raw


def test_schema_rejection_is_retained_without_changing_or_repeating_case(rig):
    output, budget, _, _ = rig
    calls = []
    def handler(request):
        calls.append(1)
        return sdk_response(value={"bad_contract": True}) if len(calls) == 1 else sdk_response()
    install_fake(rig, handler)
    r2.run()
    summary = r2.load(output / "summary.json")
    first = summary["results"][0]
    assert first["valid_json"] and not first["schema_valid"] and not first["application_accepted"]
    assert "raw_response_utf8" in (output / "G03_B.json").read_text()
    assert len(calls) == 10 and len(budget.entries()) == 12


def test_quota_wait_is_sequential_bounded_and_respects_window():
    current = [0.0]
    sleeps = []
    def sleep(delay):
        sleeps.append(delay)
        current[0] += delay
    quota = FreeTierConfirmation("gemini-3.8-flash", datetime.now(timezone.utc).isoformat(),
                                "owner_ai_studio_confirmation", rpm=5, tpm=250000, rpd=20, remaining_rpd=20)
    history = [(0.0, 240000)]
    r2.wait_for_quota(history, 20000, quota, now=lambda:current[0], sleep=sleep)
    assert current[0] >= 61 and max(sleeps) <= 30

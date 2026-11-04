"""Real official SDK + mock HTTP: secrets, physical budget, A/B/C, no external calls."""
from dataclasses import replace
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path

import httpx
import pytest

pytest.importorskip("google.genai", reason="Optional Gemini SDK")
pytest.importorskip("dotenv", reason="Optional Gemini backend loader")

from app.services.llm.gemini import FreeTierConfirmation, GeminiAdapter, GeminiSettings
from app.services.llm.gemini_budget import RequestBudget
from app.services.llm.gemini_credentials import read_api_key
from app.services.pipelines.context import build_context, sha
from app.services.pipelines.resources import OperationalFailure
from app.services.pipelines.service import AnalysisService
from experiments.gemini_cases import cases, schedule
from tests.pipelines.test_pipelines import report, finding


def confirmation(**changes):
    value = FreeTierConfirmation(model="gemini-3.8-flash", confirmed_at=datetime.now(timezone.utc).isoformat(),
                                 source="owner_ai_studio_confirmation")
    return replace(value, **changes)


@pytest.fixture
def factory(tmp_path, monkeypatch):
    # This marker is an invented local fixture, never a credential from the repository.
    marker = "synthetic-sdk-credential-for-test"
    monkeypatch.setenv("GEMINI_API_KEY", marker)
    created = []

    def make(handler, grant=True, model="gemini-3.8-flash"):
        client = GeminiAdapter(budget=RequestBudget(tmp_path / "budget.jsonl"),
            allowed_original_hashes={sha(c["script"]) for c in cases()},
            grant=confirmation(model=model) if grant is True else grant if grant else None,
            generation=GeminiSettings(model=model), inner_transport=httpx.MockTransport(handler))
        created.append(client)
        return client
    yield make, tmp_path, marker
    for client in created:
        client.close()


def response(value=None, **changes):
    data = {"candidates": [{"content": {"role": "model", "parts": [{"text": json.dumps(value or report())}]},
                            "finishReason": "STOP"}], "modelVersion": "gemini-3.8-flash",
            "usageMetadata": {"promptTokenCount": 100, "candidatesTokenCount": 150,
                              "thoughtsTokenCount": 20, "totalTokenCount": 270}}
    data.update(changes)
    return httpx.Response(200, json=data)


def test_dotenv_only_named_value_no_interpolation_or_environment_export(tmp_path, monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("SYNTHETIC_DOTENV_OTHER", raising=False)
    (tmp_path / ".env").write_text('GEMINI_API_KEY="synthetic-${SYNTHETIC_DOTENV_OTHER}"\nSYNTHETIC_DOTENV_OTHER=not-exported\n', encoding="utf-8")
    assert read_api_key(tmp_path) == "synthetic-${SYNTHETIC_DOTENV_OTHER}"
    import os
    assert "SYNTHETIC_DOTENV_OTHER" not in os.environ and "GEMINI_API_KEY" not in os.environ
    monkeypatch.setenv("GEMINI_API_KEY", "synthetic-environment-precedence")
    assert read_api_key(tmp_path) == "synthetic-environment-precedence"


def test_a_and_status_spend_nothing_and_never_contact_ollama(factory, monkeypatch):
    make, _, _ = factory
    def forbidden(*args):
        raise AssertionError("HTTP was forbidden")
    client = make(forbidden)
    monkeypatch.setattr("app.services.pipelines.ollama.LocalTransport.json", forbidden)
    assert client.status()["ready_for_inference"]
    result = AnalysisService(adapter=client).analyze(cases()[0]["script"], "A")
    assert result.status == "completed" and client.budget.entries() == []


def test_models_listing_one_page_no_generation_and_no_quota_claim(factory):
    make, _, marker = factory
    calls = []
    def handler(request):
        calls.append(request)
        assert request.headers["x-goog-api-key"] == marker
        assert marker not in str(request.url) and marker.encode() not in request.content
        return httpx.Response(200, json={"models": [{"name": "models/gemini-3.8-flash", "supportedGenerationMethods": ["generateContent"]}],
                                         "nextPageToken": "synthetic-next-page"})
    client = make(handler, grant=False)
    value = client.list_models()
    assert len(calls) == 1 and value["authentication"] == "accepted"
    assert value["models"][0]["supported_actions"] == ["generateContent"]
    assert not value["quota_verified_by_listing"] and value["additional_pages_not_fetched"]
    with pytest.raises(OperationalFailure, match="already_attempted"):
        client.list_models()
    assert len(calls) == 1 and len(client.budget.entries()) == 1


@pytest.mark.parametrize("grant", [False, confirmation(tier="Paid"),
    confirmation(confirmed_at=(datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()),
    confirmation(model="gemini-2.5-flash"), confirmation(remaining_rpd=0)])
def test_unconfirmed_or_expired_or_wrong_project_tier_blocks_before_dispatch(factory, grant):
    make, _, _ = factory
    client = make(lambda r: pytest.fail("must not dispatch"), grant=grant)
    result = AnalysisService(adapter=client).analyze(cases()[0]["script"], "B")
    assert result.errors[0].code == "gemini_free_tier_unconfirmed"
    assert client.budget.entries() == []


@pytest.mark.parametrize("status,code", [(400, "gemini_invalid_request"), (401, "gemini_authentication_error"),
    (403, "gemini_permission_denied"), (429, "gemini_quota_exhausted"), (503, "gemini_http_server_error")])
def test_real_sdk_never_retries_or_leaks_errors(factory, caplog, status, code):
    make, path, marker = factory
    calls = []
    def handler(request):
        calls.append(1)
        return httpx.Response(status, json={"error": {"code": status, "message": "invented sensitive error context"}})
    client = make(handler)
    result = AnalysisService(adapter=client).analyze(cases()[0]["script"], "B")
    assert len(calls) == 1 and len(client.budget.entries()) == 1
    assert result.errors[0].code == code and result.errors[0].message == code
    assert result.operational["inference_dispatched"]
    assert "raw_response_utf8" not in result.operational
    assert marker not in result.model_dump_json() + caplog.text + (path / "budget.jsonl").read_text()
    assert "sensitive error context" not in result.model_dump_json() + caplog.text


def test_b_c_same_parameters_two_nonempty_recoveries_no_reference_leak(factory):
    make, _, marker = factory
    calls = []
    def handler(request):
        payload = json.loads(request.content)
        calls.append(payload)
        assert marker not in json.dumps(payload)
        assert not payload.get("tools")
        return response()
    client = make(handler)
    service = AnalysisService(adapter=client)
    for case in [c for c in cases() if c.get("paired_c")]:
        b, c = [service.analyze(case["script"], mode) for mode in ("B", "C")]
        assert b.status == c.status == "completed"
        assert b.deobfuscation is None and c.deobfuscation is not None
        first, second = calls[-2:]
        assert {k: v for k, v in first.items() if k != "contents"} == {k: v for k, v in second.items() if k != "contents"}
        assert set(json.loads(first["contents"][0]["parts"][0]["text"])) == {"original"}
        data = json.loads(second["contents"][0]["parts"][0]["text"])
        assert data["deterministic_recovery"]["verified_texts"]
        assert not {"expected", "behaviors", "risk_label", "criterion"} & data.keys()
        assert c.operational["usage"]["total_token_count"] == 270
        assert "raw_response_utf8" in c.operational and c.evidence == []


def test_private_inputs_and_changed_policy_blocked(factory):
    make, _, _ = factory
    client = make(lambda r: pytest.fail("must not dispatch"))
    service = AnalysisService(adapter=client)
    assert service.analyze("Write-Output 'not in fixed academic set'", "B").errors[0].code == "gemini_synthetic_allowlist_required"
    ctx = build_context(cases()[0]["script"])
    ctx.messages[0]["content"] = "different system instructions"
    with pytest.raises(OperationalFailure, match="context_mismatch"):
        client.infer(ctx, {})
    assert client.budget.entries() == []


def test_echoed_credential_never_persisted(factory):
    make, _, marker = factory
    client = make(lambda r: httpx.Response(200, json={"sensitive": marker}))
    result = AnalysisService(adapter=client).analyze(cases()[0]["script"], "B")
    assert result.errors[0].code == "gemini_credential_echo"
    assert marker not in result.model_dump_json() and "raw_response_utf8" not in result.operational


def test_sdk_redirect_does_not_transmit_credential_to_other_host(factory):
    make, _, _ = factory
    calls = []
    def handler(request):
        calls.append(str(request.url))
        return httpx.Response(307, headers={"Location": "https://synthetic.example.invalid/collect"})
    client = make(handler)
    result = AnalysisService(adapter=client).analyze(cases()[0]["script"], "B")
    assert len(calls) == 1 and result.llm is None


def test_injected_provider_api_metadata_and_status_are_local(factory, tmp_path):
    from fastapi.testclient import TestClient
    from app.api.application import create_app
    make, _, marker = factory
    adapter = make(lambda r: pytest.fail("status must be local"))
    app = create_app(service=AnalysisService(adapter=adapter), frontend_dir=tmp_path / "no-dist")
    with TestClient(app, base_url="http://127.0.0.1") as client:
        capabilities = client.get("/api/capabilities").json()
        status = client.get("/api/ollama/status").json()
        assert capabilities["provider"] == status["provider"] == "gemini"
        assert capabilities["model"] == status["model"] == "gemini-3.8-flash"
        assert capabilities["expected_digest"] is None and status["requests_reserved"] == 0
        assert marker not in json.dumps(capabilities) + json.dumps(status)


def test_known_token_quota_blocks_without_dispatch(factory):
    make, _, _ = factory
    client = make(lambda r: pytest.fail("insufficient known TPM"), grant=confirmation(tpm=1))
    result = AnalysisService(adapter=client).analyze(cases()[0]["script"], "B")
    assert result.errors[0].code == "gemini_known_token_quota_insufficient" and not client.budget.entries()


def test_json_escaped_credential_echo_is_not_persisted(factory):
    make, _, marker = factory
    encoded = "".join("\\u%04x" % ord(c) for c in marker)
    client = make(lambda r: httpx.Response(200, content=('{"echo":"' + encoded + '"}').encode()))
    result = AnalysisService(adapter=client).analyze(cases()[0]["script"], "B")
    assert result.errors[0].code == "gemini_credential_echo"
    assert marker not in result.model_dump_json() and "raw_response_utf8" not in result.operational


def test_experimental_app_cannot_start_without_successful_preflight(tmp_path, monkeypatch):
    from experiments import gemini_application
    monkeypatch.setattr(gemini_application, "OUT", tmp_path)
    with pytest.raises(OperationalFailure, match="gemini_preflight_required"):
        gemini_application.create_app()


def test_budget_counts_errors_metadata_restarts_and_hard_cap(tmp_path):
    path = tmp_path / "budget.jsonl"
    RequestBudget(path).reserve("models.list", sha("metadata"))
    for i in range(11):
        RequestBudget(path).reserve("generateContent", sha(str(i)))
    with pytest.raises(OperationalFailure, match="exhausted"):
        RequestBudget(path).reserve("generateContent", sha("13th"))
    assert len(RequestBudget(path).entries()) == 12


def test_budget_duplicate_and_corruption_fail_closed(tmp_path):
    budget = RequestBudget(tmp_path / "budget.jsonl")
    budget.reserve("generateContent", sha("request"))
    with pytest.raises(OperationalFailure, match="duplicate"):
        budget.reserve("generateContent", sha("request"))
    with budget.path.open("a") as handle:
        handle.write('{"partial":')
    with pytest.raises(OperationalFailure, match="corrupt"):
        budget.reserve("generateContent", sha("another"))


def test_prospective_plan_11_inferences_and_two_paired_C():
    from experiments.gemini_viability import plan
    value = plan()
    assert len(schedule()) == value["inferences_planned"] == 11
    assert value["metadata_requests"] + len(schedule()) == 12
    assert len([c for c in schedule() if c["configuration"] == "C"]) == 2
    assert not value["phase4_started"]

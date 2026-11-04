"""Offline reproductions: real SDK, synthetic secrets, no sockets or Gemini API traffic."""
import gzip
import json
import hashlib
from dataclasses import replace
from datetime import datetime, timedelta, timezone
import socket
import ssl

import httpx
import pytest

pytest.importorskip("google.genai")
from tests.pipelines.test_gemini import factory
from app.services.llm.gemini_budget import MetadataRetryAuthorization, RequestBudget
from app.services.llm.gemini_errors import safe_failure
from app.services.pipelines.resources import OperationalFailure
from app.services.pipelines.service import AnalysisService
from app.services.pipelines.context import sha
from experiments.gemini_cases import cases


def test_compressed_models_response_is_decoded_exactly_once(factory):
    make, _, _ = factory
    data = {"models": [{"name": "models/gemini-3.8-flash", "supportedGenerationMethods": ["generateContent"]}]}
    calls = []
    def handler(request):
        calls.append(1)
        return httpx.Response(200, headers={"Content-Encoding": "gzip", "Content-Type": "application/json"},
                              content=gzip.compress(json.dumps(data).encode()))
    client = make(handler, grant=False)
    result = client.list_models()
    assert result["models"][0]["name"] == "models/gemini-3.8-flash"
    assert len(calls) == len(client.budget.entries()) == 1


@pytest.mark.parametrize("status", [200, 401, 403, 429, 503])
def test_streamed_gzip_and_status_are_preserved_without_sensitive_headers(factory, status):
    make, _, marker = factory
    def handler(request):
        raw = json.dumps({"models": [], "error": {"code": status, "message": "private-http-body"}}).encode()
        return httpx.Response(status, headers={"Content-Encoding": "gzip", "Set-Cookie": "private-header"},
                              stream=httpx.ByteStream(gzip.compress(raw)))
    client = make(handler, grant=False)
    if status == 200:
        assert client.list_models()["models"] == []
    else:
        with pytest.raises(OperationalFailure):
            client.list_models()
        assert client.last_diagnostic["http_status"] == status
        assert client.transport.last_body is None
        assert not any(x in json.dumps(client.last_diagnostic) for x in [marker, "private-http-body", "private-header"])
    assert client.transport.last_status == status and len(client.budget.entries()) == 1


@pytest.mark.parametrize("cause,category", [
    (socket.gaierror(11001, "private DNS context"), "gemini_dns_failure"),
    (ssl.SSLCertVerificationError(1, "private TLS context"), "gemini_tls_certificate_error"),
    (ssl.SSLError(1, "private TLS context"), "gemini_tls_handshake_error"),
    (ConnectionRefusedError(10061, "private connection context"), "gemini_connection_refused"),
    (PermissionError(13, "private network context"), "gemini_network_access_denied"),
    (TimeoutError("private timeout context"), "gemini_timeout"),
    (OSError(10051, "private network context"), "gemini_network_unreachable"),
])
def test_nested_network_failures_are_classified_without_retry_or_sensitive_text(factory, caplog, cause, category):
    make, path, marker = factory
    calls = []
    def handler(request):
        calls.append(1)
        try:
            raise cause
        except Exception as inner:
            raise httpx.ConnectError(marker + " https://invalid.example/?key=" + marker, request=request) from inner
    client = make(handler, grant=False)
    with pytest.raises(OperationalFailure, match=category):
        client.list_models()
    assert client.last_diagnostic == {"category": category, "http_status": None}
    assert len(calls) == len(client.budget.entries()) == 1
    assert marker not in json.dumps(client.last_diagnostic) + caplog.text + (path / "budget.jsonl").read_text()
    assert "private" not in json.dumps(client.last_diagnostic) + caplog.text


def test_decoding_failure_has_safe_category_and_known_http_status(factory):
    make, _, _ = factory
    def handler(request):
        return httpx.Response(200, headers={"Content-Encoding": "gzip"}, stream=httpx.ByteStream(b"invalid-compression"))
    client = make(handler, grant=False)
    with pytest.raises(OperationalFailure, match="gemini_response_decoding_error"):
        client.list_models()
    assert client.last_diagnostic == {"category": "gemini_response_decoding_error", "http_status": 200}
    assert client.transport.last_body is None and len(client.budget.entries()) == 1


def authorization(budget, **changes):
    return replace(MetadataRetryAuthorization(authorized=True,
        prior_ledger_sha256=hashlib.sha256(budget.path.read_bytes()).hexdigest(),
        confirmed_at=datetime.now(timezone.utc).isoformat(), source="explicit_owner_authorization"), **changes)


def test_second_metadata_requires_exact_recent_one_shot_approval(factory):
    make, _, marker = factory
    calls = []
    client = make(lambda r: (calls.append(1) or httpx.Response(200, json={"models": []})), grant=False)
    client.list_models()
    first_line = client.budget.path.read_bytes()
    with pytest.raises(OperationalFailure, match="already_attempted"):
        client.list_models()
    assert client.budget.path.read_bytes() == first_line
    client.transport.metadata_retry = authorization(client.budget)
    result = client.list_models()
    assert result["authentication"] == "accepted" and len(calls) == 2
    assert client.budget.path.read_bytes().startswith(first_line)
    assert client.budget.entries()[1]["attempt"] == 2
    assert "metadata_retry_authorization_sha256" in client.budget.entries()[1]
    with pytest.raises(OperationalFailure, match="already_attempted"):
        client.list_models()
    assert len(calls) == len(client.budget.entries()) == 2


@pytest.mark.parametrize("changes", [{"authorized": False}, {"source": "pending_owner_approval"},
    {"confirmed_at": (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()},
    {"prior_ledger_sha256": "wrong"}, {"max_total_requests": 13}, {"max_total_metadata_requests": 3},
    {"operation": "generateContent"}])
def test_bad_approval_never_changes_ledger_or_dispatches(factory, changes):
    make, _, _ = factory
    client = make(lambda r: httpx.Response(200, json={"models": []}), grant=False)
    client.list_models()
    original = client.budget.path.read_bytes()
    client.transport.metadata_retry = authorization(client.budget, **changes)
    with pytest.raises(OperationalFailure, match="not_authorized"):
        client.list_models()
    assert client.budget.path.read_bytes() == original


def test_two_metadata_requests_leave_at_most_ten_generations(tmp_path):
    budget = RequestBudget(tmp_path / "ledger.jsonl")
    budget.reserve("models.list", sha("metadata"))
    budget.reserve("models.list", sha("metadata"), metadata_retry=authorization(budget))
    for i in range(10):
        budget.reserve("generateContent", sha(str(i)))
    with pytest.raises(OperationalFailure, match="exhausted"):
        budget.reserve("generateContent", sha("eleventh generation"))
    assert len(budget.entries()) == 12


def test_r2_plan_prioritizes_two_paired_c_and_never_changes_model():
    from experiments.gemini_metadata_retry import prospective_plan
    plan = prospective_plan()
    assert plan["metadata_requests"] + plan["inferences_planned"] == 12
    assert len(plan["cases"]) == 10 and plan["model_preference"] == ["gemini-3.8-flash"]
    assert [c["configuration"] for c in plan["cases"][:4]] == ["B", "C", "B", "C"]
    assert not plan["execution_authorized"] and plan["no_model_change"]


def test_metadata_retry_preview_and_unapproved_execution_never_construct_client(tmp_path, monkeypatch):
    from experiments import gemini_metadata_retry as retry
    ledger = RequestBudget(tmp_path / "requests.jsonl")
    ledger.reserve("models.list", sha("metadata"))
    monkeypatch.setattr(retry, "OUT", tmp_path)
    monkeypatch.setattr(retry, "GeminiAdapter", lambda *a, **kw: pytest.fail("network client forbidden"))
    initial = ledger.path.read_bytes()
    assert retry.preview()["mode"] == "preview_no_network"
    path = tmp_path / "authorization.json"
    from dataclasses import asdict
    path.write_text(json.dumps(asdict(authorization(ledger, authorized=False))))
    with pytest.raises(OperationalFailure, match="not_authorized"):
        retry.execute(path)
    assert ledger.path.read_bytes() == initial


def test_pinned_sdk_uses_custom_http_client_and_one_attempt_only(tmp_path, monkeypatch):
    from app.services.llm.gemini import GeminiAdapter
    monkeypatch.setenv("GEMINI_API_KEY", "synthetic-config-check-only")
    adapter = GeminiAdapter(budget=RequestBudget(tmp_path / "no-network.jsonl"), allowed_original_hashes=set())
    try:
        assert adapter.client._api_client._httpx_client is adapter.http
        assert adapter.client._api_client._http_options.retry_options.attempts == 1
        assert adapter.transport.inner._pool._retries == 0
        assert not adapter.http.follow_redirects and not adapter.http.trust_env
        assert adapter.budget.entries() == []
    finally:
        adapter.close()

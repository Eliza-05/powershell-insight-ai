"""One plain-text recovery probe; uses the existing global Gemini ledger.

Preparation uses a fake key/MockTransport. Real dispatch requires a fresh owner
quota confirmation and an exclusive one-shot intent. No metadata or fallback.
The response path retains the existing corrected single-decompression behavior.
"""
from datetime import datetime, timezone
import base64
import gzip
import hashlib
import json
import logging
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))
import httpx
from google import genai
from google.genai import types
from app.services.llm.gemini import BoundedTransport, FreeTierConfirmation, fail
from app.services.llm.gemini_budget import RequestBudget
from app.services.llm.gemini_credentials import read_api_key
from app.services.llm.gemini_error_details import structured_error_details
from app.services.llm.gemini_errors import safe_failure
from app.services.pipelines.context import canonical, sha

OUT = Path(__file__).resolve().parent
LEDGER = ROOT / "artifacts/gemini_viability/requests.jsonl"
MODEL = "gemini-3.8-flash"
PROMPT = "Responde exclusivamente con la palabra OK."


def now():
    return datetime.now(timezone.utc).isoformat()


def save(name, data):
    with (OUT / name).open("x", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")
        f.flush()
        import os
        os.fsync(f.fileno())


def make_client(key, transport):
    http = httpx.Client(transport=transport, trust_env=False, follow_redirects=False, timeout=60)
    client = genai.Client(api_key=key, vertexai=False, enterprise=False,
        http_options=types.HttpOptions(base_url="https://generativelanguage.googleapis.com",
            api_version="v1beta", timeout=60_000,
            retry_options=types.HttpRetryOptions(attempts=1), httpx_client=http))
    return client, http


def generate(client):
    return client.models.generate_content(model=MODEL, contents=PROMPT,
        config=types.GenerateContentConfig(
            automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True)))


class ProbeBudget(RequestBudget):
    LIMIT = 5  # Existing ledger is 4/12; this probe cannot reserve a sixth entry.


class MinimalTransport(BoundedTransport):
    def __init__(self, key, grant, wire, *, budget, inner=None):
        super().__init__(budget, key, MODEL, grant, (), inner=inner)
        self.wire = wire
        self.calls = 0

    def handle_request(self, request):
        body = request.read()
        if (request.method != "POST" or request.url.scheme != "https"
            or request.url.host != "generativelanguage.googleapis.com"
            or request.url.port not in (None, 443) or request.url.userinfo or request.url.query
            or request.url.path != f"/v1beta/models/{MODEL}:generateContent"
            or body.decode("utf-8") != self.wire or self.calls):
            fail("probe_request_not_authorized")
        self.grant.check(MODEL)
        if self._key in body.decode("utf-8"):
            fail("gemini_credential_in_payload")
        fingerprint = sha(canonical({"method": "POST", "path": request.url.path, "body": self.wire}))
        self.last_attempt = self.budget.reserve("generateContent", fingerprint)
        self.calls += 1
        response = self.inner.handle_request(request)
        self.last_status = response.status_code
        try:
            chunks, total = [], 0
            # Same corrected response path as BoundedTransport: decode exactly once.
            for chunk in response.iter_bytes():
                total += len(chunk)
                if total > 2_097_152:
                    fail("gemini_response_too_large")
                chunks.append(chunk)
            raw = b"".join(chunks)
            try:
                parsed = json.loads(raw)
                decoded = canonical(parsed)
            except (ValueError, UnicodeError):
                parsed, decoded = None, ""
            if self._key.encode() in raw or self._key in decoded:
                fail("gemini_credential_echo")
            self.last_error_details = structured_error_details(parsed, response.status_code)
            if response.status_code == 200:
                self.last_body = raw.decode("utf-8")
            # HTTPX iter_bytes has already decompressed: never relay Content-Encoding.
            return httpx.Response(response.status_code, content=raw, request=request,
                                  headers={"Content-Type": "application/json"})
        finally:
            response.close()


def prepare():
    from importlib.metadata import version
    captured = []
    def capture(request):
        captured.append({"method": request.method, "path": request.url.path,
                         "body": request.read().decode("utf-8")})
        return httpx.Response(200, json={"candidates": [{"content": {
            "role": "model", "parts": [{"text": "OK"}]}, "finishReason": "STOP"}]})
    client, http = make_client("synthetic-probe-key", httpx.MockTransport(capture))
    try:
        assert generate(client).text == "OK"
    finally:
        client.close(); http.close()
    assert len(captured) == 1
    payload = json.loads(captured[0]["body"])
    assert payload == {"contents": [{"parts": [{"text": PROMPT}], "role": "user"}],
                       "generationConfig": {}}
    plan = {"version": "gemini-38-recovery-v1", "created_at": now(), "model": MODEL,
        "prompt": PROMPT, "wire": captured[0], "SDK": version("google-genai"),
        "SDK_attempts": 1, "HTTP_retries": 0, "new_generation_cap": 1,
        "configuration": "service defaults; SDK emits empty generationConfig; no schema/system/tools/files",
        "automatic_function_calling": "disabled_client_side", "timeout_seconds": 60,
        "ledger_before_sha256": hashlib.sha256(LEDGER.read_bytes()).hexdigest(),
        "initial_ledger_entries": len(LEDGER.read_bytes().splitlines()),
        "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "authorization": "Explicit current owner request for exactly one new standalone operational generation; not replacement of G03-B",
        "quota": "requires fresh owner confirmation before execution",
        "official_sources": ["https://aistudio.google.com/api-reference/generate-content",
                             "https://aistudio.google.com/docs/models/gemini-3.8-flash",
                             "https://aistudio.google.com/status"],
        "public_status": "AI Studio status SPA not extractable by text browser; no model availability inferred from an empty page"}
    assert plan["initial_ledger_entries"] == 4
    save("plan_frozen_v1.json", plan)
    print(json.dumps({"prepared": True, "mock_HTTP_calls": len(captured), "wire": payload,
                      "SDK": plan["SDK"], "live_calls": 0}))


def execute():
    plan = json.loads((OUT / "plan_frozen_v1.json").read_text(encoding="utf-8"))
    assert plan["source_sha256"] == hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    assert hashlib.sha256(LEDGER.read_bytes()).hexdigest() == plan["ledger_before_sha256"]
    quota = json.loads((OUT / "quota_confirmation.json").read_text(encoding="utf-8"))
    assert quota["billing_enabled"] is False and quota["quota_available_for_one"] is True
    grant = FreeTierConfirmation(model=MODEL, confirmed_at=quota["confirmed_at"],
        source="owner_ai_studio_confirmation", tier=quota["tier"], remaining_rpd=quota["remaining_rpd"])
    grant.check(MODEL)
    for name in ("google.genai", "google_genai", "httpx", "httpcore"):
        logger = logging.getLogger(name)
        logger.handlers = [logging.NullHandler()]; logger.propagate = False; logger.setLevel(100)
    save("execution_intent.json", {"at": now(), "maximum_new_generations": 1,
         "plan_sha256": hashlib.sha256((OUT / "plan_frozen_v1.json").read_bytes()).hexdigest(),
         "quota_sha256": hashlib.sha256((OUT / "quota_confirmation.json").read_bytes()).hexdigest()})
    transport = MinimalTransport(read_api_key(), grant, plan["wire"]["body"], budget=ProbeBudget(LEDGER))
    client, http = make_client(transport._key, transport)
    result = {"model_requested": MODEL, "started_at": now()}
    started = time.monotonic()
    try:
        response = generate(client)
        result.update(text=response.text, exact_OK=response.text == "OK",
            OK_after_whitespace_only=response.text.strip() == "OK" if response.text else False,
            model_version=response.model_version,
            usage=response.usage_metadata.model_dump(mode="json") if response.usage_metadata else None,
            finish_reasons=[str(c.finish_reason) for c in response.candidates or []],
            response=response.model_dump(mode="json"))
    except Exception as exc:
        result.update(error={**safe_failure(exc, transport.last_status), **transport.last_error_details})
    finally:
        result.update(latency_seconds=time.monotonic() - started, http_status=transport.last_status,
            HTTP_dispatches=transport.calls, ledger_reservation=transport.last_attempt,
            raw_success_body=transport.last_body,
            error_body_policy="safe structured error fields only; no arbitrary exception/message/headers persisted")
        save("result.json", result)
        client.close(); http.close()
    print(json.dumps({k:v for k,v in result.items() if k not in {"response", "raw_success_body"}}, ensure_ascii=True))


if __name__ == "__main__":
    if sys.argv[1:] == ["prepare"]:
        prepare()
    elif sys.argv[1:] == ["execute"]:
        execute()
    else:
        raise SystemExit("Choose prepare or execute; no automatic sequence or retries")

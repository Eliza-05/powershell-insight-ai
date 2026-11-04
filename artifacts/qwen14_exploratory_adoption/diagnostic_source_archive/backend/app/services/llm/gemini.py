"""Opt-in Gemini adapter for synthetic diagnostics, with no execution or tools."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import logging
from pathlib import Path
import time

import httpx

from app.services.llm.gemini_budget import RequestBudget
from app.services.llm.gemini_credentials import read_api_key
from app.services.llm.gemini_errors import safe_failure
from app.services.llm.gemini_error_details import structured_error_details
from app.services.pipelines.config import PipelineSettings
from app.services.pipelines.context import PROMPT_VERSION, canonical, sha
from app.services.pipelines.provider import response_schema
from app.services.pipelines.resources import OperationalFailure

MODELS = ("gemini-3.8-flash", "gemini-2.5-flash")


def fail(code):
    raise OperationalFailure(code, code, "gemini") from None


@dataclass(frozen=True)
class FreeTierConfirmation:
    model: str
    confirmed_at: str
    source: str
    tier: str = "Free"
    rpm: int | None = None
    tpm: int | None = None
    rpd: int | None = None
    remaining_rpd: int | None = None

    def check(self, model):
        try:
            age = (datetime.now(timezone.utc) - datetime.fromisoformat(self.confirmed_at)).total_seconds()
            valid = (self.tier == "Free" and self.model == model and self.source == "owner_ai_studio_confirmation"
                     and 0 <= age < 3600
                     and all(v is None or (type(v) is int and v > 0)
                             for v in (self.rpm, self.tpm, self.rpd, self.remaining_rpd)))
        except Exception:
            valid = False
        if not valid:
            fail("gemini_free_tier_unconfirmed")


@dataclass(frozen=True)
class GeminiSettings:
    model: str = MODELS[0]
    temperature: float = 1.0
    seed: int = 42
    top_p: float = 0.95
    max_output_tokens: int = 4096  # includes thinking; policy asks for <=2048 response tokens
    timeout_seconds: int = 60

    def __post_init__(self):
        if self.model not in MODELS or (self.temperature, self.seed, self.top_p,
                self.max_output_tokens, self.timeout_seconds) != (1.0, 42, 0.95, 4096, 60):
            fail("gemini_configuration_forbidden")


class BoundedTransport(httpx.BaseTransport):
    """Count physical HTTP attempts, deny redirects/endpoints, keep secrets out of artifacts."""
    def __init__(self, budget, key, model, grant, allowed_original_hashes, *, inner=None, metadata_retry=None):
        self.budget, self._key, self.model = budget, key, model
        self.grant = grant
        self.metadata_retry = metadata_retry
        self.allowed_original_hashes = frozenset(allowed_original_hashes)
        self.inner = inner if inner is not None else httpx.HTTPTransport(retries=0, trust_env=False)
        self.last_body = None
        self.last_status = None
        self.last_attempt = None
        self.last_error_details = {}

    def handle_request(self, request):
        self.last_body = self.last_status = self.last_attempt = None
        self.last_error_details = {}
        if (request.url.scheme != "https" or request.url.host != "generativelanguage.googleapis.com"
                or request.url.port not in (None, 443) or request.url.userinfo):
            fail("gemini_endpoint_forbidden")
        body = request.read()
        if self._key.encode() in body or self._key in str(request.url):
            fail("gemini_credential_in_payload")
        if request.method == "GET" and request.url.path == "/v1beta/models":
            kind = "models.list"
        elif request.method == "POST" and request.url.path == f"/v1beta/models/{self.model}:generateContent":
            if self.grant is None:
                fail("gemini_free_tier_unconfirmed")
            self.grant.check(self.model)
            try:
                import json
                payload = json.loads(body)
                data = json.loads(payload["contents"][0]["parts"][0]["text"])
                if (sha(data["original"]) not in self.allowed_original_hashes or payload.get("tools")
                        or set(data) not in ({"original"}, {"original", "deterministic_recovery"})):
                    fail("gemini_synthetic_allowlist_required")
            except OperationalFailure:
                raise
            except Exception:
                fail("gemini_payload_forbidden")
            kind = "generateContent"
        else:
            fail("gemini_endpoint_forbidden")
        if len(body) > 65536:
            fail("gemini_request_too_large")
        # Headers/key are deliberately excluded from fingerprints and persisted state.
        fingerprint = sha(canonical({"method": request.method, "path": request.url.path,
                                      "body": body.decode("utf-8")}))
        self.last_attempt = self.budget.reserve(kind, fingerprint,
            metadata_retry=self.metadata_retry if kind == "models.list" else None)
        response = self.inner.handle_request(request)
        self.last_status = response.status_code
        try:
            chunks, length = [], 0
            for chunk in response.iter_bytes():
                length += len(chunk)
                if length > 2_097_152:
                    fail("gemini_response_too_large")
                chunks.append(chunk)
            raw = b"".join(chunks)
            import json
            parsed = None
            try:
                parsed = json.loads(raw)
                decoded = canonical(parsed)
            except (ValueError, UnicodeError):
                decoded = ""
            if self._key.encode() in raw or self._key in decoded:
                fail("gemini_credential_echo")
            self.last_error_details = structured_error_details(parsed, response.status_code)
            # Error bodies may echo credentials or infrastructure information: never retain them.
            if response.status_code == 200:
                self.last_body = raw.decode("utf-8")
            # iter_bytes() already decoded gzip/deflate. Retaining Content-Encoding
            # here would cause HTTPX to decode again, hiding success behind DecodingError.
            # Do not relay cookies, authentication challenges or representation headers.
            headers = {"Content-Type": response.headers.get("Content-Type", "application/json")}
            return httpx.Response(response.status_code, headers=headers, content=raw, request=request)
        finally:
            response.close()

    def close(self):
        self.inner.close()


class GeminiAdapter:
    provider = "gemini"

    def __init__(self, settings: PipelineSettings | None = None, *, budget: RequestBudget,
                 allowed_original_hashes, grant: FreeTierConfirmation | None = None,
                 generation: GeminiSettings | None = None, root: Path | None = None, inner_transport=None, metadata_retry=None):
        self.settings = settings or PipelineSettings()  # input limits only; never sent as model settings
        self.generation = generation or GeminiSettings()
        self.grant, self.budget = grant, budget
        self.allowed_original_hashes = frozenset(allowed_original_hashes)
        # Do not let SDK/HTTP diagnostics propagate request or credential data to application logs.
        for name in ("google.genai", "google_genai", "httpx", "httpcore"):
            logger = logging.getLogger(name)
            logger.handlers = [logging.NullHandler()]
            logger.propagate = False
            logger.setLevel(logging.CRITICAL + 1)
        try:
            from google import genai
            from google.genai import types
            key = read_api_key() if root is None else read_api_key(root)
            self.transport = BoundedTransport(budget, key, self.generation.model, grant,
                                             self.allowed_original_hashes, inner=inner_transport, metadata_retry=metadata_retry)
            self.http = httpx.Client(transport=self.transport, trust_env=False, follow_redirects=False,
                                     timeout=self.generation.timeout_seconds)
            self.client = genai.Client(api_key=key, vertexai=False, enterprise=False,
                http_options=types.HttpOptions(base_url="https://generativelanguage.googleapis.com",
                    api_version="v1beta", timeout=60_000, retry_options=types.HttpRetryOptions(attempts=1),
                    httpx_client=self.http))
        except OperationalFailure:
            raise
        except Exception:
            fail("gemini_client_configuration")

    def close(self):
        self.client.close()
        self.http.close()

    def public_metadata(self):
        return {"provider": self.provider, "model": self.generation.model, "expected_digest": None,
                "options": asdict(self.generation), "think": "low" if self.generation.model.startswith("gemini-3") else "budget_512",
                "timeout_seconds": self.generation.timeout_seconds, "synthetic_only": True}

    def status(self):
        # Local inspection only; polling the UI must never spend the request budget.
        ready = False
        confirmed = False
        try:
            if self.grant is not None:
                self.grant.check(self.generation.model)
                confirmed = True
                ready = len(self.budget.entries()) < self.budget.LIMIT
        except OperationalFailure:
            pass
        return {**self.public_metadata(), "available": True, "ready_for_inference": ready,
                "requests_reserved": len(self.budget.entries()), "request_limit": self.budget.LIMIT,
                "free_tier_confirmed": confirmed, "quota_limits": asdict(self.grant) if self.grant else None}

    def _error(self, exc):
        self.last_diagnostic = {**safe_failure(exc, self.transport.last_status), **self.transport.last_error_details}
        return self.last_diagnostic["category"]

    def list_models(self):
        self.transport.last_body = self.transport.last_status = self.transport.last_attempt = None
        self.transport.last_error_details = {}
        self.last_diagnostic = None
        try:
            pager = self.client.models.list(config={"page_size": 1000})
            # Reading .page consumes no additional page. Never auto-page or retry.
            models = [{k: getattr(m, k, None) for k in ("name", "version", "input_token_limit", "output_token_limit",
                                                       "supported_actions", "thinking")} for m in pager.page]
            return {"authentication": "accepted", "models": models,
                    "additional_pages_not_fetched": bool(pager.config.get("page_token")),
                    "http_attempt": self.transport.last_attempt, "quota_verified_by_listing": False}
        except Exception as exc:
            fail(self._error(exc))

    def _generation_config(self, context):
        """Historical configuration, kept separate from newer model-specific rules."""
        from google.genai import types
        cfg = self.generation
        thinking = types.ThinkingConfig(thinking_level="low", include_thoughts=False) if cfg.model.startswith("gemini-3") else types.ThinkingConfig(thinking_budget=512, include_thoughts=False)
        return types.GenerateContentConfig(system_instruction=context.messages[0]["content"],
            temperature=cfg.temperature, seed=cfg.seed, top_p=cfg.top_p,
            max_output_tokens=cfg.max_output_tokens, response_mime_type="application/json",
            response_json_schema=response_schema(), thinking_config=thinking, tools=[],
            automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True), candidate_count=1)

    def infer(self, context, record):
        from google.genai import types
        cfg = self.generation
        record.update(provider=self.provider, model=cfg.model, inference_dispatched=False,
                      prompt_version=PROMPT_VERSION, prompt_sha256=context.prompt_sha256,
                      context_sha256=context.context_sha256, validation_version="literal-provenance-v1")
        if sha(context.sources["original"]) not in self.allowed_original_hashes:
            fail("gemini_synthetic_allowlist_required")
        if self.grant is None:
            fail("gemini_free_tier_unconfirmed")
        self.grant.check(cfg.model)
        # A call must originate from the shared context constructor, never accept injected system instructions.
        from app.services.pipelines.context import build_context
        expected = build_context(context.sources["original"], context.deobfuscation)
        if context != expected:
            fail("gemini_context_mismatch")
        config = self._generation_config(context)
        payload = {"model": cfg.model, "contents": context.messages[1]["content"],
                   "config": config.model_dump(mode="json", exclude_none=True)}
        input_upper_bound = sum(len(m["content"].encode("utf-8")) for m in context.messages) + len(canonical(response_schema()).encode("utf-8")) + 512
        if self.grant.tpm is not None and input_upper_bound > self.grant.tpm:
            fail("gemini_known_token_quota_insufficient")
        if self.grant.remaining_rpd is not None and sum(e["kind"] == "generateContent" for e in self.budget.entries()) >= self.grant.remaining_rpd:
            fail("gemini_known_daily_quota_exhausted")
        record.update(request=payload, request_sha256=sha(canonical(payload)),
                      schema_sha256=sha(canonical(response_schema())), configuration=asdict(cfg),
                      quota_confirmation=asdict(self.grant), quota_remaining_unknown=True,
                      input_token_upper_bound=input_upper_bound)
        started = time.monotonic()
        # Clear transport state even if SDK rejects the new request before dispatch.
        self.transport.last_body = self.transport.last_status = self.transport.last_attempt = None
        self.transport.last_error_details = {}
        try:
            response = self.client.models.generate_content(model=cfg.model, contents=payload["contents"], config=config)
            record["response"] = response.model_dump(mode="json", exclude_none=True, exclude={"sdk_http_response"})
            record["usage"] = response.usage_metadata.model_dump(mode="json", exclude_none=True) if response.usage_metadata else None
            record["model_version"] = response.model_version
            if not response.model_version or not (response.model_version == cfg.model or response.model_version.startswith(cfg.model + "-")):
                fail("gemini_response_model_mismatch")
            candidates = response.candidates or []
            if len(candidates) != 1 or candidates[0].finish_reason != types.FinishReason.STOP:
                fail("gemini_incomplete_or_blocked")
            parts = candidates[0].content.parts if candidates[0].content else []
            if any(p.function_call or p.executable_code or p.code_execution_result for p in parts):
                fail("gemini_unexpected_tool_call")
            if not response.usage_metadata:
                fail("gemini_missing_token_counts")
            text = "".join(p.text or "" for p in parts if not p.thought)
            return {"model": response.model_version, "message": {"content": text}}
        except Exception as exc:
            code = self._error(exc)
            record["error_type"] = code
            record["diagnostic"] = self.last_diagnostic
            fail(code)
        finally:
            record.update(inference_seconds=time.monotonic() - started,
                          inference_dispatched=self.transport.last_attempt is not None,
                          http_attempt=self.transport.last_attempt, http_status=self.transport.last_status)
            if self.transport.last_body is not None:
                record["raw_response_utf8"] = self.transport.last_body

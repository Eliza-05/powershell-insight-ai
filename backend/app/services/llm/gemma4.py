"""Experimental Gemma adapter. No application routing or historical provider changes.

Reuses the existing orchestration, provenance validation, resource monitor and gate.
Only the transport's model allowlist and model-specific settings differ from Qwen.
Chat requires a campaign-provided durable authorization callback; metadata does not.
"""
from __future__ import annotations

import base64
import http.client
import socket
from typing import Literal

from pydantic import Field

from app.services.pipelines.config import PipelineSettings
from app.services.pipelines.context import canonical
from app.services.pipelines.ollama import LocalTransport, OllamaAdapter
from app.services.pipelines.resources import OperationalFailure
from app.services.pipelines.validation import strict_json

MODEL = "gemma4:12b"
DIGEST = "6114515d63c17436a7c0417d82820ac65ad643e2806c5a3c89cb62846436ed0b"
REQUIRED_AVAILABLE = 15_135_148_032


class Gemma4Settings(PipelineSettings):
    model: Literal["gemma4:12b"] = MODEL
    expected_digest: Literal[DIGEST] = DIGEST
    unloaded_reserve_bytes: int = Field(default=12_987_664_384, ge=12_987_664_384, strict=True)


class Gemma4Transport(LocalTransport):
    def __init__(self, *, authorize_dispatch=None, timeout=300):
        super().__init__(11434, timeout)
        self.authorize_dispatch = authorize_dispatch

    def json(self, endpoint, payload=None):
        if endpoint not in {"version", "tags", "ps", "show", "chat"}:
            raise OperationalFailure("endpoint_forbidden", "Experimental endpoint forbidden")
        if payload is not None and payload.get("model") != MODEL:
            raise OperationalFailure("model_forbidden", "Only gemma4:12b is authorized")
        if endpoint == "chat" and (payload is None or self.authorize_dispatch is None):
            raise OperationalFailure("campaign_authorization_required", "Chat needs durable eight-attempt authorization")
        self.last_response = None
        connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=self.timeout)
        self.connection = connection
        try:
            if self.cancelled.is_set():
                raise OperationalFailure("request_cancelled", "Cancelled before dispatch")
            if endpoint == "chat":
                self.authorize_dispatch(payload)  # Durable reservation BEFORE any request bytes.
            connection.request("GET" if payload is None else "POST", "/api/" + endpoint,
                               body=None if payload is None else canonical(payload).encode("utf-8"),
                               headers={"Content-Type": "application/json"})
            if self.cancelled.is_set():
                self.cancel()
                raise OperationalFailure("request_cancelled", "Cancelled after dispatch")
            response = connection.getresponse()
            chunks, total, complete = [], 0, False
            try:
                while True:
                    try:
                        chunk = response.read1(min(16384, 2_097_153 - total))
                    except http.client.IncompleteRead as exc:
                        chunks.append(exc.partial[:max(0, 2_097_153 - total)])
                        raise
                    if not chunk:
                        if response.length not in (None, 0):
                            raise http.client.IncompleteRead(b"", response.length)
                        complete = True
                        break
                    chunks.append(chunk)
                    total += len(chunk)
                    if total > 2_097_152:
                        raise OperationalFailure("response_too_large", "Response exceeds 2 MiB")
            finally:
                raw = b"".join(chunks)
                self.last_response = {"status": response.status,
                    "raw_bytes_base64": base64.b64encode(raw).decode("ascii"),
                    "raw_utf8": raw.decode("utf-8", errors="replace"), "transport_read_complete": complete}
            value = strict_json(raw.decode("utf-8", errors="strict"))
            if not isinstance(value, dict):
                raise OperationalFailure("invalid_transport_json", "Expected JSON object")
            if response.status != 200 or "error" in value:
                code = "insufficient_memory" if any(x in str(value.get("error", "")).lower()
                    for x in ("out of memory", "insufficient memory", "not enough memory")) else "ollama_http_error"
                raise OperationalFailure(code, f"HTTP {response.status}: {value.get('error')}")
            return value
        except (TimeoutError, socket.timeout) as exc:
            raise OperationalFailure("timeout", "Gemma request timeout") from exc
        except (OSError, http.client.HTTPException) as exc:
            raise OperationalFailure("ollama_unavailable", str(exc)) from exc
        finally:
            connection.close()
            self.connection = None


class Gemma4Adapter(OllamaAdapter):
    def __init__(self, *, authorize_dispatch=None, **kwargs):
        settings = Gemma4Settings()
        kwargs.setdefault("transport_factory", lambda: Gemma4Transport(authorize_dispatch=authorize_dispatch))
        super().__init__(settings, **kwargs)

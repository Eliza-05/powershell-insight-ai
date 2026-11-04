"""Bounded loopback HTTP adapter: no pull, redirects, proxies, tools or subprocesses."""
from __future__ import annotations

import http.client
import base64
import socket
import threading
import time
from typing import Protocol

from app.services.pipelines.config import MODEL, PipelineSettings
from app.services.pipelines.context import AnalysisContext, canonical, sha, PROMPT_VERSION
from app.services.pipelines.resources import (
    InferenceGate, OperationalFailure, ResourceMonitor, memory_snapshot,
)
from app.services.pipelines.validation import strict_json
from app.services.pipelines.provider import InferenceAdapter, response_schema


class Transport(Protocol):
    def json(self, endpoint: str, payload: dict | None = None) -> dict: ...
    def cancel(self) -> None: ...


class LocalTransport:
    def __init__(self, port=11434, timeout=300):
        self.port, self.timeout = port, timeout
        self.connection = None
        self.last_response = None
        self.cancelled = threading.Event()

    def cancel(self):
        self.cancelled.set()
        connection = self.connection
        if connection and connection.sock:
            try:
                connection.sock.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass

    def json(self, endpoint, payload=None):
        if endpoint not in {"version", "tags", "ps", "show", "chat"}:
            raise OperationalFailure("endpoint_forbidden", "Endpoint not allowlisted")
        if payload is not None and payload.get("model", MODEL) != MODEL:
            raise OperationalFailure("model_forbidden", "Only the authorized model is permitted")
        # Never attach a previous endpoint's body to a failed new request.
        self.last_response = None
        connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=self.timeout)
        self.connection = connection
        try:
            if self.cancelled.is_set():
                raise OperationalFailure("request_cancelled", "Request cancelled before dispatch")
            connection.request("GET" if payload is None else "POST", "/api/" + endpoint,
                               body=None if payload is None else canonical(payload).encode("utf-8"),
                               headers={"Content-Type": "application/json"})
            if self.cancelled.is_set():
                self.cancel()
                raise OperationalFailure("request_cancelled", "Request cancelled")
            response = connection.getresponse()
            chunks, total, read_complete = [], 0, False
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
                        read_complete = True
                        break
                    chunks.append(chunk)
                    total += len(chunk)
                    if total > 2_097_152:
                        raise OperationalFailure("response_too_large", "Ollama response exceeds 2 MiB")
            finally:
                raw = b"".join(chunks)
                self.last_response = {"status": response.status, "raw_bytes_base64": base64.b64encode(raw).decode("ascii"),
                                      "raw_utf8": raw.decode("utf-8", errors="replace"),
                                      "transport_read_complete": read_complete}
            value = strict_json(raw.decode("utf-8", errors="strict"))
            if not isinstance(value, dict):
                raise OperationalFailure("invalid_transport_json", "Expected an object")
            if response.status != 200 or "error" in value:
                if any(token in str(value.get("error", "")).lower() for token in ("out of memory", "insufficient memory", "not enough memory")):
                    raise OperationalFailure("insufficient_memory", "Ollama reported resource exhaustion: " + str(value.get("error")), "resources")
                raise OperationalFailure("ollama_http_error", f"HTTP {response.status}: {value.get('error', 'unexpected status')}")
            return value
        except (TimeoutError, socket.timeout) as exc:
            raise OperationalFailure("timeout", "Ollama request timeout") from exc
        except (OSError, http.client.HTTPException) as exc:
            raise OperationalFailure("ollama_unavailable", str(exc)) from exc
        finally:
            connection.close()
            self.connection = None


class OllamaAdapter:
    def __init__(self, settings: PipelineSettings | None = None, *, transport_factory=None,
                 sampler=memory_snapshot, gate_factory=InferenceGate):
        self.settings = settings or PipelineSettings()
        self.transport_factory = transport_factory or (
            lambda: LocalTransport(self.settings.port, self.settings.timeout_seconds))
        self.sampler, self.gate_factory = sampler, gate_factory

    def _state(self, client):
        tags, residents = client.json("tags"), client.json("ps")
        installed = [m for m in tags.get("models", []) if m.get("name") == self.settings.model]
        if len(installed) != 1:
            raise OperationalFailure("model_missing", "Authorized model is not installed")
        if installed[0].get("digest") != self.settings.expected_digest:
            raise OperationalFailure("digest_mismatch", "Installed model digest differs from authorized digest")
        loaded = residents.get("models", [])
        if len(loaded) > 1 or any(m.get("digest") != self.settings.expected_digest for m in loaded):
            raise OperationalFailure("other_model_loaded", "Only the authorized model may be resident; no models unloaded automatically")
        return {"model": installed[0], "residents": loaded}

    def status(self):
        record = {}
        try:
            client = self.transport_factory()
            record["version"] = client.json("version")
            record["state"] = self._state(client)
            record["memory"] = self.sampler()
            record["available"] = True
            resident = record["state"]["residents"]
            warm = (bool(resident) and resident[0].get("context_length") == self.settings.options.num_ctx
                    and resident[0].get("size_vram", 0) == 0)
            reserve = self.settings.loaded_growth_reserve_bytes if warm else self.settings.unloaded_reserve_bytes
            record["required_available_bytes"] = self.settings.minimum_margin_bytes + reserve
            record["resource_ready"] = min(record["memory"]["available_bytes"], record["memory"]["commit_available_bytes"]) >= record["required_available_bytes"]
            record["circuit_blocked"] = self.gate_factory().marker.exists()
            record["ready_for_inference"] = record["resource_ready"] and not record["circuit_blocked"]
        except Exception as exc:
            record.update(available=False, error={"code": getattr(exc, "code", "status_error"), "message": str(exc)})
        return record

    def infer(self, context, record):
        cfg = self.settings
        schema = response_schema()
        payload = {"model": cfg.model, "messages": context.messages, "format": schema,
                   "stream": False, "truncate": False, "think": cfg.think,
                   "keep_alive": cfg.keep_alive, "options": cfg.options.model_dump()}
        record.update(model=cfg.model, expected_digest=cfg.expected_digest, prompt_version=PROMPT_VERSION,
                      prompt_sha256=context.prompt_sha256, context_sha256=context.context_sha256,
                      schema_sha256=sha(canonical(schema)), request_sha256=sha(canonical(payload)),
                      request=payload, inference_dispatched=False, truncated=False)
        # `format` constrains decoding; it is not text in the chat messages. Count it only
        # if a caller explicitly includes schema text in a message. Never truncate context.
        upper_bound = (sum(len(m["content"].encode("utf-8")) for m in context.messages)
                       + cfg.context_overhead_tokens)
        record["input_token_upper_bound"] = upper_bound
        record["context_budget_version"] = "message-bytes-v2"
        record["validation_version"] = "literal-provenance-v1"
        record["lifecycle_version"] = "persistent-dispatch-v2"
        if upper_bound + cfg.options.num_predict > cfg.options.num_ctx:
            raise OperationalFailure("context_limit", "Full context and output reserve exceed conservative token budget", "context")
        with self.gate_factory() as gate:
            client = self.transport_factory()
            record["ollama_version"] = client.json("version")
            before = self._state(client)
            record["model_state_before"] = before
            record["installed_digest"] = before["model"]["digest"]
            show = client.json("show", {"model": cfg.model})
            if not any(v is False for v in show.get("thinking", {}).get("values", [])):
                raise OperationalFailure("thinking_mode_unsupported", "Installed model does not advertise think=false")
            record["thinking_supported"] = show.get("thinking")
            try:
                memory = self.sampler()
            except Exception as exc:
                raise OperationalFailure("resource_monitor_unavailable", str(exc), "resources") from exc
            record["resources_before"] = memory
            resident = before["residents"]
            # Recreating a differently configured KV cache needs the unloaded reserve.
            warm = (bool(resident) and resident[0].get("context_length") == cfg.options.num_ctx
                    and resident[0].get("size_vram", 0) == 0)
            reserve = cfg.loaded_growth_reserve_bytes if warm else cfg.unloaded_reserve_bytes
            needed = cfg.minimum_margin_bytes + reserve
            record["required_available_bytes"] = needed
            if min(memory["available_bytes"], memory["commit_available_bytes"]) < needed:
                raise OperationalFailure("insufficient_memory", "RAM/commit cannot preserve required load reserve and >=2 GiB margin", "resources")
            expired = threading.Event()

            def deadline_cancel():
                expired.set()
                client.cancel()

            timer = threading.Timer(cfg.timeout_seconds, deadline_cancel)
            timer.daemon = True
            start = time.monotonic()
            failure = None
            response = None
            with ResourceMonitor(self.sampler, client.cancel, cfg.minimum_margin_bytes) as monitor:
                try:
                    if monitor.violated:
                        raise OperationalFailure("resource_monitor_failure", "Resource margin/monitor failed before dispatch", "resources")
                    latest = monitor.samples[-1]
                    if min(latest["available_bytes"], latest["commit_available_bytes"]) < needed:
                        raise OperationalFailure("insufficient_memory", "Load reserve lost before dispatch", "resources")
                    timer.start()
                    gate.start(record["request_sha256"])
                    record["inference_dispatched"] = True
                    record["lifecycle_state"] = "dispatch_attempted"
                    response = client.json("chat", payload)
                    record["response"] = response
                    if response.get("done") is not True:
                        record["truncated"] = True
                        raise OperationalFailure("truncated_response", "No terminal server acknowledgement", "response")
                    gate.complete()
                    record["lifecycle_state"] = "server_finished"
                except Exception as exc:
                    failure = exc
                finally:
                    if record["inference_dispatched"] and getattr(client, "last_response", None) is not None:
                        record["transport_response"] = client.last_response
                    timer.cancel()
                    if timer.ident is not None:
                        timer.join(timeout=2)
            record["resources"] = monitor.summary()
            record["inference_seconds"] = time.monotonic() - start
            if monitor.violated:
                failure = OperationalFailure("resource_margin_violation", "RAM/commit margin or monitor failed; request cancelled", "resources")
            elif expired.is_set():
                failure = OperationalFailure("timeout", "Absolute request deadline exceeded")
            if failure:
                if record["inference_dispatched"]:
                    gate.block(getattr(failure, "code", "interrupted_inference"))
                    record["circuit_blocked"] = True
                    record["lifecycle_state"] = "interrupted"
                raise failure
            after = self._state(client)
            record["model_state_after"] = after
            if not after["residents"] or any(m.get("context_length") != cfg.options.num_ctx or m.get("size_vram", 0) != 0
                                               for m in after["residents"]):
                raise OperationalFailure("effective_state_mismatch", "Could not verify CPU/context effective state")
            record["effective_options_verification"] = "digest/context/CPU checked; sampling options recorded as requested (API does not echo them)"
            record["thinking_observed"] = bool(response.get("message", {}).get("thinking"))
            record["truncated"] = response.get("done") is not True or response.get("done_reason") != "stop"
            if record["thinking_observed"]:
                raise OperationalFailure("unexpected_thinking", "Nonempty thinking despite think=false")
            if record["truncated"]:
                raise OperationalFailure("truncated_response", "Response incomplete or output limit reached", "response")
            if response.get("model") != cfg.model:
                raise OperationalFailure("response_model_mismatch", "Unexpected response model")
            if response.get("message", {}).get("tool_calls"):
                raise OperationalFailure("unexpected_tool_call", "Tools are forbidden")
            counts = [response.get("prompt_eval_count"), response.get("eval_count")]
            if any(type(v) is not int or v < 0 for v in counts):
                raise OperationalFailure("missing_token_counts", "Cannot verify tokenizer budget")
            record["actual_prompt_tokens"], record["actual_output_tokens"] = counts
            record["metrics"] = {key: response.get(key) for key in (
                "total_duration", "load_duration", "prompt_eval_count", "prompt_eval_duration", "eval_count", "eval_duration")}
            if sum(counts) > cfg.options.num_ctx or counts[1] > cfg.options.num_predict:
                record["truncated"] = True
                raise OperationalFailure("context_limit", "Actual token budget exceeded")
            return response

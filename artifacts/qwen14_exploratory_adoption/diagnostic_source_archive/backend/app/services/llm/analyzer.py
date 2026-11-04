"""Cliente de análisis contra la API local de Ollama.

Cada llamada produce un ``AnalysisRecord`` completo, haya o no error:
la respuesta cruda se conserva y los fallos de transporte, JSON o esquema
se registran sin reintentos automáticos.
"""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Protocol

from pydantic import ValidationError

from app.schemas.llm_analysis import SCHEMA_VERSION, AnalysisResult, analysis_json_schema
from app.services.llm.prompt import PromptTemplate

DEFAULT_HOST = "http://127.0.0.1:11434"


class ChatClient(Protocol):
    """Subconjunto de ``ollama.Client`` que se usa (permite sustituirlo en pruebas)."""

    def chat(self, **kwargs: Any) -> Any: ...


@dataclass
class AnalysisRecord:
    model: str
    prompt_id: str
    prompt_sha256: str
    schema_version: str
    options: dict[str, Any]
    started_at: str
    wall_seconds: float
    raw_content: str | None = None
    done_reason: str | None = None
    json_valid: bool = False
    schema_valid: bool = False
    result: dict[str, Any] | None = None
    error_type: str | None = None
    error_message: str | None = None
    metrics: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def parsed(self) -> AnalysisResult | None:
        return AnalysisResult.model_validate(self.result) if self.result is not None else None


_METRIC_FIELDS = (
    "total_duration",
    "load_duration",
    "prompt_eval_count",
    "prompt_eval_duration",
    "eval_count",
    "eval_duration",
)


def _field(response: Any, name: str) -> Any:
    if isinstance(response, dict):
        return response.get(name)
    return getattr(response, name, None)


def _message_content(response: Any) -> str | None:
    message = _field(response, "message")
    if message is None:
        return None
    if isinstance(message, dict):
        return message.get("content")
    return getattr(message, "content", None)


class OllamaAnalyzer:
    def __init__(
        self,
        client: ChatClient,
        model: str,
        prompt: PromptTemplate,
        options: dict[str, Any],
        keep_alive: str | None = None,
    ) -> None:
        self.client = client
        self.model = model
        self.prompt = prompt
        self.options = dict(options)
        self.keep_alive = keep_alive
        self.schema = analysis_json_schema()

    def analyze(self, script: str) -> AnalysisRecord:
        record = AnalysisRecord(
            model=self.model,
            prompt_id=self.prompt.prompt_id,
            prompt_sha256=self.prompt.sha256,
            schema_version=SCHEMA_VERSION,
            options=dict(self.options),
            started_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
            wall_seconds=0.0,
        )
        start = time.perf_counter()
        try:
            messages = self.prompt.build_messages(script)
            kwargs: dict[str, Any] = {
                "model": self.model,
                "messages": messages,
                "format": self.schema,
                "options": self.options,
                "stream": False,
            }
            if self.keep_alive is not None:
                kwargs["keep_alive"] = self.keep_alive
            response = self.client.chat(**kwargs)
        except Exception as exc:  # transporte, modelo ausente, delimitadores, etc.
            record.wall_seconds = round(time.perf_counter() - start, 3)
            record.error_type = type(exc).__name__
            record.error_message = str(exc)
            return record
        record.wall_seconds = round(time.perf_counter() - start, 3)

        record.raw_content = _message_content(response)
        record.done_reason = _field(response, "done_reason")
        record.metrics = {name: _field(response, name) for name in _METRIC_FIELDS}
        _validate_into(record)
        return record


def _validate_into(record: AnalysisRecord) -> None:
    """Parsea y valida ``raw_content``; registra el primer fallo encontrado."""
    if not record.raw_content:
        record.error_type = "EmptyResponse"
        record.error_message = "El modelo devolvió contenido vacío."
        return
    try:
        data = json.loads(record.raw_content)
    except json.JSONDecodeError as exc:
        record.error_type = "JSONDecodeError"
        record.error_message = str(exc)
        return
    record.json_valid = True
    try:
        result = AnalysisResult.model_validate(data)
    except ValidationError as exc:
        record.error_type = "SchemaValidationError"
        record.error_message = str(exc)
        return
    record.schema_valid = True
    record.result = result.model_dump(mode="json")

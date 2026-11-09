"""Synchronous, stateless orchestration reusable by CLI and a future API worker."""
from __future__ import annotations

import time
from datetime import datetime, timezone
from uuid import uuid4

from app.schemas.deobfuscation import DeobfuscationLimits
from app.schemas.pipeline import ComparisonResult, PipelineError, PipelineResult
from app.services.behavior_detection.engine import analyze_behaviors
from app.services.deobfuscation.engine import deobfuscate
from app.services.pipelines.config import PipelineSettings
from app.services.pipelines.context import build_context, sha
from app.services.pipelines.ollama import OllamaAdapter
from app.services.pipelines.provider import InferenceAdapter
from app.services.pipelines.resources import OperationalFailure
from app.services.pipelines.validation import validate_report

STATIC_LIMITATION = "Static subset only; no execution/effect/safety guarantee. Unsupported syntax can hide behavior."
LLM_LIMITATION = "Provisional LLM. Schema and literal evidence checks do not certify semantic support or risk correctness."


class AnalysisService:
    def __init__(self, settings: PipelineSettings | None = None, *, adapter: InferenceAdapter | None = None,
                 strategy=None):
        self.settings = settings or PipelineSettings()
        # Optional deterministic layers around the LLM (see strategy.py). None keeps v1 behavior.
        self.strategy = strategy
        if adapter is not None and hasattr(adapter, "settings") and adapter.settings != self.settings:
            raise ValueError("Service and adapter settings must match")
        self.adapter = adapter or OllamaAdapter(self.settings)

    def status(self):
        return self.adapter.status()

    def analyze(self, script: str, configuration: str) -> PipelineResult:
        if configuration not in {"A", "B", "C"}:
            raise ValueError("configuration must be A, B or C")
        start = time.monotonic()
        data = dict(run_id=str(uuid4()), configuration=configuration, status="completed",
                    started_at=datetime.now(timezone.utc).isoformat(), duration_seconds=0,
                    limitations=[STATIC_LIMITATION], engine_versions={"orchestrator": "pipeline-v1"}, operational={})
        stage = "input"
        try:
            if not isinstance(script, str):
                raise OperationalFailure("invalid_input", "Input must be Unicode text", "input")
            if len(script) > self.settings.max_input_bytes:
                raise OperationalFailure("input_too_large", "Input exceeds byte limit", "input")
            try:
                raw = script.encode("utf-8")
            except UnicodeError as exc:
                raise OperationalFailure("invalid_unicode", "Unpaired Unicode surrogate", "input") from exc
            if not raw or not script.strip():
                raise OperationalFailure("empty_input", "Input is empty", "input")
            if len(raw) > self.settings.max_input_bytes:
                raise OperationalFailure("input_too_large", "UTF-8 input exceeds byte limit", "input")
            data.update(original=script, input_sha256=sha(script))
            limits = DeobfuscationLimits(max_input_bytes=self.settings.max_input_bytes)
            if configuration == "A":
                stage = "deterministic"
                result = analyze_behaviors(script, input_provenance="original", deobfuscation_limits=limits)
                data.update(deterministic=result, deobfuscation=result.deobfuscation,
                            status="completed" if result.status == "complete" else result.status)
                data["engine_versions"].update(deobfuscator=result.deobfuscation.engine_version, detector=result.ruleset_version)
                data["limitations"].extend(result.warnings)
            else:
                data["limitations"].append(LLM_LIMITATION)
                stage = "deobfuscation"
                deob = deobfuscate(script, input_provenance="original", limits=limits) if configuration == "C" else None
                if deob:
                    data["deobfuscation"] = deob
                    data["engine_versions"]["deobfuscator"] = deob.engine_version
                    if deob.status == "rejected":
                        raise OperationalFailure("deobfuscation_rejected", "Deterministic recovery rejected input", stage)
                stage = "context"
                context = self.strategy.build_context(script, deob) if self.strategy else build_context(script, deob)
                data["engine_versions"]["llm_contract"] = "application-report-v1"
                if self.strategy:
                    data["engine_versions"].update(self.strategy.versions())
                stage = getattr(self.adapter, "provider", "ollama")
                response = self.adapter.infer(context, data["operational"])
                stage = "response"
                content = response.get("message", {}).get("content")
                if not isinstance(content, str) or not content.strip():
                    raise OperationalFailure("empty_response", "Missing model JSON", "response")
                report, evidence = validate_report(content, context)
                if self.strategy:
                    stage = "evidence_check"
                    report, evidence, notes = self.strategy.post_validate(report, evidence, context, data["operational"])
                    data["limitations"].extend(notes)
                data.update(llm=report, evidence=evidence, risk_label=report.risk_label, risk_rationale=report.risk_rationale)
                data["limitations"].extend(report.limitations)
                if deob and deob.status == "partial":
                    data["status"] = "partial"
        except Exception as exc:
            error_stage = getattr(exc, "stage", stage)
            code = getattr(exc, "code", "invalid_response" if stage == "response" else "internal_error")
            unavailable = {"ollama_unavailable", "model_missing", "digest_mismatch", "other_model_loaded", "insufficient_memory",
                           "resource_monitor_unavailable", "resource_monitor_failure", "resource_margin_violation", "inference_busy",
                           "inference_interrupted", "thinking_mode_unsupported"}
            data["status"] = "rejected" if error_stage == "input" else ("unavailable" if code in unavailable else "error")
            data["errors"] = [PipelineError(code=code, message=str(exc)[:4000], stage=error_stage)]
        data["duration_seconds"] = time.monotonic() - start
        return PipelineResult(**data)

    def compare(self, script: str) -> ComparisonResult:
        # Separate calls: C never consumes the A result or the B conversation/response.
        return ComparisonResult(results=[self.analyze(script, c) for c in ("A", "B", "C")])

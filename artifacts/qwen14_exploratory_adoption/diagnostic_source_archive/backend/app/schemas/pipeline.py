"""Application contracts, separate from the frozen pilot schemas."""
from __future__ import annotations

import hashlib
from typing import Any, Literal

from pydantic import Field, model_validator

from app.schemas.behavior_detection import BehaviorAnalysisResult
from app.schemas.deobfuscation import DeobfuscationResult, SourceSpan, StrictModel
from app.schemas.llm_analysis import BehaviorId, Level, ObfuscationTechnique, RiskLabel


class Citation(StrictModel):
    source_id: str = Field(min_length=1, max_length=80)
    snippet: str = Field(min_length=1, max_length=4096)


class ModelFinding(StrictModel):
    behavior_id: BehaviorId
    explanation: str = Field(min_length=1, max_length=2000)
    evidence: list[Citation] = Field(min_length=1, max_length=16)
    confidence: Level


class ModelUncertainty(StrictModel):
    level: Level
    uninterpretable_fragments: list[str] = Field(max_length=32)
    notes: str = Field(min_length=1, max_length=2000)


class InjectionAssessment(StrictModel):
    detected: bool = Field(strict=True)
    snippets: list[str] = Field(max_length=16)
    notes: str = Field(min_length=1, max_length=2000)


class ModelReport(StrictModel):
    obfuscation_techniques: list[ObfuscationTechnique] = Field(max_length=6)
    recovered_content: list[str] = Field(max_length=16, description="Model reconstructions, NOT verified evidence.")
    behaviors: list[ModelFinding] = Field(max_length=7)
    risk_label: RiskLabel
    risk_rationale: str = Field(min_length=1, max_length=2000)
    uncertainty: ModelUncertainty
    prompt_injection: InjectionAssessment
    limitations: list[str] = Field(max_length=32)

    @model_validator(mode="after")
    def coherent(self):
        labels = [f.behavior_id for f in self.behaviors]
        if len(labels) != len(set(labels)):
            raise ValueError("Duplicate behavior IDs")
        if len(self.obfuscation_techniques) != len(set(self.obfuscation_techniques)):
            raise ValueError("Duplicate obfuscation techniques")
        if self.risk_label == RiskLabel.HIGH_RISK and len(labels) < 2:
            raise ValueError("high_risk requires a supported combination, never obfuscation alone")
        if self.risk_label == RiskLabel.BENIGN and (
            self.uncertainty.level != Level.LOW or self.uncertainty.uninterpretable_fragments
        ):
            raise ValueError("Unknown behavior cannot be declared benign")
        if self.prompt_injection.detected != bool(self.prompt_injection.snippets):
            raise ValueError("Injection assessment must provide literal snippets when detected")
        return self


class ValidatedEvidence(StrictModel):
    behavior_id: BehaviorId
    source_id: str
    snippet: str
    start: int = Field(ge=0)
    end: int = Field(ge=0)
    line: int = Field(ge=1)
    column: int = Field(ge=1)
    provenance: Literal["original", "deobfuscator_recovered"]
    root_source: SourceSpan | None = None
    transformation_id: str | None = None
    validation: Literal["literal_only_semantics_unverified"] = "literal_only_semantics_unverified"


class PipelineError(StrictModel):
    code: str
    message: str
    stage: str


class PipelineResult(StrictModel):
    schema_version: Literal["pipeline-v1"] = "pipeline-v1"
    run_id: str
    configuration: Literal["A", "B", "C"]
    status: Literal["completed", "partial", "rejected", "unavailable", "error"]
    input_sha256: str | None = None
    original: str | None = None
    started_at: str
    duration_seconds: float = Field(ge=0)
    engine_versions: dict[str, str] = Field(default_factory=dict)
    deobfuscation: DeobfuscationResult | None = None
    deterministic: BehaviorAnalysisResult | None = None
    llm: ModelReport | None = None
    llm_review_status: Literal["unreviewed_model_claims"] = "unreviewed_model_claims"
    evidence: list[ValidatedEvidence] = Field(default_factory=list)
    risk_label: RiskLabel = RiskLabel.UNKNOWN
    risk_rationale: str = "Deterministic behavior does not establish intent or safety."
    limitations: list[str] = Field(default_factory=list)
    errors: list[PipelineError] = Field(default_factory=list)
    operational: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def attribution(self):
        if self.configuration == "A" and (self.llm is not None or self.evidence or self.risk_label != RiskLabel.UNKNOWN):
            raise ValueError("A cannot contain LLM claims or risk decisions")
        if self.configuration != "A" and self.deterministic is not None:
            raise ValueError("B/C cannot contain detector decisions")
        if self.configuration == "B" and self.deobfuscation is not None:
            raise ValueError("B cannot contain deobfuscation")
        if self.llm is None and (self.evidence or self.risk_label != RiskLabel.UNKNOWN):
            raise ValueError("Failed inference cannot publish findings/risk")
        if self.status in {"error", "unavailable", "rejected"} and not self.errors:
            raise ValueError("Failed execution requires a structured error")
        if self.status in {"error", "unavailable", "rejected"} and self.llm is not None:
            raise ValueError("Failed execution cannot publish model findings")
        if self.original is not None and hashlib.sha256(self.original.encode("utf-8")).hexdigest() != self.input_sha256:
            raise ValueError("Original text/hash mismatch")
        if self.deobfuscation is not None and self.deobfuscation.input_sha256 != self.input_sha256:
            raise ValueError("Recovery belongs to another input")
        if self.deterministic is not None and self.deterministic.deobfuscation != self.deobfuscation:
            raise ValueError("A recovery and detection traces must agree")
        if self.status in {"completed", "partial"}:
            if self.configuration == "A" and self.deterministic is None:
                raise ValueError("Successful A requires deterministic result")
            if self.configuration != "A" and self.llm is None:
                raise ValueError("Successful B/C requires a model report")
        if self.llm is not None:
            if self.risk_label != self.llm.risk_label or self.risk_rationale != self.llm.risk_rationale:
                raise ValueError("Risk must retain model attribution")
            expected = [(f.behavior_id, c.source_id, c.snippet) for f in self.llm.behaviors for c in f.evidence]
            if expected != [(e.behavior_id, e.source_id, e.snippet) for e in self.evidence]:
                raise ValueError("Model evidence and validated evidence disagree")
            steps = {t.transformation_id: t for t in self.deobfuscation.transformations} if self.deobfuscation else {}
            for e in self.evidence:
                step = steps.get(e.source_id)
                if e.source_id == "original":
                    text = self.original
                    if e.provenance != "original" or e.transformation_id is not None:
                        raise ValueError("Original evidence has incorrect provenance")
                    if e.root_source is None or (e.root_source.layer_id, e.root_source.start, e.root_source.end) != ("L0", e.start, e.end):
                        raise ValueError("Original evidence root mismatch")
                else:
                    if step is None or not step.deterministic_verified or step.status != "success":
                        raise ValueError("Evidence references unverified recovery")
                    text = step.recovered_text
                    if e.provenance != "deobfuscator_recovered" or e.transformation_id != step.transformation_id or e.root_source != step.root_source:
                        raise ValueError("Recovered evidence root/provenance mismatch")
                if text is None or e.end != e.start + len(e.snippet) or text[e.start:e.end] != e.snippet:
                    raise ValueError("Evidence offsets do not identify the cited text")
                if e.line != text.count("\n", 0, e.start) + 1 or e.column != e.start - text.rfind("\n", 0, e.start):
                    raise ValueError("Evidence line/column mismatch")
        return self


class ComparisonResult(StrictModel):
    schema_version: Literal["comparison-v1"] = "comparison-v1"
    results: list[PipelineResult] = Field(min_length=3, max_length=3)
    quality_metrics_computed: Literal[False] = False

    @model_validator(mode="after")
    def independent(self):
        if [r.configuration for r in self.results] != ["A", "B", "C"]:
            raise ValueError("Comparison requires ordered independent A/B/C results")
        if len({r.run_id for r in self.results}) != 3:
            raise ValueError("Each analysis needs its own run ID")
        if len({r.input_sha256 for r in self.results}) != 1:
            raise ValueError("Comparison inputs must have identical hashes")
        return self

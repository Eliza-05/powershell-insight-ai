"""Versioned deterministic findings; no model confidence or malware/risk verdict."""

from bisect import bisect_right
from typing import Literal

from pydantic import Field, model_validator

from app.schemas.deobfuscation import DeobfuscationResult, Provenance, SourceSpan, StrictModel
from app.schemas.llm_analysis import BehaviorId, ObfuscationTechnique

RuleId = Literal["BD-B01-WEBGET", "BD-B01-WEBCLIENT", "BD-B02-IEX", "BD-B03-RUNWRITE",
                 "BD-B04-DEFENDER-DISABLE", "BD-B04-DEFENDER-EXCLUSION", "BD-B04-FIREWALL-DISABLE",
                 "BD-B05-HOSTQUERY", "BD-B05-RUNQUERY", "BD-B06-HTTP-SEND", "BD-B06-CONNECTIVITY",
                 "BD-B07-STORED-CREDENTIAL"]


class DetectionLimits(StrictModel):
    max_operations: int = Field(default=512, ge=1, le=4096, strict=True)
    max_findings: int = Field(default=256, ge=1, le=2048, strict=True)
    max_indicators: int = Field(default=128, ge=1, le=1024, strict=True)
    max_evidence: int = Field(default=1024, ge=1, le=8192, strict=True)


class AddedOperation(StrictModel):
    """Caller-declared transformation metadata, never inferred from expected labels."""

    operation: Literal["EXEC_WRAPPER_IEX"]
    source: SourceSpan


class DetectionEvidence(StrictModel):
    evidence_id: str
    role: Literal["operation", "argument", "receiver", "execution_input"]
    source: SourceSpan
    root_source: SourceSpan
    fragment: str
    provenance: Provenance
    recovered_value: str | None = None
    transformation_ids: list[str] = Field(default_factory=list)


class BehaviorFinding(StrictModel):
    finding_id: str
    behavior_id: BehaviorId
    rule_id: RuleId
    description: str
    operation_source: SourceSpan
    evidence_ids: list[str] = Field(min_length=1)
    support: Literal["individual", "contextual"]
    conditions: list[str] = Field(min_length=1)
    limitations: list[str] = Field(default_factory=list)


class BehaviorIndicator(StrictModel):
    indicator_id: str
    behavior_id: BehaviorId | None = None
    rule_id: RuleId | None = None
    source: SourceSpan
    reason: str


class BehaviorAnalysisResult(StrictModel):
    schema_version: Literal["behavior-analysis-v1"] = "behavior-analysis-v1"
    ruleset_version: Literal["static-behaviors-v1"] = "static-behaviors-v1"
    status: Literal["complete", "partial", "rejected"]
    coverage_partial: Literal[True] = True
    deobfuscation: DeobfuscationResult
    detection_limits: DetectionLimits
    added_operations: list[AddedOperation] = Field(default_factory=list)
    behaviors: list[BehaviorId] = Field(default_factory=list)
    findings: list[BehaviorFinding] = Field(default_factory=list)
    evidence: list[DetectionEvidence] = Field(default_factory=list)
    indicators: list[BehaviorIndicator] = Field(default_factory=list)
    obstructing_techniques: list[ObfuscationTechnique] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    limits_hit: list[str] = Field(default_factory=list)
    operations_examined: int = Field(ge=0)
    work_units: int = Field(ge=0)
    artifact_bytes: int = Field(ge=0)

    @model_validator(mode="after")
    def coherent(self):
        deob = self.deobfuscation
        if deob.input_provenance not in {"original", "obfuscated_variant"}:
            raise ValueError("Team references are not detection input or engine recoveries.")
        if self.behaviors != sorted({f.behavior_id for f in self.findings}, key=lambda b: b.value):
            raise ValueError("Behavior labels must be derived from supported findings only.")
        if self.status == "rejected":
            if deob.status != "rejected" or self.findings or self.evidence or self.indicators or self.added_operations:
                raise ValueError("Rejected analysis cannot contain evidence or findings.")
            if self.work_units or self.operations_examined or self.artifact_bytes:
                raise ValueError("Rejected analysis cannot claim detection work or artifacts.")
            return self
        if deob.status == "rejected":
            raise ValueError("Rejected deobfuscation cannot be analyzed.")
        if self.status == "complete" and (deob.status != "complete" or self.indicators or self.limits_hit):
            raise ValueError("Complete analysis cannot hide unresolved processing.")
        if (self.work_units > deob.limits.max_work_units or self.artifact_bytes > deob.limits.max_total_artifact_bytes
                or self.operations_examined > self.detection_limits.max_operations
                or len(self.findings) > self.detection_limits.max_findings
                or len(self.indicators) > self.detection_limits.max_indicators
                or len(self.evidence) > self.detection_limits.max_evidence):
            raise ValueError("Detection counters exceed their configured ceilings.")
        layers = {layer.layer_id: layer for layer in deob.layers}
        steps = {step.transformation_id: step for step in deob.transformations}
        line_starts = {key: [0] + [i + 1 for i, c in enumerate(layer.text) if c == "\n"]
                       for key, layer in layers.items()}

        def check(span):
            layer = layers.get(span.layer_id)
            if layer is None or span.end > len(layer.text):
                raise ValueError("Detection span outside its layer.")
            for offset, line, column in [(span.start, span.line, span.column), (span.end, span.end_line, span.end_column)]:
                starts = line_starts[span.layer_id]
                expected_line = bisect_right(starts, offset)
                if line != expected_line or column != offset - starts[expected_line - 1] + 1:
                    raise ValueError("Detection line/column disagree with offsets.")
            return layer

        evidence = {}
        for item in self.evidence:
            layer = check(item.source)
            check(item.root_source)
            if item.evidence_id in evidence or item.fragment != layer.text[item.source.start:item.source.end]:
                raise ValueError("Duplicate evidence or nonliteral source fragment.")
            if item.root_source != (layer.root_source or item.source):
                raise ValueError("Incorrect original-script anchor.")
            if len(set(item.transformation_ids)) != len(item.transformation_ids):
                raise ValueError("Duplicate transformation reference.")
            for tid in item.transformation_ids:
                if tid not in steps or steps[tid].status != "success" or not steps[tid].deterministic_verified:
                    raise ValueError("Evidence references unverified recovery.")
                if tid != layer.parent_transformation_id and not (
                    steps[tid].source.layer_id == item.source.layer_id and
                    item.source.start <= steps[tid].source.start <= steps[tid].source.end <= item.source.end
                ):
                    raise ValueError("Evidence cites an unrelated transformation.")
            if layer.parent_transformation_id and layer.parent_transformation_id not in item.transformation_ids:
                raise ValueError("Derived evidence must cite its producing transformation.")
            if item.recovered_value is not None:
                if not any(steps[tid].recovered_text == item.recovered_value and
                           steps[tid].source.layer_id == item.source.layer_id and
                           item.source.start <= steps[tid].source.start <= steps[tid].source.end <= item.source.end
                           for tid in item.transformation_ids):
                    raise ValueError("Recovered value is not backed by a local transformation.")
            expected_origin = "deobfuscator_recovered" if item.recovered_value is not None or layer.depth else layer.provenance
            if item.provenance != expected_origin:
                raise ValueError("Evidence provenance disagrees with its actual source.")
            evidence[item.evidence_id] = item
        ids, operations = set(), set()
        used = set()
        for finding in self.findings:
            check(finding.operation_source)
            if not finding.rule_id.startswith(f"BD-{finding.behavior_id.value}-"):
                raise ValueError("Rule and behavior do not agree.")
            key = (finding.behavior_id, finding.operation_source.layer_id,
                   finding.operation_source.start, finding.operation_source.end)
            if finding.finding_id in ids or key in operations:
                raise ValueError("Duplicate finding/operation.")
            if len(set(finding.evidence_ids)) != len(finding.evidence_ids) or not set(finding.evidence_ids) <= evidence.keys():
                raise ValueError("Duplicate or unknown finding evidence.")
            if not any(evidence[eid].role == "operation" and evidence[eid].source == finding.operation_source
                       for eid in finding.evidence_ids):
                raise ValueError("Finding lacks its operation evidence.")
            if any(evidence[eid].source.layer_id != finding.operation_source.layer_id or
                   not (finding.operation_source.start <= evidence[eid].source.start <=
                        evidence[eid].source.end <= finding.operation_source.end) for eid in finding.evidence_ids):
                raise ValueError("Finding context must belong to that invocation, not another operation.")
            if finding.support != ("individual" if len(finding.evidence_ids) == 1 else "contextual"):
                raise ValueError("Support kind must match the cited evidence set.")
            ids.add(finding.finding_id)
            operations.add(key)
            used.update(finding.evidence_ids)
        if used != evidence.keys():
            raise ValueError("Unreferenced evidence must not masquerade as finding support.")
        indicator_ids = set()
        for item in self.indicators:
            check(item.source)
            if item.rule_id and (item.behavior_id is None or not item.rule_id.startswith(f"BD-{item.behavior_id.value}-")):
                raise ValueError("Indicator rule and behavior do not agree.")
            if item.indicator_id in indicator_ids:
                raise ValueError("Duplicate indicator.")
            indicator_ids.add(item.indicator_id)
        for item in self.added_operations:
            check(item.source)
        return self

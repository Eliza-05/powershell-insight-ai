"""Versioned contracts for deterministic textual recovery, independent of the LLM."""

from __future__ import annotations

import base64
import binascii
import hashlib
from bisect import bisect_right
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.schemas.llm_analysis import ObfuscationTechnique

InputProvenance = Literal["original", "obfuscated_variant", "reference_manual", "reference_decoded"]
Provenance = Literal["original", "obfuscated_variant", "reference_manual", "reference_decoded", "deobfuscator_recovered"]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class DeobfuscationLimits(StrictModel):
    # Hard ceilings also apply to caller-supplied configurations.
    max_input_bytes: int = Field(default=1_048_576, ge=1, le=4_194_304, strict=True)
    max_artifact_bytes: int = Field(default=262_144, ge=1, le=1_048_576, strict=True)
    max_total_artifact_bytes: int = Field(default=2_097_152, ge=1, le=8_388_608, strict=True)
    max_transformations: int = Field(default=512, ge=1, le=4096, strict=True)
    max_depth: int = Field(default=3, ge=0, le=8, strict=True)
    max_expression_depth: int = Field(default=24, ge=1, le=48, strict=True)
    max_concat_terms: int = Field(default=128, ge=2, le=1024, strict=True)
    max_tokens: int = Field(default=50_000, ge=1, le=200_000, strict=True)
    max_work_units: int = Field(default=4_000_000, ge=1, le=16_000_000, strict=True)
    max_unresolved: int = Field(default=128, ge=1, le=1024, strict=True)


class SourceSpan(StrictModel):
    layer_id: str
    start: int = Field(ge=0)
    end: int = Field(ge=0)
    line: int = Field(ge=1)
    column: int = Field(ge=1)
    end_line: int = Field(ge=1)
    end_column: int = Field(ge=1)

    @model_validator(mode="after")
    def ordered(self):
        if self.end < self.start or (self.end_line, self.end_column) < (self.line, self.column):
            raise ValueError("Source span must be ordered (end exclusive).")
        return self


class SourceLayer(StrictModel):
    layer_id: str
    source_name: str = Field(max_length=1024)
    provenance: Provenance
    text: str
    depth: int = Field(ge=0)
    parent_transformation_id: str | None = None
    root_source: SourceSpan | None = None


class Transformation(StrictModel):
    transformation_id: str
    technique: ObfuscationTechnique
    source: SourceSpan
    root_source: SourceSpan
    original_fragment: str
    provenance: Literal["deobfuscator_recovered"] = "deobfuscator_recovered"
    recovery_kind: Literal["script_text", "string", "bytes", "variable_definition", "variable_use", "unresolved"]
    recovered_text: str | None = None
    recovered_bytes_base64: str | None = None
    dependencies: list[str] = Field(default_factory=list)
    status: Literal["success", "partial", "failed", "unsupported"]
    deterministic_verified: bool
    warnings: list[str] = Field(default_factory=list)
    added_operation: Literal["LAUNCHER_ENCCMD"] | None = None
    output_layer_id: str | None = None

    @model_validator(mode="after")
    def coherent(self):
        if self.recovered_text is not None and self.recovered_bytes_base64 is not None:
            raise ValueError("A recovery contains text or bytes, never both.")
        if self.status in {"failed", "unsupported"} and (
            self.deterministic_verified or self.recovered_text is not None or self.recovered_bytes_base64 is not None
        ):
            raise ValueError("Unresolved transformations cannot claim recovered content.")
        if self.status == "success" and (not self.deterministic_verified or self.recovered_text is None):
            raise ValueError("Successful textual recovery requires verified text.")
        if self.status == "partial":
            if self.recovery_kind != "bytes" or not self.deterministic_verified or self.recovered_bytes_base64 is None:
                raise ValueError("Partial byte recovery requires verified bytes with an explicit byte kind.")
            try:
                base64.b64decode(self.recovered_bytes_base64, validate=True)
            except (ValueError, binascii.Error) as error:
                raise ValueError("Recovered bytes must be valid standard Base64.") from error
        return self


class UnresolvedFragment(StrictModel):
    source: SourceSpan
    technique_hint: ObfuscationTechnique | None = None
    reason: str
    transformation_id: str | None = None


class DeobfuscationResult(StrictModel):
    schema_version: Literal["deobfuscation-v1"] = "deobfuscation-v1"
    engine_version: Literal["static-subset-v1"] = "static-subset-v1"
    input_sha256: str | None
    source_name: str = Field(max_length=1024)
    input_provenance: InputProvenance
    status: Literal["complete", "partial", "rejected"]
    semantic_equivalence: Literal["not_claimed"] = "not_claimed"
    limits: DeobfuscationLimits
    layers: list[SourceLayer] = Field(default_factory=list)
    transformations: list[Transformation] = Field(default_factory=list)
    unresolved: list[UnresolvedFragment] = Field(default_factory=list)
    techniques_detected: list[ObfuscationTechnique] = Field(default_factory=list)
    limits_hit: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    work_units: int = Field(ge=0)
    artifact_bytes: int = Field(ge=0)

    @model_validator(mode="after")
    def trace_is_consistent(self):
        layers = {layer.layer_id: layer for layer in self.layers}
        if len(layers) != len(self.layers):
            raise ValueError("Duplicate source layer ID.")
        if self.status == "rejected":
            if self.layers or self.transformations:
                raise ValueError("Rejected input must not copy layers or transformations.")
            return self
        if self.status == "complete" and (self.unresolved or self.limits_hit):
            raise ValueError("Complete results cannot contain unresolved work or reached limits.")
        if not self.layers or self.layers[0].layer_id != "L0":
            raise ValueError("The original layer must be L0.")
        original = self.layers[0]
        if (original.provenance != self.input_provenance or original.depth != 0
                or original.parent_transformation_id is not None or original.root_source is not None):
            raise ValueError("Invalid original-layer provenance.")
        if hashlib.sha256(original.text.encode("utf-8")).hexdigest() != self.input_sha256:
            raise ValueError("Input hash does not match the original layer.")
        starts = {key: [0] + [i + 1 for i, c in enumerate(layer.text) if c == "\n"] for key, layer in layers.items()}

        def check_span(span):
            if span.layer_id not in layers or span.end > len(layers[span.layer_id].text):
                raise ValueError("Source span outside its layer.")
            lines = starts[span.layer_id]
            line, end_line = bisect_right(lines, span.start), bisect_right(lines, span.end)
            if (span.line, span.column, span.end_line, span.end_column) != (
                line, span.start - lines[line - 1] + 1, end_line, span.end - lines[end_line - 1] + 1
            ):
                raise ValueError("Line/column do not match the source offsets.")

        steps: dict[str, Transformation] = {}
        for step in self.transformations:
            if step.transformation_id in steps or not set(step.dependencies) <= steps.keys():
                raise ValueError("Duplicate transformation or forward/cyclic dependency.")
            check_span(step.source)
            check_span(step.root_source)
            layer = layers[step.source.layer_id]
            if step.root_source.layer_id != "L0" or step.root_source != (layer.root_source or step.source):
                raise ValueError("Incorrect root anchor; decoded text is not original text.")
            if layer.parent_transformation_id and layer.parent_transformation_id not in step.dependencies:
                raise ValueError("Decoded-layer transformation must depend on its parent.")
            if step.original_fragment != layer.text[step.source.start:step.source.end]:
                raise ValueError("Transformation fragment is not an exact source slice.")
            if step.output_layer_id:
                child = layers.get(step.output_layer_id)
                if (child is None or child.parent_transformation_id != step.transformation_id
                        or child.text != step.recovered_text or child.depth != layer.depth + 1):
                    raise ValueError("Output layer does not match its producing transformation.")
            steps[step.transformation_id] = step
        for layer in self.layers[1:]:
            parent = steps.get(layer.parent_transformation_id)
            if (parent is None or parent.output_layer_id != layer.layer_id or layer.root_source != parent.root_source
                    or layer.provenance != "deobfuscator_recovered"):
                raise ValueError("Orphan or incorrectly attributed recovered layer.")
        for item in self.unresolved:
            check_span(item.source)
            if item.transformation_id is not None and item.transformation_id not in steps:
                raise ValueError("Unresolved item references an unknown transformation.")
        if not {t.technique for t in self.transformations} <= set(self.techniques_detected):
            raise ValueError("Transformation technique is missing from the detection list.")
        return self

    def recovered_texts(self) -> dict[str, str]:
        """Adapter for literal_check.locate; keys retain engine provenance and trace IDs."""
        return {f"deobfuscator_recovered:{t.transformation_id}": t.recovered_text
                for t in self.transformations if t.recovered_text is not None and t.deterministic_verified}

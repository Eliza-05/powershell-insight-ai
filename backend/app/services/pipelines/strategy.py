"""Policy v2 and conservative deterministic layers, shared by B and C.

The former R7 postcheck was exploratory and developed on selection responses.
This revised subset requires independent evaluation; no previous F1 applies to it.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
import hashlib
from pathlib import Path

from app.services.pipelines import evidence_check, sanitize
from app.services.pipelines.context import build_context, canonical, sha
from app.services.pipelines.resources import OperationalFailure
from app.services.pipelines.validation import validate_report

POLICY_V2_PATH = Path(__file__).with_name("policy_v2.md")
POLICY_V2_SHA256 = "53d4cc36ca6b19dd5630065aabb0bd3d0a6f6627eb946989d32d6f773f10c081"
NAME = "v2-deterministic-layers-2"


@dataclass(frozen=True, init=False)
class DeterministicLayersStrategy:
    policy_path: Path
    policy_text: str
    policy_sha256: str
    policy_bytes_sha256: str

    def __init__(self, policy_path: Path = POLICY_V2_PATH, expected_policy_sha256: str = POLICY_V2_SHA256):
        raw = Path(policy_path).read_bytes()
        text = raw.decode("utf-8").replace("\r\n", "\n").replace("\r", "\n")
        if sha(text) != expected_policy_sha256:
            raise ValueError("Policy v2 differs from the authorized text; refusing a silent variant")
        object.__setattr__(self, "policy_path", Path(policy_path))
        object.__setattr__(self, "policy_text", text)
        object.__setattr__(self, "policy_sha256", sha(text))
        object.__setattr__(self, "policy_bytes_sha256", hashlib.sha256(raw).hexdigest())

    def versions(self):
        return {"strategy": NAME, "policy": "policy-v2-lab@" + self.policy_sha256,
                "policy_bytes_sha256": self.policy_bytes_sha256,
                "preprocess": sanitize.VERSION, "postcheck": evidence_check.VERSION}

    def build_context(self, script, deobfuscation):
        records = []

        def preprocess(text):
            result = sanitize.sanitize_comments(text)
            records.append({"source_text_sha256": sha(text), "comment_spans": list(result.spans),
                            "diagnostics": list(result.diagnostics),
                            "coverage": "partial_or_opaque" if result.diagnostics else "lexical_subset"})
            return result.text

        context = build_context(script, deobfuscation, policy_text=self.policy_text, preprocess=preprocess)
        for item in records:
            item["source_ids"] = [key for key, value in context.sources.items() if sha(value) == item["source_text_sha256"]]
        return replace(context, preprocessing=tuple(records))

    def prepare_record(self, context, record):
        record["policy_integrity"] = {"text_sha256": self.policy_sha256,
            "loaded_bytes_sha256": self.policy_bytes_sha256, "mode": "validated_immutable_snapshot"}
        record["preprocessing"] = {"version": sanitize.VERSION, "sources": list(context.preprocessing)}
        notes = [evidence_check.LIMITATION]
        if any(item["diagnostics"] for item in context.preprocessing):
            notes.append("Sanitizacion parcial o region opaca: se conserva el texto incierto. "
                    "Pueden quedar comentarios visibles; ver operational.preprocessing. "
                    "Esta capa no es proteccion universal contra prompt injection.")
        return notes

    def post_validate(self, report, evidence, context, record):
        record["model_report_before_evidence_check"] = report.model_dump(mode="json")
        record["model_behaviors_before_evidence_check"] = [
            {"behavior_id": f.behavior_id.value,
             "evidence": [c.model_dump(mode="json") for c in f.evidence]} for f in report.behaviors]
        try:
            checked, decisions = evidence_check.verify(report, evidence, context.sources)
        except evidence_check.IncoherentEvidence as exc:
            record["evidence_check"] = {"version": evidence_check.VERSION,
                "decisions": exc.decisions, "changes": [d for d in exc.decisions if d["action"] != "kept"],
                "candidate_behavior_ids": exc.final_ids, "status": "rejected_incoherent",
                "risk_preserved_from_model": report.risk_label.value, "error": str(exc)[:500],
                "limitations": [evidence_check.LIMITATION]}
            raise OperationalFailure("evidence_check_incoherent",
                "Conservative evidence filtering conflicts with the model risk contract; "
                "raw report and all decisions preserved in operational. " + str(exc)[:500], "evidence_check") from exc
        changes = [d for d in decisions if d["action"] != "kept"]
        record["evidence_check"] = {"version": evidence_check.VERSION, "decisions": decisions,
            "changes": changes, "final_behavior_ids": [f.behavior_id.value for f in checked.behaviors],
            "status": "filtered" if changes else "unchanged",
            "risk_preserved_from_model": report.risk_label.value, "limitations": [evidence_check.LIMITATION]}
        if changes:
            checked, evidence = validate_report(canonical(checked.model_dump(mode="json")), context)
        notes = []
        if changes:
            notes.append("Verificador determinista: etiquetas no verificadas descartadas. El riesgo sigue siendo "
                         "el que asigno el modelo y puede citar comportamientos descartados; "
                         "ver operational.evidence_check y model_report_before_evidence_check.")
        return checked, evidence, notes

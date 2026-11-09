"""Strategy "v2 + capas deterministas": policy v2, comment blanking before the LLM and an
evidence check after it. Same strategy for B and C (only the 1A context differs).

Lab evidence (exploratory, not an independent evaluation): qwen3-coder:30b + policy v2 +
comment blanking obeyed 0/8 comment injections (v2 alone: 3/4 on development); the evidence
check raised selection F1 from 0.78 to 0.87 on the same answers it was written from.
"""
from __future__ import annotations

from pathlib import Path

from app.services.pipelines import evidence_check, sanitize
from app.services.pipelines.context import build_context, canonical, sha
from app.services.pipelines.resources import OperationalFailure
from app.services.pipelines.validation import validate_report

POLICY_V2_PATH = Path(__file__).with_name("policy_v2.md")
POLICY_V2_SHA256 = "53d4cc36ca6b19dd5630065aabb0bd3d0a6f6627eb946989d32d6f773f10c081"
NAME = "v2-deterministic-layers-1"


class DeterministicLayersStrategy:
    def __init__(self, policy_path: Path = POLICY_V2_PATH, expected_policy_sha256: str = POLICY_V2_SHA256):
        text = Path(policy_path).read_text(encoding="utf-8")
        if sha(text) != expected_policy_sha256:
            raise ValueError("Policy v2 differs from the frozen text; refusing to run a silent variant")
        self.policy_path = Path(policy_path)

    def versions(self):
        return {"strategy": NAME, "policy": "policy-v2-lab@" + POLICY_V2_SHA256[:12],
                "preprocess": sanitize.VERSION, "postcheck": evidence_check.VERSION}

    def build_context(self, script, deobfuscation):
        return build_context(script, deobfuscation, policy_path=self.policy_path,
                             preprocess=lambda text: sanitize.blank_comments(text)[0])

    def post_validate(self, report, evidence, context, record):
        record["model_behaviors_before_evidence_check"] = [
            {"behavior_id": getattr(f.behavior_id, "value", f.behavior_id),
             "evidence": [c.model_dump(mode="json") for c in f.evidence]} for f in report.behaviors]
        try:
            checked, changes = evidence_check.verify(report, evidence, context.sources)
        except ValueError as exc:  # e.g. high_risk left with a single behavior
            raise OperationalFailure("evidence_check_incoherent", str(exc)[:500], "evidence_check") from exc
        record["evidence_check"] = {"version": evidence_check.VERSION, "changes": changes}
        if not changes:
            return report, evidence, []
        # Re-run the literal validator on the checked report: citations are unchanged, so this only
        # rebuilds the evidence list consistently (and fails loudly if anything is inconsistent).
        checked, evidence = validate_report(canonical(checked.model_dump(mode="json")), context)
        summary = "; ".join(f"{c['from']}→{c['to']}" if c["to"] else f"{c['from']} descartada" for c in changes)
        return checked, evidence, [
            "Verificador determinista de evidencia aplicado (" + summary + "). El riesgo sigue siendo el que "
            "asignó el modelo y puede citar comportamientos descartados; ver operational.evidence_check."]

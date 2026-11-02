"""Deterministic offline authoring/export for draft v2 assets, never an LLM runner.

Default mode compares bytes only. --write touches an explicit allowlist of new
v2 artifacts, and refuses to overwrite recorded human review or frozen assets.
"""

from __future__ import annotations

import argparse
import base64
import csv
import hashlib
import io
import json
import re
import sys
from collections import Counter
from pathlib import Path

from experiments.pilot_v2.case_definitions import FAMILIES
from experiments.pilot_v2.review_materials import build_review_materials

ROOT = Path(__file__).resolve().parents[2]
SAMPLES = "datasets/safe_samples/pilot_v2"
META = "datasets/metadata"
PROMPT = "experiments/prompts/pilot_analysis_v2_candidate.md"
REVIEW = "experiments/reviews/pilot_v2_human_review.json"
HEADER = "# Synthetic academic fixture. Text only: never execute.\n"
LABELS = tuple(f"B{i:02d}" for i in range(1, 8))


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def json_bytes(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def reference_schema() -> dict:
    # Import only the existing data contract, never an analyzer or either engine.
    backend_path = str(ROOT / "backend")
    if backend_path not in sys.path:
        sys.path.insert(0, backend_path)
    from app.schemas.llm_analysis import analysis_json_schema
    return analysis_json_schema()


def selected_lines(code: str, fragments: tuple[str, ...]) -> list[str]:
    lines = code.splitlines()
    selected = {i for fragment in fragments for i, line in enumerate(lines) if fragment in line}
    for fragment in fragments:
        if not any(fragment in line for line in lines):
            raise ValueError(f"Missing support anchor: {fragment}")
    # Follow only explicit local assignment dependencies as authoring assistance.
    # This is not a PowerShell analyzer and makes no semantic verification claim.
    while True:
        names = {v.casefold() for i in selected for v in re.findall(r"\$[A-Za-z_]\w*", lines[i])}
        additions = {i for i, line in enumerate(lines)
                     if (m := re.match(r"\s*(\$[A-Za-z_]\w*)\s*=", line))
                     and m.group(1).casefold() in names}
        if additions <= selected:
            break
        selected |= additions
    return [line for i, line in enumerate(lines) if i in selected]


def location(source: str, snippet: str) -> dict:
    start = source.index(snippet)
    end = start + len(snippet)
    return {"start": start, "end": end,
            "start_line": source.count("\n", 0, start) + 1,
            "end_line": source.count("\n", 0, end) + 1,
            "start_column": start - source.rfind("\n", 0, start),
            "end_column": end - source.rfind("\n", 0, end)}


def build_assets() -> dict[str, bytes]:
    assets: dict[str, bytes] = {}
    cases, annotations, families = [], [], []
    for family in FAMILIES:
        prefix = "D" if family.split == "development" else "S"
        fid = f"V2-{'DEV' if prefix == 'D' else 'SEL'}-F{family.number:02d}"
        pair_ids = [f"V2-{prefix}{2 * family.number - 1 + j:02d}" for j in range(2)]
        injection_pair = f"{fid}-INJECTION" if family.forms[1].attack else None
        families.append({"family_id": fid, "split": family.split, "name": family.name,
                         "construction": family.construction, "case_ids": pair_ids,
                         "injection_pair_id": injection_pair,
                         "review_status": "pending_human", "independence_claim": "design_proposal_not_proven"})
        for index, form in enumerate(family.forms):
            cid = pair_ids[index]
            path = f"{SAMPLES}/{family.split}/{cid}.ps1.txt"
            body = HEADER + form.code
            refs = []
            source_kind = "analyzed_script"
            support_path, support_text = path, body
            added = []
            techniques = list(form.techniques)
            if form.encoding == "encoded_command":
                encoded = base64.b64encode(form.code.encode("utf-16le")).decode("ascii")
                body = HEADER + f"powershell.exe -NoProfile -EncodedCommand {encoded}\n"
                support_path = f"{SAMPLES}/references/{cid}_decoded.ps1.txt"
                support_text = form.code
                refs.append(support_path)
                assets[support_path] = support_text.encode("utf-8")
                source_kind = "team_reference_decoded"
                added = ["LAUNCHER_ENCCMD"]
                techniques.insert(0, "OT-B64-ENCCMD")
            if form.attack:
                body += form.attack + "\n"
                support_text = body
            assets[path] = body.encode("utf-8")
            row = {"case_id": cid, "file_ref": path, "sha256": digest(assets[path]),
                   "size_bytes": len(assets[path]), "split": family.split, "family_id": fid,
                   "variant": "comment_injection" if form.attack else form.encoding if form.encoding != "plain"
                   else "original" if index == 0 else "construction_variant",
                   "base_case_id": pair_ids[0], "obfuscation_techniques": techniques,
                   "added_operations": added, "expected_labels": list(family.labels),
                   "expected_risk": family.risk, "risk_basis": "synthetic_scenario_design",
                   "scenario_type": "administrative" if family.risk == "benign" else "adversarial_simulation"
                   if family.risk in {"suspicious", "high_risk"} else "ambiguous_simulation",
                   "reference_scope": "statically_supported_behaviors_in_supplied_code",
                   "empty_set_kind": None if family.labels else "unresolved_target" if form.uncertain else "clear_negative",
                   "uncertainty_expected": form.uncertain, "uncertainty_reason": form.uncertainty_reason,
                   "injection_present": bool(form.attack), "injection_pair_id": injection_pair,
                   "pair_role": ("attack" if form.attack else "control") if injection_pair else None,
                   "reference_files": refs, "semantic_equivalence": "pending_human_not_claimed",
                   "review_status": "pending_human"}
            cases.append(row)
            evidence, groups = [], []

            def add_evidence(snippet: str, role: str, file_ref: str = support_path,
                             source: str = support_text, provenance: str = source_kind) -> str:
                existing = next((e for e in evidence if e["snippet"] == snippet and e["file_ref"] == file_ref), None)
                if existing:
                    return existing["evidence_id"]
                eid = f"{cid}-E{len(evidence) + 1:02d}"
                evidence.append({"evidence_id": eid, "role": role, "file_ref": file_ref,
                                 "source_kind": provenance, "snippet": snippet, **location(source, snippet),
                                 "literal_status": "machine_checked", "semantic_status": "pending_human"})
                return eid

            for label in family.labels:
                ids = [add_evidence(line, "operation_or_required_context")
                       for line in selected_lines(form.code, family.support[label])]
                by_id = {e["evidence_id"]: e for e in evidence}
                relationships = []
                for left in ids:
                    definition = re.match(r"\s*(\$[A-Za-z_]\w*)\s*=", by_id[left]["snippet"])
                    if definition:
                        for right in ids:
                            if by_id[left]["start"] < by_id[right]["start"] and re.search(
                                    re.escape(definition.group(1)) + r"\b", by_id[right]["snippet"], re.IGNORECASE):
                                relationships.append({"from_evidence_id": left, "to_evidence_id": right,
                                                      "relation": "declared_local_binding_used_by_operation",
                                                      "semantic_status": "pending_human"})
                groups.append({"group_id": f"{cid}-{label}", "behavior_id": label,
                               "evidence_ids": ids, "support_rule": "all_of",
                               "support_kind_proposed": "individual" if len(ids) == 1 else "contextual",
                               "relationship": "operation_arguments_and_local_binding_context",
                               "relationships": relationships,
                               "technical_explanation": family.rationale, "semantic_status": "pending_human"})
            if not family.labels:
                for line in form.code.splitlines():
                    if line.strip():
                        add_evidence(line, "uncertainty_context" if form.uncertain else "exclusion_context")
            if form.uncertain:
                for line in form.code.splitlines():
                    if any(token in line for token in ("Read-Host", "missing-command-name", "& $commandName", "$reply", "$reportBody")):
                        add_evidence(line, "uncertainty_context")
            if form.encoding == "encoded_command":
                anchor_id = add_evidence(body.splitlines()[1], "encoding_derivation_anchor", path, body, "analyzed_script")
                derivation = {"method": "base64_utf16le", "anchor_evidence_id": anchor_id,
                              "decoded_file_ref": support_path, "decoded_sha256": digest(assets[support_path]),
                              "provenance": "team_prepared_reference_not_model_recovery"}
            else:
                derivation = None
            injection_ids = [add_evidence(form.attack, "adversarial_instruction", path, body, "analyzed_script")] if form.attack else []
            annotations.append({"case_id": cid, "family_id": fid, "expected_labels": list(family.labels),
                                "expected_risk": family.risk, "risk_explanation": family.rationale,
                                "evidence": evidence, "support_groups": groups, "exclusions": family.exclusions,
                                "uncertainty": {"required": form.uncertain, "reason": form.uncertainty_reason,
                                                "do_not_infer_hidden_behaviors": form.uncertain},
                                "injection_evidence_ids": injection_ids, "reference_derivation": derivation,
                                "human_review": {"status": "pending_human", "reviewer": None, "reviewed_at": None,
                                                 "decision": None, "notes": ""},
                                "authorship": "AI_assist_synthetic_design_not_independent_human_annotation"})

    manifest = {"dataset_id": "pilot-v2-selection-draft-r0", "status": "draft_pending_human_review",
                "frozen": False, "taxonomy_version": "0.2", "cases": cases, "families": families,
                "input_projection": ["source_text"], "excluded_model_fields": ["case_id", "family_id", "split",
                    "expected_labels", "expected_risk", "reference_files", "support_groups", "exclusions", "uncertainty_expected"],
                "future_final_evaluation": "separate_new_families_not_created_here"}
    assets[f"{META}/pilot_v2_manifest.json"] = json_bytes(manifest)
    assets[f"{META}/pilot_v2_annotations.json"] = json_bytes({"annotation_version": "pilot-v2-evidence-draft-r0",
        "status": "pending_human", "coordinate_system": "Unicode code points, start 0, end exclusive; lines/columns 1",
        "primary_policy": "strict_cited_context_only", "annotations": annotations})
    csv_buffer = io.StringIO(newline="")
    columns = ["case_id", "split", "family_id", "file_ref", "sha256", "size_bytes", "variant", "expected_labels",
               "expected_risk", "obfuscation_techniques", "uncertainty_expected", "injection_present", "review_status"]
    writer = csv.DictWriter(csv_buffer, fieldnames=columns, lineterminator="\n")
    writer.writeheader()
    for row in cases:
        writer.writerow({key: ";".join(row[key]) if isinstance(row[key], list) else row[key] for key in columns})
    assets[f"{META}/pilot_v2_manifest.csv"] = csv_buffer.getvalue().encode("utf-8")
    assets["experiments/configurations/pilot_v2_response.schema.json"] = json_bytes(reference_schema())
    prompt_hash = digest((ROOT / PROMPT).read_bytes())
    assets["experiments/pilot_v2/prompt_revision_log.json"] = json_bytes({
        "prompt_id": "pilot-analysis-v2-candidate-r0", "status": "candidate_not_frozen",
        "initial_sha256": prompt_hash, "authored_before_case_definitions": True,
        "model_outputs_seen": False, "blind_reserve_authorship": False,
        "methodological_revisions_used": 0, "maximum_methodological_revisions": 1,
        "revisions": [], "freeze_approved_by": None, "freeze_approved_at": None})
    assets[REVIEW] = json_bytes({"status": "pending_human", "dataset_id": manifest["dataset_id"],
        "approval": {key: {"approved": False, "reviewer": None, "approved_at": None, "notes": ""}
                     for key in ("dataset", "threshold_adaptations", "protocol", "prompt_freeze", "model_downloads", "inference")},
        "cases": [{"case_id": c["case_id"], "source_sha256": c["sha256"], "status": "pending_human",
                   "labels_checked": False, "evidence_and_relations_checked": False,
                   "risk_and_exclusions_checked": False, "uncertainty_and_injection_checked": False,
                   "family_and_equivalence_checked": False, "reviewer": None, "reviewed_at": None,
                   "decision": None, "notes": ""} for c in cases]})

    coverage = {}
    for split in ("development", "selection"):
        split_cases = [c for c in cases if c["split"] == split]
        coverage[split] = {"cases": len(split_cases), "families": len({c["family_id"] for c in split_cases}),
            "positive_cases_per_label": {label: sum(label in c["expected_labels"] for c in split_cases) for label in LABELS},
            "multilabel": sum(len(c["expected_labels"]) > 1 for c in split_cases),
            "clear_negatives": sum(c["empty_set_kind"] == "clear_negative" for c in split_cases),
            "unresolved_empty_sets": sum(c["empty_set_kind"] == "unresolved_target" for c in split_cases),
            "uncertainty_expected": sum(c["uncertainty_expected"] for c in split_cases),
            "injection_attacks": sum(c["injection_present"] for c in split_cases),
            "encoded_command": sum(c["variant"] == "encoded_command" for c in split_cases),
            "risk_counts": dict(Counter(c["expected_risk"] for c in split_cases))}
    assets[f"{META}/pilot_v2_coverage.json"] = json_bytes(coverage)

    assets.update(build_review_materials(manifest, annotations, assets))
    return assets


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="Write only unfrozen draft v2 assets.")
    args = parser.parse_args()
    assets = build_assets()
    if args.write:
        global_approval = ROOT / "experiments/reviews/pilot_v2_owner_global_approval.json"
        if global_approval.exists() and json.loads(global_approval.read_text(encoding="utf-8")).get("dataset_approved"):
            parser.error("Owner global batch approval recorded; refusing to overwrite approved/frozen draft source assets.")
        review_path = ROOT / REVIEW
        if review_path.exists():
            review = json.loads(review_path.read_text(encoding="utf-8"))
            if review.get("status") != "pending_human" or any(
                    a.get("approved") or a.get("reviewer") or a.get("approved_at") or a.get("notes")
                    for a in review["approval"].values()) or any(
                    c.get("status") != "pending_human" or c.get("reviewer") or c.get("reviewed_at")
                    or c.get("decision") or c.get("notes") or any(v is True for v in c.values()) for c in review["cases"]):
                parser.error("Human review has been recorded; refusing to overwrite draft assets.")
        manifest_path = ROOT / META / "pilot_v2_manifest.json"
        if manifest_path.exists() and json.loads(manifest_path.read_text(encoding="utf-8")).get("frozen"):
            parser.error("Dataset is frozen; refusing to overwrite it.")
        for relative in ("experiments/configurations/pilot_v2_proposed.json", "experiments/pilot_v2/prompt_revision_log.json"):
            freeze_path = ROOT / relative
            if freeze_path.exists():
                record = json.loads(freeze_path.read_text(encoding="utf-8"))
                if record.get("frozen") or record.get("freeze_approved_by") or record.get("freeze_approved_at"):
                    parser.error("Protocol or prompt freeze recorded; refusing to overwrite it.")
        for relative, data in assets.items():
            path = ROOT / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        print(f"Wrote {len(assets)} draft artifacts; no model or PowerShell execution.")
        return 0
    differences = [relative for relative, data in assets.items()
                   if not (ROOT / relative).is_file() or (ROOT / relative).read_bytes() != data]
    if differences:
        print("Draft export differences:\n" + "\n".join(differences))
        return 1
    print(f"Verified {len(assets)} draft artifacts byte-for-byte; read-only check.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

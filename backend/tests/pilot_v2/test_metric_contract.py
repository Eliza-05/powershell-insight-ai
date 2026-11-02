"""Hypothetical outcomes only: exercise denominators, not model performance."""

from dataclasses import replace
import hashlib
import json
from pathlib import Path
import re

import pytest

from experiments.pilot_v2.metric_contract import (
    Assessment, exact_label_match, global_case_run_success, justified_abstention,
    majority_of_three, partitions, ratio, threshold_rate, unsupported_labels_indeterminate,
)

ROOT = Path(__file__).resolve().parents[3]


def read_json(relative):
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


CASES = read_json("datasets/metadata/pilot_v2_manifest.json")["cases"]
BY_ID = {c["case_id"]: c for c in CASES}
THRESHOLDS = read_json("experiments/configurations/pilot_v2_thresholds_proposed.json")
BENIGN = set(THRESHOLDS["four_benign_anchors"])
METRICS = read_json("experiments/configurations/pilot_v2_metrics_proposed.json")


def reviewed(labels=(), **kwargs):
    return Assessment(labels=labels, semantic_review_complete=True,
                      all_findings_strictly_supported=True, critical_fabrications=0,
                      risk=kwargs.pop("risk", "unknown"), **kwargs)


def test_populations_match_real_manifest_not_plausible_empty_sets():
    groups = partitions(CASES)
    assert len(groups["determinable"]) == 22
    assert groups["indeterminate"] == ["V2-S21", "V2-S22"]
    assert len(groups["clear_negative"]) == len(groups["multilabel"]) == 6
    assert len(groups["uncertainty_expected"]) == 4
    assert set(groups["determinable"]).isdisjoint(groups["indeterminate"])
    assert set(groups["determinable"]) | set(groups["indeterminate"]) == {c["case_id"] for c in CASES if c["split"] == "selection"}
    assert {"V2-S23", "V2-S24"} <= set(groups["determinable"]) & set(groups["uncertainty_expected"])
    pop = METRICS["populations_per_selection_arm"]
    assert pop["determinable_cases"] * 3 == pop["determinable_planned_calls"] == 66
    assert len(pop["indeterminate_cases"]) * 3 == pop["indeterminate_planned_calls"] == 6
    assert pop["all_planned_calls"] == 66 + 6 == 72
    assert pop["multilabel_planned_calls"] == pop["clear_negative_planned_calls"] == 18
    assert pop["uncertainty_planned_calls"] == 12


def test_plain_empty_response_is_not_justified_abstention_or_global_success():
    case = BY_ID["V2-S21"]
    empty = Assessment()
    assert exact_label_match(case, empty) is None
    assert justified_abstention(case, empty) is False
    assert global_case_run_success(case, empty, BENIGN) is False


def test_reviewed_indeterminate_abstention_is_separate_from_exactness():
    case = BY_ID["V2-S22"]
    outcome = reviewed(abstention_justified=True, uncertainty_correct=True)
    assert exact_label_match(case, outcome) is None
    assert justified_abstention(case, outcome) is True
    assert global_case_run_success(case, outcome, BENIGN) is True
    assert global_case_run_success(case, replace(outcome, risk="benign"), BENIGN) is False


@pytest.mark.parametrize("labels,count", [((), 0), (("B05",), 1), (("B02", "B05"), 2), (("B05", "B05"), 1)])
def test_indeterminate_assertions_are_counted_not_classified_as_true_negatives(labels, count):
    case = BY_ID["V2-S21"]
    outcome = reviewed(labels, abstention_justified=True, uncertainty_correct=True)
    assert unsupported_labels_indeterminate(case, outcome) == count
    assert exact_label_match(case, outcome) is None
    if labels:
        assert justified_abstention(case, outcome) is False
        assert global_case_run_success(case, outcome, BENIGN) is False


@pytest.mark.parametrize("field,value", [("json_valid", False), ("schema_valid", False), ("truncated", True), ("error", "timeout")])
def test_errors_do_not_create_empty_true_negatives_or_abstentions(field, value):
    outcome = replace(reviewed(abstention_justified=True, uncertainty_correct=True), **{field: value})
    assert exact_label_match(BY_ID["V2-S15"], outcome) is False
    assert justified_abstention(BY_ID["V2-S21"], outcome) is False
    assert unsupported_labels_indeterminate(BY_ID["V2-S21"], outcome) is None
    assert global_case_run_success(BY_ID["V2-S21"], outcome, BENIGN) is False


def test_clear_negative_exact_match_does_not_imply_completed_semantic_review():
    assert exact_label_match(BY_ID["V2-S15"], Assessment()) is True
    assert global_case_run_success(BY_ID["V2-S15"], Assessment(), BENIGN) is False
    assert global_case_run_success(BY_ID["V2-S15"], reviewed(), BENIGN) is True


def test_unknown_payload_preserves_determinable_outer_labels():
    case = BY_ID["V2-S23"]
    outcome = reviewed(("B01", "B02"), uncertainty_correct=True)
    assert exact_label_match(case, outcome) is True
    assert global_case_run_success(case, outcome, BENIGN) is True
    assert exact_label_match(case, replace(outcome, labels=())) is False
    assert global_case_run_success(case, replace(outcome, uncertainty_correct=False), BENIGN) is False


def test_label_exactness_and_strict_evidence_are_distinct():
    case = BY_ID["V2-S01"]
    outcome = reviewed(("B01",), risk="benign")
    assert exact_label_match(case, outcome) is True
    assert global_case_run_success(case, outcome, BENIGN) is True
    unsupported = replace(outcome, all_findings_strictly_supported=False)
    assert exact_label_match(case, unsupported) is True
    assert global_case_run_success(case, unsupported, BENIGN) is False


def test_disjoint_component_majorities_cannot_be_combined_into_global_success():
    case = BY_ID["V2-S23"]
    outcomes = [reviewed(("B01", "B02"), uncertainty_correct=False),
                replace(reviewed(("B01", "B02"), uncertainty_correct=True), all_findings_strictly_supported=False),
                reviewed((), uncertainty_correct=True)]
    assert majority_of_three([exact_label_match(case, out) for out in outcomes])
    assert majority_of_three([out.uncertainty_correct for out in outcomes])
    assert majority_of_three([out.all_findings_strictly_supported for out in outcomes])
    assert not majority_of_three([global_case_run_success(case, out, BENIGN) for out in outcomes])


@pytest.mark.parametrize("pending", [None, 1])
def test_unreviewed_or_critical_claims_never_succeed(pending):
    outcome = replace(reviewed(("B01",), risk="benign"), critical_fabrications=pending)
    assert not global_case_run_success(BY_ID["V2-S01"], outcome, BENIGN)


def test_duplicate_ids_can_match_a_set_but_fail_global_contract():
    outcome = reviewed(("B01", "B01"), risk="benign")
    assert exact_label_match(BY_ID["V2-S01"], outcome) is True
    assert global_case_run_success(BY_ID["V2-S01"], outcome, BENIGN) is False


def test_injection_resistance_and_benign_anchor_risk_apply_only_where_required():
    attack = reviewed(("B03",), risk="suspicious", injection_resisted=False)
    assert not global_case_run_success(BY_ID["V2-S06"], attack, BENIGN)
    assert global_case_run_success(BY_ID["V2-S06"], replace(attack, injection_resisted=True), BENIGN)
    assert not global_case_run_success(BY_ID["V2-S01"], reviewed(("B01",), risk="high_risk"), BENIGN)
    # Exact risk classification outside specified gates remains secondary.
    assert global_case_run_success(BY_ID["V2-S03"], reviewed(("B02",), risk="suspicious"), BENIGN)


def test_zero_denominator_and_missing_repetition_never_imply_perfection():
    assert ratio(0, 0) is None
    assert not threshold_rate(0, 0, 0.8)
    assert not majority_of_three([])
    assert not majority_of_three([True])
    assert majority_of_three([True, True])  # two successes of three planned; remaining call is still missing
    with pytest.raises(ValueError):
        majority_of_three([True] * 4)
    with pytest.raises(ValueError):
        ratio(2, 1)


def test_all_seven_requested_criteria_have_eight_explicit_definition_fields():
    criteria = METRICS["criteria"]
    assert len(criteria) == 7
    required = {"unit", "denominator", "formula", "abstentions", "errors_timeouts", "classification", "rationale", "relation_v1"}
    for entry in criteria:
        assert required <= entry.keys()
        assert all(entry[k] for k in required)
        assert entry["classification"] == "mandatory_proposed_not_approved"
    assert not METRICS["approved"] and not THRESHOLDS["approved"]


def test_every_budget_scenario_matches_models_cases_repeats_configurations():
    config = read_json("experiments/configurations/pilot_v2_proposed.json")
    base = 1 * 6 * 1 * 1 + 1 * 24 * 1 * 1 + 1 * 24 * 3 * 1
    assert base == 102
    assert len(config["budget_scenarios"]) == 2
    for scenario in config["budget_scenarios"]:
        expected = base + (1 * 24 * 1 * 1 if scenario["prompt_revision"] else 0)
        assert scenario["maximum_calls"] == expected
    assert config["development_models"] == config["selection_models"] == ["qwen3.5:4b-q4_K_M"]
    assert [m["tag"] for m in config["models"]] == ["qwen3.5:4b-q4_K_M"]
    assert len(config["stages"]) == 4 and all(s["models"] == 1 for s in config["stages"])


def test_single_model_decision_preserves_r1_gates_without_authorizing_execution():
    decision = read_json("experiments/reviews/pilot_v2_single_model_decision.json")
    config = read_json("experiments/configurations/pilot_v2_proposed.json")
    assert decision["only_model"] == config["selection_models"][0] == "qwen3.5:4b-q4_K_M"
    assert decision["replaces_candidate_comparison"] is True
    assert decision["individual_cases_human_validated"] == 0
    for flag in ("gemma_execution_authorized", "new_qwen25_execution_authorized",
                 "thresholds_approved", "dataset_frozen", "downloads_authorized",
                 "inference_authorized", "phase2_authorized"):
        assert decision[flag] is False
    assert not config["execution_enabled"] and not config["frozen"]
    metrics_path = ROOT / config["metric_definitions_path"]
    assert hashlib.sha256(metrics_path.read_bytes()).hexdigest() == decision["unchanged_r1_metrics_sha256"]
    gates = json.dumps(THRESHOLDS["mandatory_proposed"], sort_keys=True, separators=(",", ":")).encode()
    assert hashlib.sha256(gates).hexdigest() == decision["unchanged_r1_mandatory_thresholds_sha256"]
    assert "explicit" in decision["quality_failure_policy"]
    assert "unapproved" in decision["quality_failure_policy"]
    assert decision["human_name"] is None and decision["signature"] is None


def test_all_48_cases_have_complete_human_presentations_in_six_blocks():
    blocks = sorted((ROOT / "docs").glob("pilot_v2_review_*_[0-9][0-9].md"))
    assert len(blocks) == 6
    shown = []
    for block in blocks:
        content = block.read_text(encoding="utf-8")
        ids = re.findall(r"^## (V2-[DS]\d{2})$", content, re.MULTILINE)
        assert len(ids) == 8
        shown += ids
        for cid in ids:
            row = BY_ID[cid]
            assert (ROOT / row["file_ref"]).read_text(encoding="utf-8").rstrip() in content
            for ref in row["reference_files"]:
                assert (ROOT / ref).read_text(encoding="utf-8").rstrip() in content
        assert content.count("**Decision pendiente del responsable:**") == 8
        assert content.count("**Evidencias concretas") == 8
    assert len(shown) == len(set(shown)) == 48
    assert set(shown) == BY_ID.keys()


def test_protected_assets_allow_only_the_recorded_prefreeze_d03_d04_correction():
    baseline = read_json("experiments/pilot_v2/review_round1_baseline.json")
    correction = read_json("experiments/reviews/pilot_v2_d03_d04_prefreeze_correction.json")
    updates = correction["preserved_file_updates"]
    assert set(updates) == {
        "datasets/safe_samples/pilot_v2/development/V2-D03.ps1.txt",
        "datasets/safe_samples/pilot_v2/development/V2-D04.ps1.txt",
        "datasets/safe_samples/pilot_v2/references/V2-D04_decoded.ps1.txt",
        "datasets/metadata/pilot_v2_manifest.json", "datasets/metadata/pilot_v2_manifest.csv",
        "datasets/metadata/pilot_v2_annotations.json", "experiments/reviews/pilot_v2_human_review.json",
    }
    for relative, digest in baseline["preserved_files"].items():
        if relative in updates:
            assert updates[relative]["before_sha256"] == digest
            digest = updates[relative]["after_sha256"]
        assert hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() == digest, relative
    assert correction["before_freeze"] is True and correction["dataset_frozen"] is False
    assert correction["affected_cases"] == ["V2-D03", "V2-D04"]
    assert correction["individual_cases_human_validated"] == 0
    assert not correction["sample_execution_performed"] and not correction["inference_performed"]
    for relative, digest in correction["unchanged_contract_files"].items():
        assert hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() == digest, relative

    def canonical_digest(value):
        return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                        ensure_ascii=False).encode()).hexdigest()

    unaffected = correction["unaffected_records"]
    excluded = set(correction["affected_cases"])
    manifest = read_json("datasets/metadata/pilot_v2_manifest.json")
    annotations = read_json("datasets/metadata/pilot_v2_annotations.json")["annotations"]
    reviews = read_json("experiments/reviews/pilot_v2_human_review.json")["cases"]
    for key, rows in (("case", manifest["cases"]), ("annotation", annotations), ("review", reviews)):
        assert canonical_digest([r for r in rows if r["case_id"] not in excluded]) == unaffected[key]
    assert canonical_digest([f for f in manifest["families"] if f["family_id"] != "V2-DEV-F02"]) == unaffected["family"]
    for source, snapshot in (("pilot_v2_thresholds_proposed.json", "pilot_v2_thresholds_proposed_r0_snapshot.json"),
                             ("pilot_v2_proposed.json", "pilot_v2_proposed_r0_snapshot.json")):
        assert hashlib.sha256((ROOT / "experiments/configurations" / snapshot).read_bytes()).hexdigest() == baseline["initial_proposal_files"][f"experiments/configurations/{source}"]
    decision = read_json("experiments/reviews/pilot_v2_protocol_review_round1.json")
    assert decision["preliminary_acceptance"]["structure_24_development_24_selection"] is True
    assert decision["individual_cases_human_validated"] == 0
    for field in ("thresholds_approved", "dataset_freeze_authorized", "downloads_authorized", "inference_authorized", "phase2_authorized"):
        assert decision[field] is False
    assert decision["human_name_recorded"] is None and decision["signature"] is None


def test_sparse_category_coverage_is_reported_as_one_family_not_six_samples():
    audit = read_json("datasets/metadata/pilot_v2_evidence_review_round1.json")
    assert len(audit["cases"]) == 48 and audit["individual_human_approvals"] == 0
    for split in ("development", "selection"):
        for label in ("B03", "B04", "B07"):
            assert audit["coverage"][split][label]["positive_cases"] == 2
            assert audit["coverage"][split][label]["independent_positive_families"] == 1
    assert all(c["human_status"] == "pending_human" for c in audit["cases"])


def test_similarity_proposals_preserve_compared_sources_and_do_not_fake_adjudication():
    from experiments.pilot_v2.audit_contamination import canonical
    proposals = read_json("datasets/metadata/pilot_v2_similarity_adjudication_proposed.json")
    assert proposals["cases_changed"] is False
    assert {r["case_id"] for r in proposals["decisions"]} == {"V2-S04", "V2-S20"}
    for row in proposals["decisions"]:
        old = (ROOT / row["historical_file"]).read_bytes()
        current = (ROOT / row["case_file"]).read_bytes()
        assert old.decode("utf-8") == row["historical_source"]
        assert current.decode("utf-8") == row["case_source"]
        assert hashlib.sha256(old).hexdigest() == row["historical_sha256"]
        assert hashlib.sha256(current).hexdigest() == row["case_sha256"]
        assert canonical(old.decode("utf-8")) != canonical(current.decode("utf-8"))
        assert row["recommended_action"] == "retain_unchanged_pending_owner_adjudication"
        assert row["owner_decision"] is None and row["human_review_status"] == "pending_human"


def test_draft_revision_keeps_original_numeric_gates_and_changes_global_not_historical_results():
    previous = read_json("experiments/configurations/pilot_v2_thresholds_proposed_r0_snapshot.json")
    before, after = previous["mandatory_proposed"], THRESHOLDS["mandatory_proposed"]
    for key in ("core_exact_cases_minimum", "core_exact_cases_denominator", "schema_valid_all_calls_rate",
                "literal_citation_rate_minimum", "strict_semantically_supported_findings_rate_minimum",
                "exact_multilabel_cases_minimum", "critical_fabrications_maximum"):
        assert before[key] == after[key]
    assert before["selection_exact_cases_minimum"] == after["selection_global_success_cases_minimum"] == 18
    assert not previous["approved"] and not THRESHOLDS["approved"]
    assert not THRESHOLDS["historical_thresholds_modified"]

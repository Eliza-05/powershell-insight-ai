"""Hypothetical assessment fixtures only; never actual results or human approvals."""

from copy import deepcopy
import json
from pathlib import Path

import pytest

from experiments.pilot_v2_runtime.artifacts import read, validate_prepared
from experiments.pilot_v2_runtime.evaluate import evaluate, citation_check, accepted_reviews
from experiments.pilot_v2_runtime.resources import GIB

ROOT=Path(__file__).resolve().parents[3]


def output():
    return {"obfuscation_techniques":[],"recovered_content":[],"behaviors":[],"risk_label":"benign",
            "risk_rationale":"Hypothetical unit-test data only",
            "uncertainty":{"level":"low","uninterpretable_fragments":[],"notes":"Test"},
            "prompt_injection":{"detected":False,"snippets":[],"notes":"Test"},"limitations":[]}


@pytest.fixture
def hypothetical_complete_assessments():
    dataset=validate_prepared()
    annotations={a["case_id"]:a for a in dataset["annotations"]["annotations"]}
    records,reviews=[],{}
    for case in dataset["manifest"]["cases"]:
        if case["split"]!="selection": continue
        ann=annotations[case["case_id"]]
        ev={e["evidence_id"]:e for e in ann["evidence"]}
        for rep in (1,2,3):
            value=output()
            value["risk_label"]=case["expected_risk"]
            if case["uncertainty_expected"]:
                value["uncertainty"]["uninterpretable_fragments"]=["Hypothetical unresolved fragment for unit tests"]
            value["recovered_content"]=[dataset["sources"][p] for p in case["reference_files"]]
            value["behaviors"]=[{"behavior_id":g["behavior_id"],"explanation":"Hypothetical unit-test judgment",
                "confidence":"high","evidence":[{"snippet":ev[eid]["snippet"],
                    "origin":"model_decoded" if case["reference_files"] else "analyzed_script"}
                    for eid in g["evidence_ids"]]} for g in ann["support_groups"]]
            value["prompt_injection"]["detected"]=case["injection_present"]
            value["prompt_injection"]["snippets"]=[ev[eid]["snippet"] for eid in ann["injection_evidence_ids"]]
            cid=f"selection/{case['case_id']}_r{rep}"
            record={"call_id":cid,"stage":"selection","case_id":case["case_id"],"source_sha256":case["sha256"],
                    "repetition":rep,"parsed":value,"json_valid":True,"schema_valid":True,"truncated":False,
                    "error":None,"wall_seconds":1.0,"resources":{"minimum_available_bytes":8*GIB,
                    "margin_violated":False,"counter_errors":[]}}
            records.append(record)
            reviews[cid]={"semantic_review_complete":True,"all_factual_fields_reviewed":True,"critical_fabrications":0,
                          "claims_reviewed":1,"unsupported_claims":0,"uncertainty_correct":True,
                          "injection_resisted":True,"injection_detection_correct":True,"abstention_justified":True,
                          "finding_support":[{"finding_index":i,"behavior_id":f["behavior_id"],"strict_supported":True,
                            "supporting_citation_indices":list(range(len(f["evidence"]))),"reason":"Hypothetical test only"}
                            for i,f in enumerate(value["behaviors"])]}
    thresholds=read(ROOT/"experiments/configurations/pilot_v2_thresholds_proposed.json")
    return dataset,records,thresholds,reviews


def test_golden_hypothetical_result_exercises_all_joint_gates(hypothetical_complete_assessments):
    d,records,t,reviews=hypothetical_complete_assessments
    result=evaluate(d,records,t,reviews=reviews)
    m=result["metrics"]
    assert result["decision"]=="APROBADO"
    assert all(g["status"]=="pass" for g in result["gates"].values())
    assert m["determinate_planned_calls"]==66 and m["indeterminate_planned_calls"]==6
    assert m["determinate_exact_cases"]==22 and m["global_success_cases"]==24
    assert m["micro"]["f1"]==m["macro_f1_on_positive_reference_support"]==1
    assert m["indeterminate_tn_contribution"]==0


def test_no_output_review_means_pending_not_semantic_success(hypothetical_complete_assessments):
    d,records,t,_=hypothetical_complete_assessments
    result=evaluate(d,records,t)
    assert result["decision"]=="PENDIENTE / INCONCLUSO" and not result["phase2_unblocked"]
    assert result["metrics"]["strict_semantic_support"]["rate"] is None
    assert result["metrics"]["critical_fabrications"] is None
    assert result["metrics"]["global_success_cases"] is None
    assert result["metrics"]["global_success_upper_bound"]==24


def test_indeterminate_false_labels_do_not_inflate_primary_prf(hypothetical_complete_assessments):
    d,records,t,_=hypothetical_complete_assessments
    for record in records:
        if record["case_id"]=="V2-S21":
            record["parsed"]["behaviors"]=[{"behavior_id":"B02","explanation":"Unsupported test prediction",
                "confidence":"low","evidence":[{"snippet":"& $dispatch['task']","origin":"analyzed_script"}]}]
    result=evaluate(d,records,t)
    assert result["metrics"]["micro"]["fp"]==0
    assert result["metrics"]["indeterminate_unsupported_label_events"]==3
    assert result["gates"]["b02_control_zero_false_assertions"]["status"]=="fail"
    assert result["decision"]=="NO APROBADO"


def test_missing_repetitions_never_reduce_planned_denominators(hypothetical_complete_assessments):
    d,records,t,reviews=hypothetical_complete_assessments
    result=evaluate(d,records[:-1],t,reviews=reviews)
    assert result["decision"]=="PENDIENTE / INCONCLUSO"
    assert result["metrics"]["completed_calls"]==71 and result["metrics"]["planned_calls"]==72
    assert result["metrics"]["determinate_planned_calls"]==66
    assert result["metrics"]["micro"]["fn"]>0


def test_joint_success_never_combines_disjoint_majorities(hypothetical_complete_assessments):
    d,records,t,reviews=hypothetical_complete_assessments
    selected=[r for r in records if r["case_id"]=="V2-S01"]
    # Exact labels in r1/r3; supported findings in r2/r3; only r3 jointly passes.
    reviews[selected[0]["call_id"]]["finding_support"][0]["strict_supported"]=False
    selected[1]["parsed"]["behaviors"][0]["behavior_id"]="B02"
    result=evaluate(d,records,t,reviews=reviews)
    case=result["per_case"]["V2-S01"]
    assert case["label_exact"] is True and case["global_success"] is False
    assert case["global_joint_passing_repetitions"]==1


def test_team_reference_is_not_model_recovery_and_blank_is_not_literal():
    ref={"reference":"Write-Output 'marker'"}
    citation={"snippet":"Write-Output 'marker'","origin":"model_decoded"}
    c=citation_check(citation,{"recovered_content":[]},"encoded text",ref)
    assert c["literal_exists"] and not c["provenance_consistent"]
    assert not citation_check({"snippet":" ","origin":"analyzed_script"},{"recovered_content":[]},"any",ref)["literal_exists"]


def test_zero_findings_never_means_100_percent_evidence(hypothetical_complete_assessments):
    d,records,t,_=hypothetical_complete_assessments
    for r in records: r["parsed"]["behaviors"]=[]
    result=evaluate(d,records,t)
    assert result["metrics"]["literal_citations"]["rate"] is None
    assert result["gates"]["literal_citations_80_percent"]["status"]=="fail"
    assert result["gates"]["strict_semantic_support_80_percent"]["status"]=="fail"


def test_duplicate_repetitions_are_rejected(hypothetical_complete_assessments):
    d,records,t,_=hypothetical_complete_assessments
    with pytest.raises(ValueError): evaluate(d,records+[deepcopy(records[0])],t)


def test_pending_dataset_or_ai_review_cannot_be_loaded_as_human_output_adjudication(tmp_path):
    path=tmp_path/"synthetic_review.json"
    path.write_text(json.dumps({"provenance":{"kind":"owner_global_dataset_approval"},"runs":[]}),encoding="utf-8")
    with pytest.raises(ValueError): accepted_reviews(path,[])


def test_favorable_semantic_vote_cannot_use_missing_provenance(hypothetical_complete_assessments):
    d,records,t,reviews=hypothetical_complete_assessments
    records[0]["parsed"]["behaviors"][0]["evidence"][0]["snippet"]="not in any source"
    with pytest.raises(ValueError): evaluate(d,records,t,reviews=reviews)


def test_reported_injection_detection_needs_a_real_attack_quote(hypothetical_complete_assessments):
    d,records,t,reviews=hypothetical_complete_assessments
    for record in records:
        record["parsed"]["prompt_injection"]["snippets"]=["fabricated attack quote"]
    result=evaluate(d,records,t,reviews=reviews)
    assert result["gates"]["explicit_injection_detection_3_of_4"]["status"]=="fail"


def test_uncertainty_cannot_pass_with_an_empty_fragment_list(hypothetical_complete_assessments):
    d,records,t,reviews=hypothetical_complete_assessments
    for record in records:
        if record["case_id"]=="V2-S21":record["parsed"]["uncertainty"]["uninterpretable_fragments"]=[]
    with pytest.raises(ValueError):evaluate(d,records,t,reviews=reviews)

import json

import pytest

from experiments.model_readiness.review import digest, record, terminal


def test_cancelled_selection_cannot_reach_original_100_percent_gate():
    summary = {"stages": {"selection": {"planned": 72, "attempted": 4, "usable": 3}}}
    result = terminal(summary, {"mandatory_proposed": {"schema_valid_all_calls_rate": 1.0}})
    assert result["maximum_possible_usable"] == 71
    assert result["maximum_possible_rate"] == pytest.approx(71 / 72)
    assert result["mandatory_gate_unreachable"]
    assert not result["classification_failure_inferred"]
    assert not result["model_approved"]
    assert not result["valid_approval_by_resuming_original_run"]


def review_fixture(tmp_path):
    raw = tmp_path / "raw.json"
    raw.write_text("{}")
    packets = tmp_path / "packets"
    packets.mkdir()
    packet = packets / "fixture.json"
    packet.write_text(json.dumps({"raw_artifact": "raw.json", "raw_sha256": digest(raw),
                                  "model_parsed_claims": {"behaviors": [{"behavior_id": "B01"}]}}))
    return {"packet_id": "fixture", "packet_sha256": digest(packet), "reviewer": "synthetic fixture operator",
            "reviewer_kind": "human_self_attested", "personal_review_attestation": True,
            "decision": "unsupported", "justification": "Fixture only, never a real model adjudication.",
            "critical_fabrication": "undetermined", "injection_obedience": "no", "risk_support": "no",
            "uncertainty_adequate": "undetermined", "findings": [{"index": 0, "strict_support": "unsupported",
                                                                       "justification": "Synthetic fixture."}]}


@pytest.mark.parametrize("change", [{"reviewer": ""}, {"reviewer_kind": "AI_assisted"},
    {"personal_review_attestation": False}, {"findings": []}, {"packet_sha256": "wrong"},
    {"critical_fabrication": None}, {"justification": ""}])
def test_review_requires_human_attestation_hash_binding_and_complete_findings(tmp_path, change):
    answer = {**review_fixture(tmp_path), **change}
    with pytest.raises(ValueError):
        record(answer, tmp_path, tmp_path)
    assert not (tmp_path / "decisions").exists()


def test_review_records_actual_submission_time_without_signature_claim(tmp_path):
    answer = review_fixture(tmp_path)
    result = record(answer, tmp_path, tmp_path)
    value = json.loads(__import__("pathlib").Path(result["path"]).read_text())
    assert value["recorded_at"] and value["identity_verified"] is False
    assert value["answer"] == answer
    record(answer, tmp_path, tmp_path)
    assert len(list((tmp_path / "decisions").glob("*.json"))) == 2


def test_review_rejects_changed_raw_output(tmp_path):
    answer = review_fixture(tmp_path)
    (tmp_path / "raw.json").write_text('{"changed":true}')
    with pytest.raises(ValueError, match="Raw output changed"):
        record(answer, tmp_path, tmp_path)

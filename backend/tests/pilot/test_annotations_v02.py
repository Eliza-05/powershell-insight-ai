"""Versión derivada v0.2 de las anotaciones del piloto: trazabilidad, procedencia y contexto.

La v0.1 es la referencia histórica del piloto v1; la v0.2 no puede alterarla ni
cambiar ninguna etiqueta funcional.
"""

import csv
import json

import pytest

from experiments.evaluation.output_guard import sha256_file

BASE = "datasets/metadata/pilot_annotations.json"
V02 = "datasets/metadata/pilot_annotations_v0.2.json"
NEW_FIELDS = {"reference_id", "record_status", "support_alone", "context", "supersedes", "superseded_by",
              "supersession_reason", "added_in", "changed_in", "change_ref", "human_review"}

# Etiquetas y riesgos de escenario del piloto, confirmados por el responsable (sin cambios retroactivos).
PILOT_LABELS = {
    "PILOT-P1": ({"B05"}, "benign"), "PILOT-P2": ({"B05"}, "benign"), "PILOT-P3": ({"B01"}, "benign"),
    "PILOT-P4": ({"B03"}, "suspicious"), "PILOT-P5": ({"B01", "B02"}, "high_risk"),
    "PILOT-P6": ({"B01", "B02"}, "high_risk"), "PILOT-P7": ({"B01"}, "benign"), "PILOT-P8": ({"B03"}, "suspicious"),
}


@pytest.fixture
def base(repo_root):
    return json.loads((repo_root / BASE).read_text(encoding="utf-8"))


@pytest.fixture
def v02(repo_root):
    return json.loads((repo_root / V02).read_text(encoding="utf-8"))


def _by_id(doc):
    return {a["annotation_id"]: a for a in doc["annotations"]}


def test_v02_references_the_unchanged_v01(repo_root, v02):
    assert v02["schema_version"] == "0.2" and v02["base_schema_version"] == "0.1"
    assert v02["base_file"] == BASE and sha256_file(repo_root / BASE) == v02["base_sha256"]
    assert v02["applies_to_pilot_v1_metrics"] is False


def test_human_review_records_the_authorized_d2_scope(repo_root, v02):
    review = v02["human_review"]
    assert review["status"] == "approved_with_observations"
    assert review["reviewer"] == "Responsable del proyecto" and review["reviewer_name"] is None
    assert review["date"] == "2026-11-01" and review["decision_id"] == "D2"
    assert review["identity_basis"] and review["date_basis"] and review["approval_source"]
    assert (repo_root / review["record"].split("#")[0]).is_file()
    assert len(review["decisions"]) == 7
    assert v02["status"] == "derived_human_review_approved"
    assert set(review["annotation_ids"]) == set(_by_id(v02))
    assert {a["human_review"] for a in v02["annotations"]} == {review["status"]}
    active = {a["annotation_id"] for a in v02["annotations"] if a["record_status"] == "active"}
    for a in v02["annotations"]:
        expected = "verified_review" if a["annotation_id"] in active else "verified_literal"
        assert a["verification_status"] == expected
    change = next(c for c in v02["changes"] if c["change_id"] == "D2")
    assert change["operation"] == "human_review" and change["date"] == review["date"]
    assert set(change["annotation_ids"]) == set(review["annotation_ids"])
    assert change["document_status"] == {"from": "derived_human_review_pending", "to": v02["status"]}
    assert change["human_review_status"] == {"from": "pending", "to": review["status"]}
    update = change["verification_update"]
    assert set(update["annotation_ids"]) == active
    assert (update["field"], update["from"], update["to"]) == (
        "verification_status", "verified_literal", "verified_review")


def test_every_v01_record_is_kept_and_only_logged_fields_change(base, v02):
    new = _by_id(v02)
    logged = {(c["annotation_id"], c["field"]): c for c in v02["changes"] if c["operation"] == "relabel"}
    for change in v02["changes"]:
        if change["operation"] == "human_review":
            update = change["verification_update"]
            logged.update({(aid, update["field"]): update for aid in update["annotation_ids"]})
    for old in base["annotations"]:
        rec = new[old["annotation_id"]]
        for field, value in old.items():
            change = logged.get((old["annotation_id"], field))
            if change:
                assert (change["from"], change["to"]) == (value, rec[field])
            else:
                assert rec[field] == value, (old["annotation_id"], field)
        assert set(rec) - set(old) <= NEW_FIELDS


def test_superseded_records_keep_their_evidence_in_the_replacement(v02):
    recs = _by_id(v02)
    superseded = [a for a in v02["annotations"] if a["record_status"] == "superseded"]
    assert {a["annotation_id"] for a in superseded} == {"A-P006", "A-P018"}
    for old in superseded:
        new = recs[old["superseded_by"]]
        assert new["supersedes"] == old["annotation_id"] and new["record_status"] == "active"
        assert "NO es falsa" in old["supersession_reason"]
        for field in ("behavior_id", "evidence_text", "file_ref", "start_line", "end_line"):
            assert new[field] == old[field]
        assert new["evidence_source"] == "reference_manual" and new["reference_id"] == "REF-BASE-P03-v0"
        assert new["transformation_id"] is None


def test_provenance_vocabulary_and_team_references(repo_root, v02):
    allowed = set(v02["allowed_values"]["evidence_source"])
    config = json.loads((repo_root / "experiments/configurations/pilot_v1.json").read_text(encoding="utf-8"))
    analyzed_samples = {c["sample_id"] for c in config["cases"]}
    with (repo_root / "datasets/metadata/pilot_manifest.csv").open(encoding="utf-8", newline="") as fh:
        manifest = {row["sample_id"]: row for row in csv.DictReader(fh)}
    active = [a for a in v02["annotations"] if a["record_status"] == "active"]
    assert {a["evidence_source"] for a in active} <= allowed
    for a in active:
        if a["evidence_source"] in {"original", "obfuscated_variant"}:
            assert a["sample_id"] in analyzed_samples
            row = manifest[a["sample_id"]]
            assert a["file_ref"] == row["file_location_ref"]
            assert (a["evidence_source"] == "original") == (row["is_original"] == "true")
            assert "/reference/" not in a["file_ref"]
        if a["evidence_source"] == "reference_decoded":
            assert a["transformation_id"].startswith("REF-DECODE-") and a["file_ref"].endswith("_decoded.ps1.txt")
        if a["evidence_source"] == "reference_manual":
            ref = v02["references"][a["reference_id"]]
            assert a["file_ref"] == ref["file_ref"] == manifest[ref["sample_id"]]["file_location_ref"]
            assert "/reference/" in a["file_ref"] and a["transformation_id"] is None
            assert ref["sample_id"] not in analyzed_samples
            if a["sample_id"] in analyzed_samples:
                assert a["context"]["role"] == "reference_comparison"
            else:
                assert a["sample_id"] == ref["sample_id"] and a["context"]["role"] == "evidence"
    # El piloto no tiene salidas del motor ni del modelo en el ground truth.
    assert not {"deobfuscator_recovered", "model_recovered"} & {a["evidence_source"] for a in active}


def test_all_fragments_exist_at_their_lines(repo_root, v02):
    for a in v02["annotations"]:
        lines = (repo_root / a["file_ref"]).read_text(encoding="utf-8").splitlines()
        assert a["evidence_text"] in "\n".join(lines[a["start_line"] - 1:a["end_line"]]), a["annotation_id"]


def test_new_url_evidence_is_only_used_together_with_command_and_call(v02):
    recs = _by_id(v02)
    for url_id, group_id in (("A-P021", "G-P3-B01"), ("A-P022", "G-P7-B01")):
        url = recs[url_id]
        assert url["support_alone"] == "requires_context" and url["start_line"] == 1
        group = next(g for g in v02["evidence_groups"] if g["group_id"] == group_id)
        assert url_id in group["members"] and len(group["members"]) == 3
        assert group["sufficiency"] == "sufficient_together"


def test_context_groups_are_consistent(v02):
    recs = _by_id(v02)
    groups = {g["group_id"]: g for g in v02["evidence_groups"]}
    assert len(recs) == len(v02["annotations"]) == 24
    assert len(groups) == len(v02["evidence_groups"]) == 12
    for g in groups.values():
        assert g["members"] and len(g["members"]) == len(set(g["members"]))
        for member in g["members"]:
            assert recs[member]["sample_id"] == g["sample_id"] and recs[member]["record_status"] == "active"
            ctx = recs[member]["context"]
            assert ctx["role"] == "evidence"
            assert g["group_id"] in ctx["evidence_groups"] + ctx["also_supports_groups"]
            if recs[member]["evidence_source"] == "reference_manual":
                assert g["sample_id"].startswith("PILOT-REF-")
    for a in v02["annotations"]:
        ctx = a["context"]
        memberships = ctx["evidence_groups"] + ctx["also_supports_groups"]
        comparisons = ctx.get("comparison_groups", [])
        assert len(memberships) == len(set(memberships))
        assert not set(memberships) & set(comparisons)
        if a["record_status"] != "active":
            assert not memberships and not comparisons and not ctx["depends_on"]
            continue
        assert memberships or comparisons, a["annotation_id"]
        for gid in memberships:
            assert a["annotation_id"] in groups[gid]["members"]
        for gid in ctx["evidence_groups"]:
            assert a["behavior_id"] == groups[gid]["behavior_id"]
        for gid in comparisons:
            assert groups[gid]["sample_id"] == a["sample_id"]
            assert groups[gid]["behavior_id"] == a["behavior_id"]
            assert a["annotation_id"] not in groups[gid]["members"]
        if ctx["role"] == "reference_comparison":
            assert a["evidence_source"] == "reference_manual"
            assert comparisons and not memberships and not ctx["depends_on"]
        else:
            assert ctx["role"] == "evidence" and memberships and not comparisons
        for dep in ctx["depends_on"]:
            assert dep != a["annotation_id"]
            assert recs[dep]["record_status"] == "active" and recs[dep]["context"]["role"] == "evidence"
            assert recs[dep]["sample_id"] == a["sample_id"]
            assert set(memberships) & set(recs[dep]["context"]["evidence_groups"]
                                          + recs[dep]["context"]["also_supports_groups"])
        if a["support_alone"] == "requires_context" and ctx["role"] == "evidence":
            assert ctx["depends_on"] or ctx["same_line_context"], a["annotation_id"]


def test_manual_provenance_corrections_preserve_evidence_and_are_logged(base, v02):
    old, new = _by_id(base), _by_id(v02)
    changes = {c["change_id"]: c for c in v02["changes"]}
    assert len(changes) == len(v02["changes"])
    for aid, rid in (("A-P003", "REF-BASE-P03-v0"), ("A-P007", "REF-BASE-P04-v0")):
        a, change = new[aid], changes["C-" + aid]
        assert a["reference_id"] == rid and a["evidence_source"] == "reference_manual"
        assert a["changed_in"] == "0.2" and a["record_status"] == "active"
        assert change["annotation_id"] == aid and change["operation"] == "relabel"
        assert (change["field"], change["from"], change["to"]) == (
            "evidence_source", "original", "reference_manual")
        assert change["reference_id"] == {"from": None, "to": rid}
        for field in ("annotation_id", "sample_id", "evidence_text", "file_ref", "start_line", "end_line", "behavior_id"):
            assert a[field] == old[aid][field]


@pytest.mark.parametrize("aid,gid,members", [
    ("A-P023", "G-P3-B01", {"A-P004", "A-P005", "A-P021"}),
    ("A-P024", "G-P7-B01", {"A-P016", "A-P017", "A-P022"}),
])
def test_manual_comparisons_do_not_contribute_to_case_support(v02, aid, gid, members):
    recs = _by_id(v02)
    group = next(g for g in v02["evidence_groups"] if g["group_id"] == gid)
    assert recs[aid]["context"]["comparison_groups"] == [gid]
    assert set(group["members"]) == members
    assert group["sufficiency"] == "sufficient_together"
    assert all(recs[mid]["evidence_source"] == "obfuscated_variant" for mid in members)
    assert all(set(recs[mid]["context"]["depends_on"]) == members - {mid} for mid in members)
    change = next(c for c in v02["changes"] if c["change_id"] == "C-CONTEXT-" + aid)
    assert change["annotation_id"] == aid and change["operation"] == "move_context_link"
    assert change["from_field"] == "context.evidence_groups"
    assert change["to_field"] == "context.comparison_groups" and change["groups"] == [gid]


def test_support_counts_are_independent_of_provenance_corrections(v02):
    active = [a for a in v02["annotations"] if a["record_status"] == "active"]
    assert {a["annotation_id"] for a in active if a["support_alone"] == "individual"} == {
        "A-P001", "A-P002", "A-P003"}
    assert len(active) == 22
    assert sum(a["support_alone"] == "requires_context" for a in active) == 19
    relabeled = {c["annotation_id"] for c in v02["changes"] if c["operation"] == "relabel"}
    assert {"A-P002", "A-P003"} <= relabeled


def test_functional_labels_and_scenario_risk_are_unchanged(repo_root, v02):
    assert set(v02["allowed_values"]["behavior_id"]) == {f"B{i:02}" for i in range(1, 8)}
    with (repo_root / "datasets/metadata/pilot_manifest.csv").open(encoding="utf-8", newline="") as fh:
        manifest = {row["sample_id"]: row for row in csv.DictReader(fh)}
    for sample, (labels, risk) in PILOT_LABELS.items():
        assert set(manifest[sample]["behavior_labels"].split(";")) == labels
        assert manifest[sample]["risk_label"] == risk
        active = {a["behavior_id"] for a in v02["annotations"]
                  if a["sample_id"] == sample and a["record_status"] == "active"}
        assert active == labels, sample

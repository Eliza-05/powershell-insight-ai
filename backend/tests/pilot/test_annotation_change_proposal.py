"""La propuesta de cambios v0.2 es coherente y no altera las anotaciones v0.1."""

import json

from experiments.evaluation.output_guard import sha256_file

PROPOSAL = "datasets/metadata/pilot_annotations_v0.2_change_proposal.json"
BASE = "datasets/metadata/pilot_annotations.json"


def _load(repo_root, rel):
    return json.loads((repo_root / rel).read_text(encoding="utf-8"))


def test_proposal_is_not_applied_and_base_is_unchanged(repo_root):
    proposal = _load(repo_root, PROPOSAL)
    assert proposal["status"] == "proposed_not_applied" and proposal["owner_decision"] is None
    assert sha256_file(repo_root / BASE) == proposal["base_sha256"]


def test_modifications_start_from_the_current_base_values(repo_root):
    base = {a["annotation_id"]: a for a in _load(repo_root, BASE)["annotations"]}
    allowed = _load(repo_root, BASE)["allowed_values"]
    for change in _load(repo_root, PROPOSAL)["changes"]:
        if change["operation"] != "modify":
            continue
        for field, diff in change["fields"].items():
            assert base[change["annotation_id"]][field] == diff["from"]
        assert change["fields"]["verification_status"]["to"] in allowed["verification_status"]


def test_added_annotations_exist_literally_at_their_lines(repo_root):
    base_ids = {a["annotation_id"] for a in _load(repo_root, BASE)["annotations"]}
    for change in _load(repo_root, PROPOSAL)["changes"]:
        if change["operation"] != "add":
            continue
        ann = change["annotation"]
        assert ann["annotation_id"] not in base_ids
        lines = (repo_root / ann["file_ref"]).read_text(encoding="utf-8").splitlines()
        assert ann["evidence_text"] in "\n".join(lines[ann["start_line"] - 1:ann["end_line"]])

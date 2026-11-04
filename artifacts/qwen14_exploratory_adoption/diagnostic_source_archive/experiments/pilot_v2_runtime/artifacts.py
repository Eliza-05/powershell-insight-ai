"""Immutable, content-addressed approvals/freezes. Draft authorship remains historical."""

from __future__ import annotations

import base64
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]


def utc():
    return datetime.now(timezone.utc).isoformat()


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def encode(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def write_new(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(encode(value))


def validate_prepared(root=ROOT):
    manifest = read(root / "datasets/metadata/pilot_v2_manifest.json")
    annotations = read(root / "datasets/metadata/pilot_v2_annotations.json")
    sources, hashes = {}, {}
    assert len(manifest["cases"]) == 48
    for split in ("development", "selection"):
        rows = [r for r in manifest["cases"] if r["split"] == split]
        assert len(rows) == 24 and len({r["family_id"] for r in rows}) == 12
    family_splits = {}
    for case in manifest["cases"]:
        family_splits.setdefault(case["family_id"], set()).add(case["split"])
        for relative in [case["file_ref"], *case["reference_files"]]:
            path=(root/relative).resolve()
            if not path.is_relative_to((root/"datasets/safe_samples/pilot_v2").resolve()) or not path.name.endswith(".ps1.txt"):
                raise ValueError("Only the reviewed inert text sample/reference namespace is allowed")
            data = (root / relative).read_bytes()
            sources[relative] = data.decode("utf-8")
            hashes[relative] = sha(data)
        assert hashes[case["file_ref"]] == case["sha256"]
        assert len((root / case["file_ref"]).read_bytes()) == case["size_bytes"]
    assert all(len(s) == 1 for s in family_splits.values())
    by_id = {r["case_id"]: r for r in manifest["cases"]}
    assert set(by_id["V2-D03"]["expected_labels"]) == {"B02"}
    d03 = sources[by_id["V2-D03"]["file_ref"]].split("\n", 1)[1]
    d04 = sources[by_id["V2-D04"]["file_ref"]]
    decoded = base64.b64decode(re.search(r"-EncodedCommand (\S+)", d04).group(1), validate=True).decode("utf-16le")
    assert d03 == decoded == sources[by_id["V2-D04"]["reference_files"][0]]
    assert decoded.splitlines()[-2:] == ["Add-Type -TypeDefinition $source", "[AcademicBanner]::Text()"]
    assert len(annotations["annotations"]) == 48
    for ann in annotations["annotations"]:
        case = by_id[ann["case_id"]]
        assert ann["expected_labels"] == case["expected_labels"]
        evidence = {e["evidence_id"]: e for e in ann["evidence"]}
        for e in evidence.values():
            text = sources[e["file_ref"]]
            assert text[e["start"]:e["end"]] == e["snippet"]
            for pos, line, col in ((e["start"], e["start_line"], e["start_column"]),
                                   (e["end"], e["end_line"], e["end_column"])):
                assert text.count("\n", 0, pos) + 1 == line and pos-text.rfind("\n", 0, pos) == col
        if case["reference_files"]:
            token = re.search(r"-EncodedCommand (\S+)", sources[case["file_ref"]]).group(1)
            ref = sources[case["reference_files"][0]]
            assert base64.b64decode(token, validate=True).decode("utf-16le") == ref
            assert ann["reference_derivation"]["decoded_sha256"] == sha(ref.encode())
        if ann["case_id"] in {"V2-D03", "V2-D04"}:
            group, = ann["support_groups"]
            assert [evidence[i]["snippet"] for i in group["evidence_ids"]] == decoded.splitlines()
    return {"manifest": manifest, "annotations": annotations, "sources": sources, "source_hashes": hashes}


def formalize(instruction_path, freeze_dir, root=ROOT):
    instruction = Path(instruction_path).read_bytes()
    dataset = validate_prepared(root)
    approved_at = utc()
    approval = {"approval_id": "pilot-v2-owner-global-closure-authorization", "effective_at": approved_at,
                "source_kind": "explicit_current_user_instruction", "source_sha256": sha(instruction),
                "source_text": instruction.decode("utf-8-sig"),
                "scope": "global_owner_batch_acceptance_not_48_independent_votes",
                "accepted_case_ids": [r["case_id"] for r in dataset["manifest"]["cases"]],
                "dataset_approved": True, "r1_criteria_approved": True,
                "download_authorized": True, "inference_authorized": True,
                "dataset_freeze_authorized": True, "selection_prompt_freeze_authorized_after_development": True,
                "maximum_calls": 126, "principal_calls": 102,
                "maximum_development_prompt_revisions": 1,
                "phase2_started": False, "phase2_condition": "later assignment only after all mandatory gates and necessary adjudications pass",
                "independent_human_review_count": 0, "individual_votes_recorded": 0,
                "reviewer_name": None, "signature": None,
                "semantic_assumptions": {"D03_D04": "B02 after explicit AcademicBanner.Text invocation",
                    "S05_S06": "B03 attempted Startup configuration, no observed success",
                    "S13_S14": "B07 conditional synthetic third-party credential export, no real secrets claimed",
                    "S04_S20": "retain with documented syntactic similarity and author-exposure limitation",
                    "S21_S22": "indeterminate, no TN/primary PRF, not benign",
                    "S23_S24": "B01+B02 outer operations, remote payload unknown"}}
    freeze_dir = Path(freeze_dir)
    if freeze_dir.exists():
        raise FileExistsError("Never overwrite a freeze or approval")
    approval_path = root / "experiments/reviews/pilot_v2_owner_global_approval.json"
    write_new(approval_path, approval)
    dataset.update(frozen=True, frozen_at=approved_at,
                   approval_kind="owner_global_batch_acceptance_not_independent_per_case_review",
                   approval_sha256=sha(approval_path.read_bytes()),
                   draft_metadata_preserved_as_provenance=True)
    write_new(freeze_dir / "dataset.json", dataset)
    names = {"thresholds.json": "experiments/configurations/pilot_v2_thresholds_proposed.json",
             "metrics.json": "experiments/configurations/pilot_v2_metrics_proposed.json",
             "schema.json": "experiments/configurations/pilot_v2_response.schema.json",
             "configuration.json": "experiments/configurations/pilot_v2_proposed.json",
             "prompt_r0.md": "experiments/prompts/pilot_analysis_v2_candidate.md"}
    for name, relative in names.items():
        with (freeze_dir / name).open("xb") as stream:
            stream.write((root / relative).read_bytes())
    review = {"status": "accepted_via_owner_global_batch", "approval_sha256": dataset["approval_sha256"],
              "effective_at": approved_at, "independent_individual_review_count": 0,
              "cases": [{"case_id": r["case_id"], "source_sha256": r["sha256"],
                         "status": "accepted_via_owner_global_batch", "individual_review_performed": False,
                         "individual_reviewer": None, "individual_vote": None}
                        for r in dataset["manifest"]["cases"]]}
    write_new(freeze_dir / "effective_review.json", review)
    record = {"freeze_id": freeze_dir.name, "effective_at": approved_at, "dataset_frozen": True,
              "r1_criteria_frozen_and_approved": True, "prompt_selection_frozen": False,
              "schema_version": "pilot-schema-v1", "taxonomy_version": "0.2",
              "protocol": "r1 metrics; single-model r2; D03/D04 pre-freeze correction; explicit closure authorization",
              "approval_path": approval_path.relative_to(root).as_posix(),
              "approval_sha256": dataset["approval_sha256"],
              "files": {p.name: sha(p.read_bytes()) for p in sorted(freeze_dir.iterdir())},
              "source_files": {relative: sha((root / relative).read_bytes()) for relative in (
                  "datasets/metadata/pilot_v2_manifest.json", "datasets/metadata/pilot_v2_manifest.csv",
                  "datasets/metadata/pilot_v2_annotations.json", "experiments/reviews/pilot_v2_human_review.json",
                  *names.values())}}
    write_new(freeze_dir / "FREEZE.json", record)
    return record


def verify_freeze(freeze_dir, root=ROOT):
    freeze_dir = Path(freeze_dir)
    record = read(freeze_dir / "FREEZE.json")
    if not record["dataset_frozen"] or not record["r1_criteria_frozen_and_approved"]:
        raise ValueError("Unapproved freeze")
    for name, digest in record["files"].items():
        if sha((freeze_dir / name).read_bytes()) != digest:
            raise ValueError("Frozen artifact changed: " + name)
    for name, digest in record["source_files"].items():
        if sha((root / name).read_bytes()) != digest:
            raise ValueError("Approved source material changed: " + name)
    approval = root / record["approval_path"]
    if sha(approval.read_bytes()) != record["approval_sha256"]:
        raise ValueError("Approval changed")
    approval_data=read(approval)
    if not all(approval_data.get(k) is True for k in ("dataset_approved","r1_criteria_approved","inference_authorized","dataset_freeze_authorized")):
        raise ValueError("Missing owner approval for this experiment")
    dataset = read(freeze_dir / "dataset.json")
    for relative, digest in dataset["source_hashes"].items():
        if sha((root / relative).read_bytes()) != digest:
            raise ValueError("Sample/reference changed: " + relative)
        if sha(dataset["sources"][relative].encode()) != digest:
            raise ValueError("Frozen text changed: " + relative)
    return dataset

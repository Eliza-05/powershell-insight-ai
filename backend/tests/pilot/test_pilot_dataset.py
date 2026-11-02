"""Coherencia del dataset piloto, de sus metadatos y de las restricciones de seguridad."""

import csv
import hashlib
import json
import re

import pytest

from experiments.evaluation.reference_recovery import decode_encoded_commands

VALID_LABELS = {"B01", "B02", "B03", "B04", "B05", "B06", "B07"}


@pytest.fixture
def manifest(repo_root):
    with (repo_root / "datasets/metadata/pilot_manifest.csv").open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


@pytest.fixture
def annotations(repo_root):
    return json.loads((repo_root / "datasets/metadata/pilot_annotations.json").read_text(encoding="utf-8"))


@pytest.fixture
def config(repo_root):
    return json.loads((repo_root / "experiments/configurations/pilot_v1.json").read_text(encoding="utf-8"))


def test_manifest_matches_template_columns(repo_root, manifest):
    header = (repo_root / "datasets/metadata/manifest_template.csv").read_text(encoding="utf-8").strip().split(",")
    assert list(manifest[0].keys()) == header


def test_manifest_hashes_and_sizes_match_files(repo_root, manifest):
    for row in manifest:
        data = (repo_root / row["file_location_ref"]).read_bytes()
        assert hashlib.sha256(data).hexdigest() == row["sha256"], row["sample_id"]
        assert len(data) == int(row["size_bytes"])


def test_samples_are_inert_text_files_in_pilot_split(manifest):
    for row in manifest:
        assert row["file_location_ref"].endswith(".ps1.txt")
        assert row["split"] == "pilot" and row["evaluation_group"] == "pilot"
        assert set(filter(None, row["behavior_labels"].split(";"))) <= VALID_LABELS


def test_reference_labels_follow_pilot_plan(manifest):
    expected = {"PILOT-P1": ("B05", "benign"), "PILOT-P2": ("B05", "benign"), "PILOT-P3": ("B01", "benign"),
                "PILOT-P4": ("B03", "suspicious"), "PILOT-P5": ("B01;B02", "high_risk"),
                "PILOT-P6": ("B01;B02", "high_risk"), "PILOT-P7": ("B01", "benign"), "PILOT-P8": ("B03", "suspicious")}
    rows = {r["sample_id"]: r for r in manifest}
    for sid, (labels, risk) in expected.items():
        assert (rows[sid]["behavior_labels"], rows[sid]["risk_label"]) == (labels, risk)


def test_only_reserved_domains_are_used(repo_root):
    for path in (repo_root / "datasets/safe_samples/pilot").rglob("*.ps1.txt"):
        for host in re.findall(r"https?://([^/'\"\s]+)", path.read_text(encoding="utf-8")):
            assert host.endswith(("example.com", "example.invalid")), (path.name, host)


def test_annotation_fragments_exist_at_declared_lines(repo_root, annotations):
    for ann in annotations["annotations"]:
        assert ann["behavior_id"] in VALID_LABELS
        lines = (repo_root / ann["file_ref"]).read_text(encoding="utf-8").splitlines()
        span = "\n".join(lines[ann["start_line"] - 1: ann["end_line"]])
        assert ann["evidence_text"] in span, ann["annotation_id"]


def test_every_reference_label_has_evidence(manifest, annotations):
    annotated = {(a["sample_id"], a["behavior_id"]) for a in annotations["annotations"]}
    for row in manifest:
        for label in filter(None, row["behavior_labels"].split(";")):
            assert (row["sample_id"], label) in annotated


@pytest.mark.parametrize("case", ["P2", "P6"])
def test_encoded_cases_decode_to_reference_text(repo_root, case):
    base = repo_root / "datasets/safe_samples/pilot"
    variant = (base / f"PILOT-{case}.ps1.txt").read_text(encoding="utf-8")
    reference = (base / "reference" / f"PILOT-{case}_decoded.ps1.txt").read_text(encoding="utf-8")
    assert decode_encoded_commands(variant) == [reference]


def test_config_cases_exist_in_manifest(repo_root, manifest, config):
    ids = {r["sample_id"] for r in manifest}
    assert [c["case_id"] for c in config["cases"]] == [f"P{i}" for i in range(1, 9)]
    for case in config["cases"]:
        assert case["sample_id"] in ids
        for ref in case["references"]:
            assert (repo_root / ref).is_file()
    assert config["options"]["temperature"] == 0 and "seed" in config["options"]
    assert config["host"].startswith("http://127.0.0.1")


# Llamadas que podrían ejecutar o interpretar contenido analizado.
FORBIDDEN = re.compile(
    r"(?<![.\w])(eval|exec)\s*\(|\b(os\.system|os\.popen|pty\.spawn)\s*\(|\bsubprocess\b"
    r"|powershell(\.exe)?['\"]\s*,|\bpwsh\b['\"]|Invoke-Expression\s*\(",
    re.IGNORECASE,
)


def test_pilot_code_never_executes_analyzed_content(repo_root):
    sources = list((repo_root / "backend/app").rglob("*.py")) + list((repo_root / "experiments").rglob("*.py"))
    assert sources
    for path in sources:
        assert not FORBIDDEN.search(path.read_text(encoding="utf-8")), path

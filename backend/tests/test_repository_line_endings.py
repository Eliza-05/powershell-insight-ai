"""Check historical hashes through Git's checkout filters, without creating a checkout.

Git is required for this repository-integrity check, not by the recovery service.
The historical data, index and Git configuration are only read.
"""

import csv
import hashlib
import json
import subprocess
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize("autocrlf", ["false", "true", "input"])
def test_checkout_filters_preserve_recorded_historical_hashes(autocrlf):
    expected = {}
    pilot = ROOT / "experiments/results/pilot"
    for line in (pilot / "pilot-v1_20261101T001806Z.SHA256SUMS").read_text(encoding="utf-8").splitlines():
        digest, relative = line.split(" *", 1)
        expected[f"experiments/results/pilot/{relative}"] = digest
    for filename in ["pilot_annotations_v0.2.json", "pilot_annotations_v0.2_change_proposal.json"]:
        doc = json.loads((ROOT / "datasets/metadata" / filename).read_text(encoding="utf-8"))
        expected[doc["base_file"]] = doc["base_sha256"]
    derivation = json.loads((pilot / "derived/pilot-v1_20261101T001806Z_review-v2/derivation.json").read_text(encoding="utf-8"))
    expected[derivation["review_file"]] = derivation["review_sha256"]
    with (ROOT / "datasets/metadata/pilot_manifest.csv").open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            expected[row["file_location_ref"]] = row["sha256"]
    assert len(expected) == 18
    for relative, digest in expected.items():
        # HEAD provides the stored blob; current worktree attributes select the filters.
        # -c is per-command only. No checkout, index write or config change occurs.
        filtered = subprocess.run(
            ["git", "-c", f"core.autocrlf={autocrlf}", "cat-file", "--filters", f"HEAD:{relative}"],
            cwd=ROOT, check=True, capture_output=True,
        ).stdout
        assert hashlib.sha256(filtered).hexdigest() == digest, (autocrlf, relative)

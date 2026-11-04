"""Offline post-hoc joins and integrity; corruptions must fail without inference."""
import json
from pathlib import Path
import shutil
import socket

import pytest

from experiments import qwen14_exploratory as x


@pytest.fixture
def local(tmp_path, monkeypatch):
    root = x.ROOT
    out = tmp_path / "artifacts/qwen14_exploratory_adoption"
    history = tmp_path / "artifacts/qwen25_coder14b"
    # Copy only inputs needed by the read-only comparison, never touch canonical history.
    for folder in ("plan", "execution/results", "execution/checkpoints"):
        shutil.copytree(x.HISTORICAL / folder, history / folder)
    for name in ("FREEZE.json", "evaluation.json", "pipeline_A_regression.json", "execution/ledger.jsonl"):
        shutil.copyfile(x.HISTORICAL / name, history / name)
    manifest = x.read(x.OUT / "source_archive_manifest.json")
    for name, entry in manifest["entries"].items():
        archived = tmp_path / entry["archive"]
        archived.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(root / entry["archive"], archived)
        live = tmp_path / name
        live.parent.mkdir(parents=True, exist_ok=True)
        if not live.exists(): shutil.copyfile(root / name, live)
    x.save(out / "source_archive_manifest.json", manifest)
    monkeypatch.setattr(x, "ROOT", tmp_path)
    monkeypatch.setattr(x, "OUT", out)
    monkeypatch.setattr(x, "HISTORICAL", history)
    monkeypatch.setattr(socket, "create_connection", lambda *a, **k: pytest.fail("Network forbidden"))
    monkeypatch.delenv("PSI_PIPELINE_SETTINGS", raising=False)
    return out, history


def test_six_unique_A_and_eight_historical_joins_are_explicit(local):
    out, history = local
    x.compare()
    value = x.read(out / "comparison.json")
    assert value["new_real_inferences"] == 0 and value["unique_development_scripts"] == 6
    assert len(value["units"]) == 6 and len(value["historical_joins"]) == 8
    assert len({r["historical_pipeline_run_id"] for r in value["historical_joins"]}) == 8
    assert sum(not r["automatic_assessment_reused"]["usable"] for r in value["historical_joins"]) == 2
    assert value["metrics"]["global_Qwen_historical_unchanged"] == {"TP": 2, "FP": 3, "FN": 4,
        "precision": 0.4, "recall": 1 / 3, "F1": 4 / 11}
    assert [r["same_model_policy_parameters"] for r in value["pairs"]] == [True, True]


def test_modified_historical_raw_result_is_rejected(local):
    out, history = local
    path = history / "execution/results/Q14-01.json"
    path.write_text(path.read_text(encoding="utf-8") + " ", encoding="utf-8")
    with pytest.raises(ValueError, match="Historical output changed"): x.compare()
    assert not (out / "comparison.json").exists()


def test_modified_archive_is_rejected(local):
    out, history = local
    manifest = x.read(out / "source_archive_manifest.json")
    entry = next(iter(manifest["entries"].values()))
    (x.ROOT / entry["archive"]).write_text("altered", encoding="utf-8")
    with pytest.raises(ValueError, match="Archived diagnostic source mismatch"): x.compare()


def test_partial_and_rejected_outputs_do_not_become_successful_empty_sets():
    scores = x.classification([{"expected": [], "predicted": None}, {"expected": ["B07"], "predicted": []}])
    assert scores["exact"] == 0 and scores["denominator"] == 2 and scores["FN"] == 1

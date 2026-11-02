"""La reevaluación no puede sobrescribir resultados históricos.

Todas las pruebas trabajan sobre una copia temporal de la ejecución v1; la carpeta
histórica solo se lee para copiarla y para comprobar sus hashes registrados.
"""

import json
import shutil

import pytest

from experiments import run_pilot
from experiments.evaluation.output_guard import OutputExistsError, hash_tree, prepare_output_dir, sha256_file

HISTORICAL = "experiments/results/pilot/pilot-v1_20261101T001806Z"


@pytest.fixture
def source(repo_root, tmp_path):
    copy = tmp_path / "pilot-v1_copy"
    shutil.copytree(repo_root / HISTORICAL, copy)
    return copy


def test_historical_results_match_recorded_hashes(repo_root):
    sums = (repo_root / f"{HISTORICAL}.SHA256SUMS").read_text(encoding="utf-8").splitlines()
    recorded = {line.split(" *", 1)[1]: line.split(" ", 1)[0] for line in sums if line}
    assert len(recorded) == 6
    for rel, digest in recorded.items():
        assert sha256_file(repo_root / "experiments/results/pilot" / rel) == digest, rel


def test_evaluate_refuses_to_overwrite_existing_derived_files(source):
    before = hash_tree(source)
    with pytest.raises(OutputExistsError, match="--out-dir"):
        run_pilot.evaluate(source)
    assert hash_tree(source) == before


def test_evaluate_into_new_dir_reproduces_historical_metrics(source, tmp_path):
    before = hash_tree(source)
    out = tmp_path / "reevaluated"
    run_pilot.evaluate(source, out_dir=out)

    assert hash_tree(source) == before
    original = json.loads((source / "summary.json").read_text(encoding="utf-8"))
    recomputed = json.loads((out / "summary.json").read_text(encoding="utf-8"))
    original.pop("evaluated_at"), recomputed.pop("evaluated_at")
    assert recomputed == original
    for name in ("evaluated_runs.jsonl", "runs_table.csv"):
        assert sha256_file(out / name) == sha256_file(source / name), name

    derivation = json.loads((out / "derivation.json").read_text(encoding="utf-8"))
    assert derivation["source_sha256"]["raw_runs.jsonl"] == before["raw_runs.jsonl"]


def test_non_empty_destination_is_rejected(source, tmp_path):
    out = tmp_path / "busy"
    out.mkdir()
    (out / "keep.txt").write_text("x", encoding="utf-8")
    with pytest.raises(OutputExistsError, match="no está vacía"):
        run_pilot.evaluate(source, out_dir=out)
    assert (out / "keep.txt").read_text(encoding="utf-8") == "x"


def test_fresh_run_dir_may_receive_its_first_evaluation(tmp_path):
    run_dir = tmp_path / "fresh"
    run_dir.mkdir()
    (run_dir / "raw_runs.jsonl").write_text("", encoding="utf-8")
    assert prepare_output_dir(run_dir, run_dir, run_pilot.DERIVED_FILES) == run_dir


def test_cli_requires_out_dir_for_evaluate_only(source, monkeypatch):
    monkeypatch.setattr("sys.argv", ["run_pilot.py", "--evaluate-only", str(source)])
    with pytest.raises(SystemExit):
        run_pilot.main()

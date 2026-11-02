"""Genera la evaluación derivada v2 de una ejecución del piloto, sin modificarla.

Uso (desde la raíz del repositorio):
    python experiments/derive_pilot_review.py \
        --results experiments/results/pilot/<carpeta> \
        --review experiments/reviews/<revision>.json \
        --out-dir experiments/results/pilot/derived/<carpeta_nueva>

Lee la carpeta de resultados y la revisión; escribe solo en ``--out-dir``, que debe
estar vacía o no existir. No llama al modelo ni ejecuta ningún script.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path[:0] = [str(Path(__file__).resolve().parents[1] / "backend"), str(Path(__file__).resolve().parents[1])]

from experiments.evaluation import derived_metrics as dm  # noqa: E402
from experiments.evaluation import evidence_review as er  # noqa: E402
from experiments.evaluation import pilot_metrics as pm  # noqa: E402
from experiments.evaluation.output_guard import prepare_output_dir, sha256_file  # noqa: E402
from experiments.run_pilot import META_FILE, RAW_FILE, ROOT, load_case_inputs, load_json  # noqa: E402


def _dump(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def derive(results_dir: Path, review_path: Path, out_dir: Path) -> dict[str, Any]:
    out_dir = prepare_output_dir(out_dir, results_dir)
    meta = load_json(results_dir / META_FILE)
    config = meta["config"]
    records = [json.loads(line) for line in (results_dir / RAW_FILE).read_text(encoding="utf-8").splitlines() if line]
    review = load_json(review_path)
    problems = er.validate(review, records)
    if problems:
        raise SystemExit("La revisión no cuadra con las salidas crudas:\n- " + "\n- ".join(problems))

    cases = load_case_inputs(config)
    with (ROOT / config["manifest_path"]).open(encoding="utf-8", newline="") as fh:
        manifest = {row["sample_id"]: row for row in csv.DictReader(fh)}
    inputs = {}
    for case_id, case in cases.items():
        row = manifest[case["reference"].sample_id]
        inputs[case_id] = {
            "text": case["text"],
            "references": case["references"],
            "input_kind": "original" if row["is_original"] == "true" else "obfuscated_variant",
            "expected_recovered_strings": [s for s in row["expected_recovered_strings"].split(";") if s],
        }
    rows = [pm.evaluate_run(r, cases[r["case_id"]]["reference"], cases[r["case_id"]]["text"],
                            cases[r["case_id"]]["references"]) for r in records]

    metrics = {
        "version": dm.DERIVED_METRICS_VERSION,
        "unsupported_claims_split": dm.split_unsupported(rows),
        "prompt_injection": dm.injection_metrics(records, rows, "P8", inputs["P8"]["text"]),
        "uncertainty": dm.uncertainty_metrics(records, inputs),
        "behaviors_per_run": {str(n): sum(1 for r in rows if len(r["predicted_labels"]) == n)
                              for n in sorted({len(r["predicted_labels"]) for r in rows})},
    }
    review_summary = er.summarize(review, records, inputs)
    derivation = {
        "kind": "derived-evaluation",
        "source_results_dir": results_dir.name,
        "source_sha256": {name: sha256_file(results_dir / name) for name in (RAW_FILE, META_FILE)},
        "review_file": review_path.resolve().relative_to(ROOT).as_posix(),
        "review_sha256": sha256_file(review_path),
        "versions": {"evidence_review": er.REVIEW_VERSION, "derived_metrics": dm.DERIVED_METRICS_VERSION},
        "derived_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "note": ("Evaluación derivada. No sustituye a summary.json ni a semantic_review.json del piloto v1, "
                 "que se conservan sin cambios. Los veredictos de soporte son preliminares (AI-assist) "
                 "y están pendientes de validación humana."),
    }
    _dump(out_dir / "derived_metrics.json", metrics)
    _dump(out_dir / "evidence_review_summary.json", review_summary)
    _dump(out_dir / "derivation.json", derivation)
    return {"metrics": metrics, "evidence_review": review_summary}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--review", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    derive(args.results, args.review, args.out_dir)
    print(f"Evaluación derivada en {args.out_dir}")


if __name__ == "__main__":
    main()

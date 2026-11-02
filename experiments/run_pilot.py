"""Ejecuta el piloto de la Fase 0B y evalúa sus resultados.

Uso (desde la raíz del repositorio):
    python experiments/run_pilot.py --config experiments/configurations/pilot_v1.json
    python experiments/run_pilot.py --evaluate-only experiments/results/pilot/<carpeta> --out-dir <carpeta_nueva>

Los scripts del piloto solo se leen como texto y se envían al modelo; nunca se ejecutan.
La reevaluación solo lee la carpeta de origen y escribe en una carpeta nueva; nunca
sobrescribe resultados derivados existentes.
"""

from __future__ import annotations

import argparse
import csv
import json
import platform
import sys
import urllib.request
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "backend"), str(ROOT)]

from app.schemas.llm_analysis import SCHEMA_VERSION, TAXONOMY_VERSION  # noqa: E402
from app.services.llm.analyzer import OllamaAnalyzer  # noqa: E402
from app.services.llm.prompt import load_prompt  # noqa: E402
from experiments.evaluation import pilot_metrics as pm  # noqa: E402
from experiments.evaluation.output_guard import prepare_output_dir, sha256_file  # noqa: E402

RAW_FILE = "raw_runs.jsonl"
META_FILE = "run_metadata.json"
DERIVED_FILES = ("evaluated_runs.jsonl", "summary.json", "runs_table.csv", "derivation.json")


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_case_inputs(config: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Texto analizado, referencias recuperadas y ground truth de cada caso."""
    with (ROOT / config["manifest_path"]).open(encoding="utf-8", newline="") as fh:
        manifest = {row["sample_id"]: row for row in csv.DictReader(fh)}
    annotations = load_json(ROOT / config["annotations_path"])["annotations"]

    cases = {}
    for case in config["cases"]:
        row = manifest[case["sample_id"]]
        keys: dict[str, list[str]] = {}
        for ann in annotations:
            if ann["sample_id"] == case["sample_id"]:
                keys.setdefault(ann["behavior_id"], []).append(ann["evidence_text"])
        reference = pm.CaseReference(
            case_id=case["case_id"],
            sample_id=case["sample_id"],
            labels=frozenset(filter(None, row["behavior_labels"].split(";"))),
            risk_label=row["risk_label"],
            evidence_keys={b: tuple(v) for b, v in keys.items()},
        )
        cases[case["case_id"]] = {
            "reference": reference,
            "path": row["file_location_ref"],
            "text": (ROOT / row["file_location_ref"]).read_text(encoding="utf-8"),
            "references": {p: (ROOT / p).read_text(encoding="utf-8") for p in case["references"]},
        }
    return cases


def environment_info(client: Any, config: dict[str, Any]) -> dict[str, Any]:
    with urllib.request.urlopen(config["host"].rstrip("/") + "/api/version", timeout=10) as resp:
        ollama_version = json.load(resp).get("version")
    listed = {m.model: m for m in client.list().models}
    if config["model"] not in listed:
        raise SystemExit(f"El modelo {config['model']} no está disponible localmente. Abortando sin ejecutar.")
    entry = listed[config["model"]]
    details = client.show(config["model"]).details
    return {
        "ollama_version": ollama_version,
        "model": config["model"],
        "model_digest": entry.digest,
        "model_size_bytes": entry.size,
        "model_family": details.family,
        "parameter_size": details.parameter_size,
        "quantization_level": details.quantization_level,
        "model_format": details.format,
        "python": platform.python_version(),
        "platform": platform.platform(terse=True),
        "packages": {pkg: version(pkg) for pkg in ("ollama", "pydantic", "pytest")},
    }


def processor_split(client: Any, model: str) -> dict[str, Any] | None:
    """Reparto CPU/GPU del modelo cargado según /api/ps."""
    for m in client.ps().models:
        if m.model == model:
            size, vram = m.size or 0, m.size_vram or 0
            return {"size_bytes": size, "size_vram_bytes": vram,
                    "gpu_fraction": round(vram / size, 3) if size else None,
                    "context_length": getattr(m, "context_length", None)}
    return None


def run(config_path: Path, out_dir: Path | None) -> Path:
    import ollama

    config = load_json(config_path)
    cases = load_case_inputs(config)
    prompt = load_prompt(ROOT / config["prompt_path"])
    client = ollama.Client(host=config["host"])
    env = environment_info(client, config)

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_dir = out_dir or ROOT / "experiments/results/pilot" / f"{config['config_id']}_{stamp}"
    out_dir.mkdir(parents=True, exist_ok=False)
    meta = {
        "config_id": config["config_id"],
        "config": config,
        "config_path": config_path.resolve().relative_to(ROOT).as_posix(),
        "prompt_id": prompt.prompt_id,
        "prompt_sha256": prompt.sha256,
        "schema_version": SCHEMA_VERSION,
        "taxonomy_version": TAXONOMY_VERSION,
        "environment": env,
        "started_at": stamp,
    }
    (out_dir / META_FILE).write_text(json.dumps(meta, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    analyzer = OllamaAnalyzer(client, config["model"], prompt, config["options"], keep_alive=config.get("keep_alive"))
    with (out_dir / RAW_FILE).open("a", encoding="utf-8") as raw:
        for repetition in range(1, config["repetitions"] + 1):
            for case_id, case in cases.items():
                record = analyzer.analyze(case["text"]).to_dict()
                record.update(case_id=case_id, sample_id=case["reference"].sample_id, repetition=repetition,
                              input_path=case["path"], model_digest=env["model_digest"])
                try:
                    record["processor"] = processor_split(client, config["model"])
                except Exception as exc:  # solo informativo
                    record["processor"] = {"error": str(exc)}
                raw.write(json.dumps(record, ensure_ascii=False) + "\n")
                raw.flush()
                status = "ok" if record["schema_valid"] else f"ERROR {record['error_type']}"
                print(f"rep {repetition} {case_id}: {status} {record['wall_seconds']}s", flush=True)

    evaluate(out_dir, config_path)
    return out_dir


def evaluate(results_dir: Path, config_path: Path | None = None, out_dir: Path | None = None) -> dict[str, Any]:
    """Evalúa ``raw_runs.jsonl`` de ``results_dir`` y escribe los derivados en ``out_dir``.

    Sin ``out_dir`` escribe junto a los datos crudos, pero solo si aún no hay derivados
    (caso de una ejecución recién terminada). ``results_dir`` nunca se modifica cuando
    ``out_dir`` es otra carpeta.
    """
    out_dir = prepare_output_dir(out_dir or results_dir, results_dir, DERIVED_FILES)
    meta = load_json(results_dir / META_FILE)
    config = load_json(config_path) if config_path else meta["config"]
    cases = load_case_inputs(config)
    records = [json.loads(line) for line in (results_dir / RAW_FILE).read_text(encoding="utf-8").splitlines() if line]

    rows = []
    for record in records:
        case = cases[record["case_id"]]
        row = pm.evaluate_run(record, case["reference"], case["text"], case["references"])
        row["gpu_fraction"] = (record.get("processor") or {}).get("gpu_fraction")
        rows.append(row)

    summary = {
        "config_id": meta["config_id"],
        "environment": meta["environment"],
        "prompt_id": meta["prompt_id"],
        "schema_version": meta["schema_version"],
        "evaluated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "runs": len(rows),
        "multilabel": pm.multilabel_prf(rows),
        "evidence": pm.evidence_summary(rows),
        "unsupported_claims": sum(len(r["unsupported_claims"]) for r in rows),
        "latency": pm.latency_summary(rows),
        **pm.viability(rows),
    }
    (out_dir / "evaluated_runs.jsonl").write_text(
        "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    _write_table(out_dir / "runs_table.csv", rows)
    if out_dir.resolve() != results_dir.resolve():
        derivation = {
            "kind": "re-evaluation",
            "source_results_dir": results_dir.name,
            "source_sha256": {name: sha256_file(results_dir / name) for name in (RAW_FILE, META_FILE)},
            "config": "external" if config_path else META_FILE,
            "evaluated_at": summary["evaluated_at"],
            "note": "Derivado. Los archivos de la carpeta de origen no se modificaron.",
        }
        (out_dir / "derivation.json").write_text(json.dumps(derivation, indent=2, ensure_ascii=False) + "\n",
                                                 encoding="utf-8")

    for name, crit in summary["criteria"].items():
        print(f"{'PASS' if crit['pass'] else 'FAIL'}  {name}: {crit['value']} (umbral {crit['threshold']})")
    return summary


def _write_table(path: Path, rows: list[dict[str, Any]]) -> None:
    columns = ["case_id", "repetition", "schema_valid", "error_type", "predicted_labels", "reference_labels",
               "exact_match", "predicted_risk", "reference_risk", "obfuscation_techniques", "uncertainty_level",
               "prompt_injection_detected", "citations", "verifiable_citations", "unsupported_claims",
               "wall_seconds", "prompt_tokens", "output_tokens", "gpu_fraction"]
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        for r in rows:
            writer.writerow({
                **{c: r.get(c) for c in columns},
                "predicted_labels": ";".join(r["predicted_labels"]),
                "reference_labels": ";".join(r["reference_labels"]),
                "obfuscation_techniques": ";".join(r["obfuscation_techniques"]),
                "citations": len(r["evidence"]),
                "verifiable_citations": sum(ev["verifiable"] for ev in r["evidence"]),
                "unsupported_claims": ";".join(f"{u['behavior_id']}:{u['reason']}" for u in r["unsupported_claims"]),
            })


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--config", type=Path, default=ROOT / "experiments/configurations/pilot_v1.json")
    parser.add_argument("--out-dir", type=Path,
                        help="Carpeta nueva de resultados. Con --evaluate-only es obligatoria y debe estar vacía.")
    parser.add_argument("--evaluate-only", type=Path, metavar="RESULTS_DIR")
    args = parser.parse_args()
    if args.evaluate_only:
        if args.out_dir is None:
            parser.error("--evaluate-only requiere --out-dir: los resultados existentes no se sobrescriben.")
        evaluate(args.evaluate_only, out_dir=args.out_dir)
        print(f"Evaluación derivada en {args.out_dir}")
    else:
        print(f"Resultados en {run(args.config, args.out_dir)}")


if __name__ == "__main__":
    main()

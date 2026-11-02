"""Two new synthetic B/C functional calls, never a pilot or scientific evaluation.

Run explicitly. No downloads, retries, selection datasets, or analyzed-code execution.
"""
from __future__ import annotations

import argparse
import base64
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.services.pipelines.serialization import save_result
from app.services.pipelines.service import AnalysisService


def write_new(path, value):
    with path.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2, allow_nan=False)
        handle.write("\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", required=True, type=Path, help="New directory; never overwrite any previous run")
    parser.add_argument("--example", choices=["encoded-query", "literal-concat", "unknown-command"], default="encoded-query")
    args = parser.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=False)
    service = AnalysisService()
    # This source is authored here for application development, independent of all pilot data.
    inner = "Get-Process -Id 92047" if args.example == "encoded-query" else "phase2-functional"
    source = ("powershell -EncodedCommand " + base64.b64encode(inner.encode("utf-16le")).decode("ascii")
              if args.example == "encoded-query" else "Write-Output ('phase2-'+'functional')")
    if args.example == "unknown-command":
        inner, source = None, "& $phase2_unresolved"
    write_new(args.out_dir / "source.json", {"purpose": "synthetic_functional_only", "source": source,
              "recovered_fixture": inner, "example": args.example,
              "not_scientific_evaluation": True, "maximum_calls_this_run": 2})
    write_new(args.out_dir / "status_before.json", service.status())
    save_result(service.analyze(source, "A"), args.out_dir / "A.json")
    results = []
    for cfg in ("B", "C"):
        write_new(args.out_dir / (cfg + ".attempt.json"), {"configuration": cfg,
                  "at": datetime.now(timezone.utc).isoformat(), "dispatch_not_yet_confirmed": True})
        result = service.analyze(source, cfg)
        save_result(result, args.out_dir / (cfg + ".json"))
        results.append(result)
        print(json.dumps({"configuration": cfg, "status": result.status, "errors": [e.model_dump() for e in result.errors],
                          "dispatched": result.operational.get("inference_dispatched", False),
                          "seconds": result.duration_seconds}), flush=True)
    summary = {"functional_only": True, "scientific_validation": "pending",
               "inferences_dispatched": sum(bool(r.operational.get("inference_dispatched")) for r in results),
               "statuses": {r.configuration: r.status for r in results},
               "functional_BC_complete": all(r.status in {"completed", "partial"} and r.llm is not None for r in results)}
    write_new(args.out_dir / "summary.json", summary)
    write_new(args.out_dir / "status_after.json", service.status())
    print(json.dumps(summary), flush=True)
    return 0 if summary["functional_BC_complete"] else 2


if __name__ == "__main__":
    raise SystemExit(main())

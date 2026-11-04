"""python -m app.services.pipelines: Python only, input files are never invoked."""
import argparse
import json
from pathlib import Path
import sys

from app.services.pipelines.config import PipelineSettings
from app.services.pipelines.serialization import save_result, serialize
from app.services.pipelines.service import AnalysisService


def main():
    parser = argparse.ArgumentParser(description="Static A/B/C analysis against local Ollama")
    parser.add_argument("--configuration", choices=["A", "B", "C", "ABC"], default="A")
    parser.add_argument("--input", type=Path, help="UTF-8 text file (never executed)")
    parser.add_argument("--output", type=Path, help="New JSON file; fails if it exists")
    parser.add_argument("--settings", type=Path, help="Application settings JSON, never pilot configuration")
    parser.add_argument("--status", action="store_true", help="Read-only Ollama/model/memory inspection; no inference")
    args = parser.parse_args()
    try:
        settings = PipelineSettings.model_validate_json(args.settings.read_text(encoding="utf-8")) if args.settings else PipelineSettings()
        service = AnalysisService(settings)
        if args.status:
            status = service.status()
            print(json.dumps(status, ensure_ascii=False, indent=2))
            return 0 if status["available"] else 2
        if args.input is None:
            parser.error("--input is required unless --status")
        # Bound the file read before allocating/copying a potentially huge sample.
        with args.input.open("rb") as handle:
            raw = handle.read(settings.max_input_bytes + 1)
        if len(raw) > settings.max_input_bytes:
            raise ValueError("Input file exceeds configured byte limit")
        script = raw.decode("utf-8-sig")
        result = service.compare(script) if args.configuration == "ABC" else service.analyze(script, args.configuration)
        if args.output:
            save_result(result, args.output)
        else:
            sys.stdout.buffer.write(serialize(result).encode("utf-8"))
        results = result.results if args.configuration == "ABC" else [result]
        return 0 if all(r.status in {"completed", "partial"} for r in results) else 2
    except Exception as exc:
        print(json.dumps({"error": {"code": "cli_error", "message": str(exc)}}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

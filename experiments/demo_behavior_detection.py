"""Inert Python-only demo: JSON to stdout, no services, network or output files."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.services.behavior_detection import analyze_behaviors  # noqa: E402

SAMPLE = "Get-Process\nInvoke-WebRequest -Uri ('https://'+'example.com/training-only.csv')\n"


def main() -> None:
    print(analyze_behaviors(SAMPLE, source_name="inert-behavior-demo").model_dump_json(indent=2))


if __name__ == "__main__":
    main()

"""Portable, inert Phase 1A demo. Only the Python recovery service is run.

From the repository root: python -B experiments/demo_deobfuscation.py
The PowerShell text below is data; nothing is sent to Ollama or written to disk.
"""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.services.deobfuscation import deobfuscate  # noqa: E402

SAMPLE = "$message = 'training-' + 'only'\nWrite-Output $message\n"


def main() -> None:
    result = deobfuscate(SAMPLE, source_name="inert-demo", input_provenance="original")
    print(result.model_dump_json(indent=2))


if __name__ == "__main__":
    main()

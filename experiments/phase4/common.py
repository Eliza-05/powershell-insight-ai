from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path

from app.services.pipelines.resources import OperationalFailure
from app.services.pipelines.validation import strict_json

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "artifacts/phase4_preparation"
VERSION = "phase4-paired-proposal-v1"
LABELS = [f"B{i:02}" for i in range(1, 8)]


def now():
    return datetime.now(timezone.utc).isoformat()


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(path):
    return strict_json(Path(path).read_text(encoding="utf-8"))


def save(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n"); stream.flush(); os.fsync(stream.fileno())


def require(condition, code):
    if not condition:
        raise OperationalFailure(code, code, "phase4")


def ratio(n, d):
    return n / d if d else None

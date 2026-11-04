"""Load exactly one backend secret. Never export the dotenv file into os.environ."""
from __future__ import annotations

import os
from pathlib import Path

from app.services.pipelines.resources import OperationalFailure

ROOT = Path(__file__).resolve().parents[4]


def read_api_key(root: Path = ROOT) -> str:
    # Process environment takes precedence; dotenv interpolation is deliberately disabled.
    value = os.environ.get("GEMINI_API_KEY")
    if value is None:
        try:
            from dotenv import dotenv_values
            value = dotenv_values(root / ".env", interpolate=False, encoding="utf-8-sig").get("GEMINI_API_KEY")
        except Exception:
            raise OperationalFailure("credential_configuration", "credential_configuration", "gemini") from None
    if not isinstance(value, str) or not value.strip():
        raise OperationalFailure("credential_missing", "credential_missing", "gemini")
    return value.strip()

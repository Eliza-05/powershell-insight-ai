from __future__ import annotations

import copy
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]

VALID_RESULT = {
    "obfuscation_techniques": [],
    "recovered_content": [],
    "behaviors": [
        {
            "behavior_id": "B05",
            "explanation": "Lists running processes sorted by CPU.",
            "evidence": [{"snippet": "Get-Process", "origin": "analyzed_script"}],
            "confidence": "high",
        }
    ],
    "risk_label": "benign",
    "risk_rationale": "Administrative inventory.",
    "uncertainty": {"level": "low", "uninterpretable_fragments": [], "notes": ""},
    "prompt_injection": {"detected": False, "snippets": [], "notes": ""},
    "limitations": [],
}


@pytest.fixture
def valid_result() -> dict:
    return copy.deepcopy(VALID_RESULT)


@pytest.fixture
def repo_root() -> Path:
    return REPO_ROOT

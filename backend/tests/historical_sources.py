"""Read verified archived sources for historical fixtures; never rewrite a freeze.

Current-code regression tests must use current sources. A historical fixture may
select an archived source only by the complete digest in its original manifest.
"""
import hashlib
import importlib.util
from pathlib import Path
import sys


def verified_source(root: Path, name: str, expected: str) -> Path:
    root = root.resolve()
    if len(expected) != 64 or any(c not in "0123456789abcdef" for c in expected):
        raise ValueError("Historical source requires a complete SHA-256")
    candidates = [root / name,
                  root / "artifacts/qwen14_exploratory_adoption/diagnostic_source_archive" / name]
    for candidate in candidates:
        candidate = candidate.resolve()
        if not candidate.is_relative_to(root):
            raise ValueError("Historical source outside repository")
        if candidate.is_file() and hashlib.sha256(candidate.read_bytes()).hexdigest() == expected:
            return candidate
    raise FileNotFoundError(f"Missing verified historical source: {name}, SHA-256 {expected}")


def load_verified_module(root, name, expected, module_name, monkeypatch):
    """Execute only a source matching the historical manifest in a separate module.

    Keep live app modules untouched. Fixtures explicitly bind dependencies between
    their historical modules and restore their controller bindings at teardown.
    """
    source = verified_source(root, name, expected)
    spec = importlib.util.spec_from_file_location(module_name, source)
    module = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, module_name, module)
    spec.loader.exec_module(module)
    return module

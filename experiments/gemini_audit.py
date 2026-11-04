"""Secret-safe local audit. Never prints or persists dotenv contents or credential material."""
from __future__ import annotations

from datetime import datetime, timezone
import importlib.metadata
import json
import os
from pathlib import Path

from experiments.gemini_viability import ROOT, OUT, plan, write
from app.services.llm.gemini_credentials import read_api_key


def audit():
    key = read_api_key().encode("utf-8")
    from dotenv import dotenv_values
    vite_exposure = any(name.startswith("VITE_") and key.decode("utf-8") in (value or "")
                        for folder in (ROOT, ROOT / "frontend") for env_file in folder.glob(".env*")
                        if env_file.name != ".env.example"
                        for name, value in dotenv_values(env_file, interpolate=False).items())
    paths = set()
    for directory, dirs, filenames in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in {".git", ".venv", "node_modules", "__pycache__", ".pytest_cache", "tmp"}]
        paths.update(Path(directory) / name for name in filenames
                     if name == ".env.example" or not (name == ".env" or name.startswith(".env.")))
    leaked = []
    checked = 0
    for path in sorted(paths):
        if not path.is_file():
            continue
        checked += 1
        if key in path.read_bytes():
            leaked.append(path.relative_to(ROOT).as_posix())
    git_checks = json.loads((OUT / "git_checks.json").read_text(encoding="utf-8-sig"))
    result = {"root_dotenv_exists": (ROOT / ".env").is_file(), **git_checks,
              "credential_leak_files": leaked, "files_scanned": checked,
              "credential_in_vite_variables": vite_exposure,
              "scope": "repository including frontend/dist; excludes dotenv files, git, environments, dependencies, caches, and tmp",
              "checked_at": datetime.now(timezone.utc).isoformat()}
    write(OUT / "security_audit.json", result)
    write(OUT / "environment.json", {"packages": sorted(
        ({"name": d.metadata["Name"], "version": d.version} for d in importlib.metadata.distributions()),
        key=lambda d: d["name"].lower())})
    print(json.dumps(result, ensure_ascii=False))
    if leaked or vite_exposure or result["root_dotenv_tracked"] or not result["root_dotenv_ignored"]:
        raise SystemExit(2)


if __name__ == "__main__":
    audit()

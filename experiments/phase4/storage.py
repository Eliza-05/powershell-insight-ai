"""Explicit filesystem binding for a model store inaccessible to the SSH user.

No privilege escalation or implicit fallback. A binding records prior canonical
path metadata and must be included in the reviewed candidate configuration.
Live checks verify the mount mapping and capacity through its accessible anchor;
they do not claim to re-read a protected directory or the model weights.
"""
from __future__ import annotations

import os
from pathlib import Path, PurePosixPath
import re
import shutil
import sys

from experiments.phase4.common import require

VERSION = "linux-model-filesystem-binding-v1"


def _is_linux():
    return sys.platform.startswith("linux")


def _verify_anchor(probe):
    require(probe.resolve(strict=True) == probe and probe.is_dir(), "model_storage_anchor_changed")


def _unescape(value):
    return re.sub(r"\\([0-7]{3})", lambda m: chr(int(m[1], 8)), value)


def _mount_for(path, text):
    matches = []
    for line in text.splitlines():
        before, after = line.split(" - ", 1)
        fields, fs = before.split(), after.split()
        mountpoint = PurePosixPath(_unescape(fields[4]))
        if path.is_relative_to(mountpoint):
            matches.append({"device": fields[2], "root": _unescape(fields[3]),
                            "mountpoint": str(mountpoint), "filesystem": fs[0]})
    require(bool(matches), "model_storage_mount_unavailable")
    depth = max(len(PurePosixPath(m["mountpoint"]).parts) for m in matches)
    deepest = [m for m in matches if len(PurePosixPath(m["mountpoint"]).parts) == depth]
    require(len(deepest) == 1, "model_storage_mount_ambiguous")
    return deepest[0]


def storage_snapshot(binding=None, *, mountinfo=Path("/proc/self/mountinfo")):
    if binding is None:
        model_path = Path(os.getenv("OLLAMA_MODELS") or Path.home() / ".ollama/models")
        return {"model_path": str(model_path), "disk_free_bytes": shutil.disk_usage(model_path).free,
                "storage_accounting": {"method": "direct_path", "probe_path": str(model_path)}}

    require(_is_linux() and isinstance(binding, dict), "model_storage_binding_invalid")
    keys = {"version", "canonical_model_path", "probe_path", "mount", "filesystem_total_bytes",
            "metadata_evidence_sha256"}
    require(set(binding) == keys and binding["version"] == VERSION, "model_storage_binding_invalid")
    require(type(binding["filesystem_total_bytes"]) is int and binding["filesystem_total_bytes"] > 0
            and isinstance(binding["metadata_evidence_sha256"], str)
            and re.fullmatch(r"[a-f0-9]{64}", binding["metadata_evidence_sha256"]) is not None,
            "model_storage_binding_invalid")
    for key in ("canonical_model_path", "probe_path"):
        value = binding[key]
        require(isinstance(value, str) and value.startswith("/") and ".." not in PurePosixPath(value).parts
                and str(PurePosixPath(value)) == value, "model_storage_binding_invalid")
    model_path, probe = PurePosixPath(binding["canonical_model_path"]), Path(binding["probe_path"])
    require(model_path.is_relative_to(PurePosixPath(probe.as_posix())), "model_storage_anchor_not_ancestor")
    override = os.getenv("OLLAMA_MODELS")
    require(override is None or override == str(model_path), "model_storage_environment_mismatch")
    _verify_anchor(probe)
    text = Path(mountinfo).read_text(encoding="utf-8")
    current_model = _mount_for(model_path, text)
    current_probe = _mount_for(PurePosixPath(probe.as_posix()), text)
    require(current_model == current_probe == binding["mount"] and current_model["root"] == "/",
            "model_storage_mount_changed")
    usage = shutil.disk_usage(probe)
    require(usage.total == binding["filesystem_total_bytes"], "model_storage_filesystem_changed")
    return {"model_path": str(model_path), "disk_free_bytes": usage.free,
            "storage_accounting": {"method": VERSION, "probe_path": probe.as_posix(), "mount": current_model,
                "filesystem_total_bytes": usage.total, "metadata_evidence_sha256": binding["metadata_evidence_sha256"],
                "canonical_path_verification": "recorded_metadata; protected path not re-resolved live",
                "live_verification": "accessible ancestor, mount mapping and filesystem capacity",
                "limitation": "Protected descendants and model bytes are not read; concurrent store/symlink changes remain an external-state risk"}}

"""Download only the explicitly authorized tag into Ollama's existing storage."""

import os
from pathlib import Path
import shutil

from .artifacts import ROOT, utc, write_new
from .resources import GIB, snapshot
from .transport import LocalOllama, MODEL


def main():
    out = ROOT / "experiments/cache/pilot_v2_acquisition"
    out.mkdir(parents=True, exist_ok=True)
    if (out / "completed.json").exists():
        raise FileExistsError("Acquisition already recorded; inspect, do not overwrite")
    client = LocalOllama(timeout=3600)
    version, tags, ps = client.json("version"), client.json("tags"), client.json("ps")
    models_path = Path(os.environ.get("OLLAMA_MODELS", str(Path.home() / ".ollama/models"))).resolve()
    if models_path == ROOT or ROOT in models_path.parents:
        raise ValueError("Model storage must be outside the repository")
    disk = shutil.disk_usage(models_path if models_path.exists() else models_path.parent)
    resources = snapshot()
    if ps["models"]:
        raise RuntimeError("Other models resident; do not unload user workloads")
    if resources["available_bytes"] < 8 * GIB or resources["commit_available_bytes"] < 8 * GIB:
        raise RuntimeError("Insufficient pre-load margin: require 6 GiB upper estimate plus 2 GiB free")
    if disk.free < 8 * GIB:
        raise RuntimeError("Insufficient free model-storage space")
    if list((ROOT / "experiments/cache").glob("**/pilot_v2_runtime.lock")):
        raise RuntimeError("Another pilot lock exists")
    initial = {"started_at": utc(), "model": MODEL, "version": version, "tags_before": tags,
               "resident_before": ps, "resources": resources, "configured_storage": str(models_path),
               "disk_free_bytes": disk.free, "sample_execution": False}
    write_new(out / "preflight.json", initial)
    installed = next((m for m in tags["models"] if m["name"] == MODEL), None)
    print(f"Acquisition: {MODEL}; storage={models_path}; free RAM={resources['available_bytes']/GIB:.2f} GiB", flush=True)
    result = None
    if installed is None:
        result = client.json("pull", {"model": MODEL, "stream": False})
        print("Pull completed: " + str(result), flush=True)
    after = client.json("tags")
    installed = next((m for m in after["models"] if m["name"] == MODEL), None)
    if installed is None:
        raise RuntimeError("Requested tag absent after pull")
    show = client.json("show", {"model": MODEL, "verbose": True})
    record = {**initial, "completed_at": utc(), "pull_response": result,
              "model_metadata": installed, "show": show, "tags_after": after,
              "resident_after": client.json("ps"), "resources_after": snapshot()}
    write_new(out / "completed.json", record)
    print(f"Installed digest={installed['digest']}; size={installed['size']}; no inference performed", flush=True)


if __name__ == "__main__":
    main()

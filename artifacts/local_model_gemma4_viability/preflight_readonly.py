"""Repeatable local inspection only: no pull, show, chat, generate or external HTTP.

Run from any directory. Public metadata was archived separately; no samples are read.
Prints JSON to stdout without overwriting the original observation.
"""
from datetime import datetime, timezone
import ctypes as c
from ctypes import wintypes as w
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import urllib.request

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "backend"))
sys.path.insert(0, str(HERE.parents[1]))
from app.services.pipelines.resources import InferenceGate, memory_snapshot
from experiments.pilot_v2_runtime.resources import Entry

GIB = 1024 ** 3


def process_inventory():
    kernel = c.windll.kernel32
    kernel.CreateToolhelp32Snapshot.restype = w.HANDLE
    kernel.Process32FirstW.argtypes = [w.HANDLE, c.POINTER(Entry)]
    kernel.Process32NextW.argtypes = [w.HANDLE, c.POINTER(Entry)]
    kernel.CloseHandle.argtypes = [w.HANDLE]
    handle = kernel.CreateToolhelp32Snapshot(2, 0)
    if handle == w.HANDLE(-1).value:
        raise OSError("Cannot enumerate processes")
    entry = Entry()
    entry.size = c.sizeof(entry)
    rows = []
    try:
        ok = kernel.Process32FirstW(handle, c.byref(entry))
        while ok:
            name = entry.exe.lower()
            if any(term in name for term in ("ollama", "llama", "python", "lmstudio", "lm studio", "vllm")):
                rows.append({"pid": entry.pid, "parent_pid": entry.parent, "name": entry.exe})
            ok = kernel.Process32NextW(handle, c.byref(entry))
    finally:
        kernel.CloseHandle(handle)
    return rows


def main():
    manifest_bytes = (HERE / "registry_manifest.json").read_bytes()
    manifest = json.loads(manifest_bytes)
    config = json.loads((HERE / "registry_config.txt").read_bytes())
    text = json.loads((HERE / "upstream_config.json").read_bytes())["text_config"]
    weights = sum(layer["size"] for layer in manifest["layers"]
                  if layer["mediaType"].rsplit(".", 1)[-1] in {"model", "projector", "draft"})
    context = 8192
    # FP16 K and V, full allocation of the requested context at every layer.
    # Do not assume SWA allocation/sharing optimizations in the untested GGUF runner.
    full = text["layer_types"].count("full_attention")
    sliding = text["layer_types"].count("sliding_attention")
    full_width = full * text["num_global_key_value_heads"] * text["global_head_dim"]
    sliding_width = sliding * text["num_key_value_heads"] * text["head_dim"]
    kv = 2 * 2 * context * (full_width + sliding_width)
    optimized_kv = 4 * (context * full_width + text["sliding_window"] * sliding_width)
    buffers, margin = 2 * GIB, 2 * GIB
    required = weights + kv + buffers + margin
    memory = memory_snapshot()
    model_dir = Path(os.getenv("OLLAMA_MODELS") or Path.home() / ".ollama/models")
    disk = shutil.disk_usage(model_dir)
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    local = {}
    for endpoint in ("version", "tags", "ps"):
        with opener.open("http://127.0.0.1:11434/api/" + endpoint, timeout=5) as response:
            local[endpoint] = json.loads(response.read(1024 * 1024))
    gate = InferenceGate()  # Inspect marker only; never enter or clear the gate.
    result = {
        "observed_at_utc": datetime.now(timezone.utc).isoformat(),
        "model": "gemma4:12b", "manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
        "registry_config": config, "local": local, "memory": memory,
        "model_directory": str(model_dir), "disk": disk._asdict(),
        "process_inventory": process_inventory(), "collector_pid": os.getpid(),
        "circuit_marker": str(gate.marker), "circuit_blocked": gate.marker.exists(),
        "estimate": {"method": "FP16 KV, conservative full allocation; not a measured peak",
                     "num_ctx": context, "tensor_layers_bytes": weights,
                     "kv_bytes": kv, "optimized_swa_kv_bytes_for_comparison": optimized_kv,
                     "buffers_reserve_bytes": buffers, "safety_margin_bytes": margin,
                     "required_available_bytes": required,
                     "required_available_gib": required / GIB,
                     "ram_deficit_bytes": max(0, required - memory["available_bytes"]),
                     "ram_and_commit_sufficient": min(memory["available_bytes"], memory["commit_available_bytes"]) >= required},
        "inference_attempts": 0, "weights_downloaded": False,
        "external_client_exclusion": "Point-in-time inventory only; cannot exclude future/external clients",
        "scope": "Read-only preflight; this program cannot authorize or dispatch inference",
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

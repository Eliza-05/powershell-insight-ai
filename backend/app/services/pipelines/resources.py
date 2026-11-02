"""Read-only Windows RAM/commit sampling and application-wide inference exclusion."""
from __future__ import annotations

import ctypes
import os
from pathlib import Path
import tempfile
import threading

from app.services.pipelines.config import GIB


class OperationalFailure(Exception):
    def __init__(self, code, message, stage="ollama"):
        self.code, self.stage = code, stage
        super().__init__(message)


def memory_snapshot():
    if os.name != "nt":
        raise OperationalFailure("resource_monitor_unavailable", "Windows resource collector required", "resources")

    class Memory(ctypes.Structure):
        _fields_ = [("length", ctypes.c_ulong), ("load", ctypes.c_ulong)] + [
            (name, ctypes.c_ulonglong) for name in ("total", "available", "commit_limit", "commit_available",
                                                   "virtual_total", "virtual_available", "extended")]
    value = Memory()
    value.length = ctypes.sizeof(value)
    if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(value)):
        raise OperationalFailure("resource_monitor_unavailable", "GlobalMemoryStatusEx failed", "resources")
    return {"available_bytes": value.available, "commit_available_bytes": value.commit_available,
            "commit_used_bytes": value.commit_limit - value.commit_available,
            "physical_total_bytes": value.total, "commit_limit_bytes": value.commit_limit}


_PROCESS_LOCK = threading.Lock()


class InferenceGate:
    """Nonblocking byte lock shared by application processes in this Windows user session.

    An interrupted request leaves a persistent circuit marker. Closing the HTTP socket cannot
    prove server-side cancellation completed, so subsequent application calls fail closed.
    """
    def __init__(self, path: Path | None = None):
        self.path = path or Path(tempfile.gettempdir()) / "powershell-insight-phase2-inference.lock"
        self.marker = self.path.with_suffix(".blocked")
        self.handle = None

    def __enter__(self):
        if not _PROCESS_LOCK.acquire(blocking=False):
            raise OperationalFailure("inference_busy", "Another application inference is active")
        try:
            self.handle = self.path.open("a+b")
            self.handle.seek(0, 2)
            if self.handle.tell() == 0:
                self.handle.write(b"0")
                self.handle.flush()
            self.handle.seek(0)
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(self.handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(self.handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            if self.marker.exists():
                raise OperationalFailure("inference_interrupted", "Previous interrupted request; verify Ollama is idle before clearing " + str(self.marker))
        except Exception as exc:
            if self.handle:
                self.handle.close()
            _PROCESS_LOCK.release()
            if isinstance(exc, OperationalFailure):
                raise
            raise OperationalFailure("inference_busy", str(exc)) from exc
        return self

    def block(self, reason):
        # Marker contains no input text or model output.
        self.marker.write_text(reason, encoding="utf-8")

    def __exit__(self, *_):
        self.handle.close()  # Closing descriptor releases OS lock, without unlink races.
        _PROCESS_LOCK.release()


class ResourceMonitor:
    def __init__(self, sampler, cancel, minimum=2 * GIB, interval=1):
        self.sampler, self.cancel, self.minimum, self.interval = sampler, cancel, minimum, interval
        self.samples, self.errors = [], []
        self.violated = False
        self.stop = threading.Event()

    def collect(self):
        try:
            value = self.sampler()
            self.samples.append(value)
            if min(value["available_bytes"], value["commit_available_bytes"]) < self.minimum:
                self.violated = True
        except Exception as exc:
            self.errors.append(str(exc))
            self.violated = True
        if self.violated:
            self.cancel()

    def __enter__(self):
        self.collect()
        self.thread = threading.Thread(target=self.loop, daemon=True)
        self.thread.start()
        return self

    def loop(self):
        while not self.stop.wait(self.interval):
            self.collect()

    def __exit__(self, *_):
        self.stop.set()
        self.thread.join(timeout=3)
        self.collect()

    def summary(self):
        return {"samples": self.samples, "monitor_errors": self.errors, "margin_violated": self.violated,
                "minimum_available_bytes": min((v["available_bytes"] for v in self.samples), default=None),
                "minimum_commit_available_bytes": min((v["commit_available_bytes"] for v in self.samples), default=None)}

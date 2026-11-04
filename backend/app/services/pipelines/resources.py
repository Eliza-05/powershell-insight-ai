"""Read-only Windows RAM/commit sampling and application-wide inference exclusion."""
from __future__ import annotations

import ctypes
import hashlib
import json
import os
from pathlib import Path
import tempfile
import threading
from datetime import datetime, timezone
from uuid import uuid4

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
    def __init__(self, path: Path | None = None, *, allow_interrupted=False):
        self.path = path or Path(tempfile.gettempdir()) / "powershell-insight-phase2-inference.lock"
        self.marker = self.path.with_suffix(".blocked")
        self.handle = None
        self.allow_interrupted = allow_interrupted
        self.owner_nonce = None
        self.history = self.path.with_suffix(".history.jsonl")

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
            if self.marker.exists() and not self.allow_interrupted:
                raise OperationalFailure("inference_interrupted", "Previous interrupted request; verify Ollama is idle before clearing " + str(self.marker))
        except Exception as exc:
            if self.handle:
                self.handle.close()
            _PROCESS_LOCK.release()
            if isinstance(exc, OperationalFailure):
                raise
            raise OperationalFailure("inference_busy", str(exc)) from exc
        return self

    def _event(self, event, **fields):
        value = {"event": event, "at": datetime.now(timezone.utc).isoformat(),
                 "pid": os.getpid(), "owner_nonce": self.owner_nonce, **fields}
        with self.history.open("ab") as stream:
            stream.write((json.dumps(value, ensure_ascii=False) + "\n").encode("utf-8"))
            stream.flush()
            os.fsync(stream.fileno())
        return value

    def _write_marker(self, value, *, exclusive=False):
        with self.marker.open("x" if exclusive else "w", encoding="utf-8") as stream:
            json.dump(value, stream, ensure_ascii=False)
            stream.flush()
            os.fsync(stream.fileno())

    def start(self, request_sha256):
        """Persist intent BEFORE HTTP dispatch. A process crash now leaves a closed circuit."""
        if self.handle is None or self.handle.closed or self.marker.exists():
            raise OperationalFailure("inference_interrupted", "Cannot dispatch without an exclusive, clear gate")
        self.owner_nonce = str(uuid4())
        value = {"state": "dispatch_intent", "owner_nonce": self.owner_nonce, "pid": os.getpid(),
                 "request_sha256": request_sha256, "at": datetime.now(timezone.utc).isoformat()}
        self._write_marker(value, exclusive=True)
        self._event("dispatch_intent", request_sha256=request_sha256)

    def complete(self):
        """Only a terminal server reply permits ordinary completion, never socket closure."""
        if self.handle is None or self.handle.closed:
            raise OperationalFailure("inference_interrupted", "Completion requires the active exclusive gate")
        value = json.loads(self.marker.read_text(encoding="utf-8"))
        if not self.owner_nonce or value.get("owner_nonce") != self.owner_nonce:
            raise OperationalFailure("inference_interrupted", "In-flight marker ownership changed")
        self._event("server_finished", request_sha256=value.get("request_sha256"))
        self.marker.unlink()

    def block(self, reason):
        # Only request hashes and lifecycle metadata: no samples or model output in this journal.
        value = {"state": "interrupted", "reason": str(reason), "pid": os.getpid(),
                 "owner_nonce": self.owner_nonce, "at": datetime.now(timezone.utc).isoformat()}
        self._write_marker(value)
        self._event("interrupted", reason=str(reason))

    def acknowledge_idle(self, *, reviewer, justification, server_has_no_residents):
        """Explicit operator recovery; caller must inspect fresh state under the OS lock.

        A null resident list is necessary, not proof that external clients are excluded.
        The reviewer provides the exclusive-session attestation; this is never automatic.
        """
        if (not self.allow_interrupted or self.handle is None or self.handle.closed
                or not reviewer.strip() or not justification.strip() or not server_has_no_residents):
            raise OperationalFailure("recovery_refused", "Recovery requires a locked gate, named operator, justification and no residents")
        if not self.marker.exists():
            raise OperationalFailure("recovery_refused", "There is no interrupted marker to acknowledge")
        previous = self.marker.read_bytes()
        self._event("operator_acknowledged_idle", reviewer=reviewer, justification=justification,
                    previous_marker_sha256=hashlib.sha256(previous).hexdigest(),
                    previous_marker=previous.decode("utf-8", errors="replace"))
        self.marker.unlink()

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

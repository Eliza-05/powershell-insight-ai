"""Durable, conservative budget: every HTTP attempt counts, including metadata/errors."""
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path

from app.services.pipelines.resources import OperationalFailure


@dataclass(frozen=True)
class MetadataRetryAuthorization:
    """One explicit owner decision, bound to the unchanged first-attempt ledger."""
    authorized: bool
    prior_ledger_sha256: str
    confirmed_at: str
    source: str
    operation: str = "models.list"
    max_total_metadata_requests: int = 2
    max_total_requests: int = 12

    def check(self, prior_ledger: bytes):
        try:
            age = (datetime.now(timezone.utc) - datetime.fromisoformat(self.confirmed_at)).total_seconds()
            valid = (self.authorized is True and self.source == "explicit_owner_authorization"
                     and self.operation == "models.list" and type(self.max_total_metadata_requests) is int
                     and self.max_total_metadata_requests == 2 and type(self.max_total_requests) is int
                     and self.max_total_requests == 12 and 0 <= age < 3600
                     and self.prior_ledger_sha256 == hashlib.sha256(prior_ledger).hexdigest())
        except Exception:
            valid = False
        if not valid:
            raise OperationalFailure("gemini_metadata_retry_not_authorized", "gemini_metadata_retry_not_authorized", "gemini")
        return hashlib.sha256(json.dumps(asdict(self), sort_keys=True).encode("utf-8")).hexdigest()


class RequestBudget:
    LIMIT = 12

    def __init__(self, path: Path):
        self.path = Path(path)
        self.lock = self.path.with_suffix(".lock")

    @contextmanager
    def exclusive(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        try:
            fd = os.open(self.lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        except FileExistsError:
            raise OperationalFailure("gemini_budget_locked", "gemini_budget_locked", "gemini") from None
        try:
            yield
        finally:
            os.close(fd)
            self.lock.unlink()

    def entries(self):
        try:
            if not self.path.exists():
                return []
            entries = [json.loads(line) for line in self.path.read_text(encoding="utf-8").splitlines()]
            if any(e["attempt"] != i + 1 or e["kind"] not in {"models.list", "generateContent"}
                   or not isinstance(e["request_sha256"], str) for i, e in enumerate(entries)):
                raise ValueError
            return entries
        except Exception:
            raise OperationalFailure("gemini_budget_corrupt", "gemini_budget_corrupt", "gemini") from None

    def reserve(self, kind, request_sha256, *, metadata_retry: MetadataRetryAuthorization | None = None):
        with self.exclusive():
            entries = self.entries()
            if kind not in {"models.list", "generateContent"}:
                raise OperationalFailure("gemini_endpoint_forbidden", "gemini_endpoint_forbidden", "gemini")
            if len(entries) >= self.LIMIT:
                raise OperationalFailure("gemini_budget_exhausted", "gemini_budget_exhausted", "gemini")
            second_metadata = kind == "models.list" and any(e["kind"] == kind for e in entries)
            authorization_hash = None
            if second_metadata:
                if metadata_retry is None or len(entries) != 1 or entries[0]["request_sha256"] != request_sha256:
                    raise OperationalFailure("gemini_metadata_already_attempted", "gemini_metadata_already_attempted", "gemini")
                authorization_hash = metadata_retry.check(self.path.read_bytes())
            elif metadata_retry is not None:
                raise OperationalFailure("gemini_metadata_retry_not_authorized", "gemini_metadata_retry_not_authorized", "gemini")
            if not second_metadata and any(e["request_sha256"] == request_sha256 for e in entries):
                raise OperationalFailure("gemini_duplicate_request", "gemini_duplicate_request", "gemini")
            entry = {"attempt": len(entries) + 1, "kind": kind, "request_sha256": request_sha256,
                     "reserved_at": datetime.now(timezone.utc).isoformat()}
            if authorization_hash is not None:
                entry["metadata_retry_authorization_sha256"] = authorization_hash
            with self.path.open("a", encoding="utf-8", newline="\n") as handle:
                handle.write(json.dumps(entry, sort_keys=True) + "\n")
                handle.flush()
                os.fsync(handle.fileno())
            return entry

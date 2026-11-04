"""Deterministic resource accounting; no wall-clock-dependent result decisions."""

from dataclasses import dataclass

from app.schemas.deobfuscation import DeobfuscationLimits


class LimitReached(Exception):
    def __init__(self, limit: str):
        self.limit = limit
        super().__init__(limit)


@dataclass
class Budget:
    limits: DeobfuscationLimits
    work: int = 0
    artifact_bytes: int = 0

    def spend(self, amount: int = 1) -> None:
        if amount > self.limits.max_work_units - self.work:
            raise LimitReached("max_work_units")
        self.work += amount

    def check_value(self, size: int) -> None:
        if size > self.limits.max_artifact_bytes:
            raise LimitReached("max_artifact_bytes")

    def reserve(self, amount: int) -> None:
        if amount > self.limits.max_total_artifact_bytes - self.artifact_bytes:
            raise LimitReached("max_total_artifact_bytes")
        self.artifact_bytes += amount

"""Isolated qwen3-coder:30b profile; reuses the Qwen14 lifecycle and the A/B/C contracts.

qwen3-coder is a non-thinking completion model, so no think parameter is sent (same as Qwen14).
Only this exact model and digest are authorized; there is no pull and no provider fallback.
"""
from __future__ import annotations

from typing import Literal

from pydantic import Field

from app.services.llm.qwen14 import Qwen14Adapter, Qwen14Options, Qwen14Settings, Qwen14Transport
from app.services.pipelines.config import GIB

MODEL = "qwen3-coder:30b"
DIGEST = "06c1097efce0431c2045fe7b2e5108366e43bee1b4603a7aded8f21689e90bca"
# ~18.6 GB Q4_K_M weights + ~0.8 GB f16 KV at 8192 tokens + 2 GiB buffers (rounded up).
RESERVE = 18_600_000_000 + 3 * GIB


class Qwen3CoderSettings(Qwen14Settings):
    model: Literal["qwen3-coder:30b"] = MODEL
    expected_digest: Literal[DIGEST] = DIGEST
    port: Literal[11434] = 11434
    options: Qwen14Options = Field(default_factory=Qwen14Options)
    unloaded_reserve_bytes: int = Field(default=RESERVE, ge=RESERVE, strict=True)


class Qwen3CoderTransport(Qwen14Transport):
    model = MODEL


class Qwen3CoderAdapter(Qwen14Adapter):
    def __init__(self, settings: Qwen3CoderSettings, **kwargs):
        if not isinstance(settings, Qwen3CoderSettings):
            raise TypeError("Qwen3CoderAdapter requires Qwen3CoderSettings")
        kwargs.setdefault("transport_factory", lambda: Qwen3CoderTransport(timeout=settings.timeout_seconds))
        super().__init__(settings, **kwargs)

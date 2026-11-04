"""Immutable request settings and hard resource floors; no implicit .env loading."""
from typing import Literal

from pydantic import Field

from app.schemas.deobfuscation import StrictModel

MODEL = "qwen3.5:4b-q4_K_M"
DIGEST = "d8b0f5e9760cd1682034f292d7ef72ec46f432149be0df7574bf2d6e92e38c04"
GIB = 1024 ** 3


class InferenceOptions(StrictModel):
    temperature: float = Field(default=0, ge=0, le=1, allow_inf_nan=False)
    seed: int = Field(default=42, ge=0, strict=True)
    num_ctx: int = Field(default=8192, ge=4096, le=8192, strict=True)
    num_predict: int = Field(default=2048, ge=256, le=2048, strict=True)
    num_gpu: Literal[0] = 0
    num_thread: int = Field(default=10, ge=1, le=10, strict=True)
    num_batch: int = Field(default=256, ge=1, le=256, strict=True)
    draft_num_predict: Literal[0] = 0
    repeat_penalty: float = Field(default=1.0, ge=1, le=2, allow_inf_nan=False)
    presence_penalty: Literal[0.0] = 0.0
    frequency_penalty: Literal[0.0] = 0.0
    top_k: int = Field(default=20, ge=1, le=100, strict=True)
    top_p: float = Field(default=0.95, gt=0, le=1, allow_inf_nan=False)
    min_p: float = Field(default=0.0, ge=0, le=1, allow_inf_nan=False)


class PipelineSettings(StrictModel):
    model: Literal[MODEL] = MODEL
    expected_digest: Literal[DIGEST] = DIGEST
    port: int = Field(default=11434, ge=1, le=65535, strict=True)
    options: InferenceOptions = Field(default_factory=InferenceOptions)
    think: Literal[False] = False
    keep_alive: Literal["5m"] = "5m"
    timeout_seconds: float = Field(default=300, ge=1, le=300, allow_inf_nan=False)
    max_input_bytes: int = Field(default=65536, ge=1, le=1048576, strict=True)
    # Message bytes plus chat-template reserve; format grammar is not a chat message.
    context_overhead_tokens: int = Field(default=512, ge=512, le=1024, strict=True)
    minimum_margin_bytes: int = Field(default=2 * GIB, ge=2 * GIB, strict=True)
    unloaded_reserve_bytes: int = Field(default=8 * GIB, ge=8 * GIB, strict=True)
    loaded_growth_reserve_bytes: int = Field(default=GIB, ge=GIB, strict=True)

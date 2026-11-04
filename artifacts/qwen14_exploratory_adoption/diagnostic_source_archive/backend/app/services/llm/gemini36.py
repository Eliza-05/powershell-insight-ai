"""Explicit opt-in Gemini 3.6 settings; no deprecated/unsupported sampling controls."""
from dataclasses import dataclass

from app.services.llm.gemini import GeminiAdapter, fail
from app.services.pipelines.provider import response_schema

MODEL36 = "gemini-3.6-flash"


@dataclass(frozen=True)
class Gemini36Settings:
    model: str = MODEL36
    thinking_level: str = "medium"
    max_output_tokens: int = 8192
    timeout_seconds: int = 60

    def __post_init__(self):
        if (self.model, self.thinking_level, self.max_output_tokens, self.timeout_seconds) != (MODEL36, "medium", 8192, 60):
            fail("gemini36_configuration_forbidden")


class Gemini36Adapter(GeminiAdapter):
    def __init__(self, *args, generation=None, **kwargs):
        if generation is not None and not isinstance(generation, Gemini36Settings):
            fail("gemini36_configuration_forbidden")
        super().__init__(*args, generation=generation or Gemini36Settings(), **kwargs)

    def _generation_config(self, context):
        from google.genai import types
        cfg = self.generation
        # Deliberately omit temperature, top_p, top_k, seed, candidate_count and penalties.
        return types.GenerateContentConfig(system_instruction=context.messages[0]["content"],
            max_output_tokens=cfg.max_output_tokens, response_mime_type="application/json",
            response_json_schema=response_schema(),
            thinking_config=types.ThinkingConfig(thinking_level=cfg.thinking_level, include_thoughts=False),
            tools=[], automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True))

    def public_metadata(self):
        return {**super().public_metadata(), "think": self.generation.thinking_level,
                "sampling_controls": "omitted_not_assumed_effective", "experiment": "gemini36-v1"}

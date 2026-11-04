"""Provider-neutral inference boundary; the frozen pilot is not involved."""
from typing import Protocol

from app.schemas.pipeline import ModelReport
from app.services.pipelines.context import AnalysisContext


class InferenceAdapter(Protocol):
    def infer(self, context: AnalysisContext, record: dict) -> dict: ...
    def status(self) -> dict: ...


def response_schema():
    """Keep validation constraints, omit display-only metadata from the wire grammar."""
    def compact(value):
        if isinstance(value, dict):
            return {k: compact(v) for k, v in value.items() if k not in {"title", "description"}}
        if isinstance(value, list):
            return [compact(v) for v in value]
        return value
    return compact(ModelReport.model_json_schema())

"""Explicit local persistence. No implicit sample logging or overwrite."""
import json
from pathlib import Path

from app.schemas.pipeline import ComparisonResult, PipelineResult


def serialize(result: PipelineResult | ComparisonResult) -> str:
    # Revalidate a snapshot, because frozen Pydantic containers can contain mutable lists.
    checked = type(result).model_validate(result.model_dump())
    return json.dumps(checked.model_dump(mode="json"), ensure_ascii=False, indent=2, allow_nan=False) + "\n"


def save_result(result: PipelineResult | ComparisonResult, path: Path) -> None:
    content = serialize(result)
    with Path(path).open("x", encoding="utf-8", newline="\n") as handle:
        handle.write(content)

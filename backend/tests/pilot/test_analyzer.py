import json

import pytest

from app.schemas.llm_analysis import analysis_json_schema
from app.services.llm.analyzer import OllamaAnalyzer
from app.services.llm.prompt import load_prompt

OPTIONS = {"temperature": 0, "seed": 42, "num_ctx": 8192}


class FakeClient:
    def __init__(self, content=None, exc=None):
        self.content, self.exc, self.calls = content, exc, []

    def chat(self, **kwargs):
        self.calls.append(kwargs)
        if self.exc:
            raise self.exc
        return {
            "message": {"role": "assistant", "content": self.content},
            "done_reason": "stop",
            "total_duration": 2_000_000_000,
            "load_duration": 100,
            "prompt_eval_count": 1500,
            "eval_count": 300,
        }


@pytest.fixture
def make_analyzer(repo_root):
    prompt = load_prompt(repo_root / "experiments/prompts/pilot_analysis_v1.md")
    return lambda client: OllamaAnalyzer(client, "qwen2.5-coder:7b", prompt, OPTIONS)


def test_valid_response_is_validated_and_metrics_kept(make_analyzer, valid_result):
    client = FakeClient(json.dumps(valid_result))
    record = make_analyzer(client).analyze("Get-Process")
    assert record.json_valid and record.schema_valid and record.error_type is None
    assert record.parsed().behavior_labels() == ["B05"]
    assert record.metrics["prompt_eval_count"] == 1500
    assert record.prompt_id == "pilot-analysis-v1"


def test_request_uses_schema_options_and_no_streaming(make_analyzer, valid_result):
    client = FakeClient(json.dumps(valid_result))
    make_analyzer(client).analyze("Get-Process")
    sent = client.calls[0]
    assert sent["format"] == analysis_json_schema()
    assert sent["options"] == OPTIONS
    assert sent["stream"] is False


def test_invalid_json_is_recorded_without_retry(make_analyzer):
    client = FakeClient('{"behaviors": [')
    record = make_analyzer(client).analyze("Get-Process")
    assert len(client.calls) == 1
    assert not record.json_valid and record.error_type == "JSONDecodeError"
    assert record.raw_content == '{"behaviors": ['


def test_schema_violation_is_recorded(make_analyzer, valid_result):
    valid_result["behaviors"][0]["behavior_id"] = "B99"
    record = make_analyzer(FakeClient(json.dumps(valid_result))).analyze("Get-Process")
    assert record.json_valid and not record.schema_valid
    assert record.error_type == "SchemaValidationError" and record.result is None


def test_transport_error_is_recorded(make_analyzer):
    record = make_analyzer(FakeClient(exc=ConnectionError("refused"))).analyze("Get-Process")
    assert record.error_type == "ConnectionError" and record.raw_content is None


def test_empty_response_is_an_error(make_analyzer):
    record = make_analyzer(FakeClient("")).analyze("Get-Process")
    assert record.error_type == "EmptyResponse"

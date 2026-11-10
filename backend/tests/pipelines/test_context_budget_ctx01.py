"""CTX-01: pre-dispatch context budget. Synthetic and pilot-v2 DEVELOPMENT inputs only; never F4."""
import inspect
import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.services.llm import qwen3coder_prototype as p
from app.services.llm.qwen14_prototype import load_settings as load_qwen14
from app.services.llm.qwen3coder import Qwen3CoderSettings
from app.services.pipelines.context import message_token_upper_bound
from app.services.pipelines.service import AnalysisService
from app.services.pipelines.strategy import DeterministicLayersStrategy
from experiments.phase4 import prepare as phase4_prepare
from experiments.phase4.profile import context_for

from tests.pipelines.test_qwen3coder_v2 import GIB, InferenceGate, Server, offline, report  # noqa: F401

ROOT = Path(__file__).resolve().parents[3]
PILOT = ROOT / "experiments/freezes/pilot-v2_20261102T194623Z/dataset.json"


def synthetic_script(target_bytes):
    # Benign, development-style text; nothing here is reserved material.
    lines, i = ["# Synthetic CTX-01 fixture. Text only: never execute."], 0
    while sum(len(x) + 1 for x in lines) < target_bytes:
        lines.append(f"$item{i} = 'valor ñandú {i}' ; Write-Output $item{i}")
        i += 1
    return "\n".join(lines) + "\n"


def test_historical_profiles_keep_strict_byte_bound():
    messages = [{"role": "system", "content": "ab"}, {"role": "user", "content": "ñ" * 10}]
    assert message_token_upper_bound(messages, load_qwen14()) == (22, "message-bytes-v2")


def test_qwen3_scales_bytes_and_rounds_up():
    messages = [{"role": "system", "content": "abc"}, {"role": "user", "content": "ñ"}]  # 5 bytes
    assert message_token_upper_bound(messages, p.load_settings()) == (3, "message-bytes-scaled-v3")


@pytest.mark.parametrize("value, ok", [(0.5, True), (1.0, True), (0.49, False), (1.01, False)])
def test_factor_may_only_be_more_conservative(value, ok):
    data = Qwen3CoderSettings().model_dump(mode="json") | {"context_tokens_per_byte_upper_bound": value}
    if ok:
        assert Qwen3CoderSettings.model_validate(data).context_tokens_per_byte_upper_bound == value
    else:
        with pytest.raises(ValidationError):
            Qwen3CoderSettings.model_validate(data)


def test_prepare_uses_the_same_rule_as_the_adapter():
    source = inspect.getsource(phase4_prepare.prepare)
    assert "message_token_upper_bound(context.messages, settings)" in source
    assert 'sum(len(m["content"].encode())' not in source


def service(tmp_path, server):
    settings = p.load_settings()
    sampler = lambda: {"available_bytes": 30 * GIB, "commit_available_bytes": 40 * GIB,
                       "commit_limit_bytes": 60 * GIB, "physical_total_bytes": 32 * GIB}
    adapter = p.PrototypeAdapter(settings, transport_factory=lambda: server, sampler=sampler,
                                 gate_factory=lambda: InferenceGate(tmp_path / "ctx.lock"))
    return AnalysisService(settings, adapter=adapter, strategy=DeterministicLayersStrategy())


def test_input_rejected_by_bytes_now_dispatches_complete_and_untruncated(tmp_path):
    script = synthetic_script(4000)  # policy ~3.2 KB + JSON > 5632 bytes, far below real token limit
    server = Server(report([], risk="unknown", uncertainty="high"))
    result = service(tmp_path, server).analyze(script, "B")
    assert result.status == "completed", result.errors
    op = result.operational
    assert op["context_budget_version"] == "message-bytes-scaled-v3"
    raw_bytes = sum(len(m["content"].encode()) for m in op["request"]["messages"])
    assert raw_bytes + 512 + 2048 > 8192  # the historical rule would have rejected it
    sent = json.loads([c for c in server.calls if c[0] == "chat"][0][1]["messages"][1]["content"])
    assert len(sent["original"]) == len(script)  # nothing truncated


def test_input_above_scaled_bound_is_still_rejected_before_dispatch(tmp_path):
    server = Server(report([], risk="unknown", uncertainty="high"))
    result = service(tmp_path, server).analyze(synthetic_script(12000), "B")
    assert result.status == "error" and result.errors[0].code == "context_limit"
    assert not any(c[0] == "chat" for c in server.calls)


def test_real_input_invading_output_reserve_is_never_published(tmp_path):
    class BigPrompt(Server):
        def json(self, endpoint, payload=None):
            value = super().json(endpoint, payload)
            if endpoint == "chat":
                value["prompt_eval_count"] = 8192 - 2048 + 1
                value["eval_count"] = 100
            return value
    result = service(tmp_path, BigPrompt(report([], risk="unknown", uncertainty="high"))).analyze("Get-Date\n", "B")
    assert result.status == "error" and result.errors[0].code == "context_limit" and result.llm is None


def test_all_pilot_development_inputs_fit_for_B_and_C():
    settings = p.load_settings()
    cases = [c for c in json.loads(PILOT.read_text(encoding="utf-8"))["manifest"]["cases"] if c["split"] == "development"]
    assert len(cases) == 24
    budget = settings.options.num_ctx - settings.options.num_predict - settings.context_overhead_tokens
    for case in cases:
        script = (ROOT / case["file_ref"]).read_text(encoding="utf-8")
        for mode in ("B", "C"):
            bound, version = message_token_upper_bound(context_for(script, mode, settings).messages, settings)
            assert version == "message-bytes-scaled-v3" and bound <= budget, (case["case_id"], mode, bound)

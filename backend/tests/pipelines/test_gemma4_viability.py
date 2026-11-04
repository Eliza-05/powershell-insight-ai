"""Offline campaign guards; no model downloads or real inference."""
import json

import pytest

from app.services.deobfuscation.engine import deobfuscate
from app.services.llm.gemma4 import Gemma4Settings, Gemma4Transport, MODEL, REQUIRED_AVAILABLE
from app.services.pipelines.context import build_context, canonical, sha
from app.services.pipelines.resources import OperationalFailure
from experiments import gemma4_viability as campaign


def test_plan_preserves_previous_order_and_has_verified_nonempty_C():
    cases = campaign.planned_cases()
    assert len(cases) == 8
    assert [c[1] for c in cases] == ["B"] * 6 + ["C"] * 2
    assert [c[3] for c in cases] == [[], ["B02"], [], ["B01", "B02"], ["B07"], None, [], ["B05", "B06"]]
    prompts, schemas = set(), set()
    for _, mode, script, _, _ in cases:
        context = build_context(script, deobfuscate(script) if mode == "C" else None)
        payload = campaign.payload_for(context)
        prompts.add(payload["messages"][0]["content"])
        schemas.add(canonical(payload["format"]))
        user = json.loads(payload["messages"][1]["content"])
        assert set(user) <= {"original", "deterministic_recovery"}
        assert user["original"] == script
        if mode == "C":
            assert any(k != "original" and v for k, v in context.sources.items())
        else:
            assert context.sources == {"original": script}
        assert payload["model"] == MODEL and payload["think"] is False
    assert len(prompts) == len(schemas) == 1


def test_gemma_keeps_cold_floor_without_changing_Qwen():
    from app.services.pipelines.config import PipelineSettings
    cfg = Gemma4Settings()
    assert cfg.minimum_margin_bytes + cfg.unloaded_reserve_bytes == REQUIRED_AVAILABLE
    assert PipelineSettings().model == "qwen3.5:4b-q4_K_M"


@pytest.mark.parametrize("endpoint,payload", [
    ("pull", {"model": MODEL}), ("generate", {"model": MODEL}),
    ("chat", {"model": "gemma4:cloud"}), ("show", {"model": "qwen3.5:4b-q4_K_M"}),
    ("chat", {"model": MODEL}),
])
def test_transport_refuses_unapproved_requests_before_network(monkeypatch, endpoint, payload):
    def forbidden(*args, **kwargs):
        pytest.fail("No socket should be created")
    monkeypatch.setattr("app.services.llm.gemma4.http.client.HTTPConnection", forbidden)
    with pytest.raises(OperationalFailure):
        Gemma4Transport().json(endpoint, payload)


def test_failed_dispatch_is_spent_and_eighth_is_hard_cap(tmp_path, monkeypatch):
    payloads = [{"model": MODEL, "number": i} for i in range(8)]
    calls = [{"case_id": str(i), "request_sha256": sha(canonical(p))} for i, p in enumerate(payloads)]
    monkeypatch.setattr(campaign, "OUT", tmp_path)
    monkeypatch.setattr(campaign, "locked_plan", lambda: {"calls": calls})
    campaign.reserve(payloads[0], calls[0])  # Even if the socket then fails, this is spent.
    with pytest.raises(OperationalFailure):
        campaign.reserve(payloads[0], calls[0])
    assert len(campaign.entries()) == 1
    for p, case in zip(payloads[1:], calls[1:]):
        campaign.reserve(p, case)
    with pytest.raises(OperationalFailure, match="exhausted"):
        campaign.reserve(payloads[0], calls[0])
    assert len(campaign.entries()) == 8


def test_dispatch_reservation_precedes_socket_bytes_and_no_retry(monkeypatch):
    events = []
    class Socket:
        def __init__(self, *args, **kwargs):
            pass
        def request(self, *args, **kwargs):
            events.append("request")
            raise OSError("synthetic connection failure")
        def close(self):
            events.append("close")
    monkeypatch.setattr("app.services.llm.gemma4.http.client.HTTPConnection", Socket)
    transport = Gemma4Transport(authorize_dispatch=lambda p: events.append("reserved"))
    with pytest.raises(OperationalFailure):
        transport.json("chat", {"model": MODEL})
    assert events == ["reserved", "request", "close"]
    assert transport.last_response is None

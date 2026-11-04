"""Fault injection only: never dispatches to Ollama or executes a sample."""
import base64
import http.client
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import subprocess
import sys
import threading
import time

import pytest

from app.services.pipelines.context import build_context
from app.services.pipelines.ollama import LocalTransport, OllamaAdapter
from app.services.pipelines.resources import InferenceGate, OperationalFailure


@contextmanager
def partial_server(*, stall=False):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header("Content-Length", "100")
            self.end_headers()
            self.wfile.write(b'{"partial":')
            self.wfile.flush()
            if stall:
                time.sleep(.3)
        def log_message(self, *args):
            pass
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield server.server_port
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


@pytest.mark.parametrize("stall", [False, True])
def test_partial_raw_response_survives_disconnect_or_timeout(stall):
    with partial_server(stall=stall) as port:
        client = LocalTransport(port, timeout=.1)
        with pytest.raises(OperationalFailure) as error:
            client.json("version")
        assert error.value.code == ("timeout" if stall else "ollama_unavailable")
        assert base64.b64decode(client.last_response["raw_bytes_base64"]) == b'{"partial":'
        assert client.last_response["transport_read_complete"] is False
        assert client.connection is None


def test_new_request_failure_cannot_reuse_previous_raw_response():
    client = LocalTransport()
    client.last_response = {"raw_utf8": "previous endpoint"}
    client.cancel()
    with pytest.raises(OperationalFailure):
        client.json("chat", {})
    assert client.last_response is None


def test_chunked_incomplete_read_preserves_exception_partial_bytes(monkeypatch):
    class Response:
        status = 200
        length = None
        def read1(self, size):
            raise http.client.IncompleteRead(b"partial chunk", 100)
    class Connection:
        def __init__(self, *args, **kwargs):
            pass
        def request(self, *args, **kwargs):
            pass
        def getresponse(self):
            return Response()
        def close(self):
            pass
    monkeypatch.setattr(http.client, "HTTPConnection", Connection)
    client = LocalTransport()
    with pytest.raises(OperationalFailure):
        client.json("version")
    assert base64.b64decode(client.last_response["raw_bytes_base64"]) == b"partial chunk"
    assert client.last_response["transport_read_complete"] is False


def test_crash_after_intent_leaves_persistent_block_without_retry(tmp_path):
    root = Path(__file__).resolve().parents[3]
    path = tmp_path / "gate.lock"
    code = """
import os,sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
from app.services.pipelines.resources import InferenceGate
with InferenceGate(Path(sys.argv[2])) as gate:
    gate.start('a'*64)
    os._exit(17)
"""
    result = subprocess.run([sys.executable, "-B", "-c", code, str(root / "backend"), str(path)], timeout=10)
    assert result.returncode == 17
    with pytest.raises(OperationalFailure) as error:
        with InferenceGate(path):
            pytest.fail("Must not dispatch")
    assert error.value.code == "inference_interrupted"
    assert json.loads(path.with_suffix(".blocked").read_text())["state"] == "dispatch_intent"
    assert len(path.with_suffix(".history.jsonl").read_text().splitlines()) == 1


def test_completion_requires_owned_marker_and_records_lifecycle(tmp_path):
    path = tmp_path / "gate.lock"
    with InferenceGate(path) as gate:
        gate.start("a" * 64)
        value = json.loads(gate.marker.read_text())
        value["owner_nonce"] = "someone else"
        gate.marker.write_text(json.dumps(value))
        with pytest.raises(OperationalFailure):
            gate.complete()
        value["owner_nonce"] = gate.owner_nonce
        gate.marker.write_text(json.dumps(value))
        gate.complete()
        assert not gate.marker.exists()
    assert [json.loads(x)["event"] for x in path.with_suffix(".history.jsonl").read_text().splitlines()] == ["dispatch_intent", "server_finished"]


def test_released_gate_cannot_clear_crash_marker(tmp_path):
    with InferenceGate(tmp_path / "gate.lock") as gate:
        gate.start("a" * 64)
    with pytest.raises(OperationalFailure, match="active exclusive"):
        gate.complete()
    assert gate.marker.exists()


@pytest.mark.parametrize("reviewer,reason,idle", [("", "checked", True), ("operator", "", True), ("operator", "checked", False)])
def test_recovery_refuses_missing_attestation(tmp_path, reviewer, reason, idle):
    path = tmp_path / "gate.lock"
    with InferenceGate(path) as gate:
        gate.start("a" * 64)
        gate.block("timeout")
    with InferenceGate(path, allow_interrupted=True) as gate:
        with pytest.raises(OperationalFailure, match="Recovery requires"):
            gate.acknowledge_idle(reviewer=reviewer, justification=reason, server_has_no_residents=idle)
        assert gate.marker.exists()


def test_explicit_recovery_retains_prior_marker_in_audit(tmp_path):
    path = tmp_path / "gate.lock"
    with InferenceGate(path) as gate:
        gate.start("a" * 64)
        gate.block("timeout")
    with InferenceGate(path, allow_interrupted=True) as gate:
        gate.acknowledge_idle(reviewer="synthetic-test-operator", justification="fixture only", server_has_no_residents=True)
    with InferenceGate(path):
        pass
    events = [json.loads(x) for x in path.with_suffix(".history.jsonl").read_text().splitlines()]
    assert events[-1]["event"] == "operator_acknowledged_idle"
    assert json.loads(events[-1]["previous_marker"])["reason"] == "timeout"


def test_format_grammar_is_not_counted_as_chat_text(tmp_path):
    # This message fits the conservative budget even though the response grammar is large.
    # A refusing gate proves budget checking finished without any HTTP dispatch.
    def refusing_gate():
        raise OperationalFailure("synthetic_gate", "budget passed")
    adapter = OllamaAdapter(gate_factory=refusing_gate)
    context = build_context("x" * 2700)
    record = {}
    with pytest.raises(OperationalFailure) as error:
        adapter.infer(context, record)
    assert record["input_token_upper_bound"] == sum(len(m["content"].encode()) for m in context.messages) + 512
    assert error.value.code == "synthetic_gate"
    assert not record["inference_dispatched"]


def test_operator_recovery_never_treats_empty_ps_as_exclusive_authority():
    from experiments.model_readiness.operations import recover
    def forbidden(**kwargs):
        pytest.fail("Must refuse before network or gate mutation")
    with pytest.raises(OperationalFailure, match="external requests"):
        recover(reviewer="fixture", justification="fixture", exclusive_session_attested=False,
                gate_factory=forbidden, client_factory=forbidden)

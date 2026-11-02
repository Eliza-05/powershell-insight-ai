"""Real loopback HTTP against synthetic servers; no model or sample is run."""
import base64
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import subprocess
import sys
import threading

import pytest

from app.services.pipelines.config import GIB, MODEL, PipelineSettings
from app.services.pipelines.ollama import LocalTransport, OllamaAdapter
from app.services.pipelines.resources import InferenceGate, OperationalFailure, ResourceMonitor
from app.services.pipelines.service import AnalysisService


@contextmanager
def server(body=b'{"version":"synthetic"}', status=200):
    calls = []
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            calls.append((self.command, self.path, b""))
            self.reply()
        def do_POST(self):
            raw = self.rfile.read(int(self.headers["Content-Length"]))
            calls.append((self.command, self.path, raw))
            self.reply()
        def reply(self):
            self.send_response(status)
            self.end_headers()
            try:
                self.wfile.write(body)
            except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
                pass
        def log_message(self, *args):
            pass
    http = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=http.serve_forever, daemon=True)
    thread.start()
    try:
        yield http.server_port, calls
    finally:
        http.shutdown()
        http.server_close()
        thread.join(timeout=2)


def test_wire_protocol_exact_json_and_no_proxy(monkeypatch):
    monkeypatch.setenv("HTTP_PROXY", "http://phase2.example.invalid:9999")
    monkeypatch.setenv("HTTPS_PROXY", "http://phase2.example.invalid:9999")
    with server(b'{"done":true}') as (port, calls):
        client = LocalTransport(port, timeout=2)
        payload = {"model": MODEL, "messages": [{"role": "user", "content": "# ñ: untrusted"}], "truncate": False}
        assert client.json("chat", payload) == {"done": True}
        assert calls[0][:2] == ("POST", "/api/chat")
        assert json.loads(calls[0][2]) == payload
        assert client.connection is None
        assert base64.b64decode(client.last_response["raw_bytes_base64"]) == b'{"done":true}'


@pytest.mark.parametrize(("body", "status"), [
    (b'{"error":"synthetic OOM"}', 500), (b'{}', 302), (b'[]', 200),
    (b'{', 200), (b'{"x":1,"x":2}', 200), (b'{"x":NaN}', 200), (b'\xff', 200),
])
def test_transport_failures_no_repair(body, status):
    with server(body, status) as (port, _):
        client = LocalTransport(port, timeout=2)
        with pytest.raises((OperationalFailure, ValueError, UnicodeError)):
            client.json("chat", {"model": MODEL})
        assert base64.b64decode(client.last_response["raw_bytes_base64"]) == body
        assert client.connection is None


def test_response_size_bound():
    with server(b"x" * 2_097_153) as (port, _):
        with pytest.raises(OperationalFailure, match="2 MiB"):
            LocalTransport(port, timeout=2).json("chat", {"model": MODEL})


def test_cancel_before_dispatch_prevents_wire_request():
    with server() as (port, calls):
        client = LocalTransport(port, timeout=2)
        client.cancel()
        with pytest.raises(OperationalFailure, match="before dispatch"):
            client.json("chat", {"model": MODEL})
        assert not calls


def test_transport_rejects_other_model_without_network():
    with pytest.raises(OperationalFailure, match="authorized model"):
        LocalTransport().json("chat", {"model": "other"})


def test_ollama_oom_is_structured_resource_failure():
    with server(b'{"error":"out of memory"}', 500) as (port, _):
        with pytest.raises(OperationalFailure) as failure:
            LocalTransport(port, timeout=2).json("chat", {"model": MODEL})
        assert failure.value.code == "insufficient_memory"
        assert failure.value.stage == "resources"


def test_monitor_errors_fail_closed():
    cancelled = []
    def fail():
        raise OSError("synthetic collector failure")
    with ResourceMonitor(fail, lambda: cancelled.append(True), interval=.01) as monitor:
        assert monitor.violated
    assert cancelled and monitor.errors
    assert monitor.summary()["minimum_commit_available_bytes"] is None


def test_gate_is_exclusive_across_processes(tmp_path):
    path = tmp_path / "inference.lock"
    root = Path(__file__).resolve().parents[3]
    code = """
import sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
from app.services.pipelines.resources import InferenceGate, OperationalFailure
try:
    with InferenceGate(Path(sys.argv[2])):
        raise SystemExit(8)
except OperationalFailure as exc:
    print(exc.code)
"""
    with InferenceGate(path):
        value = subprocess.run([sys.executable, "-B", "-c", code, str(root / "backend"), str(path)],
                               capture_output=True, check=True, timeout=10)
    assert value.stdout.strip() == b"inference_busy"


def test_readonly_resource_status_without_inference(tmp_path):
    class Transport:
        def json(self, endpoint, payload=None):
            assert endpoint != "chat"
            if endpoint == "version":
                return {"version": "synthetic"}
            if endpoint == "ps":
                return {"models": []}
            from app.services.pipelines.config import DIGEST
            return {"models": [{"name": MODEL, "digest": DIGEST}]}
    state = {"available_bytes": GIB, "commit_available_bytes": GIB}
    adapter = OllamaAdapter(transport_factory=Transport, sampler=lambda: state,
                            gate_factory=lambda: InferenceGate(tmp_path / "gate.lock"))
    status = adapter.status()
    assert status["available"] and not status["resource_ready"] and not status["ready_for_inference"]
    assert not (tmp_path / "gate.lock").exists()


def test_cli_limits_file_read_and_no_overwrite(tmp_path):
    root = Path(__file__).resolve().parents[3]
    import os
    env = dict(os.environ, PYTHONPATH=str(root / "backend"))
    path = tmp_path / "large.ps1.txt"
    path.write_bytes(b"x" * 65537)
    value = subprocess.run([sys.executable, "-B", "-m", "app.services.pipelines", "--input", str(path)],
                           cwd=tmp_path, env=env, capture_output=True)
    assert value.returncode == 2 and json.loads(value.stdout)["error"]["code"] == "cli_error"


def test_output_schema_contains_zero_and_multilabel_contract():
    from app.services.pipelines.ollama import response_schema
    schema = response_schema()
    assert schema["properties"]["behaviors"]["maxItems"] == 7
    assert "minItems" not in schema["properties"]["behaviors"]
    assert schema["additionalProperties"] is False
    assert schema["$defs"]["Citation"]["additionalProperties"] is False

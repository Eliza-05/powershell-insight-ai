"""Temporary HTTP smoke server: real A, explicitly mocked/offline LLM provider."""
from pathlib import Path
import threading
import time

import uvicorn

from app.api.application import create_app
from app.services.llm.qwen14_prototype import PrototypeAdapter, load_settings
from app.services.pipelines.resources import OperationalFailure
from app.services.pipelines.service import AnalysisService


class OfflineTransport:
    def json(self, *args, **kwargs):
        raise OperationalFailure("ollama_unavailable", "SIMULATED offline provider for A-only HTTP smoke test")

    def cancel(self): pass


def make_app():
    settings = load_settings()
    adapter = PrototypeAdapter(settings, transport_factory=OfflineTransport)
    return create_app(service=AnalysisService(settings, adapter=adapter))


if __name__ == "__main__":
    stop = Path(__file__).resolve().parents[3] / "artifacts/qwen14_exploratory_adoption/smoke_stop"
    if stop.exists(): raise RuntimeError("Smoke test already closed")
    server = uvicorn.Server(uvicorn.Config(make_app(), host="127.0.0.1", port=8000, access_log=False))
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    deadline = time.monotonic() + 120
    while thread.is_alive() and time.monotonic() < deadline and not stop.exists():
        time.sleep(0.2)
    server.should_exit = True
    thread.join(timeout=10)
    if thread.is_alive(): raise RuntimeError("Smoke server failed to close")

"""Web request deadlines without changing the Phase 2 adapter or prompt."""
from app.services.pipelines.ollama import LocalTransport


class WebTransport(LocalTransport):
    def __init__(self, port=11434, inference_timeout=300):
        super().__init__(port, timeout=3)
        self.inference_timeout = inference_timeout

    def json(self, endpoint, payload=None):
        self.timeout = self.inference_timeout if endpoint == "chat" else 3
        return super().json(endpoint, payload)

"""Optional synthetic-only HTTP factory; never the default app or scientific selection."""
import json
import os
from pathlib import Path

from experiments.gemini_viability import OUT, adapter
from app.api.application import create_app as create_http_app
from app.services.llm.gemini import FreeTierConfirmation, fail
from app.services.pipelines.service import AnalysisService


def create_app():
    # A failed metadata attempt is not permission to infer from the web application.
    try:
        models = json.loads((OUT / "models.json").read_text(encoding="utf-8"))
        decision = json.loads((OUT / "model_decision.json").read_text(encoding="utf-8"))
        grant_path = os.environ["PSI_GEMINI_FREE_TIER_CONFIRMATION"]
        grant = FreeTierConfirmation(**json.loads(Path(grant_path).read_text(encoding="utf-8")))
        if models["authentication"] != "accepted" or not decision["decided_before_inference"]:
            fail("gemini_preflight_required")
        grant.check(decision["model"])
    except Exception:
        fail("gemini_preflight_required")
    client = adapter(decision["model"], grant)
    app = create_http_app(service=AnalysisService(adapter=client))
    app.add_event_handler("shutdown", client.close)
    return app

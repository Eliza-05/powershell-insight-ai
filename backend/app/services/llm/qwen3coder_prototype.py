"""Explicit local profile "qwen3coder-v2": qwen3-coder:30b + policy v2 + deterministic layers.

Selected only with PSI_LLM_PROFILE=qwen3coder-v2 (see app.api.application). Construction and
status never generate; only an explicit B/C analysis reaches infer(), behind the same owned
dispatch gate as the Qwen14 prototype. No provider fallback, model pull or implicit settings.
"""
from __future__ import annotations

import os
from pathlib import Path

from app.services.llm.qwen14_prototype import authorize_interactive_dispatch
from app.services.llm.qwen3coder import DIGEST, Qwen3CoderAdapter, Qwen3CoderSettings, Qwen3CoderTransport
from app.services.pipelines.strategy import DeterministicLayersStrategy

DECISION = "Q3C-V2-TEAM-2026-11-09"
DISCLAIMER = (
    "qwen3-coder:30b con capas deterministas es experimental y puede equivocarse. "
    "Las citas literales no certifican soporte semántico ni detección de malware. "
    "No usar para decisiones reales de seguridad sin revisión humana."
)


def load_settings():
    path = os.environ.get("PSI_PIPELINE_SETTINGS")
    if path:
        # A settings file for another model fails validation explicitly; never selected silently.
        return Qwen3CoderSettings.model_validate_json(Path(path).read_text(encoding="utf-8"))
    return Qwen3CoderSettings.model_validate(Qwen3CoderSettings().model_dump(mode="json"))


class PrototypeTransport(Qwen3CoderTransport):
    def __init__(self, inference_timeout=300):
        super().__init__(authorize_dispatch=authorize_interactive_dispatch, timeout=3)
        self.inference_timeout = inference_timeout

    def json(self, endpoint, payload=None):
        self.timeout = self.inference_timeout if endpoint == "chat" else 3
        return super().json(endpoint, payload)


class PrototypeAdapter(Qwen3CoderAdapter):
    def __init__(self, settings=None, **kwargs):
        settings = settings or load_settings()
        kwargs.setdefault("transport_factory", lambda: PrototypeTransport(settings.timeout_seconds))
        super().__init__(settings, **kwargs)

    def public_metadata(self):
        return {
            "provider": "ollama", "experimental": True, "decision_id": DECISION,
            "fallback_enabled": False, "generation_on_startup": False,
            "think_parameter_sent": False, "llm_disclaimer": DISCLAIMER,
            "strategy": DeterministicLayersStrategy().versions(),
            "research_status": {
                "llm_status": "experimental_exploratory",
                "experimental_model": self.settings.model,
                "model_selection": "team_decision_2026_11_09",
                "scientific_selection_passed": False,
                "gate_failures_on_selection": ["citations_88_percent", "latency_p95_320s_cpu"],
                "human_adjudications_pending": 8,
                "hypotheses": {"H1": "not_established", "H2": "not_established"},
                "pending_phase4": [
                    "Evaluación del verificador de evidencia con casos nuevos y reglas congeladas",
                    "Revisión humana independiente de los casos con inyección",
                    "Latencia: el p95 en CPU (320 s) supera el plazo de 300 s",
                    "Congelación del diseño, configuración y criterios independientes",
                    "Contraste pendiente de H1/H2; se admiten resultados negativos",
                ],
            },
        }


def create_service():
    from app.services.pipelines.service import AnalysisService
    settings = load_settings()
    return AnalysisService(settings, adapter=PrototypeAdapter(settings), strategy=DeterministicLayersStrategy())

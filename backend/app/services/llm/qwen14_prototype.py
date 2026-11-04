"""Explicit local exploratory profile; independent of the closed diagnostic ledger.

Construction and status never generate. Only an explicit B/C HTTP analysis reaches
infer(); its owned application gate must exist before chat bytes can be dispatched.
There is no provider fallback, model pull, or implicit settings-file loading.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Literal

from app.services.llm.qwen14 import Qwen14Adapter, Qwen14Settings, Qwen14Transport
from app.services.pipelines.context import canonical, sha
from app.services.pipelines.resources import InferenceGate, OperationalFailure
from app.services.pipelines.validation import strict_json

DIGEST = "9ec8897f747e246e970bc5cfdda85d22f1123dc2e3d34978a010a75968716849"
DECISION = "Q14-EXPLORATORY-2026-11-03"
DISCLAIMER = (
    "Qwen2.5-Coder 14B es experimental y puede equivocarse. "
    "Las citas literales no certifican soporte semántico ni detección de malware. "
    "No usar para decisiones reales de seguridad sin revisión humana."
)


class PrototypeSettings(Qwen14Settings):
    expected_digest: Literal[DIGEST] = DIGEST
    port: Literal[11434] = 11434


def load_settings():
    path = os.environ.get("PSI_PIPELINE_SETTINGS")
    if path:
        # A stale Qwen3.5/Gemma/cloud config fails explicitly; never select it.
        return PrototypeSettings.model_validate_json(Path(path).read_text(encoding="utf-8"))
    return PrototypeSettings.model_validate(PrototypeSettings().model_dump(mode="json"))


def authorize_interactive_dispatch(payload):
    marker = InferenceGate().marker
    if not marker.is_file():
        raise OperationalFailure("interactive_dispatch_not_owned", "Falta el bloqueo de análisis explícito")
    value = strict_json(marker.read_text(encoding="utf-8"))
    if (value.get("state") != "dispatch_intent" or value.get("pid") != os.getpid()
            or value.get("request_sha256") != sha(canonical(payload))):
        raise OperationalFailure("interactive_dispatch_not_owned", "El despacho no pertenece a este análisis")


class PrototypeTransport(Qwen14Transport):
    def __init__(self, inference_timeout=300):
        super().__init__(authorize_dispatch=authorize_interactive_dispatch, timeout=3)
        self.inference_timeout = inference_timeout

    def json(self, endpoint, payload=None):
        self.timeout = self.inference_timeout if endpoint == "chat" else 3
        return super().json(endpoint, payload)


class PrototypeAdapter(Qwen14Adapter):
    def __init__(self, settings=None, **kwargs):
        settings = settings or load_settings()
        if not isinstance(settings, PrototypeSettings):
            settings = PrototypeSettings.model_validate(settings.model_dump(mode="json"))
        kwargs.setdefault("transport_factory", lambda: PrototypeTransport(settings.timeout_seconds))
        super().__init__(settings, **kwargs)

    def public_metadata(self):
        return {
            "provider": "ollama", "experimental": True, "decision_id": DECISION,
            "fallback_enabled": False, "generation_on_startup": False,
            "think_parameter_sent": False, "llm_disclaimer": DISCLAIMER,
            "research_status": {
                "llm_status": "experimental_exploratory",
                "experimental_model": self.settings.model,
                "model_selection": "adopted_for_local_exploration",
                "scientific_selection_passed": False,
                "human_adjudications_pending": 8,
                "hypotheses": {"H1": "not_established", "H2": "not_established"},
                "pending_phase4": [
                    "Adjudicación personal de las ocho respuestas Qwen14",
                    "Casos no vistos y referencias revisadas para evaluación independiente",
                    "Congelación del diseño, configuración y criterios independientes",
                    "Autorización posterior de presupuesto de inferencias",
                    "Contraste pendiente de H1/H2; se admiten resultados negativos",
                ],
            },
        }

"""Contrato de la respuesta estructurada del LLM (piloto, Fase 0B).

El mismo modelo Pydantic sirve para dos cosas:

1. Generar el JSON Schema que se envía a Ollama (``format=``) para restringir la salida.
2. Validar la respuesta recibida.

Los tres ejes de docs/behavior_taxonomy.md se mantienen en campos separados:
comportamientos (B01-B07), técnicas de ofuscación y valoración de riesgo.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

SCHEMA_VERSION = "pilot-schema-v1"
TAXONOMY_VERSION = "0.2"


class BehaviorId(str, Enum):
    B01 = "B01"  # Descarga de contenido remoto
    B02 = "B02"  # Ejecución dinámica de código como parte de la lógica funcional
    B03 = "B03"  # Persistencia
    B04 = "B04"  # Modificación de mecanismos de defensa
    B05 = "B05"  # Reconocimiento del sistema
    B06 = "B06"  # Comunicación de red distinta de una descarga
    B07 = "B07"  # Acceso a información de credenciales


class ObfuscationTechnique(str, Enum):
    # Códigos de docs/dataset_selection_plan.md, sección 4.1. OT-OTHER agrupa el resto.
    B64_ENCCMD = "OT-B64-ENCCMD"
    B64_INLINE = "OT-B64-INLINE"
    CONCAT = "OT-CONCAT"
    VARSUB = "OT-VARSUB"
    FORMAT = "OT-FORMAT"
    OTHER = "OT-OTHER"


class RiskLabel(str, Enum):
    BENIGN = "benign"
    SUSPICIOUS = "suspicious"
    HIGH_RISK = "high_risk"
    UNKNOWN = "unknown"


class Level(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class EvidenceOrigin(str, Enum):
    # analyzed_script: fragmento copiado literalmente del script recibido.
    # model_decoded: fragmento que el modelo dice haber decodificado o reconstruido.
    ANALYZED_SCRIPT = "analyzed_script"
    MODEL_DECODED = "model_decoded"


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Evidence(_Strict):
    snippet: str = Field(description="Exact code fragment supporting the finding.")
    origin: EvidenceOrigin


class BehaviorFinding(_Strict):
    behavior_id: BehaviorId
    explanation: str
    evidence: list[Evidence] = Field(min_length=1)
    confidence: Level


class Uncertainty(_Strict):
    level: Level
    uninterpretable_fragments: list[str] = Field(
        description="Fragments the analyst could not interpret statically."
    )
    notes: str


class PromptInjectionAssessment(_Strict):
    detected: bool
    snippets: list[str]
    notes: str


class AnalysisResult(_Strict):
    """Respuesta del modelo. El orden de los campos es el orden de generación."""

    obfuscation_techniques: list[ObfuscationTechnique]
    recovered_content: list[str] = Field(
        description="Content the analyst decoded or reconstructed statically, if any."
    )
    behaviors: list[BehaviorFinding]
    risk_label: RiskLabel
    risk_rationale: str
    uncertainty: Uncertainty
    prompt_injection: PromptInjectionAssessment
    limitations: list[str]

    def behavior_labels(self) -> list[str]:
        """Conjunto ordenado de etiquetas predichas (sin duplicados)."""
        return sorted({finding.behavior_id.value for finding in self.behaviors})

    def duplicate_behavior_ids(self) -> list[str]:
        seen: set[str] = set()
        duplicates: set[str] = set()
        for finding in self.behaviors:
            label = finding.behavior_id.value
            if label in seen:
                duplicates.add(label)
            seen.add(label)
        return sorted(duplicates)


def analysis_json_schema() -> dict[str, Any]:
    """JSON Schema que se pasa a Ollama como ``format``."""
    return AnalysisResult.model_json_schema()

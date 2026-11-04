"""HTTP-specific input and product metadata, separate from scientific contracts."""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class AnalysisRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    script: str = Field(min_length=1, max_length=1_048_576)


PENDING = [
    "Cierre metodológico del piloto v2 interrumpido",
    "Selección definitiva del modelo",
    "Resolución del incidente de memoria para campañas largas",
    "Evaluación científica independiente A/B/C",
    "Adjudicación semántica humana de la calidad del LLM",
    "Confirmación experimental o rechazo de H1/H2",
    "Congelación definitiva de dataset, criterios, prompt, parámetros y entorno",
]


class ApiError(BaseModel):
    code: str
    message: str
    details: list[dict] = Field(default_factory=list)


class ErrorResponse(BaseModel):
    error: ApiError

"""Comprobación literal de evidencias citadas.

Solo responde si un fragmento *existe* en un texto. Que la evidencia respalde
la afirmación es otra pregunta (revisión semántica) y no se decide aquí.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from enum import Enum

_WS = re.compile(r"\s+")


class EvidenceLocation(str, Enum):
    INPUT_EXACT = "input_exact"  # aparece tal cual en el script analizado
    REFERENCE_EXACT = "reference_exact"  # aparece tal cual en un texto de referencia recuperado
    NORMALIZED_ONLY = "normalized_only"  # solo coincide ignorando espacios y mayúsculas
    NOT_FOUND = "not_found"
    EMPTY = "empty"


def normalize(text: str) -> str:
    return _WS.sub(" ", text).strip().casefold()


def locate(snippet: str, analyzed: str, references: Mapping[str, str] | None = None) -> tuple[EvidenceLocation, str | None]:
    """Devuelve dónde aparece ``snippet`` y, si es una referencia, cuál.

    Orden de prioridad: script analizado, referencias recuperadas, coincidencia normalizada.
    Los extremos en blanco del fragmento se ignoran; el interior debe coincidir exactamente.
    """
    references = references or {}
    needle = snippet.strip()
    if not needle:
        return EvidenceLocation.EMPTY, None
    if needle in analyzed:
        return EvidenceLocation.INPUT_EXACT, None
    for name, text in references.items():
        if needle in text:
            return EvidenceLocation.REFERENCE_EXACT, name
    normalized = normalize(needle)
    for name, text in {"analyzed": analyzed, **references}.items():
        if normalized in normalize(text):
            return EvidenceLocation.NORMALIZED_ONLY, name
    return EvidenceLocation.NOT_FOUND, None


def is_verifiable(location: EvidenceLocation) -> bool:
    """Cuenta para el criterio de viabilidad: existe en el script o en contenido recuperado verificable."""
    return location in (EvidenceLocation.INPUT_EXACT, EvidenceLocation.REFERENCE_EXACT)

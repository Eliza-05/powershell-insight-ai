"""Carga de plantillas de prompt versionadas y construcción de mensajes.

El script analizado se inserta como texto delimitado. Nunca se interpreta ni se ejecuta.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path

SYSTEM_MARKER = "=== SYSTEM ==="
USER_MARKER = "=== USER_TEMPLATE ==="
SCRIPT_BEGIN = "<<<BEGIN_UNTRUSTED_POWERSHELL_SCRIPT>>>"
SCRIPT_END = "<<<END_UNTRUSTED_POWERSHELL_SCRIPT>>>"

_PROMPT_ID = re.compile(r"^prompt_id:\s*(\S+)", re.MULTILINE)


class PromptError(ValueError):
    pass


@dataclass(frozen=True)
class PromptTemplate:
    prompt_id: str
    system: str
    user_template: str
    sha256: str

    def build_messages(self, script: str) -> list[dict[str, str]]:
        # Si el script contiene los delimitadores podría "cerrar" el bloque de datos.
        if SCRIPT_BEGIN in script or SCRIPT_END in script:
            raise PromptError("El script contiene los delimitadores reservados del prompt.")
        system = _fill_markers(self.system)
        # El script se inserta al final para que su contenido no se trate como marcador.
        user = _fill_markers(self.user_template).replace("{script}", script)
        return [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]


def _fill_markers(text: str) -> str:
    return text.replace("{script_begin}", SCRIPT_BEGIN).replace("{script_end}", SCRIPT_END)


def load_prompt(path: Path) -> PromptTemplate:
    raw = path.read_text(encoding="utf-8")
    match = _PROMPT_ID.search(raw)
    if not match:
        raise PromptError(f"{path} no declara prompt_id.")
    if raw.count(SYSTEM_MARKER) != 1 or raw.count(USER_MARKER) != 1:
        raise PromptError(f"{path} debe contener una sección SYSTEM y una USER_TEMPLATE.")
    _, rest = raw.split(SYSTEM_MARKER)
    system, user_template = rest.split(USER_MARKER)
    if "{script}" not in user_template:
        raise PromptError(f"{path}: USER_TEMPLATE no contiene {{script}}.")
    return PromptTemplate(
        prompt_id=match.group(1),
        system=system.strip(),
        user_template=user_template.strip(),
        sha256=hashlib.sha256(raw.encode("utf-8")).hexdigest(),
    )

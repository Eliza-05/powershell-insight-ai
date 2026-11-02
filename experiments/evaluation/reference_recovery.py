"""Transformaciones textuales de referencia para el piloto.

Sirven para preparar y comprobar el contenido de referencia de los casos codificados
(P2, P6). Son transformaciones controladas y conocidas, hechas en Python sin ejecutar
PowerShell. **No son el desofuscador de la Fase 1** y sus salidas no se usan como
resultado de ninguna configuración experimental.
"""

from __future__ import annotations

import base64
import re

LAUNCHER_PREFIX = "powershell.exe -NoProfile -EncodedCommand "

_ENCODED_ARG = re.compile(r"-(?:EncodedCommand|enc|e)\s+([A-Za-z0-9+/=]+)", re.IGNORECASE)


def encode_command(script: str) -> str:
    """Base64 de ``script`` en UTF-16LE, como espera ``-EncodedCommand``."""
    return base64.b64encode(script.encode("utf-16-le")).decode("ascii")


def build_encoded_launcher(script: str) -> str:
    return LAUNCHER_PREFIX + encode_command(script) + "\n"


def decode_encoded_commands(text: str) -> list[str]:
    """Decodifica cada argumento de ``-EncodedCommand`` encontrado en ``text``."""
    return [
        base64.b64decode(match.group(1), validate=True).decode("utf-16-le")
        for match in _ENCODED_ARG.finditer(text)
    ]

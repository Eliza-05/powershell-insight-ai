"""Protección de resultados históricos frente a sobrescrituras.

Toda evaluación derivada se escribe en una carpeta propia: vacía o inexistente,
y distinta de la carpeta de resultados de origen si esta ya contiene archivos
derivados. Las comprobaciones ocurren antes de escribir nada.
"""

from __future__ import annotations

import hashlib
from collections.abc import Iterable
from pathlib import Path


class OutputExistsError(FileExistsError):
    """El destino ya contiene archivos que no deben sobrescribirse."""


def prepare_output_dir(out_dir: Path, source_dir: Path, protected: Iterable[str] = ()) -> Path:
    """Valida ``out_dir`` y lo crea si hace falta.

    - Si ``out_dir`` es la propia ``source_dir``, solo se admite cuando ninguno de
      ``protected`` existe todavía (primera evaluación tras una ejecución nueva).
    - En cualquier otro caso, ``out_dir`` debe no existir o estar vacío.
    """
    out_dir, source_dir = Path(out_dir), Path(source_dir)
    if out_dir.resolve() == source_dir.resolve():
        existing = sorted(name for name in protected if (out_dir / name).exists())
        if existing:
            raise OutputExistsError(
                f"{out_dir} ya contiene resultados derivados ({', '.join(existing)}). "
                "No se sobrescriben: indica una carpeta de salida nueva con --out-dir."
            )
        return out_dir
    if out_dir.exists() and any(out_dir.iterdir()):
        raise OutputExistsError(f"La carpeta de salida {out_dir} no está vacía. Usa una carpeta nueva.")
    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir


def sha256_file(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def hash_tree(directory: Path) -> dict[str, str]:
    """SHA-256 de cada archivo bajo ``directory``, con rutas relativas en formato POSIX."""
    directory = Path(directory)
    return {p.relative_to(directory).as_posix(): sha256_file(p) for p in sorted(directory.rglob("*")) if p.is_file()}

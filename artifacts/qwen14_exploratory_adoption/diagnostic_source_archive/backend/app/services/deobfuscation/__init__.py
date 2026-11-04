"""Public Python API for Phase 1A. No LLM, HTTP, file I/O or PowerShell dependencies."""

from .engine import deobfuscate

__all__ = ["deobfuscate"]

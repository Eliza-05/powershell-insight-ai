"""Public static behavior API; no script execution, external services or file I/O."""

from .engine import analyze_behaviors

__all__ = ["analyze_behaviors"]

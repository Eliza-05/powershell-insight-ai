"""Comment blanking BEFORE the LLM ("protection outside the model").

Uses the repository lexer to find PowerShell comments (# line and <# #> block comments; a '#'
inside a string is not a comment). Every comment character is replaced by a space and newlines
are kept, so offsets, lines and columns of all code are unchanged: a citation copied from the
blanked text is literal at the same position in the real original, and validation still runs
against the unmodified script. Comments are inert under taxonomy 0.2, so labels do not change.

Limits: strings are NOT altered (an instruction inside a string still reaches the model), and the
model can no longer report an injection that lived only in a comment.
"""
from __future__ import annotations

from dataclasses import dataclass

from app.schemas.deobfuscation import DeobfuscationLimits
from app.services.deobfuscation.budget import Budget, LimitReached
from app.services.deobfuscation.lexer import lex

VERSION = "comment-blanking-v2-diagnostics"


@dataclass(frozen=True)
class SanitizedText:
    text: str
    spans: tuple[tuple[int, int], ...]
    diagnostics: tuple[dict, ...]


def sanitize_comments(text: str) -> SanitizedText:
    """Preserve uncertain regions and expose every lexer diagnostic to the caller."""
    limits = DeobfuscationLimits(max_input_bytes=max(1, len(text.encode("utf-8"))))
    try:
        tokens, issues = lex(text, Budget(limits))
    except LimitReached as exc:
        return SanitizedText(text, (), ({"start": 0, "end": len(text), "fatal": True,
            "reason": "Sanitization budget exhausted; original retained: " + exc.limit},))
    diagnostics = tuple({"start": i.start, "end": i.end, "reason": i.reason, "fatal": i.fatal} for i in issues)
    # A fatal issue overlapping a comment (e.g. an unterminated block) makes that
    # region uncertain. Never erase it silently, even though the lexer emits COMMENT.
    spans = tuple((t.start, t.end) for t in tokens if t.kind == "COMMENT" and not any(
        i.fatal and t.start < i.end and i.start < t.end for i in issues))
    chars = list(text)
    for start, end in spans:
        for i in range(start, end):
            if chars[i] not in "\r\n":
                chars[i] = " "
    return SanitizedText("".join(chars), spans, diagnostics)


def comment_spans(text: str) -> list[tuple[int, int]]:
    return list(sanitize_comments(text).spans)


def blank_comments(text: str) -> tuple[str, list[tuple[int, int]]]:
    result = sanitize_comments(text)
    out, spans = result.text, list(result.spans)
    if len(out) != len(text):  # pragma: no cover - defensive invariant
        raise ValueError("Comment blanking changed offsets")
    return out, spans

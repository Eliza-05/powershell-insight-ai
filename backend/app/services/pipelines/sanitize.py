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

from app.schemas.deobfuscation import DeobfuscationLimits
from app.services.deobfuscation.budget import Budget
from app.services.deobfuscation.lexer import lex

VERSION = "comment-blanking-v1"


def comment_spans(text: str) -> list[tuple[int, int]]:
    limits = DeobfuscationLimits(max_input_bytes=max(1, len(text.encode("utf-8"))))
    tokens, _issues = lex(text, Budget(limits))
    return [(t.start, t.end) for t in tokens if t.kind == "COMMENT"]


def blank_comments(text: str) -> tuple[str, list[tuple[int, int]]]:
    spans = comment_spans(text)
    chars = list(text)
    for start, end in spans:
        for i in range(start, end):
            if chars[i] not in "\r\n":
                chars[i] = " "
    out = "".join(chars)
    if len(out) != len(text):  # pragma: no cover - defensive invariant
        raise ValueError("Comment blanking changed offsets")
    return out, spans

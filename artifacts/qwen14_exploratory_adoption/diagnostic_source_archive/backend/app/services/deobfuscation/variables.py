"""Conservative, layer-local bindings. No scopes, command results or runtime environment."""

import re
from collections import Counter
from dataclasses import dataclass

from .lexer import Token

# These names do not denote ordinary independent user string bindings.
RESERVED = {"true", "false", "null", "args", "input", "this", "_", "psitem", "matches", "error",
            "home", "pwd", "pid", "host", "profile", "executioncontext", "psversiontable",
            "psscriptroot", "pscommandpath", "myinvocation", "psboundparameters", "foreach", "switch"}
CONTROL = {"if", "else", "elseif", "for", "foreach", "while", "do", "until", "switch", "function",
           "filter", "class", "enum", "param", "try", "catch", "finally", "trap", "data", "using",
           "begin", "process", "end", "dynamicparam", "workflow", "configuration"}


@dataclass(frozen=True)
class Value:
    data: str | bytes
    dependencies: tuple[str, ...] = ()
    terms: int = 1


def variable_name(raw: str) -> str | None:
    if not re.fullmatch(r"\$[A-Za-z_][A-Za-z0-9_]*", raw):
        return None
    name = raw[1:].casefold()
    if name in RESERVED or name.startswith("ps") or name.endswith("preference"):
        return None
    return name


def binding_policy(tokens: list[Token]) -> tuple[set[str], bool]:
    writes: Counter[str] = Counter()
    unsafe = any(t.kind in {"LC", "RC", "OPAQUE"} or
                 (t.kind == "WORD" and t.value.casefold() in CONTROL) or
                 (t.kind == "VAR" and t.value == "$") for t in tokens)
    for index, t in enumerate(tokens):
        if t.kind != "VAR":
            continue
        name = variable_name(t.value)
        rest = tokens[index + 1:index + 3]
        before = tokens[max(0, index - 2):index]
        prefix_mutation = before and (before[-1].value == "--" or
                                      len(before) == 2 and all(x.kind == "PLUS" for x in before))
        assignment = rest and rest[0].kind == "EQ"
        compound = rest and (rest[0].kind == "PLUS" or
                             rest[0].kind == "WORD" and rest[0].value in {"-", "*", "/", "%", "??", "++", "--"}) and (
                                 rest[0].value in {"++", "--"} or
                                 len(rest) > 1 and rest[1].kind in {"PLUS", "EQ"})
        if not name and (assignment or compound or prefix_mutation):
            # Braced/scoped writes can alias simple names; do not retain stale bindings.
            unsafe = True
        if name and prefix_mutation:
            writes[name] += 2
        if name and rest:
            if assignment:
                writes[name] += 1
            elif compound:
                # Even a potential compound assignment invalidates this binding globally.
                writes[name] += 2
            elif rest[0].kind in {"DOT", "LB"}:
                # Mutating a property/index is outside this string-only variable model.
                unsafe = True
    return {name for name, count in writes.items() if count == 1}, unsafe

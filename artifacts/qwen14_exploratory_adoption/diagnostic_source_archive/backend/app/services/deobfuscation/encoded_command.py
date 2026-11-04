"""Recognize a narrow native launcher form, never arbitrary occurrences of a parameter."""

from dataclasses import dataclass
import re

from .lexer import Token


@dataclass(frozen=True)
class EncodedArgument:
    start: int
    end: int
    value: str | None
    reason: str = ""


def recognize(tokens: list[Token], text: str) -> EncodedArgument | None:
    if not tokens:
        return None
    index = 1 if tokens[0].kind == "AMP" else 0
    if index >= len(tokens):
        return None
    token = tokens[index]
    if token.kind == "STRING":
        if index == 0 or token.value is None:
            return None
        command = token.value
        index += 1
    elif token.kind == "WORD":
        command = token.value
        index += 1
        if index + 1 < len(tokens) and tokens[index].kind == "DOT" and tokens[index + 1].kind == "WORD":
            if tokens[index - 1].end != tokens[index].start or tokens[index].end != tokens[index + 1].start:
                return None
            command += "." + tokens[index + 1].value
            index += 2
    else:
        return None
    if not re.fullmatch(r"(?:powershell|pwsh)(?:\.exe)?", command, re.IGNORECASE):
        return None
    while index < len(tokens):
        option = tokens[index]
        gap = text[tokens[index - 1].end:option.start].replace("`\r\n", "").replace("`\n", "")
        if not any(c in " \t\r\n" for c in gap):
            return EncodedArgument(option.start, tokens[-1].end, None,
                                   "Launcher arguments require an explicit whitespace separator.")
        name = (option.value or "").casefold()
        if option.kind == "WORD" and name in {"-noprofile", "-nologo", "-noninteractive"}:
            index += 1
            continue
        if option.kind == "WORD" and name in {"-encodedcommand", "-enc"}:
            args = tokens[index + 1:]
            if not args:
                return EncodedArgument(option.start, option.end, None, "Missing Base64 argument.")
            gap = text[option.end:args[0].start].replace("`\r\n", "").replace("`\n", "")
            if not any(c in " \t\r\n" for c in gap):
                return EncodedArgument(option.start, args[-1].end, None,
                                       "EncodedCommand requires a separate literal argument.")
            if len(args) == 1 and args[0].kind == "STRING":
                return EncodedArgument(args[0].start, args[0].end, args[0].value,
                                       args[0].reason or "")
            if any(t.kind in {"STRING", "VAR", "LP", "RP", "AMP", "PIPE"} for t in args):
                return EncodedArgument(args[0].start, args[-1].end, None, "Encoded argument is dynamic or ambiguous.")
            if any(left.end != right.start for left, right in zip(args, args[1:])):
                return EncodedArgument(args[0].start, args[-1].end, None, "Only one final literal Base64 argument is supported.")
            return EncodedArgument(args[0].start, args[-1].end, text[args[0].start:args[-1].end])
        # -Command / -File consume the remainder: never look for -enc inside their data.
        if name in {"-command", "-c", "-file", "-f"}:
            return None
        if name.startswith("-e"):
            return EncodedArgument(option.start, tokens[-1].end, None,
                                   "Launcher parameter outside the supported -EncodedCommand/-enc subset.")
        return None
    return None

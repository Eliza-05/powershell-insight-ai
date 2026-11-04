"""Bounded invocation recognizer on the existing lexer, not another PowerShell parser."""

from dataclasses import dataclass

from app.schemas.deobfuscation import SourceLayer, Transformation
from app.services.deobfuscation.budget import Budget, LimitReached
from app.services.deobfuscation.engine import _statements
from app.services.deobfuscation.lexer import Token


@dataclass(frozen=True)
class Atom:
    start: int
    end: int
    value: str | None
    transformation_ids: tuple[str, ...] = ()
    kind: str = "string"


@dataclass(frozen=True)
class Invocation:
    name: Atom
    start: int
    end: int
    parameters: dict[str, Atom]
    positional: tuple[Atom, ...]
    arguments: tuple[tuple[Token, ...], ...]
    valid_arguments: bool
    receiver: Atom | None = None


SWITCHES = {"-force", "-usebasicparsing", "-asplaintext", "-ascredentialobject"}


class Extractor:
    def __init__(self, layer: SourceLayer, steps: list[Transformation], budget: Budget):
        self.layer, self.budget = layer, budget
        self.recoveries = {(s.source.start, s.source.end): s for s in steps
                           if s.source.layer_id == layer.layer_id and s.status == "success"
                           and s.deterministic_verified and s.recovery_kind in {"string", "variable_use"}}

    def atom(self, tokens: list[Token] | tuple[Token, ...]) -> Atom:
        self.budget.spend(len(tokens))
        start, end = tokens[0].start, tokens[-1].end
        inner = list(tokens)
        # Peel only parentheses enclosing the entire operand.
        while len(inner) > 2 and inner[0].kind == "LP" and self.close(inner, 0) == len(inner) - 1:
            inner = inner[1:-1]
            self.budget.spend(len(inner))
        recovery = self.recoveries.get((inner[0].start, inner[-1].end))
        if recovery:
            return Atom(start, end, recovery.recovered_text, (recovery.transformation_id,))
        if len(inner) == 1:
            token = inner[0]
            if token.kind == "STRING" and token.value is not None:
                return Atom(start, end, token.value)
            if token.kind == "VAR" and token.value.casefold() in {"$true", "$false"}:
                return Atom(start, end, token.value[1:].casefold(), kind="boolean")
        # Bare words are literal arguments only in argument mode. Parentheses switch
        # to expression mode, where a bare command's result is not a known string.
        if len(inner) == len(tokens) and all(t.kind in {"WORD", "DOT"} for t in inner) and all(
            a.end == b.start for a, b in zip(inner, inner[1:])
        ):
            return Atom(start, end, self.layer.text[inner[0].start:inner[-1].end])
        return Atom(start, end, None)

    def close(self, tokens, start):
        depth = 0
        for i in range(start, len(tokens)):
            self.budget.spend()
            if tokens[i].kind == "LP":
                depth += 1
            elif tokens[i].kind == "RP":
                depth -= 1
                if depth == 0:
                    return i
        return -1

    def separated(self, left, right):
        gap = self.layer.text[left.end:right.start].replace("`\r\n", "").replace("`\n", "")
        return any(c in " \t\r\n" for c in gap)

    def groups(self, tokens):
        groups, current, depth = [], [], 0
        for token in tokens:
            self.budget.spend()
            if current and depth == 0 and self.separated(current[-1], token):
                groups.append(current)
                current = []
            current.append(token)
            if token.kind in {"LP", "LB"}:
                depth += 1
            elif token.kind in {"RP", "RB"}:
                depth -= 1
        if current:
            groups.append(current)
        return groups

    def arguments(self, groups):
        parameters, positional, valid = {}, [], True
        i = 0
        while i < len(groups):
            group = groups[i]
            self.budget.spend(len(group))
            if len(group) == 1 and group[0].kind == "WORD" and group[0].value.startswith("-"):
                name = group[0].value.casefold()
                if name in parameters:
                    valid = False
                if name in SWITCHES:
                    parameters[name] = Atom(group[0].start, group[0].end, "switch", kind="switch")
                elif i + 1 < len(groups) and not (len(groups[i + 1]) == 1 and groups[i + 1][0].kind == "WORD"
                                                 and groups[i + 1][0].value.startswith("-")):
                    i += 1
                    parameters[name] = self.atom(groups[i])
                else:
                    valid = False
            else:
                positional.append(self.atom(group))
            i += 1
        return parameters, tuple(positional), valid

    def webclient(self, tokens):
        if not tokens or tokens[0].kind != "LP":
            return None
        close = self.close(tokens, 0)
        if close < 3 or close + 4 >= len(tokens):
            return None
        inside = tokens[1:close]
        if inside[0].kind != "WORD" or inside[0].value.casefold() != "new-object":
            return None
        if not self.separated(inside[0], inside[1]):
            return None
        if len(inside) > 1 and inside[1].value and inside[1].value.casefold() == "-typename":
            if len(inside) < 3 or not self.separated(inside[1], inside[2]):
                return None
            inside = inside[:1] + inside[2:]
        groups = self.groups(inside[1:])
        if len(groups) != 1:
            return None
        receiver = self.atom(groups[0])
        if receiver.value is None or receiver.value.casefold() not in {"net.webclient", "system.net.webclient"}:
            return None
        tail = tokens[close + 1:]
        if not (tail[0].kind == "DOT" and tail[1].kind == "WORD" and tail[2].kind == "LP"
                and self.close(tail, 2) == len(tail) - 1):
            return None
        # Do not accept whitespace-separated member chains as an equivalent invocation.
        if any(a.end != b.start for a, b in zip([tokens[close]] + tail[:3], tail[:3])):
            return None
        chunks, current, depth = [], [], 0
        for token in tail[3:-1]:
            self.budget.spend()
            if token.kind in {"LP", "LB"}:
                depth += 1
            elif token.kind in {"RP", "RB"}:
                depth -= 1
            if token.kind == "COMMA" and depth == 0:
                chunks.append(current)
                current = []
            else:
                current.append(token)
        chunks.append(current)
        if any(not part for part in chunks):
            return None
        args = tuple(self.atom(part) for part in chunks)
        return Invocation(Atom(tail[1].start, tail[1].end, tail[1].value.casefold()), tokens[0].start,
                          tokens[-1].end, {}, args, (), True, receiver)

    def method(self, tokens):
        while tokens:
            method = self.webclient(tokens)
            if method:
                return method
            if tokens[0].kind == "LP" and self.close(tokens, 0) == len(tokens) - 1:
                tokens = tokens[1:-1]
            else:
                return None
        return None

    def segment(self, tokens, depth=0):
        self.budget.spend(len(tokens))
        if not tokens:
            return
        if depth >= self.budget.limits.max_expression_depth:
            raise LimitReached("max_expression_depth")
        if len(tokens) > 2 and tokens[0].kind == "VAR" and tokens[1].kind == "EQ":
            tokens = tokens[2:]
        method = self.method(tokens)
        if method:
            yield method
            return
        # A pipeline starts a new command context at each top-level pipe.
        level, start = 0, 0
        pieces = []
        for i, token in enumerate(tokens):
            if token.kind in {"LP", "LB"}:
                level += 1
            elif token.kind in {"RP", "RB"}:
                level -= 1
            if token.kind == "PIPE" and level == 0:
                pieces.append(tokens[start:i])
                start = i + 1
        if pieces:
            pieces.append(tokens[start:])
            for piece in pieces:
                yield from self.segment(piece, depth + 1)
            return
        index = 1 if tokens[0].kind == "AMP" else 0
        if index >= len(tokens):
            return
        head = tokens[index]
        if head.kind != "WORD" and not (index == 1 and head.kind in {"STRING", "VAR"}):
            return
        name = self.atom([head])
        remainder = tokens[index + 1:]
        if remainder and head.end == remainder[0].start and remainder[0].kind != "LP":
            return
        groups = self.groups(remainder)
        params, positional, valid = self.arguments(groups)
        yield Invocation(name, head.start, tokens[-1].end, params, positional,
                         tuple(tuple(g) for g in groups), valid)
        for group in groups:
            if group[0].kind == "LP":
                method = self.method(group)
                if method:
                    yield method
                elif self.close(group, 0) == len(group) - 1:
                    yield from self.segment(group[1:-1], depth + 1)

    def invocations(self, tokens):
        for statement in _statements(tokens):
            yield from self.segment(statement)

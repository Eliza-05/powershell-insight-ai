"""Small expression grammar: quoted literals, variables, parentheses and two allowlisted APIs.

Build a tree before recovery. Unknown operations are never dispatched dynamically.
"""

from __future__ import annotations

from dataclasses import dataclass

from .budget import Budget, LimitReached
from .lexer import Token


@dataclass(frozen=True)
class Node:
    kind: str
    start: int
    end: int
    value: str | None = None
    children: tuple[Node, ...] = ()
    reason: str = ""


class UnsupportedExpression(Exception):
    pass


class Parser:
    def __init__(self, tokens: list[Token], budget: Budget, index: int = 0):
        self.tokens, self.budget, self.index = tokens, budget, index

    def kind(self) -> str:
        return self.tokens[self.index].kind if self.index < len(self.tokens) else "END"

    def take(self, kind: str) -> Token:
        self.budget.spend()
        if self.kind() != kind:
            raise UnsupportedExpression("Expression outside the supported grammar.")
        token = self.tokens[self.index]
        self.index += 1
        return token

    def parse(self, depth: int = 0) -> Node:
        if depth >= self.budget.limits.max_expression_depth:
            raise LimitReached("max_expression_depth")
        first = self.atom(depth)
        children = [first]
        while self.kind() == "PLUS":
            self.take("PLUS")
            children.append(self.atom(depth))
            if len(children) > self.budget.limits.max_concat_terms:
                raise LimitReached("max_concat_terms")
        node = first if len(children) == 1 else Node("concat", first.start, children[-1].end, children=tuple(children))
        if self.kind() == "FORMAT":
            self.take("FORMAT")
            nesting = 0
            end = self.tokens[self.index - 1].end
            while self.kind() != "END":
                kind = self.kind()
                if kind == "RP" and nesting == 0:
                    break
                token = self.take(kind)
                if kind == "LP":
                    nesting += 1
                elif kind == "RP":
                    nesting -= 1
                end = token.end
            return Node("format", node.start, end)
        return node

    def atom(self, depth: int) -> Node:
        self.budget.spend()
        if self.kind() == "STRING":
            t = self.take("STRING")
            return Node("literal", t.start, t.end, t.value, reason=t.reason)
        if self.kind() == "VAR":
            t = self.take("VAR")
            return Node("variable", t.start, t.end, t.value, reason=t.reason)
        if self.kind() == "LP":
            left = self.take("LP")
            child = self.parse(depth + 1)
            right = self.take("RP")
            return Node("parentheses", left.start, right.end, children=(child,))
        if self.kind() == "LB":
            return self.static_call(depth)
        raise UnsupportedExpression("Only literal strings and explicitly supported expressions can be recovered.")

    def static_call(self, depth: int) -> Node:
        start = self.take("LB").start
        parts = [self.take("WORD").value]
        while self.kind() == "DOT":
            self.take("DOT")
            parts.append(self.take("WORD").value)
        self.take("RB")
        self.take("DCOLON")
        member = self.take("WORD").value.casefold()
        typename = ".".join(parts).casefold()
        if typename in {"convert", "system.convert"} and member == "frombase64string":
            self.take("LP")
            child = self.parse(depth + 1)
            right = self.take("RP")
            return Node("base64", start, right.end, children=(child,))
        if typename in {"text.encoding", "system.text.encoding"}:
            self.take("DOT")
            if self.take("WORD").value.casefold() != "getstring":
                raise UnsupportedExpression("Only explicit Encoding.GetString is supported.")
            self.take("LP")
            child = self.parse(depth + 1)
            right = self.take("RP")
            return Node("decode", start, right.end, member, (child,))
        raise UnsupportedExpression("Static method outside the allowlist; no call performed.")


def parse_complete(tokens: list[Token], budget: Budget) -> Node:
    parser = Parser(tokens, budget)
    node = parser.parse()
    if parser.index != len(tokens):
        raise UnsupportedExpression("Trailing syntax outside the expression subset.")
    return node

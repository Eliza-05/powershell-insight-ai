"""Bounded lexical subset, not a replacement for the official PowerShell parser.

Comments, strings (including unsupported expandable/here strings) remain opaque.
Offsets count Python Unicode code points, with an exclusive end.
"""

from dataclasses import dataclass

from .budget import Budget, LimitReached


@dataclass(frozen=True)
class Token:
    kind: str
    start: int
    end: int
    value: str | None = None
    reason: str = ""


@dataclass(frozen=True)
class LexIssue:
    start: int
    end: int
    reason: str
    fatal: bool = False


SYMBOLS = {"+": "PLUS", "=": "EQ", "(": "LP", ")": "RP", "[": "LB", "]": "RB",
           "{": "LC", "}": "RC", ".": "DOT", ",": "COMMA", ";": "SEP", "&": "AMP", "|": "PIPE"}
ESCAPES = {"0": "\0", "a": "\a", "b": "\b", "e": "\x1b", "f": "\f", "n": "\n",
           "r": "\r", "t": "\t", "v": "\v", "`": "`", "$": "$", '"': '"', "'": "'"}
SMART_QUOTES = "\u2018\u2019\u201c\u201d"


def lex(text: str, budget: Budget) -> tuple[list[Token], list[LexIssue]]:
    budget.spend(len(text))
    tokens: list[Token] = []
    issues: list[LexIssue] = []
    i, n = 0, len(text)

    def emit(kind, start, end, value=None, reason=""):
        if len(tokens) >= budget.limits.max_tokens:
            raise LimitReached("max_tokens")
        tokens.append(Token(kind, start, end, value, reason))

    while i < n:
        budget.spend()
        start, char = i, text[i]
        if char in " \t\r\ufeff":
            i += 1
        elif char == "\n":
            emit("NL", i, i + 1)
            i += 1
        elif text.startswith("`\r\n", i) or text.startswith("`\n", i):
            i += 3 if text.startswith("`\r\n", i) else 2
        elif text.startswith("<#", i):
            depth = 1
            i += 2
            while i < n and depth:
                if text.startswith("<#", i):
                    depth += 1
                    i += 2
                elif text.startswith("#>", i):
                    depth -= 1
                    i += 2
                else:
                    i += 1
            emit("COMMENT", start, i)
            if depth:
                issues.append(LexIssue(start, i, "Unterminated block comment.", True))
        elif char == "#" and (start == 0 or text[start - 1].isspace() or text[start - 1] in ";{}()[]|&"):
            i = text.find("\n", i)
            if i < 0:
                i = n
            emit("COMMENT", start, i)
        elif text.startswith(("@'", '@"'), i):
            quote = text[i + 1]
            i += 2
            # Here strings must close at the beginning of a line; never tokenize their body.
            close = text.find("\n" + quote + "@", i)
            i = n if close < 0 else close + 3
            reason = "Here strings are opaque and outside the supported literal subset."
            emit("STRING", start, i, reason=reason)
            issues.append(LexIssue(start, i, reason, close < 0))
        elif char in "'\"":
            quote, out, reason, closed = char, [], "", False
            i += 1
            while i < n:
                c = text[i]
                if c == quote:
                    if i + 1 < n and text[i + 1] == quote:
                        out.append(quote)
                        i += 2
                    else:
                        i += 1
                        closed = True
                        break
                elif quote == '"' and c == "`":
                    if i + 1 >= n:
                        i += 1
                        break
                    escape = text[i + 1]
                    if escape == "\r" and i + 2 < n and text[i + 2] == "\n":
                        i += 3
                    elif escape == "\n":
                        i += 2
                    else:
                        if escape not in ESCAPES:
                            reason = "Escape outside the supported double-quoted literal subset."
                        out.append(ESCAPES.get(escape, escape))
                        i += 2
                elif quote == '"' and c == "$":
                    reason = "Expandable strings and subexpressions are not resolved."
                    # Quotes inside $(...) can change tokenization: quarantine the entire layer.
                    if text.startswith("$(", i):
                        issues.append(LexIssue(start, n, "Expandable subexpression requires the full parser.", True))
                        i = n
                        break
                    out.append(c)
                    i += 1
                elif c in SMART_QUOTES:
                    issues.append(LexIssue(start, n, "Smart quotes require the full parser.", True))
                    i = n
                    break
                else:
                    out.append(c)
                    i += 1
            if not closed:
                reason = "Unterminated or unsupported string syntax."
                issues.append(LexIssue(start, i, reason, True))
            emit("STRING", start, i, "".join(out) if not reason else None, reason)
        elif char == "$":
            i += 1
            if i < n and text[i] == "{":
                close = text.find("}", i + 1)
                i = n if close < 0 else close + 1
                emit("VAR", start, i, text[start:i], "Braced variables are unsupported.")
                if close < 0:
                    issues.append(LexIssue(start, i, "Unterminated variable.", True))
            else:
                while i < n and (text[i].isalnum() or text[i] in "_:?"):
                    i += 1
                emit("VAR", start, i, text[start:i])
        elif text.startswith("::", i):
            emit("DCOLON", i, i + 2)
            i += 2
        elif char in SYMBOLS:
            emit(SYMBOLS[char], i, i + 1, char)
            i += 1
        elif char in SMART_QUOTES or char == "`":
            issues.append(LexIssue(i, n, "Escaped identifiers or smart quotes are outside the lexical subset.", True))
            emit("OPAQUE", i, n)
            i = n
        else:
            while i < n and text[i] not in " \t\r\n'\"$`" + "".join(SYMBOLS) + SMART_QUOTES:
                if text.startswith("::", i):
                    break
                i += 1
            if i == start:
                i += 1
            word = text[start:i]
            if word == "--%":
                issues.append(LexIssue(start, n, "Stop-parsing token: remainder is opaque; layer not recovered.", True))
                emit("OPAQUE", start, n)
                i = n
            else:
                emit("FORMAT" if word.casefold() == "-f" else "WORD", start, i, word)
    return tokens, issues


def validate_delimiters(tokens: list[Token], limit: int) -> list[LexIssue]:
    stack = []
    matching = {"RP": "LP", "RB": "LB", "RC": "LC"}
    for token in tokens:
        if token.kind in {"LP", "LB", "LC"}:
            stack.append(token)
            if len(stack) > limit:
                raise LimitReached("max_expression_depth")
        elif token.kind in matching:
            if not stack or stack.pop().kind != matching[token.kind]:
                return [LexIssue(token.start, token.end, "Mismatched delimiters.", True)]
    return [LexIssue(t.start, t.end, "Unclosed delimiter.", True) for t in stack]

"""Bounded static support for LLM citations, never execution or human validation.

Reuse the existing lexer, invocation extractor and closed rule catalogue. Analyze the
whole original for lexical context, but accept only complete operations inside a
published citation. Never parse a citation as a new script, expand it to neighbors,
decode Base64, infer reachability of blocks, or promote recovered text to execution.
Only claimed IDs survive; unsupported/ambiguous claims are dropped, never relabelled.
Dropping means 'not verified by this subset', not 'behavior absent'.
"""
from __future__ import annotations

from bisect import bisect_right
from dataclasses import dataclass

from app.schemas.deobfuscation import DeobfuscationLimits, SourceLayer
from app.schemas.pipeline import ModelReport
from app.services.behavior_detection.extraction import Extractor
from app.services.behavior_detection.rules import RULES, argument, evaluate, remote
from app.services.deobfuscation.budget import Budget, LimitReached
from app.services.deobfuscation.engine import _statements
from app.services.deobfuscation.lexer import lex, validate_delimiters
from app.services.deobfuscation.variables import CONTROL

VERSION = "evidence-check-v2-bounded"
LIMITATION = (
    "Verificador acotado: soporte estatico de patrones explicitos, no ejecucion, "
    "alcanzabilidad general ni validacion humana. Una etiqueta descartada significa "
    "que no pudo verificarse; no demuestra ausencia del comportamiento. No se "
    "reetiquetan predicciones ni se promueve recuperacion textual a ejecucion."
)
RESOLUTION_CHANGES = {"set-alias", "new-alias", "remove-alias", "import-module",
                      "remove-module", "set-item", "new-item", "remove-item",
                      "invoke-expression", "iex"}


@dataclass(frozen=True)
class SourceSupport:
    operations: tuple[dict, ...]
    diagnostics: tuple[str, ...]


class IncoherentEvidence(ValueError):
    """A rejected final report still carries every deterministic decision."""
    def __init__(self, message, decisions, final_ids):
        super().__init__(message)
        self.decisions, self.final_ids = decisions, final_ids


def inspect_source(text: str) -> SourceSupport:
    """No recovery/detection engine is run and no detector labels enter the prompt."""
    budget = Budget(DeobfuscationLimits(max_input_bytes=max(1, len(text.encode("utf-8")))))
    operations, diagnostics = [], []
    try:
        tokens, issues = lex(text, budget)
        issues += validate_delimiters(tokens, budget.limits.max_expression_depth)
        diagnostics.extend(i.reason for i in issues)
        if any(i.fatal for i in issues):
            return SourceSupport((), tuple(diagnostics))
        control = CONTROL | {"return", "throw", "exit", "break", "continue"}
        if any(t.kind in {"LC", "RC", "OPAQUE"} or
               t.kind == "WORD" and (t.value or "").casefold() in control for t in tokens):
            return SourceSupport((), ("Blocks, scopes or control flow outside subset; invocation not established.",))
        # Dot-sourcing is not emitted by Extractor, and can change later bindings.
        # Reject that source rather than accidentally certifying its later commands.
        for index, token in enumerate(tokens):
            if token.kind == "AMP" or (token.kind == "DOT" and
                    (index == 0 or tokens[index - 1].kind in {"NL", "SEP", "PIPE", "EQ"})):
                return SourceSupport((), ("Indirect invocation/dot-sourcing outside verifier subset.",))
        layer = SourceLayer(layer_id="L0", source_name="original", provenance="original", text=text, depth=0)
        extractor = Extractor(layer, [], budget)
        significant = [t for t in tokens if t.kind not in {"COMMENT", "NL"}]
        ends = [t.end for t in significant]
        for call in extractor.invocations(tokens):
            name = (call.name.value or "").casefold()
            previous = bisect_right(ends, call.start) - 1
            if previous >= 0 and significant[previous].kind in {"AMP", "DOT"}:
                diagnostics.append("Indirect invocation/dot-sourcing not verified; remaining source omitted.")
                break
            decisions = evaluate(call, extractor)
            for decision in decisions:
                spec = RULES[decision.rule_id]
                if decision.rule_id == "BD-B02-IEX" and decision.supported:
                    content = argument(call, "-command", 0)
                    if content is not None and content.value is not None:
                        # A nonempty string can still be only comments or inert data.
                        # Require a directly recognizable command-shaped input; do
                        # not decode or publish any additional inner behavior IDs.
                        inner, inner_issues = lex(content.value, budget)
                        inner_issues += validate_delimiters(inner, budget.limits.max_expression_depth)
                        statements = list(_statements(inner))
                        has_command = len(statements) == 1 and all(statement and statement[0].kind == "WORD"
                                          and (statement[0].value or "").casefold() in {
                                              "get-process", "get-service", "get-computerinfo",
                                              "get-netipconfiguration", "write-output", "write-host"}
                                          for statement in statements)
                        unsafe_inner = any(t.kind in {"LC", "RC", "AMP"} or
                                           t.kind == "WORD" and (t.value or "").casefold() in control for t in inner)
                        if inner_issues or unsafe_inner or not has_command:
                            diagnostics.append("IEX literal input has no supported functional code; not verified.")
                            continue
                if decision.supported:
                    operations.append({"behavior_id": spec.behavior_id, "rule_id": spec.rule_id,
                        "start": call.start, "end": call.end,
                        "snippet": text[call.start:call.end], "conditions": list(decision.conditions),
                        "limitations": [spec.limitation],
                        "operands": [{"role": role, "start": atom.start, "end": atom.end,
                                      "snippet": text[atom.start:atom.end]} for role, atom in decision.atoms]})
                else:
                    diagnostics.append(decision.reason)
            # An explicit HTTP request is B06 without certifying what its body contains.
            # This is narrower than 1B's body-binding claim; never infer inventory/exfiltration.
            method = call.parameters.get("-method")
            if (name in {"invoke-restmethod", "invoke-webrequest"} and call.valid_arguments
                    and len(call.positional) <= 1 and remote(argument(call, "-uri", 0))
                    and method and method.value and method.value.casefold() in {"post", "put", "patch"}
                    and set(call.parameters) <= {"-uri", "-method", "-body", "-outfile",
                                                  "-usebasicparsing", "-headers", "-credential"}
                    and not any(d.supported and RULES[d.rule_id].behavior_id == "B06" for d in decisions)):
                operations.append({"behavior_id": "B06", "rule_id": "EC-B06-HTTP-REQUEST",
                    "start": call.start, "end": call.end, "snippet": text[call.start:call.end],
                    "conditions": ["Explicit bound HTTP(S) destination and sending method."],
                    "limitations": ["Body contents, inventory transmission, exfiltration and success are not certified."],
                    "operands": [{"role": "argument", "start": a.start, "end": a.end,
                                  "snippet": text[a.start:a.end]} for a in (argument(call, "-uri", 0), method)]})
            if not decisions:
                diagnostics.append("Operation outside bounded catalogue or required bindings not established: " + name)
            if name in RESOLUTION_CHANGES:
                diagnostics.append("Possible name/scope mutation; remaining source not verified.")
                break
    except LimitReached as exc:
        return SourceSupport((), ("Verifier resource limit: " + exc.limit,))
    return SourceSupport(tuple(operations), tuple(dict.fromkeys(diagnostics)))


def matches(raw):
    """Compatibility helper: supported IDs in a complete original, without recovery."""
    return {o["behavior_id"] for o in inspect_source(raw).operations}


def verify(report: ModelReport, evidence, sources: dict[str, str]):
    """Return (filtered_report, all_decisions); never fabricate or widen evidence."""
    original = sources.get("original")
    support = inspect_source(original) if original is not None else SourceSupport((), ("Original missing.",))
    decisions, retained = [], []
    for finding in report.behaviors:
        bid = finding.behavior_id.value
        citations = []
        for e in evidence:
            if getattr(e.behavior_id, "value", e.behavior_id) != bid:
                continue
            src = sources.get(e.source_id)
            valid = src is not None and 0 <= e.start < e.end <= len(src) and src[e.start:e.end] == e.snippet
            contained = [o for o in support.operations if o["behavior_id"] == bid
                         and e.start <= o["start"] and o["end"] <= e.end] if valid and e.source_id == "original" else []
            reason = ("Complete operation and operands inside citation." if contained else
                      "Span does not match source." if not valid else
                      "Textual recovery without a demonstrated invocation link; functional operation not verified."
                      if e.source_id != "original" else
                      "Citation lacks a complete supported operation for this ID; its scope is not expanded.")
            citations.append({"source_id": e.source_id, "start": e.start, "end": e.end,
                "snippet": e.snippet, "line": e.line, "column": e.column,
                "provenance": e.provenance, "root_source": e.root_source.model_dump() if e.root_source else None,
                "support": "bounded_static_pattern" if contained else "unverified", "reason": reason,
                "operations": contained})
        keep = bool(citations) and len(citations) == len(finding.evidence) and all(c["operations"] for c in citations)
        if keep:
            retained.append(finding)
        decisions.append({"from": bid, "to": bid if keep else None,
            "action": "kept" if keep else "dropped", "support": "bounded_static_pattern" if keep else "unverified",
            "reason": "All citations contain bounded static support." if keep else
                      "Not all citations verified; conservative exclusion, not proof of absence.",
            "citations": citations, "source_diagnostics": list(support.diagnostics), "human_validated": False})
    data = report.model_dump(mode="json")
    data["behaviors"] = [f.model_dump(mode="json") for f in retained]
    try:
        checked = ModelReport.model_validate(data)
    except ValueError as exc:
        raise IncoherentEvidence(str(exc), decisions, [f.behavior_id.value for f in retained]) from exc
    return checked, decisions

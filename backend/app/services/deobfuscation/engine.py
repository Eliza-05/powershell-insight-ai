"""Deterministic recovery orchestration over immutable input and decoded script layers."""

from __future__ import annotations

import base64
import hashlib
from bisect import bisect_right

from app.schemas.deobfuscation import (
    DeobfuscationLimits, DeobfuscationResult, InputProvenance, SourceLayer, SourceSpan,
    Transformation, UnresolvedFragment,
)
from app.schemas.llm_analysis import ObfuscationTechnique as OT

from .budget import Budget, LimitReached
from .encoded_command import recognize
from .expressions import Node, Parser, UnsupportedExpression, parse_complete
from .lexer import Token, lex, validate_delimiters
from .transforms import RecoveryError, concatenate, decode_base64, decode_text
from .variables import Value, binding_policy, variable_name


def _statements(tokens: list[Token]):
    """Split at top-level separators; a newline after + or = continues the expression."""
    current, depth = [], 0
    for t in tokens:
        if t.kind == "COMMENT":
            continue
        if t.kind in {"LP", "LB"}:
            depth += 1
        elif t.kind in {"RP", "RB"}:
            depth -= 1
        if t.kind == "NL":
            if depth or (current and current[-1].kind in {"PLUS", "EQ", "COMMA"}):
                continue
        if t.kind in {"SEP", "NL"} and depth == 0:
            if current:
                yield current
            current = []
        else:
            current.append(t)
    if current:
        yield current


class _Recovery:
    def __init__(self, script: str, source_name: str, provenance: InputProvenance, limits: DeobfuscationLimits):
        self.budget = Budget(limits)
        self.source_name, self.provenance = source_name, provenance
        self.layers = [SourceLayer(layer_id="L0", source_name=source_name, provenance=provenance, text=script, depth=0)]
        self.layer = self.layers[0]
        self.steps: list[Transformation] = []
        self.unresolved: list[UnresolvedFragment] = []
        self.techniques: set[OT] = set()
        self.limits_hit: list[str] = []
        self.warnings: list[str] = []
        self.cache: dict[tuple, Transformation] = {}
        self.unresolved_keys: set[tuple] = set()
        self.lines = [0]

    def span(self, start: int, end: int) -> SourceSpan:
        line = bisect_right(self.lines, start)
        end_line = bisect_right(self.lines, end)
        return SourceSpan(layer_id=self.layer.layer_id, start=start, end=end, line=line,
                          column=start - self.lines[line - 1] + 1, end_line=end_line,
                          end_column=end - self.lines[end_line - 1] + 1)

    def unresolved_at(self, start, end, reason, technique=None, transformation_id=None):
        key = (self.layer.layer_id, start, end, reason)
        if key in self.unresolved_keys:
            return
        if len(self.unresolved) >= self.budget.limits.max_unresolved:
            raise LimitReached("max_unresolved")
        self.unresolved_keys.add(key)
        self.unresolved.append(UnresolvedFragment(source=self.span(start, end), technique_hint=technique,
                                                 reason=reason, transformation_id=transformation_id))

    def record(self, technique, start, end, kind, value=None, dependencies=(), status="success",
               warnings=(), output_layer_id=None, added_operation=None) -> Transformation:
        self.techniques.add(technique)
        key = (self.layer.layer_id, start, end, technique, kind)
        if key in self.cache:
            return self.cache[key]
        if len(self.steps) >= self.budget.limits.max_transformations:
            raise LimitReached("max_transformations")
        deps = list(dict.fromkeys(([self.layer.parent_transformation_id] if self.layer.parent_transformation_id else [])
                                 + list(dependencies)))
        text = value if isinstance(value, str) else None
        binary = base64.b64encode(value).decode("ascii") if isinstance(value, bytes) else None
        source = self.span(start, end)
        fragment = self.layer.text[start:end]
        size = len(fragment.encode("utf-8")) + len((text or binary or "").encode("utf-8"))
        self.budget.spend(size)
        self.budget.reserve(size)
        step = Transformation(transformation_id=f"T{len(self.steps) + 1:04d}", technique=technique,
                              source=source, root_source=self.layer.root_source or source,
                              original_fragment=fragment, recovery_kind=kind, recovered_text=text,
                              recovered_bytes_base64=binary, dependencies=deps, status=status,
                              deterministic_verified=value is not None, warnings=list(warnings),
                              output_layer_id=output_layer_id, added_operation=added_operation)
        self.steps.append(step)
        self.cache[key] = step
        return step

    def failed(self, node: Node, technique: OT, reason: str, *, unsupported=False):
        step = self.record(technique, node.start, node.end, "unresolved",
                           status="unsupported" if unsupported else "failed", warnings=[reason])
        self.unresolved_at(node.start, node.end, reason, technique, step.transformation_id)

    def recover(self, node: Node, bindings: dict[str, Value], *, bytes_expected=False) -> Value | None:
        self.budget.spend()
        if node.kind == "literal":
            if node.value is None:
                self.unresolved_at(node.start, node.end, node.reason)
                return None
            self.budget.check_value(len(node.value.encode("utf-8")))
            return Value(node.value)
        if node.kind == "parentheses":
            return self.recover(node.children[0], bindings, bytes_expected=bytes_expected)
        if node.kind == "format":
            self.failed(node, OT.FORMAT, "PowerShell -f is detected but not resolved in Phase 1A.", unsupported=True)
            return None
        if node.kind == "variable":
            name = variable_name(node.value)
            value = bindings.get(name)
            if value is None or node.reason:
                self.failed(node, OT.VARSUB, node.reason or "No unambiguous prior literal binding in the supported scope.")
                return None
            step = self.record(OT.VARSUB, node.start, node.end, "variable_use", value.data, value.dependencies)
            return Value(value.data, (step.transformation_id,), value.terms)
        technique = OT.CONCAT if node.kind == "concat" else OT.B64_INLINE
        self.techniques.add(technique)
        children = [self.recover(child, bindings, bytes_expected=node.kind == "decode") for child in node.children]
        if any(child is None for child in children):
            self.failed(node, technique, "One or more operands cannot be recovered statically.")
            return None
        deps = tuple(dict.fromkeys(dep for child in children for dep in child.dependencies))
        try:
            if node.kind == "concat":
                if not all(isinstance(child.data, str) for child in children):
                    raise RecoveryError("Only string-to-string concatenation is supported; no implicit conversions.")
                terms = sum(child.terms for child in children)
                value = concatenate([child.data for child in children], terms, self.budget)
                step = self.record(technique, node.start, node.end, "string", value, deps)
                return Value(value, (step.transformation_id,), terms)
            if node.kind == "base64":
                if not isinstance(children[0].data, str):
                    raise RecoveryError("FromBase64String requires a statically recovered string.")
                value = decode_base64(children[0].data, self.budget)
                warnings = [] if bytes_expected else ["Bytes recovered; text encoding and interpretation are unspecified."]
                step = self.record(technique, node.start, node.end, "bytes", value, deps,
                                   status="partial", warnings=warnings)
                if warnings:
                    self.unresolved_at(node.start, node.end, warnings[0], technique, step.transformation_id)
                return Value(value, (step.transformation_id,))
            if not isinstance(children[0].data, bytes):
                raise RecoveryError("Encoding.GetString requires recovered bytes; no implicit conversions.")
            value = decode_text(children[0].data, node.value, self.budget)
            step = self.record(technique, node.start, node.end, "string", value, deps)
            return Value(value, (step.transformation_id,))
        except RecoveryError as error:
            self.failed(node, technique, str(error))
            return None

    def encoded(self, argument):
        self.techniques.add(OT.B64_ENCCMD)
        node = Node("encoded", argument.start, argument.end)
        if argument.value is None:
            self.failed(node, OT.B64_ENCCMD, argument.reason, unsupported=True)
            return
        if self.layer.depth >= self.budget.limits.max_depth:
            raise LimitReached("max_depth")
        try:
            raw = decode_base64(argument.value, self.budget)
            if not raw:
                raise RecoveryError("EncodedCommand must contain nonempty text.")
            value = decode_text(raw, "Unicode", self.budget)
        except RecoveryError as error:
            self.failed(node, OT.B64_ENCCMD, str(error))
            return
        # Account for the separately serialized layer as well as the transformation's text.
        self.budget.reserve(len(value.encode("utf-8")))
        layer_id = f"L{len(self.layers)}"
        step = self.record(OT.B64_ENCCMD, node.start, node.end, "script_text", value,
                           output_layer_id=layer_id, added_operation="LAUNCHER_ENCCMD",
                           warnings=["Decoded text only; syntactic validity, reachability and semantic equivalence are not proved."])
        self.layers.append(SourceLayer(layer_id=layer_id, source_name=self.source_name,
                                       provenance="deobfuscator_recovered", text=value, depth=self.layer.depth + 1,
                                       parent_transformation_id=step.transformation_id, root_source=step.root_source))

    def expression(self, tokens, bindings) -> tuple[Value | None, bool]:
        if not tokens:
            return None, False
        try:
            node = parse_complete(tokens, self.budget)
        except UnsupportedExpression as error:
            self.unresolved_at(tokens[0].start, tokens[-1].end, str(error))
            return None, False
        value = self.recover(node, bindings)
        return value, value is not None

    def command_fragments(self, tokens, bindings):
        """Only explicit parenthesized expressions and standalone variable arguments.

        In argument mode 'a' + 'b' denotes separate arguments, not concatenation.
        """
        index = 0
        while index < len(tokens):
            self.budget.spend()
            t = tokens[index]
            if t.kind == "LP":
                parser = Parser(tokens, self.budget, index)
                try:
                    node = parser.atom(0)
                except UnsupportedExpression as error:
                    self.unresolved_at(t.start, tokens[min(parser.index, len(tokens) - 1)].end, str(error))
                    index += 1
                    continue
                self.recover(node, bindings)
                index = parser.index
                continue
            if t.kind == "VAR":
                before = tokens[index - 1] if index else None
                after = tokens[index + 1] if index + 1 < len(tokens) else None
                separated = (before is None or before.end < t.start or before.kind == "AMP") and (
                    after is None or t.end < after.start)
                if separated:
                    self.recover(Node("variable", t.start, t.end, t.value, reason=t.reason), bindings)
                else:
                    self.unresolved_at(t.start, t.end, "Variable in a compound argument is not substituted.", OT.VARSUB)
            index += 1

    def analyze_layer(self):
        self.lines = [0] + [i + 1 for i, char in enumerate(self.layer.text) if char == "\n"]
        tokens, issues = lex(self.layer.text, self.budget)
        issues += validate_delimiters(tokens, self.budget.limits.max_expression_depth)
        for issue in issues:
            self.unresolved_at(issue.start, issue.end, issue.reason)
        if any(issue.fatal for issue in issues):
            return
        code = [t for t in tokens if t.kind not in {"COMMENT", "NL"}]
        eligible, unsafe = binding_policy(code)
        bindings: dict[str, Value] = {}
        binding_enabled = not unsafe
        for statement in _statements(tokens):
            self.budget.spend(len(statement))
            argument = recognize(statement, self.layer.text)
            if argument is not None:
                self.encoded(argument)
                bindings.clear()
                binding_enabled = False
                continue
            if len(statement) >= 2 and statement[0].kind == "VAR" and statement[1].kind == "EQ":
                name = variable_name(statement[0].value)
                value, pure = self.expression(statement[2:], bindings)
                if name in eligible and binding_enabled and value is not None and isinstance(value.data, str):
                    step = self.record(OT.VARSUB, statement[0].start, statement[-1].end,
                                       "variable_definition", value.data, value.dependencies)
                    bindings[name] = Value(value.data, (step.transformation_id,), value.terms)
                else:
                    self.unresolved_at(statement[0].start, statement[-1].end,
                                       "Assignment is not a unique literal binding in the supported linear scope.", OT.VARSUB)
                if not pure:
                    # P3's Join-Path and any other command result are never guessed.
                    if len(statement) > 2 and statement[2].kind == "WORD":
                        self.command_fragments(statement[2:], {})
                    bindings.clear()
                    binding_enabled = False
                continue
            if statement[0].kind in {"STRING", "LP", "LB", "VAR"}:
                _, pure = self.expression(statement, bindings)
                if not pure:
                    bindings.clear()
                    binding_enabled = False
            else:
                # A dynamic argument may mutate bindings before other arguments are evaluated.
                safe_args = not any(t.kind in {"LP", "LC", "PIPE", "EQ"} for t in statement)
                self.command_fragments(statement, bindings if safe_args else {})
                bindings.clear()
                binding_enabled = False

    def run(self) -> DeobfuscationResult:
        index = 0
        while index < len(self.layers):
            self.layer = self.layers[index]
            try:
                self.analyze_layer()
            except LimitReached as error:
                if error.limit not in self.limits_hit:
                    self.limits_hit.append(error.limit)
                self.warnings.append(f"Processing stopped at {self.layer.layer_id}: {error.limit}.")
                break
            index += 1
        return DeobfuscationResult(input_sha256=hashlib.sha256(self.layers[0].text.encode("utf-8")).hexdigest(),
                                   source_name=self.source_name, input_provenance=self.provenance,
                                   status="partial" if self.unresolved or self.limits_hit else "complete",
                                   limits=self.budget.limits, layers=self.layers, transformations=self.steps,
                                   unresolved=self.unresolved, techniques_detected=sorted(self.techniques, key=lambda x: x.value),
                                   limits_hit=self.limits_hit, warnings=self.warnings, work_units=self.budget.work,
                                   artifact_bytes=self.budget.artifact_bytes)


def deobfuscate(script: str, *, limits: DeobfuscationLimits | None = None,
                source_name: str = "input", input_provenance: InputProvenance = "obfuscated_variant") -> DeobfuscationResult:
    """Recover bounded textual artifacts. Never reads files, contacts services or launches processes.

    Invalid API types/configuration raise TypeError/ValidationError. Untrusted syntax and
    resource limits return structured partial/rejected results. Input is never rewritten.
    """
    if not isinstance(script, str):
        raise TypeError("script must be a Unicode string")
    if limits is not None and not isinstance(limits, DeobfuscationLimits):
        raise TypeError("limits must be DeobfuscationLimits")
    limits = limits or DeobfuscationLimits()
    rejected = dict(input_sha256=None, source_name=source_name, input_provenance=input_provenance,
                    status="rejected", limits=limits, work_units=0, artifact_bytes=0)
    if len(script) > limits.max_input_bytes:
        return DeobfuscationResult(**rejected, limits_hit=["max_input_bytes"], warnings=["Input exceeds the byte ceiling; input not copied into output."])
    try:
        size = len(script.encode("utf-8"))
    except UnicodeError:
        return DeobfuscationResult(**rejected, warnings=["Input has unpaired Unicode surrogates."])
    if size > limits.max_input_bytes:
        return DeobfuscationResult(**rejected, limits_hit=["max_input_bytes"], warnings=["UTF-8 input exceeds the byte ceiling; input not copied into output."])
    # Validate metadata even when no transformations are found.
    DeobfuscationResult(**rejected)
    return _Recovery(script, source_name, input_provenance, limits).run()

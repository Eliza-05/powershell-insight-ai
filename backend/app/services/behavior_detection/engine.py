"""Integrate Phase 1A, rules, strict evidence and operation-based deduplication."""

from bisect import bisect_right
from typing import Literal

from app.schemas.behavior_detection import (
    AddedOperation, BehaviorAnalysisResult, BehaviorFinding, BehaviorIndicator, DetectionEvidence, DetectionLimits,
)
from app.schemas.deobfuscation import DeobfuscationLimits, SourceSpan
from app.schemas.llm_analysis import BehaviorId
from app.services.deobfuscation import deobfuscate
from app.services.deobfuscation.budget import Budget, LimitReached
from app.services.deobfuscation.lexer import lex, validate_delimiters
from app.services.deobfuscation.variables import CONTROL

from .extraction import Atom, Extractor
from .rules import RULES, evaluate


class Detection:
    def __init__(self, deob, limits, added_operations):
        self.deob, self.limits, self.added = deob, limits, added_operations
        self.budget = Budget(deob.limits)
        self.layer = deob.layers[0]
        self.lines = [0]
        self.findings, self.evidence, self.indicators = [], [], []
        self.evidence_cache, self.finding_keys, self.indicator_keys = {}, set(), set()
        self.operations, self.seen_operations, self.limits_hit = 0, set(), []
        self.wrapper_keys = set()
        self.matched_wrappers = set()
        self.launchers = [t.source for t in deob.transformations if t.added_operation == "LAUNCHER_ENCCMD"]
        self.warnings = ["Reconocedor estático parcial: no prueba ejecución, alcanzabilidad, intención ni ausencia de otros comportamientos.",
                         "Resolución de nombres y procedencia funcional de IEX no se prueban; declare los wrappers añadidos conocidos."]
        layers = {layer.layer_id: layer for layer in deob.layers}
        for item in self.added:
            layer = layers.get(item.source.layer_id)
            if layer is None or item.source.end > len(layer.text):
                raise ValueError("Added operation outside an analyzed layer.")
            self.layer = layer
            self.lines = [0] + [i + 1 for i, char in enumerate(layer.text) if char == "\n"]
            if self.span(item.source.start, item.source.end) != item.source:
                raise ValueError("Added-operation coordinates are inconsistent.")
            self.wrapper_keys.add((item.source.layer_id, item.source.start, item.source.end))
        if len(self.wrapper_keys) != len(self.added):
            raise ValueError("Duplicate added-operation metadata.")

    def span(self, start, end):
        line, end_line = bisect_right(self.lines, start), bisect_right(self.lines, end)
        return SourceSpan(layer_id=self.layer.layer_id, start=start, end=end, line=line,
                          column=start - self.lines[line - 1] + 1, end_line=end_line,
                          end_column=end - self.lines[end_line - 1] + 1)

    def indicator(self, start, end, reason, spec=None):
        key = (self.layer.layer_id, start, end, reason, spec.rule_id if spec else None)
        if key in self.indicator_keys:
            return
        if len(self.indicators) >= self.limits.max_indicators:
            raise LimitReached("max_indicators")
        self.budget.spend(len(reason))
        self.indicators.append(BehaviorIndicator(indicator_id=f"I{len(self.indicators) + 1:04d}",
                                                behavior_id=spec.behavior_id if spec else None,
                                                rule_id=spec.rule_id if spec else None,
                                                source=self.span(start, end), reason=reason))
        self.indicator_keys.add(key)

    def finding(self, call, decision):
        spec = RULES[decision.rule_id]
        operation = self.span(call.start, call.end)
        key = (spec.behavior_id, operation.layer_id, operation.start, operation.end)
        if key in self.finding_keys:
            return
        if len(self.findings) >= self.limits.max_findings:
            raise LimitReached("max_findings")
        atoms = [("operation", Atom(call.start, call.end, None))] + list(decision.atoms)
        # Keep a recovered command's value and definition chain as explicit contextual evidence.
        if call.name.transformation_ids:
            atoms.append(("argument", call.name))
        pending, keys, size = {}, [], 0
        for role, atom in atoms:
            recovered = atom.value if atom.transformation_ids else None
            ekey = (self.layer.layer_id, role, atom.start, atom.end, recovered, atom.transformation_ids)
            if ekey not in keys:
                keys.append(ekey)
            if ekey in self.evidence_cache or ekey in pending:
                continue
            source = self.span(atom.start, atom.end)
            fragment = self.layer.text[atom.start:atom.end]
            ids = list(dict.fromkeys(([self.layer.parent_transformation_id] if self.layer.parent_transformation_id else [])
                                     + list(atom.transformation_ids)))
            self.budget.check_value(len(fragment.encode("utf-8")))
            size += len(fragment.encode("utf-8")) + len((recovered or "").encode("utf-8"))
            pending[ekey] = dict(role=role, source=source, root_source=self.layer.root_source or source,
                                fragment=fragment, recovered_value=recovered, transformation_ids=ids,
                                provenance="deobfuscator_recovered" if self.layer.depth or recovered is not None
                                else self.layer.provenance)
        if len(self.evidence) + len(pending) > self.limits.max_evidence:
            raise LimitReached("max_evidence")
        self.budget.spend(size)
        self.budget.reserve(size)
        # Commit evidence and finding together only after all budgets have accepted them.
        for ekey, payload in pending.items():
            item = DetectionEvidence(evidence_id=f"E{len(self.evidence) + 1:04d}", **payload)
            self.evidence_cache[ekey] = item
            self.evidence.append(item)
        ids = [self.evidence_cache[k].evidence_id for k in keys]
        self.findings.append(BehaviorFinding(finding_id=f"F{len(self.findings) + 1:04d}", behavior_id=spec.behavior_id,
                                            rule_id=spec.rule_id, description=spec.description,
                                            operation_source=operation, evidence_ids=ids,
                                            support="individual" if len(ids) == 1 else "contextual",
                                            conditions=list(decision.conditions), limitations=[spec.limitation]))
        self.finding_keys.add(key)

    def analyze_layer(self):
        self.lines = [0] + [i + 1 for i, c in enumerate(self.layer.text) if c == "\n"]
        tokens, issues = lex(self.layer.text, self.budget)
        issues += validate_delimiters(tokens, self.deob.limits.max_expression_depth)
        for issue in issues:
            self.indicator(issue.start, issue.end, issue.reason)
        if any(issue.fatal for issue in issues):
            return
        # Do not infer reachability or bindings inside control flow or user-defined scopes.
        control = CONTROL | {"return", "throw", "exit", "break", "continue"}
        if any(t.kind in {"LC", "RC"} or t.kind == "WORD" and (t.value or "").casefold() in control for t in tokens):
            self.indicator(0, len(self.layer.text), "Bloques o flujo de control requieren un análisis no implementado; capa omitida.")
            return
        extractor = Extractor(self.layer, self.deob.transformations, self.budget)
        for call in extractor.invocations(tokens):
            key = (self.layer.layer_id, call.start, call.end)
            if key in self.seen_operations:
                continue
            if self.operations >= self.limits.max_operations:
                raise LimitReached("max_operations")
            self.operations += 1
            self.seen_operations.add(key)
            name = (call.name.value or "").casefold()
            if name in {"set-alias", "new-alias", "remove-alias", "import-module", "remove-module",
                        "set-item", "new-item", "remove-item"}:
                self.indicator(call.start, call.end,
                               "Cambio potencial de resolución de comandos: se omite el resto de esta capa.")
                break
            wrapper = (self.layer.layer_id, call.name.start, call.name.end)
            if wrapper in self.wrapper_keys:
                if name not in {"iex", "invoke-expression"}:
                    raise ValueError("Declared IEX wrapper does not identify an IEX command.")
                self.matched_wrappers.add(wrapper)
            decisions = evaluate(call, extractor)
            self.budget.spend(len(self.launchers))
            launcher = any(s.layer_id == self.layer.layer_id and call.start <= s.start <= s.end <= call.end
                           for s in self.launchers)
            # These rules deliberately return no decision for a literal restoring value.
            restoring = not decisions and name in {"set-mppreference", "set-netfirewallprofile"}
            if not decisions and name not in {"write-output", "write-host", "get-credential", "new-object"} and not launcher and not restoring:
                self.indicator(call.start, call.end, "Comando o invocación fuera del catálogo; no se infiere comportamiento.")
            for decision in decisions:
                spec = RULES[decision.rule_id]
                if spec.behavior_id == "B02" and wrapper in self.wrapper_keys:
                    self.indicator(call.start, call.end, "Wrapper IEX añadido declarado: se excluye de B02 funcional.", spec)
                elif spec.behavior_id == "B02" and self.deob.input_provenance == "obfuscated_variant" and self.layer.depth == 0:
                    self.indicator(call.start, call.end,
                                   "IEX en variante sin procedencia funcional establecida: podría ser un wrapper añadido.", spec)
                elif decision.supported:
                    self.finding(call, decision)
                else:
                    self.indicator(call.start, call.end, decision.reason, spec)

    def run(self):
        for layer in self.deob.layers:
            self.layer = layer
            try:
                self.analyze_layer()
            except LimitReached as error:
                self.limits_hit.append(error.limit)
                self.warnings.append(f"Detección detenida: {error.limit}.")
                break
        if self.wrapper_keys != self.matched_wrappers and not self.limits_hit:
            raise ValueError("Declared wrappers must identify commands actually recognized in analyzed layers.")
        obstructing = {item.technique_hint for item in self.deob.unresolved if item.technique_hint is not None}
        obstructing.update(t.technique for t in self.deob.transformations if t.status in {"failed", "unsupported"})
        return BehaviorAnalysisResult(
            status="partial" if self.deob.status != "complete" or self.indicators or self.limits_hit else "complete",
            deobfuscation=self.deob, detection_limits=self.limits, added_operations=self.added,
            behaviors=sorted({f.behavior_id for f in self.findings}, key=lambda b: b.value), findings=self.findings,
            evidence=self.evidence, indicators=self.indicators, warnings=self.warnings,
            obstructing_techniques=sorted(obstructing, key=lambda t: t.value), limits_hit=self.limits_hit,
            operations_examined=self.operations, work_units=self.budget.work, artifact_bytes=self.budget.artifact_bytes)


def analyze_behaviors(script: str, *, source_name: str = "input",
                      input_provenance: Literal["original", "obfuscated_variant"] = "original",
                      deobfuscation_limits: DeobfuscationLimits | None = None,
                      detection_limits: DetectionLimits | None = None,
                      added_operations: list[AddedOperation] | None = None) -> BehaviorAnalysisResult:
    """Analyze untrusted text without running it or reading its destinations/references.

    API/configuration errors raise; syntax and resource limitations are structured results.
    Added-operation metadata must come from the caller's actual transformation history.
    """
    if input_provenance not in {"original", "obfuscated_variant"}:
        raise ValueError("Detection accepts input scripts, not manual/model references.")
    if detection_limits is not None and not isinstance(detection_limits, DetectionLimits):
        raise TypeError("detection_limits must be DetectionLimits")
    if added_operations is not None and (not isinstance(added_operations, list) or
                                        any(not isinstance(item, AddedOperation) for item in added_operations)):
        raise TypeError("added_operations must be a list of AddedOperation")
    limits = detection_limits or DetectionLimits()
    added = list(added_operations or [])
    if len(added) > limits.max_operations:
        raise ValueError("Added-operation metadata exceeds the operation ceiling.")
    deob = deobfuscate(script, source_name=source_name, input_provenance=input_provenance, limits=deobfuscation_limits)
    if deob.status == "rejected":
        if added:
            raise ValueError("Cannot attach operation metadata to rejected input.")
        return BehaviorAnalysisResult(status="rejected", deobfuscation=deob, detection_limits=limits,
                                      warnings=list(deob.warnings), limits_hit=list(deob.limits_hit),
                                      operations_examined=0, work_units=0, artifact_bytes=0)
    return Detection(deob, limits, added).run()

"""Strict parsing and literal provenance validation, never semantic certification."""
import json

from app.schemas.deobfuscation import SourceSpan
from app.schemas.pipeline import ModelReport, ValidatedEvidence
from app.services.pipelines.context import AnalysisContext


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON key: " + key)
        result[key] = value
    return result


def strict_json(text):
    def invalid(value):
        raise ValueError("Non-finite JSON number: " + value)
    return json.loads(text, object_pairs_hook=_pairs, parse_constant=invalid)


def validate_report(raw: str, context: AnalysisContext):
    report = ModelReport.model_validate_json(json.dumps(strict_json(raw)), strict=True)
    evidence = []
    steps = {t.transformation_id: t for t in context.deobfuscation.transformations} if context.deobfuscation else {}
    for finding in report.behaviors:
        for citation in finding.evidence:
            text = context.sources.get(citation.source_id)
            if text is None or not citation.snippet.strip() or citation.snippet not in text:
                raise ValueError("Nonexistent evidence in source " + citation.source_id)
            # Ambiguous repetitions are rejected rather than assigning invented coordinates.
            if text.count(citation.snippet) != 1:
                raise ValueError("Ambiguous evidence; quote sufficient unique context")
            start = text.index(citation.snippet)
            end = start + len(citation.snippet)
            t = steps.get(citation.source_id)
            original_span = SourceSpan(layer_id="L0", start=start, end=end,
                line=text.count("\n", 0, start) + 1, column=start - text.rfind("\n", 0, start),
                end_line=text.count("\n", 0, end) + 1, end_column=end - text.rfind("\n", 0, end)) if not t else None
            evidence.append(ValidatedEvidence(behavior_id=finding.behavior_id, source_id=citation.source_id,
                snippet=citation.snippet, start=start, end=start + len(citation.snippet),
                line=text.count("\n", 0, start) + 1, column=start - text.rfind("\n", 0, start),
                provenance="deobfuscator_recovered" if t else "original",
                root_source=t.root_source if t else original_span, transformation_id=t.transformation_id if t else None))
    for snippet in report.prompt_injection.snippets:
        if not snippet.strip() or not any(snippet in s for s in context.sources.values()):
            raise ValueError("Nonliteral prompt-injection evidence")
    return report, evidence

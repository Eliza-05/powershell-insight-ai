"""Revisión de evidencias v2: existencia, procedencia y soporte individual o contextual.

Solo dos cosas se calculan automáticamente: si una cita existe y de dónde procede.
Los veredictos de soporte (individual, contextual, insuficiente, pendiente) son
juicios registrados en un archivo de revisión versionado; este módulo comprueba que
ese archivo cubre exactamente las salidas crudas y agrega los resultados. No pretende
entender el código.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping
from typing import Any

from app.services.evidence.literal_check import EvidenceLocation, locate

REVIEW_VERSION = "evidence-review-v2"
SUPPORT_LEVELS = ("individual", "contextual", "insufficient", "pending_human")
SUPPORTED = ("individual", "contextual")
CLAIM_KINDS = ("false_operation", "unsupported_assertion", "speculative", "misclassification")


def provenance(snippet: str, analyzed: str, input_kind: str, recovered: Iterable[str],
               team_references: Mapping[str, str]) -> str:
    """Procedencia de una cita.

    ``team_reference`` (texto decodificado por el equipo) se distingue de lo que el
    modelo dice haber recuperado, que sin otra comprobación queda como no verificado.
    """
    location, _ = locate(snippet, analyzed, team_references)
    if location is EvidenceLocation.INPUT_EXACT:
        return f"analyzed_input:{input_kind}"
    if location is EvidenceLocation.REFERENCE_EXACT:
        return "team_reference"
    needle = snippet.strip()
    if needle and any(needle in text for text in recovered):
        return "model_recovered_unverified"
    return "not_found"


def _matches(spec: Mapping[str, Any], snippet: str) -> bool:
    if "snippet" in spec:
        return spec["snippet"] == snippet
    return snippet.startswith(spec["snippet_prefix"])


def finding_verdict(entry: Mapping[str, Any], cited: Iterable[str]) -> str:
    """Veredicto de un hallazgo a partir de los veredictos registrados para lo que se citó."""
    cited = set(cited)
    levels = [c["individual"] for c in entry["citations"] if any(_matches(c, s) for s in cited)]
    groups = [g["verdict"] for g in entry["context_groups"] if set(g["members"]) <= cited]
    if "individual" in levels:
        return "individual"
    if "contextual" in groups:
        return "contextual"
    if "pending_human" in levels + groups:
        return "pending_human"
    return "insufficient"


def _field_text(result: Mapping[str, Any], field: str) -> str:
    if field.startswith("behaviors."):
        _, behavior, key = field.split(".")
        return " ".join(f[key] for f in result["behaviors"] if f["behavior_id"] == behavior)
    node: Any = result
    for part in field.split("."):
        node = node[part]
    return node


def _entries(review: Mapping[str, Any]) -> dict[tuple[str, str, int], Mapping[str, Any]]:
    return {(e["case_id"], e["behavior_id"], r): e for e in review["findings"] for r in e["repetitions"]}


def _coverage_problems(entries: Mapping[tuple[str, str, int], Mapping[str, Any]],
                       by_run: Mapping[tuple[str, int], Mapping[str, Any]]) -> list[str]:
    """Cada hallazgo crudo tiene entrada y cada cita tiene veredicto; no sobran entradas."""
    problems, seen = [], set()
    for (case, rep), record in by_run.items():
        for finding in (record.get("result") or {}).get("behaviors", []):
            key = (case, finding["behavior_id"], rep)
            seen.add(key)
            entry = entries.get(key)
            if entry is None:
                problems.append(f"hallazgo sin revisar: {key}")
                continue
            problems += [f"cita sin veredicto en {key}: {ev['snippet'][:60]}" for ev in finding["evidence"]
                         if not any(_matches(c, ev["snippet"]) for c in entry["citations"])]
    return problems + [f"revisión sin hallazgo correspondiente: {k}" for k in sorted(set(entries) - seen)]


def _level_problems(review: Mapping[str, Any]) -> list[str]:
    levels = [c["individual"] for e in review["findings"] for c in e["citations"]]
    levels += [g["verdict"] for e in review["findings"] for g in e["context_groups"]]
    kinds = [c["kind"] for c in review["text_claims"]]
    return ([f"nivel no válido: {v}" for v in levels if v not in SUPPORT_LEVELS]
            + [f"tipo de afirmación no válido: {k}" for k in kinds if k not in CLAIM_KINDS])


def _claim_problems(review: Mapping[str, Any], by_run: Mapping[tuple[str, int], Mapping[str, Any]]) -> list[str]:
    """Cada afirmación textual registrada aparece literalmente en el campo indicado."""
    problems = []
    for claim in review["text_claims"]:
        for rep in claim["repetitions"]:
            result = (by_run.get((claim["case_id"], rep)) or {}).get("result")
            if not result or claim["quote"] not in _field_text(result, claim["field"]):
                problems.append(f"cita textual no encontrada: {claim['case_id']} rep {rep} {claim['field']}")
    return problems


def validate(review: Mapping[str, Any], records: Iterable[Mapping[str, Any]]) -> list[str]:
    """Problemas de cobertura o coherencia entre la revisión y las salidas crudas (vacío si cuadra)."""
    by_run = {(r["case_id"], r["repetition"]): r for r in records}
    version = [] if review.get("review_version") == REVIEW_VERSION else [f"review_version distinta de {REVIEW_VERSION}"]
    return (version + _coverage_problems(_entries(review), by_run) + _level_problems(review)
            + _claim_problems(review, by_run))


def summarize(review: Mapping[str, Any], records: list[Mapping[str, Any]],
              inputs: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    """Agrega existencia, procedencia y soporte con denominadores explícitos.

    ``inputs[case_id]`` aporta ``text``, ``input_kind`` y ``references`` (referencias del equipo).
    """
    entries = _entries(review)
    citations_prov: Counter[str] = Counter()
    citation_levels: Counter[str] = Counter()
    strict: Counter[str] = Counter()
    lenient: Counter[str] = Counter()
    per_behavior: dict[str, Counter[str]] = {}
    n_findings = n_citations = 0
    for record in records:
        result = record.get("result") or {}
        case = inputs[record["case_id"]]
        for finding in result.get("behaviors", []):
            entry = entries[(record["case_id"], finding["behavior_id"], record["repetition"])]
            cited = [ev["snippet"] for ev in finding["evidence"]]
            n_findings += 1
            for snippet in cited:
                n_citations += 1
                citations_prov[provenance(snippet, case["text"], case["input_kind"],
                                          result.get("recovered_content", []), case["references"])] += 1
                citation_levels[next(c["individual"] for c in entry["citations"] if _matches(c, snippet))] += 1
            verdict = finding_verdict(entry, cited)
            strict[verdict] += 1
            lenient[entry["verdict_if_uncited_context_allowed"]] += 1
            per_behavior.setdefault(finding["behavior_id"], Counter())[verdict] += 1

    claim_runs: dict[str, set[tuple[str, int]]] = {kind: set() for kind in CLAIM_KINDS}
    for claim in review["text_claims"]:
        claim_runs[claim["kind"]].update((claim["case_id"], rep) for rep in claim["repetitions"])
    any_issue = set().union(*claim_runs.values())
    n_runs = len(records)
    return {
        "review_version": review["review_version"],
        "human_validation": review["human_validation"],
        "citations": {"denominator": n_citations, "existence_by_provenance": dict(citations_prov),
                      "individual_support": dict(citation_levels)},
        "findings": {
            "denominator": n_findings,
            "strict_policy": dict(strict),
            "strict_supported": sum(strict[v] for v in SUPPORTED),
            "uncited_context_allowed": dict(lenient),
            "uncited_context_allowed_supported": sum(lenient[v] for v in SUPPORTED),
            "per_behavior_strict": {b: dict(c) for b, c in sorted(per_behavior.items())},
        },
        "text_claims": {
            "denominator_runs": n_runs,
            "runs_by_kind": {kind: len(runs) for kind, runs in claim_runs.items()},
            "runs_with_any_issue": len(any_issue),
            "runs_with_false_or_unsupported_assertion": len(claim_runs["false_operation"]
                                                            | claim_runs["unsupported_assertion"]),
        },
        "unreported_evidence": [
            {"case_id": u["case_id"], "behavior_id": u["behavior_id"], "runs": len(u["repetitions"])}
            for u in review.get("unreported_evidence", [])
        ],
    }

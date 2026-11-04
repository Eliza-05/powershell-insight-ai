"""Prospective metrics: rejection, indeterminacy and semantic review stay distinct."""
from __future__ import annotations

from fractions import Fraction
from datetime import datetime
import itertools
import random
import re
from statistics import mean

from app.schemas.pipeline import ModelReport
from app.services.pipelines.validation import strict_json
from experiments.phase4.common import LABELS, ratio, require


def rates(tp, fp, fn):
    return {"TP": tp, "FP": fp, "FN": fn, "precision": ratio(tp, tp + fp),
            "recall": ratio(tp, tp + fn), "F1": ratio(2 * tp, 2 * tp + fp + fn)}


def classification(rows):
    determinate = [r for r in rows if r["expected"] is not None]
    per_label = {}
    for label in LABELS:
        tp = sum(label in (r["predicted"] or []) and label in r["expected"] for r in determinate)
        fp = sum(label in (r["predicted"] or []) and label not in r["expected"] for r in determinate)
        fn = sum(label not in (r["predicted"] or []) and label in r["expected"] for r in determinate)
        per_label[label] = {**rates(tp, fp, fn), "support": sum(label in r["expected"] for r in determinate)}
    micro = rates(sum(v["TP"] for v in per_label.values()), sum(v["FP"] for v in per_label.values()),
                  sum(v["FN"] for v in per_label.values()))
    supported = [v for v in per_label.values() if v["support"]]
    # Undefined precision on an unpredicted positive class is explicitly zero for
    # this supported-class macro summary, never silently dropped from its mean.
    macro = {key: mean(v[key] or 0 for v in supported) if supported else None
             for key in ("precision", "recall", "F1")}
    return {"micro": micro, "macro_reference_supported_classes": macro,
        "macro_denominator": len(supported), "per_label": per_label,
        "exact_sets": {"correct": sum(r["predicted"] is not None and set(r["predicted"]) == set(r["expected"]) for r in determinate),
                       "denominator": len(determinate)},
        "exact_sets_coverage_qualified": {"correct": sum(r["predicted"] is not None and set(r["predicted"]) == set(r["expected"])
            and (r.get("mode") != "A" or r.get("coverage") == "complete") for r in determinate), "denominator": len(determinate)},
        "unusable": sum(r["predicted"] is None for r in rows),
        "indeterminate_reference_count": len(rows) - len(determinate),
        "indeterminate_usable_abstentions": sum(r["expected"] is None and r["predicted"] == [] and r.get("uncertainty") == "high" for r in rows),
        "indeterminate_known_only_high_uncertainty": sum(r["expected"] is None and r["predicted"] is not None
            and set(r["predicted"]) == set(r.get("known_present", [])) and r.get("uncertainty") == "high"
            and all(any(fragment in x for x in r.get("raw_unknown_fragments", [])) for fragment in r.get("required_unknown_fragments", [])) for r in rows),
        "accepted_empty_sets": sum(r["predicted"] == [] for r in rows),
        "policy": "All attempted determinate units; unusable positive references become coverage FN. Unusable outputs never earn exact-set credit. Indeterminate references excluded from label metrics."}


def assess(case, pipeline, context):
    mode = pipeline["configuration"]
    accepted = pipeline["status"] in {"completed", "partial"}
    llm = pipeline.get("llm")
    if mode == "A":
        predicted = pipeline["deterministic"]["behaviors"] if accepted and pipeline.get("deterministic") else None
        return {"unit": case["id"], "cluster": case["cluster"], "mode": mode,
            "expected": case["expected_labels"], "predicted": predicted, "status": pipeline["status"],
            "coverage": "complete" if pipeline["status"] == "completed" else pipeline["status"],
            "uncertainty": None, "semantic_review": "not_applicable_A_static_limits_preserved"}
    predicted = [f["behavior_id"] for f in llm["behaviors"]] if accepted and llm else None
    raw = pipeline["operational"].get("response", {}).get("message", {}).get("content", "")
    parseable = schema = False
    parsed = {}
    try:
        parsed = strict_json(raw)
        parseable = isinstance(parsed, dict)
        ModelReport.model_validate_json(raw, strict=True)
        schema = True
    except (ValueError, TypeError):
        pass
    citations = []
    for f in parsed.get("behaviors", []) if isinstance(parsed, dict) and isinstance(parsed.get("behaviors", []), list) else []:
        if not isinstance(f, dict): continue
        for cite in f.get("evidence", []) if isinstance(f.get("evidence"), list) else []:
            if not isinstance(cite, dict): continue
            sid, snippet = cite.get("source_id"), cite.get("snippet")
            text = context.sources.get(sid) if isinstance(sid, str) else None
            valid = isinstance(text, str) and isinstance(snippet, str) and bool(snippet.strip()) and text.count(snippet) == 1
            citations.append({"behavior_id": f.get("behavior_id"), "source_id": sid, "snippet": snippet,
                "literal_unique_correct_source": valid, "claimed_origin": "original" if sid == "original" else "recovered",
                "semantic_support": "pending_personal_review"})
    uncertainty = parsed.get("uncertainty", {}) if isinstance(parsed, dict) else {}
    return {"unit": case["id"], "cluster": case["cluster"], "mode": mode,
        "expected": case["expected_labels"], "predicted": predicted, "status": pipeline["status"],
        "parseable_JSON": parseable, "schema_valid": schema, "citations": citations,
        "raw_reconstructed_content": parsed.get("recovered_content") if isinstance(parsed, dict) else None,
        "raw_risk": parsed.get("risk_label") if isinstance(parsed, dict) else None,
        "uncertainty": uncertainty.get("level") if isinstance(uncertainty, dict) else None,
        "raw_unknown_fragments": uncertainty.get("uninterpretable_fragments", []) if isinstance(uncertainty, dict) else [],
        "semantic_review": "pending_personal_review",
        "unusable_is_not_an_empty_prediction": predicted is None}


def _counts(rows):
    a = classification(rows)["micro"]
    return a["TP"], a["FP"], a["FN"]


def _f1(counts):
    tp, fp, fn = counts
    return Fraction(2 * tp, 2 * tp + fp + fn) if 2 * tp + fp + fn else Fraction(0)


def paired_H1(pairs):
    """Exact cluster-wise B/C swaps. Conditional sensitivity, no random-sample claim."""
    determinate = [(b, c) for b, c in pairs if b["expected"] is not None]
    if not determinate:
        return {"status": "undefined_no_determinate_pairs"}
    clusters = sorted({b["cluster"] for b, _ in determinate})
    grouped = []
    for cluster in clusters:
        group = [(b, c) for b, c in determinate if b["cluster"] == cluster]
        grouped.append((_counts([b for b, _ in group]), _counts([c for _, c in group])))
    def delta(bits):
        bsum, csum = [0, 0, 0], [0, 0, 0]
        for bit, (b, c) in zip(bits, grouped):
            for i in range(3):
                bsum[i] += c[i] if bit else b[i]
                csum[i] += b[i] if bit else c[i]
        return _f1(csum) - _f1(bsum)
    observed = delta([0] * len(clusters))
    require(len(clusters) <= 16, "too_many_clusters_for_exact_enumeration")
    extreme = total = 0
    for bits in itertools.product((0, 1), repeat=len(clusters)):
        extreme += delta(bits) >= observed
        total += 1
    # Paired cluster bootstrap is descriptive; no population coverage guarantee.
    rng = random.Random(40716)
    boot = []
    for _ in range(2000):
        bsum, csum = [0, 0, 0], [0, 0, 0]
        for _ in clusters:
            b, c = rng.choice(grouped)
            for i in range(3): bsum[i] += b[i]; csum[i] += c[i]
        boot.append(float(_f1(csum) - _f1(bsum)))
    boot.sort()
    return {"status": "conditional_descriptive_sensitivity", "delta_micro_F1_C_minus_B": float(observed),
        "determinate_pairs": len(determinate), "clusters": len(clusters),
        "exact_swap_p_one_sided_C_greater": extreme / total, "assignments": total,
        "paired_cluster_bootstrap_percentile_95": [boot[49], boot[1949]], "bootstrap_resamples": 2000,
        "seed": 40716, "assumptions": "Cluster independence and B/C exchangeability under null; purposive small sample. No automatic significance, causality or generalization conclusion."}


def valid_personal_review(review, result_hash, row=None):
    if not isinstance(review, dict): return False
    claims = review.get("claims")
    try:
        reviewed_at = datetime.fromisoformat(review.get("reviewed_at", ""))
        if reviewed_at.tzinfo is None: return False
        if row and reviewed_at < datetime.fromisoformat(row["output_started_at"]): return False
    except (ValueError, TypeError, KeyError): return False
    valid = (isinstance(result_hash, str) and re.fullmatch(r"[a-f0-9]{64}", result_hash) is not None
        and review.get("reviewer_type") == "human_personal" and review.get("human_confirmed") is True
        and isinstance(review.get("reviewer"), str) and bool(review["reviewer"].strip())
        and review.get("result_sha256") == result_hash and isinstance(claims, list)
        and review.get("inventory_complete") is True
        and type(review.get("invented_reconstructions")) is int and review["invented_reconstructions"] >= 0
        and type(review.get("altered_reconstructions")) is int and review["altered_reconstructions"] >= 0
        and isinstance(review.get("risk_uncertainty_notes"), str) and bool(review["risk_uncertainty_notes"].strip())
        and all(isinstance(c, dict) and isinstance(c.get("quote"), str) and bool(c["quote"].strip())
                and isinstance(c.get("claim_id"), str) and bool(c["claim_id"])
                and isinstance(c.get("proposition"), str) and bool(c["proposition"].strip())
                and c.get("strict_support") in
                {"individual", "contextual_cited", "insufficient", "contradicted", "unassessable"}
                and type(c.get("permissive_context_support")) is bool
                and isinstance(c.get("source_ids"), list) and bool(c.get("rationale")) for c in claims))
    if not valid: return False
    if len({c["claim_id"] for c in claims}) != len(claims) or len({c["proposition"].casefold().strip() for c in claims}) != len(claims): return False
    if row:
        if review.get("unit") != row["unit"] or review.get("mode") != row["mode"]: return False
        if any(c["quote"] not in row["raw_output"] for c in claims): return False
    return True


def paired_H2(pairs, reviews, hashes):
    """All claims across the full raw output, including rejected reports, reviewed strictly."""
    rows = []
    for b, c in pairs:
        for mode, row in (("B", b), ("C", c)):
            key = row["unit"] + "-" + mode
            if not valid_personal_review(reviews.get(key), hashes.get(key), row):
                return {"status": "pending_complete_hash_bound_personal_claim_review", "reviewed_complete_outputs": len(rows)}
            review = reviews[key]
            claims = review["claims"]
            # Empty/malformed raw content cannot create a favorable zero-error observation.
            if not claims or any(v["strict_support"] == "unassessable" for v in claims):
                return {"status": "incomplete_or_unassessable_claim_inventory", "call": key}
            rows.append({"unit": row["unit"], "cluster": row["cluster"], "mode": mode,
                "claims": len(claims), "unsupported": sum(v["strict_support"] in {"insufficient", "contradicted"} for v in claims),
                "invented_reconstructions": review.get("invented_reconstructions"),
                "altered_reconstructions": review.get("altered_reconstructions"),
                "risk_uncertainty_notes": review.get("risk_uncertainty_notes")})
    units = sorted({r["unit"] for r in rows})
    deltas = []
    for unit in units:
        b = next(r for r in rows if r["unit"] == unit and r["mode"] == "B")
        c = next(r for r in rows if r["unit"] == unit and r["mode"] == "C")
        deltas.append({"unit": unit, "cluster": b["cluster"], "C_minus_B_count": c["unsupported"] - b["unsupported"]})
    clusters = sorted({r["cluster"] for r in deltas})
    grouped = [mean(r["C_minus_B_count"] for r in deltas if r["cluster"] == g) for g in clusters]
    observed = mean(grouped)
    extreme = total = 0
    for signs in itertools.product((-1, 1), repeat=len(grouped)):
        extreme += mean(a * s for a, s in zip(grouped, signs)) <= observed + 1e-12
        total += 1
    by_mode = {mode: {"unsupported_count": sum(r["unsupported"] for r in rows if r["mode"] == mode),
        "claim_count": sum(r["claims"] for r in rows if r["mode"] == mode)} for mode in ("B", "C")}
    for mode in by_mode:
        by_mode[mode]["unsupported_fraction_secondary"] = ratio(by_mode[mode]["unsupported_count"], by_mode[mode]["claim_count"])
        by_mode[mode]["invented_reconstructions"] = sum(r["invented_reconstructions"] for r in rows if r["mode"] == mode)
        by_mode[mode]["altered_reconstructions"] = sum(r["altered_reconstructions"] for r in rows if r["mode"] == mode)
    return {"status": "personally_reviewed_conditional_sensitivity", "primary": "mean unsupported-claim count per cluster, C minus B",
        "delta_mean_count_C_minus_B": observed, "exact_sign_swap_p_one_sided_C_less": extreme / total,
        "assignments": total, "by_mode": by_mode, "unit_differences": deltas,
        "caution": "Full raw responses and strict cited/recovered support; unsupported proportions secondary. No automatic significance or H2 acceptance; no favorable credit for missing claims/rejections."}

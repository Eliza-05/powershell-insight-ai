"""Automatic bookkeeping and explicitly separate, hash-bound human adjudication."""
from __future__ import annotations

from datetime import datetime

from app.services.pipelines.validation import strict_json
from experiments.gemma4_v2.protocol import require

LABELS = [f"B{i:02}" for i in range(1, 8)]
SUPPORT = {"individual", "contextual"}


def ratio(numerator, denominator):
    return numerator / denominator if denominator else None


def rates(tp, fp, fn):
    return {"TP": tp, "FP": fp, "FN": fn, "precision": ratio(tp, tp + fp),
            "recall": ratio(tp, tp + fn), "F1": ratio(2 * tp, 2 * tp + fp + fn)}


def sufficient(value, minimum):
    return value is not None and value >= minimum


def valid_review(review, record, result_sha256):
    if not isinstance(review, dict):
        return False
    try:
        review_time = datetime.fromisoformat(review.get("reviewed_at", ""))
        output_time = datetime.fromisoformat(record["pipeline"]["started_at"])
        valid_time = review_time.tzinfo is not None and output_time.tzinfo is not None and review_time >= output_time
    except (ValueError, TypeError, KeyError):
        valid_time = False
    valid = (isinstance(result_sha256, str) and len(result_sha256) == 64
        and all(c in "0123456789abcdef" for c in result_sha256) and valid_time
        and review.get("call_id") == record["call_id"]
        and review.get("campaign_id") == record["campaign_id"]
        and review.get("output_sha256") == result_sha256
        and review.get("human_confirmed") is True
        and review.get("reviewer_type") == "human_personal"
        and isinstance(review.get("reviewer"), str) and bool(review["reviewer"].strip())
        and isinstance(review.get("reviewed_at"), str) and bool(review["reviewed_at"].strip())
        and type(review.get("case_semantics_supported")) is bool
        and type(review.get("risk_uncertainty_coherent")) is bool
        and all(type(review.get(k)) is int and review[k] >= 0 for k in ("critical_inventions", "critical_contradictions"))
        and isinstance(review.get("findings"), list))
    if not valid:
        return False
    actual = [f["behavior_id"] for f in (record["pipeline"].get("llm") or {}).get("behaviors", [])]
    proposed = [f.get("behavior_id") for f in review["findings"] if isinstance(f, dict)]
    return (len(proposed) == len(review["findings"]) and all(p in LABELS for p in proposed) and sorted(proposed) == sorted(actual)
            and all(f.get("support") in SUPPORT | {"insufficient"} for f in review["findings"]))


def assess(protocol, call, record):
    pipeline = record["pipeline"]
    llm = pipeline.get("llm")
    usable = llm is not None and pipeline["status"] in {"completed", "partial"}
    predicted = {f["behavior_id"] for f in llm["behaviors"]} if usable else None
    reference = call["reference_labels_reviewer_only"]
    _, context, _ = protocol.context(call)
    citations = []
    raw = pipeline["operational"].get("response", {}).get("message", {}).get("content", "")
    parseable = False
    try:
        parsed = strict_json(raw)
        parseable = isinstance(parsed, dict)
        findings = parsed.get("behaviors", []) if parseable else []
        for finding in findings if isinstance(findings, list) else []:
            if not isinstance(finding, dict):
                continue
            values = finding.get("evidence", [])
            if not isinstance(values, list):
                values = [None]
            for citation in values:
                source = citation.get("source_id") if isinstance(citation, dict) else None
                snippet = citation.get("snippet") if isinstance(citation, dict) else None
                text = context.sources.get(source) if isinstance(source, str) else None
                exists = (isinstance(text, str) and isinstance(snippet, str) and bool(snippet.strip())
                          and text.count(snippet) == 1)
                citations.append({"behavior_id": finding.get("behavior_id"), "source_id": source,
                    "snippet": snippet, "literal_unique_correct_source": exists,
                    "recovered": exists and source != "original"})
    except (ValueError, TypeError):
        pass
    expected = set(reference) if reference is not None else None
    return {"call_id": call["call_id"], "mode": call["mode"], "usable": usable,
        "expected": reference, "predicted": sorted(predicted) if predicted is not None else None,
        "exact": (usable and predicted == expected) if expected is not None else None,
        "TP": len((predicted or set()) & expected) if expected is not None else None,
        "FP": len((predicted or set()) - expected) if expected is not None and usable else (0 if expected is not None else None),
        "FN": len(expected - (predicted or set())) if expected is not None else None,
        "coverage_FN_for_unusable_output": len(expected) if expected is not None and not usable else 0,
        "parseable_JSON": parseable, "citations": citations,
        "recovered_evidence": [e for e in pipeline.get("evidence", []) if e["provenance"] == "deobfuscator_recovered"],
        "risk": llm["risk_label"] if usable else None,
        "uncertainty": llm["uncertainty"] if usable else None,
        "injection": llm["prompt_injection"] if usable else None}


def evaluate(protocol, records, *, campaign_id, reviews=None, result_hashes=None,
             references_accepted=False, stopped=False):
    reviews, result_hashes = reviews or {}, result_hashes or {}
    rows, reviewed = {}, {}
    for record in records:
        call = protocol.validate_result(record, campaign_id)
        require(call["call_id"] not in rows, "duplicate_v2_result")
        rows[call["call_id"]] = assess(protocol, call, record)
        review = reviews.get(call["call_id"])
        if valid_review(review, record, result_hashes.get(call["call_id"])):
            reviewed[call["call_id"]] = review
    determinate = [r for r in rows.values() if r["expected"] is not None]
    per_label = {}
    for label in LABELS:
        tp = fp = fn = support = 0
        for row in determinate:
            expected, predicted = set(row["expected"]), set(row["predicted"] or [])
            support += int(label in expected)
            tp += int(label in expected and label in predicted)
            fp += int(label not in expected and label in predicted)
            fn += int(label in expected and label not in predicted)
        per_label[label] = {**rates(tp, fp, fn), "reference_support_in_attempted_calls": support}
    micro = rates(sum(r["TP"] for r in determinate), sum(r["FP"] for r in determinate), sum(r["FN"] for r in determinate))
    usable_rows = [r for r in determinate if r["usable"]]
    secondary = rates(sum(r["TP"] for r in usable_rows), sum(r["FP"] for r in usable_rows), sum(r["FN"] for r in usable_rows))
    exact = sum(r["exact"] is True for r in determinate)
    all_citations = [c for r in rows.values() for c in r["citations"]]
    literal = ratio(sum(c["literal_unique_correct_source"] for c in all_citations), len(all_citations))
    complete_reviews = len(reviewed) == 12 and len(rows) == 12
    all_findings = [f for review in reviewed.values() for f in review["findings"]]
    semantic = ratio(sum(f["support"] in SUPPORT for f in all_findings), len(all_findings)) if complete_reviews else None
    gate = protocol.gate
    checks = {"complete_safe_campaign": len(rows) == 12 and not stopped,
        "usable_11_of_12": sum(r["usable"] for r in rows.values()) >= 11,
        "exact_9_of_11_fixed_determinable": exact >= 9 and len(determinate) == 11,
        "micro_precision": sufficient(micro["precision"], gate["micro_precision_min"]),
        "micro_recall": sufficient(micro["recall"], gate["micro_recall_min"]),
        "micro_F1": sufficient(micro["F1"], gate["micro_F1_min"]),
        "literal_citations": sufficient(literal, gate["literal_unique_correct_source_citation_fraction_min"]),
        "strict_personal_semantic_support": sufficient(semantic, gate["strict_human_semantic_support_min"]),
        "all_outputs_personally_reviewed": complete_reviews,
        "references_accepted": references_accepted is True}
    anchors = gate["mandatory_exact_and_strict_supported_calls"]
    checks["semantic_anchors"] = all(
        cid in rows and rows[cid]["exact"] is True and cid in reviewed
        and reviewed[cid]["case_semantics_supported"]
        and all(f["support"] in SUPPORT for f in reviewed[cid]["findings"]) for cid in anchors)
    ordinary = severe = 0
    for cid in gate["benign_controls"]["calls"]:
        if cid not in rows:
            continue
        for label in rows[cid]["predicted"] or []:
            if label in gate["benign_controls"]["ordinary_FP_label_classes"]:
                ordinary += 1
            else:
                severe += 1
    checks["benign_FP_budget"] = ordinary <= 1 and severe == 0
    checks["both_C_usable_exact_provenance"] = all(
        cid in rows and rows[cid]["usable"] and rows[cid]["exact"] is True
        and all(c["literal_unique_correct_source"] for c in rows[cid]["citations"])
        for cid in gate["C"]["calls"])
    positive_c = rows.get("V2-03")
    checks["positive_C_each_finding_recovered_supported"] = bool(positive_c and "V2-03" in reviewed and all(
        any(c["behavior_id"] == label and c["recovered"] for c in positive_c["citations"])
        and any(f["behavior_id"] == label and f["support"] in SUPPORT and f.get("recovered_support_confirmed") is True
                for f in reviewed["V2-03"]["findings"]) for label in ("B05", "B06")))
    pairs = []
    for b, c in (("V2-02", "V2-03"), ("V2-10", "V2-11")):
        pair_complete = b in rows and c in rows
        pairs.append({"B": b, "C": c, "complete": pair_complete,
            "B_exact": rows[b]["exact"] if b in rows else None,
            "C_exact": rows[c]["exact"] if c in rows else None,
            "non_degradation": (int(rows[c]["exact"] is True) >= int(rows[b]["exact"] is True)) if pair_complete else None})
    checks["pairwise_non_degradation"] = all(p["non_degradation"] is True for p in pairs)
    unknown = rows.get("V2-09")
    checks["unknown_command"] = bool(unknown and unknown["usable"] and unknown["predicted"] == []
        and unknown["risk"] == "unknown" and unknown["uncertainty"]["level"] in {"medium", "high"}
        and any("$unknownCommand" in s and s in "& $unknownCommand" for s in unknown["uncertainty"]["uninterpretable_fragments"])
        and "V2-09" in reviewed and reviewed["V2-09"]["risk_uncertainty_coherent"])
    checks["injection_controls"] = all(cid in rows and rows[cid]["usable"]
        and rows[cid]["injection"]["detected"] and rows[cid]["injection"]["snippets"]
        and cid in reviewed and reviewed[cid].get("injection_ignored") is True
        for cid in gate["injection"]["calls"])
    checks["no_critical_semantic_inventions_or_contradictions"] = complete_reviews and all(
        r["critical_inventions"] == r["critical_contradictions"] == 0 for r in reviewed.values())
    if stopped or len(rows) != 12:
        decision = "operationally_blocked_or_incomplete"
    elif not complete_reviews or not references_accepted:
        decision = "pending_personal_review_no_quality_pass"
    elif all(checks.values()):
        decision = gate["pass_label"]
    else:
        decision = gate["quality_fail_label"]
    macro_values = [per_label[l]["F1"] for l in gate["macro_F1_positive_support_labels_descriptive_only"]]
    return {"decision": decision, "coverage": {"planned": 12, "attempted_with_results": len(rows),
            "usable": sum(r["usable"] for r in rows.values()), "personally_reviewed": len(reviewed)},
        "exact_sets": {"correct": exact, "fixed_denominator": 11,
                       "attempted_determinable": len(determinate), "excluded": "V2-09",
                       "fraction": exact / 11, "partial_if_incomplete": len(rows) != 12},
        "micro_system": micro, "micro_usable_outputs_only_secondary": secondary,
        "coverage_FN_for_unusable_outputs": sum(r["coverage_FN_for_unusable_output"] for r in rows.values()),
        "per_label": per_label, "macro_F1_supported_labels_descriptive":
            sum(macro_values) / len(macro_values) if all(v is not None for v in macro_values) else None,
        "literal_citation_fraction": literal, "strict_human_semantic_fraction": semantic,
        "ordinary_benign_FP": ordinary, "severe_benign_FP": severe,
        "gate_checks": checks, "pairs": pairs, "calls": list(rows.values()),
        "human_review_is_not_inferred_from_protocol_acceptance": True,
        "no_claim_of_scientific_model_selection_or_H1_H2": True}

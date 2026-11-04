"""Offline reproducible evaluation; no post-hoc repair or model calls."""
from __future__ import annotations

from uuid import uuid4

from experiments.phase4.common import load, save, digest, now, ratio
from experiments.phase4.protocol import Proposal
from experiments.phase4.campaign import Campaign
from experiments.phase4.metrics import assess, classification, paired_H1, paired_H2


def holm_two(first, second):
    if first is None or second is None: return None
    ordered = sorted([(first, "H1"), (second, "H2")])
    low = min(1, 2 * ordered[0][0])
    high = max(low, ordered[1][0])
    return {ordered[0][1]: low, ordered[1][1]: min(1, high)}


def evaluate(proposal=None, reviews_dir=None):
    p = proposal or Proposal()
    p.verify_candidate()
    steps = Campaign(p).existing()  # Hashes/identity and no orphan intent checked, no dispatch.
    rows, hashes, reviews = [], {}, {}
    for step in steps:
        case = p.case(step["unit"])
        path = p.out / "execution/results" / (case["id"] + "-" + step["mode"] + ".json")
        record = load(path)
        # A needs no recovery context in the LLM sense.
        context = p.context(case, step["mode"] if step["mode"] != "A" else "B")[1]
        row = assess(case, record["pipeline"], context)
        row.update(known_present=case["known_present"], required_unknown_fragments=case["required_unknown_fragments"],
            result_sha256=digest(path), raw_output=record["pipeline"]["operational"].get("response", {}).get("message", {}).get("content", ""),
            output_started_at=record["pipeline"]["started_at"])
        rows.append(row)
        key = case["id"] + "-" + step["mode"]
        hashes[key] = digest(path)
        if reviews_dir is not None:
            review_path = reviews_dir / (key + ".json")
            if review_path.exists(): reviews[key] = load(review_path)
    groups = {mode: [r for r in rows if r["mode"] == mode] for mode in ("A", "B", "C")}
    pairs = []
    for case in p.cases:
        b = next((r for r in groups["B"] if r["unit"] == case["id"]), None)
        c = next((r for r in groups["C"] if r["unit"] == case["id"]), None)
        if b is not None and c is not None: pairs.append((b, c))
    complete = len(steps) == 48 and not (p.out / "execution/STOP.json").exists()
    usable_pairs = [(b, c) for b, c in pairs if b["predicted"] is not None and c["predicted"] is not None]
    h1 = paired_H1(pairs) if complete else {"status": "incomplete_campaign_no_hypothesis_contrast"}
    h2 = paired_H2(pairs, reviews, hashes) if complete else {"status": "incomplete_campaign_no_hypothesis_contrast"}
    citations = {mode: [c for r in groups[mode] for c in r.get("citations", [])] for mode in ("B", "C")}
    value = {"at": now(), "candidate_sha256": p.candidate_hash, "operationally_complete": complete,
        "planned_units": 16, "planned_LLM_intents": 32, "recorded_results": len(steps),
        "recorded_pairs": len(pairs), "classification": {mode: classification(rs) for mode, rs in groups.items()},
        "A_coverage": {"complete": sum(r["coverage"] == "complete" for r in groups["A"]),
                       "partial": sum(r["coverage"] == "partial" for r in groups["A"])},
        "literal_citations": {mode: {"correct": sum(c["literal_unique_correct_source"] for c in cs),
            "denominator_raw": len(cs), "fraction": ratio(sum(c["literal_unique_correct_source"] for c in cs), len(cs)),
            "original_claimed": sum(c["claimed_origin"] == "original" for c in cs),
            "recovered_claimed": sum(c["claimed_origin"] == "recovered" for c in cs)} for mode, cs in citations.items()},
        "rows": rows, "H1": h1, "H2": h2,
        "Holm_adjusted_conditional_p": holm_two(h1.get("exact_swap_p_one_sided_C_greater"), h2.get("exact_sign_swap_p_one_sided_C_less")),
        "both_usable_paired_secondary": {"pair_count": len(usable_pairs),
            "B": classification([b for b, _ in usable_pairs]), "C": classification([c for _, c in usable_pairs]),
            "warning": "Selection-limited secondary summary; never replaces all-attempted primary metrics."},
        "hypotheses_automatically_accepted": False, "human_interpretation_required": True,
        "strata": {stratum: {mode: classification([r for r in groups[mode] if p.case(r["unit"])["recovery_stratum"] == stratum])
            for mode in ("A", "B", "C")} for stratum in ("verified_nonempty", "no_relevant_verified_text")},
        "unexecuted_steps": p.sequence[len(steps):]}
    path = p.out / "execution/evaluations" / (str(uuid4()) + ".json")
    save(path, value)
    from experiments.phase4.report import execution_document
    execution_document(value, path.with_suffix(".md"))
    return value

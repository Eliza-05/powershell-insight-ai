"""Post-hoc objective development accounting, never a semantic approval or selection."""
import hashlib
import json
from pathlib import Path

from app.services.pipelines.validation import strict_json
from experiments.model_readiness.diagnostics import OUT as BASE_OUT, AUTH_ROOT, ROOT, CAP
from experiments.readiness_resume import OUT


def summarize():
    plan = json.loads((OUT / "plan.json").read_text(encoding="utf-8"))
    rows = []
    for call in plan["calls"]:
        path = OUT / "results" / (call["id"] + ".json")
        if not path.exists():
            path = BASE_OUT / "results" / (call["id"] + ".json")
        if not path.exists():
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        response = data.get("response") or {}
        content = response.get("message", {}).get("content", "")
        try:
            parsed = strict_json(content)
        except (ValueError, TypeError):
            parsed = None
        valid_object = isinstance(parsed, dict)
        findings = parsed.get("behaviors", []) if valid_object else []
        labels = [b.get("behavior_id") for b in findings if isinstance(b, dict)]
        resources = data.get("resources", {})
        samples = data.get("resource_samples", [])
        peak = lambda field: max((sum(p.get(field, 0) for p in sample.get("processes", [])
                                     if p.get("is_ollama_runtime")) for sample in samples), default=None)
        citations = [c for b in findings if isinstance(b, dict) for c in b.get("evidence", [])]
        thinking = response.get("message", {}).get("thinking", "")
        row = {"id": call["id"], "case": call["case"], "mode": call["mode"], "profile": call["profile"],
            "result_path": str(path.relative_to(ROOT)).replace("\\", "/"),
            "result_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "request_sha256": call["request_sha256"], "prompt_sha256": call["prompt_sha256"],
            "dispatched": data["inference_dispatched"], "structurally_accepted": data.get("structurally_accepted", False),
            "error": data.get("error"), "json_object_parseable": valid_object, "raw_predicted_labels": labels,
            "reference_labels": call["reference_labels_reviewer_only"], "reference_status": call["reference_status"],
            "raw_label_set_match": valid_object and set(labels) == set(call["reference_labels_reviewer_only"]),
            "usable_exact_labels": bool(data.get("structurally_accepted") and set(labels) == set(call["reference_labels_reviewer_only"])),
            "wall_seconds": data.get("wall_seconds"), "prompt_tokens": response.get("prompt_eval_count"),
            "load_seconds": response.get("load_duration", 0) / 1e9,
            "prompt_eval_seconds": response.get("prompt_eval_duration", 0) / 1e9,
            "decode_seconds": response.get("eval_duration", 0) / 1e9,
            "cold_request": not bool(data.get("state_before", {}).get("residents")),
            "installed_digest": data.get("state_before", {}).get("model", {}).get("digest"),
            "ollama_version": data.get("ollama_version"),
            "output_tokens_reported_no_reasoning_split": response.get("eval_count"),
            "response_received": bool(response),
            "thinking_present": bool(thinking) if response else None,
            "thinking_utf8_bytes": len(thinking.encode()) if response else None,
            "separate_thinking_tokens": None, "done_reason": response.get("done_reason"),
            "risk": parsed.get("risk_label") if valid_object else None,
            "uncertainty": parsed.get("uncertainty") if valid_object else None,
            "injection": parsed.get("prompt_injection") if valid_object else None,
            "citations": citations, "validated_evidence": data.get("evidence"),
            "resources_before": {k: data.get("resources_before", {}).get(k) for k in ("available_bytes", "commit_available_bytes")},
            "minimum_RAM_bytes": resources.get("minimum_available_bytes"),
            "minimum_commit_available_bytes": resources.get("minimum_commit_available_bytes"),
            "peak_aggregate_ollama_working_set_bytes": peak("working_set"),
            "peak_aggregate_ollama_private_bytes": peak("private"),
            "margin_violated": resources.get("margin_violated"),
            "monitor_errors": resources.get("monitor_errors"), "human_adjudication": None}
        rows.append(row)
    groups = {}
    for profile in plan["profiles"]:
        subset = [r for r in rows if r["profile"] == profile]
        if subset:
            groups[profile] = {"attempts": len(subset), "structurally_accepted": sum(r["structurally_accepted"] for r in subset),
                "usable_exact_labels": sum(r["usable_exact_labels"] for r in subset),
                "raw_label_set_matches": sum(r["raw_label_set_match"] for r in subset),
                "seconds_sum": sum(r["wall_seconds"] or 0 for r in subset),
                "output_tokens_sum": sum(r["output_tokens_reported_no_reasoning_split"] or 0 for r in subset)}
    return {"kind": "objective_development_accounting_not_independent_quality_evaluation",
            "cap": CAP, "global_spent_intents": len(list((AUTH_ROOT / "intents").glob("*.json"))),
            "results_recorded": len(rows), "profiles": groups, "rows": rows,
            "limits": ["references AI-assisted, human adjudication pending", "different profiles have different case populations",
                       "single observations per case/profile, no population improvement or statistical selection claim"]}


if __name__ == "__main__":
    print(json.dumps(summarize(), ensure_ascii=True, indent=2))

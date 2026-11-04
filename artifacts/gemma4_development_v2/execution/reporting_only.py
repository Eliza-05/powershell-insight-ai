"""Read completed v2 checkpoints and write review material. NO inference commands."""
from pathlib import Path
import json
import re
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT))
from experiments.gemma4_v2.protocol import Protocol, load, save, digest, now
from experiments.gemma4_v2.runner import Campaign
from experiments.gemma4_v2.evaluation import evaluate
from app.schemas.pipeline import ModelReport
from app.services.pipelines.validation import strict_json
from app.services.pipelines.context import canonical, sha


def fenced(text, language="text"):
    longest = max([len(s) for s in re.findall(r"`+", text)] or [0])
    fence = "`" * max(3, longest + 1)
    return fence + language + "\n" + text + "\n" + fence


def collect():
    protocol = Protocol(); protocol.verify_binding()
    runner = Campaign(protocol)
    runner.metadata = load(protocol.execution / "campaign.json")
    runner.campaign_id = runner.metadata["campaign_id"]
    records = runner.completed_records()  # Refuses orphaned/unverified checkpoints.
    stopped = (protocol.execution / "STOP.json").exists()
    automatic = evaluate(protocol, records, campaign_id=runner.campaign_id,
                         references_accepted=runner.metadata["references_accepted"], stopped=stopped)
    save(protocol.execution / "evaluations/automatic.json", automatic)
    by_id = {r["call_id"]: r for r in records}
    rows, all_samples = [], []
    for call in protocol.calls:
        cid = call["call_id"]
        if cid not in by_id:
            rows.append({"call_id": cid, "attempted": False, "mode": call["mode"],
                         "expected": call["reference_labels_reviewer_only"], "unobserved": True})
            continue
        record = by_id[cid]; pipeline = record["pipeline"]; op = pipeline["operational"]
        raw = op.get("response", {}).get("message", {}).get("content", "")
        parsed = None; valid_json = schema_valid = False
        try:
            parsed = strict_json(raw); valid_json = True
            ModelReport.model_validate_json(json.dumps(parsed), strict=True); schema_valid = True
        except (ValueError, TypeError):
            pass
        claims = parsed.get("behaviors") if isinstance(parsed, dict) else None
        raw_labels = [f.get("behavior_id") for f in claims if isinstance(f, dict)] if isinstance(claims, list) else None
        actual_request = op["request"]
        assert sha(canonical(actual_request)) == call["request_sha256_canonical"]
        user = strict_json(actual_request["messages"][1]["content"])
        assert set(user) == ({"original", "deterministic_recovery"} if call["mode"] == "C" else {"original"})
        resources = op.get("resources", {})
        all_samples.extend(resources.get("samples", []))
        row = {"call_id": cid, "attempted": True, "mode": call["mode"], "run_id": pipeline["run_id"],
            "expected": call["reference_labels_reviewer_only"], "raw_unvalidated_labels": raw_labels,
            "accepted_labels": [f["behavior_id"] for f in pipeline["llm"]["behaviors"]] if pipeline["llm"] else None,
            "status": pipeline["status"], "valid_JSON": valid_json, "schema_and_coherence_valid": schema_valid,
            "usable": pipeline["llm"] is not None, "errors": pipeline["errors"],
            "seconds": op.get("inference_seconds"), "metrics": op.get("metrics"),
            "raw_token_counts": {k: op.get("response", {}).get(k) for k in ("prompt_eval_count", "eval_count")},
            "truncated": op.get("truncated"), "resources": {k:v for k,v in resources.items() if k != "samples"},
            "source_ids_actually_sent": ["original"] + [t["source_id"] for t in user.get("deterministic_recovery", {}).get("verified_texts", [])],
            "evidence": pipeline.get("evidence", []), "result_sha256": digest(protocol.execution / "results" / (cid + ".json")),
            "risk": parsed.get("risk_label") if isinstance(parsed, dict) else None,
            "uncertainty": parsed.get("uncertainty") if isinstance(parsed, dict) else None,
            "injection": parsed.get("prompt_injection") if isinstance(parsed, dict) else None,
            "model_recovered_content_unverified": parsed.get("recovered_content") if isinstance(parsed, dict) else None,
            "raw_model_claims_are_not_accepted_labels_if_report_rejected": True,
            "human_output_adjudication": "pending"}
        rows.append(row)
        content_path = protocol.execution / "raw_model_content" / (cid + ".json")
        content_path.parent.mkdir(parents=True, exist_ok=True)
        with content_path.open("xb") as stream: stream.write(raw.encode("utf-8"))
        packet = "# " + cid + " — revisión personal pendiente\n\n"
        packet += "Modo: " + call["mode"] + ". Referencia aceptada: " + json.dumps(call["reference_labels_reviewer_only"]) + ".\n\n"
        packet += "Resultado SHA-256: `" + row["result_sha256"] + "`. Run ID: `" + row["run_id"] + "`.\n\n"
        packet += "## Original exacto (datos, no ejecutar)\n\n" + fenced(pipeline["original"], "powershell") + "\n\n"
        if call["mode"] == "C":
            packet += "## Recuperación realmente enviada y sus raíces\n\n" + fenced(json.dumps(user["deterministic_recovery"], ensure_ascii=False, indent=2), "json") + "\n\n"
        packet += "## Respuesta cruda del modelo\n\n" + fenced(raw, "json") + "\n\n"
        packet += "## Validación automática (no adjudicación semántica humana)\n\n" + fenced(json.dumps(row, ensure_ascii=False, indent=2), "json") + "\n"
        target = protocol.execution / "review_packets" / (cid + ".md")
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("x", encoding="utf-8", newline="\n") as stream: stream.write(packet)
    def tree(sample, field):
        return sum(p.get(field, 0) for p in sample.get("processes", []) if p.get("is_ollama_runtime"))
    resources = {"sample_count": len(all_samples),
        "minimum_RAM_bytes": min((s["available_bytes"] for s in all_samples), default=None),
        "minimum_commit_available_bytes": min((s["commit_available_bytes"] for s in all_samples), default=None),
        "peak_Ollama_tree_private_bytes": max((tree(s, "private") for s in all_samples), default=None),
        "peak_Ollama_tree_working_set_bytes": max((tree(s, "working_set") for s in all_samples), default=None),
        "resource_margin_violations": sum(bool(r.get("resources", {}).get("margin_violated")) for r in rows),
        "total_inference_seconds": sum(r.get("seconds") or 0 for r in rows),
        "process_names": sorted({p["name"] for s in all_samples for p in s.get("processes", []) if p.get("is_ollama_runtime")})}
    save(protocol.execution / "evaluations/results_inventory.json", {"at": now(), "calls": rows, "resources": resources,
        "model_requests_generated_by_this_reporter": 0, "human_output_reviews_created": 0,
        "automatic_evaluator_decision": automatic["decision"]})
    print(json.dumps({"result_count": len(records), "usable": automatic["coverage"]["usable"],
        "exact": automatic["exact_sets"], "micro": automatic["micro_system"], "decision": automatic["decision"]}))


if __name__ == "__main__":
    collect()

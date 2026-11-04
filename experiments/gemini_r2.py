"""One-shot, sequential generation controller for the already frozen ten-case r2 plan."""
from __future__ import annotations

import argparse
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import time

from experiments.gemini_viability import ROOT, OUT as INITIAL, write
from experiments.gemini_metadata_retry import DIAGNOSTIC, prospective_plan
from app.schemas.pipeline import ModelReport
from app.services.deobfuscation.engine import deobfuscate
from app.services.llm.gemini import FreeTierConfirmation, GeminiAdapter, GeminiSettings, fail
from app.services.llm.gemini_budget import RequestBudget
from app.services.llm.gemini_credentials import read_api_key
from app.services.pipelines.context import build_context, canonical, sha
from app.services.pipelines.provider import response_schema
from app.services.pipelines.service import AnalysisService
from app.services.pipelines.validation import strict_json

OUTPUT = ROOT / "artifacts/gemini_r2"
PLAN = DIAGNOSTIC / "plan_r2.json"
ORDER = ["G03_B", "G03_C", "G06_B", "G06_C", "G01_B", "G09_B", "G04_B", "G07_B", "G08_B", "G05_B"]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def context_for(case):
    script = case["script"]
    return build_context(script, deobfuscate(script) if case["configuration"] == "C" else None)


def input_bound(context):
    return sum(len(m["content"].encode("utf-8")) for m in context.messages) + len(canonical(response_schema()).encode("utf-8")) + 512


def prepare(quota_path):
    quota = FreeTierConfirmation(**load(quota_path))
    quota.check("gemini-3.8-flash")
    if (quota.rpm, quota.tpm, quota.rpd, quota.remaining_rpd) != (5, 250000, 20, 20):
        fail("gemini_owner_quota_mismatch")
    plan = load(PLAN)
    if plan != prospective_plan() or [c["id"] + "_" + c["configuration"] for c in plan["cases"]] != ORDER:
        fail("gemini_prospective_plan_mismatch")
    delivery = load(DIAGNOSTIC / "metadata_02_delivery.json")
    if any(digest(ROOT / p) != h for p, h in delivery["files"].items()):
        fail("gemini_historical_integrity_mismatch")
    previous = load(DIAGNOSTIC / "delivery_inventory.json")
    if any(digest(ROOT / p) != h for p, h in previous["sha256"].items() if not p.startswith("docs/")):
        fail("gemini_code_integrity_mismatch")
    budget = RequestBudget(INITIAL / "requests.jsonl")
    entries = budget.entries()
    if len(entries) != 2 or any(e["kind"] != "models.list" for e in entries):
        fail("gemini_generation_start_requires_two_metadata_only")
    models = load(DIAGNOSTIC / "metadata_retry_02.json")
    if models["authentication"] != "accepted" or not models["exact_model_listed"]:
        fail("gemini_preflight_required")
    if not read_api_key():
        fail("credential_missing")
    contexts = []
    for case in plan["cases"]:
        context = context_for(case)
        if context.prompt_sha256 != plan["policy_sha256"] or sha(canonical(response_schema())) != plan["schema_sha256"]:
            fail("gemini_contract_changed")
        if case["configuration"] == "C" and len(context.sources) < 2:
            fail("gemini_nonempty_recovery_required")
        if input_bound(context) + 4096 > quota.tpm:
            fail("gemini_known_token_quota_insufficient")
        contexts.append({"case": case["id"] + "_" + case["configuration"],
            "original_sha256": sha(case["script"]), "context_sha256": context.context_sha256,
            "prompt_sha256": context.prompt_sha256, "messages": context.messages, "sources": context.sources,
            "input_upper_bound": input_bound(context), "total_token_reserve": input_bound(context) + 4096})
    paths = list((ROOT / "backend/app").rglob("*.py")) + list((ROOT / "backend/app").rglob("*.md"))
    paths += [ROOT / p for p in ["experiments/gemini_cases.py", "experiments/gemini_viability.py",
              "experiments/gemini_metadata_retry.py", "experiments/gemini_r2.py"]]
    protected = set()
    for folder in ["datasets", "experiments/prompts", "experiments/configurations", "experiments/reviews",
                   "experiments/results/pilot", "experiments/pilot_v2", "experiments/pilot_v2_runtime",
                   "artifacts/gemini_viability", "artifacts/gemini_transport_diagnostic"]:
        protected.update(p for p in (ROOT / folder).rglob("*") if p.is_file() and "__pycache__" not in p.parts)
    protected.update(ROOT / p for p in [".git/index", ".git/HEAD"] if (ROOT / p).is_file())
    OUTPUT.mkdir(exist_ok=True)
    write(OUTPUT / "integrity_before.json", {p.relative_to(ROOT).as_posix(): digest(p) for p in sorted(protected)})
    write(OUTPUT / "binding.json", {"plan_sha256": digest(PLAN), "initial_ledger_sha256": digest(budget.path),
        "initial_ledger_entries": entries, "runtime_hashes": {p.relative_to(ROOT).as_posix(): digest(p) for p in paths},
        "quota_sha256": digest(quota_path), "settings": asdict(GeminiSettings()), "contexts": contexts,
        "policy": "sequential_21s_no_retry_stop_operational_or_safety_continue_structural_rejection",
        "minimum_dispatch_interval_seconds": 21, "immutable_after_first_dispatch": True})
    write(OUTPUT / "generation_authorization.json", {"authorized": True, "source": "explicit_owner_chat_authorization",
        "recorded_at": datetime.now(timezone.utc).isoformat(), "model": "gemini-3.8-flash", "maximum_generations": 10,
        "quota_file": str(quota_path.relative_to(ROOT)), "project": "Default Gemini Project",
        "billing_enabled": False, "quota_verified_by": "owner_ai_studio_current_chat_report",
        "panel_usage_reported": 0, "panel_usage_scope": "owner_selected_period_not_independently_queried",
        "binding_sha256": digest(OUTPUT / "binding.json"), "plan_sha256": digest(PLAN),
        "no_metadata_queries": True, "no_migration": True, "phase4_started": False})


def frozen_check(binding):
    if digest(PLAN) != binding["plan_sha256"] or any(digest(ROOT / p) != h for p, h in binding["runtime_hashes"].items()):
        fail("gemini_frozen_runtime_changed")


def wait_for_quota(history, reserve, quota, now=time.time, sleep=time.sleep):
    while True:
        current = now()
        recent = [(t, n) for t, n in history if current-t < 61]
        delay = max(0, history[-1][0] + 21-current) if history else 0
        if len(recent) >= quota.rpm or sum(n for _, n in recent)+reserve > quota.tpm:
            delay = max(delay, recent[0][0]+61-current)
        if delay <= 0:
            return
        sleep(min(delay, 30))


def finish_reasons(result):
    return [c.get("finish_reason") for c in result.operational.get("response", {}).get("candidates", [])]


def must_stop(result):
    if result.status in {"completed", "partial"}:
        return False
    codes = {e.code for e in result.errors}
    if codes <= {"invalid_response", "empty_response"} and result.operational.get("http_status") == 200:
        return False  # retain the raw rejection, then the next predetermined case; never retry it
    if codes == {"gemini_incomplete_or_blocked"} and finish_reasons(result) == ["MAX_TOKENS"]:
        return False  # a truncation is a quality observation, not a reason to replace the case
    return True


def assess(result, case):
    operational = result.operational
    response = operational.get("response", {})
    text = "".join(p.get("text", "") for c in response.get("candidates", [])
                   for p in c.get("content", {}).get("parts", []) if not p.get("thought"))
    value, valid_json, schema_valid = None, False, False
    try:
        value = strict_json(text)
        valid_json = True
        ModelReport.model_validate_json(json.dumps(value), strict=True)
        schema_valid = True
    except (ValueError, TypeError):
        pass
    labels = [f.get("behavior_id") for f in value.get("behaviors", []) if isinstance(f, dict)] if isinstance(value, dict) and isinstance(value.get("behaviors"), list) else None
    labels = sorted(labels) if labels is not None and all(isinstance(v, str) for v in labels) else None
    context = context_for(case)
    citations = []
    if isinstance(value, dict):
        for finding in value.get("behaviors", []) if isinstance(value.get("behaviors"), list) else []:
            if not isinstance(finding, dict):
                continue
            for citation in finding.get("evidence", []) if isinstance(finding.get("evidence"), list) else []:
                if not isinstance(citation, dict):
                    continue
                source, snippet = citation.get("source_id"), citation.get("snippet")
                original = context.sources.get(source) if isinstance(source, str) else None
                literal = bool(isinstance(snippet, str) and snippet.strip() and original is not None and snippet in original)
                citations.append({"behavior_id": finding.get("behavior_id"), "source_id": source,
                    "literal": literal, "unique": literal and original.count(snippet) == 1,
                    "verified_recovered_source": source in context.sources and source != "original" if isinstance(source, str) else False})
    expected = sorted(case["expected"])
    return {"id": case["id"], "configuration": case["configuration"], "status": result.status,
        "run_id": result.run_id, "http_attempt": operational.get("http_attempt"), "http_status": operational.get("http_status"),
        "valid_json": valid_json, "schema_valid": schema_valid, "application_accepted": result.llm is not None,
        "expected_labels": expected, "raw_observed_labels": labels, "raw_labels_are_unvalidated_claims": result.llm is None,
        "exact_labels": labels == expected, "false_positives": sorted(set(labels)-set(expected)) if labels is not None else None,
        "false_negatives": sorted(set(expected)-set(labels)) if labels is not None else None,
        "citations": citations, "nonempty_recovery": len(context.sources)>1 if case["configuration"] == "C" else None,
        "accepted_citing_recovery": bool(result.llm and any(e.provenance == "deobfuscator_recovered" for e in result.evidence)) if case["configuration"] == "C" else None,
        "finish_reasons": finish_reasons(result), "response_id": response.get("response_id"),
        "model_version": operational.get("model_version"), "usage": operational.get("usage"),
        "seconds": operational.get("inference_seconds"), "errors": [e.model_dump() for e in result.errors],
        "semantic_review": "pending_agent_review_not_independent_human_adjudication"}


def run():
    authorization = load(OUTPUT / "generation_authorization.json")
    binding = load(OUTPUT / "binding.json")
    frozen_check(binding)
    if authorization.get("authorized") is not True or authorization["binding_sha256"] != digest(OUTPUT / "binding.json"):
        fail("gemini_generation_not_authorized")
    quota_path = ROOT / authorization["quota_file"]
    quota = FreeTierConfirmation(**load(quota_path))
    quota.check("gemini-3.8-flash")
    if digest(quota_path) != binding["quota_sha256"]:
        fail("gemini_owner_quota_mismatch")
    budget = RequestBudget(INITIAL / "requests.jsonl")
    if len(budget.entries()) != 2 or digest(budget.path) != binding["initial_ledger_sha256"]:
        fail("gemini_generation_start_requires_two_metadata_only")
    plan = load(PLAN)
    write(OUTPUT / "execution_intent.json", {"started_at": datetime.now(timezone.utc).isoformat(),
          "binding_sha256": digest(OUTPUT / "binding.json"), "no_automatic_restart_or_replay": True})
    client = GeminiAdapter(budget=budget, grant=quota, generation=GeminiSettings(),
                          allowed_original_hashes={sha(c["script"]) for c in plan["cases"]})
    service = AnalysisService(adapter=client)
    rows, history, stop = [], [], None
    try:
        for index, case in enumerate(plan["cases"]):
            frozen_check(binding)
            quota.check("gemini-3.8-flash")
            reserve = binding["contexts"][index]["total_token_reserve"]
            wait_for_quota(history, reserve, quota)
            if len(budget.entries()) != 2+index:
                fail("gemini_unexpected_external_dispatch")
            context = context_for(case)
            if context.context_sha256 != binding["contexts"][index]["context_sha256"]:
                fail("gemini_frozen_context_changed")
            dispatched_at = time.time()
            result = service.analyze(case["script"], case["configuration"])
            if result.operational.get("inference_dispatched"):
                history.append((dispatched_at, reserve))
            write(OUTPUT / (ORDER[index]+".json"), result.model_dump(mode="json"))
            row = assess(result, case)
            rows.append(row)
            write(OUTPUT / (ORDER[index]+".assessment.json"), row)
            print(json.dumps({k: row[k] for k in ("id", "configuration", "status", "http_status", "exact_labels", "application_accepted")}), flush=True)
            if must_stop(result):
                stop = [e.code for e in result.errors]
                break
        write(OUTPUT / "summary.json", {"results": rows, "planned_generations": 10,
            "generations_dispatched": sum(e["kind"] == "generateContent" for e in budget.entries()),
            "requests_reserved": len(budget.entries()), "automatic_retries": 0, "stop_reason": stop,
            "not_executed": ORDER[len(rows):], "phase4_started": False, "scientific_selection_approved": False,
            "quota_remaining_provider": "not_independently_queried", "quota_owner_snapshot": asdict(quota)})
    finally:
        client.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["prepare", "run"])
    parser.add_argument("--quota", type=Path)
    args = parser.parse_args()
    try:
        if args.action == "prepare":
            if args.quota is None:
                fail("gemini_free_tier_unconfirmed")
            prepare(args.quota.resolve())
        else:
            run()
        return 0
    except Exception as exc:
        print(json.dumps({"error_type": getattr(exc, "code", "gemini_r2_local_error")}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

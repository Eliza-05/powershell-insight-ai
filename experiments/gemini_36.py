"""Four new 3.6 calls only, one-shot, same global ledger; never resume/replay 3.8."""
from dataclasses import asdict
from datetime import datetime, timezone
import argparse
import json
from pathlib import Path
import time

from experiments.gemini_r2 import ROOT, INITIAL, context_for, input_bound, digest, load, wait_for_quota, must_stop, assess
from experiments.gemini_viability import write
from app.services.llm.gemini import FreeTierConfirmation, fail
from app.services.llm.gemini36 import MODEL36, Gemini36Adapter, Gemini36Settings
from app.services.llm.gemini_budget import RequestBudget
from app.services.llm.gemini_credentials import read_api_key
from app.services.pipelines.context import canonical, sha
from app.services.pipelines.provider import response_schema
from app.services.pipelines.service import AnalysisService

OUTPUT = ROOT / "artifacts/gemini_36"
DIAGNOSTIC = ROOT / "artifacts/gemini_transport_diagnostic"
R2_PLAN = DIAGNOSTIC / "plan_r2.json"
ORDER = ["G03_B", "G03_C", "G06_B", "G06_C"]


def new_plan():
    cases = load(R2_PLAN)["cases"][:4]
    return {"experiment": "gemini36-v1", "model": MODEL36, "historical_r2_sha256": digest(R2_PLAN),
        "cases": cases, "order": ORDER, "maximum_new_generations": 4, "initial_global_reservations": 3,
        "maximum_global_reservations_after_plan": 7, "global_limit": 12, "metadata_queries": 0,
        "settings": asdict(Gemini36Settings()), "minimum_dispatch_interval_seconds": 21,
        "policy_sha256": context_for(cases[0]).prompt_sha256, "schema_sha256": sha(canonical(response_schema())),
        "omitted_request_parameters": ["temperature", "top_p", "top_k", "seed", "candidate_count", "frequency_penalty", "presence_penalty"],
        "sampling_effective_values": "unknown_not_requested", "tools": [], "automatic_retries": 0,
        "continuation_policy": "stop_operational_or_safety_failure_preserve_structural_and_semantic_rejections",
        "independent_scientific_selection": False, "phase4_started": False}


def prepare():
    budget = RequestBudget(INITIAL / "requests.jsonl")
    entries = budget.entries()
    if len(entries) != 3 or [e["kind"] for e in entries] != ["models.list", "models.list", "generateContent"]:
        fail("gemini36_start_requires_three_historical_attempts")
    saved = load(DIAGNOSTIC / "metadata_retry_02.json")
    available = [m for m in saved["models"] if m["name"] == "models/" + MODEL36 and "generateContent" in (m["supported_actions"] or [])]
    if saved["authentication"] != "accepted" or len(available) != 1:
        fail("gemini36_not_in_saved_authenticated_listing")
    if not read_api_key():
        fail("credential_missing")
    plan = new_plan()
    if [c["id"] + "_" + c["configuration"] for c in plan["cases"]] != ORDER:
        fail("gemini36_plan_mismatch")
    now = datetime.now(timezone.utc).isoformat()
    quota = FreeTierConfirmation(MODEL36, now, "owner_ai_studio_confirmation", rpm=5, tpm=250000, rpd=20)
    contexts = []
    for case in plan["cases"]:
        ctx = context_for(case)
        if case["configuration"] == "C" and len(ctx.sources) < 2:
            fail("gemini36_recovery_missing")
        contexts.append({"case": case["id"]+"_"+case["configuration"], "messages": ctx.messages,
            "sources": ctx.sources, "context_sha256": ctx.context_sha256, "prompt_sha256": ctx.prompt_sha256,
            "input_token_upper_bound": input_bound(ctx), "total_token_reserve": input_bound(ctx)+8192})
    paths = list((ROOT/"backend/app").rglob("*.py")) + list((ROOT/"backend/app").rglob("*.md"))
    paths += [ROOT/p for p in ["experiments/gemini_36.py", "experiments/gemini_r2.py", "experiments/gemini_cases.py",
                               "experiments/gemini_viability.py", "experiments/gemini_metadata_retry.py"]]
    write(OUTPUT/"plan_v1.json", plan)
    write(OUTPUT/"quota_confirmation.json", asdict(quota))
    write(OUTPUT/"binding.json", {"plan_sha256": digest(OUTPUT/"plan_v1.json"), "initial_ledger_sha256": digest(budget.path),
        "initial_ledger_entries": entries, "saved_listing_sha256": digest(DIAGNOSTIC/"metadata_retry_02.json"),
        "saved_model_metadata": available[0], "contexts": contexts, "runtime_hashes": {p.relative_to(ROOT).as_posix(): digest(p) for p in paths},
        "quota_sha256": digest(OUTPUT/"quota_confirmation.json")})
    write(OUTPUT/"authorization.json", {"authorized": True, "recorded_at_utc": now,
        "source": "explicit_owner_chat_authorization_gemini36", "model": MODEL36, "maximum_new_generations": 4,
        "binding_sha256": digest(OUTPUT/"binding.json"), "project": "Default Gemini Project", "tier": "Free",
        "billing_enabled": False, "rpm":5,"tpm":250000,"rpd":20,"remaining_rpd":"not_reported_or_queried",
        "no_metadata_queries": True, "historical_38_attempt_not_replaced": True})


def frozen_check(binding):
    if digest(OUTPUT/"plan_v1.json") != binding["plan_sha256"] or any(digest(ROOT/p) != h for p,h in binding["runtime_hashes"].items()):
        fail("gemini36_frozen_runtime_changed")


def run():
    binding = load(OUTPUT/"binding.json")
    auth = load(OUTPUT/"authorization.json")
    frozen_check(binding)
    if auth.get("authorized") is not True or auth["model"] != MODEL36 or auth["maximum_new_generations"] != 4 or auth["binding_sha256"] != digest(OUTPUT/"binding.json"):
        fail("gemini36_not_authorized")
    quota_path = OUTPUT/"quota_confirmation.json"
    quota = FreeTierConfirmation(**load(quota_path))
    quota.check(MODEL36)
    if digest(quota_path) != binding["quota_sha256"]:
        fail("gemini36_quota_changed")
    budget = RequestBudget(INITIAL/"requests.jsonl")
    if len(budget.entries()) != 3 or digest(budget.path) != binding["initial_ledger_sha256"]:
        fail("gemini36_start_requires_three_historical_attempts")
    plan = load(OUTPUT/"plan_v1.json")
    write(OUTPUT/"execution_intent.json", {"started_at": datetime.now(timezone.utc).isoformat(),
        "model": MODEL36, "binding_sha256": digest(OUTPUT/"binding.json"), "no_replay_or_automatic_restart": True})
    client = Gemini36Adapter(budget=budget, grant=quota, allowed_original_hashes={sha(c["script"]) for c in plan["cases"]})
    service = AnalysisService(adapter=client)
    history, rows, stop = [], [], None
    try:
        for index, case in enumerate(plan["cases"]):
            frozen_check(binding)
            quota.check(MODEL36)
            wait_for_quota(history, binding["contexts"][index]["total_token_reserve"], quota)
            if len(budget.entries()) != 3+index or len(budget.entries()) >= 7:
                fail("gemini36_budget_or_external_dispatch")
            ctx = context_for(case)
            if ctx.context_sha256 != binding["contexts"][index]["context_sha256"]:
                fail("gemini36_context_changed")
            start = time.time()
            result = service.analyze(case["script"], case["configuration"])
            if result.operational.get("inference_dispatched"):
                history.append((start, binding["contexts"][index]["total_token_reserve"]))
            write(OUTPUT/(ORDER[index]+".json"), result.model_dump(mode="json"))
            row = {**assess(result, case), "requested_model": MODEL36}
            rows.append(row)
            write(OUTPUT/(ORDER[index]+".assessment.json"), row)
            print(json.dumps({k:row[k] for k in ["id","configuration","status","http_status","application_accepted","exact_labels"]}), flush=True)
            if must_stop(result):
                stop = [e.code for e in result.errors]
                break
        write(OUTPUT/"summary.json", {"experiment":"gemini36-v1","model":MODEL36,"planned_generations":4,
            "new_generations_dispatched":len(budget.entries())-3,"requests_reserved_global":len(budget.entries()),
            "stop_reason":stop,"results":rows,"not_executed":ORDER[len(rows):],"automatic_retries":0,
            "provider_remaining_quota":"unknown_not_queried","scientific_selection_approved":False,"phase4_started":False})
    finally:
        client.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action",choices=["prepare","run"])
    args=parser.parse_args()
    try:
        prepare() if args.action=="prepare" else run()
        return 0
    except Exception as exc:
        print(json.dumps({"error_type":getattr(exc,"code","gemini36_local_error")}))
        return 2


if __name__=="__main__":
    raise SystemExit(main())

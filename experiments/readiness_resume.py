"""Prospective v4 controller: one new reasoning/provenance comparison within 24.

Preserves the v3 runner, source locks, results and shared authorization ledger.
Only the never-dispatched slot 18 changes; no failed inference is repeated.
"""
from copy import deepcopy
import hashlib
import json
from pathlib import Path

from experiments.model_readiness import diagnostics as base

OUT = base.ROOT / "artifacts/pre_phase4/diagnostics_v4"


def amend_plan(original, spent):
    plan = deepcopy(original)
    removed = plan["calls"][17]
    if removed["id"] in spent:
        raise ValueError("Cannot replace an already-dispatched slot")
    call = deepcopy(original["calls"][1])  # same C source/policy as P1, now P3 bundle
    call.update(id="18-C-recovered-P3", profile="P3")
    call["payload"]["think"] = original["profiles"]["P3"]["think"]
    call["payload"]["options"] = deepcopy(original["profiles"]["P3"]["options"])
    call["request_sha256"] = base.sha(base.canonical(call["payload"]))
    plan["calls"][17] = call
    plan["version"] = "readiness-development-v4"
    plan["prospective_amendment"] = {
        "basis": "user continuation prioritizes reasoning, semantic quality and provenance",
        "replaced_never_dispatched_id": removed["id"], "replaced_request_sha256": removed["request_sha256"],
        "replacement_id": call["id"],
        "reason": "test recovered-source provenance with P3; extended output reserve already tested by P3 and B05 has a separate recon case",
        "other_23_requests_unchanged": True, "total_cap_unchanged": 24,
        "registered_before_any_P3_output": not any("-P3" in item for item in spent),
        "historical_results_changed": False,
        "comparison_limit": "P3 differs in thinking, temperature and output budget together; not an isolated causal estimate of thinking"}
    return plan


def prepare():
    original = base.prepare()  # verifies the complete v3 source/prompt/contract lock
    plan = amend_plan(original, base.spent_ids())
    # The amendment's registered-before flag is fixed by its first durable creation.
    path = OUT / "plan.json"
    if path.exists():
        stored = json.loads(path.read_text(encoding="utf-8"))
        plan["prospective_amendment"]["registered_before_any_P3_output"] = stored["prospective_amendment"]["registered_before_any_P3_output"]
    plan["base_plan_sha256"] = hashlib.sha256((base.OUT / "plan.json").read_bytes()).hexdigest()
    plan["continuation_controller_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    if path.exists():
        if stored != plan:
            raise ValueError("Prospective plan/controller changed; cannot overwrite")
    else:
        base.save(path, plan)
    return plan


def run():
    plan = prepare()
    previous_out, previous_prepare = base.OUT, base.prepare
    try:
        base.OUT = OUT
        base.prepare = lambda: plan
        return base.run()
    finally:
        base.OUT, base.prepare = previous_out, previous_prepare


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["prepare", "run"])
    args = parser.parse_args()
    print(json.dumps(run() if args.command == "run" else {"version": prepare()["version"], "cap": 24}))

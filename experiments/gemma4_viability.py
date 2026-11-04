"""Continue the original Gemma viability experiment; fixed root, eight intents total.

Commands: prepare (no inference), next (one case), review (AI-assisted checkpoint).
No selection data, sample execution, cloud client, model pull or prompt tuning.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path

from app.services.deobfuscation.engine import deobfuscate
from app.services.llm.gemma4 import DIGEST, MODEL, Gemma4Adapter, Gemma4Settings
from app.services.pipelines.context import build_context, canonical, sha
from app.services.pipelines.provider import response_schema
from app.services.pipelines.resources import InferenceGate, OperationalFailure
from app.services.pipelines.service import AnalysisService
from experiments.gemini_cases import cases
from experiments.model_readiness.diagnostics import build_plan as readiness_plan
from experiments.pilot_v2_runtime.resources import snapshot

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/local_model_gemma4_viability"
CONT = OUT / "continuation_01"
AUTH_SHA = "98fe1c9c791448259c4bb613573453defdaa82a25a05cd7cbf7959de4e6706c8"
CAP = 8


def now():
    return datetime.now(timezone.utc).isoformat()


def save(path, value):
    with Path(path).open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())


def file_sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def planned_cases():
    old = {c["case"]: c["script"] for c in readiness_plan()["calls"]}
    g = {c["id"]: c for c in cases()}
    # Exact order and coverage from the previous report, no held-out imports.
    return [
        ("01-credential-control", "B", old["credential-control"], [], False),
        ("02-functional-iex", "B", g["G02"]["script"], ["B02"], False),
        ("03-stored-block", "B", g["G04"]["script"], [], False),
        ("04-download-invoke", "B", old["download-invoke"], ["B01", "B02"], False),
        ("05-stored-credential", "B", g["G08"]["script"], ["B07"], False),
        ("06-unknown-command", "B", "& $unknown", None, True),
        ("07-recovered-display", "C", g["G03"]["script"], [], False),
        ("08-recovered-connectivity", "C", g["G06"]["script"], ["B05", "B06"], False),
    ]


def payload_for(context):
    cfg = Gemma4Settings()
    return {"model": MODEL, "messages": context.messages, "format": response_schema(),
            "stream": False, "truncate": False, "think": cfg.think,
            "keep_alive": cfg.keep_alive, "options": cfg.options.model_dump()}


def prepare():
    assert file_sha(CONT / "authorization.txt") == AUTH_SHA
    assert json.loads((OUT / "decision.json").read_text(encoding="utf-8"))["inference_dispatches"] == 0
    if (OUT / "inference_ledger.jsonl").exists():
        raise ValueError("Cannot replace a campaign with an existing ledger")
    calls = []
    for case_id, mode, script, expected, unknown in planned_cases():
        deob = deobfuscate(script) if mode == "C" else None
        context = build_context(script, deob)
        if mode == "C":
            assert any(k != "original" and v for k, v in context.sources.items())
        payload = payload_for(context)
        assert sum(len(m["content"].encode("utf-8")) for m in context.messages) + 512 + 2048 <= 8192
        calls.append({"case_id": case_id, "mode": mode, "script": script,
            "reference_labels_reviewer_only": expected, "unknown_command": unknown,
            "reference_status": "existing_development_reference_not_new_human_adjudication",
            "sources": context.sources, "recovery": deob.model_dump(mode="json") if deob else None,
            "payload": payload, "request_sha256": sha(canonical(payload)),
            "prompt_sha256": context.prompt_sha256, "schema_sha256": sha(canonical(response_schema()))})
    paths = list((ROOT / "backend/app").rglob("*.py"))
    paths += [ROOT / "backend/app/services/pipelines/policy_v1.md", Path(__file__).resolve(),
              ROOT / "experiments/gemini_cases.py", ROOT / "experiments/model_readiness/diagnostics.py",
              ROOT / "experiments/pilot_v2_runtime/resources.py", CONT / "authorization.txt"]
    source_locks = {p.relative_to(ROOT).as_posix(): file_sha(p) for p in sorted(set(paths))}
    plan = {"experiment": "local_model_gemma4_viability", "prepared_at": now(), "cap": CAP,
        "continues_prior_zero_attempt_experiment": True, "model": MODEL, "digest": DIGEST,
        "authorization_sha256": AUTH_SHA, "calls": calls, "source_locks": source_locks,
        "gate": {"all_eight_usable": True, "exact_determinable_labels": True,
            "unknown_abstention_without_invented_inner_behavior": True,
            "critical_semantic_errors": 0, "minimum_C_with_correct_recovered_citation": 1,
            "minimum_RAM_and_commit_bytes": 2 * 1024 ** 3,
            "strict_semantic_review_is_AI_assisted_not_human": True},
        "stopping_rule": "Stop on first operational/JSON/provenance/essential semantic failure; no retries or adjustments",
        "review_requirement": "Each completed case needs a separate AI-assisted checkpoint before the next case"}
    save(OUT / "plan_frozen.json", plan)
    save(OUT / "authorization.json", {"authorization_sha256": AUTH_SHA, "budget": CAP,
        "plan_sha256": sha(canonical(plan)), "authorized_at_recorded": now(),
        "source": "explicit_owner_resume", "ledger": "inference_ledger.jsonl"})
    print(json.dumps({"prepared": len(calls), "C_sources": {c["case_id"]: list(c["sources"]) for c in calls if c["mode"] == "C"},
                      "plan_sha256": sha(canonical(plan))}))


def locked_plan():
    plan = json.loads((OUT / "plan_frozen.json").read_text(encoding="utf-8"))
    auth = json.loads((OUT / "authorization.json").read_text(encoding="utf-8"))
    assert plan["cap"] == CAP and len(plan["calls"]) == CAP
    assert auth["authorization_sha256"] == AUTH_SHA == file_sha(CONT / "authorization.txt")
    assert auth["plan_sha256"] == sha(canonical(plan))
    for name, expected in plan["source_locks"].items():
        assert file_sha(ROOT / name) == expected, "Frozen source changed: " + name
    return plan


def entries():
    path = OUT / "inference_ledger.jsonl"
    rows = [json.loads(s) for s in path.read_text(encoding="utf-8").splitlines()] if path.exists() else []
    if len(rows) > CAP or any(r["attempt"] != i + 1 for i, r in enumerate(rows)):
        raise ValueError("Corrupt campaign ledger")
    return rows


def reserve(payload, case):
    # Called under the inherited application-wide OS gate. No independent budget root.
    plan = locked_plan()
    rows = entries()
    if len(rows) >= CAP:
        raise OperationalFailure("budget_exhausted", "Eight-attempt budget exhausted")
    if (OUT / "STOP.json").exists():
        raise OperationalFailure("campaign_stopped", "Campaign already stopped")
    expected = plan["calls"][len(rows)]
    if expected["case_id"] != case["case_id"] or sha(canonical(payload)) != expected["request_sha256"]:
        raise OperationalFailure("request_not_frozen", "Dispatch differs from fixed schedule")
    row = {"attempt": len(rows) + 1, "case_id": case["case_id"],
           "request_sha256": expected["request_sha256"], "reserved_before_HTTP_at": now()}
    with (OUT / "inference_ledger.jsonl").open("a", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(row) + "\n")
        stream.flush()
        os.fsync(stream.fileno())
    return row


def run_next():
    plan = locked_plan()
    rows = entries()
    if (OUT / "STOP.json").exists() or len(rows) >= CAP:
        raise ValueError("Stopped or exhausted; no extra dispatch")
    if rows:
        review_path = CONT / (rows[-1]["case_id"] + ".review.json")
        if not review_path.exists() or not json.loads(review_path.read_text(encoding="utf-8"))["continue"]:
            raise ValueError("Previous case requires assisted semantic review; no automatic progression")
    case = plan["calls"][len(rows)]
    result_path = CONT / (case["case_id"] + ".result.json")
    if result_path.exists():
        raise ValueError("Existing result cannot be replaced or retried")
    adapter = Gemma4Adapter(authorize_dispatch=lambda payload: reserve(payload, case), sampler=snapshot)
    result = AnalysisService(settings=adapter.settings, adapter=adapter).analyze(case["script"], case["mode"])
    data = result.model_dump(mode="json")
    save(result_path, data)
    predicted = [f["behavior_id"] for f in data["llm"]["behaviors"]] if data["llm"] else None
    expected = case["reference_labels_reviewer_only"]
    exact = set(predicted) == set(expected) if predicted is not None and expected is not None else None
    assessment = {"case_id": case["case_id"], "status": data["status"], "json_schema_provenance_accepted": data["llm"] is not None,
        "expected_labels": expected, "predicted_labels": predicted, "exact_set": exact,
        "false_positives": sorted(set(predicted) - set(expected)) if predicted is not None and expected is not None else None,
        "false_negatives": sorted(set(expected) - set(predicted)) if predicted is not None and expected is not None else None,
        "indeterminate_case_excluded_from_label_metrics": expected is None,
        "recovered_evidence_count": sum(e["provenance"] == "deobfuscator_recovered" for e in data["evidence"]),
        "semantic_support": "requires_AI_assisted_review", "human_adjudication": "not_performed",
        "result_sha256": file_sha(result_path)}
    save(CONT / (case["case_id"] + ".assessment.json"), assessment)
    if data["status"] not in {"completed", "partial"} or exact is False:
        save(OUT / "STOP.json", {"at": now(), "case_id": case["case_id"],
             "reason": "operational_or_contract_or_essential_label_failure", "assessment": assessment})
    print(json.dumps(assessment, ensure_ascii=False))


def review(case_id, passed, notes):
    locked_plan()
    rows = entries()
    assert rows and rows[-1]["case_id"] == case_id
    result_path = CONT / (case_id + ".result.json")
    value = {"case_id": case_id, "at": now(), "reviewer_type": "AI_assisted",
             "human_adjudication": False, "continue": passed, "notes": notes,
             "result_sha256": file_sha(result_path)}
    save(CONT / (case_id + ".review.json"), value)
    if not passed and not (OUT / "STOP.json").exists():
        save(OUT / "STOP.json", {"at": now(), "case_id": case_id, "reason": "essential_semantic_failure_AI_assisted", "review": value})
    print(json.dumps(value, ensure_ascii=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["prepare", "next", "review"])
    parser.add_argument("--case")
    parser.add_argument("--passed", action="store_true")
    parser.add_argument("--notes")
    args = parser.parse_args()
    if args.command == "prepare":
        prepare()
    elif args.command == "next":
        run_next()
    else:
        review(args.case, args.passed, args.notes)

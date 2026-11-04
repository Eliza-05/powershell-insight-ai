"""Opt-in diagnostic CLI. Only fixed synthetic cases; metadata also counts toward 12."""
from __future__ import annotations

import argparse
from dataclasses import asdict
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.services.deobfuscation.engine import deobfuscate
from app.services.llm.gemini import FreeTierConfirmation, GeminiAdapter, GeminiSettings, MODELS
from app.services.llm.gemini_budget import RequestBudget
from app.services.llm.gemini_credentials import read_api_key
from app.services.pipelines.context import build_context, canonical, sha
from app.services.pipelines.provider import response_schema
from app.services.pipelines.resources import OperationalFailure
from app.services.pipelines.service import AnalysisService
from app.services.pipelines.validation import strict_json
from experiments.gemini_cases import cases, schedule

OUT = ROOT / "artifacts/gemini_viability"
PLAN_FILE = "plan_r1.json"


def write(path, data):
    text = json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    if read_api_key() in text:
        raise OperationalFailure("gemini_credential_echo", "gemini_credential_echo", "gemini")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def plan():
    return {"experiment": "gemini-viability-v1", "revision": "r1", "purpose": "exploratory_development_not_selection",
            "http_request_limit": 12, "metadata_requests": 1, "inferences_planned": 11,
            "model_preference": list(MODELS), "cases": schedule(),
            "criteria": ["strict_json", "schema", "exact_labels", "multilabel", "literal_unique_evidence",
                         "source_provenance", "semantic_support_review", "no_inventions_review", "uncertainty",
                         "injection_resistance", "nonempty_C_recovery", "C_cites_recovery", "quota_and_tokens"],
            "policy_sha256": build_context("Write-Output 731").prompt_sha256,
            "schema_sha256": sha(canonical(response_schema())),
            "retry_policy": "none_including_errors", "tools": [], "samples_executed": False,
            "rate_policy": "one request per >=21 seconds; >=61 seconds if TPM unknown; stop on any API failure",
            "independent_review": False, "phase4_started": False}


def adapter(model=MODELS[0], grant=None):
    return GeminiAdapter(budget=RequestBudget(OUT / "requests.jsonl"), generation=GeminiSettings(model=model),
        allowed_original_hashes={sha(c["script"]) for c in cases()}, grant=grant)


def prepare():
    write(OUT / PLAN_FILE, plan())
    # A and C recovery preparation are local Python text analysis, never sample execution.
    local = []
    service = AnalysisService()
    for case in cases():
        result = service.analyze(case["script"], "A")
        ctx = build_context(case["script"], result.deobfuscation)
        local.append({"id": case["id"], "A": result.model_dump(mode="json"),
                      "verified_recoveries": {k: v for k, v in ctx.sources.items() if k != "original"}})
        if case.get("paired_c") and len(ctx.sources) < 2:
            raise ValueError("nonempty C recovery required")
    write(OUT / "local_preparation.json", local)


def preflight():
    client = adapter()
    try:
        result = client.list_models()
        write(OUT / "models.json", result)
        names = {m["name"] for m in result["models"] if "generateContent" in (m["supported_actions"] or [])}
        selected = next((m for m in MODELS if "models/" + m in names), None)
        decision = {"model": selected, "decided_before_inference": True,
                    "reason": "Prefer 3.8 Flash when listed; otherwise 2.5 Flash with documented free text input/output.",
                    "free_tier_project": "owner_confirmed_in_chat", "model_listing_is_not_quota_proof": True,
                    "pricing_source": "https://ai.google.dev/gemini-api/docs/pricing",
                    "requires_current_owner_free_tier_confirmation": True}
        write(OUT / "model_decision.json", decision)
        print(json.dumps({"authentication": result["authentication"], "model_count": len(names), "selected_model": selected,
                          "http_attempts": len(client.budget.entries()), "inferences": 0}))
    except Exception as exc:
        code = getattr(exc, "code", "gemini_preflight_error")
        write(OUT / "preflight_error.json", {"error_type": code, "http_attempts": len(client.budget.entries())})
        print(json.dumps({"error_type": code}))
        return 2
    finally:
        client.close()
    return 0


def evaluate(result, case):
    raw = result.operational.get("response", {})
    texts = [p.get("text", "") for c in raw.get("candidates", []) for p in c.get("content", {}).get("parts", []) if not p.get("thought")]
    json_valid = False
    try:
        strict_json("".join(texts))
        json_valid = bool(texts)
    except (ValueError, TypeError):
        pass
    labels = sorted(f.behavior_id.value for f in result.llm.behaviors) if result.llm else None
    recovery = bool(result.deobfuscation and any(t.deterministic_verified and t.recovered_text and t.status == "success" for t in result.deobfuscation.transformations))
    return {"id": case["id"], "configuration": case["configuration"], "status": result.status,
            "valid_json": json_valid, "schema_and_literal_validation": result.llm is not None,
            "expected_labels": case["expected"], "observed_labels": labels, "exact_labels": labels == sorted(case["expected"]),
            "multilabel_expected": len(case["expected"]) > 1,
            "verified_recovery_nonempty": recovery if case["configuration"] == "C" else None,
            "cites_recovery": any(e.provenance == "deobfuscator_recovered" for e in result.evidence) if case["configuration"] == "C" else None,
            "uncertainty_check": (result.llm.uncertainty.level.value != "low" and result.llm.risk_label.value != "benign") if result.llm and case.get("unknown") else None,
            "injection_check": (result.llm.prompt_injection.detected and labels == sorted(case["expected"])) if result.llm and case.get("injection") else None,
            "semantic_support": "requires_case_review", "inventions": "requires_case_review",
            "usage": result.operational.get("usage"), "seconds": result.operational.get("inference_seconds"),
            "errors": [e.code for e in result.errors]}


def run(grant_path):
    prospective = json.loads((OUT / PLAN_FILE).read_text(encoding="utf-8"))
    if prospective != plan():
        raise ValueError("prospective plan changed")
    decision = json.loads((OUT / "model_decision.json").read_text(encoding="utf-8"))
    grant = FreeTierConfirmation(**json.loads(grant_path.read_text(encoding="utf-8")))
    grant.check(decision["model"])
    client = adapter(decision["model"], grant)
    service = AnalysisService(adapter=client)
    rows = []
    try:
        for case in schedule():
            # A rerun loads finished artifacts; it never repeats a reserved request, even after interruption.
            target = OUT / f"{case['id']}_{case['configuration']}.json"
            if target.exists():
                from app.schemas.pipeline import PipelineResult
                result = PipelineResult.model_validate_json(target.read_text(encoding="utf-8"))
                rows.append(evaluate(result, case))
                if result.status not in {"completed", "partial"}:
                    break
                continue
            last = client.budget.entries()
            if last:
                elapsed = (datetime.now(timezone.utc) - datetime.fromisoformat(last[-1]["reserved_at"])).total_seconds()
                interval = max(21, 61 / grant.rpm) if grant.rpm else 21
                # Unknown project TPM: allow each prior request's entire minute to expire.
                interval = max(interval, 61)
                delay = max(0, interval - elapsed)
                while delay > 0:
                    chunk = min(delay, 30)
                    time.sleep(chunk)
                    delay -= chunk
            result = service.analyze(case["script"], case["configuration"])
            write(target, result.model_dump(mode="json"))
            row = evaluate(result, case)
            rows.append(row)
            print(json.dumps({k: row[k] for k in ("id", "configuration", "status", "exact_labels", "errors")}), flush=True)
            if result.status not in {"completed", "partial"}:
                break
        write(OUT / "summary.json", {"results": rows, "http_attempts": len(client.budget.entries()),
              "inferences_dispatched": sum(e["kind"] == "generateContent" for e in client.budget.entries()),
              "planned_inferences": 11, "free_tier_limits": asdict(grant), "scientific_selection_approved": False,
              "free_quota_remaining": "unknown", "phase4_started": False})
    finally:
        client.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["prepare", "preflight", "run"])
    parser.add_argument("--free-tier-confirmation", type=Path)
    args = parser.parse_args()
    try:
        if args.action == "prepare":
            prepare()
        elif args.action == "preflight":
            return preflight()
        else:
            if not args.free_tier_confirmation:
                raise ValueError("free tier confirmation required")
            run(args.free_tier_confirmation)
        return 0
    except Exception as exc:
        print(json.dumps({"error_type": getattr(exc, "code", "gemini_experiment_configuration")}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

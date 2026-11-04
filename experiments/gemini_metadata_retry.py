"""Preview by default. Execute ONE models.list only after explicit owner authorization."""
from __future__ import annotations

import argparse
from dataclasses import asdict
import hashlib
import json
from pathlib import Path

from experiments.gemini_viability import ROOT, OUT, plan, write
from experiments.gemini_cases import schedule
from app.services.llm.gemini import GeminiAdapter, GeminiSettings, fail
from app.services.llm.gemini_budget import MetadataRetryAuthorization, RequestBudget

DIAGNOSTIC = ROOT / "artifacts/gemini_transport_diagnostic"


def prospective_plan():
    original = {f"{c['id']}_{c['configuration']}": c for c in schedule()}
    order = ["G03_B", "G03_C", "G06_B", "G06_C", "G01_B", "G09_B", "G04_B", "G07_B", "G08_B", "G05_B"]
    return {**plan(), "revision": "transport-r2-prospective", "metadata_requests": 2,
            "inferences_planned": 10, "model_preference": ["gemini-3.8-flash"],
            "cases": [original[key] for key in order], "execution_authorized": False,
            "requires": ["explicit_authorization_for_second_metadata", "successful_listing",
                         "model_specific_positive_free_quota_confirmation", "permission_to_resume_generation"],
            "omitted_control": {"id": "G02_B", "reason": "Reserve one extra metadata request; B02 outer invocation remains in G09, inert-block negative in G04. Isolated bound-input IEX control deferred."},
            "supersedes_for_future_execution": "artifacts/gemini_viability/plan_r1.json",
            "no_model_change": True}


def preview():
    ledger = RequestBudget(OUT / "requests.jsonl")
    entries = ledger.entries()
    return {"mode": "preview_no_network", "requests_reserved": len(entries),
            "ledger_sha256": hashlib.sha256(ledger.path.read_bytes()).hexdigest(),
            "next_operation": "models.list", "would_use_reservation": 2,
            "maximum_future_generations_after_second_metadata": 10,
            "model_change": False, "requires_explicit_owner_authorization": True}


def execute(authorization_path):
    ledger = RequestBudget(OUT / "requests.jsonl")
    # Refuse before client creation if no exact one-shot approval or prospective plan.
    if len(ledger.entries()) != 1 or ledger.entries()[0]["kind"] != "models.list":
        fail("gemini_metadata_retry_not_authorized")
    authorization = MetadataRetryAuthorization(**json.loads(authorization_path.read_text(encoding="utf-8-sig")))
    authorization_hash = authorization.check(ledger.path.read_bytes())
    if json.loads((DIAGNOSTIC / "plan_r2.json").read_text(encoding="utf-8")) != prospective_plan():
        fail("gemini_prospective_plan_mismatch")
    target = DIAGNOSTIC / "metadata_retry_02.json"
    if target.exists():
        fail("gemini_metadata_retry_not_authorized")
    client = GeminiAdapter(budget=ledger, allowed_original_hashes=set(), generation=GeminiSettings(),
                           metadata_retry=authorization)
    try:
        result = client.list_models()
        exact_model_listed = any(m["name"] == "models/gemini-3.8-flash" and "generateContent" in (m["supported_actions"] or [])
                                 for m in result["models"])
        write(target, {"status": "metadata_received", **result, "model_requested_for_future": "gemini-3.8-flash",
                       "exact_model_listed": exact_model_listed, "free_quota_verified": False,
                       "authorization_sha256": authorization_hash, "generation_enabled": False})
        print(json.dumps({"status": "metadata_received", "requests_reserved": len(ledger.entries()),
                          "exact_model_listed": exact_model_listed, "inferences": 0, "quota_verified": False}))
        return 0
    except Exception as exc:
        code = getattr(exc, "code", "gemini_local_client_error")
        write(target, {"status": "failed", "diagnostic": client.last_diagnostic or {"category": code, "http_status": None},
                       "http_attempt": client.transport.last_attempt,
                       "authorization_sha256": authorization_hash, "inferences": 0})
        print(json.dumps({"error_type": code, "requests_reserved": len(ledger.entries()), "inferences": 0}))
        return 2
    finally:
        client.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--authorization", type=Path)
    args = parser.parse_args()
    try:
        if not args.execute:
            print(json.dumps(preview(), indent=2))
            return 0
        if args.authorization is None:
            fail("gemini_metadata_retry_not_authorized")
        return execute(args.authorization)
    except Exception as exc:
        print(json.dumps({"error_type": getattr(exc, "code", "gemini_local_client_error")}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

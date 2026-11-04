"""Record the blocked first preflight without retrying it or inventing model results."""
from datetime import datetime, timezone
import json

from experiments.gemini_viability import OUT, plan, write
from experiments.gemini_cases import schedule


def main():
    error = json.loads((OUT / "preflight_error.json").read_text(encoding="utf-8"))
    entries = [json.loads(line) for line in (OUT / "requests.jsonl").read_text(encoding="utf-8").splitlines()]
    if len(entries) != 1 or entries[0]["kind"] != "models.list":
        raise ValueError("This closeout applies only to the first failed metadata request")
    write(OUT / "plan_r1.json", plan())
    write(OUT / "plan_amendment.json", {
        "supersedes": "plan.json", "active": "plan_r1.json", "changed_case": "G01",
        "change": "Expected labels [] -> [B05]: Get-MpPreference queries software/defense information; no B04/B07.",
        "reason": "Local prospective taxonomy review; no Gemini inference or model output existed.",
        "inferences_before_amendment": 0, "original_plan_retained": True,
        "recorded_at": datetime.now(timezone.utc).isoformat()})
    write(OUT / "owner_confirmation.json", {
        "source": "user_chat_reply", "project_tier": "Free", "owner_confirmed": True,
        "model_specific_positive_quota_confirmed": False,
        "billing_console_independently_inspected": False,
        "rpm": None, "tpm": None, "rpd": None, "remaining_rpd": None,
        "inference_authorization_active": False,
        "reason": "Preflight failed; no validated available-model listing or live quota evidence."})
    write(OUT / "summary.json", {
        "status": "blocked_preflight_no_inference", "candidate_model": "gemini-3.8-flash",
        "model_actually_tested": None, "model_version": None, "authentication": "unverified",
        "available_models": None, "project_tier": "owner_confirmed_Free", "quota_limits": "unknown",
        "api_requests_reserved": len(entries), "api_request_limit": 12,
        "inferences_dispatched": 0, "inferences_planned": 11,
        "inference_token_consumption": 0, "quota_remaining": "unverified",
        "preflight_error": error["error_type"], "preflight_http_status": None,
        "preflight_error_subtype": "not_recorded_in_first_attempt",
        "automatic_retries": 0, "raw_model_responses": 0,
        "results": [{"id": c["id"], "configuration": c["configuration"], "status": "not_executed",
                     "expected_labels": c["expected"], "observed_labels": None, "quality_metrics": None}
                    for c in schedule()],
        "scientific_selection_approved": False, "phase4_started": False,
        "recommendation": "Integration passes offline controls; live feasibility and quality remain undetermined."})


if __name__ == "__main__":
    main()

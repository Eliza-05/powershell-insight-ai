"""Create diagnostic-only review packets, or record a personally completed human form.

Usage with PYTHONPATH=backend;.:
  python -B artifacts/pre_phase4/resume_01/review_diagnostics.py prepare
  python -B artifacts/pre_phase4/resume_01/review_diagnostics.py record completed.json
Never copies a human approval from historical development to these outputs.
"""
import argparse
import json
from pathlib import Path

from app.services.pipelines.validation import strict_json
from experiments.model_readiness import review
from experiments.model_readiness.diagnostics import OUT as BASE_OUT, ROOT, save
from experiments.readiness_resume import OUT

HERE = Path(__file__).resolve().parent
PACKETS = HERE / "semantic_review"


def prepare():
    review.OUT = PACKETS
    plan = json.loads((OUT / "plan.json").read_text(encoding="utf-8"))
    notes = json.loads((HERE / "semantic_AI_notes.json").read_text(encoding="utf-8"))
    entries = []
    for call in plan["calls"]:
        path = OUT / "results" / (call["id"] + ".json")
        if not path.exists():
            path = BASE_OUT / "results" / (call["id"] + ".json")
        if not path.exists():
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        try:
            parsed = strict_json(data.get("response", {}).get("message", {}).get("content", ""))
        except ValueError:
            parsed = None
        item = review.packet(call["id"], path, call["script"], parsed,
            {"labels": call["reference_labels_reviewer_only"], "human_approved": False},
            "predeclared AI-assisted synthetic development reference, not independent ground truth",
            "diagnostic_development", {**data, "case_id": call["case"]})
        item["diagnostic_structural_validation"] = {"accepted": data.get("structurally_accepted", False), "error": data.get("error")}
        item["profile"] = call["profile"]
        item["request_sha256"] = call["request_sha256"]
        item["historical_truncated"] = data.get("response", {}).get("done_reason") == "length"
        item["AI_assistance"] = {"kind": "AI_assisted_diagnostic_observation", "not_human_adjudication": True,
                                  "text": notes[call["id"]]["observation"]}
        entries.append(review.write_packet(item))
    save(PACKETS / "index.json", {"packets": entries, "human_decisions": 0,
        "strict_semantic_support_rate": None, "scope": "new predeclared synthetic diagnostics only",
        "reference_and_review_status": "AI_assisted_not_independently_human_adjudicated"})
    return {"packets": len(entries), "human_decisions": 0}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["prepare", "record"])
    parser.add_argument("form", nargs="?")
    args = parser.parse_args()
    result = prepare() if args.command == "prepare" else review.record(
        json.loads(Path(args.form).read_text(encoding="utf-8")), out=PACKETS, root=ROOT)
    print(json.dumps(result))

"""New static A analyses + explicitly historical B/C, without any inference path."""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path

from app.schemas.pipeline import PipelineResult
from app.services.llm.qwen14_prototype import DECISION, DIGEST, load_settings
from app.services.pipelines.context import canonical, sha
from app.services.pipelines.service import AnalysisService
from app.services.pipelines.validation import strict_json

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/qwen14_exploratory_adoption"
HISTORICAL = ROOT / "artifacts/qwen25_coder14b"


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return strict_json(Path(path).read_text(encoding="utf-8"))


def save(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n"); stream.flush(); os.fsync(stream.fileno())


def require(condition, message):
    if not condition:
        raise ValueError(message)


class NoInference:
    def infer(self, *_):
        raise AssertionError("This comparison permits static A only; B/C are historical")

    def status(self):
        raise AssertionError("This comparison must not query model providers")


def verify_archive(root=ROOT, out=OUT):
    historical = root / "artifacts/qwen25_coder14b"
    manifest = read(out / "source_archive_manifest.json")
    require(digest(historical / "FREEZE.json") == manifest["original_freeze_sha256"], "Historical FREEZE changed")
    freeze = read(historical / "FREEZE.json")
    require(set(manifest["entries"]) == set(freeze["files_sha256"]), "Incomplete diagnostic source archive")
    changed = []
    for name, expected in freeze["files_sha256"].items():
        entry = manifest["entries"][name]
        archive = (root / entry["archive"]).resolve()
        require(archive.is_relative_to(out.resolve()) and digest(archive) == entry["sha256"] == expected,
                "Archived diagnostic source mismatch: " + name)
        if digest(root / name) != expected:
            changed.append(name)
    return {"original_freeze_sha256": manifest["original_freeze_sha256"],
            "archived_entries_verified": len(freeze["files_sha256"]), "evolved_live_sources": changed}


def classification(rows):
    tp = sum(len(set(r["predicted"] or []) & set(r["expected"])) for r in rows)
    fp = sum(len(set(r["predicted"] or []) - set(r["expected"])) for r in rows)
    fn = sum(len(set(r["expected"]) - set(r["predicted"] or [])) for r in rows)
    return {"TP": tp, "FP": fp, "FN": fn, "precision": tp / (tp + fp) if tp + fp else None,
            "recall": tp / (tp + fn) if tp + fn else None,
            "F1": 2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else None,
            "exact": sum(r["predicted"] is not None and set(r["predicted"]) == set(r["expected"]) for r in rows),
            "denominator": len(rows)}


def compare():
    archive = verify_archive(ROOT, OUT)
    calls = read(HISTORICAL / "plan/calls.json")["calls"]
    require(len(calls) == 8 and len({c["input_sha256"] for c in calls}) == 6, "Wrong development units")
    ledger = [strict_json(line) for line in (HISTORICAL / "execution/ledger.jsonl").read_text(encoding="utf-8").splitlines()]
    require(len(ledger) == 8, "Historical diagnostic budget changed")
    evaluation = read(HISTORICAL / "evaluation.json")
    require(len(evaluation["rows"]) == 8, "Incomplete historical evaluation")
    old_a = {r["input_sha256"]: r["pipeline_A"] for r in read(HISTORICAL / "pipeline_A_regression.json")["results"]}
    service = AnalysisService(load_settings(), adapter=NoInference())
    static, joined = {}, []
    for call, intent, row in zip(calls, ledger, evaluation["rows"]):
        name = call["call_id"]
        path = HISTORICAL / "execution/results" / (name + ".json")
        require(digest(path) == read(HISTORICAL / "execution/checkpoints" / (name + ".json"))["result_sha256"], "Historical output changed")
        record = read(path)
        result = PipelineResult.model_validate(record["pipeline"])
        request = read(HISTORICAL / "plan" / call["request_file"])
        script = (HISTORICAL / "plan" / call["script_file"]).read_text(encoding="utf-8")
        require(name == record["call_id"] == row["call_id"] == intent["call_id"], "Wrong historical join")
        require(result.configuration == call["mode"] and result.input_sha256 == call["input_sha256"] == sha(script), "Input/mode mismatch")
        require(record["freeze_sha256"] == intent["freeze_sha256"] == archive["original_freeze_sha256"], "Foreign freeze")
        require(sha(canonical(request)) == call["request_sha256_canonical"] == intent["request_sha256"] == record["request_sha256"], "Request mismatch")
        require(result.operational["request"] == request and result.operational["installed_digest"] == DIGEST, "Foreign profile")
        admitted = [b.behavior_id.value for b in result.llm.behaviors] if result.llm is not None else None
        require(admitted == row["predicted"] and row["expected"] == call["reference_labels_reviewer_only"], "Evaluation mismatch")
        if call["input_sha256"] not in static:
            a = service.analyze(script, "A").model_dump(mode="json")
            require(a["operational"] == {} and a["llm"] is None, "A dispatched inference")
            require(a["deterministic"] == old_a[call["input_sha256"]]["deterministic"], "Deterministic regression")
            value = {"specimen": call["specimen"], "script_sha256": call["input_sha256"],
                "reference_labels_reused": row["expected"], "predicted": a["deterministic"]["behaviors"],
                "complete": a["status"] == "completed", "pipeline": a}
            static[call["input_sha256"]] = value
            save(OUT / "static_A" / (call["specimen"] + ".json"), value)
        joined.append({"call_id": name, "mode": call["mode"], "specimen": call["specimen"],
            "script_sha256": call["input_sha256"], "historical_pipeline_run_id": result.run_id,
            "historical_started_at": result.started_at, "historical_result_path": path.relative_to(ROOT).as_posix(),
            "historical_result_sha256": digest(path), "request_sha256": record["request_sha256"],
            "origin": "historical_Qwen14_diagnostic_reused_without_new_inference",
            "automatic_assessment_reused": row, "new_A_artifact": "static_A/" + call["specimen"] + ".json",
            "personal_adjudication": "pending", "reference_status": "reused_development_not_independent"})
    pairs = []
    for b, c in ((1, 2), (3, 4)):
        before, after = joined[b], joined[c]
        require(before["script_sha256"] == after["script_sha256"], "Pair input mismatch")
        before_request = read(HISTORICAL / "plan" / calls[b]["request_file"])
        after_request = read(HISTORICAL / "plan" / calls[c]["request_file"])
        require({k: v for k, v in before_request.items() if k != "messages"} ==
                {k: v for k, v in after_request.items() if k != "messages"}, "Pair parameters differ")
        require(before_request["messages"][0] == after_request["messages"][0], "Pair policy differs")
        pairs.append({"B": before["call_id"], "C": after["call_id"], "script_sha256": before["script_sha256"],
            "same_model_policy_parameters": True,
            "B_assessment": before["automatic_assessment_reused"], "C_assessment": after["automatic_assessment_reused"],
            "semantic_observation_origin": "AI_assisted_existing_review_not_personal_adjudication",
            "summary": "C improves classification partially and recovered support; B06 still missing" if b == 1 else
                       "Both rejected; C keeps false activation and worsens source attribution"})
    a_rows = [{"predicted": a["predicted"], "expected": a["reference_labels_reused"]} for a in static.values()]
    metrics = {"A_unique_script_sets": classification(a_rows),
        "A_complete_unique_script_sets": classification([r for a, r in zip(static.values(), a_rows) if a["complete"]]),
        "B_six_unique_scripts": classification([r for r in evaluation["rows"] if r["mode"] == "B"]),
        "C_two_paired_scripts": classification([r for r in evaluation["rows"] if r["mode"] == "C"]),
        "paired_B_only": classification([evaluation["rows"][i] for i in (1, 3)]),
        "paired_C_only": classification([evaluation["rows"][i] for i in (2, 4)]),
        "global_Qwen_historical_unchanged": evaluation["micro"],
        "caveat": "Descriptive development counts; A/B six units, C two-unit subset. Partial A is not a certified negative; rejected LLM reports are not empty successful predictions."}
    save(OUT / "comparison.json", {"decision_id": DECISION, "created_at": datetime.now(timezone.utc).isoformat(),
        "unique_development_scripts": 6, "new_static_A_runs": 6, "historical_BC_records_reused": 8,
        "new_real_inferences": 0, "independent_evaluation": False, "personal_adjudications": 0,
        "archive_verification": archive, "units": list(static.values()), "historical_joins": joined,
        "pairs": pairs, "metrics": metrics})
    print(json.dumps({"new_A": 6, "historical_BC": 8, "new_inferences": 0, "metrics": metrics}, ensure_ascii=False))


if __name__ == "__main__":
    compare()

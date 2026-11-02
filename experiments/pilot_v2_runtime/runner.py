"""Sequential one-model experiment. Fixed loopback requests; samples are strings only."""

from __future__ import annotations

import argparse
from contextlib import contextmanager
import json
import os
from pathlib import Path
import random
import sys
import threading
import time

from .artifacts import ROOT, encode, read, sha, utc, verify_freeze, write_new
from .resources import GIB, Monitor, snapshot
from .transport import LocalOllama, MODEL

sys.path.insert(0, str(ROOT / "backend"))
from app.schemas.llm_analysis import AnalysisResult
from app.services.llm.prompt import load_prompt


def strict_json(text):
    def pairs(values):
        result = {}
        for key, value in values:
            if key in result:
                raise ValueError("Duplicate JSON key: " + key)
            result[key] = value
        return result

    def invalid_constant(value):
        raise ValueError("Non-JSON numeric constant: " + value)

    return json.loads(text, object_pairs_hook=pairs, parse_constant=invalid_constant)


def parse_response(response, options):
    result = {"json_valid": False, "schema_valid": False, "truncated": False,
              "error": None, "parsed": None}
    try:
        if response.get("raw_utf8_valid") is False:
            raise ValueError("Invalid UTF-8 response; do not repair")
        outer = strict_json(response["raw"])
        if not isinstance(outer, dict):
            raise ValueError("Server response must be a JSON object")
        result["ollama"] = outer
        if response["status"] != 200 or "error" in outer:
            raise ValueError("HTTP/API error: " + str(outer.get("error", response["status"])))
        if outer.get("done") is not True:
            raise ValueError("Incomplete server response")
        result["truncated"] = outer.get("done_reason") != "stop"
        if not isinstance(outer.get("message"), dict):
            raise ValueError("Missing/invalid assistant message")
        if outer["message"].get("tool_calls"):
            raise ValueError("Unexpected tool invocation output")
        prompt_tokens, generated_tokens = outer.get("prompt_eval_count"), outer.get("eval_count")
        if not isinstance(prompt_tokens, int) or not isinstance(generated_tokens, int):
            raise ValueError("Missing tokenizer counts")
        if prompt_tokens > 5500 or prompt_tokens + generated_tokens > options["num_ctx"]:
            result["truncated"] = True
            result["error"] = "Context/token budget violated"
        content = outer.get("message", {}).get("content", "")
        parsed = strict_json(content)
        result["json_valid"] = True
        AnalysisResult.model_validate_json(content, strict=True)
        result["schema_valid"] = True
        result["parsed"] = parsed
        result["thinking_observed"] = bool(outer.get("message", {}).get("thinking"))
    except (ValueError, TypeError, KeyError) as exc:
        result["error"] = str(exc)
    return result


def usable(result):
    return result["json_valid"] and result["schema_valid"] and not result["truncated"] and result["error"] is None


def make_request(source, prompt, config, schema):
    common = config["common_request_proposal"]
    return {"model": MODEL, "messages": prompt.build_messages(source), "format": schema,
            "think": False, "stream": False, "truncate": False, "shift": False,
            "keep_alive": common["keep_alive"], "options": dict(common["options"])}


def plan(stage, cases, config):
    by_id = {c["case_id"]: c for c in cases}
    if stage == "technical":
        ids = config["stages"][0]["cases"]
        rows = [(by_id[cid], 1) for cid in ids]
    elif stage in {"development", "revision"}:
        rows = [(c, 1) for c in cases if c["split"] == "development"]
    elif stage == "selection":
        rows = []
        rng = random.Random(config["selection_order_seed"])
        for repetition in (1, 2, 3):
            split = [c for c in cases if c["split"] == "selection"]
            rng.shuffle(split)
            rows.extend((c, repetition) for c in split)
    else:
        raise ValueError("Unknown stage")
    if stage != "selection" and any(c["split"] != "development" for c, _ in rows):
        raise ValueError("Selection may not enter development")
    return rows


@contextmanager
def exclusive_lock(root=ROOT):
    path = root / "experiments/cache/pilot_v2_runtime.lock"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps({"pid": os.getpid(), "created_at": utc()}))
    try:
        yield
    finally:
        path.unlink()


def ledger_event(run_dir, event):
    with (run_dir / "ledger.jsonl").open("ab") as stream:
        stream.write((json.dumps(event, ensure_ascii=False) + "\n").encode())
        stream.flush(); os.fsync(stream.fileno())


def dispatched(run_dir):
    ledger = run_dir / "ledger.jsonl"
    return [json.loads(line) for line in ledger.read_text(encoding="utf-8").splitlines()
            if json.loads(line)["event"] == "dispatched"] if ledger.exists() else []


def model_state(client):
    tags = client.json("tags")
    model = next((m for m in tags["models"] if m["name"] == MODEL), None)
    if not model:
        raise RuntimeError("The authorized model is not installed")
    residents = client.json("ps")
    if any(m["name"] != MODEL for m in residents["models"]):
        raise RuntimeError("Another model is resident; leave user workloads alone")
    return {"model": model, "residents": residents}


def code_hashes():
    return {p.name: sha(p.read_bytes()) for p in (Path(__file__).parent / n for n in (
        "runner.py", "transport.py", "resources.py", "artifacts.py"))}


def assert_run_namespace(run_dir):
    namespace=(ROOT/"experiments/results/raw/pilot_v2").resolve()
    target=Path(run_dir).resolve()
    if target==namespace or not target.is_relative_to(namespace):
        raise ValueError("Use a new run directory under experiments/results/raw/pilot_v2; never historical results")


def bind_authorized_execution(run_dir, freeze_dir):
    """One experiment for this authorization, not 126 fresh calls per new folder."""
    path=ROOT/"experiments/reviews/pilot_v2_execution_binding.json"
    expected={"run_dir":Path(run_dir).resolve().relative_to(ROOT.resolve()).as_posix(),
              "freeze_sha256":sha((Path(freeze_dir)/"FREEZE.json").read_bytes())}
    if path.exists():
        binding=read(path)
        if any(binding[k]!=value for k,value in expected.items()):
            raise ValueError("This authorization is already bound to another experiment")
    else:
        write_new(path,{**expected,"bound_at":utc(),"maximum_inference_attempts":126,
                        "note":"No automatic new experiment or model after failure"})


def freeze_selection(freeze_dir, run_dir, prompt_path, decision):
    assert_run_namespace(run_dir)
    verify_freeze(freeze_dir)
    bind_authorized_execution(run_dir,freeze_dir)
    run_dir = Path(run_dir)
    for stage, expected in (("technical", 6), ("development", 24)):
        results = list((run_dir / stage).glob("*.result.json"))
        if len(results) != expected:
            raise ValueError("Complete technical/development before selection freeze")
        if not read(run_dir / stage / "stage_completed.json")["complete"]:
            raise ValueError("Prior stage did not complete")
    revision = prompt_path.resolve() != (Path(freeze_dir) / "prompt_r0.md").resolve()
    if revision and len(list((run_dir / "revision").glob("*.result.json"))) != 24:
        raise ValueError("A changed prompt requires the single development revision")
    if revision:
        authorization=read(run_dir/"revision_authorization.json")
        if authorization["prompt_sha256"]!=sha(prompt_path.read_bytes()):
            raise ValueError("Final prompt differs from the single tested revision")
        if any(read(p)["prompt_sha256"]!=authorization["prompt_sha256"] for p in (run_dir/"revision").glob("*.result.json")):
            raise ValueError("Revision did not use one identical prompt")
    if any(r["stage"] == "selection" for r in dispatched(run_dir)):
        raise ValueError("Selection already accessed")
    prompt_text = prompt_path.read_bytes()
    with (run_dir / "selection_prompt.md").open("xb") as stream:
        stream.write(prompt_text)
    record = {"frozen_at": utc(), "dataset_freeze_sha256": sha((Path(freeze_dir)/"FREEZE.json").read_bytes()),
              "prompt_sha256": sha(prompt_text), "prompt_id": load_prompt(prompt_path).prompt_id,
              "prompt_revision_used": int((run_dir / "revision").exists()),
              "final_prompt_is_revision": revision, "development_only_decision": decision,
              "configuration_sha256": sha((Path(freeze_dir)/"configuration.json").read_bytes()),
              "model_state": read(run_dir / "development/stage_completed.json")["model_state_after"],
              "code_hashes": code_hashes(), "selection_outputs_seen": False,
              "effective_parameters_evidence": "accepted exact HTTP request; context/CPU verified via /api/ps, token counts and absence of thinking; API does not echo every sampler option"}
    config = read(Path(freeze_dir)/"configuration.json")
    record["effective_request_controls"] = {"model":MODEL,"think":False,"truncate":False,"shift":False,
        "stream":False,"options":config["common_request_proposal"]["options"],
        "schema_sha256":sha((Path(freeze_dir)/"schema.json").read_bytes()),
        "execution_authority":"frozen owner global approval; copied draft flags are preserved provenance, not active denials"}
    write_new(run_dir / "selection_lock.json", record)
    return record


def prepare_revision(freeze_dir, run_dir, prompt_path, rationale):
    assert_run_namespace(run_dir)
    verify_freeze(freeze_dir)
    run_dir, prompt_path = Path(run_dir), Path(prompt_path)
    if (run_dir/"selection_lock.json").exists() or (run_dir/"selection").exists():
        raise ValueError("No revision after selection access")
    results=sorted((run_dir/"development").glob("*.result.json"))
    if len(results)!=24 or not read(run_dir/"development/stage_completed.json")["complete"]:
        raise ValueError("Finish initial development before revising")
    if sha(prompt_path.read_bytes())==sha((Path(freeze_dir)/"prompt_r0.md").read_bytes()):
        raise ValueError("The revision must differ from r0")
    record={"at":utc(),"revision_number":1,"maximum_calls":24,"selection_outputs_seen":False,
            "rationale_development_only":rationale,"prompt_sha256":sha(prompt_path.read_bytes()),
            "prompt_id":load_prompt(prompt_path).prompt_id,
            "development_result_hashes":{p.name:sha(p.read_bytes()) for p in results}}
    write_new(run_dir/"revision_authorization.json",record)
    return record


def run_stage(freeze_dir, run_dir, stage, prompt_path=None, client=None, sampler=snapshot):
    assert_run_namespace(run_dir)
    freeze_dir, run_dir = Path(freeze_dir), Path(run_dir)
    dataset = verify_freeze(freeze_dir)
    config, schema = read(freeze_dir / "configuration.json"), read(freeze_dir / "schema.json")
    client = client or LocalOllama(timeout=config["resources"]["request_timeout_seconds"])
    prompt_path = Path(prompt_path) if prompt_path else freeze_dir / "prompt_r0.md"
    if stage == "selection":
        lock = read(run_dir / "selection_lock.json")
        prompt_path = run_dir / "selection_prompt.md"
        if lock["prompt_sha256"] != sha(prompt_path.read_bytes()) or lock["code_hashes"] != code_hashes():
            raise ValueError("Selection prompt or runner changed after freeze")
        if lock["dataset_freeze_sha256"] != sha((freeze_dir / "FREEZE.json").read_bytes()):
            raise ValueError("Selection freeze changed")
    elif stage in {"development", "revision"}:
        prerequisite = "technical" if stage == "development" else "development"
        if not read(run_dir / prerequisite / "stage_completed.json")["complete"]:
            raise ValueError("Previous stage incomplete")
        if (run_dir / "selection_lock.json").exists():
            raise ValueError("No development or revision after selection freeze")
    prompt = load_prompt(prompt_path)
    if stage in {"technical", "development"} and prompt.sha256 != sha((freeze_dir/"prompt_r0.md").read_bytes()):
        raise ValueError("Initial technical/development must use r0")
    if stage == "revision":
        revision_record=read(run_dir/"revision_authorization.json")
        if prompt.sha256!=revision_record["prompt_sha256"] or revision_record["revision_number"]!=1:
            raise ValueError("Unrecorded or additional prompt revision")
    sequence = plan(stage, dataset["manifest"]["cases"], config)
    with exclusive_lock():
        bind_authorized_execution(run_dir,freeze_dir)
        state = model_state(client)
        if stage == "selection" and state["model"]["digest"] != lock["model_state"]["model"]["digest"]:
            raise ValueError("Model digest changed before selection")
        run_dir.mkdir(parents=True, exist_ok=True)
        binding_path = run_dir/"run_binding.json"
        if binding_path.exists():
            binding=read(binding_path)
        else:
            origin=read(run_dir/"technical/stage_started.json") if stage!="technical" else None
            binding={"at":utc(),"dataset_freeze_sha256":origin["freeze_sha256"] if origin else sha((freeze_dir/"FREEZE.json").read_bytes()),
                     "model_digest":origin["model_state"]["model"]["digest"] if origin else state["model"]["digest"],
                     "derived_from_already_recorded_technical_start":origin is not None}
            write_new(binding_path,binding)
        if binding["dataset_freeze_sha256"]!=sha((freeze_dir/"FREEZE.json").read_bytes()) or binding["model_digest"]!=state["model"]["digest"]:
            raise ValueError("The experiment's initial model or dataset binding changed")
        stage_dir = run_dir / stage
        stage_dir.mkdir(exist_ok=False)
        if len(dispatched(run_dir)) + len(sequence) > (126 if stage == "revision" or (run_dir / "revision").exists() else 102):
            raise ValueError("Call budget exceeded")
        version = client.json("version")
        show = client.json("show", {"model": MODEL})
        if not any(v is False for v in show.get("thinking", {}).get("values", [])):
            raise RuntimeError("The installed model does not advertise think=false")
        write_new(stage_dir / "stage_started.json", {"at": utc(), "stage": stage, "planned_calls": len(sequence),
                  "freeze_sha256": sha((freeze_dir / "FREEZE.json").read_bytes()), "prompt_sha256": prompt.sha256,
                  "version": version, "model_state": state, "show": show, "code_hashes": code_hashes()})
        failures = 0
        stopped = None
        completed = []
        for index, (case, repetition) in enumerate(sequence, 1):
            verify_freeze(freeze_dir)
            if stage=="selection" and (lock["code_hashes"]!=code_hashes() or lock["prompt_sha256"]!=sha(prompt_path.read_bytes())):
                stopped="selection_code_or_prompt_changed"; break
            current = model_state(client)
            if current["model"]["digest"] != state["model"]["digest"]:
                stopped = "model_digest_changed"; break
            before = sampler()
            needed = 2 * GIB if current["residents"]["models"] else 8 * GIB
            if before["available_bytes"] < needed or before["commit_available_bytes"] < needed:
                stopped = "insufficient_memory_before_request"; break
            stem = f"{index:03d}_{case['case_id']}_r{repetition}"
            request = make_request(dataset["sources"][case["file_ref"]], prompt, config, schema)
            write_new(stage_dir / (stem + ".request.json"), request)
            record = {"call_id": f"{stage}/{stem}", "stage": stage, "case_id": case["case_id"],
                      "repetition": repetition, "started_at": utc(), "prompt_sha256": prompt.sha256,
                      "source_sha256": case["sha256"], "request_sha256": sha(encode(request)),
                      "model_digest": state["model"]["digest"], "ollama_version": version,
                      "effective_request": request, "resources_before": before}
            print(f"{stage} {index}/{len(sequence)} {case['case_id']} r{repetition}", flush=True)
            start = time.monotonic()
            with Monitor(client.cancel, sampler=sampler) as monitor:
                if monitor.violated:
                    stopped = "resource_monitor_failure_before_dispatch"; break
                ledger_event(run_dir, {"event": "dispatched", "at": utc(), "call_id": record["call_id"],
                                      "stage": stage, "model_digest": state["model"]["digest"]})
                deadline_fired = threading.Event()

                def deadline_cancel():
                    deadline_fired.set()
                    client.cancel()

                deadline = threading.Timer(config["resources"]["request_timeout_seconds"], deadline_cancel)
                deadline.daemon = True
                deadline.start()
                try:
                    raw = client.request("chat", request)
                    record["response"] = raw
                    record.update(parse_response(raw, request["options"]))
                except Exception as exc:
                    record.update(json_valid=False, schema_valid=False, truncated=False,
                                  error=f"{type(exc).__name__}: {exc}", parsed=None)
                finally:
                    deadline.cancel()
                if deadline_fired.is_set():
                    record["error"] = "Timeout: absolute request deadline exceeded"
            record.update(finished_at=utc(), wall_seconds=time.monotonic()-start,
                          resource_samples=monitor.samples, resources=monitor.summary())
            if monitor.violated:
                record["error"] = "Memory margin/monitor failure"
            try:
                after = model_state(client)
                record["model_state_after"] = after
                loaded = after["residents"]["models"]
                if not loaded or any(m.get("context_length") != request["options"]["num_ctx"] or m.get("size_vram", 0) != 0 for m in loaded):
                    record["error"] = "CPU/context effective-state mismatch"
                if after["model"]["digest"] != record["model_digest"]:
                    record["error"] = "Model digest changed"
            except Exception as exc:
                record["effective_state_error"] = str(exc)
                record["error"] = "Could not verify effective model state"
            write_new(stage_dir / (stem + ".result.json"), record)
            ledger_event(run_dir, {"event": "completed", "at": utc(), "call_id": record["call_id"],
                                  "usable": usable(record)})
            completed.append(record)
            print(f"  usable={usable(record)} duration={record['wall_seconds']:.1f}s error={record['error']}", flush=True)
            failures = 0 if usable(record) else failures + 1
            if monitor.violated:
                stopped = "resource_margin_violation"; break
            if failures >= 2 and stage != "selection":
                stopped = "two_consecutive_operational_failures"; break
            if record["error"] and any(t in str(record["error"]).lower() for t in ("out of memory", "context length", "timeout", "timed out")):
                stopped = "unresolved_infrastructure_failure"; break
        final = {"at": utc(), "stage": stage, "planned": len(sequence), "attempted": len(completed),
                 "complete": len(completed) == len(sequence), "stopped_reason": stopped,
                 "usable": sum(usable(r) for r in completed), "model_state_after": model_state(client),
                 "projection_total_102_hours_with_20pct_margin":
                     1.2 * 102 * sum(r["wall_seconds"] for r in completed)/len(completed)/3600 if completed else None,
                 "projection_total_126_hours_with_20pct_margin":
                     1.2 * 126 * sum(r["wall_seconds"] for r in completed)/len(completed)/3600 if completed else None}
        write_new(stage_dir / "stage_completed.json", final)
        print(json.dumps(final, ensure_ascii=False), flush=True)
        return final


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("stage", "freeze-selection", "prepare-revision"))
    parser.add_argument("--freeze-dir", type=Path, required=True)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--stage", choices=("technical", "development", "revision", "selection"))
    parser.add_argument("--prompt", type=Path)
    parser.add_argument("--decision")
    args = parser.parse_args()
    if args.action == "stage":
        if not args.stage:
            parser.error("--stage required")
        run_stage(args.freeze_dir, args.run_dir, args.stage, args.prompt)
    elif args.action=="freeze-selection":
        if not args.decision:
            parser.error("--decision required, based exclusively on actual development")
        freeze_selection(args.freeze_dir, args.run_dir, args.prompt or args.freeze_dir / "prompt_r0.md", args.decision)
    else:
        if not args.prompt or not args.decision:
            parser.error("--prompt and development-only --decision required")
        prepare_revision(args.freeze_dir,args.run_dir,args.prompt,args.decision)


if __name__ == "__main__":
    main()

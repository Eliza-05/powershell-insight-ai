"""Frozen eight-intent development campaign. No retries, cloud or sample execution."""
from __future__ import annotations

import json
import os
from pathlib import Path
from uuid import uuid4

from packaging.version import Version

from app.services.deobfuscation.engine import deobfuscate
from app.services.llm.qwen14 import Qwen14Adapter, Qwen14Settings, Qwen14Transport, MODEL
from app.services.pipelines.context import build_context, canonical, sha
from app.services.pipelines.provider import response_schema
from app.services.pipelines.resources import InferenceGate, OperationalFailure
from app.services.pipelines.service import AnalysisService
from app.services.pipelines.validation import strict_json
from app.schemas.pipeline import ModelReport, PipelineResult
from experiments.gemma4_v2.runner import CampaignLock
from experiments.gemma4_v2.evaluation import assess, rates, ratio
from experiments.qwen14_environment import ROOT, OUT, now, sha as file_sha, state

GIB = 1024**3
VERSION = "qwen25-coder14b-development-v1"
SOURCES = ["experiments/qwen14_campaign.py", "experiments/qwen14_environment.py",
           "backend/app/services/llm/qwen14.py", "backend/tests/pipelines/test_qwen14.py"]


def load(path):
    return strict_json(Path(path).read_text(encoding="utf-8"))


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as f:
        json.dump(value, f, ensure_ascii=False, indent=2)
        f.write("\n"); f.flush(); os.fsync(f.fileno())


def require(condition, code):
    if not condition:
        raise OperationalFailure(code, code, "qwen14_campaign")


def payload_for(settings, context):
    return {"model": settings.model, "messages": context.messages, "format": response_schema(),
            "stream": False, "truncate": False, "keep_alive": settings.keep_alive,
            "options": settings.options.model_dump()}


def prepare():
    """Only locally preserved development scripts; references never enter requests."""
    installed = load(OUT/"installation.json")
    target = next(m for m in installed["tags"]["models"] if m["name"] == MODEL)
    # Normalize typed numeric defaults before freezing the exact wire payload.
    settings = Qwen14Settings.model_validate(Qwen14Settings(expected_digest=target["digest"]).model_dump(mode="json"))
    require(target["details"]["quantization_level"] == "Q4_K_M", "wrong_quantization")
    show=installed["show"]
    require("completion" in show["capabilities"] and "thinking" not in show["capabilities"], "unexpected_capabilities")
    info=show["model_info"]
    require(all(info.get(key)==value for key,value in {
        "qwen2.block_count":48,"qwen2.embedding_length":5120,
        "qwen2.attention.head_count":40,"qwen2.attention.head_count_kv":8}.items()), "architecture_budget_mismatch")
    require(info.get("qwen2.context_length",0)>=8192 and target["size"]<=9_100_000_000, "model_exceeds_resource_budget")
    old = ROOT/"artifacts/gemma4_development_v2"
    source_calls = load(old/"cases_and_order.json")["calls"]
    selected = [0, 1, 2, 9, 10, 4, 5, 6]
    plan = OUT/"plan"
    calls = []
    for number, index in enumerate(selected, 1):
        previous = source_calls[index]
        script = (old/previous["script_file"]).read_text(encoding="utf-8")
        require(sha(script) == previous["input_sha256"], "historical_script_changed")
        name = f"Q14-{number:02}"
        path = plan/"scripts"/(name+".ps1.txt")
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("x", encoding="utf-8", newline="\n") as f:
            f.write(script)
        context = build_context(script, deobfuscate(script) if previous["mode"] == "C" else None)
        payload = payload_for(settings, context)
        require(sum(len(m["content"].encode()) for m in context.messages)+512+settings.options.num_predict <= settings.options.num_ctx,
                "context_overflow")
        write(plan/"requests"/(name+".json"), payload)
        expected = previous["reference_labels_reviewer_only"]
        calls.append({**previous, "call_id":name, "order":number, "gemma_equivalent":previous["call_id"],
            "script_file":f"scripts/{name}.ps1.txt", "request_file":f"requests/{name}.json",
            "request_sha256_canonical":sha(canonical(payload)), "sources_for_review_only":context.sources,
            "excluded_labels_reviewer_only":sorted(set(f"B{i:02}" for i in range(1,8))-set(expected)),
            "reference_status":"Reused frozen development reference, AI assisted; not a new independent adjudication",
            "recovery_for_review_only":context.deobfuscation.model_dump(mode="json") if context.deobfuscation else None})
    write(plan/"calls.json", {"version":VERSION,"calls":calls})
    write(plan/"configuration.json", {"settings":settings.model_dump(mode="json"),
        "budget":8, "retries":0, "runtime_minimum":"0.5.0", "wire_think_parameter":False,
        "resource_budget":{"weights_upper_bytes":9_100_000_000,"KV_f16_bytes":3*GIB//2,
            "buffers_runtime_bytes":2*GIB,"safety_margin_bytes":2*GIB,
            "cold_required_bytes":settings.unloaded_reserve_bytes+settings.minimum_margin_bytes,
            "warm_required_bytes":settings.loaded_growth_reserve_bytes+settings.minimum_margin_bytes,
            "disk_minimum_bytes":2*GIB, "deadline_seconds":300},
        "criteria":{"operational":"8 terminal recorded replies, B and C supported, no critical stop",
            "promising":{"usable_min":7,"json_min":7,"exact_min":5,"denominator":8,
                "micro_precision_min":0.70,"micro_recall_min":0.70,"micro_f1_min":0.70,
                "literal_citation_fraction_min":0.90,"both_C_usable":True,
                "stored_executed_distinction":True,"systematic_benign_FP_max_unique_families":1},
            "limited":"Operationally complete/evaluable, with ordinary quality failures; errors retained",
            "critical_stop":"Resources, integrity, unauthorized tools/model, nonterminal transport, monitor/storage failure",
            "ordinary_continue":"Terminal malformed JSON, literal provenance error, output length, ordinary FP/FN",
            "semantic_support":"Provisional until personal review; no reliable detector claim"},
        "authorization":{"source":"Explicit owner request in attached text","maximum_real_local_inferences":8,
            "only_model":MODEL,"no_gemini":True,"no_phase4":True,"no_independent_selection":True}})
    files = [p for p in plan.rglob("*") if p.is_file()]
    runtime = [p for base in (ROOT/"backend/app", ROOT/"experiments/pilot_v2_runtime")
               for p in base.rglob("*") if p.suffix in {".py", ".md"}]
    runtime += [ROOT/p for p in SOURCES] + [ROOT/"experiments/gemma4_v2/runner.py",
        ROOT/"experiments/gemma4_v2/evaluation.py", ROOT/"experiments/gemma4_v2/protocol.py"]
    write(OUT/"FREEZE.json", {"version":VERSION,"at":now(),
        "files_sha256":{p.relative_to(ROOT).as_posix():file_sha(p) for p in files+runtime},
        "reference_limit":"Six development specimens, eight calls. Exposure to Gemma outcomes; no independent selection."})
    print("Frozen", file_sha(OUT/"FREEZE.json"), flush=True)


class Protocol:
    def __init__(self, out=OUT, root=ROOT):
        self.root, self.out = Path(root), Path(out)
        self.plan_dir = self.out/"plan"
        self.freeze_hash = file_sha(self.out/"FREEZE.json")
        self.verify()
        self.configuration = load(self.plan_dir/"configuration.json")
        self.settings = Qwen14Settings.model_validate(self.configuration["settings"])
        self.calls = load(self.plan_dir/"calls.json")["calls"]
        require(len(self.calls)==8 and [c["mode"] for c in self.calls]==list("BBCBCBBB"), "distribution_mismatch")

    def verify(self):
        require(file_sha(self.out/"FREEZE.json")==self.freeze_hash, "freeze_changed")
        for name, expected in load(self.out/"FREEZE.json")["files_sha256"].items():
            path=(self.root/name).resolve()
            require(path.is_relative_to(self.root.resolve()) and file_sha(path)==expected, "frozen_file_changed")

    def context(self, call):
        script=(self.plan_dir/call["script_file"]).read_text(encoding="utf-8")
        require(sha(script)==call["input_sha256"], "input_changed")
        context=build_context(script, deobfuscate(script) if call["mode"]=="C" else None)
        payload=payload_for(self.settings, context)
        require(payload==load(self.plan_dir/call["request_file"]) and sha(canonical(payload))==call["request_sha256_canonical"], "request_changed")
        require(context.sources==call["sources_for_review_only"], "sources_changed")
        user=strict_json(context.messages[1]["content"])
        require(set(user)==({"original","deterministic_recovery"} if call["mode"]=="C" else {"original"}), "reference_leak")
        return script, context, payload


class Campaign:
    def __init__(self, protocol=None, *, metadata=state, transport_builder=None,
                 gate_factory=InferenceGate):
        self.p=protocol or Protocol()
        self.out=self.p.out/"execution"
        self.metadata=metadata
        self.transport_builder=transport_builder or (lambda callback: Qwen14Transport(authorize_dispatch=callback))
        self.gate_factory=gate_factory
        self.active=None

    def entries(self):
        path=self.out/"ledger.jsonl"
        rows=[strict_json(s) for s in path.read_text(encoding="utf-8").splitlines()] if path.exists() else []
        require(len(rows)<=8, "budget_exceeded")
        for i,row in enumerate(rows):
            require(row["call_id"]==self.p.calls[i]["call_id"] and row["attempt"]==i+1
                    and row["freeze_sha256"]==self.p.freeze_hash, "ledger_corrupt")
        return rows

    def preflight(self, initial):
        self.p.verify()
        s=self.metadata()
        cfg=self.p.settings
        s["passed"]=False
        reason=None
        try:
            require(Version(s["version"]["version"])>=Version("0.5.0"), "runtime_incompatible")
            match=[m for m in s["tags"]["models"] if m["name"]==MODEL]
            require(len(match)==1 and match[0]["digest"]==cfg.expected_digest, "digest_mismatch")
            require(match[0]["details"]["quantization_level"]=="Q4_K_M", "quantization_mismatch")
            residents=s["ps"]["models"]
            require(not initial or not residents, "initial_resident_model")
            require(len(residents)<=1 and all(m["digest"]==cfg.expected_digest for m in residents), "other_model_resident")
            warm=bool(residents) and residents[0].get("context_length")==8192 and residents[0].get("size_vram")==0
            required=cfg.minimum_margin_bytes+(cfg.loaded_growth_reserve_bytes if warm else cfg.unloaded_reserve_bytes)
            s.update(warm=warm,required_available_bytes=required)
            require(min(s["memory"]["available_bytes"],s["memory"]["commit_available_bytes"])>=required, "insufficient_memory")
            require(s["disk"]["free"]>=2*GIB, "insufficient_disk")
            require(not s["circuit_blocked"], "interrupted_inference")
            runtime=[p for p in s["memory"]["processes"] if p.get("is_ollama_runtime")]
            require(runtime and all(type(p.get("private")) is int and type(p.get("working_set")) is int for p in runtime), "process_counters_unavailable")
            s["passed"]=True
        except Exception as exc:
            reason=getattr(exc,"code","preflight_failure")
        write(self.out/"preflights"/(str(uuid4())+".json"),s)
        require(s["passed"], reason or "preflight_failure")
        return s

    def reserve(self,payload):
        self.p.verify()
        rows=self.entries()
        require(self.active is not None and len(rows)<8 and not (self.out/"STOP.json").exists(), "dispatch_forbidden")
        call=self.active
        require(call["call_id"]==self.p.calls[len(rows)]["call_id"] and sha(canonical(payload))==call["request_sha256_canonical"], "dispatch_order_or_payload")
        marker=load(self.gate_factory().marker)
        require(marker.get("pid")==os.getpid() and marker.get("state")=="dispatch_intent"
                and marker.get("request_sha256")==call["request_sha256_canonical"], "dispatch_gate_required")
        row={"attempt":len(rows)+1,"call_id":call["call_id"],"request_sha256":call["request_sha256_canonical"],
             "freeze_sha256":self.p.freeze_hash,"at":now()}
        with (self.out/"ledger.jsonl").open("a",encoding="utf-8") as f:
            f.write(canonical(row)+"\n");f.flush();os.fsync(f.fileno())

    @staticmethod
    def hard_failure(pipeline):
        op=pipeline["operational"]
        response=op.get("response",{})
        if op.get("circuit_blocked") or op.get("resources",{}).get("margin_violated"):
            return "resource_or_interrupted_inference"
        if response.get("model")!=MODEL or response.get("message",{}).get("tool_calls") or response.get("message",{}).get("thinking"):
            return "response_identity_or_capability"
        for error in pipeline.get("errors",[]):
            ordinary=error["code"]=="invalid_response" and error["stage"]=="response"
            output_limit=error["code"]=="truncated_response" and response.get("done_reason")=="length"
            if not ordinary and not output_limit:
                return error["code"]
        if response.get("done") is not True or response.get("done_reason") not in {"stop","length"}:
            return "missing_terminal_acknowledgement"
        return None

    def run(self):
        self.out.mkdir(parents=True,exist_ok=True)
        with CampaignLock(self.out/"campaign.lock"):
            require(not (self.out/"campaign.json").exists() and not self.entries() and not (self.out/"STOP.json").exists(), "campaign_cannot_retry_or_resume")
            write(self.out/"campaign.json",{"version":VERSION,"at":now(),"freeze_sha256":self.p.freeze_hash,
                "authorization":self.p.configuration["authorization"],"exclusion_scope":"Application OS gate and observed Ollama state; cannot exclude arbitrary external clients"})
            try:
                for call in self.p.calls:
                    with self.gate_factory():
                        self.preflight(initial=not self.entries())
                    self.active=call
                    script,_,_=self.p.context(call)
                    adapter=Qwen14Adapter(self.p.settings, transport_factory=lambda:self.transport_builder(self.reserve),
                        sampler=lambda:self.metadata()["memory"], gate_factory=self.gate_factory)
                    pipeline=AnalysisService(self.p.settings,adapter=adapter).analyze(script,call["mode"]).model_dump(mode="json")
                    record={"experiment":VERSION,"call_id":call["call_id"],"mode":call["mode"],
                        "input_sha256":call["input_sha256"],"request_sha256":call["request_sha256_canonical"],
                        "freeze_sha256":self.p.freeze_hash,"pipeline":pipeline}
                    path=self.out/"results"/(call["call_id"]+".json")
                    write(path,record)
                    write(self.out/"checkpoints"/(call["call_id"]+".json"),{"result_sha256":file_sha(path)})
                    require(len(self.entries())==call["order"], "no_dispatch_reservation")
                    print(call["call_id"],pipeline["status"],pipeline["duration_seconds"],flush=True)
                    reason=self.hard_failure(pipeline)
                    require(reason is None,reason or "critical_failure")
            except BaseException as exc:
                write(self.out/"STOP.json",{"at":now(),"reason":getattr(exc,"code","controller_or_storage_failure"),
                    "detail":str(exc),"call_id":self.active["call_id"] if self.active else None,"automatic_resume":False})
                raise
            finally:
                self.active=None
        return {"attempts":len(self.entries()),"stopped":False}


def evaluate(out=OUT, root=ROOT):
    p=Protocol(out, root=root)
    records=[load(path) for path in sorted((p.out/"execution/results").glob("*.json"))]
    ledger=p.out/"execution/ledger.jsonl"
    intents=[strict_json(line) for line in ledger.read_text(encoding="utf-8").splitlines()] if ledger.exists() else []
    require(len(intents)==len(records)<=8,"unaccounted_intent_or_result")
    for i,record in enumerate(records):
        call=p.calls[i]
        path=p.out/"execution/results"/(call["call_id"]+".json")
        require(record["call_id"]==intents[i]["call_id"]==call["call_id"] and
            record["freeze_sha256"]==intents[i]["freeze_sha256"]==p.freeze_hash and
            record["request_sha256"]==intents[i]["request_sha256"]==call["request_sha256_canonical"],"result_identity_mismatch")
        require(load(p.out/"execution/checkpoints"/(call["call_id"]+".json"))["result_sha256"]==file_sha(path),"result_hash_mismatch")
        pipeline=PipelineResult.model_validate(record["pipeline"])
        require(pipeline.configuration==call["mode"] and pipeline.input_sha256==call["input_sha256"],"pipeline_identity_mismatch")
    rows=[assess(p,next(c for c in p.calls if c["call_id"]==r["call_id"]),r) for r in records]
    for row,record in zip(rows,records):
        op=record["pipeline"]["operational"]
        response=op.get("response",{})
        raw=response.get("message",{}).get("content","")
        row["schema_valid"]=False
        row["raw_predicted"]=None
        try:
            parsed=strict_json(raw)
            row["raw_predicted"]=[b["behavior_id"] for b in parsed.get("behaviors",[])]
            ModelReport.model_validate_json(raw,strict=True)
            row["schema_valid"]=True
        except (ValueError,TypeError,KeyError,AttributeError):
            pass
        row.update(false_positives=sorted(set(row["predicted"] or [])-set(row["expected"])),
            false_negatives=sorted(set(row["expected"])-set(row["predicted"] or [])),
            inference_seconds=op.get("inference_seconds"),model=op.get("model"),digest=op.get("installed_digest"),
            metrics={k:response.get(k) for k in ("prompt_eval_count","eval_count","total_duration","load_duration")},
            contract_errors=record["pipeline"]["errors"],semantic_support="provisional_pending_personal_review")
    micro=rates(sum(r["TP"] for r in rows),sum(r["FP"] for r in rows),sum(r["FN"] for r in rows))
    citations=[c for r in rows for c in r["citations"]]
    value={"rows":rows,"micro":micro,"attempted":len(records),"planned":8,
        "exact_sets":{"numerator":sum(r["exact"] is True for r in rows),"denominator":len(rows)},
        "literal_citations":{"numerator":sum(c["literal_unique_correct_source"] for c in citations),"denominator":len(citations)},
        "json_valid":sum(r["parseable_JSON"] for r in rows),"usable":sum(r["usable"] for r in rows),
        "schema_valid":sum(r["schema_valid"] for r in rows),
        "metric_policy":"All attempted determinable calls; unusable outputs count as no predictions, reference positives become FN. Unattempted calls excluded and reported separately.",
        "semantic_review":"Provisional AI-assisted observations; personal adjudication pending"}
    write(p.out/"evaluation.json",value)
    print(json.dumps({k:v for k,v in value.items() if k!="rows"},ensure_ascii=False))


if __name__ == "__main__":
    import sys
    {"prepare":prepare,"run":lambda:print(Campaign().run()),"evaluate":evaluate}[sys.argv[1]]()

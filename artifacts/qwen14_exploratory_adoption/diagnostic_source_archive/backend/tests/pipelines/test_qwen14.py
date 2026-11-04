"""Offline contract/controller checks; no model or canonical budget is contacted."""
from copy import deepcopy
import json
from pathlib import Path
import shutil
import socket
import subprocess

import pytest

from app.services.llm.qwen14 import MODEL, Qwen14Transport
from app.services.pipelines.resources import InferenceGate, OperationalFailure
from experiments import qwen14_campaign as q

REAL_ROOT = q.ROOT


@pytest.fixture
def protocol(tmp_path, monkeypatch):
    monkeypatch.setattr(socket, "create_connection", lambda *a,**k:pytest.fail("Real network forbidden"))
    monkeypatch.setattr(subprocess, "Popen", lambda *a,**k:pytest.fail("Subprocess forbidden"))
    for name in q.SOURCES+["experiments/gemma4_v2/runner.py","experiments/gemma4_v2/evaluation.py","experiments/gemma4_v2/protocol.py"]:
        path=tmp_path/name;path.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(REAL_ROOT/name,path)
    source=REAL_ROOT/"artifacts/gemma4_development_v2"
    target=tmp_path/"artifacts/gemma4_development_v2"
    shutil.copytree(source/"scripts",target/"scripts")
    shutil.copyfile(source/"cases_and_order.json",target/"cases_and_order.json")
    out=tmp_path/"artifacts/qwen25_coder14b"
    q.write(out/"installation.json",{"tags":{"models":[{"name":MODEL,"digest":"1"*64,"size":9_000_000_000,"details":{"quantization_level":"Q4_K_M"}}]},
        "show":{"capabilities":["completion"],"model_info":{"qwen2.block_count":48,"qwen2.embedding_length":5120,
            "qwen2.attention.head_count":40,"qwen2.attention.head_count_kv":8,"qwen2.context_length":32768}}})
    monkeypatch.setattr(q,"ROOT",tmp_path);monkeypatch.setattr(q,"OUT",out)
    q.prepare()
    return q.Protocol(out,root=tmp_path)


class Server:
    def __init__(self,p):
        self.p=p;self.chats=[];self.residents=[];self.override={};self.free=20*q.GIB
        self.on_chat=None

    def metadata(self):
        return {"version":{"version":"0.40.13"},"tags":{"models":[{"name":MODEL,
            "digest":self.p.settings.expected_digest,"details":{"quantization_level":"Q4_K_M"}}]},
            "ps":{"models":deepcopy(self.residents)},"circuit_blocked":False,
            "disk":{"free":30*q.GIB},"memory":{"available_bytes":self.free,
                "commit_available_bytes":25*q.GIB,"commit_limit_bytes":50*q.GIB,
                "commit_used_bytes":25*q.GIB,"physical_total_bytes":32*q.GIB,
                "processes":[{"name":"ollama.exe","is_ollama_runtime":True,"private":100,"working_set":100}]}}

    def transport(self,callback):
        server=self
        class Transport:
            last_response=None
            def cancel(self): pass
            def json(self,endpoint,payload=None):
                if endpoint in {"version","tags","ps"}:return server.metadata()[endpoint]
                if endpoint=="show":return {"capabilities":["completion"],"model_info":{"qwen2.context_length":32768}}
                assert endpoint=="chat" and callback
                callback(payload)
                number=len(server.chats);call=server.p.calls[number]
                server.chats.append(deepcopy(payload))
                server.residents=[{"digest":server.p.settings.expected_digest,"context_length":8192,"size_vram":0}]
                report={"obfuscation_techniques":[],"recovered_content":[],
                    "behaviors":[{"behavior_id":label,"confidence":"medium","explanation":"Offline fixture",
                        "evidence":[{"source_id":"original","snippet":call["sources_for_review_only"]["original"]}]} for label in call["reference_labels_reviewer_only"]],
                    "risk_label":"unknown","risk_rationale":"Offline fixture",
                    "uncertainty":{"level":"medium","notes":"Offline fixture","uninterpretable_fragments":[]},
                    "prompt_injection":{"detected":False,"snippets":[],"notes":"Offline fixture"},
                    "limitations":["Offline fixture"]}
                response={"model":MODEL,"message":{"content":json.dumps(report)},"done":True,"done_reason":"stop",
                    "prompt_eval_count":1000,"eval_count":300}
                change=server.override.get(number)
                if isinstance(change,Exception):raise change
                if change:response.update(change)
                if server.on_chat:server.on_chat(number,response)
                self.last_response={"raw_utf8":json.dumps(response),"transport_read_complete":True,"status":200}
                return response
        return Transport()


def campaign(p,server):
    return q.Campaign(p,metadata=server.metadata,transport_builder=server.transport,
        gate_factory=lambda:InferenceGate(p.out/"test.lock"))


def test_eight_calls_no_retry_no_reference_leaks_and_metrics(protocol):
    s=Server(protocol);c=campaign(protocol,s)
    assert c.run()=={"attempts":8,"stopped":False}
    assert len(s.chats)==8
    for call,payload in zip(protocol.calls,s.chats):
        assert "think" not in payload and "draft_num_predict" not in payload["options"]
        user=json.loads(payload["messages"][1]["content"])
        assert set(user)==({"original","deterministic_recovery"} if call["mode"]=="C" else {"original"})
    for a,b in ((1,2),(3,4)):
        assert s.chats[a]["options"]==s.chats[b]["options"]
        assert s.chats[a]["messages"][0]==s.chats[b]["messages"][0]
        assert protocol.calls[a]["input_sha256"]==protocol.calls[b]["input_sha256"]
    with pytest.raises(OperationalFailure,match="cannot_retry"):
        c.run()
    assert len(s.chats)==8
    q.evaluate(protocol.out, root=protocol.root)
    e=q.load(protocol.out/"evaluation.json")
    assert e["micro"]=={"TP":6,"FP":0,"FN":0,"precision":1,"recall":1,"F1":1}
    assert e["exact_sets"]=={"numerator":8,"denominator":8}


def test_low_memory_never_dispatches(protocol):
    s=Server(protocol);s.free=3*q.GIB;c=campaign(protocol,s)
    with pytest.raises(OperationalFailure,match="insufficient_memory"):c.run()
    assert not s.chats and not c.entries()
    assert q.load(c.out/"STOP.json")["reason"]=="insufficient_memory"


def test_frozen_script_change_stops_before_dispatch(protocol):
    s=Server(protocol)
    (protocol.plan_dir/protocol.calls[0]["script_file"]).write_text("changed",encoding="utf-8")
    with pytest.raises(OperationalFailure,match="frozen_file_changed"):campaign(protocol,s).run()
    assert not s.chats


def test_terminal_contract_error_and_ordinary_FP_continue(protocol):
    s=Server(protocol)
    s.override[0]={"message":{"content":"{malformed"}}
    c=campaign(protocol,s);c.run()
    assert len(s.chats)==8
    first=q.load(c.out/"results/Q14-01.json")
    assert first["pipeline"]["status"]=="error"


def test_critical_tool_request_stops_and_never_retries(protocol):
    s=Server(protocol);s.override[0]={"message":{"content":"{}","tool_calls":[{"name":"forbidden"}]}}
    c=campaign(protocol,s)
    with pytest.raises(OperationalFailure):c.run()
    assert len(s.chats)==1 and len(c.entries())==1
    with pytest.raises(OperationalFailure):c.run()
    assert len(s.chats)==1


def test_dispatch_callback_enforces_limit_and_frozen_payload(protocol):
    s=Server(protocol);c=campaign(protocol,s);c.run()
    c.active=protocol.calls[-1]
    with pytest.raises(OperationalFailure,match="dispatch_forbidden"):
        c.reserve(s.chats[-1])
    assert len(c.entries())==8


def test_transport_rejects_wrong_model_and_missing_authorization():
    with pytest.raises(OperationalFailure,match="Only qwen"):
        Qwen14Transport().json("show",{"model":"other"})
    with pytest.raises(OperationalFailure,match="Chat needs"):
        Qwen14Transport().json("chat",{"model":MODEL})


def test_unusable_positive_output_remains_in_metric_denominator(protocol):
    s=Server(protocol);s.override[1]={"message":{"content":"{malformed"}}
    c=campaign(protocol,s);c.run();q.evaluate(protocol.out,root=protocol.root)
    e=q.load(protocol.out/"evaluation.json")
    assert e["micro"]["TP"]==4 and e["micro"]["FN"]==2 and e["micro"]["FP"]==0
    assert e["exact_sets"]=={"numerator":7,"denominator":8}
    assert e["usable"]==7


def test_resource_margin_lost_during_inference_stops(protocol):
    s=Server(protocol)
    s.on_chat=lambda number,response:setattr(s,"free",q.GIB)
    c=campaign(protocol,s)
    with pytest.raises(OperationalFailure,match="resource_or_interrupted"):c.run()
    assert len(s.chats)==1 and len(c.entries())==1


def test_timeout_consumes_one_intent_and_stops(protocol):
    s=Server(protocol);s.override[0]=OperationalFailure("timeout","SIMULATED deadline")
    c=campaign(protocol,s)
    with pytest.raises(OperationalFailure):c.run()
    assert len(c.entries())==1 and len(s.chats)==1


def test_wrong_citation_is_preserved_and_campaign_continues(protocol):
    s=Server(protocol)
    def wrong_citation(number,response):
        if number==2:
            report=json.loads(response["message"]["content"])
            report["behaviors"][0]["evidence"][0]={"source_id":"original","snippet":"invented citation"}
            response["message"]["content"]=json.dumps(report)
    s.on_chat=wrong_citation
    c=campaign(protocol,s);c.run()
    assert len(s.chats)==8
    record=q.load(c.out/"results/Q14-03.json")
    assert record["pipeline"]["status"]=="error"
    assert "invented citation" in record["pipeline"]["operational"]["response"]["message"]["content"]

"""Official SDK and mocked HTTP only; four new-model calls share the historical budget."""
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import json

import httpx
import pytest

pytest.importorskip("google.genai")
from experiments import gemini_36 as g36
from experiments.gemini_metadata_retry import prospective_plan
from app.services.llm.gemini import FreeTierConfirmation, GeminiAdapter, GeminiSettings
from app.services.llm.gemini36 import MODEL36, Gemini36Adapter, Gemini36Settings
from app.services.llm.gemini_budget import MetadataRetryAuthorization, RequestBudget
from app.services.pipelines.service import AnalysisService
from app.services.pipelines.context import sha
from tests.pipelines.test_pipelines import report, finding


@pytest.fixture
def rig(tmp_path, monkeypatch):
    marker="synthetic-gemini36-test-key"
    monkeypatch.setenv("GEMINI_API_KEY",marker)
    output,initial=tmp_path/"out",tmp_path/"initial"
    output.mkdir(); initial.mkdir()
    historical=tmp_path/"r2.json"
    historical.write_text(json.dumps(prospective_plan()),encoding="utf-8")
    monkeypatch.setattr(g36,"ROOT",tmp_path)
    monkeypatch.setattr(g36,"OUTPUT",output)
    monkeypatch.setattr(g36,"INITIAL",initial)
    monkeypatch.setattr(g36,"R2_PLAN",historical)
    plan=g36.new_plan()
    (output/"plan_v1.json").write_text(json.dumps(plan))
    budget=RequestBudget(initial/"requests.jsonl")
    budget.reserve("models.list","metadata")
    auth=MetadataRetryAuthorization(True,hashlib.sha256(budget.path.read_bytes()).hexdigest(),datetime.now(timezone.utc).isoformat(),"explicit_owner_authorization")
    budget.reserve("models.list","metadata",metadata_retry=auth)
    budget.reserve("generateContent","historical-38-503")
    quota=FreeTierConfirmation(MODEL36,datetime.now(timezone.utc).isoformat(),"owner_ai_studio_confirmation",rpm=5,tpm=250000,rpd=20)
    (output/"quota_confirmation.json").write_text(json.dumps(asdict(quota)))
    binding={"plan_sha256":g36.digest(output/"plan_v1.json"),"runtime_hashes":{},
        "quota_sha256":g36.digest(output/"quota_confirmation.json"),"initial_ledger_sha256":g36.digest(budget.path),
        "contexts":[{"context_sha256":g36.context_for(c).context_sha256,"total_token_reserve":g36.input_bound(g36.context_for(c))+8192} for c in plan["cases"]]}
    (output/"binding.json").write_text(json.dumps(binding))
    (output/"authorization.json").write_text(json.dumps({"authorized":True,"model":MODEL36,"maximum_new_generations":4,"binding_sha256":g36.digest(output/"binding.json")}))
    monkeypatch.setattr(g36,"wait_for_quota",lambda *a:None)
    return output,budget,plan,monkeypatch,marker


def response(value=None,model=MODEL36):
    return httpx.Response(200,json={"candidates":[{"content":{"role":"model","parts":[{"text":json.dumps(report() if value is None else value)}]},"finishReason":"STOP"}],
        "modelVersion":model,"responseId":"synthetic36-response","usageMetadata":{"promptTokenCount":100,"candidatesTokenCount":150,"thoughtsTokenCount":200,"totalTokenCount":450}})


def fake(rig,handler):
    rig[3].setattr(g36,"Gemini36Adapter",lambda **kw:Gemini36Adapter(**kw,inner_transport=httpx.MockTransport(handler)))


def test_exact_four_calls_use_supported_config_shared_budget_and_nonempty_C(rig):
    output,budget,plan,_,marker=rig
    before=budget.path.read_bytes()
    requests=[]
    def handler(request):
        assert request.method=="POST" and request.url.path=="/v1beta/models/gemini-3.6-flash:generateContent"
        wire=json.loads(request.content); requests.append(wire)
        cfg=wire["generationConfig"]
        assert not {"temperature","topP","topK","seed","candidateCount","frequencyPenalty","presencePenalty"}&cfg.keys()
        assert cfg["thinkingConfig"]=={"include_thoughts":False,"thinking_level":"MEDIUM"}
        assert cfg["maxOutputTokens"]==8192 and cfg["responseMimeType"]=="application/json"
        assert not wire.get("tools") and marker not in request.content.decode()
        data=json.loads(wire["contents"][0]["parts"][0]["text"])
        index=len(requests)-1
        assert data["original"]==plan["cases"][index]["script"]
        assert set(data)==({"original","deterministic_recovery"} if index%2 else {"original"})
        if index%2:
            assert data["deterministic_recovery"]["verified_texts"]
        if index==3:
            text=data["deterministic_recovery"]["verified_texts"][0]
            return response(report(finding("B05",text["text"],text["source_id"]),finding("B06",text["text"],text["source_id"])))
        return response()
    fake(rig,handler)
    g36.run()
    assert len(requests)==4 and len(budget.entries())==7 and budget.path.read_bytes().startswith(before)
    for b,c in [(requests[0],requests[1]),(requests[2],requests[3])]:
        assert {k:v for k,v in b.items() if k!="contents"}=={k:v for k,v in c.items() if k!="contents"}
    result=g36.load(output/"G06_C.json")
    assert result["llm"] and all(e["provenance"]=="deobfuscator_recovered" for e in result["evidence"])
    with pytest.raises(Exception): g36.run()
    assert len(requests)==4


@pytest.mark.parametrize("status",[503,429,401,403])
def test_first_operational_failure_stops_at_four_of_twelve_without_retry(rig,status):
    output,budget,_,_,marker=rig
    calls=[]
    def handler(request):
        calls.append(1)
        return httpx.Response(status,json={"error":{"code":status,"message":"sensitive-http-message"}})
    fake(rig,handler)
    g36.run()
    assert len(calls)==1 and len(budget.entries())==4
    summary=g36.load(output/"summary.json")
    assert summary["stop_reason"] and len(summary["not_executed"])==3
    text=(output/"G03_B.json").read_text()
    assert marker not in text and "sensitive-http-message" not in text


def test_transport_failure_stops_without_another_model(rig):
    _,budget,_,_,_=rig
    calls=[]
    def handler(request):
        calls.append(request.url.path)
        raise httpx.ConnectError("private context",request=request)
    fake(rig,handler)
    g36.run()
    assert len(calls)==1 and len(budget.entries())==4 and "3.6-flash" in calls[0]


def test_new_settings_reject_other_models_and_legacy_settings():
    for other in ["gemini-3.8-flash","gemini-3.5-flash-lite"]:
        with pytest.raises(Exception): Gemini36Settings(model=other)
    with pytest.raises(Exception): Gemini36Adapter(generation=GeminiSettings())


def test_historical_config_unchanged_and_explicit36_api_status_is_local(rig,tmp_path):
    from fastapi.testclient import TestClient
    from app.api.application import create_app
    _,budget,plan,_,marker=rig
    context=g36.context_for(plan["cases"][0])
    legacy=GeminiAdapter(budget=budget,allowed_original_hashes=set(),inner_transport=httpx.MockTransport(lambda r:pytest.fail("no network")))
    modern=Gemini36Adapter(budget=budget,allowed_original_hashes=set(),inner_transport=httpx.MockTransport(lambda r:pytest.fail("no network")))
    try:
        old=legacy._generation_config(context).model_dump(exclude_none=True)
        assert old["temperature"]==1 and old["top_p"]==0.95 and old["seed"]==42 and old["candidate_count"]==1
        app=create_app(service=AnalysisService(adapter=modern),frontend_dir=tmp_path/"no-dist")
        with TestClient(app,base_url="http://127.0.0.1") as client:
            result=client.get("/api/capabilities").json()
            assert result["model"]==MODEL36 and result["think"]=="medium"
            assert marker not in json.dumps(result)
        assert len(budget.entries())==3
    finally:
        legacy.close(); modern.close()

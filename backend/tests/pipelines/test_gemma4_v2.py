"""OFFLINE simulated v2 controller tests. No canonical ledger or model is used."""
import base64
from copy import deepcopy
import json
from pathlib import Path
import shutil
import socket
import subprocess

import pytest

from app.services.pipelines.resources import InferenceGate, OperationalFailure
from experiments.gemma4_v2.protocol import Protocol, ROOT, SOURCE_FILES, FREEZE_SHA, digest, load, save, now
from experiments.gemma4_v2.runner import Campaign, CampaignLock
from experiments.gemma4_v2.evaluation import evaluate
from tests.historical_sources import load_verified_module, verified_source

GIB = 1024 ** 3


@pytest.fixture(autouse=True)
def no_real_network_or_processes(monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("No network connection or subprocess is allowed in v2 controller tests")
    monkeypatch.setattr(socket, "create_connection", forbidden)
    monkeypatch.setattr(subprocess, "Popen", forbidden)


def sample(free=20 * GIB, commit=None):
    return {"available_bytes": free, "commit_available_bytes": free if commit is None else commit,
            "commit_limit_bytes": 50 * GIB, "commit_used_bytes": 10 * GIB,
            "physical_total_bytes": 32 * GIB,
            "processes": [{"name": "ollama.exe", "pid": 8, "is_ollama_runtime": True,
                           "private": GIB, "working_set": GIB}]}


def mock_report(call, *, labels=None, wrong_source=False):
    labels = call["reference_labels_reviewer_only"] or [] if labels is None else labels
    sources = call["sources_for_review_only"]
    sid = next((s for s in sources if s != "original"), "original")
    original = sources["original"]
    injection = call["injection_control"]
    return {"obfuscation_techniques": [], "recovered_content": [],
        "behaviors": [{"behavior_id": label, "confidence": "medium",
            "explanation": "SIMULATED offline fixture; no empirical model claim.",
            "evidence": [{"source_id": "invalid-source" if wrong_source else sid,
                          "snippet": sources[sid]}]} for label in labels],
        "risk_label": "unknown", "risk_rationale": "SIMULATED static uncertainty.",
        "uncertainty": {"level": "medium", "notes": "SIMULATED static analysis only.",
                        "uninterpretable_fragments": ["$unknownCommand"] if call["indeterminate"] else []},
        "prompt_injection": {"detected": injection,
            "snippets": [original.splitlines()[0]] if injection else [], "notes": "SIMULATED ignored comment."},
        "limitations": ["SIMULATED response for a controller test, not a Gemma inference."]}


class Server:
    def __init__(self, protocol):
        self.protocol = protocol
        self.chats = []
        self.residents = []
        self.overrides = {}
        self.on_chat = None
        self.version = "0.40.13"
        self.cancelled = False

    def transport(self, callback):
        server = self
        class Transport:
            last_response = None
            def json(self, endpoint, payload=None):
                cfg = server.protocol.settings
                if endpoint == "version":
                    return {"version": server.version}
                if endpoint == "tags":
                    return {"models": [{"name": cfg.model, "digest": cfg.expected_digest,
                        "details": {"quantization_level": "Q4_K_M"}}]}
                if endpoint == "ps":
                    return {"models": deepcopy(server.residents)}
                if endpoint == "show":
                    return {"thinking": {"values": [False, True]}, "capabilities": ["completion", "thinking"],
                        "model_info": {"gemma4.context_length": 262144}}
                assert endpoint == "chat" and callback is not None
                callback(payload)  # Same physical-dispatch authorization boundary as real Gemma transport.
                index = len(server.chats)
                server.chats.append(deepcopy(payload))
                server.residents = [{"name": cfg.model, "digest": cfg.expected_digest,
                                     "context_length": 8192, "size_vram": 0}]
                if server.on_chat:
                    server.on_chat(index, payload)
                value = server.overrides.get(index)
                if isinstance(value, BaseException):
                    raise value
                response = {"model": cfg.model, "done": True, "done_reason": "stop",
                    "prompt_eval_count": 500, "eval_count": 100,
                    "message": {"role": "assistant", "content": json.dumps(mock_report(server.protocol.calls[index]))}}
                if callable(value):
                    response = value(response, server.protocol.calls[index])
                raw = json.dumps(response)
                self.last_response = {"status": 200, "raw_utf8": raw,
                    "raw_bytes_base64": base64.b64encode(raw.encode()).decode(), "transport_read_complete": True}
                return response
            def cancel(self):
                server.cancelled = True
        return Transport()


@pytest.fixture
def rig(tmp_path, monkeypatch):
    freeze_path = ROOT / "artifacts/gemma4_development_v2/FREEZE.json"
    manifest = load(freeze_path)
    names = set(manifest["files_sha256"]) | set(manifest["runtime_contract_sources_sha256"]) | set(SOURCE_FILES)
    names |= {"artifacts/gemma4_development_v2/FREEZE.json",
              "artifacts/gemma4_v2_execution_preparation/gate_clarification_v2.0-a1.json"}
    for name in names:
        target = tmp_path / name
        target.parent.mkdir(parents=True, exist_ok=True)
        source = ROOT / name
        # Reproduce historical integrity with exact archived sources, while
        # current-code regression suites continue to test the live implementation.
        expected = manifest["runtime_contract_sources_sha256"].get(name) or manifest["files_sha256"].get(name)
        if expected is not None:
            source = verified_source(ROOT, name, expected)
        shutil.copyfile(source, target)
    # Copying the files alone is insufficient: controller globals would otherwise
    # still call the evolved live context/service. Bind the verified historical
    # implementations in isolated modules for these historical controller tests.
    import experiments.gemma4_v2.protocol as protocol_module
    import experiments.gemma4_v2.runner as runner_module
    hashes = manifest["runtime_contract_sources_sha256"]
    context_name = "backend/app/services/pipelines/context.py"
    service_name = "backend/app/services/pipelines/service.py"
    historical_context = load_verified_module(tmp_path, context_name, hashes[context_name],
                                              "tests._gemma4_historical_context", monkeypatch)
    historical_service = load_verified_module(tmp_path, service_name, hashes[service_name],
                                              "tests._gemma4_historical_service", monkeypatch)
    historical_service.build_context = historical_context.build_context
    monkeypatch.setattr(protocol_module, "build_context", historical_context.build_context)
    monkeypatch.setattr(runner_module, "AnalysisService", historical_service.AnalysisService)
    protocol = Protocol(tmp_path)
    save(protocol.binding_path, {"freeze_sha256": FREEZE_SHA,
        "clarification_sha256": digest(protocol.clarification_path),
        "source_sha256": {name: digest(tmp_path / name) for name in SOURCE_FILES},
        "scope": "SIMULATED test binding, never production authorization"})
    auth = tmp_path / "SIMULATED_AUTHORIZATION.json"
    save(auth, {"execution_authorized": True, "references_accepted": True, "clarification_accepted": True,
        "maximum_inference_intents": 12, "freeze_sha256": FREEZE_SHA,
        "runner_binding_sha256": digest(protocol.binding_path),
        "clarification_sha256": digest(protocol.clarification_path),
        "source": "explicit_owner_execution_authorization", "owner_statement": "SIMULATED TEST ONLY",
        "exclusive_session_attested": True})
    server = Server(protocol)
    gate = lambda: InferenceGate(tmp_path / "SIMULATED_GLOBAL.lock")
    runner = Campaign(protocol, transport_builder=server.transport, sampler=sample,
                      gate_factory=gate, disk_sampler=lambda p: 20 * GIB)
    return runner, server, auth


def execute(rig):
    runner, _, auth = rig
    return runner.run(auth, exclusive_session_attested=True)


def reviews_for(runner, records):
    reviews, hashes = {}, {}
    for record in records:
        cid = record["call_id"]
        call = runner.protocol.calls[record["attempt"] - 1]
        report = record["pipeline"].get("llm") or {}
        hashes[cid] = digest(runner.out / "results" / (cid + ".json"))
        reviews[cid] = {"call_id": cid, "campaign_id": runner.campaign_id,
            "output_sha256": hashes[cid], "human_confirmed": True, "reviewer_type": "human_personal",
            "reviewer": "SIMULATED REVIEWER FOR UNIT TEST ONLY", "reviewed_at": now(),
            "case_semantics_supported": sorted(f["behavior_id"] for f in report.get("behaviors", [])) == sorted(call["reference_labels_reviewer_only"] or []),
            "risk_uncertainty_coherent": True, "injection_ignored": True,
            "critical_inventions": 0, "critical_contradictions": 0,
            "findings": [{"behavior_id": f["behavior_id"],
                "support": "individual" if f["behavior_id"] in (call["reference_labels_reviewer_only"] or []) else "insufficient",
                "recovered_support_confirmed": call["mode"] == "C"} for f in report.get("behaviors", [])]}
    return reviews, hashes


def metrics(runner):
    records = runner.completed_records()
    reviews, hashes = reviews_for(runner, records)
    return evaluate(runner.protocol, records, campaign_id=runner.campaign_id,
                    reviews=reviews, result_hashes=hashes, references_accepted=True,
                    stopped=(runner.out / "STOP.json").exists())


def test_complete_sequential_campaign_and_denominator_with_12_usable(rig):
    runner, server, _ = rig
    result = execute(rig)
    assert result["reserved_attempts"] == result["completed_result_records"] == len(server.chats) == 12
    assert not result["stopped"]
    rows = runner.entries()
    assert [r["call_id"] for r in rows] == [c["call_id"] for c in runner.protocol.calls]
    assert len({r["attempt_id"] for r in rows}) == 12
    records = runner.completed_records()
    assert len({r["pipeline"]["run_id"] for r in records}) == 12
    score = metrics(runner)
    assert score["coverage"]["usable"] == 12
    assert score["exact_sets"]["correct"] == score["exact_sets"]["fixed_denominator"] == 11
    assert score["micro_system"] == {"TP": 9, "FP": 0, "FN": 0, "precision": 1, "recall": 1, "F1": 1}
    assert score["decision"] == runner.protocol.gate["pass_label"]


def test_ordinary_first_false_positive_continues_and_can_pass_v2(rig):
    runner, server, _ = rig
    server.overrides[0] = lambda r,c: {**r, "message": {"role": "assistant", "content": json.dumps(mock_report(c, labels=["B05"]))}}
    execute(rig)
    assert len(server.chats) == 12 and not (runner.out / "STOP.json").exists()
    score = metrics(runner)
    assert score["exact_sets"]["correct"] == 10
    assert score["micro_system"]["TP"] == 9 and score["micro_system"]["FP"] == 1
    assert score["micro_system"]["precision"] == pytest.approx(.9)
    assert score["micro_system"]["F1"] == pytest.approx(18/19)
    assert score["decision"] == runner.protocol.gate["pass_label"]


def test_nine_exact_of_eleven_with_all_twelve_usable(rig):
    runner, server, _ = rig
    for index, labels in [(0,["B05"]),(1,["B05"])]:
        server.overrides[index] = lambda r,c,labels=labels: {**r,"message":{"role":"assistant","content":json.dumps(mock_report(c,labels=labels))}}
    execute(rig)
    score = metrics(runner)
    assert score["coverage"]["usable"] == 12
    assert score["exact_sets"] == {"correct":9,"fixed_denominator":11,"attempted_determinable":11,
                                  "excluded":"V2-09","fraction":9/11,"partial_if_incomplete":False}
    assert score["micro_system"]["TP"] == 8 and score["micro_system"]["FP"] == score["micro_system"]["FN"] == 1
    assert score["micro_system"]["precision"] == score["micro_system"]["recall"] == score["micro_system"]["F1"] == pytest.approx(8/9)
    assert score["decision"] == runner.protocol.gate["pass_label"]


def test_indeterminate_never_enters_label_metrics_but_has_own_gate(rig):
    runner, server, _ = rig
    server.overrides[8] = lambda r,c: {**r,"message":{"role":"assistant","content":json.dumps(mock_report(c,labels=["B03"]))}}
    execute(rig)
    score=metrics(runner)
    assert score["exact_sets"]["correct"] == 11 and score["micro_system"]["FP"] == 0
    assert not score["gate_checks"]["unknown_command"]
    assert score["decision"] == runner.protocol.gate["quality_fail_label"]


@pytest.mark.parametrize("kind", ["invalid_inner_JSON", "terminal_truncation"])
def test_terminal_quality_failure_continues_and_is_not_a_true_negative(rig,kind):
    runner, server, _ = rig
    server.overrides[0] = (lambda r,c: {**r,"message":{"role":"assistant","content":"{broken"}}) if kind=="invalid_inner_JSON" else (lambda r,c:{**r,"done_reason":"length","eval_count":2048})
    execute(rig)
    records=runner.completed_records();score=metrics(runner)
    assert len(server.chats)==12 and records[0]["pipeline"]["llm"] is None
    assert score["coverage"]["usable"]==11 and score["exact_sets"]["correct"]==10
    assert score["calls"][0]["predicted"] is None and score["calls"][0]["exact"] is False
    assert not (runner.out/'STOP.json').exists()


@pytest.mark.parametrize("kind", ["tool", "wrong_model", "timeout", "no_terminal_ack"])
def test_critical_failures_stop_without_retry(rig,kind):
    runner, server, _ = rig
    if kind=="timeout":server.overrides[0]=OperationalFailure("timeout","synthetic timeout")
    elif kind=="tool":server.overrides[0]=lambda r,c:{**r,"message":{**r['message'],"tool_calls":[{"function":{"name":"forbidden"}}]}}
    elif kind=="wrong_model":server.overrides[0]=lambda r,c:{**r,"model":"different-model"}
    else:server.overrides[0]=lambda r,c:{**r,"done":False}
    summary=execute(rig)
    assert summary['stopped'] and len(server.chats)==len(runner.entries())==1
    assert (runner.out/'STOP.json').exists()
    assert (runner.out/'results/V2-01.json').exists()


@pytest.mark.parametrize("key", ["available_bytes","commit_available_bytes"])
def test_insufficient_cold_memory_blocks_before_inference_and_preserves_measurement(rig,key):
    runner, server, _=rig
    def low():
        value=sample();value[key]=14*GIB;return value
    runner.sampler=low
    with pytest.raises(OperationalFailure,match="insufficient_memory"):execute(rig)
    assert len(server.chats)==len(runner.entries())==0
    failure=load(next((runner.out/'preflight_failures').glob('*.json')))
    assert failure['memory'][key]==14*GIB and failure['required_available_bytes']==15135148032


def test_resource_margin_violation_cancels_and_leaves_closed_circuit(rig):
    runner, server, _=rig; state={'low':False}
    runner.sampler=lambda:sample(GIB if state['low'] else 20*GIB)
    server.on_chat=lambda i,p:state.update(low=True)
    summary=execute(rig)
    assert summary['stopped'] and len(server.chats)==1 and server.cancelled
    assert runner.gate_factory().marker.exists()
    result=load(runner.out/'results/V2-01.json')
    assert result['pipeline']['operational']['resources']['margin_violated']


def test_plan_integrity_change_prevents_any_client_dispatch(rig):
    runner, server, _=rig
    path=runner.protocol.plan_dir/'requests/V2-01.json';path.write_text('{}',encoding='utf-8')
    with pytest.raises(OperationalFailure,match="frozen_source_or_plan_changed"):execute(rig)
    assert server.chats==[] and not runner.out.exists()


def test_integrity_change_during_campaign_stops_before_next_call(rig):
    runner, server, _=rig
    server.on_chat=lambda i,p:(runner.protocol.plan_dir/'scripts/FORMAT.ps1.txt').write_text('tampered',encoding='utf-8')
    with pytest.raises(OperationalFailure,match="frozen_source_or_plan_changed"):execute(rig)
    assert len(server.chats)==len(runner.entries())==1 and (runner.out/'STOP.json').exists()


def test_crash_after_reservation_is_spent_and_cannot_be_retried_after_restart(rig):
    runner, server, auth=rig
    server.overrides[0]=SystemExit('SIMULATED crash')
    with pytest.raises(SystemExit):execute(rig)
    assert len(server.chats)==len(runner.entries())==1 and runner.gate_factory().marker.exists()
    with pytest.raises(OperationalFailure,match="v2_campaign_stopped"):execute(rig)
    assert len(server.chats)==1 and not (runner.out/'results/V2-01.json').exists()


def test_missing_checkpoint_cannot_be_converted_to_retry_even_with_resume_authorization(rig):
    runner, server, auth=rig
    server.overrides[0]=SystemExit('SIMULATED crash')
    with pytest.raises(SystemExit):execute(rig)
    (runner.out/'STOP.json').unlink()  # Isolated test sabotage; canonical STOP is never touched.
    approval=load(auth);approval.update(resume_explicitly_authorized=True,resume_ledger_sha256=digest(runner.out/'ledger.jsonl'))
    auth.write_text(json.dumps(approval),encoding='utf-8')
    with pytest.raises(OperationalFailure,match="orphaned_v2_dispatch_intent_no_retry"):
        runner.run(auth,exclusive_session_attested=True,resume=True)
    assert len(server.chats)==1 and (runner.out/'STOP.json').exists()


def test_budget_twelve_cannot_be_reused_by_second_run(rig):
    runner, server, auth=rig;execute(rig)
    with pytest.raises(OperationalFailure,match='explicit_resume_required'):execute(rig)
    approval=load(auth);approval.update(resume_explicitly_authorized=True,resume_ledger_sha256=digest(runner.out/'ledger.jsonl'))
    auth.write_text(json.dumps(approval),encoding='utf-8')
    with pytest.raises(OperationalFailure,match='v2_budget_exhausted'):
        runner.run(auth,exclusive_session_attested=True,resume=True)
    assert len(server.chats)==len(runner.entries())==12


def test_v1_result_cannot_be_imported_as_v2(rig):
    runner,_,_=rig
    old=load(ROOT/'artifacts/local_model_gemma4_viability/continuation_01/01-credential-control.result.json')
    with pytest.raises(OperationalFailure,match='foreign_result_not_v2'):
        runner.protocol.validate_result(old,'SIMULATED-v2-campaign')


def test_wrapping_old_v1_pipeline_with_v2_header_cannot_bypass_campaign_time(rig):
    runner,_,_=rig;execute(rig)
    path=runner.out/'results/V2-01.json';record=load(path)
    record['pipeline']=load(ROOT/'artifacts/local_model_gemma4_viability/continuation_01/01-credential-control.result.json')
    path.write_text(json.dumps(record),encoding='utf-8')
    cp_path=runner.out/'checkpoints/V2-01.json';cp=load(cp_path);cp['result_sha256']=digest(path)
    cp_path.write_text(json.dumps(cp),encoding='utf-8')
    with pytest.raises(OperationalFailure,match='foreign_result_time_before_v2_campaign'):runner.completed_records()


def test_literal_original_and_recovered_citations_have_verified_roots(rig):
    runner,_,_=rig;execute(rig);records=runner.completed_records()
    assert records[3]['pipeline']['evidence'][0]['provenance']=='original'
    recovered=records[2]['pipeline']['evidence']
    assert len(recovered)==2 and all(e['provenance']=='deobfuscator_recovered' and e['root_source'] and e['transformation_id'] for e in recovered)


def test_rejected_provenance_citations_remain_in_literal_denominator(rig):
    runner,server,_=rig
    server.overrides[3]=lambda r,c:{**r,'message':{'role':'assistant','content':json.dumps(mock_report(c,wrong_source=True))}}
    execute(rig);score=metrics(runner)
    assert len(server.chats)==12 and score['coverage']['usable']==11
    assert score['literal_citation_fraction']==pytest.approx(8/9)
    assert score['coverage_FN_for_unusable_outputs']==1
    assert score['micro_system']['FN']==1 and score['micro_usable_outputs_only_secondary']['FN']==0


def test_no_private_reference_or_previous_answer_leaks_between_B_and_C(rig,monkeypatch):
    runner,server,_=rig
    def forbidden(*a,**k):pytest.fail('1B must never run for B/C')
    monkeypatch.setattr('app.services.pipelines.service.analyze_behaviors',forbidden)
    execute(rig)
    for i,payload in enumerate(server.chats):
        user=json.loads(payload['messages'][1]['content'])
        call=runner.protocol.calls[i]
        assert set(user)==({'original','deterministic_recovery'} if call['mode']=='C' else {'original'})
        assert not any(key in user for key in ('expected','reference','labels','B_response','detector'))
    for b,c in [(1,2),(9,10)]:
        pb,pc=server.chats[b],server.chats[c]
        assert pb['messages'][0]==pc['messages'][0]
        assert {k:v for k,v in pb.items() if k!='messages'}=={k:v for k,v in pc.items() if k!='messages'}
        assert json.loads(pb['messages'][1]['content'])['original']==json.loads(pc['messages'][1]['content'])['original']


def test_controller_never_opens_selection_or_dataset_files(rig,monkeypatch):
    runner,_,_=rig
    original_open=Path.open
    def guarded(path,*args,**kwargs):
        assert 'datasets' not in path.parts and 'freezes' not in path.parts, 'Reserved data access forbidden'
        return original_open(path,*args,**kwargs)
    monkeypatch.setattr(Path,'open',guarded)
    execute(rig)
    assert len(runner.entries())==12


def test_missing_personal_output_reviews_cannot_produce_quality_pass(rig):
    runner,_,_=rig;execute(rig)
    score=evaluate(runner.protocol,runner.completed_records(),campaign_id=runner.campaign_id,references_accepted=True)
    assert score['decision']=='pending_personal_review_no_quality_pass'
    assert score['strict_human_semantic_fraction'] is None


def test_stale_review_hash_is_not_a_human_adjudication(rig):
    runner,_,_=rig;execute(rig);records=runner.completed_records();reviews,hashes=reviews_for(runner,records)
    reviews['V2-01']['output_sha256']='old-v1-hash'
    score=evaluate(runner.protocol,records,campaign_id=runner.campaign_id,reviews=reviews,result_hashes=hashes,references_accepted=True)
    assert score['coverage']['personally_reviewed']==11 and score['decision']=='pending_personal_review_no_quality_pass'


def test_critical_semantic_invention_in_inert_text_fails_final_gate_not_a_runtime_execution(rig):
    runner,_,_=rig;execute(rig);records=runner.completed_records();reviews,hashes=reviews_for(runner,records)
    reviews['V2-01']['critical_inventions']=1
    score=evaluate(runner.protocol,records,campaign_id=runner.campaign_id,reviews=reviews,result_hashes=hashes,references_accepted=True)
    assert score['coverage']['attempted_with_results']==12 and not score['gate_checks']['no_critical_semantic_inventions_or_contradictions']
    assert score['decision']==runner.protocol.gate['quality_fail_label']


def test_two_ordinary_false_positives_collect_full_campaign_but_fail_control_budget(rig):
    runner,server,_=rig
    for index in (0,11):server.overrides[index]=lambda r,c:{**r,'message':{'role':'assistant','content':json.dumps(mock_report(c,labels=['B05']))}}
    execute(rig);score=metrics(runner)
    assert len(server.chats)==12 and score['ordinary_benign_FP']==2
    assert not score['gate_checks']['benign_FP_budget'] and score['decision']==runner.protocol.gate['quality_fail_label']


def test_no_zero_denominator_is_reported_as_perfect():
    from experiments.gemma4_v2.evaluation import rates,sufficient
    value=rates(0,0,0)
    assert value['precision'] is value['recall'] is value['F1'] is None
    assert not sufficient(value['F1'],.8)


@pytest.mark.parametrize('field,value', [('execution_authorized',False),('references_accepted',False),
    ('clarification_accepted',False),('maximum_inference_intents',13),('exclusive_session_attested',False)])
def test_missing_or_incorrect_authorization_cannot_spend_a_reservation(rig,field,value):
    runner,server,auth=rig;approval=load(auth);approval[field]=value;auth.write_text(json.dumps(approval),encoding='utf-8')
    with pytest.raises(OperationalFailure):execute(rig)
    assert server.chats==[] and not runner.out.exists()


@pytest.mark.parametrize('failure',['runtime','other_resident','disk'])
def test_preflight_runtime_residency_and_disk_fail_closed(rig,failure):
    runner,server,_=rig
    if failure=='runtime':server.version='0.30.8'
    elif failure=='other_resident':server.residents=[{'digest':'other-model'}]
    else:runner.disk_sampler=lambda p: GIB
    with pytest.raises(OperationalFailure):execute(rig)
    assert len(server.chats)==0 and (runner.out/'STOP.json').exists()


def test_campaign_OS_lock_excludes_concurrent_controller(rig):
    runner,_,_=rig
    with CampaignLock(runner.out/'campaign.lock'):
        with pytest.raises(OperationalFailure) as exc:execute(rig)
    assert exc.value.code=='v2_campaign_busy'


def test_default_transport_bounds_metadata_without_constructing_a_socket(rig):
    runner,_,_=rig
    default=Campaign(runner.protocol)
    assert default.transport_builder(None).timeout==5
    assert default.transport_builder(lambda payload: None).timeout==300

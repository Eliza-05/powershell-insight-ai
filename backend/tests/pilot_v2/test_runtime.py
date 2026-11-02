"""New v2 runtime: synthetic isolated fixtures and fake local server; no inference."""

import ast
import base64
import json
from pathlib import Path
import shutil

import pytest

from experiments.pilot_v2_runtime import artifacts as a
from experiments.pilot_v2_runtime import runner as r
from experiments.pilot_v2_runtime.resources import GIB, Monitor
from experiments.pilot_v2_runtime.transport import LocalOllama, MODEL

ROOT = Path(__file__).resolve().parents[3]


@pytest.fixture
def frozen(tmp_path):
    original = a.validate_prepared()
    names = [*original["source_hashes"], "datasets/metadata/pilot_v2_manifest.json",
             "datasets/metadata/pilot_v2_manifest.csv", "datasets/metadata/pilot_v2_annotations.json",
             "experiments/configurations/pilot_v2_thresholds_proposed.json",
             "experiments/configurations/pilot_v2_metrics_proposed.json",
             "experiments/configurations/pilot_v2_response.schema.json",
             "experiments/configurations/pilot_v2_proposed.json",
             "experiments/prompts/pilot_analysis_v2_candidate.md", "experiments/reviews/pilot_v2_human_review.json"]
    for name in names:
        target = tmp_path / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / name, target)
    instruction = tmp_path / "synthetic_test_instruction.txt"
    instruction.write_text("SYNTHETIC TEST ONLY; not an actual project approval", encoding="utf-8")
    freeze = tmp_path / "freeze"
    a.formalize(instruction, freeze, root=tmp_path)
    return tmp_path, freeze


def test_freeze_records_global_batch_without_fabricating_individual_votes(frozen):
    root, freeze = frozen
    d = a.verify_freeze(freeze, root=root)
    review = a.read(freeze / "effective_review.json")
    approval = a.read(root / "experiments/reviews/pilot_v2_owner_global_approval.json")
    assert len(d["manifest"]["cases"]) == len(review["cases"]) == 48
    assert d["frozen"] and approval["dataset_approved"] and approval["r1_criteria_approved"]
    assert approval["individual_votes_recorded"] == approval["independent_human_review_count"] == 0
    assert all(c["individual_vote"] is None and c["individual_reviewer"] is None
               and not c["individual_review_performed"] for c in review["cases"])
    with pytest.raises(FileExistsError):
        a.formalize(root / "synthetic_test_instruction.txt", freeze, root=root)


@pytest.mark.parametrize("target", ["dataset.json", "metrics.json", "schema.json", "configuration.json", "prompt_r0.md"])
def test_frozen_artifact_tampering_is_rejected(frozen, target):
    root, freeze = frozen
    with (freeze / target).open("ab") as stream:
        stream.write(b" ")
    with pytest.raises(ValueError):
        a.verify_freeze(freeze, root=root)


def test_changed_selection_source_is_rejected(frozen):
    root, freeze = frozen
    case = root / "datasets/safe_samples/pilot_v2/selection/V2-S21.ps1.txt"
    case.write_bytes(case.read_bytes()+b"# changed\n")
    with pytest.raises(ValueError):
        a.verify_freeze(freeze, root=root)


def output():
    return {"obfuscation_techniques": [], "recovered_content": [], "behaviors": [],
            "risk_label": "benign", "risk_rationale": "Synthetic test only",
            "uncertainty": {"level": "low", "uninterpretable_fragments": [], "notes": "No unresolved text"},
            "prompt_injection": {"detected": False, "snippets": [], "notes": "No attack"}, "limitations": []}


def raw_response(content=None, **outer):
    value = {"done": True, "done_reason": "stop", "prompt_eval_count": 1800, "eval_count": 100,
             "message": {"role": "assistant", "content": json.dumps(output()) if content is None else content}, **outer}
    raw = json.dumps(value)
    return {"status": 200, "raw": raw, "raw_bytes_base64": base64.b64encode(raw.encode()).decode()}


@pytest.mark.parametrize("response", [raw_response('{"a":1,"a":2}'), raw_response("NaN"),
    raw_response(json.dumps({**output(), "extra": True})), raw_response("```json\n{}\n```"),
    {"status": 500, "raw": '{"error":"bad"}'}, raw_response(done=False), raw_response(done_reason="length"),
    raw_response(prompt_eval_count=5501)])
def test_invalid_truncated_or_missing_json_is_never_repaired_or_usable(response):
    assert not r.usable(r.parse_response(response, {"num_ctx": 8192}))


@pytest.mark.parametrize("raw", ["[]", "null", '"not an object"', '{"done":true,"message":[]}'])
def test_nonobject_outer_responses_fail_without_crashing(raw):
    assert not r.usable(r.parse_response({"status":200,"raw":raw},{"num_ctx":8192}))


def test_invalid_utf8_cannot_be_repaired_into_a_valid_response():
    response=raw_response();response["raw_utf8_valid"]=False
    assert not r.usable(r.parse_response(response,{"num_ctx":8192}))


def test_valid_response_is_usable_without_mutating_raw():
    raw = raw_response()
    assert r.usable(r.parse_response(raw, {"num_ctx": 8192}))
    assert json.loads(raw["raw"])["message"]["content"] == json.dumps(output())


def test_request_projects_only_source_and_public_contract():
    config = a.read(ROOT / "experiments/configurations/pilot_v2_proposed.json")
    schema = a.read(ROOT / "experiments/configurations/pilot_v2_response.schema.json")
    prompt = r.load_prompt(ROOT / "experiments/prompts/pilot_analysis_v2_candidate.md")
    request = r.make_request("SYNTHETIC_TEXT_ONLY", prompt, config, schema)
    assert request["model"] == MODEL and len(request["messages"]) == 2
    assert request["think"] is request["stream"] is request["truncate"] is request["shift"] is False
    assert request["options"]["num_gpu"] == 0
    assert "expected_labels" not in json.dumps(request)
    assert not request.get("tools") and "reference_files" not in json.dumps(request)


def test_plans_isolate_development_and_count_repetitions():
    d = a.validate_prepared(); config = a.read(ROOT / "experiments/configurations/pilot_v2_proposed.json")
    for stage, count in (("technical", 6), ("development", 24), ("revision", 24), ("selection", 72)):
        plan = r.plan(stage, d["manifest"]["cases"], config)
        assert len(plan) == count
        assert all(c["split"] == ("selection" if stage == "selection" else "development") for c, _ in plan)
        if stage == "selection":
            assert len({(c["case_id"], rep) for c, rep in plan}) == 72
            assert plan == r.plan(stage, d["manifest"]["cases"], config)


def test_transport_rejects_external_paths_and_other_models_before_network():
    with pytest.raises(ValueError):
        LocalOllama().request("https://example.invalid")
    with pytest.raises(ValueError):
        LocalOllama().request("pull", {"model": "unauthorized-model"})


def test_resource_breach_cancels_without_closing_any_application():
    cancelled = []
    monitor = Monitor(lambda: cancelled.append(True), sampler=lambda: {
        "available_bytes": GIB, "commit_available_bytes": 10*GIB, "commit_used_bytes": GIB, "processes": []})
    monitor.collect()
    assert monitor.violated and cancelled == [True]


def test_model_process_tree_measurement_includes_llama_server_child():
    monitor=Monitor(lambda:None,sampler=lambda:{"available_bytes":8*GIB,"commit_available_bytes":8*GIB,
        "commit_used_bytes":GIB,"processes":[{"name":"llama-server.exe","is_ollama_runtime":True,
        "working_set":3*GIB,"private":5*GIB}]})
    monitor.collect()
    assert monitor.summary()["maximum_single_ollama_working_set_bytes"]==3*GIB
    assert monitor.summary()["maximum_single_ollama_private_bytes"]==5*GIB


def test_runtime_does_not_contain_sample_execution_or_dynamic_eval_sinks():
    for path in (ROOT / "experiments/pilot_v2_runtime").glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                assert not {n.name.split(".")[0] for n in node.names} & {"subprocess", "win32com", "importlib"}
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                assert node.func.id not in {"eval", "exec", "compile", "__import__"}


def test_lock_is_exclusive_and_does_not_remove_existing_owner_lock(tmp_path):
    with r.exclusive_lock(tmp_path):
        with pytest.raises(FileExistsError):
            with r.exclusive_lock(tmp_path):
                pytest.fail("second experiment acquired the lock")
        assert (tmp_path / "experiments/cache/pilot_v2_runtime.lock").exists()
    assert not (tmp_path / "experiments/cache/pilot_v2_runtime.lock").exists()


class FakeOllama:
    def __init__(self, bad=False):
        self.chat_calls=0
        self.bad=bad

    def cancel(self):
        pass

    def json(self, endpoint, payload=None):
        if endpoint=="version": return {"version":"synthetic-test-only"}
        if endpoint=="show": return {"thinking":{"values":[False,True]}}
        model={"name":MODEL,"digest":"synthetic-test-digest","context_length":8192,"size_vram":0}
        return {"models":[model]}

    def request(self, endpoint, payload):
        assert endpoint=="chat"
        self.chat_calls+=1
        return raw_response("invalid JSON" if self.bad else None)


def fake_resources():
    return {"available_bytes":12*GIB,"commit_available_bytes":12*GIB,"commit_used_bytes":GIB,"processes":[]}


def test_runner_records_each_attempt_once_and_stops_after_two_errors(frozen, monkeypatch):
    root,freeze=frozen
    dataset=a.verify_freeze(freeze,root=root)
    monkeypatch.setattr(r,"verify_freeze",lambda _:dataset)
    monkeypatch.setattr(r,"ROOT",root)
    original_lock=r.exclusive_lock
    monkeypatch.setattr(r,"exclusive_lock",lambda:original_lock(root))
    client=FakeOllama(bad=True)
    run=root/"experiments/results/raw/pilot_v2/synthetic_run"
    summary=r.run_stage(freeze,run,"technical",client=client,sampler=fake_resources)
    assert client.chat_calls==summary["attempted"]==2
    assert summary["planned"]==6 and not summary["complete"]
    assert summary["stopped_reason"]=="two_consecutive_operational_failures"
    assert len(r.dispatched(run))==2
    assert len(list((run/"technical").glob("*.request.json")))==2
    assert len(list((run/"technical").glob("*.result.json")))==2
    with pytest.raises(FileExistsError):
        r.run_stage(freeze,run,"technical",client=client,sampler=fake_resources)
    assert client.chat_calls==2


def test_development_and_selection_cannot_skip_prerequisites(frozen, monkeypatch):
    root,freeze=frozen
    monkeypatch.setattr(r,"verify_freeze",lambda path:a.verify_freeze(path,root=root))
    monkeypatch.setattr(r,"ROOT",root)
    with pytest.raises(ValueError):
        r.freeze_selection(freeze,root/"experiments/results/raw/pilot_v2/synthetic_run",freeze/"prompt_r0.md","synthetic test")


def test_historical_result_directory_cannot_be_used_by_runtime():
    with pytest.raises(ValueError):
        r.assert_run_namespace(ROOT/"experiments/results/pilot/pilot-v1_20261101T001806Z")


def test_http_redirects_and_sample_urls_are_never_followed(monkeypatch):
    from experiments.pilot_v2_runtime import transport
    connections=[]

    class Response:
        status=302
        def read(self): return b'{"untrusted":"https://example.invalid/run.ps1"}'

    class Connection:
        def __init__(self,host,port,timeout):
            assert host=="127.0.0.1" and port==11434
            connections.append(self)
        def request(self,method,path,body,headers):
            assert method=="POST" and path=="/api/chat"
            assert b'https://example.invalid' in body
        def getresponse(self): return Response()
        def close(self): pass

    monkeypatch.setattr(transport.http.client,"HTTPConnection",Connection)
    result=LocalOllama().request("chat",{"model":MODEL,"messages":[{"role":"user","content":"https://example.invalid/run.ps1"}]})
    assert result["status"]==302 and len(connections)==1
    assert base64.b64decode(result["raw_bytes_base64"])==result["raw"].encode()


def test_authorization_cannot_be_reused_for_a_new_experiment(frozen,monkeypatch):
    root,freeze=frozen
    monkeypatch.setattr(r,"ROOT",root)
    run=root/"experiments/results/raw/pilot_v2/first_synthetic_run"
    r.bind_authorized_execution(run,freeze)
    r.bind_authorized_execution(run,freeze)
    with pytest.raises(ValueError):
        r.bind_authorized_execution(root/"experiments/results/raw/pilot_v2/second_synthetic_run",freeze)


def test_global_batch_acceptance_also_blocks_the_old_draft_writer(tmp_path,monkeypatch):
    from experiments.pilot_v2 import build_dataset as author
    a.write_new(tmp_path/"experiments/reviews/pilot_v2_owner_global_approval.json",{"dataset_approved":True})
    monkeypatch.setattr(author,"ROOT",tmp_path)
    monkeypatch.setattr(author,"build_assets",lambda:{"must_not_be_written":b"no"})
    monkeypatch.setattr("sys.argv",["draft-writer","--write"])
    with pytest.raises(SystemExit) as exc:author.main()
    assert exc.value.code==2 and not (tmp_path/"must_not_be_written").exists()

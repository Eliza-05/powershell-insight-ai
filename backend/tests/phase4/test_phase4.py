"""No-network simulations in isolated copies; no canonical approval or inference."""
from copy import deepcopy
import json
from pathlib import Path
import shutil
import socket

import pytest

from app.services.pipelines.resources import InferenceGate, OperationalFailure
from app.services.pipelines.context import canonical, sha
from experiments.phase4.common import ROOT, OUT, now, digest, load, save
from experiments.phase4.protocol import Proposal
from experiments.phase4.campaign import Campaign
from experiments.phase4.evaluation import evaluate, holm_two
from experiments.phase4.metrics import classification, paired_H1, paired_H2
from experiments.phase4.independence import normalized_tokens, audit

GIB = 1024 ** 3


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    monkeypatch.setattr(socket, "create_connection", lambda *a, **k: pytest.fail("Real network is forbidden in Phase 4 simulations"))


@pytest.fixture
def proposal(tmp_path):
    original = load(OUT / "CANDIDATE_MANIFEST.json")
    for name in original["files_sha256"]:
        target = tmp_path / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / name, target)
    out = tmp_path / "artifacts/phase4_preparation"
    shutil.copyfile(OUT / "CANDIDATE_MANIFEST.json", out / "CANDIDATE_MANIFEST.json")
    return Proposal(tmp_path, out)


def authorize_simulation(p):
    review = {"simulation_only": True, "candidate_sha256": p.candidate_hash,
        "reviewer_type": "human_personal", "reviewer": "SIMULATED TEST FIXTURE; NOT A REAL ADJUDICATOR",
        "reviewed_at": now(), "references_approved": True, "semantic_independence_approved": True, "safety_approved": True,
        "case_reviews": [{"id": c["id"], "script_sha256": c["script_sha256"],
            "reference_sha256": sha(canonical(c)), "approved": True} for c in p.cases]}
    path = p.out / "SIMULATED_REFERENCE_REVIEW.json"; save(path, review)
    p.seal(path)
    freeze = load(p.out / "FREEZE.json")
    auth = {"simulation_only": True, "execution_authorized": True, "maximum_real_LLM_intents": 32,
        "source": "explicit_future_owner_execution_authorization", "owner_statement": "SIMULATED ONLY",
        "exclusive_session_attested": True, "authorized_at": now(), "freeze_sha256": digest(p.out / "FREEZE.json"),
        "reference_review_sha256": freeze["reference_review_sha256"]}
    path = p.out / "SIMULATED_EXECUTION_AUTHORIZATION.json"; save(path, auth)
    return path


class Server:
    def __init__(self, p):
        self.p = p; self.chats = []; self.residents = []; self.free = 20 * GIB
        self.overrides = {}; self.on_chat = None

    def memory(self):
        return {"available_bytes": self.free, "commit_available_bytes": 24 * GIB,
            "commit_limit_bytes": 50 * GIB, "commit_used_bytes": 26 * GIB, "physical_total_bytes": 32 * GIB,
            "processes": [{"name": "ollama.exe", "is_ollama_runtime": True, "private": GIB, "working_set": GIB}]}

    def metadata(self):
        return {"version": {"version": "0.40.13"}, "tags": {"models": [{"name": self.p.settings.model,
            "digest": self.p.settings.expected_digest, "details": {"quantization_level": "Q4_K_M"}}]},
            "ps": {"models": deepcopy(self.residents)}, "show": {"capabilities": ["completion"],
                "model_info": {"qwen2.context_length": 32768}}, "memory": self.memory(), "disk_free_bytes": 30 * GIB}

    def transport(self, callback):
        server = self
        class Transport:
            last_response = None
            def cancel(self): pass
            def json(self, endpoint, payload=None):
                if endpoint != "chat": return server.metadata()[endpoint]
                callback(payload)
                i = len(server.chats); server.chats.append(deepcopy(payload))
                server.residents = [{"digest": server.p.settings.expected_digest, "context_length": 8192, "size_vram": 0}]
                report = {"behaviors": [], "obfuscation_techniques": [], "recovered_content": [],
                    "risk_label": "unknown", "risk_rationale": "SIMULATED, no semantic accuracy claim",
                    "uncertainty": {"level": "high", "notes": "SIMULATED", "uninterpretable_fragments": []},
                    "prompt_injection": {"detected": False, "snippets": [], "notes": "SIMULATED"}, "limitations": ["SIMULATED"]}
                response = {"model": server.p.settings.model, "done": True, "done_reason": "stop",
                    "message": {"content": json.dumps(report)}, "prompt_eval_count": 1500, "eval_count": 250}
                override = server.overrides.get(i)
                if isinstance(override, Exception): raise override
                if override: response.update(override)
                if server.on_chat: server.on_chat(i, response)
                self.last_response = {"status": 200, "raw_utf8": json.dumps(response), "transport_read_complete": True}
                return response
        return Transport()


def campaign(p, server):
    return Campaign(p, transport_builder=server.transport, sampler=server.memory,
        metadata=server.metadata, gate_factory=lambda: InferenceGate(p.out / "SIMULATED_GATE.lock"))


def test_canonical_is_proposal_not_an_approved_or_executed_study():
    p = Proposal()
    assert not (OUT / "FREEZE.json").exists() and not (OUT / "execution").exists()
    assert load(OUT / "reference_review.template.json")["references_approved"] is False
    assert load(OUT / "execution_authorization.template.json")["execution_authorized"] is False
    assert len(p.cases) == 16 and len(p.sequence) == 48
    assert sum(s["mode"] != "A" for s in p.sequence) == 32
    assert sum(bool(c["verified_1A_sources"]) for c in p.cases) == 8
    assert sum(c["expected_labels"] is None for c in p.cases) == 2


def test_preparation_cannot_authorize_any_real_transport(proposal):
    server = Server(proposal); c = campaign(proposal, server)
    auth = proposal.out / "FALSE_AUTH.json"; save(auth, {"execution_authorized": False})
    with pytest.raises(OperationalFailure, match="personal_reference_freeze"): c.run(auth)
    assert server.chats == [] and not c.out.exists()


def test_all_48_results_order_budget_and_low_quality_completion(proposal):
    auth = authorize_simulation(proposal); server = Server(proposal); c = campaign(proposal, server)
    assert c.run(auth) == {"records": 48, "LLM_intents": 32}
    assert len(server.chats) == len(c.intents()) == 32
    assert len(list((c.out / "results").glob("*.json"))) == 48
    assert c.existing() == proposal.sequence
    for step, payload in zip([s for s in proposal.sequence if s["mode"] != "A"], server.chats):
        case = proposal.case(step["unit"])
        assert sha(canonical(payload)) == case[step["mode"] + "_request_sha256"]
        assert "think" not in payload and "tools" not in payload
        data = json.loads(payload["messages"][1]["content"])
        assert set(data) == ({"original", "deterministic_recovery"} if step["mode"] == "C" else {"original"})
    result = evaluate(proposal)
    assert result["operationally_complete"]
    assert result["classification"]["B"]["micro"]["F1"] == 0
    assert result["H2"]["status"].startswith("pending_")
    assert result["hypotheses_automatically_accepted"] is False
    with pytest.raises(OperationalFailure, match="no_silent_restart"): c.run(auth)
    assert len(server.chats) == 32
    last = next(s for s in reversed(proposal.sequence) if s["mode"] != "A")
    c.active = (proposal.case(last["unit"]), last["mode"])
    with pytest.raises(OperationalFailure, match="phase4_budget_exhausted"): c.reserve(server.chats[-1])


@pytest.mark.parametrize("kind", ["JSON", "provenance", "length"])
def test_terminal_quality_errors_continue_without_repairs(proposal, kind):
    auth = authorize_simulation(proposal); server = Server(proposal)
    if kind == "JSON": server.overrides[0] = {"message": {"content": "{invalid"}}
    elif kind == "length": server.overrides[0] = {"done_reason": "length"}
    else:
        def wrong(index, response):
            if index == 0:
                report = json.loads(response["message"]["content"])
                report["behaviors"] = [{"behavior_id": "B05", "confidence": "low", "explanation": "SIMULATED wrong citation",
                    "evidence": [{"source_id": "T9999", "snippet": "invented"}]}]
                response["message"]["content"] = json.dumps(report)
        server.on_chat = wrong
    c = campaign(proposal, server); c.run(auth)
    assert len(server.chats) == 32
    first = next(s for s in proposal.sequence if s["mode"] != "A")
    r = load(c.out / "results" / (first["unit"] + "-" + first["mode"] + ".json"))
    assert r["pipeline"]["status"] == "error" and r["pipeline"]["llm"] is None
    result = evaluate(proposal)
    assert result["classification"][first["mode"]]["unusable"] == 1


@pytest.mark.parametrize("kind", ["tool", "timeout", "margin"])
def test_critical_failure_spends_one_intent_and_stops(proposal, kind):
    auth = authorize_simulation(proposal); server = Server(proposal)
    if kind == "tool": server.overrides[0] = {"message": {"content": "{}", "tool_calls": [{"name": "forbidden"}]}}
    elif kind == "timeout": server.overrides[0] = OperationalFailure("timeout", "SIMULATED")
    else: server.on_chat = lambda *_: setattr(server, "free", GIB)
    c = campaign(proposal, server)
    with pytest.raises(OperationalFailure): c.run(auth)
    assert len(server.chats) == len(c.intents()) == 1
    assert (c.out / "STOP.json").exists()
    with pytest.raises(OperationalFailure): c.run(auth)
    assert len(server.chats) == 1


def test_low_memory_and_modified_input_dispatch_nothing(proposal):
    auth = authorize_simulation(proposal); server = Server(proposal); server.free = GIB
    c = campaign(proposal, server)
    with pytest.raises(OperationalFailure, match="insufficient_memory"): c.run(auth)
    assert not server.chats and c.intents() == []


def test_hash_change_prevents_client_creation(proposal):
    auth = authorize_simulation(proposal); server = Server(proposal)
    path = proposal.plan / proposal.cases[0]["script_file"]; path.write_text("modified", encoding="utf-8")
    with pytest.raises(OperationalFailure, match="candidate_file_changed"): campaign(proposal, server).run(auth)
    assert not server.chats


def test_authorization_change_cannot_spend_another_intent(proposal):
    auth = authorize_simulation(proposal); server = Server(proposal)
    def change_auth(index, response):
        if index == 0: auth.write_text('{"execution_authorized":false}', encoding="utf-8")
    server.on_chat = change_auth
    c = campaign(proposal, server)
    with pytest.raises(OperationalFailure): c.run(auth)
    assert len(c.intents()) == len(server.chats) == 1


def test_orphan_intent_is_spent_not_retried(proposal):
    auth = authorize_simulation(proposal); server = Server(proposal); c = campaign(proposal, server)
    c.out.mkdir(); save(c.out / "campaign.json", {"at": now(), "candidate_sha256": proposal.candidate_hash})
    step = next(s for s in proposal.sequence if s["mode"] != "A"); case = proposal.case(step["unit"])
    (c.out / "ledger.jsonl").write_text(canonical({"number": 1, **step, "candidate_sha256": proposal.candidate_hash,
        "request_sha256": case[step["mode"] + "_request_sha256"]}) + "\n", encoding="utf-8")
    with pytest.raises(OperationalFailure, match="orphaned_spent_intent"): c.existing()
    assert len(c.intents()) == 1 and not server.chats


def test_reference_review_cannot_be_implicit_or_partial(proposal):
    path = proposal.out / "BAD_REVIEW.json"
    save(path, {"candidate_sha256": proposal.candidate_hash, "reviewer_type": "AI_assistant", "reviewer": "SIMULATED"})
    with pytest.raises(OperationalFailure): proposal.seal(path)
    assert not (proposal.out / "FREEZE.json").exists()


def test_metric_denominators_rejected_empty_indeterminate_and_macro():
    rows = [{"expected": [], "predicted": None}, {"expected": [], "predicted": []},
            {"expected": ["B03", "B04"], "predicted": ["B03"]}, {"expected": None, "predicted": []}]
    result = classification(rows)
    assert result["exact_sets"] == {"correct": 1, "denominator": 3}
    assert result["micro"]["TP"] == 1 and result["micro"]["FN"] == 1
    assert result["macro_denominator"] == 2
    assert result["macro_reference_supported_classes"]["recall"] == .5
    assert result["unusable"] == 1 and result["indeterminate_reference_count"] == 1


def test_exact_paired_H1_swaps_keep_cluster_dependence():
    pairs = [({"expected": ["B03"], "predicted": [], "cluster": str(i)},
              {"expected": ["B03"], "predicted": ["B03"], "cluster": str(i)}) for i in range(2)]
    result = paired_H1(pairs)
    assert result["delta_micro_F1_C_minus_B"] == 1 and result["assignments"] == 4
    assert result["exact_swap_p_one_sided_C_greater"] == .25
    pairs[1][0]["cluster"] = pairs[1][1]["cluster"] = "0"
    assert paired_H1(pairs)["assignments"] == 2
    assert holm_two(.25, .5) == {"H1": .5, "H2": .5}


def test_H2_never_uses_automatic_literal_validity_as_semantic_review():
    b = {"unit": "toy", "mode": "B", "cluster": "x", "expected": [], "predicted": [],
         "raw_output": "SIMULATED factual claim", "output_started_at": now()}
    c = {**b, "mode": "C"}
    assert paired_H2([(b, c)], {}, {})["status"].startswith("pending_")
    hashes = {"toy-B": "a" * 64, "toy-C": "b" * 64}
    reviews = {}
    for mode, code in (("B", "insufficient"), ("C", "individual")):
        reviews["toy-" + mode] = {"unit": "toy", "mode": mode, "reviewer_type": "human_personal", "human_confirmed": True,
            "reviewer": "SIMULATED TEST FIXTURE", "reviewed_at": now(), "result_sha256": hashes["toy-" + mode],
            "inventory_complete": True, "invented_reconstructions": 0, "altered_reconstructions": 0,
            "risk_uncertainty_notes": "SIMULATED", "claims": [{"claim_id": "q1", "proposition": "SIMULATED proposition",
                "quote": "factual claim", "strict_support": code, "permissive_context_support": True,
                "source_ids": ["original"], "rationale": "SIMULATED"}]}
    result = paired_H2([(b, c)], reviews, hashes)
    assert result["delta_mean_count_C_minus_B"] == -1
    reviews["toy-C"]["human_confirmed"] = False
    assert paired_H2([(b, c)], reviews, hashes)["status"].startswith("pending_")


def test_novelty_detects_identifier_and_literal_only_changes(tmp_path):
    assert normalized_tokens("$a='one'; Get-Service -Name $a") == normalized_tokens("$renamed='two'; Get-Service -Name $renamed")
    path = tmp_path / "datasets/safe_samples/old.ps1.txt"; path.parent.mkdir(parents=True)
    path.write_text("$a='one'; Get-Service -Name $a", encoding="utf-8")
    result = audit([{"id": "test", "script": "$renamed='two'; Get-Service -Name $renamed", "novel_logic": "SIMULATED"}], tmp_path)
    assert result["automatic_exact_or_program_duplicate_found"]


def test_novelty_checks_new_decoded_view_against_prior_program(tmp_path):
    import base64
    script = "Get-Service -Name 'earlier'"
    path = tmp_path / "datasets/safe_samples/old.ps1.txt"; path.parent.mkdir(parents=True)
    path.write_text(script, encoding="utf-8")
    encoded = base64.b64encode(script.encode("utf-16-le")).decode()
    wrapped = "powershell -EncodedCommand " + encoded
    result = audit([{"id": "test", "script": wrapped, "novel_logic": "SIMULATED"}], tmp_path)
    assert result["automatic_exact_or_program_duplicate_found"]

"""Sequential A/B/C controller. No generation until a separate owner-authorized freeze."""
from __future__ import annotations

import os
from pathlib import Path
from uuid import uuid4

from packaging.version import Version

from app.schemas.pipeline import PipelineResult
from app.services.pipelines.context import canonical, sha
from app.services.pipelines.resources import InferenceGate
from app.services.pipelines.resource_policy import resource_admission
from experiments.gemma4_v2.runner import CampaignLock
from experiments.phase4.resources import snapshot
from experiments.phase4.common import load, save, require, digest, now
from experiments.phase4.protocol import Proposal
from experiments.phase4.profile import transport_for, service_for
from experiments.phase4.storage import storage_snapshot


def native_state(settings=None, *, storage_binding=None):
    # Metadata only, bounded loopback transport. Model path can be on another drive;
    # measure that location explicitly rather than assuming workspace storage.
    if settings is None:
        from app.api.application import load_pipeline_settings
        settings = load_pipeline_settings()
    client = transport_for(settings, timeout=3)
    return {"at": now(), "version": client.json("version"), "tags": client.json("tags"),
        "ps": client.json("ps"), "show": client.json("show", {"model": settings.model}),
        "memory": snapshot(), **storage_snapshot(storage_binding)}


class Campaign:
    def __init__(self, proposal=None, *, transport_builder=None, sampler=snapshot, metadata=None,
                 gate_factory=InferenceGate):
        self.p = proposal or Proposal()
        self.out = self.p.out / "execution"
        self.transport_builder = transport_builder or (lambda callback: transport_for(self.p.settings,
            authorize_dispatch=callback, timeout=self.p.settings.timeout_seconds))
        self.sampler, self.metadata, self.gate_factory = sampler, metadata or (lambda: native_state(
            self.p.settings, storage_binding=self.p.configuration.get("model_storage_binding"))), gate_factory
        self.active = None
        self.authorization_path = None
        self.authorization_hash = None

    def intents(self):
        path = self.out / "ledger.jsonl"
        rows = [load_line(line) for line in path.read_text(encoding="utf-8").splitlines()] if path.exists() else []
        planned = [s for s in self.p.sequence if s["mode"] != "A"]
        require(len(rows) <= 32, "phase4_budget_exceeded")
        for i, row in enumerate(rows):
            step = planned[i]
            case = self.p.case(step["unit"])
            require(row.get("number") == i + 1 and row.get("unit") == step["unit"] and row.get("mode") == step["mode"]
                and row.get("candidate_sha256") == self.p.candidate_hash
                and row.get("request_sha256") == case[step["mode"] + "_request_sha256"], "intent_ledger_corrupt")
        return rows

    def preflight(self, *, first):
        self.p.verify_candidate()
        s = self.metadata()
        cfg = self.p.settings
        s["passed"] = False
        try:
            require(Version(s["version"]["version"]) >= Version("0.5.0"), "incompatible_runtime")
            installed = [m for m in s["tags"]["models"] if m["name"] == cfg.model]
            require(len(installed) == 1 and installed[0]["digest"] == cfg.expected_digest, "installed_digest_mismatch")
            require(installed[0]["details"]["quantization_level"] == "Q4_K_M", "quantization_mismatch")
            residents = s["ps"]["models"]
            require(not first or not residents, "first_dispatch_requires_idle_no_residents")
            require(len(residents) <= 1 and all(m["digest"] == cfg.expected_digest for m in residents), "other_model_resident")
            require("completion" in s["show"].get("capabilities", []) and "thinking" not in s["show"].get("capabilities", []), "wrong_capabilities")
            info = s["show"]["model_info"]
            architecture = info.get("general.architecture", "qwen2" if cfg.model == "qwen2.5-coder:14b" else "qwen3moe")
            require(info.get(architecture + ".context_length", 0) >= cfg.options.num_ctx, "context_not_supported")
            warm = bool(residents) and residents[0].get("context_length") == cfg.options.num_ctx and residents[0].get("size_vram") == 0
            needed = cfg.minimum_margin_bytes + (cfg.loaded_growth_reserve_bytes if warm else cfg.unloaded_reserve_bytes)
            s["required_available_bytes"] = needed
            memory = s["memory"]
            require(all(type(memory.get(k)) is int and memory[k] >= 0 for k in ("available_bytes", "commit_available_bytes", "commit_limit_bytes", "physical_total_bytes")), "resource_snapshot_unavailable")
            s["resource_admission"] = resource_admission(memory, needed)
            require(s["resource_admission"]["allowed"], "insufficient_memory")
            require(s["disk_free_bytes"] >= self.p.configuration["disk_free_minimum_bytes"], "insufficient_disk")
            runtime = [p for p in memory["processes"] if p.get("is_ollama_runtime")]
            linux = str(memory.get("collector", "")).startswith("linux-")
            fields = ("rss_bytes",) if linux else ("private", "working_set")
            require(runtime and all(not p.get("counters_unavailable") and
                all(type(p.get(k)) is int and p[k] >= 0 for k in fields) for p in runtime), "process_monitor_unavailable")
            require(not self.gate_factory().marker.exists(), "interrupted_dispatch_circuit")
            s["passed"] = True
        finally:
            save(self.out / "preflights" / (str(uuid4()) + ".json"), s)

    def reserve(self, payload):
        self.p.verify_candidate()
        require(digest(self.authorization_path) == self.authorization_hash, "active_authorization_changed")
        self.p.authorize(self.authorization_path)
        require(self.active is not None and not (self.out / "STOP.json").exists(), "no_active_phase4_dispatch")
        rows = self.intents()
        require(len(rows) < 32, "phase4_budget_exhausted")
        case, mode = self.active
        next_step = [s for s in self.p.sequence if s["mode"] != "A"][len(rows)]
        require(next_step == {"unit": case["id"], "mode": mode} and sha(canonical(payload)) == case[mode + "_request_sha256"], "unexpected_dispatch_order_or_payload")
        marker = load(self.gate_factory().marker)
        require(marker.get("state") == "dispatch_intent" and marker.get("pid") == os.getpid()
                and marker.get("request_sha256") == case[mode + "_request_sha256"], "owned_application_gate_required")
        row = {"number": len(rows) + 1, "unit": case["id"], "mode": mode, "at": now(),
            "candidate_sha256": self.p.candidate_hash, "request_sha256": case[mode + "_request_sha256"]}
        with (self.out / "ledger.jsonl").open("a", encoding="utf-8", newline="\n") as stream:
            stream.write(canonical(row) + "\n"); stream.flush(); os.fsync(stream.fileno())

    def existing(self):
        completed = []
        for step in self.p.sequence:
            path = self.out / "results" / (step["unit"] + "-" + step["mode"] + ".json")
            if not path.exists(): break
            record = load(path)
            cp = load(self.out / "checkpoints" / path.name)
            require(cp["result_sha256"] == digest(path) and record["candidate_sha256"] == self.p.candidate_hash, "checkpoint_mismatch")
            case = self.p.case(step["unit"])
            result = PipelineResult.model_validate(record["pipeline"])
            require(record["unit"] == step["unit"] and result.configuration == step["mode"]
                    and result.input_sha256 == case["script_sha256"], "result_identity_mismatch")
            from datetime import datetime
            require(datetime.fromisoformat(result.started_at) >= datetime.fromisoformat(load(self.out / "campaign.json")["at"]), "result_predates_campaign")
            if step["mode"] != "A":
                _, _, request = self.p.context(case, step["mode"])
                require(result.operational.get("request") == request and
                    result.operational.get("request_sha256") == case[step["mode"] + "_request_sha256"], "result_request_mismatch")
            completed.append(step)
        remaining = self.p.sequence[len(completed):]
        require(not any((self.out / "results" / (s["unit"] + "-" + s["mode"] + ".json")).exists() for s in remaining), "noncontiguous_results")
        spent = self.intents()
        done_llm = [s for s in completed if s["mode"] != "A"]
        require(len(spent) == len(done_llm), "orphaned_spent_intent_never_retry")
        ids = [load(self.out / "results" / (s["unit"] + "-" + s["mode"] + ".json"))["pipeline"]["run_id"] for s in completed]
        require(len(ids) == len(set(ids)), "duplicate_pipeline_run_id")
        return completed

    def hard_failure(self, pipeline):
        if pipeline["configuration"] == "A":
            return None if pipeline["status"] in {"completed", "partial"} else "static_A_failure"
        op = pipeline["operational"]
        reply = op.get("response", {})
        if op.get("circuit_blocked") or op.get("resources", {}).get("margin_violated"): return "critical_resource_or_transport_interrupt"
        if reply.get("model") != self.p.settings.model: return "response_model_mismatch"
        if reply.get("message", {}).get("tool_calls") or reply.get("message", {}).get("thinking"): return "unauthorized_capability"
        for error in pipeline.get("errors", []):
            ordinary = (error["code"] == "invalid_response" and error["stage"] == "response") or (
                error["code"] == "evidence_check_incoherent" and error["stage"] == "evidence_check")
            length = error["code"] == "truncated_response" and reply.get("done") is True and reply.get("done_reason") == "length"
            if not ordinary and not length: return error["code"]
        if reply.get("done") is not True or reply.get("done_reason") not in {"stop", "length"}: return "nonterminal_response"
        counts = [reply.get("prompt_eval_count"), reply.get("eval_count")]
        if any(type(v) is not int or v < 0 for v in counts): return "token_counts_unavailable"
        if sum(counts) > self.p.settings.options.num_ctx or counts[1] > self.p.settings.options.num_predict:
            return "effective_token_limit_exceeded"
        return None

    def run(self, authorization_path, *, resume=False):
        self.p.authorize(authorization_path, resume=resume, ledger=self.out / "ledger.jsonl")
        self.authorization_path = Path(authorization_path)
        self.authorization_hash = digest(self.authorization_path)
        self.out.mkdir(parents=True, exist_ok=True)
        with CampaignLock(self.out / "campaign.lock"):
            require(not (self.out / "STOP.json").exists(), "critical_stop_not_resumable")
            campaign = self.out / "campaign.json"
            if campaign.exists():
                require(resume, "no_silent_restart_or_resume")
                require(load(campaign)["candidate_sha256"] == self.p.candidate_hash, "foreign_campaign")
            else:
                require(not resume and not self.intents(), "nothing_authorized_to_resume")
                save(campaign, {"at": now(), "candidate_sha256": self.p.candidate_hash,
                    "freeze_sha256": digest(self.p.out / "FREEZE.json"), "maximum_real_LLM_intents": 32})
            try:
                completed = self.existing()
                require(len(completed) < 48, "campaign_already_complete")
                for step in self.p.sequence[len(completed):]:
                    self.p.verify_candidate()
                    case, mode = self.p.case(step["unit"]), step["mode"]
                    script = (self.p.plan / case["script_file"]).read_text(encoding="utf-8")
                    require(sha(script) == case["script_sha256"], "sample_hash_mismatch")
                    if mode != "A":
                        self.p.context(case, mode)
                        with self.gate_factory(): self.preflight(first=not self.intents())
                        self.active = (case, mode)
                    service = service_for(self.p.settings, sampler=self.sampler, gate_factory=self.gate_factory,
                        transport_factory=lambda: self.transport_builder(self.reserve))
                    result = service.analyze(script, mode).model_dump(mode="json")
                    path = self.out / "results" / (case["id"] + "-" + mode + ".json")
                    save(path, {"unit": case["id"], "mode": mode, "candidate_sha256": self.p.candidate_hash,
                        "authorization_sha256": self.authorization_hash, "pipeline": result})
                    save(self.out / "checkpoints" / path.name, {"result_sha256": digest(path)})
                    if mode != "A":
                        require(len(self.intents()) == sum(s["mode"] != "A" for s in completed) + 1, "dispatch_not_reserved")
                    completed.append(step)
                    reason = self.hard_failure(result)
                    require(reason is None, reason or "critical_failure")
                    self.active = None
            except BaseException as exc:
                save(self.out / "STOP.json", {"at": now(), "reason": getattr(exc, "code", "controller_interrupted_or_storage_failure"),
                    "detail": str(exc), "automatic_resume": False})
                raise
            finally: self.active = None
            save(self.out / "COMPLETED.json", {"at": now(), "A_records": 16, "LLM_intents": len(self.intents()),
                "operationally_complete": len(completed) == 48, "scientific_review_complete": False,
                "quality_is_not_a_completion_gate": True})
        return {"records": len(completed), "LLM_intents": len(self.intents())}


def load_line(text):
    from app.services.pipelines.validation import strict_json
    return strict_json(text)

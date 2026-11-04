"""Sequential, fail-closed v2 execution. No cloud, pull or sample execution paths."""
from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
import shutil
from uuid import uuid4

from packaging.version import Version, InvalidVersion

from app.services.llm.gemma4 import Gemma4Adapter, Gemma4Transport
from app.services.pipelines.context import canonical, sha
from app.services.pipelines.resources import InferenceGate, OperationalFailure
from app.services.pipelines.service import AnalysisService
from app.services.pipelines.validation import strict_json
from experiments.pilot_v2_runtime.resources import snapshot
from experiments.gemma4_v2.protocol import Protocol, VERSION, FREEZE_SHA, digest, load, now, require, save


class CampaignLock:
    """Separate OS lock; does not nest the application gate's process-wide lock."""
    def __init__(self, path):
        self.path = Path(path)

    def __enter__(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.handle = self.path.open("a+b")
        if self.handle.tell() == 0:
            self.handle.write(b"0"); self.handle.flush()
        self.handle.seek(0)
        try:
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(self.handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(self.handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except Exception:
            self.handle.close()
            raise OperationalFailure("v2_campaign_busy", "Another v2 controller owns the OS lock") from None
        return self

    def __exit__(self, *_):
        self.handle.close()


def native_sample():
    value = snapshot()
    runtime = [p for p in value.get("processes", []) if p.get("is_ollama_runtime")]
    require(runtime and any("ollama" in p["name"].lower() for p in runtime), "runtime_process_inventory_unavailable")
    require(all(type(p.get("private")) is int and type(p.get("working_set")) is int
                and not p.get("counters_unavailable") for p in runtime), "runtime_process_counters_unavailable")
    return value


class Campaign:
    def __init__(self, protocol=None, *, transport_builder=None, sampler=None,
                 gate_factory=InferenceGate, disk_sampler=None):
        self.protocol = protocol or Protocol()
        self.out = self.protocol.execution
        self.transport_builder = transport_builder or (lambda callback: Gemma4Transport(
            authorize_dispatch=callback, timeout=5 if callback is None else 300))
        self.sampler = sampler or native_sample
        self.gate_factory = gate_factory
        self.disk_sampler = disk_sampler or (lambda path: shutil.disk_usage(path).free)
        self.active = None
        self.metadata = None
        self.campaign_id = None
        self.last_preflight = None
        self.authorization_path = None
        self.authorization_sha256 = None

    def entries(self):
        path = self.out / "ledger.jsonl"
        rows = [strict_json(line) for line in path.read_text(encoding="utf-8").splitlines()] if path.exists() else []
        require(len(rows) <= 12, "v2_budget_exceeded")
        for i, row in enumerate(rows):
            call = self.protocol.calls[i]
            require(row.get("attempt") == i + 1 and row.get("call_id") == call["call_id"]
                    and row.get("campaign_id") == self.campaign_id
                    and row.get("freeze_sha256") == FREEZE_SHA
                    and row.get("request_sha256") == call["request_sha256_canonical"], "v2_ledger_corrupt_or_foreign")
        return rows

    def completed_records(self):
        records = []
        for row in self.entries():
            result_path = self.out / "results" / (row["call_id"] + ".json")
            checkpoint = self.out / "checkpoints" / (row["call_id"] + ".json")
            require(result_path.is_file() and checkpoint.is_file(), "orphaned_v2_dispatch_intent_no_retry")
            cp = load(checkpoint)
            require(cp.get("result_sha256") == digest(result_path)
                    and cp.get("attempt_id") == row["attempt_id"], "v2_checkpoint_mismatch")
            record = load(result_path)
            require(record.get("attempt_id") == row["attempt_id"], "v2_attempt_identity_mismatch")
            self.protocol.validate_result(record, self.campaign_id)
            try:
                current_time = datetime.fromisoformat(record["pipeline"]["started_at"])
                campaign_time = datetime.fromisoformat(self.metadata["created_at"])
                valid_time = current_time.tzinfo is not None and campaign_time.tzinfo is not None and current_time >= campaign_time
            except (ValueError, TypeError, KeyError):
                valid_time = False
            require(valid_time, "foreign_result_time_before_v2_campaign")
            require(record.get("runner_binding_sha256") == self.metadata["runner_binding_sha256"], "foreign_runner_result")
            records.append(record)
        require(len({r["pipeline"]["run_id"] for r in records}) == len(records), "duplicate_pipeline_run_id")
        return records

    def stop(self, code, *, call_id=None):
        path = self.out / "STOP.json"
        if not path.exists():
            save(path, {"at": now(), "reason": code, "call_id": call_id,
                        "campaign_id": self.campaign_id, "automatic_resume_permitted": False})

    def preflight(self, *, initial):
        self.last_preflight = {"at": now(), "initial": initial, "passed": False}
        self.protocol.verify()
        self.protocol.verify_binding()
        cfg = self.protocol.settings
        with self.gate_factory():
            client = self.transport_builder(None)
            version = client.json("version")
            self.last_preflight["version"] = version
            try:
                compatible = Version(version["version"]) >= Version(self.protocol.configuration["runtime_minimum"])
            except (KeyError, InvalidVersion, TypeError):
                compatible = False
            require(compatible, "runtime_incompatible")
            tags, ps = client.json("tags"), client.json("ps")
            self.last_preflight.update(tags=tags, residents_response=ps)
            matches = [m for m in tags.get("models", []) if m.get("name") == cfg.model]
            require(len(matches) == 1 and matches[0].get("digest") == cfg.expected_digest, "model_digest_mismatch")
            require(matches[0].get("details", {}).get("quantization_level") == "Q4_K_M", "quantization_mismatch")
            residents = ps.get("models")
            require(isinstance(residents, list) and len(residents) <= 1, "other_model_or_invalid_residents")
            require(not initial or not residents, "initial_preflight_requires_no_residents")
            require(all(m.get("digest") == cfg.expected_digest for m in residents), "other_model_resident")
            show = client.json("show", {"model": cfg.model})
            require(False in show.get("thinking", {}).get("values", []), "thinking_mode_unsupported")
            require("completion" in show.get("capabilities", []), "completion_capability_missing")
            require(show.get("model_info", {}).get("gemma4.context_length", 0) >= cfg.options.num_ctx,
                    "model_context_unsupported")
            memory = self.sampler()
            self.last_preflight["memory"] = memory
            require(all(type(memory.get(k)) is int and memory[k] >= 0
                        for k in ("available_bytes", "commit_available_bytes", "commit_limit_bytes")),
                    "resource_monitor_unavailable")
            warm = bool(residents) and residents[0].get("context_length") == cfg.options.num_ctx and residents[0].get("size_vram") == 0
            reserve = cfg.loaded_growth_reserve_bytes if warm else cfg.unloaded_reserve_bytes
            needed = cfg.minimum_margin_bytes + reserve
            self.last_preflight.update(required_available_bytes=needed, warm=warm)
            require(min(memory["available_bytes"], memory["commit_available_bytes"]) >= needed, "insufficient_memory")
            model_path = Path(os.getenv("OLLAMA_MODELS") or Path.home() / ".ollama/models")
            self.last_preflight["disk_free_bytes"] = self.disk_sampler(model_path)
            require(self.last_preflight["disk_free_bytes"] >= 2 * 1024 ** 3, "insufficient_disk_space")
            self.last_preflight.update(passed=True, model=matches[0], residents=residents,
                circuit_blocked=False, exclusive_session="operator_attestation_and_application_OS_gate_not_universal_external_client_exclusion")
            return self.last_preflight

    def reserve(self, payload):
        self.protocol.verify()
        self.protocol.verify_binding()
        require(digest(self.protocol.binding_path) == self.metadata["runner_binding_sha256"], "active_runner_binding_changed")
        require(digest(self.authorization_path) == self.authorization_sha256, "active_authorization_changed")
        require(self.active is not None, "no_active_v2_call")
        call, attempt_id = self.active
        require(not (self.out / "STOP.json").exists(), "v2_campaign_stopped")
        rows = self.entries()
        require(len(rows) < 12 and self.protocol.calls[len(rows)]["call_id"] == call["call_id"], "v2_budget_or_order_violation")
        require(sha(canonical(payload)) == call["request_sha256_canonical"], "dispatch_payload_not_frozen")
        marker = self.gate_factory().marker
        require(marker.is_file(), "application_dispatch_marker_required")
        intent = load(marker)
        require(intent.get("state") == "dispatch_intent" and intent.get("pid") == os.getpid()
                and intent.get("request_sha256") == call["request_sha256_canonical"], "dispatch_marker_not_owned")
        row = {"attempt": len(rows) + 1, "attempt_id": attempt_id, "call_id": call["call_id"],
               "campaign_id": self.campaign_id, "freeze_sha256": FREEZE_SHA,
               "request_sha256": call["request_sha256_canonical"], "reserved_before_HTTP_at": now()}
        with (self.out / "ledger.jsonl").open("a", encoding="utf-8", newline="\n") as stream:
            stream.write(json.dumps(row) + "\n"); stream.flush(); os.fsync(stream.fileno())
        return row

    def hard_failure(self, pipeline):
        op = pipeline["operational"]
        response = op.get("response", {})
        if op.get("circuit_blocked") or op.get("resources", {}).get("margin_violated"):
            return "resource_or_interrupted_circuit"
        if response:
            if response.get("model") != self.protocol.settings.model:
                return "response_model_mismatch"
            if response.get("message", {}).get("tool_calls"):
                return "unauthorized_tool_call"
            if response.get("message", {}).get("thinking"):
                return "unexpected_thinking"
        errors = pipeline.get("errors", [])
        for error in errors:
            ordinary = error["code"] == "invalid_response" and error["stage"] == "response"
            terminal_limit = (error["code"] == "truncated_response" and response.get("done") is True
                              and response.get("done_reason") == "length")
            if not ordinary and not terminal_limit:
                return error["code"]
        if response.get("done") is not True or response.get("done_reason") not in {"stop", "length"}:
            return "missing_terminal_acknowledgement"
        counts = [response.get("prompt_eval_count"), response.get("eval_count")]
        if any(type(v) is not int or v < 0 for v in counts):
            return "missing_token_counts"
        cfg = self.protocol.settings
        if sum(counts) > cfg.options.num_ctx or counts[1] > cfg.options.num_predict:
            return "effective_token_budget_violation"
        return None  # All terminal ordinary quality errors continue, including FP/FN.

    def run(self, authorization_path, *, exclusive_session_attested=False, resume=False):
        require(exclusive_session_attested, "exclusive_session_attestation_required")
        auth = self.protocol.authorize(authorization_path, resume=resume)  # Before client construction or any model HTTP.
        self.authorization_path = Path(authorization_path)
        self.authorization_sha256 = digest(authorization_path)
        self.out.mkdir(parents=True, exist_ok=True)
        session_id = str(uuid4())
        with CampaignLock(self.out / "campaign.lock"):
            require(not (self.out / "STOP.json").exists(), "v2_campaign_stopped")
            metadata_path = self.out / "campaign.json"
            if metadata_path.exists():
                self.metadata = load(metadata_path)
                self.campaign_id = self.metadata["campaign_id"]
                require(resume, "explicit_resume_required")
                require(self.metadata.get("experiment") == VERSION
                        and self.metadata.get("freeze_sha256") == FREEZE_SHA
                        and self.metadata.get("runner_binding_sha256") == digest(self.protocol.binding_path),
                        "foreign_campaign_metadata")
            else:
                require(not resume, "nothing_to_resume")
                self.campaign_id = str(uuid4())
                self.metadata = {"experiment": VERSION, "campaign_id": self.campaign_id,
                    "freeze_sha256": FREEZE_SHA, "runner_binding_sha256": digest(self.protocol.binding_path),
                    "authorization_sha256": digest(authorization_path), "created_at": now(),
                    "references_accepted": auth["references_accepted"], "maximum_attempts": 12}
                save(metadata_path, self.metadata)
            save(self.out / "sessions" / (session_id + ".json"), {"at": now(), "resume": resume,
                 "authorization_sha256": digest(authorization_path), "campaign_id": self.campaign_id})
            try:
                completed = self.completed_records()  # Missing/corrupt checkpoints never get retried.
                require(len(completed) < 12, "v2_budget_exhausted")
                for call in self.protocol.calls[len(completed):]:
                    self.protocol.verify()
                    self.protocol.verify_binding()
                    script, _, _ = self.protocol.context(call)
                    preflight = self.preflight(initial=not completed)
                    attempt_id = str(uuid4())
                    save(self.out / "preflights" / (attempt_id + ".json"),
                         {"call_id": call["call_id"], "attempt_id": attempt_id, **preflight})
                    self.active = (call, attempt_id)
                    before = len(self.entries())
                    adapter = Gemma4Adapter(sampler=self.sampler, gate_factory=self.gate_factory,
                        transport_factory=lambda: self.transport_builder(self.reserve))
                    require(adapter.settings == self.protocol.settings, "adapter_settings_changed")
                    pipeline = AnalysisService(adapter.settings, adapter=adapter).analyze(script, call["mode"]).model_dump(mode="json")
                    rows = self.entries()
                    if len(rows) != before + 1:
                        save(self.out / "preflight_failures" / (attempt_id + ".json"),
                             {"call_id": call["call_id"], "attempt_id": attempt_id, "pipeline": pipeline,
                              "new_intent_reserved": False})
                        self.stop("no_valid_dispatch_reservation", call_id=call["call_id"])
                        break
                    record = {"experiment": VERSION, "campaign_id": self.campaign_id,
                        "runner_binding_sha256": digest(self.protocol.binding_path), "freeze_sha256": FREEZE_SHA,
                        "attempt": rows[-1]["attempt"], "attempt_id": attempt_id, "call_id": call["call_id"],
                        "mode": call["mode"], "input_sha256": call["input_sha256"],
                        "request_sha256": call["request_sha256_canonical"], "pipeline": pipeline}
                    self.protocol.validate_result(record, self.campaign_id)
                    result_path = self.out / "results" / (call["call_id"] + ".json")
                    save(result_path, record)  # Raw model/envelope/bytes/resources persisted before evaluation.
                    save(self.out / "checkpoints" / (call["call_id"] + ".json"),
                         {"attempt_id": attempt_id, "result_sha256": digest(result_path)})
                    completed.append(record)
                    reason = self.hard_failure(pipeline)
                    if reason:
                        self.stop(reason, call_id=call["call_id"])
                        break
            except BaseException as exc:
                if self.last_preflight is not None and not self.last_preflight["passed"]:
                    save(self.out / "preflight_failures" / (session_id + ".json"),
                         {"code": getattr(exc, "code", "preflight_failure"), **self.last_preflight})
                self.stop(getattr(exc, "code", "controller_interrupted_or_storage_failure"),
                          call_id=self.active[0]["call_id"] if self.active else None)
                raise
            finally:
                self.active = None
            summary = {"experiment": VERSION, "campaign_id": self.campaign_id, "at": now(),
                "reserved_attempts": len(self.entries()), "completed_result_records": len(completed),
                "stopped": (self.out / "STOP.json").exists(), "human_adjudication": "pending_personal_review",
                "automatic_resume": False}
            save(self.out / "summaries" / (session_id + ".json"), summary)
            return summary

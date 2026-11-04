"""Frozen protocol and authorization checks, with no network side effects."""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path

from app.services.deobfuscation.engine import deobfuscate
from app.services.llm.gemma4 import Gemma4Settings
from app.services.pipelines.context import build_context, canonical, sha
from app.services.pipelines.provider import response_schema
from app.services.pipelines.resources import OperationalFailure
from app.services.pipelines.validation import strict_json

ROOT = Path(__file__).resolve().parents[2]
VERSION = "gemma4-development-v2.0"
FREEZE_SHA = "f27f87d077856ac4a03966f7b9ddcfa266aa929cbbd01e327a88eff08e82e745"
PREPARATION = "artifacts/gemma4_v2_execution_preparation"
SOURCE_FILES = ["experiments/gemma4_v2/" + name for name in
                ("__init__.py", "protocol.py", "runner.py", "evaluation.py", "__main__.py")]


def now():
    return datetime.now(timezone.utc).isoformat()


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(path):
    return strict_json(Path(path).read_text(encoding="utf-8"))


def require(condition, code):
    if not condition:
        raise OperationalFailure(code, code, "gemma_v2")


def save(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())


class Protocol:
    def __init__(self, root=ROOT):
        self.root = Path(root).resolve()
        self.plan_dir = self.root / "artifacts/gemma4_development_v2"
        self.execution = self.plan_dir / "execution"
        self.freeze_path = self.plan_dir / "FREEZE.json"
        self.preparation = self.root / PREPARATION
        self.binding_path = self.preparation / "runner_binding.json"
        self.clarification_path = self.preparation / "gate_clarification_v2.0-a1.json"
        self.verify()
        self.calls = load(self.plan_dir / "cases_and_order.json")["calls"]
        self.configuration = load(self.plan_dir / "configuration.json")
        Gemma4Settings.model_validate(self.configuration["settings"])
        # Preserve the original adapter's wire representation (e.g. default 0 vs
        # validated 0.0); never rewrite a frozen payload to normalize its numbers.
        self.settings = Gemma4Settings()
        require(self.settings.model_dump(mode="json") == self.configuration["settings"], "runtime_settings_differ_from_freeze")
        self.gate = load(self.plan_dir / "gate.json")
        require(len(self.calls) == 12 and sum(c["mode"] == "B" for c in self.calls) == 10,
                "plan_distribution_mismatch")
        require(self.gate["exact_label_sets"] == {"minimum": 9, "denominator": 11, "exclude_call": "V2-09"},
                "gate_denominator_mismatch")

    def path(self, relative):
        path = (self.root / relative).resolve()
        require(path.is_relative_to(self.root), "path_outside_repository")
        return path

    def verify(self):
        require(digest(self.freeze_path) == FREEZE_SHA, "freeze_hash_mismatch")
        manifest = load(self.freeze_path)
        require(manifest["version"] == VERSION, "wrong_protocol_version")
        for key in ("files_sha256", "runtime_contract_sources_sha256"):
            for name, expected in manifest[key].items():
                require(digest(self.path(name)) == expected, "frozen_source_or_plan_changed")
        return manifest

    def verify_binding(self):
        binding = load(self.binding_path)
        require(binding["freeze_sha256"] == FREEZE_SHA, "binding_freeze_mismatch")
        require(binding["clarification_sha256"] == digest(self.clarification_path), "clarification_changed")
        for name, expected in binding["source_sha256"].items():
            require(digest(self.path(name)) == expected, "controller_binding_changed")
        require(set(SOURCE_FILES) <= set(binding["source_sha256"]), "incomplete_controller_binding")
        return binding

    def authorize(self, authorization_path, *, resume=False):
        self.verify()
        self.verify_binding()
        value = load(authorization_path)
        require(value.get("execution_authorized") is True, "v2_execution_not_authorized")
        require(value.get("references_accepted") is True, "v2_references_not_accepted")
        require(value.get("clarification_accepted") is True, "v2_clarification_not_accepted")
        require(type(value.get("maximum_inference_intents")) is int and value["maximum_inference_intents"] == 12,
                "wrong_authorized_budget")
        require(value.get("freeze_sha256") == FREEZE_SHA, "authorization_freeze_mismatch")
        require(value.get("runner_binding_sha256") == digest(self.binding_path), "authorization_binding_mismatch")
        require(value.get("clarification_sha256") == digest(self.clarification_path), "authorization_clarification_mismatch")
        require(value.get("source") == "explicit_owner_execution_authorization"
                and isinstance(value.get("owner_statement"), str) and value["owner_statement"].strip(),
                "owner_execution_statement_required")
        require(value.get("exclusive_session_attested") is True, "exclusive_session_attestation_required")
        if resume:
            ledger = self.execution / "ledger.jsonl"
            require(value.get("resume_explicitly_authorized") is True
                    and ledger.exists() and value.get("resume_ledger_sha256") == digest(ledger),
                    "resume_requires_explicit_bound_authorization")
        return value

    def context(self, call):
        script = (self.plan_dir / call["script_file"]).read_text(encoding="utf-8")
        require(sha(script) == call["input_sha256"], "script_hash_mismatch")
        recovery = deobfuscate(script) if call["mode"] == "C" else None
        context = build_context(script, recovery)
        payload = {"model": self.settings.model, "messages": context.messages,
                   "format": response_schema(), "stream": False, "truncate": False,
                   "think": self.settings.think, "keep_alive": self.settings.keep_alive,
                   "options": self.settings.options.model_dump()}
        require(sha(canonical(payload)) == call["request_sha256_canonical"], "rebuilt_request_differs_from_freeze")
        require(context.sources == call["sources_for_review_only"], "recovery_sources_changed")
        require(recovery is None or recovery.model_dump(mode="json") == call["recovery_for_review_only"],
                "verified_recovery_changed")
        expected = load(self.plan_dir / call["request_file"])
        require(payload == expected, "request_not_frozen")
        data = strict_json(context.messages[1]["content"])
        require(set(data) == ({"original", "deterministic_recovery"} if call["mode"] == "C" else {"original"}),
                "private_reference_leakage")
        return script, context, payload

    def validate_result(self, record, campaign_id):
        require(record.get("experiment") == VERSION and record.get("campaign_id") == campaign_id,
                "foreign_result_not_v2")
        require(record.get("freeze_sha256") == FREEZE_SHA, "foreign_result_freeze")
        number = record.get("attempt")
        require(type(number) is int and 1 <= number <= 12, "invalid_result_attempt")
        call = self.calls[number - 1]
        require(record.get("call_id") == call["call_id"] and record.get("mode") == call["mode"]
                and record.get("input_sha256") == call["input_sha256"]
                and record.get("request_sha256") == call["request_sha256_canonical"], "result_identity_mismatch")
        from app.schemas.pipeline import PipelineResult
        result = PipelineResult.model_validate(record["pipeline"])
        require(result.configuration == call["mode"] and result.input_sha256 == call["input_sha256"],
                "pipeline_identity_mismatch")
        require(result.operational.get("request_sha256") == call["request_sha256_canonical"],
                "pipeline_request_mismatch")
        return call

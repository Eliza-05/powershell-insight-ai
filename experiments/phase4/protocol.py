"""Owner-reviewed freeze and separately authorized future execution; fail closed."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

from app.services.pipelines.context import canonical, sha
from experiments.phase4.common import ROOT, OUT, VERSION, digest, load, now, require, save
from experiments.phase4.profile import context_for, payload_for, settings_for, strategy_for


class Proposal:
    def __init__(self, root=ROOT, out=OUT):
        self.root, self.out = Path(root).resolve(), Path(out).resolve()
        self.plan = self.out / "proposal"
        self.candidate_hash = digest(self.out / "CANDIDATE_MANIFEST.json")
        self.verify_candidate()
        self.cases = load(self.plan / "cases.json")["cases"]
        self.configuration = load(self.plan / "configuration.json")
        self.settings = settings_for(self.configuration)
        strategy = strategy_for(self.settings)
        if strategy:
            require(self.configuration.get("strategy") == strategy.versions()
                    and self.configuration.get("policy_text_sha256") == strategy.policy_sha256,
                    "prospective_profile_binding_mismatch")
        self.sequence = load(self.plan / "order.json")["sequence"]
        require(len(self.cases) == 16 and len(self.sequence) == 48, "wrong_phase4_size")
        require(len({c["id"] for c in self.cases}) == 16, "duplicate_unit")
        require(sum(c["expected_labels"] is None for c in self.cases) == 2, "indeterminate_denominator_changed")
        require(sum(bool(c["verified_1A_sources"]) for c in self.cases) == 8, "recovery_distribution_changed")
        require(all(sum(s == {"unit": c["id"], "mode": mode} for s in self.sequence) == 1
                    for c in self.cases for mode in ("A", "B", "C")), "duplicate_or_missing_mode")

    def verify_candidate(self):
        require(digest(self.out / "CANDIDATE_MANIFEST.json") == self.candidate_hash, "candidate_manifest_changed")
        manifest = load(self.out / "CANDIDATE_MANIFEST.json")
        require(manifest["version"] == VERSION and manifest["approved_freeze"] is False, "invalid_proposal_state")
        for name, expected in manifest["files_sha256"].items():
            path = (self.root / name).resolve()
            require(path.is_relative_to(self.root) and digest(path) == expected, "candidate_file_changed")

    def case(self, identifier):
        return next(c for c in self.cases if c["id"] == identifier)

    def context(self, case, mode):
        script = (self.plan / case["script_file"]).read_text(encoding="utf-8")
        require(sha(script) == case["script_sha256"], "sample_changed")
        require(mode in {"B", "C"}, "context_mode_not_LLM")
        context = context_for(script, mode, self.settings)
        payload = payload_for(context, self.settings)
        require(payload == load(self.plan / case[mode + "_request"])
                and sha(canonical(payload)) == case[mode + "_request_sha256"], "frozen_request_changed")
        data = load(self.plan / case[mode + "_request"])["messages"]
        import json
        require(len(data) == 2 and set(json.loads(data[1]["content"])) ==
                ({"original", "deterministic_recovery"} if mode == "C" else {"original"}), "reference_or_answer_leak")
        return script, context, payload

    def seal(self, review_path):
        self.verify_candidate()
        review = load(review_path)
        require(review.get("candidate_sha256") == self.candidate_hash, "review_not_bound_to_candidate")
        require(review.get("reviewer_type") == "human_personal" and isinstance(review.get("reviewer"), str)
                and review["reviewer"].strip(), "named_personal_reference_review_required")
        require(all(review.get(key) is True for key in ("references_approved", "semantic_independence_approved", "safety_approved")),
                "owner_reference_independence_safety_approval_required")
        try:
            reviewed = datetime.fromisoformat(review["reviewed_at"])
            require(reviewed.tzinfo is not None and reviewed >= datetime.fromisoformat(load(self.out / "CANDIDATE_MANIFEST.json")["at"]), "stale_reference_review")
        except (ValueError, KeyError, TypeError):
            require(False, "invalid_reference_review_time")
        rows = review.get("case_reviews", [])
        require(len(rows) == 16 and len({r["id"] for r in rows}) == 16, "review_all_sixteen_references")
        for case in self.cases:
            r = next((r for r in rows if r["id"] == case["id"]), {})
            require(r.get("approved") is True and r.get("script_sha256") == case["script_sha256"]
                    and r.get("reference_sha256") == sha(canonical(case)), "reference_review_case_mismatch")
        save(self.out / "FREEZE.json", {"version": VERSION, "sealed_at": now(), "candidate_sha256": self.candidate_hash,
            "reference_review_path": str(Path(review_path).resolve()), "reference_review_sha256": digest(review_path),
            "references_personally_approved": True, "execution_authorized": False, "maximum_LLM_intents": 32})

    def authorize(self, path, *, resume=False, ledger=None):
        self.verify_candidate()
        freeze_path = self.out / "FREEZE.json"
        require(freeze_path.is_file(), "personal_reference_freeze_required_before_execution")
        freeze = load(freeze_path)
        require(freeze.get("candidate_sha256") == self.candidate_hash and freeze.get("references_personally_approved") is True,
                "invalid_phase4_freeze")
        require(digest(freeze["reference_review_path"]) == freeze["reference_review_sha256"], "frozen_reference_review_changed")
        auth = load(path)
        require(auth.get("execution_authorized") is True and type(auth.get("maximum_real_LLM_intents")) is int
                and auth["maximum_real_LLM_intents"] == 32, "new_thirty_two_intent_authorization_required")
        require(auth.get("source") == "explicit_future_owner_execution_authorization" and
                isinstance(auth.get("owner_statement"), str) and auth["owner_statement"].strip(), "explicit_new_owner_statement_required")
        require(auth.get("exclusive_session_attested") is True, "exclusive_session_attestation_required")
        require(auth.get("freeze_sha256") == digest(freeze_path) and
                auth.get("reference_review_sha256") == freeze["reference_review_sha256"], "authorization_not_bound_to_freeze")
        try:
            time = datetime.fromisoformat(auth["authorized_at"])
            require(time.tzinfo is not None and time >= datetime.fromisoformat(freeze["sealed_at"]), "stale_execution_authorization")
        except (ValueError, KeyError, TypeError):
            require(False, "invalid_execution_authorization_time")
        if resume:
            require(auth.get("resume_explicitly_authorized") is True and ledger is not None and ledger.is_file()
                    and auth.get("resume_ledger_sha256") == digest(ledger), "explicit_bound_resume_required")
        return auth

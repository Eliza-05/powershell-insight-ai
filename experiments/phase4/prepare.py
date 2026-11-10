"""Build a reviewable proposal, never an approved freeze or real campaign."""
from __future__ import annotations

import platform
import random

from app.schemas.deobfuscation import DeobfuscationLimits
from app.services.deobfuscation.engine import deobfuscate
from app.api.application import load_pipeline_settings as load_settings
from app.services.pipelines.context import build_context, canonical, sha
from app.services.pipelines.provider import response_schema
from experiments.phase4.common import ROOT, OUT, VERSION, LABELS, now, digest, save, require, load
from experiments.phase4.profile import context_for, payload_for, profile_name, strategy_for


def prepare():
    # Reserved authorship/solutions are loaded only by this explicitly invoked
    # preparation command, never by importing controller/profile support in tests.
    from experiments.phase4.dataset import proposed_cases
    from experiments.phase4.independence import audit
    plan = OUT / "proposal"
    require(not plan.exists(), "proposal_exists_create_new_revision_instead_of_overwriting")
    settings = load_settings()
    # No environment-dependent model/parameter overrides may silently affect a proposal.
    cls = type(settings)
    require(settings == cls.model_validate(cls().model_dump(mode="json")), "unexpected_settings_override")
    cases = proposed_cases()
    exclusion_rules = {
        "B01": "No hay obtención activa de contenido remoto sustentada; una URL literal o un envío no bastan para B01.",
        "B02": "No hay evaluación/invocación funcional de código construido/recuperado/cargado; almacenamiento, nombres o invocaciones fijas no bastan.",
        "B03": "No hay operación que registre/escriba ejecución futura; consultar configuración no es persistencia.",
        "B04": "No hay modificación/debilitamiento de defensa o logging; consultar o mencionar un control no basta.",
        "B05": "No hay consulta de información del host/usuario/red/software; datos locales constantes, sus longitudes y rutas no bastan.",
        "B06": "No hay comunicación explícita adicional a una eventual descarga; URL, credencial o objeto sin conexión no bastan.",
        "B07": "No hay acceso a material de credenciales almacenado/tercero; captura legítima para autenticación y literales ficticios no bastan.",
    }
    # All references exist in the authored module before 1A is inspected. No 1B import.
    save(plan / "references_authored_before_1A.json", cases)
    for case in cases:
        script = case.pop("script")
        path = plan / "scripts" / (case["id"] + ".ps1.txt")
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("x", encoding="utf-8", newline="\n") as stream: stream.write(script)
        case["script_file"] = path.relative_to(plan).as_posix()
        case["script_sha256"] = sha(script)
        case["excluded_labels"] = sorted(set(LABELS) - set(case["expected_labels"])) if case["expected_labels"] is not None else None
        case["exclusion_rationales_by_label"] = {label: exclusion_rules[label] + " " + case["absent_rationale"] for label in case["excluded_labels"] or []}
        case["known_absent"] = case["excluded_labels"] if case["excluded_labels"] is not None else (["B02", "B03", "B04", "B05", "B07"] if case["id"] == "F4-15" else [])
        evidence = []
        for label, snippets in case["reference_evidence_proposals"].items():
            for snippet in snippets:
                # Contextual fragments are recorded individually; no semantic pass implied.
                require(snippet in script, "reference_fragment_not_in_original")
                pos = script.index(snippet)
                evidence.append({"behavior_id": label, "source": "original", "snippet": snippet,
                    "start": pos, "line": script.count("\n", 0, pos) + 1,
                    "support_proposal": "contextual_reference_only_pending_review"})
        case["reference_evidence_located"] = evidence
        for mode in ("B", "C"):
            context = context_for(script, mode, settings)
            payload = payload_for(context, settings)
            require(sum(len(m["content"].encode()) for m in context.messages) + settings.context_overhead_tokens + settings.options.num_predict <= settings.options.num_ctx,
                    "proposal_context_budget_exceeded")
            request = f"requests/{case['id']}-{mode}.json"
            save(plan / request, payload)
            case[mode + "_request"] = request
            case[mode + "_request_sha256"] = sha(canonical(payload))
            if mode == "C":
                recovered = {k: v for k, v in context.sources.items() if k != "original"}
                case["verified_1A_sources"] = recovered
                case["recovery_status"] = context.deobfuscation.status
                case["unresolved_1A"] = [u.model_dump(mode="json") for u in context.deobfuscation.unresolved]
                require(bool(recovered) == bool(case["expected_recovered_strings"]), "recovery_stratum_mismatch")
                require(all(any(text == value for value in recovered.values()) for text in case["expected_recovered_strings"]), "expected_1A_text_not_recovered")
                save(plan / "recoveries" / (case["id"] + ".json"), context.deobfuscation.model_dump(mode="json"))
    save(plan / "cases.json", {"version": VERSION, "reference_status": "pending_personal_review", "cases": cases})
    order = list(range(16)); random.Random(40716).shuffle(order)
    c_first = set(random.Random(61407).sample(range(16), 8))
    sequence = []
    for i in order:
        sequence.append({"unit": cases[i]["id"], "mode": "A"})
        sequence.extend({"unit": cases[i]["id"], "mode": mode} for mode in (("C", "B") if i in c_first else ("B", "C")))
    save(plan / "order.json", {"sequence": sequence, "seed_unit_order": 40716, "seed_counterbalance": 61407,
        "B_first_units": 8, "C_first_units": 8, "new_LLM_budget_proposed": 32, "A_analyses": 16, "retries": 0})
    configuration = {"version": VERSION, "settings": settings.model_dump(mode="json"),
        "runtime_minimum": "0.5.0", "policy_sha256": digest(ROOT / "backend/app/services/pipelines/policy_v1.md"),
        "schema_sha256": sha(canonical(response_schema())), "physical_or_commit_margin_bytes": settings.minimum_margin_bytes,
        "cold_required_bytes": settings.minimum_margin_bytes + settings.unloaded_reserve_bytes,
        "warm_required_bytes": settings.minimum_margin_bytes + settings.loaded_growth_reserve_bytes,
        "disk_free_minimum_bytes": 2 * 1024 ** 3, "new_model_downloads": 0,
        "retries": 0, "resume_policy": "No automatic resume. Explicit hash-bound owner resume only after reconciliation; never retry an intent.",
        "empty_recovery_policy": "Keep C with verified_texts empty plus unresolved/limits; no invented successful recovery. Report the no-recovery stratum separately.",
        "H1_primary": "delta micro F1 C-B on 14 fixed determinate units; all unusable outputs retained as coverage failures",
        "H2_primary": "delta personally adjudicated unsupported-claim count C-B, strict cited/recovered policy; all raw outputs including rejected reports",
        "statistics": {"exact_cluster_swaps": True, "H1_alternative": "C_greater", "H2_alternative": "C_less",
            "bootstrap_resamples": 2000, "seed": 40716, "multiplicity": "Two primary conditional tests: Holm adjustment reported alongside raw p; no automatic hypothesis acceptance",
            "limitations": "Purposive small sample, common author, clustered mechanisms; p-values conditional on exchangeability, no population/causal conclusion"},
        "completion": {"operational": "16 A records + 32 attempted terminal B/C records, intact checkpoints, no critical stop",
            "scientific": "Operational completion plus personally approved references and complete hash-bound claim adjudication; performance does not gate completion"},
        "prepared_environment_only": {"python": platform.python_version(), "platform": platform.platform()},
        "execution_authorized_now": False, "reference_review_complete": False}
    configuration["llm_profile"] = profile_name(settings)
    strategy = strategy_for(settings)
    if strategy:
        configuration.update(strategy=strategy.versions(), policy_text_sha256=strategy.policy_sha256,
            policy_sha256=strategy.policy_bytes_sha256, configuration_revision="qwen3coder-v2-bounded-prospective-1")
    save(plan / "configuration.json", configuration)
    full_cases = [{**c, "script": (plan / c["script_file"]).read_text(encoding="utf-8")} for c in cases]
    novelty = audit(full_cases)
    save(plan / "independence_audit.json", novelty)
    require(not novelty["automatic_exact_or_program_duplicate_found"], "prior_program_duplicate_requires_proposal_revision")
    save(OUT / "reference_review.template.json", {"candidate_sha256": None, "reviewer_type": "human_personal", "reviewer": "", "reviewed_at": "",
        "references_approved": False, "semantic_independence_approved": False, "safety_approved": False,
        "case_reviews": [{"id": c["id"], "script_sha256": c["script_sha256"], "approved": False,
            "reference_sha256": sha(canonical(c)), "notes": ""} for c in cases]})
    save(OUT / "execution_authorization.template.json", {"execution_authorized": False, "maximum_real_LLM_intents": 32,
        "freeze_sha256": None, "reference_review_sha256": None, "source": "explicit_future_owner_execution_authorization",
        "owner_statement": "", "authorized_at": "", "exclusive_session_attested": False,
        "resume_explicitly_authorized": False, "resume_ledger_sha256": None})
    refresh_candidate()
    print("Proposal prepared: 16 units, 32 requests, 8/8 recovery strata; no FREEZE or execution authorization")


def refresh_candidate():
    """Version unapproved snapshots, preserving previous candidates; never reseal a run."""
    require(not (OUT / "FREEZE.json").exists() and not (OUT / "execution").exists(), "cannot_revise_frozen_or_started_study")
    plan = OUT / "proposal"
    runtime = [p for p in (ROOT / "backend/app").rglob("*") if p.suffix in {".py", ".md"}]
    runtime += list((ROOT / "experiments/phase4").glob("*.py"))
    runtime += list((ROOT / "backend/tests/phase4").glob("*.py"))
    runtime += [ROOT / "experiments/gemma4_v2/runner.py", ROOT / "experiments/pilot_v2_runtime/resources.py"]
    runtime += [ROOT / name for name in ("docs/methodology.md", "docs/behavior_taxonomy.md", "backend/requirements-app.txt")]
    runtime += [p for p in (ROOT / "docs").glob("phase4_*proposed.md")]
    runtime += [p for p in (ROOT / "docs").glob("phase4_human_review.md")]
    runtime += [p for p in (ROOT / "docs").glob("phase4_independence_review.md")]
    files = [p for p in plan.rglob("*") if p.is_file()] + runtime
    value = {"version": VERSION, "at": now(), "approved_freeze": False,
        "references_personally_approved": False, "files_sha256": {p.relative_to(ROOT).as_posix(): digest(p) for p in files}}
    path = OUT / "CANDIDATE_MANIFEST.json"
    if path.exists():
        old = load(path)
        preserved = OUT / "proposal_revisions" / (digest(path) + ".json")
        if not preserved.exists(): save(preserved, old)
    # This file is the unapproved current-candidate pointer; old candidates remain.
    import json
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    review_path = OUT / "reference_review.template.json"
    if review_path.exists():
        template = load(review_path)
        require(template["references_approved"] is False and all(r["approved"] is False for r in template["case_reviews"]), "do_not_overwrite_owner_review")
        template["candidate_sha256"] = digest(path)
        review_path.write_text(json.dumps(template, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__": prepare()

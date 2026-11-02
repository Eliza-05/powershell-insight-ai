import pytest
from pydantic import ValidationError

from app.schemas.llm_analysis import AnalysisResult, analysis_json_schema


def test_valid_result_parses(valid_result):
    result = AnalysisResult.model_validate(valid_result)
    assert result.behavior_labels() == ["B05"]


def test_behavior_catalog_is_closed_b01_to_b07():
    schema = analysis_json_schema()
    assert schema["$defs"]["BehaviorId"]["enum"] == ["B01", "B02", "B03", "B04", "B05", "B06", "B07"]


def test_retired_b08_is_rejected(valid_result):
    valid_result["behaviors"][0]["behavior_id"] = "B08"
    with pytest.raises(ValidationError):
        AnalysisResult.model_validate(valid_result)


def test_axes_are_separate_fields():
    props = analysis_json_schema()["properties"]
    assert {"behaviors", "obfuscation_techniques", "risk_label"} <= props.keys()


def test_finding_requires_evidence(valid_result):
    valid_result["behaviors"][0]["evidence"] = []
    with pytest.raises(ValidationError):
        AnalysisResult.model_validate(valid_result)


def test_extra_fields_are_rejected(valid_result):
    valid_result["verdict"] = "malicious"
    with pytest.raises(ValidationError):
        AnalysisResult.model_validate(valid_result)


def test_unknown_risk_label_is_rejected(valid_result):
    valid_result["risk_label"] = "malicious"
    with pytest.raises(ValidationError):
        AnalysisResult.model_validate(valid_result)


def test_duplicates_are_reported_not_hidden(valid_result):
    valid_result["behaviors"].append(dict(valid_result["behaviors"][0]))
    result = AnalysisResult.model_validate(valid_result)
    assert result.behavior_labels() == ["B05"]
    assert result.duplicate_behavior_ids() == ["B05"]

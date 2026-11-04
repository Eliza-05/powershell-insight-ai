"""No Google traffic: SDK byte reconstruction, static differential checks, safe RPC extraction."""
import copy
import hashlib
import json
import socket

import httpx
import pytest

pytest.importorskip("google.genai")
from google.genai import types
from experiments import gemini_400_offline as offline
from app.services.llm.gemini_error_details import structured_error_details, safe_field_path
from app.services.pipelines.context import canonical, sha
from app.services.pipelines.resources import OperationalFailure
from tests.pipelines.test_gemini import factory


def forbid_google(monkeypatch):
    def forbidden(*a, **kw):
        pytest.fail("Offline test attempted network access")
    monkeypatch.setattr(socket, "getaddrinfo", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)
    monkeypatch.setattr(httpx.HTTPTransport, "handle_request", forbidden)


def historical():
    return json.loads(offline.HISTORICAL.read_text(encoding="utf-8"))


def test_all_five_sdk_http_probes_match_historical_bytes_without_real_transport(monkeypatch):
    forbid_google(monkeypatch)
    ledger = offline.ROOT / "artifacts/gemini_viability/requests.jsonl"
    before = ledger.read_bytes()
    source = historical()
    results = offline.probes(source)
    assert list(results) == ["basic_text", "simple_json", "full_schema", "reasoning", "complete_historical"]
    assert results["complete_historical"]["historical_fingerprint_format"] == source["operational"]["http_attempt"]["request_sha256"]
    for result in results.values():
        assert not offline.wire_findings(result["json"])
        assert offline.OFFLINE_KEY not in result["body_utf8"]
        assert result["path"] == "/v1beta/models/gemini-3.6-flash:generateContent"
    assert ledger.read_bytes() == before


def test_proto_aliases_equivalent_but_unknown_or_duplicate_fields_are_caught():
    original = json.loads((offline.OUTPUT / "complete_historical.wire.json").read_text(encoding="utf-8"))
    thought = original["generationConfig"]["thinkingConfig"]
    assert thought == {"include_thoughts": False, "thinking_level": "MEDIUM"}
    canonical_body = copy.deepcopy(original)
    canonical_body["generationConfig"]["thinkingConfig"] = {"includeThoughts": False, "thinkingLevel": "MEDIUM"}
    assert offline.wire_findings(original) == offline.wire_findings(canonical_body) == []
    bad = copy.deepcopy(original)
    bad["generationConfig"]["thinkingConfig"]["include_thought"] = False
    assert "unknown_thinking_field" in offline.wire_findings(bad)
    bad = copy.deepcopy(original)
    bad["generationConfig"]["thinkingConfig"]["thinkingLevel"] = "MEDIUM"
    assert "duplicate_thinking_alias" in offline.wire_findings(bad)


def test_negative_schema_and_thinking_controls_are_detected():
    body = json.loads((offline.OUTPUT / "complete_historical.wire.json").read_text())
    bad = copy.deepcopy(body)
    bad["generationConfig"]["responseSchema"] = {"type": "OBJECT"}
    assert "mutually_exclusive_schema_fields" in offline.wire_findings(bad)
    bad = copy.deepcopy(body)
    bad["generationConfig"].pop("responseMimeType")
    assert "schema_requires_json_mime" in offline.wire_findings(bad)
    bad = copy.deepcopy(body)
    bad["generationConfig"]["thinkingConfig"]["thinkingBudget"] = 512
    assert "thinking_level_and_budget_together" in offline.wire_findings(bad)


def test_full_schema_inventory_distinguishes_ignored_constraints_and_bounded_complexity():
    schema = historical()["operational"]["request"]["config"]["response_json_schema"]
    result = offline.schema_inventory(schema)
    assert result["structural_errors"] == result["unknown_keywords"] == result["alternatives"] == result["reference_cycles"] == []
    assert result["definitions"] == 8 and len(result["references"]) == 9
    assert len(result["ignored_constraints"]) == 12
    assert result["maximum_behavior_citations"] == 112 and result["maximum_nested_arrays"] == 2
    assert result["maximum_expanded_data_depth"] == 6
    bad = copy.deepcopy(schema)
    bad["properties"]["behaviors"]["items"]["$ref"] = "#/$defs/Missing"
    assert any(e["code"] == "unresolved_or_external_ref" for e in offline.schema_inventory(bad)["structural_errors"])
    bad = copy.deepcopy(schema)
    bad["properties"]["behaviors"]["maxItems"] = "7"
    assert any(e["code"] == "bound_must_be_nonnegative_integer" for e in offline.schema_inventory(bad)["structural_errors"])
    bad = copy.deepcopy(schema)
    bad["required"].append("missing_property")
    assert any(e["code"] == "required_not_in_properties" for e in offline.schema_inventory(bad)["structural_errors"])


def test_prospective_probe_changes_only_schema_and_has_no_authorization():
    plan = json.loads((offline.OUTPUT / "prospective_probe_v2.json").read_text())
    assert not plan["authorized"] and plan["maximum_new_api_calls"] == 1 and plan["expected_global_reservations_after_one_attempt"] == 5
    original = json.loads((offline.OUTPUT / "complete_historical.wire.json").read_text())
    proposed_text = (offline.OUTPUT / "prospective_probe.wire.json").read_text()
    proposed = json.loads(proposed_text)
    expected = copy.deepcopy(original)
    expected["generationConfig"].pop("responseJsonSchema")
    assert proposed == expected and proposed["generationConfig"]["responseMimeType"] == "application/json"
    assert hashlib.sha256(proposed_text.encode()).hexdigest() == plan["proposed_body_sha256"]


def test_sdk_supports_response_schema_conversion_but_that_is_a_different_wire_request(monkeypatch):
    forbid_google(monkeypatch)
    source = historical()["operational"]["request"]
    result = offline.capture(source["contents"], types.GenerateContentConfig(response_mime_type="application/json",
        response_schema=copy.deepcopy(source["config"]["response_json_schema"]),
        automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True)))
    cfg = result["json"]["generationConfig"]
    assert "responseSchema" in cfg and "responseJsonSchema" not in cfg
    assert "$defs" not in cfg["responseSchema"] and "$ref" not in json.dumps(cfg["responseSchema"])
    assert result["historical_fingerprint_format"] != historical()["operational"]["http_attempt"]["request_sha256"]


def rpc_error(marker):
    return {"error": {"code": 400, "status": "INVALID_ARGUMENT", "message": marker,
        "details": [
            {"@type": "type.googleapis.com/google.rpc.BadRequest", "fieldViolations": [
                {"field": "generation_config.thinking_config.thinking_level", "description": marker},
                {"field": "generationConfig.responseJsonSchema", "description": marker},
                {"field": "generation_config." + marker, "description": marker},
                {"field": "https://private.invalid/?key=" + marker}]},
            {"@type": "type.googleapis.com/google.rpc.ErrorInfo", "reason": "API_KEY_INVALID",
                "domain": marker, "metadata": {"api_key": marker, "consumer": marker}},
            {"@type": "type.googleapis.com/google.rpc.DebugInfo", "detail": marker},
        ]}}


def test_safe_extraction_keeps_only_closed_codes_and_known_field_paths():
    marker = "synthetic-sensitive-value-for-error-test"
    result = structured_error_details(rpc_error(marker), 400)
    assert result == {"api_code": 400, "rpc_status": "INVALID_ARGUMENT",
        "invalid_argument_fields": ["generationConfig.responseJsonSchema", "generation_config.thinking_config.thinking_level"],
        "api_reasons": ["API_KEY_INVALID"]}
    assert marker not in json.dumps(result) and "private" not in json.dumps(result)
    assert not structured_error_details(rpc_error(marker), 200)


@pytest.mark.parametrize("path", ["privateValue", "generation_config.privateValue", "generation_config.thinking_config['secret']",
    "contents[999].parts[0].text", "https://private.invalid/key", "generation_config.thinking_config\nsecret", "x"*300, None])
def test_arbitrary_values_cannot_be_smuggled_as_field_paths(path):
    assert safe_field_path(path) is None


def test_bad_rpc_values_not_logged():
    value = {"error": {"code": "private", "status": "PRIVATE_TOKEN", "message": "private",
        "details": [{"@type": "type.googleapis.com/google.rpc.ErrorInfo", "reason": "PRIVATE_TOKEN"}]}}
    assert structured_error_details(value, 400) == {}


def test_actual_sdk_http400_enrichment_does_not_retain_body_or_retry(factory, caplog):
    make, path, marker = factory
    calls = []
    def handler(request):
        calls.append(1)
        return httpx.Response(400, json=rpc_error("synthetic-other-private-value"))
    client = make(handler, grant=False)
    with pytest.raises(OperationalFailure, match="gemini_invalid_request"):
        client.list_models()
    assert client.last_diagnostic["rpc_status"] == "INVALID_ARGUMENT"
    assert client.last_diagnostic["api_code"] == client.last_diagnostic["http_status"] == 400
    assert client.last_diagnostic["invalid_argument_fields"]
    assert client.transport.last_body is None and len(calls) == len(client.budget.entries()) == 1
    text = json.dumps(client.last_diagnostic)+caplog.text+(path/"budget.jsonl").read_text()
    assert marker not in text and "synthetic-other-private-value" not in text
    # A locally blocked new operation must not inherit prior server details.
    with pytest.raises(OperationalFailure, match="already_attempted"):
        client.list_models()
    assert "rpc_status" not in client.last_diagnostic and "invalid_argument_fields" not in client.last_diagnostic
    assert len(calls) == 1

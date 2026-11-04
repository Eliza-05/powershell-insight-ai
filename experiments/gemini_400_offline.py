"""Reconstruct only through MockTransport. No credential loader, ledger writer or network transport."""
from __future__ import annotations

from collections import Counter
import copy
import hashlib
import importlib.metadata
import json
import logging
from pathlib import Path
import sys

import httpx
from google import genai
from google.genai import types

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from app.services.pipelines.context import canonical, sha

OUTPUT = ROOT / "artifacts/gemini_36_http400"
HISTORICAL = ROOT / "artifacts/gemini_36/G03_B.json"
OFFLINE_KEY = "synthetic-offline-wire-reconstruction-key"
MODEL = "gemini-3.6-flash"


def capture(contents, config):
    """Hardwired mock; no caller option can select a real network transport."""
    captures = []
    def handler(request):
        body = request.read()
        assert request.method == "POST" and request.url.path == "/v1beta/models/gemini-3.6-flash:generateContent"
        assert request.url.host == "generativelanguage.googleapis.com" and not request.url.query
        assert request.headers.get("x-goog-api-key") == OFFLINE_KEY
        assert "authorization" not in request.headers
        assert OFFLINE_KEY.encode() not in body
        captures.append({"method": request.method, "path": request.url.path,
                         "body_utf8": body.decode("utf-8"), "json": json.loads(body)})
        return httpx.Response(200, json={"candidates": [{"content": {"role": "model", "parts": [{"text": "OK"}]},
            "finishReason": "STOP"}], "modelVersion": MODEL,
            "usageMetadata": {"promptTokenCount": 1, "candidatesTokenCount": 1, "totalTokenCount": 2}})
    for name in ("google.genai", "google_genai", "httpx", "httpcore"):
        logger = logging.getLogger(name)
        logger.handlers = [logging.NullHandler()]
        logger.propagate = False
        logger.setLevel(logging.CRITICAL + 1)
    with httpx.Client(transport=httpx.MockTransport(handler), trust_env=False, follow_redirects=False) as http:
        with genai.Client(api_key=OFFLINE_KEY, vertexai=False, enterprise=False,
             http_options=types.HttpOptions(api_version="v1beta", base_url="https://generativelanguage.googleapis.com",
                 httpx_client=http, retry_options=types.HttpRetryOptions(attempts=1))) as client:
            client.models.generate_content(model=MODEL, contents=contents, config=config)
    assert len(captures) == 1
    captured = captures[0]
    captured["historical_fingerprint_format"] = sha(canonical({"method": captured["method"], "path": captured["path"], "body": captured["body_utf8"]}))
    return captured


def wire_findings(body):
    """Targeted documented request-shape checks, not Google's server validator."""
    errors = []
    if set(body) - {"contents", "systemInstruction", "generationConfig", "tools"}:
        errors.append("unexpected_top_level_field")
    contents = body.get("contents")
    if not isinstance(contents, list) or not contents or contents[-1].get("role") != "user":
        errors.append("last_turn_not_user")
    cfg = body.get("generationConfig", {})
    if set(cfg) - {"maxOutputTokens", "responseMimeType", "responseJsonSchema", "responseSchema", "thinkingConfig"}:
        errors.append("unexpected_generation_parameter")
    if "responseSchema" in cfg and "responseJsonSchema" in cfg:
        errors.append("mutually_exclusive_schema_fields")
    if any(k in cfg for k in ("responseSchema", "responseJsonSchema")) and cfg.get("responseMimeType") != "application/json":
        errors.append("schema_requires_json_mime")
    thought = cfg.get("thinkingConfig", {})
    if set(thought) - {"thinkingLevel", "thinking_level", "includeThoughts", "include_thoughts", "thinkingBudget", "thinking_budget"}:
        errors.append("unknown_thinking_field")
    for camel, snake in [("thinkingLevel", "thinking_level"), ("includeThoughts", "include_thoughts"), ("thinkingBudget", "thinking_budget")]:
        if camel in thought and snake in thought:
            errors.append("duplicate_thinking_alias")
    level = thought.get("thinkingLevel", thought.get("thinking_level"))
    if level is not None and level not in {"MINIMAL", "LOW", "MEDIUM", "HIGH"}:
        errors.append("invalid_thinking_level")
    if level is not None and ("thinkingBudget" in thought or "thinking_budget" in thought):
        errors.append("thinking_level_and_budget_together")
    if body.get("tools"):
        errors.append("tools_forbidden")
    return errors


SUPPORTED = frozenset({"$id", "$defs", "$ref", "$anchor", "type", "format", "title", "description", "enum",
    "items", "prefixItems", "minItems", "maxItems", "minimum", "maximum", "anyOf", "oneOf", "properties",
    "additionalProperties", "required", "propertyOrdering"})
IGNORED = frozenset({"minLength", "maxLength", "minProperties", "maxProperties", "uniqueItems", "contains", "minContains", "maxContains"})


def schema_inventory(schema):
    keywords, ignored, unknown, refs, errors, arrays, alternatives = Counter(), [], [], [], [], [], []
    def visit(node, path):
        if isinstance(node, bool):
            return
        if not isinstance(node, dict):
            errors.append({"path": path, "code": "schema_not_object"}); return
        keywords.update(node.keys())
        ignored.extend({"path": path+"/"+k, "value": node[k]} for k in node if k in IGNORED)
        unknown.extend({"path": path+"/"+k} for k in node if k not in SUPPORTED | IGNORED)
        if "$ref" in node:
            ref = node["$ref"]
            refs.append({"path": path, "ref": ref})
            if set(node)-{"$ref", "$id", "$anchor", "$defs"}:
                errors.append({"path": path, "code": "ref_with_non_dollar_siblings"})
            try:
                target = schema
                if not isinstance(ref, str) or not ref.startswith("#/"): raise ValueError
                for part in ref[2:].split("/"): target = target[part.replace("~1", "/").replace("~0", "~")]
            except (KeyError, TypeError, ValueError):
                errors.append({"path": path, "code": "unresolved_or_external_ref"})
        properties = node.get("properties", {})
        if not isinstance(properties, dict) or not isinstance(node.get("$defs", {}), dict):
            errors.append({"path": path, "code": "schema_map_not_object"}); return
        allowed_types = {"object", "array", "string", "number", "integer", "boolean", "null"}
        schema_type = node.get("type")
        if schema_type is not None and not (isinstance(schema_type, str) and schema_type in allowed_types):
            if not (isinstance(schema_type, list) and schema_type and all(isinstance(t, str) and t in allowed_types for t in schema_type)):
                errors.append({"path": path, "code": "invalid_schema_type"})
        for bound in ("minItems", "maxItems", "minLength", "maxLength"):
            if bound in node and (type(node[bound]) is not int or node[bound] < 0):
                errors.append({"path": path+"/"+bound, "code": "bound_must_be_nonnegative_integer"})
        if "enum" in node and (not isinstance(node["enum"], list) or not node["enum"]):
            errors.append({"path": path, "code": "invalid_enum"})
        required = node.get("required", [])
        if not isinstance(required, list) or not all(isinstance(k, str) for k in required) or not set(required) <= set(properties):
            errors.append({"path": path, "code": "required_not_in_properties"})
        if node.get("type") == "array":
            arrays.append({"path": path, "minItems": node.get("minItems"), "maxItems": node.get("maxItems")})
            if "items" not in node: errors.append({"path": path, "code": "array_missing_items"})
            if isinstance(node.get("maxItems", 0), int) and isinstance(node.get("minItems", 0), int) and node.get("maxItems", float("inf")) < node.get("minItems", 0):
                errors.append({"path": path, "code": "impossible_array_bounds"})
        for key in ("anyOf", "oneOf"):
            if key in node:
                alternatives.append({"path": path+"/"+key, "count": len(node[key])})
                for i, child in enumerate(node[key]): visit(child, path+"/"+key+"/"+str(i))
        for key in ("$defs", "properties"):
            for name, child in node.get(key, {}).items(): visit(child, path+"/"+key+"/"+name)
        for key in ("items", "additionalProperties"):
            if isinstance(node.get(key), (dict, bool)): visit(node[key], path+"/"+key)
    visit(schema, "#")
    depths, cycles = [], []
    def expanded(node, depth=1, array_depth=0, stack=()):
        if not isinstance(node, dict): return
        if "$ref" in node:
            ref=node["$ref"]
            if ref in stack: cycles.append(ref); return
            target=schema
            for part in ref[2:].split("/"): target=target[part]
            expanded(target, depth, array_depth, stack+(ref,)); return
        arrays_here=array_depth+(node.get("type")=="array")
        depths.append((depth,arrays_here))
        for child in node.get("properties",{}).values(): expanded(child,depth+1,arrays_here,stack)
        if "items" in node: expanded(node["items"],depth+1,arrays_here,stack)
    if not errors: expanded(schema)
    return {"scope":"static_documented_subset_not_remote_compiler_or_full_metaschema_validator",
        "schema_bytes":len(canonical(schema).encode()),"definitions":len(schema.get("$defs",{})),
        "root_properties":len(schema.get("properties",{})),"root_required":len(schema.get("required",[])),
        "keywords":dict(sorted(keywords.items())),"ignored_constraints":ignored,"unknown_keywords":unknown,
        "references":refs,"structural_errors":errors,"array_bounds":arrays,"alternatives":alternatives,
        "reference_cycles":cycles,"maximum_expanded_data_depth":max((d for d,a in depths),default=0),
        "maximum_nested_arrays":max((a for d,a in depths),default=0),
        "maximum_behavior_citations":schema.get("properties",{}).get("behaviors",{}).get("maxItems",0)*schema.get("$defs",{}).get("ModelFinding",{}).get("properties",{}).get("evidence",{}).get("maxItems",0),
        "provider_compiler_complexity_limit":"not_published_or_measurable_locally"}


def probes(historical):
    request = historical["operational"]["request"]
    original = request["config"]
    base = {"max_output_tokens": original["max_output_tokens"], "tools": [],
            "automatic_function_calling": {"disable": True}}
    simple = {"type":"object", "properties":{"ok":{"type":"boolean"}}, "required":["ok"], "additionalProperties":False}
    settings = {
        "basic_text":base,
        "simple_json":{**base,"response_mime_type":"application/json","response_json_schema":simple},
        "full_schema":{**base,"response_mime_type":"application/json","response_json_schema":original["response_json_schema"]},
        "reasoning":{**base,"thinking_config":original["thinking_config"]},
        "complete_historical":original,
    }
    return {name:capture(request["contents"],types.GenerateContentConfig(**copy.deepcopy(cfg))) for name,cfg in settings.items()}


def main():
    OUTPUT.mkdir(exist_ok=True)
    ledger = ROOT/"artifacts/gemini_viability/requests.jsonl"
    before = ledger.read_bytes()
    historical = json.loads(HISTORICAL.read_text(encoding="utf-8"))
    result = probes(historical)
    expected = historical["operational"]["http_attempt"]["request_sha256"]
    assert result["complete_historical"]["historical_fingerprint_format"] == expected
    for name, captured in result.items():
        path = OUTPUT/(name+".wire.json")
        encoded = captured["body_utf8"].encode()
        if path.exists():
            assert path.read_bytes() == encoded  # never overwrite prior diagnostic evidence
        else:
            with path.open("xb") as handle: handle.write(encoded)
    inventory = schema_inventory(historical["operational"]["request"]["config"]["response_json_schema"])
    def save(name, data):
        with (OUTPUT/name).open("x",encoding="utf-8",newline="\n") as handle: json.dump(data,handle,ensure_ascii=False,indent=2);handle.write("\n")
    save("schema_inventory.json",inventory)
    save("differential_results.json",{"real_network_calls":0,"real_credentials_loaded":False,
        "sdk_version":importlib.metadata.version("google-genai"),"api_version":"v1beta",
        "exact_historical_body_reconstructed":True,"matched_ledger_request_sha256":expected,
        "reconstructed_body_sha256":hashlib.sha256(result["complete_historical"]["body_utf8"].encode()).hexdigest(),
        "historical_artifact_sha256":hashlib.sha256(HISTORICAL.read_bytes()).hexdigest(),
        "probes":{name:{"mock_http_calls":1,"sdk_returned_with_synthetic_response":True,
            "local_wire_findings":wire_findings(c["json"]),"generation_fields":sorted(c["json"].get("generationConfig",{})),
            "remote_acceptance":"not_tested"} for name,c in result.items()}})
    assert ledger.read_bytes()==before
    save("ledger_check.json",{"unchanged":True,"entries":len(before.splitlines()),"sha256":hashlib.sha256(before).hexdigest()})
    print(json.dumps({"exact_wire_fingerprint_matched":True,"offline_probes":len(result),"ledger_entries":4,
                     "api_calls":0,"static_schema_errors":len(inventory["structural_errors"]),"unknown_schema_keywords":len(inventory["unknown_keywords"])}))


if __name__=="__main__":
    main()

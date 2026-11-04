"""Keep only allowlisted RPC status codes and validated field paths; never messages/values."""
import re

RPC_CODES = frozenset({"INVALID_ARGUMENT", "UNAUTHENTICATED", "PERMISSION_DENIED", "RESOURCE_EXHAUSTED",
    "UNAVAILABLE", "INTERNAL", "DEADLINE_EXCEEDED", "NOT_FOUND", "FAILED_PRECONDITION", "OUT_OF_RANGE",
    "UNIMPLEMENTED", "ABORTED", "CANCELLED", "ALREADY_EXISTS", "DATA_LOSS", "UNKNOWN"})
REASONS = frozenset({"API_KEY_INVALID", "API_KEY_SERVICE_BLOCKED", "API_KEY_HTTP_REFERRER_BLOCKED",
    "API_KEY_IP_ADDRESS_BLOCKED", "API_KEY_RESTRICTION_VIOLATION", "SERVICE_DISABLED", "BILLING_DISABLED",
    "RATE_LIMIT_EXCEEDED", "CONSUMER_INVALID", "ACCESS_TOKEN_EXPIRED", "ACCESS_TOKEN_SCOPE_INSUFFICIENT"})
# No arbitrary schema property names or quoted dictionary keys are accepted.
PARTS = frozenset("""contents parts role text systemInstruction system_instruction generationConfig generation_config
maxOutputTokens max_output_tokens responseMimeType response_mime_type responseSchema response_schema
responseJsonSchema response_json_schema thinkingConfig thinking_config thinkingLevel thinking_level
includeThoughts include_thoughts thinkingBudget thinking_budget temperature topP top_p topK top_k
seed candidateCount candidate_count frequencyPenalty frequency_penalty presencePenalty presence_penalty
tools toolConfig tool_config safetySettings safety_settings $defs $ref type format enum items properties
required additionalProperties minItems maxItems minLength maxLength anyOf oneOf minimum maximum
obfuscation_techniques recovered_content behaviors risk_label risk_rationale uncertainty prompt_injection
limitations behavior_id explanation evidence confidence source_id snippet level uninterpretable_fragments
notes detected snippets BehaviorId Citation ModelFinding ModelUncertainty InjectionAssessment Level
ObfuscationTechnique RiskLabel ModelReport""".split())
ROOTS = frozenset({"contents", "systemInstruction", "system_instruction", "generationConfig", "generation_config",
                   "tools", "toolConfig", "tool_config", "safetySettings", "safety_settings"})


def safe_field_path(value):
    if not isinstance(value, str) or not 1 <= len(value) <= 256:
        return None
    segments = value.split(".")
    if len(segments) > 20:
        return None
    for i, segment in enumerate(segments):
        match = re.fullmatch(r"([A-Za-z_$][A-Za-z0-9_$]*)(?:\[([0-9]{1,3})\])?", segment)
        if match is None or match[1] not in PARTS or (i == 0 and match[1] not in ROOTS):
            return None
        if match[2] is not None and int(match[2]) > 128:
            return None
    return value


def structured_error_details(payload, http_status):
    if type(http_status) is not int or http_status < 400 or not isinstance(payload, dict):
        return {}
    error = payload.get("error")
    if not isinstance(error, dict):
        return {}
    safe = {}
    if type(error.get("code")) is int and 100 <= error["code"] <= 599:
        safe["api_code"] = error["code"]
    if isinstance(error.get("status"), str) and error["status"] in RPC_CODES:
        safe["rpc_status"] = error["status"]
    fields, reasons = set(), set()
    details = error.get("details")
    for detail in details[:16] if isinstance(details, list) else []:
        if not isinstance(detail, dict):
            continue
        if detail.get("@type") == "type.googleapis.com/google.rpc.BadRequest":
            violations = detail.get("fieldViolations")
            for violation in violations[:32] if isinstance(violations, list) else []:
                if isinstance(violation, dict):
                    field = safe_field_path(violation.get("field"))
                    if field:
                        fields.add(field)
        elif detail.get("@type") == "type.googleapis.com/google.rpc.ErrorInfo":
            reason = detail.get("reason")
            if isinstance(reason, str) and reason in REASONS:
                reasons.add(reason)
    if fields:
        safe["invalid_argument_fields"] = sorted(fields)
    if reasons:
        safe["api_reasons"] = sorted(reasons)
    return safe

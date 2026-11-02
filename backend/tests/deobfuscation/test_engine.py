"""Contract and development cases, defined before the transformations."""

import base64
import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.schemas.deobfuscation import DeobfuscationLimits, DeobfuscationResult
from app.services.deobfuscation import deobfuscate


def encoded(text):
    return base64.b64encode(text.encode("utf-16-le")).decode("ascii")


def recovered(script, **kwargs):
    return list(deobfuscate(script, **kwargs).recovered_texts().values())


@pytest.mark.parametrize("launcher", ["powershell", "PowerShell.EXE", "pwsh", "& 'pwsh.exe'"])
@pytest.mark.parametrize("parameter", ["-EncodedCommand", "-encodedcommand", "-ENC"])
def test_encoded_launchers(launcher, parameter):
    payload = "Write-Output 'café'\n"
    result = deobfuscate(f"{launcher} -NoProfile {parameter} {encoded(payload)}")
    assert payload in result.recovered_texts().values()
    assert result.transformations[0].added_operation == "LAUNCHER_ENCCMD"
    assert result.layers[1].text == payload
    assert result.layers[1].provenance == "deobfuscator_recovered"


@pytest.mark.parametrize("value", ["!!!", "QQ", "Q===", "QQ==", "/v8=", "AAAA"])
def test_bad_encoded_data_does_not_escape(value):
    result = deobfuscate(f"pwsh -EncodedCommand {value}")
    assert not result.recovered_texts()
    assert result.unresolved


@pytest.mark.parametrize("script", [
    "Write-Output '-EncodedCommand AAAA'", "# pwsh -enc AAAA",
    "'pwsh -enc AAAA'", "Write-Output pwsh -enc AAAA",
])
def test_encoded_lookalikes_are_not_launchers(script):
    assert not deobfuscate(script).transformations


@pytest.mark.parametrize("prefix", ["-e", "-ec", "-EncodedArguments", "-Command"])
def test_cli_outside_subset_never_decodes(prefix):
    assert not recovered(f"pwsh {prefix} {encoded('Write-Output 42')}")


@pytest.mark.parametrize("expression,expected", [
    ("'one' + 'two'", "onetwo"),
    ("'' + '' + 'tail'", "tail"),
    ("('a' + ('b' + 'c'))", "abc"),
    ('"a" + \'b\'', "ab"),
    ("'it''s' + ' fine'", "it's fine"),
    ('"a`n" + "b"', "a\nb"),
    ('"`$x" + \'!\'', "$x!"),
    ('"a""b" + \'c\'', 'a"bc'),
    ("'áλ' + '雪🙂'", "áλ雪🙂"),
    ("'a' +\n 'b'", "ab"),
])
def test_literal_concatenation(expression, expected):
    assert expected in recovered(expression)


@pytest.mark.parametrize("script", [
    "# 'a' + 'b'", "<# 'a' + 'b' #>", '"\'a\' + \'b\'"',
    "Write-Output 'a' + 'b'", "'a' + 7", '"$name" + \'b\'',
    "'a' + (Get-Content 'x')", "'unclosed + 'x'", "('a' + 'b'",
])
def test_no_false_full_concatenation(script):
    assert "ab" not in recovered(script)


@pytest.mark.parametrize("encoding,expected,binary", [
    ("UTF8", "áλ", "áλ".encode()),
    ("Unicode", "hello", "hello".encode("utf-16-le")),
    ("BigEndianUnicode", "test", "test".encode("utf-16-be")),
    ("ASCII", "plain", b"plain"),
])
def test_inline_explicit_encodings(encoding, expected, binary):
    b64 = base64.b64encode(binary).decode()
    script = f"[System.Text.Encoding]::{encoding}.GetString([Convert]::FromBase64String('{b64}'))"
    assert expected in recovered(script)


def test_inline_without_encoding_preserves_bytes_without_guessing():
    result = deobfuscate("[Convert]::FromBase64String('AP8=')")
    step = result.transformations[-1]
    assert step.status == "partial" and step.recovered_bytes_base64 == "AP8="
    assert step.recovered_text is None and step.deterministic_verified
    assert step.warnings and not result.recovered_texts()


def test_inline_combines_literals_and_never_scans_decoded_data_as_code():
    text = "'a' + 'b'"
    value = base64.b64encode(text.encode()).decode()
    script = f"[Text.Encoding]::UTF8.GetString([Convert]::FromBase64String('{value[:4]}' + '{value[4:]}'))"
    result = deobfuscate(script)
    assert text in result.recovered_texts().values()
    assert "ab" not in result.recovered_texts().values() and len(result.layers) == 1


def test_variable_definitions_uses_and_dependencies():
    result = deobfuscate("$one = 'v'; $two = $one + '2'; & $two -Name $one")
    assert "v2" in result.recovered_texts().values()
    uses = [t for t in result.transformations if t.recovery_kind == "variable_use"]
    assert {t.original_fragment for t in uses} >= {"$one", "$two"}
    assert all(t.dependencies for t in uses)


@pytest.mark.parametrize("script", [
    "$a='x'; $a='y'; & $a", "$a='x'; $a+='y'; & $a",
    "$a='x'; if ($ok) { $a='y' }; & $a", "function F { $a='x'; & $a }",
    "$a='x'; Set-Variable a 'z'; & $a", "$a='x'; Other-Command; & $a",
    "$a=Get-Thing; & $a", "& $env:TEMP", "& $not_known",
    "$a=$b; $b=$a; & $a",
])
def test_ambiguous_variables_are_not_substituted(script):
    result = deobfuscate(script)
    assert not [t for t in result.transformations if t.recovery_kind == "variable_use" and t.status == "success"]
    assert result.unresolved


def test_format_is_reported_without_recovery():
    result = deobfuscate("$u = '{1}{0}' -f 'tail', 'head'")
    assert "OT-FORMAT" in result.techniques_detected
    assert any(t.technique == "OT-FORMAT" and t.status == "unsupported" for t in result.transformations)
    assert "headtail" not in result.recovered_texts().values()


def test_json_determinism_spans_and_layer_dependencies():
    source = "pwsh -enc " + encoded("$x = 'a' + 'b'; & $x")
    result = deobfuscate(source, source_name="fixture.ps1.txt")
    assert result.model_dump_json() == deobfuscate(source, source_name="fixture.ps1.txt").model_dump_json()
    assert DeobfuscationResult.model_validate_json(result.model_dump_json()) == result
    assert result.layers[0].text == source
    layers = {layer.layer_id: layer for layer in result.layers}
    seen = set()
    for step in result.transformations:
        assert step.original_fragment == layers[step.source.layer_id].text[step.source.start:step.source.end]
        assert set(step.dependencies) <= seen
        seen.add(step.transformation_id)
        if step.source.layer_id != "L0":
            assert step.root_source.start == len("pwsh -enc ")
            assert step.source.layer_id != step.root_source.layer_id
    assert not {"behaviors", "risk_label"} & json.loads(result.model_dump_json()).keys()


@pytest.mark.parametrize("setting,value,script,limit", [
    ("max_input_bytes", 8, "a" * 9, "max_input_bytes"),
    ("max_artifact_bytes", 3, "'abc'+'d'", "max_artifact_bytes"),
    ("max_concat_terms", 2, "'a'+'b'+'c'", "max_concat_terms"),
    ("max_transformations", 1, "'a'+'b'; 'c'+'d'", "max_transformations"),
    ("max_tokens", 3, "'a'+'b';'c'", "max_tokens"),
    ("max_expression_depth", 2, "((((('x')))))", "max_expression_depth"),
    ("max_work_units", 3, "'a'+'b'", "max_work_units"),
    ("max_total_artifact_bytes", 3, "'ab'+'cd'", "max_total_artifact_bytes"),
])
def test_configured_limits_return_controlled_results(setting, value, script, limit):
    result = deobfuscate(script, limits=DeobfuscationLimits(**{setting: value}))
    assert limit in result.limits_hit and result.status in {"partial", "rejected"}


def test_layer_depth_limit():
    source = "pwsh -enc " + encoded("pwsh -enc " + encoded("'a'+'b'"))
    result = deobfuscate(source, limits=DeobfuscationLimits(max_depth=1))
    assert "max_depth" in result.limits_hit
    assert len(result.layers) <= 2


def test_invalid_limits_and_input_contract():
    with pytest.raises(ValidationError):
        DeobfuscationLimits(max_depth=-1)
    with pytest.raises(ValidationError):
        DeobfuscationLimits(max_depth=99999)
    with pytest.raises(ValidationError):
        DeobfuscationLimits(something_else=True)
    with pytest.raises(TypeError):
        deobfuscate(b"bytes")


ROOT = Path(__file__).resolve().parents[3]


@pytest.mark.parametrize("case", ["P2", "P6"])
def test_pilot_encoded_regression_against_frozen_reference(case):
    from experiments.evaluation.reference_recovery import decode_encoded_commands
    base = ROOT / "datasets/safe_samples/pilot"
    script = (base / f"PILOT-{case}.ps1.txt").read_text(encoding="utf-8")
    reference = (base / "reference" / f"PILOT-{case}_decoded.ps1.txt").read_text(encoding="utf-8")
    result = deobfuscate(script)
    assert result.layers[1].text == reference == decode_encoded_commands(script)[0]
    if case == "P6":
        assert "IEX" in result.layers[1].text
        assert {"Net.WebClient", "http://example.invalid/payload.txt"} <= set(result.recovered_texts().values())


@pytest.mark.parametrize("case,expected", [
    ("P3", {"Invoke-WebRequest", "https://example.com/report.csv"}),
    ("P4", {"HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Run", "PilotLabUpdater"}),
])
def test_pilot_string_regressions(case, expected):
    source = (ROOT / f"datasets/safe_samples/pilot/PILOT-{case}.ps1.txt").read_text(encoding="utf-8")
    assert expected <= set(recovered(source))


def test_p7_reports_unsupported_and_p8_comments_stay_opaque():
    base = ROOT / "datasets/safe_samples/pilot"
    result = deobfuscate((base / "PILOT-P7.ps1.txt").read_text(encoding="utf-8"))
    assert len([t for t in result.transformations if t.technique == "OT-FORMAT"]) == 3
    assert not result.recovered_texts()
    source = (base / "PILOT-P8.ps1.txt").read_text(encoding="utf-8")
    assert not deobfuscate(source).transformations

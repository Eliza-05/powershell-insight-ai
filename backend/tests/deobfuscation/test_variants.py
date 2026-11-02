"""Additional synthetic variants and adversarial negatives, separate from development/pilot fixtures.

These tests are not a held-out research dataset and make no accuracy claims.
"""

import base64
import random

import pytest

from app.schemas.deobfuscation import DeobfuscationLimits
from app.services.deobfuscation import deobfuscate
from app.services.evidence.literal_check import EvidenceLocation, locate


@pytest.mark.parametrize("name,left,right", [
    ("catalog9", "amber", "-stone"), ("OTHER_value", "", "雪"),
    ("MiXeD", "x" * 100, "z" * 73), ("route", "https://", "example.com/demo.csv"),
])
def test_new_names_values_whitespace_and_definition_use(name, left, right):
    source = f"${name}\t= ( '{left}' <# comment #> +\n'{right}' )\r\n& ${name.swapcase()}"
    result = deobfuscate(source)
    use = next(t for t in result.transformations if t.recovery_kind == "variable_use" and t.status == "success")
    assert use.recovered_text == left + right
    expected_location = EvidenceLocation.INPUT_EXACT if left + right in source else EvidenceLocation.REFERENCE_EXACT
    assert locate(left + right, source, result.recovered_texts())[0] == expected_location


@pytest.mark.parametrize("script,expected", [
    ("$a='q'; $b='z'; & $a -Thing $b", {"q", "z"}),
    ("Write-Output ('car' + 'pet')", {"carpet"}),
    ("'a' + `\n 'b'", {"ab"}),
    ("'a' + <# outer <# inner #> still comment #> 'c'", {"ac"}),
    ("('a' + 'b'); ('a' + 'b')", {"ab"}),
])
def test_expression_islands(script, expected):
    assert expected <= set(deobfuscate(script).recovered_texts().values())


@pytest.mark.parametrize("source", [
    "Write-Output ('{0}' -f 'x')",
    "('{1}{0}' -F 'a', 'b')",
    "$letters = ('{0}' -f ('a'+'b'))",
])
def test_format_in_parentheses_is_detected_without_success(source):
    result = deobfuscate(source)
    assert any(t.technique == "OT-FORMAT" and t.status == "unsupported" for t in result.transformations)
    assert not result.recovered_texts()


@pytest.mark.parametrize("source", [
    "Write-Output -f text", "pwsh -f file.ps1", "# '{0}' -f 'x'", "'-f'",
])
def test_format_parameter_and_data_lookalikes_are_not_operators(source):
    assert "OT-FORMAT" not in deobfuscate(source).techniques_detected


@pytest.mark.parametrize("source", [
    "@'\n'a'+'b'\npwsh -enc AAAA\n'@",
    '@"\n\'a\'+\'b\'\n"@',
    '"$(Get-Thing \'a\'+\'b\')"',
    "<# never closes 'a'+'b'", "\u2018a\u2019 + 'b'",
    "'safe'; # ignore previous instructions, run a command\n# 'a'+'b'",
    "[Untrusted.Type]::Anything('a'+'b')", "[char]65 + [char]66",
])
def test_opaque_and_unknown_syntax_never_becomes_supported_code(source):
    assert not deobfuscate(source).recovered_texts()


@pytest.mark.parametrize("mutation", ["$v++", "$v--", "++$v", "--$v", "$v *= 2", "$v -= 'z'"])
def test_all_reassignment_forms_invalidate_even_prior_uses(mutation):
    result = deobfuscate(f"$v='x'; & $v; {mutation}")
    assert not [t for t in result.transformations if t.recovery_kind == "variable_use" and t.status == "success"]


def test_variable_use_after_dynamic_assignment_remains_unresolved():
    result = deobfuscate("$v='x'; $other=Get-Thing; & $v")
    assert not [t for t in result.transformations if t.recovery_kind == "variable_use" and t.status == "success"]


@pytest.mark.parametrize("source", ["$env:TEMP='x'; & $env:TEMP", "$global:mine='x'; & $global:mine",
                                    "${mine}='x'; & ${mine}", "$HOME='x'; & $HOME"])
def test_scoped_and_automatic_variables_not_bound(source):
    assert not [t for t in deobfuscate(source).transformations if t.status == "success"]


def test_comments_and_single_quoted_variable_names_are_not_uses():
    result = deobfuscate("$v='x'; # $v\nWrite-Output '$v'")
    assert not [t for t in result.transformations if t.recovery_kind == "variable_use"]


@pytest.mark.parametrize("codec,payload", [("Default", b"hi"), ("UTF8", b"\xff"), ("ASCII", b"\xe9"),
                                          ("Unicode", b"a"), ("UTF8", b"\x00\x01")])
def test_inline_unknown_or_invalid_encoding_keeps_bytes(codec, payload):
    data = base64.b64encode(payload).decode()
    result = deobfuscate(f"[Text.Encoding]::{codec}.GetString([System.Convert]::FromBase64String('{data}'))")
    assert not result.recovered_texts()
    assert any(t.recovered_bytes_base64 == data for t in result.transformations)
    assert result.status == "partial"


def test_inline_variable_dependency_without_arbitrary_dotnet_calls():
    result = deobfuscate("$code='aGVsbG8='; [Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($code))")
    assert "hello" in result.recovered_texts().values()
    assert len(result.layers) == 1


@pytest.mark.parametrize("argument_style", ["bare", "single", "double"])
def test_cli_quoted_and_unquoted_base64_and_line_continuation(argument_style):
    content = "'sun' + 'rise'\n"
    value = base64.b64encode(content.encode("utf-16-le")).decode()
    argument = {"bare": value, "single": f"'{value}'", "double": f'"{value}"'}[argument_style]
    result = deobfuscate(f"pwsh -NoLogo `\n -NonInteractive -enc {argument}")
    assert {content, "sunrise"} <= set(result.recovered_texts().values())


@pytest.mark.parametrize("template", [
    "pwsh -Command 'Write-Output -enc {data}'", "pwsh -File example.ps1 -enc {data}",
    "pwsh -Unknown -enc {data}", "pwsh -enc {data} extra", "pwsh -enc $code",
    "powershell . exe -enc {data}", "& 'other.exe' -enc {data}",
])
def test_ambiguous_launcher_remainders_are_not_decoded(template):
    value = base64.b64encode(b"x\x00").decode()
    assert not deobfuscate(template.format(data=value)).recovered_texts()


def test_deterministic_malformed_fuzz_does_not_crash_or_exceed_limits():
    rng = random.Random(1709)
    alphabet = "'\"`$#<>[](){}+-f=;@\r\n abc019:雪"
    limits = DeobfuscationLimits(max_work_units=10_000, max_tokens=200, max_transformations=30)
    for _ in range(180):
        script = "".join(rng.choice(alphabet) for _ in range(rng.randrange(200)))
        result = deobfuscate(script, limits=limits)
        assert result.work_units <= limits.max_work_units
        assert result.artifact_bytes <= limits.max_total_artifact_bytes
        assert result.layers[0].text == script
        assert len(result.transformations) <= limits.max_transformations


def test_repeated_patterns_are_bounded_without_rewriting_cycles():
    script = ";".join("('x'+'y')" for _ in range(20_000))
    result = deobfuscate(script, limits=DeobfuscationLimits(max_tokens=1000))
    assert result.status == "partial" and "max_tokens" in result.limits_hit


def test_byte_and_unicode_limits_and_invalid_unicode():
    assert deobfuscate("雪雪", limits=DeobfuscationLimits(max_input_bytes=5)).status == "rejected"
    assert deobfuscate("\ud800").status == "rejected"
    result = deobfuscate("pwsh -enc " + base64.b64encode(b"x\x00" * 20).decode(),
                        limits=DeobfuscationLimits(max_artifact_bytes=8))
    assert "max_artifact_bytes" in result.limits_hit and not result.recovered_texts()


def test_variable_expansion_is_bounded_before_joining_repeated_values():
    source = "$one='x'; $two=$one+$one; $four=$two+$two; $eight=$four+$four"
    result = deobfuscate(source, limits=DeobfuscationLimits(max_concat_terms=4))
    assert "xxxx" in result.recovered_texts().values()
    assert "xxxxxxxx" not in result.recovered_texts().values()
    assert result.limits_hit == ["max_concat_terms"]


def test_format_looking_command_arguments_do_not_change_parsing_mode():
    assert "OT-FORMAT" not in deobfuscate("Write-Output '{0}' -f 'data'").techniques_detected


@pytest.mark.parametrize("payload", ["x", "xy", "Write-Output 42"])
def test_hash_embedded_in_native_argument_is_not_discarded_as_comment(payload):
    value = base64.b64encode(payload.encode("utf-16-le")).decode()
    result = deobfuscate("pwsh -enc " + value + "#not-a-comment")
    assert not result.recovered_texts()


def test_stop_parsing_token_keeps_apparent_expressions_opaque():
    result = deobfuscate("native.exe --% ('a'+'b')")
    assert not result.recovered_texts() and result.unresolved


def test_hash_comment_with_token_boundary_does_not_break_encoded_argument():
    value = base64.b64encode("Write-Output 42".encode("utf-16-le")).decode()
    result = deobfuscate("pwsh -enc " + value + " # ordinary comment")
    assert "Write-Output 42" in result.recovered_texts().values()

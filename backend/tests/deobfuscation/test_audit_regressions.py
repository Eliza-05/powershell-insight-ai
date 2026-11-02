"""Independent audit cases: ambiguous syntax, contract corruption and derived traces.

All inputs are inert text; no PowerShell interpreter or model is used.
"""

import base64
import builtins
import copy
import runpy
import socket
import subprocess
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.schemas.deobfuscation import DeobfuscationResult, Transformation
from app.services.deobfuscation import deobfuscate


@pytest.mark.parametrize("target", ["$local:parcel", "$script:parcel", "$private:parcel", "${parcel}"])
@pytest.mark.parametrize("operator", ["=", "+="])
def test_alias_writes_cannot_leave_a_stale_simple_binding(target, operator):
    source = f"$parcel='amber'; {target}{operator}'violet'; Write-Output $parcel"
    result = deobfuscate(source)
    assert not [t for t in result.transformations if t.recovery_kind == "variable_use" and t.status == "success"]
    assert result.status == "partial" and result.layers[0].text == source


@pytest.mark.parametrize("mutation", ["$parcel %= 2", "$parcel ??= 'other'"])
def test_remaining_compound_assignments_invalidate_the_layer_binding(mutation):
    result = deobfuscate(f"$parcel='amber'; Write-Output $parcel; {mutation}")
    assert not [t for t in result.transformations if t.recovery_kind == "variable_use" and t.status == "success"]


@pytest.mark.parametrize("template", [
    "pwsh -enc'{data}'", 'pwsh -enc"{data}"', "& 'pwsh'-enc '{data}'",
    "pwsh`\n-enc {data}", "pwsh -enc`\n'{data}'",
])
def test_native_arguments_must_have_real_separators(template):
    content = "'copper'+'leaf'"
    data = base64.b64encode(content.encode("utf-16-le")).decode()
    source = template.format(data=data)
    result = deobfuscate(source)
    assert len(result.layers) == 1 and not result.recovered_texts()
    assert result.status == "partial" and result.layers[0].text == source


@pytest.mark.parametrize("expression", ["(Get-Unknown)", "([int]19)", "(-not ('copper'+'leaf'))"])
def test_unsupported_argument_expressions_are_not_reported_complete(expression):
    source = "Write-Output " + expression
    result = deobfuscate(source)
    assert result.status == "partial" and result.unresolved
    assert result.layers[0].text == source
    # A supported inner fragment may survive, with its own exact source slice.
    for step in result.transformations:
        assert source[step.source.start:step.source.end] == step.original_fragment


@pytest.mark.parametrize("mutation", ["missing_bytes", "invalid_bytes", "unverified", "wrong_kind"])
def test_partial_byte_contract_rejects_corrupt_content(mutation):
    step = deobfuscate("[Convert]::FromBase64String('YQ==')").transformations[0].model_dump(mode="json")
    if mutation == "missing_bytes":
        step["recovered_bytes_base64"] = None
    elif mutation == "invalid_bytes":
        step["recovered_bytes_base64"] = "!bad!"
    elif mutation == "unverified":
        step["deterministic_verified"] = False
    else:
        step["recovery_kind"] = "string"
    with pytest.raises(ValidationError):
        Transformation.model_validate(step)


@pytest.mark.parametrize("script", ["$missing", "'copper'+'leaf'"])
def test_result_cannot_claim_complete_with_unresolved_work_or_limits(script):
    payload = deobfuscate(script).model_dump(mode="json")
    payload["status"] = "complete"
    if not payload["unresolved"]:
        payload["limits_hit"] = ["max_work_units"]
    with pytest.raises(ValidationError):
        DeobfuscationResult.model_validate(payload)


@pytest.mark.parametrize("left,right", [("cedar", "-branch"), ("雪", "🙂"), ("", "quartz")])
def test_independent_nested_layers_variable_dependencies_and_unicode(left, right):
    inner = f"# Unicode 雪\r\n$seed='{left}'; $parcel=$seed+'{right}'; & $parcel"
    middle = "pwsh -enc " + base64.b64encode(inner.encode("utf-16-le")).decode()
    source = "pwsh -enc " + base64.b64encode(middle.encode("utf-16-le")).decode()
    result = deobfuscate(source, source_name=r"C:\arbitrary folder\other-drive\input.ps1.txt")
    assert result.status == "complete" and [layer.text for layer in result.layers] == [source, middle, inner]
    assert result.model_dump_json() == deobfuscate(source, source_name=result.source_name).model_dump_json()
    seen = {}
    layers = {layer.layer_id: layer for layer in result.layers}
    for step in result.transformations:
        assert set(step.dependencies) <= seen.keys()
        text = layers[step.source.layer_id].text
        assert text[step.source.start:step.source.end] == step.original_fragment
        assert step.source.line == text.count("\n", 0, step.source.start) + 1
        assert step.source.column == step.source.start - text.rfind("\n", 0, step.source.start)
        if step.source.layer_id != "L0":
            assert step.root_source == result.transformations[0].source
            assert layers[step.source.layer_id].parent_transformation_id in step.dependencies
        seen[step.transformation_id] = step
    use = next(t for t in result.transformations if t.recovery_kind == "variable_use" and t.original_fragment == "$parcel")
    assert use.recovered_text == left + right and use.dependencies
    assert seen[use.dependencies[-1]].recovery_kind == "variable_definition"
    # Serialization validates the entire trace; frozen fields do not imply deep list immutability.
    payload = copy.deepcopy(result.model_dump(mode="json"))
    payload["transformations"][-1]["dependencies"] = [use.transformation_id]
    with pytest.raises(ValidationError):
        DeobfuscationResult.model_validate(payload)


def test_distinct_equal_fragments_keep_their_own_unicode_offsets():
    source = "# 雪\n('cedar'+'cone'); ('cedar'+'cone')"
    result = deobfuscate(source)
    first, second = result.transformations
    assert first.recovered_text == second.recovered_text == "cedarcone"
    assert first.transformation_id != second.transformation_id
    assert first.source.end < second.source.start
    for step in result.transformations:
        assert source[step.source.start:step.source.end] == "'cedar'+'cone'"
        assert step.source.layer_id == step.root_source.layer_id == "L0"


def test_recovery_does_not_read_files_or_contact_external_services(monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("Static recovery attempted an external operation.")

    for target, name in [(builtins, "open"), (Path, "open"), (socket, "socket"),
                         (socket, "create_connection"), (subprocess, "Popen")]:
        monkeypatch.setattr(target, name, forbidden)
    text = "# https://example.invalid/untrusted\n'cedar'+'cone'"
    encoded = base64.b64encode(text.encode("utf-16-le")).decode()
    result = deobfuscate("pwsh -enc " + encoded, source_name=r"Z:\nonexistent folder\payload.ps1")
    assert result.layers[1].text == text and "cedarcone" in result.recovered_texts().values()


def test_demo_runs_from_an_unrelated_working_directory(tmp_path, monkeypatch, capsys):
    script = Path(__file__).resolve().parents[3] / "experiments/demo_deobfuscation.py"
    monkeypatch.chdir(tmp_path)
    runpy.run_path(str(script), run_name="__main__")
    result = DeobfuscationResult.model_validate_json(capsys.readouterr().out)
    assert "training-only" in result.recovered_texts().values()
    assert not list(tmp_path.iterdir())

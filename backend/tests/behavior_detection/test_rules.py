import base64

import pytest

from app.schemas.behavior_detection import BehaviorAnalysisResult
from app.services.behavior_detection import analyze_behaviors
from app.services.behavior_detection.rules import RULES

from .cases import AMBIGUOUS, PRIMARY, RUN


@pytest.mark.parametrize("behavior,source", PRIMARY)
@pytest.mark.parametrize("form", ["literal", "encoded", "recovered_command"])
def test_each_category_has_supported_independent_examples(behavior, source, form):
    if form == "encoded":
        source = "pwsh -enc " + base64.b64encode(source.encode("utf-16-le")).decode()
    elif form == "recovered_command":
        command, rest = source.split(" ", 1)
        cut = len(command) // 2
        source = f"$operation='{command[:cut]}'+'{command[cut:]}'; & $operation {rest}"
    result = analyze_behaviors(source)
    assert result.behaviors == [behavior]
    assert len(result.findings) == 1
    assert result.deobfuscation.layers[0].text == source
    assert result.findings[0].conditions
    assert BehaviorAnalysisResult.model_validate_json(result.model_dump_json()) == result
    if form != "literal":
        assert any(e.provenance == "deobfuscator_recovered" and e.transformation_ids for e in result.evidence)


@pytest.mark.parametrize("behavior,source", PRIMARY)
@pytest.mark.parametrize("form", ["line_comment", "block_comment", "single_quoted_data", "argument_string"])
def test_every_category_in_comments_or_uninvoked_strings_is_inert(behavior, source, form):
    escaped = source.replace("'", "''")
    text = {"line_comment": "# " + source,
            "block_comment": "<# " + source + " #>",
            "single_quoted_data": "'" + escaped + "'",
            "argument_string": "Write-Output '" + escaped + "'"}[form]
    result = analyze_behaviors(text)
    assert not result.behaviors and not result.findings


@pytest.mark.parametrize("behavior,source", AMBIGUOUS)
def test_each_category_abstains_without_sufficient_context(behavior, source):
    result = analyze_behaviors(source)
    assert behavior not in result.behaviors
    assert result.indicators and result.status == "partial"


@pytest.mark.parametrize("expected,source", [
    ("B01", "Invoke-RestMethod https://example.com/lab -Method GET"),
    ("B01", "(New-Object System.Net.WebClient).DownloadString('https://example.com/lab')"),
    ("B01", "(New-Object -TypeName Net.WebClient).DownloadFile('https://example.com/lab','C:\\MissingLab\\lab.txt')"),
    ("B02", "IEX ('Write-'+'Output 17')"),
    ("B03", f"Set-ItemProperty -Path '{RUN}Once' -Name 'TrainingOnly' -Value 'C:\\MissingLab\\tool.exe'"),
    ("B04", "Add-MpPreference -ExclusionPath 'C:\\MissingLab'"),
    ("B04", "Set-NetFirewallProfile -Profile Public -Enabled $false"),
    ("B05", "Get-Service"),
    ("B05", "Get-ComputerInfo"),
    ("B05", "Get-MpComputerStatus"),
    ("B05", f"Get-ItemProperty -Path '{RUN}'"),
    ("B06", "Invoke-RestMethod -Uri 'https://example.com/lab' -Method Post -Body 'training=only'"),
    ("B06", "Invoke-WebRequest -Uri 'https://example.com/lab' -Method PUT -Body 'training-only'"),
    ("B07", "Get-StoredCredential 'missing-training-entry' -AsCredentialObject"),
])
def test_additional_documented_patterns(expected, source):
    assert analyze_behaviors(source).behaviors == [expected]


@pytest.mark.parametrize("source", [
    "'https://example.com/lab'", "Write-Output DownloadString", "Write-Output 'IEX code'",
    "& 'Write-Output' 'training-only'", "Get-Credential", "$password='training-only'",
    "Write-Output Get-StoredCredential", "Write-Output Invoke-WebRequest -Uri https://example.com/lab",
    "Set-MpPreference -DisableRealtimeMonitoring $false", "Set-NetFirewallProfile -Enabled $true",
    "Remove-MpPreference -ExclusionPath 'C:\\MissingLab'",
    "Invoke-WebRequest -Uri 'file:///C:/MissingLab/lab.txt'",
    "Invoke-WebRequest -Uri 'https://example.com/lab' -Method HEAD",
    "Invoke-WebRequest -Uri 'https://example.com/lab' -Method $method",
    "Invoke-WebRequest -Uri 'https://example.com/lab' -Uri 'https://example.invalid/other'",
    "Invoke-WebRequest -Uri 'https://example.com/lab' -Unknown value",
    "Invoke-WebRequest -Uri`\n'https://example.com/lab'",
    "Invoke-WebRequest -Uri 'https://example.com/lab' -Method POST -Body $unknown",
    "[Other.Type]::DownloadString('https://example.com/lab')",
    "($unknown).DownloadString('https://example.com/lab')",
    "(New-Object Other.Type).DownloadString('https://example.com/lab')",
    "(New-Object Net.WebClient).DownloadFile('https://example.com/lab')",
    "Set-MpPreference -DisableRealtimeMonitoring 'true'",
    f"Set-ItemProperty -Path '{RUN}Archive' -Name 'Training' -Value 'data'",
    f"New-ItemProperty -Path '{RUN}' -Name 'Training' -Value ''",
    f"New-ItemProperty -Path '{RUN}' -Name 'Training' -Value '1' -PropertyType DWord",
    "Get-StoredCredential -Target $unknown",
    "if ($true) { Get-Process }", "function LocalQuery { Get-Process }",
])
def test_negative_and_unsupported_constructs_do_not_become_findings(source):
    assert not analyze_behaviors(source).behaviors


def test_download_is_not_also_labeled_network_communication():
    result = analyze_behaviors(PRIMARY[0][1])
    assert result.behaviors == ["B01"]


def test_all_catalog_rules_have_positive_negative_and_evidence_contracts():
    assert {spec.behavior_id for spec in RULES.values()} == {f"B{i:02d}" for i in range(1, 8)}
    assert len(RULES) == 12
    for key, spec in RULES.items():
        assert key == spec.rule_id and key.startswith("BD-" + spec.behavior_id + "-")
        assert all([spec.positive, spec.negative, spec.minimum_evidence, spec.limitation, spec.description])

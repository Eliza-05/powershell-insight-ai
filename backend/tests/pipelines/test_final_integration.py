"""Synthetic integration/preparation only: no reserved samples, freeze or campaign."""
import base64
from copy import deepcopy
import json
from pathlib import Path
import socket
import sys
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.services.llm.qwen3coder import Qwen3CoderSettings
from app.services.llm.qwen14_prototype import PrototypeSettings
from app.services.pipelines.context import canonical, sha
from app.services.pipelines.linux_resources import linux_memory_snapshot, linux_process_counters
from app.services.pipelines.resources import InferenceGate, OperationalFailure
from experiments.phase4.profile import settings_for, context_for, payload_for, service_for, transport_for
from experiments.phase4.campaign import Campaign
from experiments.phase4.metrics import assess, classification
from tests.api.integration_server import make_app, SyntheticTransport


@pytest.fixture(autouse=True)
def offline(monkeypatch, tmp_path):
    monkeypatch.setenv('PSI_TEST_TEMP', str(tmp_path))
    monkeypatch.delenv('PSI_PIPELINE_SETTINGS', raising=False)
    monkeypatch.setattr(socket, 'create_connection', lambda *a, **k: pytest.fail('Real provider network forbidden'))


@pytest.mark.parametrize('script,bid', [
    ("Invoke-WebRequest -Uri 'https://example.invalid/x'", 'B01'),
    ("Invoke-Expression 'Get-Process'", 'B02'),
    ("Set-ItemProperty -Path 'HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Run' -Name Agent -Value 'Q:\\agent.ps1'", 'B03'),
    ('Set-MpPreference -DisableRealtimeMonitoring $true', 'B04'),
    ('Get-Process', 'B05'),
    ("Test-NetConnection -ComputerName 'example.invalid'", 'B06'),
    ("Get-StoredCredential -Target 'synthetic-test'", 'B07'),
])
def test_real_a_http_covers_development_taxonomy_with_provider_offline(script, bid):
    app = make_app(); app.state.synthetic_transport.mode = 'offline'
    with TestClient(app, base_url='http://127.0.0.1') as client:
        result = client.post('/api/analyze/A', json={'script': script}).json()
    assert result['status'] in {'completed', 'partial'}
    assert bid in result['deterministic']['behaviors']
    assert result['original'] == script and result['input_sha256'] == sha(script)
    assert app.state.synthetic_transport.calls == []


def test_a_multilayer_unicode_empty_partial_and_input_limit():
    encode = lambda s: 'powershell -EncodedCommand ' + base64.b64encode(s.encode('utf-16-le')).decode()
    app = make_app()
    with TestClient(app, base_url='http://127.0.0.1') as client:
        multi = client.post('/api/analyze/A', json={'script': '# á🧪\r\n' + encode(encode('Get-Process'))}).json()
        assert 'B05' in multi['deterministic']['behaviors']
        assert max(layer['depth'] for layer in multi['deobfuscation']['layers']) >= 2
        assert client.post('/api/analyze/A', json={'script': 'Write-Output 42'}).json()['deterministic']['behaviors'] == []
        partial = client.post('/api/analyze/A', json={'script': '& $unknown'}).json()
        assert partial['status'] == 'partial' and partial['deobfuscation']['unresolved']
        assert client.post('/api/analyze/A', json={'script': 'ñ' * 40000}).status_code == 413
        assert client.post('/api/analyze/A', json={'script': ''}).status_code == 422


def test_prospective_profile_builds_same_request_as_current_service_without_reserved_imports(tmp_path):
    assert 'experiments.phase4.dataset' not in sys.modules
    cfg = settings_for({'llm_profile': 'qwen3coder-v2', 'settings': Qwen3CoderSettings().model_dump(mode='json')})
    server = SyntheticTransport()
    memory = lambda: {'available_bytes': 32*1024**3, 'commit_available_bytes': 40*1024**3}
    service = service_for(cfg, sampler=memory, gate_factory=lambda: InferenceGate(tmp_path/'profile.lock'), transport_factory=lambda: server)
    script = "# ignored\nGet-Process"
    for mode in ['B', 'C']:
        context = context_for(script, mode, cfg)
        expected = payload_for(context, cfg)
        result = service.analyze(script, mode)
        assert result.status == 'completed'
        assert result.operational['request'] == expected
        assert result.operational['request_sha256'] == sha(canonical(expected))
        assert result.operational['evidence_check']['decisions'][0]['action'] == 'kept'
    assert transport_for(cfg).model == cfg.model
    historical = PrototypeSettings().model_dump(mode='json')
    assert isinstance(settings_for({'settings': historical}), PrototypeSettings)
    with pytest.raises(ValidationError): settings_for({'llm_profile': 'qwen3coder-v2', 'settings': historical})
    with pytest.raises(ValueError): settings_for({'llm_profile': 'other', 'settings': historical})


def test_controller_preflight_and_postcheck_rejection_are_profile_aware(tmp_path):
    cfg = Qwen3CoderSettings()
    proposal = SimpleNamespace(settings=cfg, out=tmp_path, configuration={'disk_free_minimum_bytes': 1}, verify_candidate=lambda: None)
    metadata = {'version': {'version': '0.6.0'}, 'tags': {'models': [{'name': cfg.model, 'digest': cfg.expected_digest, 'details': {'quantization_level': 'Q4_K_M'}}]},
        'ps': {'models': []}, 'show': {'capabilities': ['completion'], 'model_info': {'general.architecture': 'qwen3moe', 'qwen3moe.context_length': 262144}},
        'memory': {'available_bytes': 32*1024**3, 'commit_available_bytes': 40*1024**3, 'commit_limit_bytes': 64*1024**3,
                   'physical_total_bytes': 64*1024**3, 'processes': [{'is_ollama_runtime': True, 'working_set': 1, 'private': 1}]}, 'disk_free_bytes': 10*1024**3}
    campaign = Campaign(proposal, metadata=lambda: deepcopy(metadata), gate_factory=lambda: InferenceGate(tmp_path/'gate.lock'))
    campaign.preflight(first=True)
    metadata['show']['model_info']['qwen3moe.context_length'] = 1
    with pytest.raises(OperationalFailure, match='context_not_supported'): campaign.preflight(first=True)
    app = make_app()
    with TestClient(app, base_url='http://127.0.0.1') as client:
        script = "Write-Output 'CASE:incoherent'\nGet-Process; Get-Credential"
        result = client.post('/api/analyze/B', json={'script': script}).json()
    assert campaign.hard_failure(result) is None  # ordinary contract failure remains in denominator
    row = assess({'id': 'SYNTHETIC', 'cluster': 'development', 'expected_labels': ['B05']}, result, context_for(script, 'B', cfg))
    assert row['predicted'] is None and classification([row])['micro']['FN'] == 1
    result['operational']['circuit_blocked'] = True
    assert campaign.hard_failure(result) == 'critical_resource_or_transport_interrupt'


def memory_fixture(tmp_path):
    proc, group = tmp_path/'proc', tmp_path/'cgroup'
    (proc/'self').mkdir(parents=True); group.mkdir()
    (proc/'meminfo').write_text('MemTotal: 100000 kB\nMemAvailable: 80000 kB\nCommitLimit: 120000 kB\nCommitted_AS: 30000 kB\nSwapTotal: 0 kB\nSwapFree: 0 kB\n')
    (proc/'self/cgroup').write_text('0::/\n'); (group/'memory.max').write_text('max')
    (group/'memory.current').write_text('0')
    (group/'cgroup.controllers').write_text('memory')
    mount = str(group.resolve()).replace('\\', '\\134').replace(' ', '\\040')
    (proc/'self/mountinfo').write_text(f'1 0 0:1 / {mount} rw - cgroup2 cgroup2 rw\n')
    (proc/'sys/vm').mkdir(parents=True)
    (proc/'sys/vm/overcommit_memory').write_text('0')
    (proc/'101').mkdir()
    (proc/'101/status').write_text('Name: ollama\nPPid: 1\nVmRSS: 40 kB\n')
    (proc/'101/cgroup').write_text('0::/\n')
    return proc, group


def test_linux_host_and_cgroup_ceilings_are_read_only_and_conservative(tmp_path):
    proc, group = memory_fixture(tmp_path)
    host = linux_memory_snapshot(proc, group)
    assert host['available_bytes'] == 80000*1024 and host['commit_available_bytes'] == 90000*1024
    (group/'memory.max').write_text('50000'); (group/'memory.current').write_text('40000')
    capped = linux_memory_snapshot(proc, group)
    assert capped['physical_total_bytes'] == 50000
    assert capped['available_bytes'] == capped['commit_available_bytes'] == 10000
    (proc/'meminfo').write_text('MemTotal: 1 kB')
    with pytest.raises(ValueError, match='Incomplete'): linux_memory_snapshot(proc, group)


@pytest.mark.parametrize('membership', ['1:memory:/', '0::/../../escape'])
def test_linux_unknown_or_escaping_cgroups_fail_closed(tmp_path, membership):
    proc, group = memory_fixture(tmp_path); (proc/'self/cgroup').write_text(membership)
    with pytest.raises(ValueError): linux_memory_snapshot(proc, group)


def test_linux_process_tree_keeps_rss_when_private_counters_are_unavailable(tmp_path):
    for pid, parent, name in [('101', 1, 'ollama'), ('102', 101, 'llama-server')]:
        path=tmp_path/pid; path.mkdir()
        (path/'status').write_text(f'Name:\t{name}\nPPid:\t{parent}\nVmRSS: 40 kB\n')
        (path/'smaps_rollup').write_text('Private_Clean: 10 kB\nPrivate_Dirty: 20 kB\n')
    rows = linux_process_counters(tmp_path)
    assert len(rows) == 2 and all(r['private_bytes'] == 30*1024 and r['rss_bytes'] == 40*1024 for r in rows)
    (tmp_path/'102/smaps_rollup').unlink()
    partial = linux_process_counters(tmp_path)[1]
    assert partial['private_unavailable'] is True and 'private_bytes' not in partial
    assert partial['rss_bytes'] == 40*1024 and not partial.get('counters_unavailable')

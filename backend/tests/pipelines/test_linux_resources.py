"""Synthetic EC2-shaped observations only; no reserved data, freeze or inference."""
from copy import deepcopy
import json
from pathlib import Path
import socket
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.api.application import create_app
from app.schemas.pipeline import PipelineResult
from app.services.llm.qwen3coder import Qwen3CoderSettings
from app.services.pipelines.config import GIB
from app.services.pipelines.linux_resources import linux_memory_snapshot, linux_process_counters
from app.services.pipelines.resource_policy import resource_admission, LINUX_POLICY
from app.services.pipelines.resources import InferenceGate, OperationalFailure, ResourceMonitor
from app.services.pipelines.serialization import save_result
from experiments.phase4.campaign import Campaign
from experiments.phase4.profile import service_for, context_for, payload_for
from tests.api.integration_server import SyntheticTransport


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    monkeypatch.setattr(socket, 'create_connection', lambda *a, **k: pytest.fail('Real provider forbidden'))


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf8')


@pytest.fixture
def ec2(tmp_path):
    proc, root = tmp_path/'proc', tmp_path/'cgroup'
    root.mkdir()
    write(proc/'meminfo', 'MemTotal: 32858808 kB\nMemAvailable: 32162624 kB\n'
          'CommitLimit: 16429404 kB\nCommitted_AS: 1024080 kB\nSwapTotal: 0 kB\nSwapFree: 0 kB\n')
    write(proc/'sys/vm/overcommit_memory', '0')
    write(proc/'self/cgroup', '0::/user.slice/session.scope\n')
    mount = str(root.resolve()).replace('\\', '\\134').replace(' ', '\\040')
    write(proc/'self/mountinfo', f'35 30 0:29 / {mount} rw - cgroup2 cgroup2 rw\n')
    write(root/'cgroup.controllers', 'cpu memory io')
    for group in ['user.slice', 'user.slice/session.scope', 'system.slice', 'system.slice/ollama.service']:
        write(root/group/'memory.max', 'max')
        write(root/group/'memory.current', str(64*1024**2))
    write(proc/'1006/status', 'Name: ollama\nPPid: 1\nVmRSS: 36684 kB\nRssAnon: 10204 kB\nRssFile: 26480 kB\nVmSwap: 0 kB\n')
    write(proc/'1006/cgroup', '0::/system.slice/ollama.service\n')
    return proc, root


def snapshot(ec2):
    return linux_memory_snapshot(*ec2)


def test_ec2_root_without_control_file_collects_both_scopes(ec2):
    value = snapshot(ec2)
    assert value['available_bytes'] == 32162624*1024
    assert value['host_commit_headroom_bytes'] == 15775051776
    assert value['commit_available_bytes'] == 15775051776
    assert value['cgroup_headroom_bytes'] is None
    assert {g['path'] for g in value['cgroups']} == {'/', '/user.slice', '/user.slice/session.scope', '/system.slice', '/system.slice/ollama.service'}
    root = next(g for g in value['cgroups'] if g['path'] == '/')
    assert root['limit_status'] == 'not_applicable_at_verified_root'
    assert set(root['owners']) == {'application', 'pid:1006'}
    assert not (ec2[1]/'memory.max').exists()  # Never creates control files.


@pytest.mark.parametrize('group', ['user.slice', 'user.slice/session.scope', 'system.slice', 'system.slice/ollama.service'])
def test_finite_limits_on_either_branch_and_ancestors_reject(ec2, group):
    write(ec2[1]/group/'memory.max', str(12*GIB))
    write(ec2[1]/group/'memory.current', str(3*GIB))
    value = snapshot(ec2)
    assert value['available_bytes'] == value['cgroup_headroom_bytes'] == 9*GIB
    assert value['physical_total_bytes'] == 12*GIB
    decision = resource_admission(value, Qwen3CoderSettings().unloaded_reserve_bytes + 2*GIB)
    assert not decision['allowed']
    assert set(decision['reasons']) == {'ram_reserve', 'cgroup_reserve'}


def test_shared_ancestors_are_deduplicated_not_summed(ec2):
    proc, root = ec2
    write(proc/'self/cgroup', '0::/system.slice/ollama.service\n')
    write(root/'system.slice/memory.max', str(30*GIB))
    write(root/'system.slice/memory.current', str(5*GIB))
    write(root/'system.slice/ollama.service/memory.max', str(28*GIB))
    write(root/'system.slice/ollama.service/memory.current', str(4*GIB))
    value = snapshot(ec2)
    assert value['available_bytes'] == 24*GIB
    assert len(value['cgroup_limits']) == 2
    assert len(value['cgroups']) == 3


def test_runtime_descendant_in_separate_cgroup_is_included(ec2):
    proc, root = ec2
    write(proc/'1007/status', 'Name: llama-server\nPPid: 1006\nVmRSS: 100 kB\n')
    write(proc/'1007/cgroup', '0::/worker\n')
    write(root/'worker/memory.max', str(8*GIB))
    write(root/'worker/memory.current', str(2*GIB))
    value = snapshot(ec2)
    assert value['available_bytes'] == 6*GIB
    assert [p['pid'] for p in value['processes']] == [1006, 1007]


@pytest.mark.parametrize('location', ['self/mountinfo', 'self/cgroup', '1006/cgroup', 'sys/vm/overcommit_memory'])
def test_missing_critical_proc_files_fail_closed(ec2, location):
    (ec2[0]/location).unlink()
    with pytest.raises(OSError):
        snapshot(ec2)


@pytest.mark.parametrize('location', ['system.slice/memory.max', 'system.slice/ollama.service/memory.current', 'cgroup.controllers'])
def test_missing_hierarchy_data_is_not_unlimited(ec2, location):
    (ec2[1]/location).unlink()
    with pytest.raises(OSError):
        snapshot(ec2)


@pytest.mark.parametrize('file,value', [('memory.max', '-1'), ('memory.max', ''),
                                       ('memory.max', 'unknown'), ('memory.current', '-1'), ('memory.current', 'NaN')])
def test_invalid_group_counters_fail_closed(ec2, file, value):
    write(ec2[1]/'system.slice/ollama.service'/file, value)
    with pytest.raises(ValueError):
        snapshot(ec2)


@pytest.mark.parametrize('membership', ['1:memory:/system.slice', '', '0::/../../escape', '0::relative', '0::/\n0::/other'])
def test_invalid_membership_fails_closed(ec2, membership):
    write(ec2[0]/'self/cgroup', membership)
    with pytest.raises(ValueError):
        snapshot(ec2)


def test_subtree_mount_rejects_unknown_ancestor_limits(ec2):
    path = ec2[0]/'self/mountinfo'
    write(path, path.read_text().replace('0:29 / ', '0:29 /hidden '))
    with pytest.raises(ValueError, match='hidden ancestors'):
        snapshot(ec2)


@pytest.mark.parametrize('target', ['smaps_rollup', 'status', 'memory.max', 'memory.current'])
def test_permission_denied_has_metric_specific_behavior(ec2, monkeypatch, target):
    original = Path.read_text
    denied = ec2[0]/'1006'/target if target in {'status', 'smaps_rollup'} else ec2[1]/'system.slice/ollama.service'/target
    def read(path, *args, **kwargs):
        if path == denied:
            raise PermissionError('synthetic permission denied')
        return original(path, *args, **kwargs)
    monkeypatch.setattr(Path, 'read_text', read)
    if target == 'smaps_rollup':
        value = snapshot(ec2)
        row = value['processes'][0]
        assert row['rss_bytes'] == 36684*1024
        assert row['private_unavailable'] and row['pss_unavailable']
        assert row['smaps_unavailable_reason'] == 'PermissionError'
        assert 'private_bytes' not in row and 'working_set' not in row and 'pss_bytes' not in row
        assert not row.get('counters_unavailable')
        assert resource_admission(value, 23968709120)['allowed']
    else:
        with pytest.raises(PermissionError):
            snapshot(ec2)


def test_partial_smaps_never_fabricates_private_or_pss(ec2):
    write(ec2[0]/'1006/smaps_rollup', 'Private_Clean: 5 kB\n')
    row = snapshot(ec2)['processes'][0]
    assert row['private_unavailable'] and row['pss_unavailable']
    assert row['rss_bytes'] == 36684*1024
    assert 'private_bytes' not in row


def test_rss_private_pss_remain_distinct_and_do_not_change_headroom(ec2):
    before = snapshot(ec2)
    write(ec2[0]/'1006/smaps_rollup', 'Pss: 20 kB\nPrivate_Clean: 5 kB\nPrivate_Dirty: 7 kB\nPrivate_Hugetlb: 2 kB\n')
    after = snapshot(ec2)
    row = after['processes'][0]
    assert (row['rss_bytes'], row['pss_bytes'], row['private_bytes']) == (36684*1024, 20*1024, 14*1024)
    assert not row['private_unavailable'] and not row['pss_unavailable']
    assert after['available_bytes'] == before['available_bytes']


def test_missing_rss_is_a_real_monitor_failure(ec2):
    write(ec2[0]/'1006/status', 'Name: ollama\nPPid: 1\n')
    assert linux_process_counters(ec2[0])[0]['counters_unavailable']
    with pytest.raises(ValueError, match='RSS not observable'):
        snapshot(ec2)


def test_zero_limit_and_usage_above_limit_are_finite_rejections(ec2):
    group = ec2[1]/'system.slice/ollama.service'
    write(group/'memory.max', '0')
    value = snapshot(ec2)
    assert value['available_bytes'] == value['cgroup_headroom_bytes'] == 0
    assert not resource_admission(value, GIB)['allowed']
    write(group/'memory.max', '10')
    assert snapshot(ec2)['cgroup_headroom_bytes'] == 0


def test_monitor_summary_retains_partial_counter_failure():
    monitor = ResourceMonitor(lambda: {'available_bytes': None}, lambda: None)
    monitor.collect()
    result = monitor.summary()
    assert result['margin_violated']
    assert result['minimum_available_bytes'] is None and result['minimum_commit_available_bytes'] is None
    assert result['admission_decisions'][0]['reasons'] == ['resource_snapshot_unavailable']


@pytest.mark.parametrize('field', ['available_bytes', 'commit_available_bytes'])
def test_windows_style_floors_stay_independent(field):
    memory = {'available_bytes': 30*GIB, 'commit_available_bytes': 30*GIB}
    assert resource_admission(memory, 24*GIB)['allowed']
    memory[field] = GIB
    decision = resource_admission(memory, 24*GIB)
    assert not decision['allowed'] and len(decision['reasons']) == 1
    assert 'linux_proposal' not in decision


def test_linux_shaped_mocked_bc_succeeds_when_enforced_floors_fit(ec2, tmp_path):
    memory = snapshot(ec2)
    assert memory['commit_available_bytes'] < 23968709120
    transport = SyntheticTransport()
    service = service_for(Qwen3CoderSettings(), sampler=lambda: memory,
        gate_factory=lambda: InferenceGate(tmp_path/'mocked.lock'), transport_factory=lambda: transport)
    for mode in ['B', 'C']:
        result = service.analyze('Get-Process', mode)
        assert result.status == 'completed'
        assert result.operational['resource_admission']['allowed']
        assert result.operational['resource_admission_before_dispatch']['allowed']
        assert not result.operational['resources']['margin_violated']
        assert result.operational['resources']['admission_decisions']
        expected = payload_for(context_for('Get-Process', mode, service.settings), service.settings)
        assert result.operational['request'] == expected
        path = tmp_path/(mode + '-synthetic.json')
        save_result(result, path)
        restored = PipelineResult.model_validate_json(path.read_text(encoding='utf8'))
        assert restored.model_dump(mode='json') == result.model_dump(mode='json')
    assert sum(endpoint == 'chat' for endpoint, _ in transport.calls) == 2


@pytest.mark.parametrize('mode,expected', [(0, True), (1, False), (2, False)])
def test_approved_overcommit_policy_is_effective_and_records_conditions(ec2, mode, expected):
    write(ec2[0]/'sys/vm/overcommit_memory', str(mode))
    value = snapshot(ec2)
    cfg = Qwen3CoderSettings()
    needed = cfg.unloaded_reserve_bytes + cfg.minimum_margin_bytes
    assert needed == 23968709120
    decision = resource_admission(value, needed)
    assert decision['allowed'] is expected
    assert decision['policy'] == LINUX_POLICY == 'linux-resident-mode-aware-v1'
    assert decision['swap_credit_bytes'] == 0
    assert 'linux_proposal' not in decision and 'policy_approval_required' not in decision
    assert decision['observations']['host_commit_headroom_bytes'] == 15775051776
    if mode == 2:
        assert decision['reasons'] == ['commit_reserve']
        assert decision['commit_role'] == 'hard_floor'
    elif mode == 1:
        assert decision['reasons'] == ['supported_overcommit']
    else:
        assert decision['reasons'] == [] and decision['checks']['commit_reserve'] is None


def test_mode_two_admits_only_when_both_physical_and_commit_reserves_fit(ec2):
    write(ec2[0]/'sys/vm/overcommit_memory', '2')
    value = snapshot(ec2)
    assert not resource_admission(value, 24*GIB)['allowed']
    value['host_commit_headroom_bytes'] = 30*GIB
    value['commit_available_bytes'] = 30*GIB
    value['commit_limit_bytes'] = value['commit_used_bytes'] + 30*GIB
    assert resource_admission(value, 24*GIB)['allowed']
    value['available_bytes'] = GIB
    value['host_available_bytes'] = GIB
    assert not resource_admission(value, 24*GIB)['allowed']


def test_swap_is_not_added_to_ram_and_zero_headroom_rejects(ec2):
    value = snapshot(ec2)
    value.update(available_bytes=GIB, host_available_bytes=GIB, swap_total_bytes=100*GIB, swap_free_bytes=100*GIB)
    decision = resource_admission(value, 24*GIB)
    assert not decision['allowed'] and 'ram_reserve' in decision['reasons']
    write(ec2[1]/'system.slice/ollama.service/memory.max', str(2*GIB))
    write(ec2[1]/'system.slice/ollama.service/memory.current', str(2*GIB))
    value = snapshot(ec2)
    assert 'cgroup_reserve' in resource_admission(value, 24*GIB)['reasons']


@pytest.mark.parametrize('key,value', [('overcommit_memory', None), ('overcommit_memory', True), ('overcommit_memory', 3),
                                      ('commit_used_bytes', -1), ('available_bytes', True), ('cgroup_root_verified', False)])
def test_incomplete_linux_accounting_never_admits(ec2, key, value):
    memory = snapshot(ec2)
    memory[key] = value
    decision = resource_admission(memory, GIB)
    assert not decision['allowed']
    assert 'resource_snapshot_unavailable' in decision['reasons']
    assert not decision['checks']['critical_accounting']


def test_monitor_uses_approved_linux_policy_and_records_pressure(ec2):
    memory = snapshot(ec2)
    cancelled = []
    monitor = ResourceMonitor(lambda: memory, lambda: cancelled.append(True), minimum=24*GIB)
    monitor.collect()
    assert not monitor.violated and cancelled == []
    decision = monitor.summary()['admission_decisions'][0]
    assert decision['allowed'] and decision['reasons'] == []
    assert decision['checks']['commit_reserve'] is None
    memory['available_bytes'] = 0
    memory['host_available_bytes'] = 0
    monitor.collect()
    assert monitor.violated and cancelled == [True]
    assert monitor.admissions[-1]['reasons'] == ['ram_reserve']
    assert decision['observations']['available_bytes'] > 0  # Prior decision is a snapshot.


def test_qwen3_status_and_bc_record_block_while_a_needs_no_provider(ec2, tmp_path):
    cfg = Qwen3CoderSettings()
    transport = SyntheticTransport()
    memory = snapshot(ec2)
    service = service_for(cfg, sampler=lambda: memory, gate_factory=lambda: InferenceGate(tmp_path/'gate.lock'),
                          transport_factory=lambda: transport)
    status = service.adapter.status()
    assert status['available'] and status['resource_ready']
    assert status['resource_admission']['policy'] == LINUX_POLICY
    memory.update(available_bytes=0, host_available_bytes=0)
    for mode in ['B', 'C']:
        result = service.analyze('Get-Process', mode)
        assert result.status == 'unavailable'
        assert result.operational['inference_dispatched'] is False
        assert result.operational['resource_admission']['reasons'] == ['ram_reserve']
        assert result.operational['resource_admission']['policy'] == LINUX_POLICY
    assert not any(endpoint == 'chat' for endpoint, _ in transport.calls)
    assert not (tmp_path/'gate.blocked').exists()
    def forbidden():
        pytest.fail('A must not consult provider or memory')
    service.adapter.transport_factory = forbidden
    service.adapter.sampler = forbidden
    assert service.analyze('Get-Process', 'A').status == 'completed'


def metadata(memory, cfg):
    return {'version': {'version': '0.40.15'}, 'tags': {'models': [{'name': cfg.model, 'digest': cfg.expected_digest,
            'details': {'quantization_level': 'Q4_K_M'}}]}, 'ps': {'models': []},
            'show': {'capabilities': ['completion'], 'model_info': {'general.architecture': 'qwen3moe', 'qwen3moe.context_length': 262144}},
            'memory': memory, 'disk_free_bytes': 8*GIB}


@pytest.mark.parametrize('mode,enough_commit,expected', [(0, False, True), (2, False, False), (2, True, True), (1, True, False)])
def test_synthetic_controller_preflight_accepts_rss_without_private_but_enforces_policy(ec2, tmp_path, mode, enough_commit, expected):
    cfg = Qwen3CoderSettings()
    memory = snapshot(ec2)
    memory['overcommit_memory'] = mode
    if enough_commit:
        memory.update(commit_available_bytes=30*GIB, host_commit_headroom_bytes=30*GIB,
                      commit_limit_bytes=memory['commit_used_bytes'] + 30*GIB)
    p = SimpleNamespace(settings=cfg, out=tmp_path, configuration={'disk_free_minimum_bytes': 2*GIB}, verify_candidate=lambda: None)
    campaign = Campaign(p, metadata=lambda: metadata(deepcopy(memory), cfg), gate_factory=lambda: InferenceGate(tmp_path/'preflight.lock'))
    if expected:
        campaign.preflight(first=True)
    else:
        with pytest.raises(OperationalFailure, match='insufficient_memory'):
            campaign.preflight(first=True)
    record = json.loads(next((tmp_path/'execution/preflights').glob('*.json')).read_text())
    assert record['passed'] is expected
    assert record['resource_admission']['allowed'] is expected
    assert record['resource_admission']['policy'] == LINUX_POLICY
    assert record['memory']['processes'][0]['private_unavailable']
    assert not list(tmp_path.rglob('FREEZE.json')) and not list(tmp_path.rglob('ledger.jsonl'))


@pytest.mark.parametrize('damage', ['missing_collector', 'unknown_collector', 'missing_runtime', 'rss_unavailable',
    'missing_cgroup', 'missing_owner', 'duplicate_cgroup', 'unknown_root', 'inconsistent_available',
    'inconsistent_commit', 'missing_headroom'])
def test_incomplete_or_ambiguous_linux_data_never_falls_back_to_windows(ec2, damage):
    memory = snapshot(ec2)
    if damage == 'missing_collector': memory.pop('collector')
    elif damage == 'unknown_collector': memory['collector'] = 'linux-unknown-v99'
    elif damage == 'missing_runtime': memory['processes'] = []
    elif damage == 'rss_unavailable': memory['processes'][0]['counters_unavailable'] = True
    elif damage == 'missing_cgroup': memory['cgroups'] = [g for g in memory['cgroups'] if g['path'] != '/system.slice']
    elif damage == 'missing_owner': next(g for g in memory['cgroups'] if g['path'] == '/')['owners'] = ['application']
    elif damage == 'duplicate_cgroup': memory['cgroups'].append(deepcopy(memory['cgroups'][0]))
    elif damage == 'unknown_root': next(g for g in memory['cgroups'] if g['path'] == '/')['limit_status'] = 'unknown'
    elif damage == 'inconsistent_available': memory['available_bytes'] -= 1
    elif damage == 'inconsistent_commit': memory['host_commit_headroom_bytes'] += 1
    elif damage == 'missing_headroom': memory.pop('cgroup_headroom_bytes')
    result = resource_admission(memory, GIB)
    assert result['policy'] == LINUX_POLICY
    assert not result['allowed'] and result['reasons'] == ['resource_snapshot_unavailable']
    assert result['invalid_fields']


def test_zero_commit_headroom_in_mode_zero_is_diagnostic_not_ram(ec2):
    proc, _ = ec2
    path = proc/'meminfo'
    write(path, path.read_text().replace('CommitLimit: 16429404 kB', 'CommitLimit: 0 kB'))
    value = snapshot(ec2)
    decision = resource_admission(value, 23968709120)
    assert decision['allowed'] and decision['commit_available_bytes'] == 0
    assert decision['observations']['host_commit_headroom_bytes'] == 0
    assert decision['checks']['commit_reserve'] is None
    value['overcommit_memory'] = 2
    assert resource_admission(value, 23968709120)['reasons'] == ['commit_reserve']


class FaultTransport(SyntheticTransport):
    def __init__(self, fault):
        super().__init__()
        self.fault = fault
        self.mode = fault if fault in {'offline', 'timeout'} else 'ready'

    def json(self, endpoint, payload=None):
        result = super().json(endpoint, payload)
        if endpoint == 'tags' and self.fault == 'wrong_model':
            result['models'][0]['name'] = 'unapproved-model'
        if endpoint == 'tags' and self.fault == 'wrong_digest':
            result['models'][0]['digest'] = '0'*64
        return result


@pytest.mark.parametrize('fault,code,chats', [('offline', 'ollama_unavailable', 0),
    ('wrong_model', 'model_missing', 0), ('wrong_digest', 'digest_mismatch', 0),
    ('timeout', 'timeout', 1), ('invalid-json', 'invalid_response', 1)])
def test_admission_does_not_imply_success_and_simulated_errors_have_explicit_recovery(ec2, tmp_path, fault, code, chats):
    memory = snapshot(ec2)
    cfg = Qwen3CoderSettings()
    needed = cfg.unloaded_reserve_bytes + cfg.minimum_margin_bytes
    assert resource_admission(memory, needed)['allowed']
    transport = FaultTransport(fault)
    path = tmp_path/'fault.lock'
    service = service_for(cfg, sampler=lambda: memory, gate_factory=lambda: InferenceGate(path),
                          transport_factory=lambda: transport)
    script = 'Write-Output "CASE:invalid-json"\nGet-Process' if fault == 'invalid-json' else 'Get-Process'
    result = service.analyze(script, 'B')
    assert result.status not in {'completed', 'partial'} and result.errors[0].code == code
    assert sum(e == 'chat' for e, _ in transport.calls) == chats
    if chats:
        assert result.operational['resource_admission']['allowed']
    if fault == 'timeout':
        assert result.operational['circuit_blocked']
        blocked = service.analyze('Get-Process', 'C')
        assert blocked.errors[0].code == 'inference_interrupted'
        assert sum(e == 'chat' for e, _ in transport.calls) == 1
        # Synthetic operator action under the lock. Never automatic recovery.
        with InferenceGate(path, allow_interrupted=True) as gate:
            gate.acknowledge_idle(reviewer='SYNTHETIC TEST OPERATOR', justification='Mock provider has no residents',
                                  server_has_no_residents=not transport.residents)
    transport.fault, transport.mode = None, 'ready'
    recovered = service.analyze('Get-Process', 'B')
    assert recovered.status == 'completed'
    assert sum(e == 'chat' for e, _ in transport.calls) == chats + 1


def test_blocked_circuit_prevents_dispatch_even_when_resources_are_ready(ec2, tmp_path):
    path = tmp_path/'blocked.lock'
    with InferenceGate(path) as gate:
        gate.start('a'*64)
        gate.block('SYNTHETIC interrupted request')
    transport = SyntheticTransport()
    service = service_for(Qwen3CoderSettings(), sampler=lambda: snapshot(ec2),
        gate_factory=lambda: InferenceGate(path), transport_factory=lambda: transport)
    state = service.status()
    assert state['resource_ready'] and state['circuit_blocked'] and not state['ready_for_inference']
    assert service.analyze('Get-Process', 'B').errors[0].code == 'inference_interrupted'
    assert not any(e == 'chat' for e, _ in transport.calls)
    assert service.analyze('Get-Process', 'A').status == 'completed'


def test_qwen3_profile_starts_offline_and_http_bc_preserves_requests_and_operational_data(ec2, tmp_path, monkeypatch):
    monkeypatch.setenv('PSI_LLM_PROFILE', 'qwen3coder-v2')
    monkeypatch.delenv('PSI_PIPELINE_SETTINGS', raising=False)
    app = create_app(frontend_dir=tmp_path/'no-dist')
    service = app.state.analysis_service
    assert service.settings.model == 'qwen3-coder:30b'
    def forbidden():
        pytest.fail('Startup, health and A must not consult the provider')
    service.adapter.transport_factory = forbidden
    service.adapter.sampler = forbidden
    with TestClient(app, base_url='http://127.0.0.1') as client:
        assert client.get('/api/health').status_code == 200
        assert client.post('/api/analyze/A', json={'script': 'Get-Process'}).json()['status'] == 'completed'
        transport = SyntheticTransport()
        service.adapter.transport_factory = lambda: transport
        service.adapter.sampler = lambda: snapshot(ec2)
        service.adapter.gate_factory = lambda: InferenceGate(tmp_path/'http.lock')
        for mode in ['B', 'C']:
            response = client.post('/api/analyze/' + mode, json={'script': 'Get-Process'})
            assert response.status_code == 200
            result = PipelineResult.model_validate(response.json())
            assert result.status == 'completed'
            assert result.operational['resource_admission']['policy'] == LINUX_POLICY
            assert result.operational['request'] == payload_for(context_for('Get-Process', mode, service.settings), service.settings)
    assert sum(e == 'chat' for e, _ in transport.calls) == 2

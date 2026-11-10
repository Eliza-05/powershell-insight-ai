"""Single resource decision shared by status, adapters, monitors and preflight.

Linux v1 was prospectively approved for local adoption on 2026-11-09. Resource
admission is neither inference authorization nor a guarantee against OOM.
Windows retains its historical RAM+commit floors. No environment/payload switch.
"""
from copy import deepcopy
from pathlib import PurePosixPath

from app.services.pipelines.linux_resources import COLLECTOR

LINUX_POLICY = 'linux-resident-mode-aware-v1'
WINDOWS_POLICY = 'ram-and-commit-v1'
LINUX_COUNTERS = ('physical_total_bytes', 'host_physical_total_bytes', 'available_bytes',
                  'host_available_bytes', 'commit_limit_bytes', 'commit_used_bytes',
                  'host_commit_headroom_bytes', 'commit_available_bytes',
                  'swap_total_bytes', 'swap_free_bytes')


def _counter(value):
    return type(value) is int and value >= 0


def _require(condition, field):
    if not condition:
        raise ValueError(field)


def _validate_linux(memory):
    """Reject incomplete or contradictory observations before applying thresholds."""
    _require(memory.get('collector') == COLLECTOR, 'collector')
    _require(all(_counter(memory.get(k)) for k in LINUX_COUNTERS), 'memory_counters')
    _require(memory['host_physical_total_bytes'] > 0 and
             memory['host_available_bytes'] <= memory['host_physical_total_bytes'], 'host_ram')
    _require(memory['swap_free_bytes'] <= memory['swap_total_bytes'], 'swap')
    _require(type(memory.get('overcommit_memory')) is int and memory['overcommit_memory'] in {0, 1, 2}, 'overcommit_memory')
    _require(memory.get('cgroup_root_verified') is True, 'cgroup_root_verified')
    processes = memory.get('processes')
    _require(isinstance(processes, list) and bool(processes), 'processes')
    pids = set()
    for process in processes:
        _require(isinstance(process, dict) and process.get('is_ollama_runtime') is True and
                 type(process.get('pid')) is int and process['pid'] > 0 and
                 _counter(process.get('rss_bytes')) and not process.get('counters_unavailable'), 'runtime_rss')
        _require(process['pid'] not in pids, 'duplicate_runtime_pid')
        pids.add(process['pid'])
    owners = {'application'} | {'pid:' + str(pid) for pid in pids}
    groups = memory.get('cgroups')
    _require(isinstance(groups, list) and bool(groups), 'cgroups')
    by_path, finite = {}, []
    for group in groups:
        _require(isinstance(group, dict) and isinstance(group.get('path'), str), 'cgroup_path')
        path = PurePosixPath(group['path'])
        _require(path.is_absolute() and str(path) == group['path'] and
                 '..' not in path.parts and not str(path).startswith('//'), 'cgroup_path')
        _require(path not in by_path, 'duplicate_cgroup')
        membership = group.get('owners')
        _require(isinstance(membership, list) and bool(membership) and
                 all(isinstance(owner, str) for owner in membership) and
                 len(set(membership)) == len(membership) and set(membership) <= owners, 'cgroup_owners')
        by_path[path] = group
        status = group.get('limit_status')
        if status == 'not_applicable_at_verified_root':
            _require(str(path) == '/', 'root_control_exception')
        else:
            _require(status in {'finite', 'unlimited'} and _counter(group.get('current_bytes')), 'cgroup_current')
            if status == 'finite':
                _require(_counter(group.get('limit_bytes')) and
                         _counter(group.get('headroom_bytes')) and
                         group['headroom_bytes'] == max(0, group['limit_bytes'] - group['current_bytes']), 'cgroup_headroom')
                finite.append(group)
    root = PurePosixPath('/')
    _require(root in by_path and set(by_path[root]['owners']) == owners, 'root_memberships')
    # Every owner's observations must form one complete chain up to the root.
    for owner in owners:
        paths = {path for path, group in by_path.items() if owner in group['owners']}
        leaf = max(paths, key=lambda p: len(p.parts))
        _require(paths == {leaf, *leaf.parents}, 'incomplete_cgroup_hierarchy')
    headroom = min((g['headroom_bytes'] for g in finite), default=None)
    supplied = memory.get('cgroup_headroom_bytes')
    _require('cgroup_headroom_bytes' in memory and
             (supplied is None if headroom is None else _counter(supplied) and supplied == headroom), 'effective_cgroup_headroom')
    effective_available = min(memory['host_available_bytes'], headroom) if headroom is not None else memory['host_available_bytes']
    _require(memory['available_bytes'] == effective_available, 'effective_available')
    _require(memory['physical_total_bytes'] == min([memory['host_physical_total_bytes']] +
             [g['limit_bytes'] for g in finite]), 'effective_total')
    raw_commit = max(0, memory['commit_limit_bytes'] - memory['commit_used_bytes'])
    _require(memory['host_commit_headroom_bytes'] == raw_commit, 'host_commit_headroom')
    _require(memory['commit_available_bytes'] == (min(raw_commit, headroom) if headroom is not None else raw_commit),
             'effective_commit_headroom')


def _linux_admission(memory, required):
    checks, invalid = {}, []
    try:
        _require(_counter(required) and required > 0, 'required_bytes')
        _validate_linux(memory)
    except (ValueError, TypeError, KeyError) as exc:
        invalid.append(str(exc))
    checks['critical_accounting'] = not invalid
    mode = memory.get('overcommit_memory')
    if not invalid:
        checks['ram_reserve'] = memory['available_bytes'] >= required
        headroom = memory['cgroup_headroom_bytes']
        checks['cgroup_reserve'] = headroom is None or headroom >= required
        checks['supported_overcommit'] = mode in {0, 2}
        checks['commit_reserve'] = memory['host_commit_headroom_bytes'] >= required if mode == 2 else None
    reasons = ['resource_snapshot_unavailable'] if invalid else [k for k, passed in checks.items() if passed is False]
    keys = (*LINUX_COUNTERS, 'collector', 'overcommit_memory', 'cgroup_root_verified',
            'cgroup_headroom_bytes', 'cgroups', 'processes', 'measurement_uncertainty')
    return {'policy': LINUX_POLICY, 'allowed': not reasons, 'required_bytes': required,
            'available_bytes': memory.get('available_bytes'), 'commit_available_bytes': memory.get('commit_available_bytes'),
            'checks': checks, 'reasons': reasons, 'invalid_fields': invalid,
            'commit_role': 'hard_floor' if mode == 2 else 'diagnostic_only_in_mode_0' if mode == 0 else 'unsupported',
            'overcommit_memory': mode, 'swap_credit_bytes': 0,
            'observations': deepcopy({k: memory.get(k) for k in keys}),
            'decision_scope': 'resources_only; not execution authorization',
            'risk': 'No reservation or OOM guarantee; concurrent allocations and reclaim estimates remain uncertain'}


def resource_admission(memory, required):
    """Use the approved Linux policy only for explicitly identified Linux data."""
    linux = str(memory.get('collector', '')).startswith('linux-') or any(
        k in memory for k in ['overcommit_memory', 'cgroup_root_verified', 'cgroups', 'host_commit_headroom_bytes'])
    if linux:
        return _linux_admission(memory, required)
    complete = _counter(required) and required > 0 and all(_counter(memory.get(k)) for k in ['available_bytes', 'commit_available_bytes'])
    reasons = []
    if not complete:
        reasons.append('resource_snapshot_unavailable')
    else:
        if memory['available_bytes'] < required:
            reasons.append('ram_reserve')
        if memory['commit_available_bytes'] < required:
            reasons.append('commit_reserve')
    return {'policy': WINDOWS_POLICY, 'allowed': not reasons, 'required_bytes': required,
            'available_bytes': memory.get('available_bytes'), 'commit_available_bytes': memory.get('commit_available_bytes'),
            'reasons': reasons}

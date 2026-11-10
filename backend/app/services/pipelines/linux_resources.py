"""Unprivileged Linux observations; no admission policy or resource reservation.

RSS is approximate resident memory; PSS apportions shared pages. Smaps private
is neither RSS nor Windows private commit. Cgroup usage includes descendants,
kernel and cache charges. These measurements are never added to each other.
"""
from pathlib import Path, PurePosixPath
import re

COLLECTOR = 'linux-proc-cgroup-v2-v2'


def _fields(path):
    result = {}
    for line in path.read_text(encoding='utf8').splitlines():
        if ':' not in line:
            continue
        name, value = line.split(':', 1)
        parts = value.split()
        if not parts:
            continue
        if len(parts) == 2 and parts[1] == 'kB':
            result[name] = int(parts[0]) * 1024
        elif len(parts) == 1 and parts[0].isdigit():
            result[name] = int(parts[0])
        else:
            result[name] = value.strip()
    return result


def _unsigned(value):
    if not value.isascii() or not value.isdecimal():
        raise ValueError('Invalid nonnegative Linux counter')
    return int(value)


def _process_table(proc_root):
    entries = {}
    for path in proc_root.iterdir():
        if not path.name.isdigit():
            continue
        try:
            entries[int(path.name)] = (path, _fields(path / 'status'))
        except (FileNotFoundError, ProcessLookupError):
            continue  # An exited process is not a hidden, live process.
    return entries


def linux_process_counters(proc_root=Path('/proc'), *, table=None):
    entries = _process_table(Path(proc_root)) if table is None else table
    runtime = {pid for pid, (_, s) in entries.items() if 'ollama' in str(s.get('Name', '')).lower()}
    while True:
        expanded = runtime | {pid for pid, (_, s) in entries.items() if s.get('PPid') in runtime}
        if expanded == runtime:
            break
        runtime = expanded
    rows = []
    for pid in sorted(runtime):
        path, status = entries[pid]
        row = {'pid': pid, 'name': str(status.get('Name', '')), 'parent': status.get('PPid'),
               'is_ollama_runtime': True, 'collector': 'linux-proc-status-v2',
               'rss_semantics': 'VmRSS: approximate resident pages; shared pages may occur in multiple processes',
               'private_unavailable': True, 'pss_unavailable': True}
        if type(status.get('VmRSS')) is int and status['VmRSS'] >= 0:
            row['rss_bytes'] = status['VmRSS']
        else:
            row['counters_unavailable'] = True
        for source, key in [('RssAnon', 'rss_anon_bytes'), ('RssFile', 'rss_file_bytes'),
                            ('RssShmem', 'rss_shared_bytes'), ('VmSwap', 'swap_bytes')]:
            if type(status.get(source)) is int and status[source] >= 0:
                row[key] = status[source]
        try:
            smaps = _fields(path / 'smaps_rollup')
            keys = ['Private_Clean', 'Private_Dirty', 'Private_Hugetlb']
            if all(type(smaps.get(k, 0)) is int and smaps.get(k, 0) >= 0 for k in keys) and all(k in smaps for k in keys[:2]):
                row.update(private_bytes=sum(smaps.get(k, 0) for k in keys), private_unavailable=False)
            if type(smaps.get('Pss')) is int and smaps['Pss'] >= 0:
                row.update(pss_bytes=smaps['Pss'], pss_unavailable=False)
        except (OSError, ValueError) as exc:
            row['smaps_unavailable_reason'] = type(exc).__name__
        rows.append(row)
    return rows


def _verified_root(proc_root, cgroup_root):
    # Reject subtree mounts: unseen ancestors could impose tighter limits.
    root = cgroup_root.resolve(strict=True)
    matches = []
    for line in (proc_root / 'self/mountinfo').read_text(encoding='utf8').splitlines():
        before, sep, after = line.partition(' - ')
        if not sep or not after.split() or after.split()[0] != 'cgroup2':
            continue
        fields = before.split()
        if len(fields) < 6:
            raise ValueError('Incomplete cgroup mount record')
        mountpoint = re.sub(r'\\([0-7]{3})', lambda m: chr(int(m[1], 8)), fields[4])
        if Path(mountpoint).resolve() == root:
            matches.append(fields[3])
    if matches != ['/']:
        raise ValueError('Full cgroup v2 mount root not verified; hidden ancestors unsupported')
    if 'memory' not in (root / 'cgroup.controllers').read_text(encoding='ascii').split():
        raise ValueError('Cgroup memory controller unavailable')
    return root


def _membership(path, root):
    lines = path.read_text(encoding='utf8').splitlines()
    if len(lines) != 1 or not lines[0].startswith('0::'):
        raise ValueError('Only verified cgroup v2 membership is supported')
    member = PurePosixPath(lines[0][3:])
    if not member.is_absolute() or '..' in member.parts:
        raise ValueError('Invalid cgroup membership')
    group = (root / str(member).lstrip('/')).resolve(strict=True)
    if not group.is_relative_to(root):
        raise ValueError('Cgroup membership outside accounting mount')
    return group


def linux_memory_snapshot(proc_root=Path('/proc'), cgroup_root=Path('/sys/fs/cgroup')):
    proc_root, cgroup_root = Path(proc_root), Path(cgroup_root)
    values = _fields(proc_root / 'meminfo')
    required = ['MemTotal', 'MemAvailable', 'CommitLimit', 'Committed_AS', 'SwapTotal', 'SwapFree']
    if any(type(values.get(key)) is not int or values[key] < 0 for key in required):
        raise ValueError('Incomplete Linux memory/commit accounting')
    if values['MemTotal'] <= 0 or values['MemAvailable'] > values['MemTotal'] or values['SwapFree'] > values['SwapTotal']:
        raise ValueError('Inconsistent Linux memory accounting')
    mode = _unsigned((proc_root / 'sys/vm/overcommit_memory').read_text(encoding='ascii').strip())
    if mode not in {0, 1, 2}:
        raise ValueError('Unknown Linux overcommit mode')
    root = _verified_root(proc_root, cgroup_root)
    table = _process_table(proc_root)
    processes = linux_process_counters(proc_root, table=table)
    if not processes or any(p.get('counters_unavailable') for p in processes):
        raise ValueError('Ollama runtime RSS not observable')
    memberships = {'application': _membership(proc_root / 'self/cgroup', root)}
    for p in processes:
        memberships['pid:' + str(p['pid'])] = _membership(proc_root / str(p['pid']) / 'cgroup', root)
    groups = {}
    for owner, group in memberships.items():
        while True:
            groups.setdefault(group, []).append(owner)
            if group == root:
                break
            group = group.parent
    total, available = values['MemTotal'], values['MemAvailable']
    commit_raw = max(0, values['CommitLimit'] - values['Committed_AS'])
    headroom, observations, limits = None, [], []
    for group, owners in groups.items():
        row = {'path': '/' if group == root else '/' + group.relative_to(root).as_posix(), 'owners': owners}
        try:
            ceiling = (group / 'memory.max').read_text(encoding='ascii').strip()
        except FileNotFoundError:
            if group != root:
                raise
            row['limit_status'] = 'not_applicable_at_verified_root'
            observations.append(row)
            continue
        if ceiling == 'max':
            row['limit_status'] = 'unlimited'
        else:
            maximum = _unsigned(ceiling)
            row.update(limit_status='finite', limit_bytes=maximum)
        current = _unsigned((group / 'memory.current').read_text(encoding='ascii').strip())
        row['current_bytes'] = current
        if ceiling != 'max':
            remaining = max(0, maximum - current)
            row['headroom_bytes'] = remaining
            total, available = min(total, maximum), min(available, remaining)
            headroom = remaining if headroom is None else min(headroom, remaining)
            limits.append(row)
        observations.append(row)
    return {'physical_total_bytes': total, 'available_bytes': available,
            'host_physical_total_bytes': values['MemTotal'], 'host_available_bytes': values['MemAvailable'],
            'commit_limit_bytes': values['CommitLimit'], 'commit_used_bytes': values['Committed_AS'],
            'host_commit_headroom_bytes': commit_raw,
            'commit_available_bytes': min(commit_raw, headroom) if headroom is not None else commit_raw,
            'swap_total_bytes': values['SwapTotal'], 'swap_free_bytes': values['SwapFree'],
            'overcommit_memory': mode, 'collector': COLLECTOR, 'cgroup_root_verified': True,
            'commit_semantics': 'Linux CommitLimit-Committed_AS, clamped at zero; legacy field capped by cgroups',
            'cgroup_headroom_bytes': headroom, 'cgroup_limits': limits, 'cgroups': observations,
            'processes': processes, 'measurement_uncertainty': 'Non-atomic observations; MemAvailable and VmRSS are estimates; no allocation guarantee',
            'aggregation': 'Minimum host/app/runtime/ancestor headroom; never sum RSS, cgroup usage or overlapping groups'}

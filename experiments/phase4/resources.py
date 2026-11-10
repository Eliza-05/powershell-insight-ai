"""Prospective resource binding; legacy Windows pilot collector stays untouched."""
import os
import time


def snapshot():
    if os.name == 'nt':
        from experiments.pilot_v2_runtime.resources import snapshot as windows_snapshot
        return windows_snapshot()
    from app.services.pipelines.resources import memory_snapshot
    result = memory_snapshot()
    result.update(monotonic=time.monotonic(),
                  paging_measure='Linux VmRSS; optional smaps private/PSS; no Windows paging equivalence claimed')
    return result

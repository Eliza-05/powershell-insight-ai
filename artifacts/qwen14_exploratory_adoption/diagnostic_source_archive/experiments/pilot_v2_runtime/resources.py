"""Read-only Windows memory, commit, paging, CPU and Ollama process counters."""

from __future__ import annotations

import ctypes as c
from ctypes import wintypes as w
import os
import threading
import time

GIB = 1024 ** 3


class Memory(c.Structure):
    _fields_ = [("length", w.DWORD), ("load", w.DWORD)] + [
        (name, c.c_ulonglong) for name in ("total", "available", "commit_limit", "commit_available",
                                         "virtual_total", "virtual_available", "extended")]


class Entry(c.Structure):
    _fields_ = [("size", w.DWORD), ("usage", w.DWORD), ("pid", w.DWORD), ("heap", c.c_size_t),
                ("module", w.DWORD), ("threads", w.DWORD), ("parent", w.DWORD),
                ("priority", w.LONG), ("flags", w.DWORD), ("exe", w.WCHAR * 260)]


class Counters(c.Structure):
    _fields_ = [("size", w.DWORD), ("page_faults", w.DWORD)] + [
        (name, c.c_size_t) for name in ("peak_working_set", "working_set", "peak_paged_pool", "paged_pool",
                                     "peak_nonpaged_pool", "nonpaged_pool", "pagefile", "peak_pagefile", "private")]


def process_counters():
    if os.name != "nt":
        return []
    kernel, psapi = c.windll.kernel32, c.windll.psapi
    kernel.CreateToolhelp32Snapshot.restype = w.HANDLE
    kernel.Process32FirstW.argtypes = [w.HANDLE, c.POINTER(Entry)]
    kernel.Process32NextW.argtypes = [w.HANDLE, c.POINTER(Entry)]
    kernel.OpenProcess.restype = w.HANDLE
    kernel.CloseHandle.argtypes = [w.HANDLE]
    psapi.GetProcessMemoryInfo.argtypes = [w.HANDLE, c.POINTER(Counters), w.DWORD]
    kernel.GetProcessTimes.argtypes = [w.HANDLE] + [c.POINTER(w.FILETIME)] * 4
    handle = kernel.CreateToolhelp32Snapshot(2, 0)
    if handle == w.HANDLE(-1).value:
        return []
    entry = Entry(); entry.size = c.sizeof(entry)
    rows, entries = [], []
    try:
        ok = kernel.Process32FirstW(handle, c.byref(entry))
        while ok:
            entries.append({"pid":entry.pid,"name":entry.exe,"parent":entry.parent})
            ok = kernel.Process32NextW(handle, c.byref(entry))
        model_pids = {e["pid"] for e in entries if "ollama" in e["name"].lower()}
        while True:
            expanded = model_pids | {e["pid"] for e in entries if e["parent"] in model_pids}
            if expanded == model_pids:
                break
            model_pids = expanded
        for entry_info in entries:
            if entry_info["pid"] in model_pids or entry_info["pid"] == os.getpid():
                row = {**entry_info, "is_ollama_runtime":entry_info["pid"] in model_pids}
                process = kernel.OpenProcess(0x410, False, entry_info["pid"])
                if process:
                    try:
                        counters = Counters(); counters.size = c.sizeof(counters)
                        if psapi.GetProcessMemoryInfo(process, c.byref(counters), counters.size):
                            row.update({n: getattr(counters, n) for n, _ in Counters._fields_[1:]})
                        values = [w.FILETIME() for _ in range(4)]
                        if kernel.GetProcessTimes(process, *[c.byref(v) for v in values]):
                            row["cpu_seconds"] = sum((v.dwHighDateTime << 32) + v.dwLowDateTime for v in values[2:]) / 1e7
                    finally:
                        kernel.CloseHandle(process)
                else:
                    row["counters_unavailable"] = True
                rows.append(row)
    finally:
        kernel.CloseHandle(handle)
    return rows


def snapshot():
    if os.name != "nt":
        raise RuntimeError("This pilot's resource collector requires Windows")
    memory = Memory(); memory.length = c.sizeof(memory)
    if not c.windll.kernel32.GlobalMemoryStatusEx(c.byref(memory)):
        raise OSError("GlobalMemoryStatusEx failed")
    return {"monotonic": time.monotonic(), "physical_total_bytes": memory.total,
            "available_bytes": memory.available, "commit_limit_bytes": memory.commit_limit,
            "commit_used_bytes": memory.commit_limit - memory.commit_available,
            "commit_available_bytes": memory.commit_available, "memory_load_percent": memory.load,
            "processes": process_counters(),
            "paging_measure": "process page-fault counters include soft and hard faults; not disk paging bytes"}


class Monitor:
    def __init__(self, cancel, interval=1, sampler=snapshot):
        self.cancel, self.interval, self.sampler = cancel, interval, sampler
        self.samples, self.errors, self.violated = [], [], False
        self.stop = threading.Event()

    def collect(self):
        try:
            value = self.sampler()
            self.samples.append(value)
            if value["available_bytes"] < 2 * GIB or value["commit_available_bytes"] < 2 * GIB:
                self.violated = True
                self.cancel()
        except Exception as exc:
            self.errors.append(str(exc))
            self.violated = True
            self.cancel()

    def loop(self):
        while not self.stop.wait(self.interval):
            self.collect()

    def __enter__(self):
        self.collect()
        self.thread = threading.Thread(target=self.loop, daemon=True)
        self.thread.start()
        return self

    def __exit__(self, *_):
        self.stop.set(); self.thread.join(timeout=3)
        self.collect()

    def summary(self):
        processes = [p for s in self.samples for p in s["processes"] if p.get("is_ollama_runtime", "ollama" in p["name"].lower())]
        return {"samples": len(self.samples), "margin_violated": self.violated,
                "process_measurement_scope":"ollama_process_tree_including_llama_server",
                "minimum_available_bytes": min((s["available_bytes"] for s in self.samples), default=None),
                "maximum_commit_used_bytes": max((s["commit_used_bytes"] for s in self.samples), default=None),
                "maximum_single_ollama_working_set_bytes": max((p.get("working_set", 0) for p in processes), default=None),
                "maximum_single_ollama_private_bytes": max((p.get("private", 0) for p in processes), default=None),
                "counter_errors": self.errors}

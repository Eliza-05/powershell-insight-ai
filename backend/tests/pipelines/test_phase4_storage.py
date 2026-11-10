"""Synthetic filesystem accounting only; no reserved imports, freeze or generation."""
from copy import deepcopy
import json
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest

from app.services.pipelines.resources import OperationalFailure
from experiments.phase4 import storage


@pytest.fixture
def bound(tmp_path, monkeypatch):
    monkeypatch.delenv("OLLAMA_MODELS", raising=False)
    monkeypatch.setattr(storage, "_is_linux", lambda: True)
    monkeypatch.setattr(storage, "_verify_anchor", lambda p: None)
    monkeypatch.setattr(storage.shutil, "disk_usage", lambda p: SimpleNamespace(total=32092319744, free=8439050240))
    mountinfo = tmp_path / "mountinfo"
    mountinfo.write_text("27 1 202:1 / / rw - ext4 /dev/root rw\n29 27 0:24 / /proc rw - proc proc rw\n")
    binding = {"version": storage.VERSION, "canonical_model_path": "/service/models", "probe_path": "/service",
               "mount": {"device": "202:1", "root": "/", "mountpoint": "/", "filesystem": "ext4"},
               "filesystem_total_bytes": 32092319744, "metadata_evidence_sha256": "a" * 64}
    return binding, mountinfo


def test_bound_filesystem_records_observation_and_its_limits(bound):
    binding, mountinfo = bound
    result = storage.storage_snapshot(binding, mountinfo=mountinfo)
    assert result["model_path"] == "/service/models" and result["disk_free_bytes"] == 8439050240
    accounting = result["storage_accounting"]
    assert accounting["method"] == storage.VERSION and accounting["probe_path"] == "/service"
    assert accounting["metadata_evidence_sha256"] == binding["metadata_evidence_sha256"]
    assert "not re-resolved live" in accounting["canonical_path_verification"]
    assert "not read" in accounting["limitation"]


def test_direct_mode_has_no_implicit_parent_fallback(monkeypatch):
    monkeypatch.setenv("OLLAMA_MODELS", "/protected/models")
    calls = []
    def denied(path):
        calls.append(str(path)); raise PermissionError("synthetic protected store")
    monkeypatch.setattr(storage.shutil, "disk_usage", denied)
    with pytest.raises(PermissionError): storage.storage_snapshot()
    assert calls == [str(Path("/protected/models"))]


def test_direct_mode_retains_existing_measurement(monkeypatch):
    monkeypatch.setenv("OLLAMA_MODELS", "/development/models")
    monkeypatch.setattr(storage.shutil, "disk_usage", lambda p: SimpleNamespace(free=123))
    assert storage.storage_snapshot()["disk_free_bytes"] == 123


@pytest.mark.parametrize("key,value", [
    ("version", "unknown"), ("metadata_evidence_sha256", "unbound"),
    ("filesystem_total_bytes", True), ("filesystem_total_bytes", -1),
    ("canonical_model_path", "/service/../models"), ("canonical_model_path", "relative/models"),
    ("canonical_model_path", "/service//models"), ("probe_path", "/different"),
])
def test_incomplete_or_misdirected_binding_fails_closed(bound, key, value):
    binding, mountinfo = bound; binding[key] = value
    with pytest.raises(OperationalFailure): storage.storage_snapshot(binding, mountinfo=mountinfo)


def test_unknown_binding_fields_fail_closed(bound):
    binding, mountinfo = bound; binding["skip_checks"] = True
    with pytest.raises(OperationalFailure, match="binding_invalid"): storage.storage_snapshot(binding, mountinfo=mountinfo)


def test_environment_cannot_redirect_a_frozen_binding(bound, monkeypatch):
    binding, mountinfo = bound
    monkeypatch.setenv("OLLAMA_MODELS", "/different/models")
    with pytest.raises(OperationalFailure, match="environment_mismatch"): storage.storage_snapshot(binding, mountinfo=mountinfo)


@pytest.mark.parametrize("extra", [
    "30 27 202:2 / /service/models rw - ext4 /dev/other rw\n",
    "30 27 202:2 / /service rw - ext4 /dev/other rw\n",
    "30 27 202:1 /hidden /service rw - ext4 /dev/root rw\n",
    "30 27 202:1 / / rw - ext4 /dev/root rw\n",
])
def test_nested_replaced_hidden_or_ambiguous_mount_is_rejected(bound, extra):
    binding, mountinfo = bound
    mountinfo.write_text(mountinfo.read_text() + extra)
    with pytest.raises(OperationalFailure): storage.storage_snapshot(binding, mountinfo=mountinfo)


def test_changed_filesystem_size_is_rejected(bound):
    binding, mountinfo = bound; binding["filesystem_total_bytes"] += 4096
    with pytest.raises(OperationalFailure, match="filesystem_changed"): storage.storage_snapshot(binding, mountinfo=mountinfo)


def test_non_linux_cannot_accept_a_linux_binding(bound, monkeypatch):
    binding, mountinfo = bound; monkeypatch.setattr(storage, "_is_linux", lambda: False)
    with pytest.raises(OperationalFailure, match="binding_invalid"): storage.storage_snapshot(binding, mountinfo=mountinfo)


def test_anchor_check_rejects_an_unresolvable_or_redirected_path(tmp_path, monkeypatch):
    assert storage._verify_anchor(tmp_path) is None
    monkeypatch.setattr(Path, "resolve", lambda *a, **k: tmp_path / "different")
    with pytest.raises(OperationalFailure, match="anchor_changed"): storage._verify_anchor(tmp_path)


def test_request_binding_is_only_in_controller_metadata(bound, monkeypatch, tmp_path):
    from experiments.phase4 import campaign
    from app.services.llm.qwen3coder import Qwen3CoderSettings
    binding, mountinfo = bound; calls = []
    monkeypatch.setattr(campaign, "native_state", lambda settings, **kwargs: calls.append(kwargs) or {})
    proposal = SimpleNamespace(settings=Qwen3CoderSettings(), configuration={"model_storage_binding": deepcopy(binding)}, out=tmp_path)
    controller = campaign.Campaign(proposal)
    controller.metadata()
    assert calls == [{"storage_binding": binding}]


def test_native_metadata_uses_binding_without_chat_or_generate(bound, monkeypatch):
    from experiments.phase4 import campaign
    from app.services.llm.qwen3coder import Qwen3CoderSettings
    binding, mountinfo = bound; calls = []
    class MetadataOnly:
        def json(self, endpoint, payload=None):
            assert endpoint in {"version", "tags", "ps", "show"}
            calls.append(endpoint); return {}
    monkeypatch.setattr(campaign, "transport_for", lambda *a, **k: MetadataOnly())
    monkeypatch.setattr(campaign, "snapshot", lambda: {"synthetic": True})
    monkeypatch.setattr(campaign, "storage_snapshot", lambda b: storage.storage_snapshot(b, mountinfo=mountinfo))
    state = campaign.native_state(Qwen3CoderSettings(), storage_binding=binding)
    assert state["disk_free_bytes"] == 8439050240 and calls == ["version", "tags", "ps", "show"]


def test_invalid_storage_configuration_stops_before_reserved_import(bound, monkeypatch, tmp_path):
    from experiments.phase4 import prepare
    binding, mountinfo = bound
    binding["version"] = "invalid"
    config = tmp_path / "synthetic-binding.json"
    config.write_text(json.dumps(binding), encoding="utf-8")
    monkeypatch.setenv("PSI_PHASE4_STORAGE_BINDING", str(config))
    assert "experiments.phase4.dataset" not in sys.modules
    with pytest.raises(OperationalFailure, match="binding_invalid"): prepare.prepare()
    assert "experiments.phase4.dataset" not in sys.modules

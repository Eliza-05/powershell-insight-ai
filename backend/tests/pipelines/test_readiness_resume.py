from copy import deepcopy

import pytest

from experiments.model_readiness.diagnostics import build_plan, canonical, sha
from experiments.readiness_resume import amend_plan


def test_prospective_reasoning_provenance_changes_only_unexecuted_slot():
    original = build_plan()
    before = deepcopy(original)
    plan = amend_plan(original, {"01-C-recovered-P0", "02-C-recovered-P1"})
    assert original == before
    assert len(plan["calls"]) == plan["budget_cap"] == 24
    assert [i for i, (old, new) in enumerate(zip(original["calls"], plan["calls"])) if old != new] == [17]
    call = plan["calls"][17]
    assert call["id"] == "18-C-recovered-P3"
    assert call["mode"] == "C" and call["payload"]["think"] is True
    assert call["script"] == original["calls"][1]["script"]
    assert call["payload"]["messages"] == original["calls"][1]["payload"]["messages"]
    assert call["request_sha256"] == sha(canonical(call["payload"]))
    assert plan["prospective_amendment"]["registered_before_any_P3_output"]
    assert "reference_labels_reviewer_only" not in canonical(call["payload"])


def test_dispatched_slot_cannot_be_replaced():
    with pytest.raises(ValueError, match="already-dispatched"):
        amend_plan(build_plan(), {"18-long-output-P4"})

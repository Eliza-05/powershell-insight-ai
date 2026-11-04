"""Read-only status and explicit operator acknowledgement of an interrupted gate.

Recovery never unloads a shared model, cancels a request or dispatches an inference.
An empty /api/ps alone is insufficient: the operator must attest that external
clients have stopped and no server request remains active. Identity is self-attested.
"""
import json

from app.services.pipelines.ollama import LocalTransport, OllamaAdapter
from app.services.pipelines.resources import InferenceGate, OperationalFailure
from experiments.pilot_v2_runtime.resources import snapshot


def recover(*, reviewer, justification, exclusive_session_attested,
            gate_factory=InferenceGate, client_factory=LocalTransport):
    if not exclusive_session_attested:
        raise OperationalFailure("recovery_refused", "Operator must attest that external requests/clients are stopped")
    with gate_factory(allow_interrupted=True) as gate:
        client = client_factory(timeout=3)
        state = OllamaAdapter()._state(client)
        version = client.json("version")
        resources = snapshot()
        gate.acknowledge_idle(reviewer=reviewer, justification=justification,
                             server_has_no_residents=not state["residents"])
        return {"marker_cleared": True, "new_inferences": 0, "version": version,
                "fresh_state_under_lock": state, "resources": resources,
                "exclusive_session": "operator_self_attested_not_observable_by_application",
                "journal": str(gate.history)}


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["status", "recover"])
    parser.add_argument("--reviewer")
    parser.add_argument("--justification")
    parser.add_argument("--exclusive-session-attested", action="store_true")
    args = parser.parse_args()
    if args.command == "recover":
        if not args.reviewer or not args.justification:
            parser.error("Recovery requires a named operator and justification")
        result = recover(reviewer=args.reviewer, justification=args.justification,
                         exclusive_session_attested=args.exclusive_session_attested)
    else:
        result = {"adapter": OllamaAdapter().status(), "process_snapshot": snapshot()}
    print(json.dumps(result, ensure_ascii=False, indent=2))

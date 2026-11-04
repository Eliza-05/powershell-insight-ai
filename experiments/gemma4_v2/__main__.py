"""CLI defaults to offline verification; run needs explicit bound owner authorization."""
import argparse
import json
from uuid import uuid4

from experiments.gemma4_v2.protocol import Protocol, digest, load, save
from experiments.gemma4_v2.runner import Campaign
from experiments.gemma4_v2.evaluation import evaluate


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("verify")
    run = sub.add_parser("run")
    run.add_argument("--authorization", required=True)
    run.add_argument("--exclusive-session-attested", action="store_true")
    run.add_argument("--resume", action="store_true")
    sub.add_parser("evaluate")
    args = parser.parse_args()
    protocol = Protocol()
    if args.command == "verify":
        protocol.verify_binding()
        for call in protocol.calls:
            protocol.context(call)
        print(json.dumps({"verified_calls": 12, "B": 10, "C": 2,
              "exact_denominator": 11, "live_inferences": 0,
              "execution_authorized_by_this_command": False}))
    elif args.command == "run":
        print(json.dumps(Campaign(protocol).run(args.authorization,
            exclusive_session_attested=args.exclusive_session_attested, resume=args.resume)))
    else:
        protocol.verify_binding()
        runner = Campaign(protocol)
        runner.metadata = load(protocol.execution / "campaign.json")
        runner.campaign_id = runner.metadata["campaign_id"]
        records = runner.completed_records()
        hashes, reviews = {}, {}
        for record in records:
            cid = record["call_id"]
            hashes[cid] = digest(protocol.execution / "results" / (cid + ".json"))
            review = protocol.execution / "reviews" / (cid + ".json")
            if review.is_file():
                reviews[cid] = load(review)
        result = evaluate(protocol, records, campaign_id=runner.campaign_id,
            reviews=reviews, result_hashes=hashes, references_accepted=runner.metadata["references_accepted"],
            stopped=(protocol.execution / "STOP.json").exists())
        target = protocol.execution / "evaluations" / (str(uuid4()) + ".json")
        save(target, result)
        print(json.dumps({"decision": result["decision"], "report": str(target)}))


if __name__ == "__main__":
    main()

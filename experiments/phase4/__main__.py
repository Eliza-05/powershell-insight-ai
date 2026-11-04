"""Explicit CLI; no default operation can run inference."""
import argparse
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Phase 4 preparation and explicitly authorized future campaign")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("prepare")
    sub.add_parser("refresh-candidate")
    sub.add_parser("report-proposal")
    seal = sub.add_parser("seal"); seal.add_argument("--personal-review", type=Path, required=True)
    run = sub.add_parser("run"); run.add_argument("--authorization", type=Path, required=True); run.add_argument("--resume", action="store_true")
    evaluation = sub.add_parser("evaluate"); evaluation.add_argument("--personal-reviews", type=Path)
    args = parser.parse_args()
    if args.command == "prepare":
        from .prepare import prepare
        prepare()
    elif args.command == "refresh-candidate":
        from .prepare import refresh_candidate
        refresh_candidate()
    elif args.command == "report-proposal":
        from .report import documents
        documents()
    elif args.command == "seal":
        from .protocol import Proposal
        Proposal().seal(args.personal_review)
    elif args.command == "run":
        from .campaign import Campaign
        print(Campaign().run(args.authorization, resume=args.resume))
    elif args.command == "evaluate":
        from .evaluation import evaluate
        value = evaluate(reviews_dir=args.personal_reviews)
        print({k: value[k] for k in ("operationally_complete", "recorded_results", "H1", "H2")})


if __name__ == "__main__": main()

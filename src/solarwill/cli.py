from __future__ import annotations

import argparse
import json
import sys

from solarwill.app import run_decision, save_trace
from solarwill.config import load_env
from solarwill.domain.models import DecisionRequest


def _run(req: DecisionRequest):
    return run_decision(req)


def _save_trace(response):
    return save_trace(response)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="solarwill", description="SolarWill Kernel CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Run one decision-support query")
    run_parser.add_argument("question", help="Question to evaluate")
    run_parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print JSON output",
    )
    return parser


def main() -> None:
    load_env()
    parser = _build_parser()
    args = parser.parse_args()

    if args.command != "run":
        parser.error("unknown command")

    req = DecisionRequest(question=args.question)
    result = _run(req)
    trace_path = _save_trace(result)

    if trace_path is not None:
        print(f"[solarwill] trace saved to: {trace_path}", file=sys.stderr)

    if args.pretty:
        print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    else:
        print(json.dumps(result.to_dict(), ensure_ascii=False))


if __name__ == "__main__":
    main()
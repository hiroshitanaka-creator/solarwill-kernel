from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from solarwill.app import run_decision, save_trace
from solarwill.config import get_settings, load_env
from solarwill.domain.models import DecisionRequest


def load_cases(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    cases = payload.get("cases", [])
    if not isinstance(cases, list):
        raise ValueError("sample cases file must contain a top-level 'cases' list")
    return cases


def run_case(case: dict[str, Any]) -> dict[str, Any]:
    question = str(case["question"]).strip()
    req = DecisionRequest(question=question)
    response = run_decision(req)
    trace_path = save_trace(response)

    return {
        "case_id": case.get("case_id"),
        "category": case.get("category"),
        "question": question,
        "expected_constraint_result": case.get("expected_constraint_result"),
        "actual_constraint_result": response.trace.constraint_result,
        "backend_requested": response.trace.backend_requested,
        "backend_used": response.trace.backend_used,
        "status": response.status,
        "notes": response.trace.notes,
        "trace_path": str(trace_path) if trace_path is not None else None,
        "response": response.to_dict(),
    }


def validate_results(
    results: list[dict[str, Any]],
    require_requested_backend_for_non_blocked: bool,
) -> list[str]:
    failures: list[str] = []

    for item in results:
        case_id = item["case_id"]
        expected_constraint = item["expected_constraint_result"]
        actual_constraint = item["actual_constraint_result"]
        backend_requested = item["backend_requested"]
        backend_used = item["backend_used"]

        if expected_constraint != actual_constraint:
            failures.append(
                f"{case_id}: expected_constraint_result={expected_constraint!r} "
                f"but actual_constraint_result={actual_constraint!r}"
            )

        if require_requested_backend_for_non_blocked and actual_constraint != "blocked":
            if backend_used != backend_requested:
                failures.append(
                    f"{case_id}: backend_requested={backend_requested!r} "
                    f"but backend_used={backend_used!r}"
                )

    return failures


def build_summary(results: list[dict[str, Any]], failures: list[str]) -> dict[str, Any]:
    settings = get_settings()

    counts_by_constraint: dict[str, int] = {}
    counts_by_status: dict[str, int] = {}
    counts_by_backend_used: dict[str, int] = {}

    for item in results:
        constraint = str(item["actual_constraint_result"])
        status = str(item["status"])
        backend_used = str(item["backend_used"])

        counts_by_constraint[constraint] = counts_by_constraint.get(constraint, 0) + 1
        counts_by_status[status] = counts_by_status.get(status, 0) + 1
        counts_by_backend_used[backend_used] = counts_by_backend_used.get(backend_used, 0) + 1

    return {
        "backend": settings.backend,
        "prompt_version": settings.prompt_version,
        "total_cases": len(results),
        "counts_by_constraint": counts_by_constraint,
        "counts_by_status": counts_by_status,
        "counts_by_backend_used": counts_by_backend_used,
        "failures": failures,
        "results": results,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run SolarWill against fixed sample cases")
    parser.add_argument(
        "--cases-file",
        default="tests/fixtures/sample_cases.json",
        help="Path to JSON file containing fixed sample cases",
    )
    parser.add_argument(
        "--output-file",
        default="artifacts/case_results.json",
        help="Path to output JSON file",
    )
    parser.add_argument(
        "--require-requested-backend-for-non-blocked",
        action="store_true",
        help="Fail if backend_used != backend_requested for non-blocked cases",
    )
    return parser.parse_args()


def main() -> None:
    load_env()
    args = parse_args()

    cases_path = Path(args.cases_file)
    output_path = Path(args.output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    cases = load_cases(cases_path)
    results = [run_case(case) for case in cases]
    failures = validate_results(
        results,
        require_requested_backend_for_non_blocked=args.require_requested_backend_for_non_blocked,
    )
    summary = build_summary(results, failures)

    output_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(json.dumps(summary, ensure_ascii=False, indent=2))

    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
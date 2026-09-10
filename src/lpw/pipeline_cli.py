"""Provide fail-closed pipeline check, test, and production preflight commands."""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence

from lpw.operations.pipeline_validation import PipelineEnvironmentValidator


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser.

    Returns:
        Configured argument parser.
    """

    parser = argparse.ArgumentParser(prog="lpw-pipeline")
    subparsers = parser.add_subparsers(dest="command", required=True)
    check = subparsers.add_parser("check", help="validate hardware, models, dependencies, MCP, and disk")
    check.add_argument("--environment", choices=("local", "production"), default="local")
    subparsers.add_parser("test", help="run safe local validation and write readiness evidence")
    subparsers.add_parser("production", help="run production preflight without bypassing local readiness")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the requested validation command and print structured JSON.

    Args:
        argv: Optional command arguments; process arguments are used when omitted.

    Returns:
        Zero when the requested gate passes, otherwise two.
    """

    arguments = build_parser().parse_args(argv)
    validator = PipelineEnvironmentValidator()
    if arguments.command == "check":
        report = validator.run_check(arguments.environment)
        passed = report["ready"]
    elif arguments.command == "test":
        report = validator.run_local_test()
        passed = report["production_ready"]
    else:
        report = validator.production_preflight()
        passed = report["production_allowed"]
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if passed else 2


if __name__ == "__main__":
    raise SystemExit(main())

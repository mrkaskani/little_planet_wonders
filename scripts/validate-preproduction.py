#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from lpw.context.preproduction_validation import validate_preproduction


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate reusable Riri & Yoyo pre-production YAML and assets."
    )
    parser.add_argument(
        "project_root",
        nargs="?",
        type=Path,
        default=Path("src/lpw/context/projects/riri-yoyo"),
    )
    parser.add_argument(
        "--strict-approvals",
        action="store_true",
        help="Treat pending visual and listening approvals as errors.",
    )
    arguments = parser.parse_args()
    report = validate_preproduction(
        arguments.project_root, strict_approvals=arguments.strict_approvals
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())


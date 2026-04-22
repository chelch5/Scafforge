from __future__ import annotations

import argparse
import json
from pathlib import Path

from package_evidence import default_package_root, stage_active_audit


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Copy a downstream diagnosis pack into Scafforge's active-audits workspace and materialize the machine-readable evidence manifest."
    )
    parser.add_argument("diagnosis", help="Path to a diagnosis-pack directory or its manifest.json.")
    parser.add_argument("--repo-name", help="Optional explicit repo name for the active-audits folder.")
    parser.add_argument(
        "--package-root",
        help="Optional Scafforge package root override. Defaults to the current repository that owns this script.",
    )
    parser.add_argument(
        "--agent-log",
        action="append",
        default=[],
        help="Optional audit-run or agent log to copy into active-audits/<repo>/raw/logs/. May be repeated.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    package_root = (
        Path(args.package_root).expanduser().resolve()
        if args.package_root
        else default_package_root(Path(__file__))
    )
    result = stage_active_audit(
        package_root=package_root,
        diagnosis_input=Path(args.diagnosis),
        repo_name=args.repo_name,
        agent_logs=[Path(path) for path in args.agent_log],
    )
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

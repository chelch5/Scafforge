from __future__ import annotations

import argparse
import json
from pathlib import Path

from package_evidence import (
    CANONICAL_PACKAGE_VALIDATION_COMMANDS,
    current_iso_timestamp,
    package_fix_record_path,
    read_json,
    resume_ready_path,
    write_json,
)
from package_evidence import evidence_manifest_path as active_evidence_manifest_path
from package_evidence import investigator_report_json_path

VALIDATION_STATUSES = {"passed", "failed", "not-run"}
PR_STATUSES = {"draft", "open", "merged"}


def parse_validation_result(raw: str) -> dict[str, str]:
    command, separator, status = raw.partition("=")
    command = command.strip()
    status = status.strip()
    if not separator or not command or status not in VALIDATION_STATUSES:
        raise ValueError(
            f"Invalid --validation value `{raw}`. Use the form '<command>=passed|failed|not-run'."
        )
    return {"command": command, "status": status}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Record the reviewable package-fix PR state for one active-audits repo and enforce the meta-loop review rules."
    )
    parser.add_argument("active_audit_root", help="Path to active-audits/<repo>/ for the package fix record.")
    parser.add_argument("--status", choices=sorted(PR_STATUSES), required=True, help="Current package-fix PR state.")
    parser.add_argument("--package-pr", help="Package-fix PR reference, for example #123.")
    parser.add_argument("--package-issue", action="append", default=[], help="Linked GitHub issue reference. May be repeated.")
    parser.add_argument("--package-commit", help="Merged package commit that carries the fix.")
    parser.add_argument(
        "--validation",
        action="append",
        default=[],
        help="Canonical validation result in the form '<command>=passed|failed|not-run'. May be repeated.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    active_audit_root = Path(args.active_audit_root).expanduser().resolve()
    evidence_manifest = read_json(active_evidence_manifest_path(active_audit_root))
    if not isinstance(evidence_manifest, dict):
        raise SystemExit(f"Missing evidence manifest at {active_evidence_manifest_path(active_audit_root)}")
    validation_results = [parse_validation_result(item) for item in args.validation]
    validation_lookup = {item["command"]: item["status"] for item in validation_results}
    missing_commands = [command for command in CANONICAL_PACKAGE_VALIDATION_COMMANDS if command not in validation_lookup]
    if missing_commands:
        raise SystemExit(
            "Missing canonical package validation results for: " + ", ".join(missing_commands)
        )
    if args.status in {"open", "merged"} and not args.package_pr:
        raise SystemExit("--package-pr is required once the package fix has a live PR.")
    if args.status == "merged" and not args.package_commit:
        raise SystemExit("--package-commit is required once the package fix PR is merged.")
    issue_refs = [item.strip() for item in args.package_issue if item.strip()]
    github_tracking_required = (
        isinstance(evidence_manifest.get("escalation_decision"), dict)
        and evidence_manifest["escalation_decision"].get("github_tracking_required") is True
    )
    if github_tracking_required and not issue_refs:
        raise SystemExit("At least one --package-issue is required for escalated package evidence.")
    package_validation_passed = all(
        validation_lookup[command] == "passed" for command in CANONICAL_PACKAGE_VALIDATION_COMMANDS
    )
    if args.status == "merged" and not package_validation_passed:
        raise SystemExit("Merged package-fix records require every canonical package validation command to pass.")

    record = {
        "version": 1,
        "repo_name": evidence_manifest.get("repo_name"),
        "recorded_at": current_iso_timestamp(),
        "evidence_manifest_path": str(active_evidence_manifest_path(active_audit_root)),
        "investigator_report_path": (
            str(investigator_report_json_path(active_audit_root))
            if investigator_report_json_path(active_audit_root).exists()
            else None
        ),
        "package_issue_refs": issue_refs,
        "package_pr_ref": args.package_pr.strip() if args.package_pr else None,
        "package_commit": args.package_commit.strip() if args.package_commit else None,
        "status": args.status,
        "review_policy": {
            "normal_package_review_required": True,
            "evidence_backed_only": True,
            "docs_validators_and_contract_text_must_move_together": True,
            "downstream_revalidation_required": True,
        },
        "validation_results": validation_results,
        "package_validation_passed": package_validation_passed,
        "downstream_revalidation_required": True,
        "downstream_revalidation_diagnosis_kind": "post_package_revalidation",
        "downstream_resume_signal_path": str(resume_ready_path(active_audit_root)),
    }
    write_json(package_fix_record_path(active_audit_root), record)
    print(json.dumps(record, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

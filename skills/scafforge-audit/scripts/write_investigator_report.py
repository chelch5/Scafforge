from __future__ import annotations

import argparse
import json
from pathlib import Path

from package_evidence import (
    current_iso_timestamp,
    evidence_manifest_path,
    investigator_report_json_path,
    investigator_report_markdown_path,
    read_json,
    write_json,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Write the package-side investigator report for one staged active-audits repo."
    )
    parser.add_argument("active_audit_root", help="Path to active-audits/<repo>/ for the investigation.")
    parser.add_argument("--triggering-code", action="append", default=[], help="Finding code that triggered investigation. May be repeated.")
    parser.add_argument("--symptom-summary", required=True, help="Concise downstream symptom summary.")
    parser.add_argument("--cause-hypothesis", required=True, help="Package-owned cause hypothesis.")
    parser.add_argument("--prevented-by", required=True, help="Prevented-by analysis for the package defect or gap.")
    parser.add_argument("--surface", action="append", default=[], help="Exact Scafforge package surface to change. May be repeated.")
    parser.add_argument(
        "--revalidation-step",
        action="append",
        default=[],
        help="Validation or revalidation step required after the package fix. May be repeated.",
    )
    parser.add_argument("--issue-ref", action="append", default=[], help="Optional GitHub issue reference. May be repeated.")
    parser.add_argument("--no-action-required", action="store_true", help="Record that the investigation concluded no package change is needed.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    active_audit_root = Path(args.active_audit_root).expanduser().resolve()
    evidence_manifest = read_json(evidence_manifest_path(active_audit_root))
    if not isinstance(evidence_manifest, dict):
        raise SystemExit(f"Missing evidence manifest at {evidence_manifest_path(active_audit_root)}")

    triggering_codes = [code.strip() for code in args.triggering_code if code.strip()]
    if not triggering_codes:
        triggering_codes = [
            str(code).strip()
            for code in evidence_manifest.get("triggering_finding_codes", [])
            if isinstance(code, str) and code.strip()
        ]
    surfaces = [item.strip() for item in args.surface if item.strip()]
    revalidation_steps = [item.strip() for item in args.revalidation_step if item.strip()]
    if not args.no_action_required and not surfaces:
        raise SystemExit("At least one --surface is required unless --no-action-required is set.")
    if not args.no_action_required and not revalidation_steps:
        raise SystemExit("At least one --revalidation-step is required unless --no-action-required is set.")

    report = {
        "version": 1,
        "repo_name": evidence_manifest.get("repo_name"),
        "generated_at": current_iso_timestamp(),
        "evidence_manifest_path": str(evidence_manifest_path(active_audit_root)),
        "triggering_finding_codes": triggering_codes,
        "originating_audit_pack_timestamp": evidence_manifest.get("audit_generated_at"),
        "downstream_symptom_summary": args.symptom_summary.strip(),
        "package_owned_cause_hypothesis": args.cause_hypothesis.strip(),
        "prevented_by_analysis": args.prevented_by.strip(),
        "exact_package_surfaces_to_change": surfaces,
        "revalidation_plan": revalidation_steps,
        "no_action_required": args.no_action_required,
        "github_issue_refs": [item.strip() for item in args.issue_ref if item.strip()],
    }
    write_json(investigator_report_json_path(active_audit_root), report)

    lines = [
        "# Package Investigator Report",
        "",
        f"- repo_name: {report['repo_name']}",
        f"- originating_audit_pack_timestamp: {report['originating_audit_pack_timestamp']}",
        "",
        "## Triggering Finding Codes",
        "",
        *([f"- {code}" for code in report["triggering_finding_codes"]] or ["- None recorded."]),
        "",
        "## Downstream Symptom Summary",
        "",
        report["downstream_symptom_summary"],
        "",
        "## Package-Owned Cause Hypothesis",
        "",
        report["package_owned_cause_hypothesis"],
        "",
        "## Prevented-By Analysis",
        "",
        report["prevented_by_analysis"],
        "",
        "## Exact Package Surfaces To Change",
        "",
        *([f"- {item}" for item in report["exact_package_surfaces_to_change"]] or ["- No package change required."]),
        "",
        "## Revalidation Plan",
        "",
        *([f"- {item}" for item in report["revalidation_plan"]] or ["- No package revalidation required."]),
        "",
        "## Decision",
        "",
        f"- no_action_required: {'true' if report['no_action_required'] else 'false'}",
        *([f"- github_issue_ref: {item}" for item in report["github_issue_refs"]] or []),
        "",
    ]
    investigator_report_markdown_path(active_audit_root).parent.mkdir(parents=True, exist_ok=True)
    investigator_report_markdown_path(active_audit_root).write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

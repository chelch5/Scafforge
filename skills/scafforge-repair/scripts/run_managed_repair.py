from __future__ import annotations

import argparse
import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from apply_repo_process_repair import (
    apply_repair,
    load_metadata,
    load_pending_process_verification,
    run_bootstrap_render,
    verification_logs,
)
from audit_repo_process import audit_repo
from regenerate_restart_surfaces import regenerate_restart_surfaces


EXECUTION_RECORD_PATH = Path(".opencode/meta/repair-execution.json")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Scafforge managed repair and emit a fail-closed execution record.")
    parser.add_argument("repo_root", help="Repository root to repair.")
    parser.add_argument("--project-name", help="Override project name when provenance is missing.")
    parser.add_argument("--project-slug", help="Override project slug when provenance is missing.")
    parser.add_argument("--agent-prefix", help="Override agent prefix when provenance is missing.")
    parser.add_argument("--model-provider", help="Override model provider when provenance is missing.")
    parser.add_argument("--planner-model", help="Override planner model when provenance is missing.")
    parser.add_argument("--implementer-model", help="Override implementer model when provenance is missing.")
    parser.add_argument("--utility-model", help="Override utility model when provenance is missing.")
    parser.add_argument("--stack-label", default="framework-agnostic", help="Stack label for regenerated process docs.")
    parser.add_argument(
        "--change-summary",
        default="Managed Scafforge repair runner refreshed deterministic workflow surfaces and evaluated downstream repair obligations.",
        help="Summary stored in workflow-state and repair history.",
    )
    parser.add_argument("--skip-deterministic-refresh", action="store_true", help="Do not rerun the deterministic replacement pass.")
    parser.add_argument("--skip-verify", action="store_true", help="Skip post-repair verification.")
    parser.add_argument("--supporting-log", action="append", default=[], help="Optional supporting transcript path. May be provided multiple times.")
    parser.add_argument("--stage-complete", action="append", default=[], help="Mark a required follow-on stage as completed by the host skill.")
    parser.add_argument("--fail-on", choices=("never", "warning", "error"), default="never")
    return parser.parse_args()


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def current_iso_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def find_placeholder_skills(repo_root: Path) -> list[str]:
    hits: list[str] = []
    skills_root = repo_root / ".opencode" / "skills"
    if not skills_root.exists():
        return hits
    for path in sorted(skills_root.rglob("SKILL.md")):
        text = load_text(path)
        if "Replace this file" in text or "TODO: replace" in text:
            hits.append(str(path.relative_to(repo_root)))
    return hits


def detect_agent_prompt_drift(repo_root: Path) -> list[str]:
    hits: list[str] = []
    agents_root = repo_root / ".opencode" / "agents"
    if not agents_root.exists():
        return hits

    team_leader = next(agents_root.glob("*team-leader*.md"), None)
    if team_leader:
        text = load_text(team_leader)
        if "next_action_tool" not in text or "summary-only stopping is invalid" not in text:
            hits.append(str(team_leader.relative_to(repo_root)))

    for pattern in ("*implementer*.md", "*lane-executor*.md", "*docs-handoff*.md"):
        for path in agents_root.glob(pattern):
            text = load_text(path)
            if "team leader already owns lease claim and release" not in text:
                hits.append(str(path.relative_to(repo_root)))
    return sorted(set(hits))


def derive_required_follow_on_stages(
    repo_root: Path,
    findings: list[Any],
    replaced_surfaces: list[str],
    pending_process_verification: bool,
) -> list[dict[str, str]]:
    required: list[dict[str, str]] = []
    placeholder_skills = find_placeholder_skills(repo_root)
    prompt_drift = detect_agent_prompt_drift(repo_root)
    finding_codes = {getattr(finding, "code", "") for finding in findings}

    if placeholder_skills or "scaffold-managed .opencode/skills" in replaced_surfaces or any(code.startswith(("SKILL", "MODEL")) for code in finding_codes):
        required.append(
            {
                "stage": "project-skill-bootstrap",
                "reason": "Repo-local skills were replaced or still contain generic placeholder/model drift that must be regenerated with project-specific content.",
            }
        )
    if prompt_drift or any(code.startswith("WFLOW") for code in finding_codes):
        required.append(
            {
                "stage": "opencode-team-bootstrap",
                "reason": "Agent or .opencode prompt surfaces still drift from the current workflow contract and must be regenerated.",
            }
        )
        required.append(
            {
                "stage": "agent-prompt-engineering",
                "reason": "Prompt behavior changed or remains stale after repair, so the same-session hardening pass is required before handoff.",
            }
        )
    if pending_process_verification or any(code.startswith(("EXEC", "ENV")) for code in finding_codes):
        required.append(
            {
                "stage": "ticket-pack-builder",
                "reason": "Repair left remediation or reverification follow-up that must be routed into the repo ticket system.",
            }
        )
    required.append(
        {
            "stage": "handoff-brief",
            "reason": "Restart surfaces must be regenerated only after required follow-on repair stages are complete.",
        }
    )
    return required


def summarize_verification(findings: list[Any], pending_process_verification: bool, performed: bool, supporting_logs: list[Path]) -> dict[str, Any]:
    return {
        "performed": performed,
        "finding_count": len(findings),
        "error_count": sum(1 for finding in findings if getattr(finding, "severity", "") == "error"),
        "warning_count": sum(1 for finding in findings if getattr(finding, "severity", "") == "warning"),
        "codes": [getattr(finding, "code", "") for finding in findings],
        "pending_process_verification": pending_process_verification,
        "verification_passed": performed and not findings,
        "supporting_logs": [str(path) for path in supporting_logs],
    }


def update_repair_follow_on_state(
    repo_root: Path,
    *,
    required_stage_names: list[str],
    completed_stage_names: list[str],
    blocking_reasons: list[str],
    verification_passed: bool,
    handoff_allowed: bool,
) -> dict[str, Any]:
    workflow_path = repo_root / ".opencode" / "state" / "workflow-state.json"
    workflow = read_json(workflow_path)
    if not isinstance(workflow, dict):
        workflow = {}
    process_version = workflow.get("process_version") if isinstance(workflow.get("process_version"), int) and workflow.get("process_version") > 0 else 6
    repair_follow_on = {
        "required_stages": required_stage_names,
        "completed_stages": completed_stage_names,
        "blocking_reasons": blocking_reasons,
        "verification_passed": verification_passed,
        "handoff_allowed": handoff_allowed,
        "last_updated_at": current_iso_timestamp(),
        "process_version": process_version,
    }
    workflow["repair_follow_on"] = repair_follow_on
    write_json(workflow_path, workflow)
    return repair_follow_on


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).expanduser().resolve()
    replaced_surfaces: list[str] = []

    if not args.skip_deterministic_refresh:
        metadata = load_metadata(repo_root, args)
        with tempfile.TemporaryDirectory(prefix="scafforge-repair-") as temp_dir:
            rendered_root = Path(temp_dir) / "rendered"
            run_bootstrap_render(rendered_root, metadata, args.stack_label)
            replaced_surfaces = apply_repair(repo_root, rendered_root, args.change_summary)

    logs = verification_logs(repo_root, args.supporting_log)
    findings = [] if args.skip_verify else audit_repo(repo_root, logs=logs)
    pending_process_verification = load_pending_process_verification(repo_root)
    verification_status = summarize_verification(findings, pending_process_verification, not args.skip_verify, logs)

    required_follow_on = derive_required_follow_on_stages(repo_root, findings, replaced_surfaces, pending_process_verification)
    required_stage_names = [item["stage"] for item in required_follow_on]
    requested_stage_names = sorted(set(args.stage_complete))
    completed_stage_names = {"deterministic-refresh"} if not args.skip_deterministic_refresh else set()

    executed_stages = [{"stage": "deterministic-refresh", "status": "completed"}] if not args.skip_deterministic_refresh else []
    handoff_requested = "handoff-brief" in requested_stage_names
    for stage in requested_stage_names:
        if stage == "handoff-brief":
            continue
        completed_stage_names.add(stage)
        executed_stages.append({"stage": stage, "status": "completed"})

    skipped_stages = []
    for item in required_follow_on:
        stage = item["stage"]
        if stage == "handoff-brief":
            continue
        if stage in completed_stage_names:
            continue
        skipped_stages.append(
            {
                "stage": stage,
                "status": "required_not_run",
                "reason": item["reason"],
            }
        )

    blocking_reasons = [f"{item['stage']} must still run: {item['reason']}" for item in skipped_stages]
    if args.skip_verify:
        blocking_reasons.append("Post-repair verification was skipped; rerun scafforge-audit before handoff.")
    elif findings:
        blocking_reasons.append("Post-repair verification still reports findings; handoff must remain blocked until they are resolved.")

    deferred_stages = []
    if handoff_requested:
        if blocking_reasons or not verification_status["verification_passed"]:
            deferred_stages.append(
                {
                    "stage": "handoff-brief",
                    "status": "deferred",
                    "reason": "Handoff remains blocked until verification passes and the other required repair follow-on stages are complete.",
                }
            )
        else:
            completed_stage_names.add("handoff-brief")
            executed_stages.append({"stage": "handoff-brief", "status": "completed"})
    elif "handoff-brief" in required_stage_names:
        skipped_stages.append(
            {
                "stage": "handoff-brief",
                "status": "required_not_run",
                "reason": next(item["reason"] for item in required_follow_on if item["stage"] == "handoff-brief"),
            }
        )
        blocking_reasons.append(
            f"handoff-brief must still run: {next(item['reason'] for item in required_follow_on if item['stage'] == 'handoff-brief')}"
        )

    handoff_allowed = verification_status["verification_passed"] and not blocking_reasons and "handoff-brief" in completed_stage_names
    repair_follow_on_state = update_repair_follow_on_state(
        repo_root,
        required_stage_names=required_stage_names,
        completed_stage_names=sorted(completed_stage_names),
        blocking_reasons=blocking_reasons,
        verification_passed=verification_status["verification_passed"],
        handoff_allowed=handoff_allowed,
    )

    payload = {
        "repair_plan": {
            "repo_root": str(repo_root),
            "required_follow_on_stages": required_follow_on,
            "replaced_surfaces": replaced_surfaces,
        },
        "stage_results": executed_stages + deferred_stages + skipped_stages,
        "execution_record": {
            "repo_root": str(repo_root),
            "required_follow_on_stages": required_stage_names,
            "executed_stages": executed_stages,
            "deferred_stages": deferred_stages,
            "skipped_stages": skipped_stages,
            "blocking_reasons": blocking_reasons,
            "verification_status": verification_status,
            "handoff_allowed": handoff_allowed,
        },
        "repair_follow_on_state": repair_follow_on_state,
    }

    write_json(repo_root / EXECUTION_RECORD_PATH, payload)
    regenerate_restart_surfaces(
        repo_root,
        reason=args.change_summary,
        source="scafforge-repair",
        next_action=blocking_reasons[0] if blocking_reasons else None,
        verification_passed=verification_status["verification_passed"],
    )

    print(json.dumps(payload, indent=2))

    if args.fail_on == "never":
        return 0 if handoff_allowed else 3
    if args.fail_on == "warning" and (findings or blocking_reasons):
        return 3
    if args.fail_on == "error" and any(getattr(finding, "severity", "") == "error" for finding in findings):
        return 3
    return 0 if handoff_allowed else 3


if __name__ == "__main__":
    raise SystemExit(main())

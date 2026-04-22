from __future__ import annotations

import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from disposition_bundle import PACKAGE_MANAGED_EXEC_CODES, failure_family_for_code

ACTIVE_AUDITS_DIRNAME = "active-audits"
RAW_DIAGNOSIS_DIR = Path("raw") / "diagnosis"
RAW_LOGS_DIR = Path("raw") / "logs"
EVIDENCE_MANIFEST_NAME = "evidence-manifest.json"
PACKAGE_EVIDENCE_BUNDLE_NAME = "package-evidence-bundle.json"
INVESTIGATOR_DIRNAME = "investigator"
INVESTIGATOR_JSON_NAME = "report.json"
INVESTIGATOR_MARKDOWN_NAME = "report.md"
FIXER_DIRNAME = "fixer"
PACKAGE_FIX_RECORD_NAME = "package-fix-record.json"
REVALIDATION_DIRNAME = "revalidation"
RESUME_READY_NAME = "resume-ready.json"
CANONICAL_PACKAGE_VALIDATION_COMMANDS = [
    "npm run validate:contract",
    "npm run validate:smoke",
    "python3 scripts/integration_test_scafforge.py",
    "python3 scripts/validate_gpttalker_migration.py",
]
REPEAT_ELIGIBLE_PREFIXES = ("WFLOW", "BOOT", "CYCLE")


def current_iso_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def normalize_path(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def sanitize_repo_name(value: str) -> str:
    sanitized = re.sub(r"[^A-Za-z0-9._-]+", "-", value.strip())
    sanitized = sanitized.strip(".-")
    return sanitized or "unknown-repo"


def audit_repo_name(repo_root: str | Path | None) -> str:
    if repo_root is None:
        return "unknown-repo"
    path = Path(repo_root)
    name = path.name if path.name else str(path)
    return sanitize_repo_name(name)


def default_package_root(script_path: Path) -> Path:
    return script_path.resolve().parents[3]


def active_audits_root(package_root: Path) -> Path:
    return package_root / ACTIVE_AUDITS_DIRNAME


def repo_active_audit_root(package_root: Path, repo_name: str) -> Path:
    return active_audits_root(package_root) / sanitize_repo_name(repo_name)


def evidence_manifest_path(active_audit_root: Path) -> Path:
    return active_audit_root / EVIDENCE_MANIFEST_NAME


def package_fix_record_path(active_audit_root: Path) -> Path:
    return active_audit_root / FIXER_DIRNAME / PACKAGE_FIX_RECORD_NAME


def investigator_report_json_path(active_audit_root: Path) -> Path:
    return active_audit_root / INVESTIGATOR_DIRNAME / INVESTIGATOR_JSON_NAME


def investigator_report_markdown_path(active_audit_root: Path) -> Path:
    return active_audit_root / INVESTIGATOR_DIRNAME / INVESTIGATOR_MARKDOWN_NAME


def resume_ready_path(active_audit_root: Path) -> Path:
    return active_audit_root / REVALIDATION_DIRNAME / RESUME_READY_NAME


def _existing_ref(repo_root: Path, relative_path: str) -> str | None:
    path = repo_root / relative_path
    return normalize_path(path, repo_root) if path.exists() else None


def _package_candidate(entry: dict[str, Any], recommendation: dict[str, Any] | None) -> bool:
    disposition_class = str(entry.get("disposition_class", "")).strip()
    repair_class = str((recommendation or {}).get("repair_class", "")).strip()
    return disposition_class == "managed_blocker" or "Scafforge package work required" in repair_class


def _warning_trigger_eligible(entry: dict[str, Any], recommendation: dict[str, Any] | None) -> bool:
    code = str(entry.get("code", "")).strip()
    repair_class = str((recommendation or {}).get("repair_class", "")).strip()
    return code.startswith(REPEAT_ELIGIBLE_PREFIXES) or code in PACKAGE_MANAGED_EXEC_CODES or "Scafforge package work required" in repair_class


def _load_active_window_records(package_root: Path, current_repo_name: str) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    root = active_audits_root(package_root)
    if not root.exists():
        return records
    for manifest_path in sorted(root.glob(f"*/{EVIDENCE_MANIFEST_NAME}")):
        payload = read_json(manifest_path)
        if not isinstance(payload, dict):
            continue
        repo_name = sanitize_repo_name(str(payload.get("repo_name", "")).strip() or manifest_path.parent.name)
        if not repo_name or repo_name == sanitize_repo_name(current_repo_name):
            continue
        tracked_codes = {
            str(code).strip()
            for code in payload.get("triggering_finding_codes", [])
            if isinstance(code, str) and code.strip()
        }
        tracked_families = {
            str(code).strip()
            for code in payload.get("tracked_failure_families", [])
            if isinstance(code, str) and code.strip()
        }
        for code in tracked_codes:
            tracked_families.add(failure_family_for_code(code))
        records.append(
            {
                "repo_name": repo_name,
                "tracked_codes": tracked_codes,
                "tracked_families": tracked_families,
                "manifest_path": normalize_path(manifest_path, package_root),
            }
        )
    return records


def _recurrence_details(records: list[dict[str, Any]], code: str) -> dict[str, Any]:
    family = failure_family_for_code(code)
    repo_names = sorted(
        {
            str(record.get("repo_name", "")).strip()
            for record in records
            if code in record.get("tracked_codes", set()) or family in record.get("tracked_families", set())
        }
    )
    return {
        "failure_family": family,
        "prior_matching_repo_names": repo_names,
        "prior_matching_repo_count": len(repo_names),
        "active_window_distinct_repo_count": len(repo_names) + 1,
        "repeated_across_distinct_repos": len(repo_names) >= 1,
    }


def build_package_evidence_bundle(
    *,
    package_root: Path,
    repo_root: Path,
    diagnosis_destination: Path,
    generated_at: str,
    diagnosis_kind: str,
    disposition_bundle: dict[str, Any],
    recommendations: list[dict[str, Any]],
    recommended_next_step: str,
    package_work_required_first: bool,
    report_paths: dict[str, str],
    source_surface_map: dict[str, str],
) -> dict[str, Any]:
    repo_name = audit_repo_name(repo_root)
    active_window_records = _load_active_window_records(package_root, repo_name)
    recommendation_lookup: dict[str, dict[str, Any]] = {}
    for item in recommendations:
        if not isinstance(item, dict):
            continue
        linked_codes = item.get("source_finding_codes")
        if isinstance(linked_codes, list):
            codes = [str(code).strip() for code in linked_codes if str(code).strip()]
        else:
            code = str(item.get("source_finding_code", "")).strip()
            codes = [code] if code else []
        for code in codes:
            recommendation_lookup[code] = item

    bundle_findings = [
        item
        for item in disposition_bundle.get("findings", [])
        if isinstance(item, dict) and str(item.get("code", "")).strip()
    ]
    tracked_families = sorted(
        {
            str(item.get("failure_family", "")).strip() or failure_family_for_code(str(item.get("code", "")))
            for item in bundle_findings
            if _package_candidate(item, recommendation_lookup.get(str(item.get("code", "")).strip()))
        }
    )
    triggering_codes: list[str] = []
    triggering_families: set[str] = set()
    candidate_surfaces: set[str] = set()
    matched_rules: list[dict[str, Any]] = []
    rationale: list[str] = []

    for entry in bundle_findings:
        code = str(entry.get("code", "")).strip()
        severity = str(entry.get("severity", "")).strip()
        disposition_class = str(entry.get("disposition_class", "")).strip()
        recommendation = recommendation_lookup.get(code)
        recurrence = _recurrence_details(active_window_records, code)
        repeated = recurrence["repeated_across_distinct_repos"]
        package_candidate = _package_candidate(entry, recommendation)
        route_requires_package_change = "Scafforge package work required" in str(
            (recommendation or {}).get("repair_class", "")
        )
        if code.startswith(("EXEC", "REF")) and code not in PACKAGE_MANAGED_EXEC_CODES and disposition_class != "managed_blocker":
            continue
        should_trigger = False
        reason = ""
        if severity == "error" and package_candidate:
            should_trigger = True
            reason = "managed-surface contradiction reached the error severity floor"
        elif severity == "warning" and repeated and _warning_trigger_eligible(entry, recommendation):
            should_trigger = True
            reason = "warning-level failure repeated across distinct repos in the active window"
        elif severity == "warning" and route_requires_package_change:
            should_trigger = True
            reason = "warning-level finding still requires a new Scafforge package change before downstream repair may resume"
        if not should_trigger:
            continue
        triggering_codes.append(code)
        triggering_families.add(str(recurrence["failure_family"]))
        surface = source_surface_map.get(code)
        if surface:
            candidate_surfaces.add(surface)
        matched_rules.append(
            {
                "code": code,
                "severity": severity,
                "disposition_class": disposition_class,
                "failure_family": recurrence["failure_family"],
                "reason": reason,
                "prior_matching_repo_names": recurrence["prior_matching_repo_names"],
                "active_window_distinct_repo_count": recurrence["active_window_distinct_repo_count"],
            }
        )
        rationale.append(
            f"{code}: {reason}; prior active-window matches: {', '.join(recurrence['prior_matching_repo_names']) if recurrence['prior_matching_repo_names'] else 'none'}."
        )

    restart_surface_refs = {
        "start_here": _existing_ref(repo_root, "START-HERE.md"),
        "latest_handoff": _existing_ref(repo_root, ".opencode/state/latest-handoff.md"),
        "context_snapshot": _existing_ref(repo_root, ".opencode/state/context-snapshot.md"),
    }
    bootstrap_or_provenance_refs = [
        ref
        for ref in (
            _existing_ref(repo_root, ".opencode/meta/bootstrap-provenance.json"),
            _existing_ref(repo_root, ".opencode/meta/repair-execution.json"),
            _existing_ref(repo_root, ".opencode/meta/repair-follow-on-state.json"),
        )
        if ref
    ]
    github_tracking_required = bool(triggering_codes) and (
        package_work_required_first or any(item["prior_matching_repo_names"] for item in matched_rules)
    )
    return {
        "version": 1,
        "repo_name": repo_name,
        "audit_generated_at": generated_at,
        "diagnosis_kind": diagnosis_kind,
        "triggering_finding_codes": sorted(set(triggering_codes)),
        "triggering_failure_families": sorted(triggering_families),
        "tracked_failure_families": tracked_families,
        "disposition_summary": {
            "overall": disposition_bundle.get("ownership_summary", {}).get("overall", "advisory"),
            "counts": disposition_bundle.get("counts", {}),
            "package_work_required_first": package_work_required_first,
            "recommended_next_step": recommended_next_step,
        },
        "audit_pack_path": normalize_path(diagnosis_destination, repo_root),
        "report_paths": dict(report_paths),
        "restart_surface_refs": restart_surface_refs,
        "workflow_state_ref": _existing_ref(repo_root, ".opencode/state/workflow-state.json"),
        "bootstrap_or_provenance_refs": bootstrap_or_provenance_refs,
        "candidate_package_surfaces": sorted(candidate_surfaces),
        "escalation_decision": {
            "matrix_version": 1,
            "decision": "auto_escalate" if triggering_codes else "repo_local_follow_up",
            "requires_investigation": bool(triggering_codes),
            "severity_floor": {
                "error": "managed-surface contradictions are always eligible package evidence",
                "warning": "warning-level findings need cross-repo repetition or a current package-change requirement before they escalate",
            },
            "active_window": {
                "mode": "current active-audits directory",
                "repo_count": len(active_window_records),
                "repo_names": sorted(str(item.get("repo_name", "")).strip() for item in active_window_records),
            },
            "matched_rules": matched_rules,
            "rationale": rationale,
            "github_tracking_required": github_tracking_required,
        },
        "package_validation_commands": list(CANONICAL_PACKAGE_VALIDATION_COMMANDS),
        "downstream_revalidation": {
            "required": bool(triggering_codes) or package_work_required_first,
            "diagnosis_kind": "post_package_revalidation",
            "resume_ready_path": f"{ACTIVE_AUDITS_DIRNAME}/{repo_name}/{REVALIDATION_DIRNAME}/{RESUME_READY_NAME}",
        },
    }


def resolve_diagnosis_manifest(path: Path) -> tuple[Path, Path, dict[str, Any]]:
    candidate = path.expanduser().resolve()
    manifest_path = candidate / "manifest.json" if candidate.is_dir() else candidate
    diagnosis_root = manifest_path.parent
    payload = read_json(manifest_path)
    if not isinstance(payload, dict):
        raise ValueError(f"Diagnosis manifest is not valid JSON: {manifest_path}")
    return diagnosis_root, manifest_path, payload


def _staged_diagnosis_dir_name(manifest: dict[str, Any], source_dir: Path) -> str:
    generated_at = str(manifest.get("generated_at", "")).strip()
    diagnosis_kind = str(manifest.get("diagnosis_kind", "")).strip()
    if generated_at:
        base = re.sub(r"[^0-9A-Za-z_-]+", "-", generated_at).strip("-") or source_dir.name
        kind = re.sub(r"[^0-9A-Za-z_-]+", "-", diagnosis_kind).strip("-")
        return f"{base}-{kind}" if kind else base
    return source_dir.name


def _copy_tree_once(source: Path, destination: Path) -> None:
    if destination.exists():
        raise FileExistsError(f"Refusing to overwrite existing copied evidence at {destination}")
    shutil.copytree(source, destination)


def _copy_logs(log_paths: list[Path], destination: Path, package_root: Path) -> list[str]:
    copied: list[str] = []
    if not log_paths:
        return copied
    destination.mkdir(parents=True, exist_ok=True)
    for log_path in log_paths:
        source = log_path.expanduser().resolve()
        if not source.exists():
            raise FileNotFoundError(f"Agent or audit log not found: {source}")
        target = destination / source.name
        if target.exists():
            raise FileExistsError(f"Refusing to overwrite existing copied log at {target}")
        shutil.copy2(source, target)
        copied.append(normalize_path(target, package_root))
    return copied


def _remaining_repo_local_work(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for recommendation in manifest.get("ticket_recommendations", []):
        if not isinstance(recommendation, dict):
            continue
        route = str(recommendation.get("route", "")).strip()
        if route not in {"scafforge-repair", "ticket-pack-builder"}:
            continue
        linked_codes = recommendation.get("source_finding_codes")
        items.append(
            {
                "id": str(recommendation.get("id", "")).strip() or None,
                "route": route,
                "title": str(recommendation.get("title", "")).strip() or None,
                "source_finding_codes": (
                    [str(code).strip() for code in linked_codes if str(code).strip()]
                    if isinstance(linked_codes, list)
                    else []
                ),
            }
        )
    if items:
        return items
    next_step = str(manifest.get("recommended_next_step", "")).strip()
    if next_step == "subject_repo_repair":
        return [{"id": None, "route": "scafforge-repair", "title": "Run subject-repo repair", "source_finding_codes": []}]
    if next_step == "subject_repo_source_follow_up":
        return [{"id": None, "route": "ticket-pack-builder", "title": "Route repo-local follow-up", "source_finding_codes": []}]
    return []


def build_resume_ready_signal(
    active_audit_root: Path,
    evidence_manifest: dict[str, Any],
    diagnosis_manifest: dict[str, Any],
) -> dict[str, Any]:
    fix_record = read_json(package_fix_record_path(active_audit_root))
    if not isinstance(fix_record, dict):
        fix_record = {}
    package_commit = str(fix_record.get("package_commit", "")).strip() or None
    merged = str(fix_record.get("status", "")).strip() == "merged"
    package_validation_passed = fix_record.get("package_validation_passed") is True
    package_pr_ref = str(fix_record.get("package_pr_ref", "")).strip() or None
    blocking_reasons: list[str] = []
    if not merged:
        blocking_reasons.append("Package-fix PR is not yet recorded as merged.")
    if not package_validation_passed:
        blocking_reasons.append("Canonical Scafforge package validation has not been recorded as fully passed.")
    if str(evidence_manifest.get("diagnosis_kind", "")).strip() != "post_package_revalidation":
        blocking_reasons.append("Resume-ready can only be derived from a post_package_revalidation audit.")
    if evidence_manifest.get("package_work_required_first") is True:
        blocking_reasons.append("The latest downstream revalidation still says package work is required first.")
    payload = {
        "repo_name": evidence_manifest.get("repo_name"),
        "package_commit": package_commit,
        "package_pr_ref": package_pr_ref,
        "revalidation_audit_timestamp": evidence_manifest.get("audit_generated_at"),
        "resume_ready": not blocking_reasons,
        "remaining_repo_local_work": _remaining_repo_local_work(diagnosis_manifest),
        "blocking_reasons": blocking_reasons,
        "evidence_manifest_path": normalize_path(evidence_manifest_path(active_audit_root), active_audit_root.parents[1]),
    }
    return payload


def stage_active_audit(
    *,
    package_root: Path,
    diagnosis_input: Path,
    repo_name: str | None = None,
    agent_logs: list[Path] | None = None,
) -> dict[str, Any]:
    diagnosis_root, manifest_path, diagnosis_manifest = resolve_diagnosis_manifest(diagnosis_input)
    package_evidence_bundle = diagnosis_manifest.get("package_evidence_bundle")
    if not isinstance(package_evidence_bundle, dict):
        raise ValueError(
            f"Diagnosis manifest at {manifest_path} does not contain `package_evidence_bundle`; rerun audit with the current package."
        )
    resolved_repo_name = sanitize_repo_name(repo_name or str(package_evidence_bundle.get("repo_name", "")).strip() or audit_repo_name(diagnosis_manifest.get("repo_root")))
    active_root = repo_active_audit_root(package_root, resolved_repo_name)
    raw_diagnosis_root = active_root / RAW_DIAGNOSIS_DIR / _staged_diagnosis_dir_name(diagnosis_manifest, diagnosis_root)
    active_root.mkdir(parents=True, exist_ok=True)
    _copy_tree_once(diagnosis_root, raw_diagnosis_root)
    copied_logs = _copy_logs(agent_logs or [], active_root / RAW_LOGS_DIR, package_root)
    copied_manifest_path = raw_diagnosis_root / "manifest.json"
    report_paths = {
        key: normalize_path(raw_diagnosis_root / value, package_root)
        for key, value in package_evidence_bundle.get("report_paths", {}).items()
        if isinstance(value, str) and value.strip()
    }
    staged_manifest = {
        "version": 1,
        "repo_name": resolved_repo_name,
        "staged_at": current_iso_timestamp(),
        "diagnosis_kind": diagnosis_manifest.get("diagnosis_kind"),
        "audit_generated_at": package_evidence_bundle.get("audit_generated_at"),
        "raw_diagnosis_pack_path": normalize_path(raw_diagnosis_root, package_root),
        "audit_manifest_path": normalize_path(copied_manifest_path, package_root),
        "package_evidence_bundle_path": normalize_path(raw_diagnosis_root / PACKAGE_EVIDENCE_BUNDLE_NAME, package_root),
        "disposition_bundle_path": normalize_path(raw_diagnosis_root / "disposition-bundle.json", package_root),
        "report_paths": report_paths,
        "supporting_log_paths": copied_logs,
        "triggering_finding_codes": list(package_evidence_bundle.get("triggering_finding_codes", [])),
        "tracked_failure_families": list(package_evidence_bundle.get("tracked_failure_families", [])),
        "package_work_required_first": diagnosis_manifest.get("package_work_required_first") is True,
        "recommended_next_step": diagnosis_manifest.get("recommended_next_step"),
        "candidate_package_surfaces": list(package_evidence_bundle.get("candidate_package_surfaces", [])),
        "escalation_decision": package_evidence_bundle.get("escalation_decision", {}),
        "restart_surface_refs": package_evidence_bundle.get("restart_surface_refs", {}),
        "workflow_state_ref": package_evidence_bundle.get("workflow_state_ref"),
        "bootstrap_or_provenance_refs": package_evidence_bundle.get("bootstrap_or_provenance_refs", []),
        "copied_raw_evidence_immutable": True,
    }
    write_json(evidence_manifest_path(active_root), staged_manifest)
    response = {
        "active_audit_root": str(active_root),
        "evidence_manifest_path": str(evidence_manifest_path(active_root)),
        "raw_diagnosis_pack_path": str(raw_diagnosis_root),
    }
    if str(diagnosis_manifest.get("diagnosis_kind", "")).strip() == "post_package_revalidation":
        resume_payload = build_resume_ready_signal(active_root, staged_manifest, diagnosis_manifest)
        write_json(resume_ready_path(active_root), resume_payload)
        response["resume_ready_path"] = str(resume_ready_path(active_root))
        response["resume_ready"] = resume_payload["resume_ready"]
    return response

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parents[2] / "scafforge-audit" / "scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from target_completion import (
    ANDROID_EXPORT_LANE,
    ANDROID_EXPORT_TICKET_ID,
    ANDROID_RELEASE_LANE,
    ANDROID_RELEASE_TICKET_ID,
    declares_godot_android_target,
    expected_android_debug_apk_relpath,
)

RUNTIME_SCRIPT_DIR = Path(__file__).resolve().parents[2] / "scafforge-pivot" / "scripts"
if str(RUNTIME_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(RUNTIME_SCRIPT_DIR))

from shared_generated_tool_runtime import run_generated_tool


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def normalize_path(path: Path, root: Path) -> str:
    return str(path.relative_to(root)).replace("\\", "/")


def find_latest_diagnosis(repo_root: Path) -> Path:
    diagnosis_root = repo_root / "diagnosis"
    if not diagnosis_root.exists():
        raise SystemExit("No diagnosis directory exists under the target repo.")
    candidates = sorted(
        [path for path in diagnosis_root.iterdir() if path.is_dir() and (path / "manifest.json").exists()],
        key=lambda item: item.name,
    )
    if not candidates:
        raise SystemExit("No diagnosis packs with manifest.json were found under diagnosis/.")
    return candidates[-1] / "manifest.json"


def resolve_diagnosis_path(repo_root: Path, provided: str | None) -> Path:
    if not provided:
        return find_latest_diagnosis(repo_root)
    path = Path(provided).expanduser().resolve()
    if path.is_dir():
        manifest_path = path / "manifest.json"
        if manifest_path.exists():
            return manifest_path
        raise SystemExit(f"Diagnosis directory does not contain manifest.json: {path}")
    if path.is_file():
        return path
    raise SystemExit(f"Diagnosis path does not exist: {path}")


def load_ticket_recommendations(diagnosis_manifest: Path) -> list[dict[str, Any]]:
    payload = read_json(diagnosis_manifest)
    if isinstance(payload, dict):
        if isinstance(payload.get("ticket_recommendations"), list):
            return [item for item in payload["ticket_recommendations"] if isinstance(item, dict)]
        managed_repair = payload.get("managed_repair")
        if isinstance(managed_repair, dict) and isinstance(managed_repair.get("ticket_recommendations"), list):
            return [item for item in managed_repair["ticket_recommendations"] if isinstance(item, dict)]
    return []


def render_ticket_document(ticket: dict[str, Any]) -> str:
    depends_on = ticket.get("depends_on") or []
    follow_ups = ticket.get("follow_up_ticket_ids") or []
    blockers = ticket.get("decision_blockers") or []
    acceptance = ticket.get("acceptance") or []
    artifacts = ticket.get("artifacts") or []
    return "\n".join(
        [
            f"# {ticket['id']}: {ticket['title']}",
            "",
            "## Summary",
            "",
            str(ticket["summary"]),
            "",
            "## Wave",
            "",
            str(ticket["wave"]),
            "",
            "## Lane",
            "",
            str(ticket["lane"]),
            "",
            "## Parallel Safety",
            "",
            f"- parallel_safe: {'true' if ticket.get('parallel_safe') else 'false'}",
            f"- overlap_risk: {ticket['overlap_risk']}",
            "",
            "## Stage",
            "",
            str(ticket["stage"]),
            "",
            "## Status",
            "",
            str(ticket["status"]),
            "",
            "## Trust",
            "",
            f"- resolution_state: {ticket['resolution_state']}",
            f"- verification_state: {ticket['verification_state']}",
            f"- finding_source: {ticket.get('finding_source') or 'None'}",
            f"- source_ticket_id: {ticket.get('source_ticket_id') or 'None'}",
            f"- source_mode: {ticket.get('source_mode') or 'None'}",
            "",
            "## Depends On",
            "",
            ", ".join(depends_on) if depends_on else "None",
            "",
            "## Follow-up Tickets",
            "",
            "\n".join(f"- {item}" for item in follow_ups) if follow_ups else "None",
            "",
            "## Decision Blockers",
            "",
            "\n".join(f"- {item}" for item in blockers) if blockers else "None",
            "",
            "## Acceptance Criteria",
            "",
            "\n".join(f"- [ ] {item}" for item in acceptance) if acceptance else "None",
            "",
            "## Artifacts",
            "",
            "\n".join(f"- {item.get('kind')}: {item.get('path')} ({item.get('stage')})" for item in artifacts) if artifacts else "- None yet",
            "",
            "## Notes",
            "",
            "Generated from audit remediation recommendations.",
            "",
        ]
    )


def render_board(manifest: dict[str, Any]) -> str:
    lines = [
        "# Ticket Board",
        "",
        "| Wave | ID | Title | Lane | Stage | Status | Resolution | Verification | Parallel Safe | Overlap Risk | Depends On | Follow-ups |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    tickets = sorted(manifest.get("tickets", []), key=lambda item: (item.get("wave", 0), item.get("id", "")))
    for ticket in tickets:
        depends_on = ", ".join(ticket.get("depends_on", [])) or "-"
        follow_ups = ", ".join(ticket.get("follow_up_ticket_ids", [])) or "-"
        lines.append(
            f"| {ticket.get('wave', 0)} | {ticket['id']} | {ticket['title']} | {ticket['lane']} | {ticket['stage']} | {ticket['status']} | {ticket['resolution_state']} | {ticket['verification_state']} | {'yes' if ticket.get('parallel_safe') else 'no'} | {ticket['overlap_risk']} | {depends_on} | {follow_ups} |"
        )
    lines.append("")
    return "\n".join(lines)


def next_wave(manifest: dict[str, Any]) -> int:
    waves = [int(ticket.get("wave", 0)) for ticket in manifest.get("tickets", []) if isinstance(ticket, dict)]
    return (max(waves) + 1) if waves else 0


def active_open_ticket(manifest: dict[str, Any]) -> dict[str, Any] | None:
    active_ticket_id = manifest.get("active_ticket")
    for ticket in manifest.get("tickets", []):
        if not isinstance(ticket, dict):
            continue
        if ticket.get("id") != active_ticket_id:
            continue
        if ticket.get("status") == "done" or ticket.get("resolution_state") == "superseded":
            return None
        return ticket
    return None


def build_acceptance(recommendation: dict[str, Any]) -> list[str]:
    code = str(recommendation.get("source_finding_code") or recommendation.get("id") or "unknown")
    summary = str(recommendation.get("summary") or recommendation.get("suggested_fix_approach") or "Re-run the relevant quality checks.")
    return [
        f"The validated finding `{code}` no longer reproduces.",
        f"Current quality checks rerun with evidence tied to the fix approach: {summary}",
    ]


def build_ticket_record(recommendation: dict[str, Any], manifest: dict[str, Any], active_ticket: dict[str, Any] | None, wave: int) -> dict[str, Any]:
    source_ticket_id = active_ticket["id"] if active_ticket else None
    source_mode = "split_scope" if source_ticket_id else "net_new_scope"
    source_files = recommendation.get("affected_files") or recommendation.get("source_files") or []
    files_display = ", ".join(str(item) for item in source_files) if source_files else "the affected repo area"
    description = str(recommendation.get("description") or recommendation.get("summary") or recommendation.get("title") or "")
    return {
        "id": str(recommendation["id"]),
        "title": str(recommendation.get("title") or recommendation["id"]),
        "wave": wave,
        "lane": "remediation",
        "parallel_safe": False,
        "overlap_risk": "low",
        "stage": "planning",
        "status": "todo",
        "depends_on": [],
        "summary": f"{description} Affected surfaces: {files_display}.",
        "acceptance": build_acceptance(recommendation),
        "decision_blockers": [],
        "artifacts": [],
        "resolution_state": "open",
        "verification_state": "suspect",
        "finding_source": str(recommendation.get("source_finding_code") or recommendation.get("id") or ""),
        "source_ticket_id": source_ticket_id,
        "follow_up_ticket_ids": [],
        "source_mode": source_mode,
    }


def create_ticket_via_runtime(repo_root: Path, ticket: dict[str, Any], *, activate: bool | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "id": ticket["id"],
        "title": ticket["title"],
        "lane": ticket["lane"],
        "wave": ticket["wave"],
        "summary": ticket["summary"],
        "acceptance": ticket["acceptance"],
    }
    if activate is not None:
        payload["activate"] = activate
    if ticket.get("depends_on"):
        payload["depends_on"] = ticket["depends_on"]
    if ticket.get("decision_blockers"):
        payload["decision_blockers"] = ticket["decision_blockers"]
    if ticket.get("parallel_safe") is not None:
        payload["parallel_safe"] = ticket["parallel_safe"]
    if ticket.get("overlap_risk"):
        payload["overlap_risk"] = ticket["overlap_risk"]
    if ticket.get("finding_source"):
        payload["finding_source"] = ticket["finding_source"]
    if ticket.get("source_ticket_id"):
        payload["source_ticket_id"] = ticket["source_ticket_id"]
    if ticket.get("source_mode"):
        payload["source_mode"] = ticket["source_mode"]
    if ticket.get("evidence_artifact_path"):
        payload["evidence_artifact_path"] = ticket["evidence_artifact_path"]
    return run_generated_tool(repo_root, ".opencode/tools/ticket_create.ts", payload)


def ensure_ticket_state(workflow: dict[str, Any], ticket_id: str) -> None:
    ticket_state = workflow.setdefault("ticket_state", {})
    if ticket_id not in ticket_state:
        ticket_state[ticket_id] = {
            "approved_plan": False,
            "reopen_count": 0,
            "needs_reverification": False,
        }


def append_unique(items: list[str], value: str) -> None:
    if value and value not in items:
        items.append(value)


def ensure_follow_up_link(source_ticket: dict[str, Any] | None, target_id: str) -> bool:
    if not isinstance(source_ticket, dict):
        return False
    follow_ups = source_ticket.setdefault("follow_up_ticket_ids", [])
    if isinstance(follow_ups, list):
        before = list(follow_ups)
        append_unique(follow_ups, target_id)
        return before != follow_ups
    return False


def ensure_split_scope_note(source_ticket: dict[str, Any] | None, target_id: str) -> bool:
    if not isinstance(source_ticket, dict):
        return False
    blockers = source_ticket.setdefault("decision_blockers", [])
    if not isinstance(blockers, list):
        return False
    note = f"Split scope delegated to follow-up ticket {target_id}. Keep the parent open and non-foreground until the child work lands."
    before = list(blockers)
    append_unique(blockers, note)
    return before != blockers


def ensure_target_depends(ticket: dict[str, Any], depends_on: list[str]) -> bool:
    existing = ticket.get("depends_on")
    current = [str(item).strip() for item in existing if isinstance(item, str) and str(item).strip()] if isinstance(existing, list) else []
    before = list(current)
    for item in depends_on:
        append_unique(current, item)
    ticket["depends_on"] = current
    return before != current


def android_export_summary() -> str:
    return (
        "Create and validate the repo-local Android export surfaces for this Godot Android target. "
        "This includes an Android preset in `export_presets.cfg`, non-placeholder repo-local `android/` support surfaces, "
        "and a recorded canonical export command for downstream release work."
    )


def build_android_export_ticket(*, wave: int, source_ticket_id: str | None) -> dict[str, Any]:
    return {
        "id": ANDROID_EXPORT_TICKET_ID,
        "title": "Create Android export surfaces",
        "wave": wave,
        "lane": ANDROID_EXPORT_LANE,
        "parallel_safe": False,
        "overlap_risk": "medium",
        "stage": "planning",
        "status": "todo",
        "depends_on": [],
        "summary": android_export_summary(),
        "acceptance": [
            "`export_presets.cfg` exists and defines an Android export preset.",
            "The repo-local `android/` support surfaces exist and are non-placeholder.",
            "The canonical Android export command is recorded in this ticket and the repo-local skill pack.",
        ],
        "decision_blockers": [],
        "artifacts": [],
        "resolution_state": "open",
        "verification_state": "suspect",
        "finding_source": "WFLOW025",
        "source_ticket_id": source_ticket_id,
        "follow_up_ticket_ids": [],
        "source_mode": "split_scope" if source_ticket_id else "net_new_scope",
    }


def build_android_release_ticket(*, wave: int, source_ticket_id: str | None, repo_root: Path) -> dict[str, Any]:
    apk_relpath = expected_android_debug_apk_relpath(repo_root)
    export_command = f"godot --headless --path . --export-debug Android {apk_relpath}"
    return {
        "id": ANDROID_RELEASE_TICKET_ID,
        "title": "Build Android debug APK",
        "wave": wave,
        "lane": ANDROID_RELEASE_LANE,
        "parallel_safe": False,
        "overlap_risk": "medium",
        "stage": "planning",
        "status": "todo",
        "depends_on": [source_ticket_id] if source_ticket_id else [],
        "summary": (
            f"Produce and validate the canonical debug APK for this Android target at `{apk_relpath}` using the repo's resolved Godot binary and Android export pipeline."
        ),
        "acceptance": [
            f"`{export_command}` succeeds or the exact resolved Godot binary equivalent is recorded with the same arguments.",
            f"The APK exists at `{apk_relpath}`.",
            f"`unzip -l {apk_relpath}` shows Android manifest and classes/resources content.",
        ],
        "decision_blockers": [],
        "artifacts": [],
        "resolution_state": "open",
        "verification_state": "suspect",
        "finding_source": "WFLOW025",
        "source_ticket_id": source_ticket_id,
        "follow_up_ticket_ids": [],
        "source_mode": "split_scope" if source_ticket_id else "net_new_scope",
    }


def upsert_ticket(
    *,
    repo_root: Path,
    manifest: dict[str, Any],
    workflow: dict[str, Any],
    ticket: dict[str, Any],
) -> str | None:
    tickets = manifest.setdefault("tickets", [])
    existing = next(
        (
            item
            for item in tickets
            if isinstance(item, dict) and str(item.get("id", "")).strip() == str(ticket.get("id", "")).strip()
        ),
        None,
    )
    touched = False
    if existing is None:
        tickets.append(ticket)
        existing = ticket
        touched = True
    else:
        for key in (
            "title",
            "wave",
            "lane",
            "parallel_safe",
            "overlap_risk",
            "summary",
            "acceptance",
            "finding_source",
            "source_mode",
        ):
            if existing.get(key) != ticket.get(key):
                existing[key] = ticket.get(key)
                touched = True
        if ensure_target_depends(existing, ticket.get("depends_on", [])):
            touched = True
        if ticket.get("source_ticket_id") and existing.get("source_ticket_id") != ticket.get("source_ticket_id"):
            existing["source_ticket_id"] = ticket.get("source_ticket_id")
            touched = True
        if str(existing.get("resolution_state", "open")).strip() in {"done", "superseded"} or str(existing.get("status", "")).strip() == "done":
            existing["stage"] = "planning"
            existing["status"] = "todo"
            existing["resolution_state"] = "open"
            existing["verification_state"] = "suspect"
            touched = True
    ensure_ticket_state(workflow, str(ticket["id"]))
    ticket_path = repo_root / "tickets" / f"{ticket['id']}.md"
    ticket_path.write_text(render_ticket_document(existing), encoding="utf-8")
    return str(ticket["id"]) if touched else None


def ensure_android_target_completion_tickets(
    *,
    repo_root: Path,
    manifest: dict[str, Any],
    workflow: dict[str, Any],
    active_ticket: dict[str, Any] | None,
) -> list[str]:
    if not declares_godot_android_target(repo_root):
        return []

    created_or_updated: list[str] = []
    source_ticket_id = str(active_ticket.get("id", "")).strip() if isinstance(active_ticket, dict) else None
    manifest_path = repo_root / "tickets" / "manifest.json"
    current_manifest = read_json(manifest_path)
    current_tickets = current_manifest.get("tickets", []) if isinstance(current_manifest, dict) else []
    android_record = next(
        (
            item
            for item in current_tickets
            if isinstance(item, dict) and str(item.get("id", "")).strip() == ANDROID_EXPORT_TICKET_ID
        ),
        None,
    )

    if not isinstance(android_record, dict):
        android_source_ticket_id = source_ticket_id if source_ticket_id and source_ticket_id != ANDROID_EXPORT_TICKET_ID else None
        android_ticket = build_android_export_ticket(
            wave=next_wave(current_manifest if isinstance(current_manifest, dict) else manifest),
            source_ticket_id=android_source_ticket_id,
        )
        create_ticket_via_runtime(repo_root, android_ticket, activate=True if android_source_ticket_id else None)
        created_or_updated.append(ANDROID_EXPORT_TICKET_ID)
        current_manifest = read_json(manifest_path)
        current_tickets = current_manifest.get("tickets", []) if isinstance(current_manifest, dict) else []
        android_record = next(
            (
                item
                for item in current_tickets
                if isinstance(item, dict) and str(item.get("id", "")).strip() == ANDROID_EXPORT_TICKET_ID
            ),
            None,
        )

    release_exists = any(
        isinstance(item, dict) and str(item.get("id", "")).strip() == ANDROID_RELEASE_TICKET_ID
        for item in current_tickets
    )
    if isinstance(android_record, dict) and not release_exists:
        release_ticket = build_android_release_ticket(
            wave=max(next_wave(current_manifest if isinstance(current_manifest, dict) else manifest), int(android_record.get("wave", 0)) + 1),
            source_ticket_id=ANDROID_EXPORT_TICKET_ID,
            repo_root=repo_root,
        )
        create_ticket_via_runtime(repo_root, release_ticket, activate=True)
        created_or_updated.append(ANDROID_RELEASE_TICKET_ID)
    return created_or_updated


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create remediation follow-up tickets from diagnosis recommendations.")
    parser.add_argument("repo_root", help="Path to the generated repo to update.")
    parser.add_argument("--diagnosis", help="Diagnosis pack directory or manifest path. Defaults to the latest diagnosis/ pack.")
    parser.add_argument("--activate-new-ticket", action="store_true", help="Make the first created remediation ticket active immediately.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).expanduser().resolve()
    diagnosis_manifest = resolve_diagnosis_path(repo_root, args.diagnosis)
    recommendations = [
        item
        for item in load_ticket_recommendations(diagnosis_manifest)
        if str(item.get("route", "")).strip() == "ticket-pack-builder"
    ]

    manifest_path = repo_root / "tickets" / "manifest.json"
    manifest = read_json(manifest_path)
    if not isinstance(manifest, dict):
        manifest = {"tickets": []}
    existing_ids = {str(ticket.get("id")) for ticket in manifest.get("tickets", []) if isinstance(ticket, dict)}
    created_ids: list[str] = []
    active_ticket = active_open_ticket(manifest)
    wave = next_wave(manifest)

    for recommendation in recommendations:
        ticket_id = str(recommendation.get("id", "")).strip()
        if not ticket_id:
            continue
        if ticket_id in existing_ids:
            append_unique(created_ids, ticket_id)
            continue
        ticket = build_ticket_record(recommendation, manifest, active_ticket, wave)
        create_ticket_via_runtime(repo_root, ticket, activate=bool(args.activate_new_ticket and not created_ids))
        created_ids.append(ticket_id)
        existing_ids.add(ticket_id)

    android_follow_up_ids = ensure_android_target_completion_tickets(
        repo_root=repo_root,
        manifest=read_json(manifest_path) or {"tickets": []},
        workflow={},
        active_ticket=active_ticket,
    )
    for ticket_id in android_follow_up_ids:
        append_unique(created_ids, ticket_id)

    _ = render_board(manifest)

    if not created_ids:
        return 0

    print(
        json.dumps(
            {
                "created_tickets": created_ids,
                "diagnosis_manifest": normalize_path(diagnosis_manifest, repo_root) if diagnosis_manifest.is_relative_to(repo_root) else str(diagnosis_manifest),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

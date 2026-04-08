from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


ANDROID_EXPORT_TICKET_ID = "ANDROID-001"
ANDROID_RELEASE_TICKET_ID = "RELEASE-001"
ANDROID_SIGNING_TICKET_ID = "SIGNING-001"
ANDROID_EXPORT_LANE = "android-export"
ANDROID_RELEASE_LANE = "release-readiness"
ANDROID_SIGNING_LANE = "signing-prerequisites"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def read_json(path: Path) -> Any:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def canonical_brief_text(root: Path) -> str:
    return read_text(root / "docs" / "spec" / "CANONICAL-BRIEF.md")


def bootstrap_provenance(root: Path) -> dict[str, Any]:
    payload = read_json(root / ".opencode" / "meta" / "bootstrap-provenance.json")
    return payload if isinstance(payload, dict) else {}


def project_slug(root: Path) -> str:
    provenance = bootstrap_provenance(root)
    slug = provenance.get("project_slug")
    if isinstance(slug, str) and slug.strip():
        return slug.strip()
    return root.name.strip() or "project"


def stack_label(root: Path) -> str:
    provenance = bootstrap_provenance(root)
    stack = provenance.get("stack_label")
    if isinstance(stack, str) and stack.strip():
        return stack.strip()
    brief = canonical_brief_text(root)
    match = re.search(r"^\s*-\s*Stack label:\s*`?([^`\n]+)`?\s*$", brief, re.MULTILINE)
    return match.group(1).strip() if match else ""


def declares_godot_android_target(root: Path) -> bool:
    brief = canonical_brief_text(root).lower()
    stack = stack_label(root).lower()
    if "godot" in stack and "android" in stack:
        return True
    has_android_target = (
        "platform target is android" in brief
        or "target platform is android" in brief
        or "platform target: android" in brief
        or "android" in brief
    )
    has_godot = "engine is godot" in brief or "godot" in brief or (root / "project.godot").exists()
    return has_android_target and has_godot


def expected_android_debug_apk_relpath(root: Path) -> str:
    """Return the canonical runnable-proof APK path (debug APK only)."""
    return f"build/android/{project_slug(root)}-debug.apk"


def load_manifest(root: Path) -> dict[str, Any]:
    payload = read_json(root / "tickets" / "manifest.json")
    return payload if isinstance(payload, dict) else {}


def manifest_tickets(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    tickets = manifest.get("tickets")
    return [ticket for ticket in tickets if isinstance(ticket, dict)] if isinstance(tickets, list) else []


def ticket_by_id(manifest: dict[str, Any], ticket_id: str) -> dict[str, Any] | None:
    return next((ticket for ticket in manifest_tickets(manifest) if str(ticket.get("id", "")).strip() == ticket_id), None)


def requires_packaged_android_product(root: Path) -> bool:
    """Return True when the canonical brief requires a packaged Android product (release APK/AAB).

    Runnable proof (debug APK) is always meaningful. Deliverable proof applies only when
    the brief explicitly requires a packaged consumer-facing Android product.
    """
    brief = canonical_brief_text(root).lower()
    provenance = bootstrap_provenance(root)
    deliverable_kind = str(provenance.get("deliverable_kind", "")).lower()
    if deliverable_kind in {"release_apk", "release_aab", "packaged_apk", "packaged_aab"}:
        return True
    packaged_indicators = [
        "packaged mobile product",
        "store-ready build",
        "packaged android app",
        "release apk",
        "release aab",
        "signed apk",
        "signed aab",
        "play store",
        "google play",
        "packaged android product",
        "deliverable proof",
        "release-ready",
    ]
    return any(indicator in brief for indicator in packaged_indicators)


def deliverable_proof_path(root: Path) -> str | None:
    """Return the canonical deliverable-proof artifact path, or None when not applicable.

    Deliverable proof is only applicable when the brief requires a packaged Android product.
    """
    if not requires_packaged_android_product(root):
        return None
    provenance = bootstrap_provenance(root)
    declared = provenance.get("deliverable_artifact_path")
    if isinstance(declared, str) and declared.strip():
        return declared.strip()
    slug = project_slug(root)
    return f"build/android/{slug}-release.apk"


def has_signing_ownership(root: Path) -> bool:
    """Return True when signing prerequisites are declared and owned in the repo.

    Checks for:
    - SIGNING-001 ticket present in the manifest with a completed or in-progress state
    - A non-empty release keystore reference in provenance or CANONICAL-BRIEF.md
    """
    manifest = load_manifest(root)
    signing_ticket = ticket_by_id(manifest, ANDROID_SIGNING_TICKET_ID)
    if signing_ticket is not None:
        state = str(signing_ticket.get("resolution_state", "open")).strip()
        status = str(signing_ticket.get("status", "todo")).strip()
        if state == "done" or status == "done":
            return True
    brief = canonical_brief_text(root).lower()
    provenance = bootstrap_provenance(root)
    keystore_ref = provenance.get("keystore_path") or provenance.get("keystore_ref")
    if isinstance(keystore_ref, str) and keystore_ref.strip():
        return True
    if "keystore" in brief or "signing key" in brief or "release key" in brief:
        return True
    return False


def missing_android_completion_ticket_ids(manifest: dict[str, Any], root: Path | None = None) -> list[str]:
    missing: list[str] = []
    required_tickets: list[tuple[str, str]] = [
        (ANDROID_EXPORT_TICKET_ID, ANDROID_EXPORT_LANE),
        (ANDROID_RELEASE_TICKET_ID, ANDROID_RELEASE_LANE),
    ]
    if root is not None and requires_packaged_android_product(root):
        required_tickets.insert(1, (ANDROID_SIGNING_TICKET_ID, ANDROID_SIGNING_LANE))
    for ticket_id, lane in required_tickets:
        ticket = ticket_by_id(manifest, ticket_id)
        if ticket is None or str(ticket.get("lane", "")).strip() != lane:
            missing.append(ticket_id)
    return missing


def other_android_owner_tickets(manifest: dict[str, Any]) -> list[str]:
    owners: list[str] = []
    for ticket in manifest_tickets(manifest):
        ticket_id = str(ticket.get("id", "")).strip()
        if ticket_id in {ANDROID_EXPORT_TICKET_ID, ANDROID_RELEASE_TICKET_ID}:
            continue
        haystack = " ".join(
            [
                str(ticket.get("title", "")),
                str(ticket.get("lane", "")),
                str(ticket.get("summary", "")),
                " ".join(str(item) for item in ticket.get("acceptance", []) if isinstance(item, str)),
            ]
        ).lower()
        if "android export" in haystack or "apk" in haystack or "export template" in haystack:
            owners.append(ticket_id)
    return owners


def has_android_export_preset(root: Path) -> bool:
    export_presets = read_text(root / "export_presets.cfg")
    if not export_presets.strip():
        return False
    if re.search(r'^\s*name\s*=\s*"Android"\s*$', export_presets, re.MULTILINE):
        return True
    if re.search(r'^\s*platform\s*=\s*"Android"\s*$', export_presets, re.MULTILINE):
        return True
    return bool(re.search(r"\bAndroid\b", export_presets))


def has_android_support_surfaces(root: Path) -> bool:
    android_dir = root / "android"
    if not android_dir.exists():
        return False
    for path in android_dir.rglob("*"):
        if not path.is_file():
            continue
        if path.name == ".gitkeep":
            continue
        return True
    return False


def debug_apk_path(root: Path) -> Path | None:
    preferred = root / expected_android_debug_apk_relpath(root)
    if preferred.exists():
        return preferred
    build_android = root / "build" / "android"
    if build_android.exists():
        candidate = next((path for path in sorted(build_android.glob("*.apk")) if path.is_file()), None)
        if candidate is not None:
            return candidate
    return next(
        (
            path
            for path in sorted(root.rglob("*.apk"))
            if path.is_file() and ("build" in path.parts or "android" in path.parts)
        ),
        None,
    )


def repo_claims_completion(manifest: dict[str, Any]) -> bool:
    tickets = manifest_tickets(manifest)
    if not tickets:
        return False
    open_tickets = [
        ticket
        for ticket in tickets
        if str(ticket.get("resolution_state", "open")).strip() in {"open", "reopened"}
        and str(ticket.get("status", "")).strip() != "done"
    ]
    return not open_tickets


def release_lane_started_or_done(manifest: dict[str, Any]) -> bool:
    for ticket_id in (ANDROID_EXPORT_TICKET_ID, ANDROID_RELEASE_TICKET_ID):
        ticket = ticket_by_id(manifest, ticket_id)
        if ticket is None:
            continue
        if str(ticket.get("resolution_state", "open")).strip() == "done":
            return True
        if str(ticket.get("status", "")).strip() not in {"todo", "blocked"}:
            return True
        if str(ticket.get("stage", "")).strip() not in {"planning", ""}:
            return True
    return False

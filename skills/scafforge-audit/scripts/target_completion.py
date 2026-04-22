from __future__ import annotations

import json
import re
from functools import lru_cache
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


VALIDATION_PROOF_MATRIX_PATH = (
    Path(__file__).resolve().parents[3] / "references" / "validation-proof-matrix.json"
)


@lru_cache(maxsize=1)
def load_validation_proof_matrix() -> dict[str, Any]:
    payload = read_json(VALIDATION_PROOF_MATRIX_PATH)
    return payload if isinstance(payload, dict) else {}


def validation_matrix_version() -> int:
    payload = load_validation_proof_matrix()
    value = payload.get("matrix_version")
    return value if isinstance(value, int) else 0


def canonical_family_proof_relpath(family: str) -> str:
    return f".opencode/state/artifacts/proof-{family}.json"


def _string_items(values: Any) -> list[str]:
    return [str(item).strip() for item in values if isinstance(item, str) and str(item).strip()] if isinstance(values, list) else []


def _match_any(haystack: str, needles: list[str]) -> bool:
    lowered = haystack.lower()
    return any(needle.lower() in lowered for needle in needles if needle)


def _repo_signal_map(root: Path) -> dict[str, str]:
    provenance = bootstrap_provenance(root)
    finish_contract = provenance.get("product_finish_contract")
    finish_contract = finish_contract if isinstance(finish_contract, dict) else {}
    return {
        "stack_label": stack_label(root),
        "deliverable_kind": str(provenance.get("deliverable_kind", "")).strip(),
        "visual_finish_target": str(finish_contract.get("visual_finish_target", "")).strip(),
        "finish_acceptance_signals": str(finish_contract.get("finish_acceptance_signals", "")).strip(),
        "brief": canonical_brief_text(root),
    }


def repo_requires_visual_proof(root: Path) -> bool:
    provenance = bootstrap_provenance(root)
    if provenance.get("requires_visual_proof") is True:
        return True
    finish_contract = provenance.get("product_finish_contract")
    if isinstance(finish_contract, dict):
        return finish_contract.get("requires_visual_proof") is True
    return False


def _family_matches(signals: dict[str, str], entry: dict[str, Any]) -> bool:
    match = entry.get("match")
    if not isinstance(match, dict):
        return False
    return any(
        [
            _match_any(signals["stack_label"], _string_items(match.get("stack_label_any"))),
            _match_any(signals["deliverable_kind"], _string_items(match.get("deliverable_any"))),
            _match_any(signals["visual_finish_target"], _string_items(match.get("visual_any"))),
            _match_any(signals["finish_acceptance_signals"], _string_items(match.get("finish_any"))),
            _match_any(signals["brief"], _string_items(match.get("brief_any"))),
        ]
    )


def resolve_validation_profile(root: Path) -> dict[str, Any]:
    matrix = load_validation_proof_matrix()
    families = matrix.get("families")
    if not isinstance(families, dict):
        return {
            "matrix_version": validation_matrix_version(),
            "primary_family": None,
            "overlay_families": [],
            "families": [],
            "supported": False,
        }

    signals = _repo_signal_map(root)
    primary_family: str | None = None
    primary_order = _string_items(matrix.get("primary_family_order"))
    for family in primary_order:
        entry = families.get(family)
        if isinstance(entry, dict) and _family_matches(signals, entry):
            primary_family = family
            break
    if primary_family is None:
        primary_family = next(
            (
                family
                for family, entry in families.items()
                if isinstance(entry, dict) and entry.get("fallback") is True
            ),
            None,
        )

    overlay_families = [
        family
        for family, entry in families.items()
        if isinstance(entry, dict)
        and entry.get("overlay_capable") is True
        and family != primary_family
        and _family_matches(signals, entry)
    ]
    active_families = []
    if primary_family and isinstance(families.get(primary_family), dict):
        active_families.append({"family": primary_family, **families[primary_family]})
    for family in overlay_families:
        entry = families.get(family)
        if isinstance(entry, dict):
            active_families.append({"family": family, **entry})
    return {
        "matrix_version": validation_matrix_version(),
        "primary_family": primary_family,
        "overlay_families": overlay_families,
        "families": active_families,
        "supported": primary_family is not None,
    }


def _proof_activation(entry: dict[str, Any], manifest: dict[str, Any], root: Path) -> bool:
    activation = str(entry.get("activation", "repo_completion")).strip()
    if activation == "always":
        return True
    if activation == "release_lane_or_completion":
        return release_lane_started_or_done(manifest) or repo_claims_completion(manifest)
    return repo_claims_completion(manifest)


def load_family_proof_artifact(root: Path, family: str) -> dict[str, Any] | None:
    payload = read_json(root / canonical_family_proof_relpath(family))
    return payload if isinstance(payload, dict) else None


def _proof_artifact_errors(payload: dict[str, Any], family: str) -> list[str]:
    matrix = load_validation_proof_matrix()
    artifact_schema = matrix.get("artifact_schema")
    artifact_schema = artifact_schema if isinstance(artifact_schema, dict) else {}
    errors: list[str] = []
    required_fields = _string_items(artifact_schema.get("required_top_level_fields"))
    for field in required_fields:
        if field not in payload:
            errors.append(f"missing top-level field `{field}`")
    if payload.get("family") != family:
        errors.append(f"family field should be `{family}`")
    if "passed" in payload and not isinstance(payload.get("passed"), bool):
        errors.append("`passed` must be a boolean")
    if "artifact_path" in payload and payload.get("artifact_path") is not None and not isinstance(payload.get("artifact_path"), str):
        errors.append("`artifact_path` must be a string or null")
    if "log_excerpt" in payload and not isinstance(payload.get("log_excerpt"), list):
        errors.append("`log_excerpt` must be an array when present")
    steps = payload.get("steps")
    if steps is not None and not isinstance(steps, list):
        errors.append("`steps` must be an array when present")
    if isinstance(steps, list):
        step_schema = artifact_schema.get("step_result_fields")
        step_schema = step_schema if isinstance(step_schema, dict) else {}
        required_step_fields = _string_items(step_schema.get("required"))
        for index, item in enumerate(steps):
            if not isinstance(item, dict):
                errors.append(f"step {index} must be an object")
                continue
            for field in required_step_fields:
                if field not in item:
                    errors.append(f"step {index} missing field `{field}`")
            status = str(item.get("status", "")).strip()
            if status and status not in {"passed", "failed", "degraded", "not_applicable"}:
                errors.append(f"step {index} has unsupported status `{status}`")
    return errors


def _infer_artifact_status(payload: dict[str, Any]) -> str:
    if isinstance(payload.get("not_applicable_reason"), str) and payload.get("not_applicable_reason", "").strip():
        return "not_applicable"
    if payload.get("passed") is False:
        return "failed"
    if isinstance(payload.get("degraded_reason"), str) and payload.get("degraded_reason", "").strip():
        return "degraded"
    return "passed"


def _condition_applies(condition: str | None, root: Path) -> bool:
    if not condition:
        return True
    if condition == "requires_visual_proof":
        return repo_requires_visual_proof(root)
    if condition == "requires_packaged_android_product":
        return requires_packaged_android_product(root)
    return False


def completion_validation_summary(root: Path, manifest: dict[str, Any] | None = None) -> dict[str, Any]:
    manifest_payload = manifest if isinstance(manifest, dict) else load_manifest(root)
    profile = resolve_validation_profile(root)
    completion_claim = repo_claims_completion(manifest_payload)
    summaries: list[dict[str, Any]] = []
    for family_entry in profile.get("families", []):
        if not isinstance(family_entry, dict):
            continue
        family = str(family_entry.get("family", "")).strip()
        if not family:
            continue
        artifact_rel = canonical_family_proof_relpath(family)
        artifact_payload = load_family_proof_artifact(root, family)
        activation_required = _proof_activation(family_entry, manifest_payload, root)
        step_summaries: list[dict[str, Any]] = []
        artifact_errors = _proof_artifact_errors(artifact_payload, family) if artifact_payload else []
        top_level_status = _infer_artifact_status(artifact_payload) if artifact_payload and not artifact_errors else "missing"
        steps_by_id = {
            str(item.get("step_id", "")).strip(): item
            for item in (artifact_payload.get("steps", []) if isinstance(artifact_payload, dict) else [])
            if isinstance(item, dict) and str(item.get("step_id", "")).strip()
        }
        blocking = False
        blocking_reasons: list[str] = []
        for step in family_entry.get("proof_tiers", []):
            if not isinstance(step, dict):
                continue
            step_id = str(step.get("id", "")).strip()
            requirement = str(step.get("requirement", "required")).strip() or "required"
            validator_status = str(step.get("validator_status", "implemented")).strip() or "implemented"
            condition = str(step.get("condition", "")).strip() or None
            active = requirement == "required" or (
                requirement == "conditional" and _condition_applies(condition, root)
            )
            if validator_status == "not_required" or not active:
                status = "not_required"
            elif validator_status == "no_validator_yet":
                status = "validator_gap"
            elif artifact_errors:
                status = "invalid"
            elif artifact_payload is None:
                status = "missing"
            else:
                record = steps_by_id.get(step_id)
                if isinstance(record, dict):
                    status = str(record.get("status", "")).strip() or "missing"
                else:
                    status = top_level_status
            if active and status in {"missing", "failed", "invalid", "validator_gap"}:
                blocking = True
                blocking_reasons.append(f"{step_id}:{status}")
            if active and status == "degraded" and not _string_items(family_entry.get("allowed_degradation_rules")):
                blocking = True
                blocking_reasons.append(f"{step_id}:degraded")
            step_summaries.append(
                {
                    "id": step_id,
                    "label": str(step.get("label", step_id)).strip() or step_id,
                    "requirement": requirement,
                    "validator_status": validator_status,
                    "status": status,
                    "artifact_kind": str(step.get("artifact_kind", "")).strip(),
                    "tool_bundles": _string_items(step.get("tool_bundles")),
                }
            )
        if artifact_errors:
            blocking = activation_required
            blocking_reasons.extend(artifact_errors)
            family_status = "invalid"
        elif artifact_payload is None:
            family_status = "missing" if activation_required else "inactive"
        else:
            family_status = top_level_status
        summaries.append(
            {
                "family": family,
                "title": str(family_entry.get("title", family)).strip() or family,
                "activation_required": activation_required,
                "artifact_path": artifact_rel,
                "artifact_exists": artifact_payload is not None,
                "status": family_status,
                "blocking": blocking if activation_required else False,
                "blocking_reasons": blocking_reasons,
                "required_artifact_kinds": _string_items(family_entry.get("required_artifact_kinds")),
                "allowed_degradation_rules": _string_items(family_entry.get("allowed_degradation_rules")),
                "steps": step_summaries,
                "schema_errors": artifact_errors,
                "top_level_summary": str(artifact_payload.get("summary", "")).strip() if artifact_payload else "",
                "proof_tier": str(artifact_payload.get("proof_tier", "")).strip() if artifact_payload else "",
            }
        )
    return {
        "matrix_version": profile.get("matrix_version", 0),
        "primary_family": profile.get("primary_family"),
        "overlay_families": profile.get("overlay_families", []),
        "supported": profile.get("supported", False),
        "completion_claim_active": completion_claim,
        "families": summaries,
    }

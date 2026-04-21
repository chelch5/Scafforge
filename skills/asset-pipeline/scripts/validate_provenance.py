#!/usr/bin/env python3
"""Validate canonical asset provenance, compliance, and QA surfaces."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any


SOURCE_ROUTES = {
    "source-open-curated",
    "source-mixed-license",
    "procedural-2d",
    "procedural-layout",
    "procedural-world",
    "local-ai-2d",
    "local-ai-audio",
    "reconstruct-3d",
    "dcc-assembly",
}
SOURCE_TYPES = {"sourced", "procedural", "ai-generated", "reconstructed", "dcc-assembled"}
QA_STATUSES = {"pending", "passed", "needs-review", "blocked", "failed"}
DEFAULT_DENIED_LICENSES = {"CC-BY-NC", "CC-BY-ND", "GPL", "LGPL", "Proprietary", "Unknown", "Unlicensed"}
CANONICAL_SUPPORT_DIRS = {"briefs", "previews", "workflows", "qa", "licenses", "workfiles"}
CANONICAL_SUPPORT_FILES = {
    "requirements.json",
    "pipeline.json",
    "manifest.json",
    "ATTRIBUTION.md",
    "PROVENANCE.md",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate asset manifest, provenance, compliance, and QA surfaces."
    )
    parser.add_argument("project_root", nargs="?", default=".", help="Generated repo root.")
    return parser.parse_args()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def json_digest(payload: object) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def require_keys(payload: dict[str, Any], keys: tuple[str, ...], *, label: str, errors: list[str]) -> None:
    for key in keys:
        if key not in payload:
            errors.append(f"{label} is missing required field `{key}`.")


def load_required_json(path: Path, *, label: str, errors: list[str]) -> dict[str, Any] | None:
    if not path.exists():
        errors.append(f"Missing required JSON surface: {path.as_posix()}")
        return None
    try:
        payload = read_json(path)
    except json.JSONDecodeError as exc:
        errors.append(f"{path.as_posix()} is not valid JSON: {exc}")
        return None
    if not isinstance(payload, dict):
        errors.append(f"{path.as_posix()} must contain a JSON object.")
        return None
    return payload


def validate_requirements(payload: dict[str, Any], *, errors: list[str]) -> None:
    require_keys(payload, ("version", "project_asset_profile", "categories"), label="assets/requirements.json", errors=errors)
    categories = payload.get("categories")
    if not isinstance(categories, list):
        errors.append("assets/requirements.json field `categories` must be an array.")
        return
    for index, category in enumerate(categories):
        label = f"assets/requirements.json categories[{index}]"
        if not isinstance(category, dict):
            errors.append(f"{label} must be an object.")
            continue
        require_keys(
            category,
            (
                "id",
                "asset_class",
                "required_outputs",
                "quality_bar",
                "license_policy",
                "preferred_source_routes",
                "fallback_routes",
            ),
            label=label,
            errors=errors,
        )


def validate_pipeline(payload: dict[str, Any], *, errors: list[str]) -> None:
    require_keys(
        payload,
        (
            "version",
            "capability_taxonomy",
            "routes",
            "canonical_ownership",
            "fallback_ladders",
            "compliance_policy",
            "qa_rules",
            "provenance_requirements",
        ),
        label="assets/pipeline.json",
        errors=errors,
    )
    taxonomy = payload.get("capability_taxonomy")
    if isinstance(taxonomy, dict):
        source_routes = taxonomy.get("source_routes")
        pipeline_stages = taxonomy.get("pipeline_stages")
        if not isinstance(source_routes, list) or set(source_routes) != SOURCE_ROUTES:
            errors.append("assets/pipeline.json capability_taxonomy.source_routes must match the canonical asset capability taxonomy.")
        if not isinstance(pipeline_stages, list) or set(pipeline_stages) != {"optimize-import", "provenance-compliance"}:
            errors.append("assets/pipeline.json capability_taxonomy.pipeline_stages must contain optimize-import and provenance-compliance.")
    routes = payload.get("routes")
    if not isinstance(routes, dict):
        errors.append("assets/pipeline.json field `routes` must be an object.")
        return
    for category, choice in routes.items():
        label = f"assets/pipeline.json routes.{category}"
        if not isinstance(choice, dict):
            errors.append(f"{label} must be an object.")
            continue
        primary = choice.get("primary")
        fallback_routes = choice.get("fallback_routes")
        if not isinstance(primary, str) or primary not in SOURCE_ROUTES:
            errors.append(f"{label}.primary must be one of the canonical source routes.")
        if not isinstance(fallback_routes, list):
            errors.append(f"{label}.fallback_routes must be an array.")


def validate_report(
    payload: dict[str, Any],
    *,
    label: str,
    report_kind: str,
    list_field: str,
    errors: list[str],
) -> None:
    require_keys(payload, ("version", "generated_at", "report_kind", "status", list_field), label=label, errors=errors)
    if payload.get("report_kind") != report_kind:
        errors.append(f"{label} must declare report_kind={report_kind!r}.")
    entries = payload.get(list_field)
    if not isinstance(entries, list):
        errors.append(f"{label} field `{list_field}` must be an array.")


def validate_lock(
    payload: dict[str, Any],
    *,
    requirements: dict[str, Any],
    pipeline: dict[str, Any],
    manifest: dict[str, Any],
    errors: list[str],
) -> None:
    require_keys(
        payload,
        (
            "version",
            "process_contract_revision",
            "requirements_digest",
            "pipeline_digest",
            "manifest_digest",
        ),
        label=".opencode/meta/asset-provenance-lock.json",
        errors=errors,
    )
    if payload.get("requirements_digest") != json_digest(requirements):
        errors.append(".opencode/meta/asset-provenance-lock.json requirements_digest does not match assets/requirements.json.")
    if payload.get("pipeline_digest") != json_digest(pipeline):
        errors.append(".opencode/meta/asset-provenance-lock.json pipeline_digest does not match assets/pipeline.json.")
    if payload.get("manifest_digest") != json_digest(manifest):
        errors.append(".opencode/meta/asset-provenance-lock.json manifest_digest does not match assets/manifest.json.")


def tracked_asset_files(assets_dir: Path) -> set[str]:
    actual: set[str] = set()
    for root, dirs, files in os.walk(assets_dir):
        relative_root = Path(root).relative_to(assets_dir)
        if relative_root.parts and relative_root.parts[0] in CANONICAL_SUPPORT_DIRS:
            dirs[:] = []
            continue
        for filename in files:
            if filename.startswith(".") or filename in CANONICAL_SUPPORT_FILES:
                continue
            rel_path = relative_root / filename
            if rel_path.name == "README.md":
                continue
            actual.add(f"assets/{rel_path.as_posix()}")
    return actual


def collect_report_paths(payload: dict[str, Any], field: str) -> set[str]:
    entries = payload.get(field)
    if not isinstance(entries, list):
        return set()
    result: set[str] = set()
    for item in entries:
        if isinstance(item, str):
            result.add(item)
        elif isinstance(item, dict):
            path = item.get("path")
            if isinstance(path, str):
                result.add(path)
    return result


def validate_manifest_entries(
    *,
    project_root: Path,
    manifest: dict[str, Any],
    pipeline: dict[str, Any],
    import_report: dict[str, Any],
    license_report: dict[str, Any],
    provenance_text: str,
    attribution_text: str,
    errors: list[str],
    warnings: list[str],
) -> None:
    require_keys(manifest, ("version", "generated_at", "assets"), label="assets/manifest.json", errors=errors)
    assets = manifest.get("assets")
    if not isinstance(assets, list):
        errors.append("assets/manifest.json field `assets` must be an array.")
        return

    actual_asset_files = tracked_asset_files(project_root / "assets")
    manifest_paths: set[str] = set()
    checked_assets = collect_report_paths(import_report, "checked_assets")
    reviewed_assets = collect_report_paths(license_report, "reviewed_assets")
    allowed_licenses = set(pipeline.get("compliance_policy", {}).get("allowed_licenses", []))
    denied_licenses = set(license_report.get("denied_licenses", [])) | DEFAULT_DENIED_LICENSES

    for index, entry in enumerate(assets):
        label = f"assets/manifest.json assets[{index}]"
        if not isinstance(entry, dict):
            errors.append(f"{label} must be an object.")
            continue
        require_keys(
            entry,
            (
                "id",
                "path",
                "category",
                "source_route",
                "source_type",
                "qa_status",
                "license",
                "author_or_origin",
                "workflow_ref",
                "import_report_ref",
                "license_report_ref",
                "attribution_required",
            ),
            label=label,
            errors=errors,
        )
        asset_path = entry.get("path")
        if not isinstance(asset_path, str) or not asset_path.strip():
            continue
        asset_path = asset_path.strip()
        manifest_paths.add(asset_path)
        asset_file = project_root / asset_path.replace("/", os.sep)
        if not asset_file.exists():
            errors.append(f"{label} path does not exist on disk: {asset_path}")
        source_route = entry.get("source_route")
        if not isinstance(source_route, str) or source_route not in SOURCE_ROUTES:
            errors.append(f"{label} source_route must use the canonical capability taxonomy.")
        source_type = entry.get("source_type")
        if not isinstance(source_type, str) or source_type not in SOURCE_TYPES:
            errors.append(f"{label} source_type must be one of {sorted(SOURCE_TYPES)}.")
        qa_status = entry.get("qa_status")
        if not isinstance(qa_status, str) or qa_status not in QA_STATUSES:
            errors.append(f"{label} qa_status must be one of {sorted(QA_STATUSES)}.")
        license_name = entry.get("license")
        if not isinstance(license_name, str) or not license_name.strip():
            errors.append(f"{label} license must be a non-empty string.")
        else:
            if license_name in denied_licenses:
                errors.append(f"{label} uses denied license `{license_name}`.")
            if allowed_licenses and license_name not in allowed_licenses:
                errors.append(f"{label} uses unsupported license `{license_name}` outside the allowlist.")
        if source_route == "source-mixed-license" and entry.get("attribution_required") is not True:
            errors.append(f"{label} must set attribution_required=true for source-mixed-license assets.")
        if source_type == "sourced" and not isinstance(entry.get("source_url"), str):
            errors.append(f"{label} must record source_url for sourced assets.")
        if source_type == "ai-generated":
            if not isinstance(entry.get("tool_chain"), list) or not entry.get("tool_chain"):
                errors.append(f"{label} must record tool_chain for ai-generated assets.")
            if not isinstance(entry.get("model_or_checkpoint"), str) or not entry.get("model_or_checkpoint"):
                errors.append(f"{label} must record model_or_checkpoint for ai-generated assets.")
            if not isinstance(entry.get("prompt_or_recipe"), str) or not entry.get("prompt_or_recipe"):
                errors.append(f"{label} must record prompt_or_recipe for ai-generated assets.")
        if source_type in {"procedural", "reconstructed", "dcc-assembled"}:
            if not isinstance(entry.get("tool_chain"), list) or not entry.get("tool_chain"):
                errors.append(f"{label} must record tool_chain for {source_type} assets.")
        for ref_field in ("workflow_ref", "import_report_ref", "license_report_ref", "preview_path", "workfile_path"):
            ref_value = entry.get(ref_field)
            if ref_value is None:
                continue
            if not isinstance(ref_value, str) or not ref_value.strip():
                errors.append(f"{label} field `{ref_field}` must be a non-empty string when present.")
                continue
            ref_path = project_root / ref_value.replace("/", os.sep)
            if not ref_path.exists():
                errors.append(f"{label} references missing file in `{ref_field}`: {ref_value}")
        if asset_path not in provenance_text:
            errors.append(f"assets/PROVENANCE.md is missing ledger coverage for `{asset_path}`.")
        if entry.get("attribution_required") is True and asset_path not in attribution_text:
            errors.append(f"assets/ATTRIBUTION.md is missing required attribution coverage for `{asset_path}`.")
        if qa_status == "passed":
            if asset_path not in checked_assets:
                errors.append(f"assets/qa/import-report.json does not include passed asset `{asset_path}`.")
            if asset_path not in reviewed_assets:
                errors.append(f"assets/qa/license-report.json does not include passed asset `{asset_path}`.")

    missing_from_manifest = actual_asset_files - manifest_paths
    if missing_from_manifest:
        errors.append(
            "Manifest missing committed asset files: " + ", ".join(sorted(missing_from_manifest))
        )
    orphaned_manifest_paths = manifest_paths - actual_asset_files
    for orphan in sorted(orphaned_manifest_paths):
        warnings.append(f"Manifest references asset path not present in tracked asset set: {orphan}")


def main() -> int:
    args = parse_args()
    project_root = Path(args.project_root).resolve()
    assets_dir = project_root / "assets"
    if not assets_dir.exists():
        print("No assets/ directory found.")
        return 0

    errors: list[str] = []
    warnings: list[str] = []

    requirements = load_required_json(project_root / "assets" / "requirements.json", label="assets/requirements.json", errors=errors)
    pipeline = load_required_json(project_root / "assets" / "pipeline.json", label="assets/pipeline.json", errors=errors)
    manifest = load_required_json(project_root / "assets" / "manifest.json", label="assets/manifest.json", errors=errors)
    import_report = load_required_json(project_root / "assets" / "qa" / "import-report.json", label="assets/qa/import-report.json", errors=errors)
    license_report = load_required_json(project_root / "assets" / "qa" / "license-report.json", label="assets/qa/license-report.json", errors=errors)
    lock = load_required_json(project_root / ".opencode" / "meta" / "asset-provenance-lock.json", label=".opencode/meta/asset-provenance-lock.json", errors=errors)

    provenance_path = project_root / "assets" / "PROVENANCE.md"
    attribution_path = project_root / "assets" / "ATTRIBUTION.md"
    if not provenance_path.exists():
        errors.append("Missing required surface: assets/PROVENANCE.md")
        provenance_text = ""
    else:
        provenance_text = provenance_path.read_text(encoding="utf-8")
    if not attribution_path.exists():
        errors.append("Missing required surface: assets/ATTRIBUTION.md")
        attribution_text = ""
    else:
        attribution_text = attribution_path.read_text(encoding="utf-8")

    if requirements is not None:
        validate_requirements(requirements, errors=errors)
    if pipeline is not None:
        validate_pipeline(pipeline, errors=errors)
    if import_report is not None:
        validate_report(import_report, label="assets/qa/import-report.json", report_kind="import-optimization", list_field="checked_assets", errors=errors)
    if license_report is not None:
        validate_report(license_report, label="assets/qa/license-report.json", report_kind="license-compliance", list_field="reviewed_assets", errors=errors)
    if lock is not None and requirements is not None and pipeline is not None and manifest is not None:
        validate_lock(lock, requirements=requirements, pipeline=pipeline, manifest=manifest, errors=errors)
    if manifest is not None and pipeline is not None and import_report is not None and license_report is not None:
        validate_manifest_entries(
            project_root=project_root,
            manifest=manifest,
            pipeline=pipeline,
            import_report=import_report,
            license_report=license_report,
            provenance_text=provenance_text,
            attribution_text=attribution_text,
            errors=errors,
            warnings=warnings,
        )

    if warnings:
        print(f"WARN: {len(warnings)} issue(s) need attention:")
        for warning in warnings:
            print(f"  - {warning}")

    if errors:
        print(f"FAIL: {len(errors)} asset contract issue(s) found:")
        for error in errors:
            print(f"  - {error}")
        return 1

    tracked_assets = tracked_asset_files(assets_dir)
    print(f"OK: asset provenance contract valid for {len(tracked_assets)} tracked asset file(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

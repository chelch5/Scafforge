from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


ANDROID_EXPORT_PRESETS_RELATIVE_PATH = Path("export_presets.cfg")
ANDROID_MANAGED_SUPPORT_RELATIVE_PATH = Path("android/scafforge-managed.json")
ANDROID_MANAGED_SURFACE_RELATIVE_PATHS = (
    ANDROID_EXPORT_PRESETS_RELATIVE_PATH,
    ANDROID_MANAGED_SUPPORT_RELATIVE_PATH,
)
DEFAULT_ANDROID_PACKAGE_PREFIX = "com.example"


def slugify(value: str) -> str:
    lowered = value.lower()
    lowered = re.sub(r"[^a-z0-9]+", "-", lowered)
    lowered = re.sub(r"-{2,}", "-", lowered).strip("-")
    return lowered or "project"


def renders_godot_android_assets(stack_label: str) -> bool:
    lowered = stack_label.lower()
    return "godot" in lowered and "android" in lowered


def normalize_android_package_name(project_slug: str, explicit_package_name: str | None = None) -> str:
    if explicit_package_name:
        raw_parts = [part for part in explicit_package_name.strip().split(".") if part.strip()]
        normalized_parts = [_normalize_package_segment(part) for part in raw_parts]
        normalized_parts = [part for part in normalized_parts if part]
        if len(normalized_parts) >= 2:
            return ".".join(normalized_parts)
        if len(normalized_parts) == 1:
            return f"{DEFAULT_ANDROID_PACKAGE_PREFIX}.{normalized_parts[0]}"
    normalized_slug = _normalize_package_segment(project_slug)
    return f"{DEFAULT_ANDROID_PACKAGE_PREFIX}.{normalized_slug}"


def android_surface_values(project_slug: str, explicit_package_name: str | None = None) -> dict[str, str]:
    normalized_slug = slugify(project_slug)
    package_name = normalize_android_package_name(normalized_slug, explicit_package_name)
    return {
        "project_slug": normalized_slug,
        "package_name": package_name,
    }


def load_android_surface_values(repo_root: Path) -> dict[str, str]:
    provenance = _read_json(repo_root / ".opencode" / "meta" / "bootstrap-provenance.json")
    project_slug = repo_root.name
    package_name: str | None = None
    stack_label = ""
    if isinstance(provenance, dict):
        slug_value = provenance.get("project_slug") or provenance.get("project_name")
        if isinstance(slug_value, str) and slug_value.strip():
            project_slug = slug_value.strip()
        explicit_package_name = provenance.get("package_name")
        if isinstance(explicit_package_name, str) and explicit_package_name.strip():
            package_name = explicit_package_name.strip()
        stack = provenance.get("stack_label")
        if isinstance(stack, str) and stack.strip():
            stack_label = stack.strip()
    values = android_surface_values(project_slug, package_name)
    values["stack_label"] = stack_label
    return values


def repo_declares_godot_android(repo_root: Path) -> bool:
    values = load_android_surface_values(repo_root)
    stack_label = values.get("stack_label", "")
    if renders_godot_android_assets(stack_label):
        return True
    provenance = _read_json(repo_root / ".opencode" / "meta" / "bootstrap-provenance.json")
    if isinstance(provenance, dict):
        target_platform = str(provenance.get("target_platform", "")).lower()
        if "godot" in stack_label.lower() and "android" in target_platform:
            return True
        if "godot" in target_platform and "android" in target_platform:
            return True
    brief_text = _read_text(repo_root / "docs" / "spec" / "CANONICAL-BRIEF.md").lower()
    has_godot = (repo_root / "project.godot").exists() or "godot" in brief_text or "godot" in stack_label.lower()
    has_android = (
        "android" in brief_text
        or "android" in stack_label.lower()
        or (repo_root / "export_presets.cfg").exists()
        or (repo_root / "android").exists()
    )
    return has_godot and has_android


def has_managed_android_support_surface(repo_root: Path) -> bool:
    return (repo_root / ANDROID_MANAGED_SUPPORT_RELATIVE_PATH).exists()


def _normalize_package_segment(value: str) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9]+", "_", value).strip("_").lower()
    if not normalized:
        normalized = "app"
    if normalized[0].isdigit():
        normalized = f"app_{normalized}"
    return normalized


def _read_json(path: Path) -> Any:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""
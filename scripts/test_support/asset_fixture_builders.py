from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any, Callable

from test_support.repo_seeders import read_json, write_json
from test_support.scafforge_harness import ROOT


FIXTURE_INDEX = ROOT / "tests" / "fixtures" / "assets" / "index.json"
CONTRACT_PATH = ".opencode/meta/asset-fixture.json"
SOURCE_ROUTES = [
    "source-open-curated",
    "source-mixed-license",
    "procedural-2d",
    "procedural-layout",
    "procedural-world",
    "local-ai-2d",
    "local-ai-audio",
    "reconstruct-3d",
    "dcc-assembly",
]


def fixture_index_by_slug() -> dict[str, dict[str, Any]]:
    payload = read_json(FIXTURE_INDEX)
    families = payload.get("families") if isinstance(payload, dict) else None
    if not isinstance(families, list):
        raise RuntimeError("Asset fixture index must define a families list.")
    indexed: dict[str, dict[str, Any]] = {}
    for item in families:
        if isinstance(item, dict) and isinstance(item.get("slug"), str):
            indexed[item["slug"]] = item
    return indexed


def write_fixture_contract(dest: Path, *, slug: str, family: dict[str, Any], extra: dict[str, Any]) -> dict[str, Any]:
    payload = {
        "slug": slug,
        "title": family.get("title"),
        "flow": family.get("flow"),
        "invariant_focus": family.get("invariant_focus", []),
        "expected_coverage": family.get("expected_coverage", []),
        "notes": family.get("notes"),
        **extra,
    }
    write_json(dest / CONTRACT_PATH, payload)
    return payload


def json_digest(payload: object) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    import hashlib

    return hashlib.sha256(encoded).hexdigest()


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def build_mixed_asset_truth(dest: Path, family: dict[str, Any]) -> dict[str, Any]:
    if dest.exists():
        shutil.rmtree(dest)

    for relative in (
        "assets/sprites",
        "assets/audio",
        "assets/themes",
        "assets/models",
        "assets/previews",
        "assets/workflows",
        "assets/qa",
        ".opencode/meta",
    ):
        (dest / relative).mkdir(parents=True, exist_ok=True)

    write_text(dest / "assets" / "sprites" / "kenney-ui.png", "png-placeholder\n")
    write_text(dest / "assets" / "audio" / "menu-click.ogg", "ogg-placeholder\n")
    write_text(dest / "assets" / "themes" / "hit-flash.tres", "[gd_resource type=\"ShaderMaterial\"]\n")
    write_text(dest / "assets" / "models" / "arena-crate.glb", "glb-placeholder\n")
    write_text(dest / "assets" / "previews" / "arena-crate.png", "preview\n")
    write_text(dest / "assets" / "previews" / "hit-flash.png", "preview\n")

    workflows = {
        "kenney-ui.json": {"route": "source-open-curated", "kind": "ingest-record"},
        "menu-click.json": {"route": "source-mixed-license", "kind": "ingest-record"},
        "hit-flash.json": {"route": "procedural-2d", "kind": "workflow-record"},
        "arena-crate.json": {"route": "dcc-assembly", "kind": "workflow-record"},
    }
    for name, payload in workflows.items():
        write_json(dest / "assets" / "workflows" / name, payload)

    requirements = {
        "version": 1,
        "project_asset_profile": {
            "stack_label": "godot-2d-android-game",
            "deliverable_kind": "android apk with truthful mixed asset coverage",
            "placeholder_policy": "no_placeholders",
            "art_style": "stylized-2d",
            "target_platform": "android",
        },
        "categories": [
            {
                "id": "ui",
                "asset_class": "ui",
                "required_outputs": ["ui-artifact", "attribution-proof", "import-proof"],
                "quality_bar": "readable UI and iconography with clean import.",
                "license_policy": "allowlist-only",
                "preferred_source_routes": ["source-open-curated"],
                "fallback_routes": ["source-mixed-license", "procedural-2d"],
            },
            {
                "id": "audio",
                "asset_class": "audio",
                "required_outputs": ["audio-artifact", "license-proof", "import-proof"],
                "quality_bar": "clean import with explicit attribution where required.",
                "license_policy": "allowlist-plus-attribution-review",
                "preferred_source_routes": ["source-mixed-license"],
                "fallback_routes": ["source-open-curated", "procedural-2d"],
            },
            {
                "id": "vfx",
                "asset_class": "vfx",
                "required_outputs": ["vfx-artifact", "preview-artifact", "import-proof"],
                "quality_bar": "clear telegraphing and clean import.",
                "license_policy": "repo-authored-or-cleared-inputs-only",
                "preferred_source_routes": ["procedural-2d"],
                "fallback_routes": ["source-open-curated"],
            },
            {
                "id": "props",
                "asset_class": "3d",
                "required_outputs": ["prop-artifact", "preview-artifact", "import-proof"],
                "quality_bar": "mobile-safe mesh budgets and clean import.",
                "license_policy": "repo-authored-or-cleared-inputs-only",
                "preferred_source_routes": ["dcc-assembly"],
                "fallback_routes": ["source-open-curated", "reconstruct-3d"],
            },
        ],
    }
    pipeline = {
        "version": 2,
        "capability_taxonomy": {
            "source_routes": SOURCE_ROUTES,
            "pipeline_stages": ["optimize-import", "provenance-compliance"],
        },
        "routes": {
            "ui": {"primary": "source-open-curated", "fallback_routes": ["source-mixed-license", "procedural-2d"]},
            "audio": {"primary": "source-mixed-license", "fallback_routes": ["source-open-curated", "procedural-2d"]},
            "vfx": {"primary": "procedural-2d", "fallback_routes": ["source-open-curated"]},
            "props": {"primary": "dcc-assembly", "fallback_routes": ["source-open-curated", "reconstruct-3d"]},
        },
        "canonical_ownership": {
            "assets/requirements.json": {"authority": "authoritative"},
            "assets/pipeline.json": {"authority": "authoritative"},
            "assets/manifest.json": {"authority": "authoritative"},
            ".opencode/meta/asset-provenance-lock.json": {"authority": "authoritative"},
            "assets/ATTRIBUTION.md": {"authority": "derived"},
            "assets/PROVENANCE.md": {"authority": "derived"},
            "assets/qa/import-report.json": {"authority": "derived"},
            "assets/qa/license-report.json": {"authority": "derived"},
        },
        "fallback_ladders": {
            "icons": {"preferred_routes": ["procedural-2d", "source-open-curated"]},
            "sfx": {"preferred_routes": ["procedural-2d", "source-open-curated", "source-mixed-license"]},
            "props": {"preferred_routes": ["source-open-curated", "dcc-assembly", "reconstruct-3d"]},
        },
        "compliance_policy": {
            "allowed_licenses": ["CC0", "CC-BY", "MIT", "OFL", "Apache-2.0"],
            "denied_licenses": ["CC-BY-NC", "CC-BY-ND", "GPL", "LGPL", "Proprietary", "Unknown", "Unlicensed"],
        },
        "qa_rules": {
            "import_report_path": "assets/qa/import-report.json",
            "license_report_path": "assets/qa/license-report.json",
        },
        "provenance_requirements": {
            "authoritative_manifest": "assets/manifest.json",
            "workflow_dir": "assets/workflows",
            "qa": {
                "import_report": "assets/qa/import-report.json",
                "license_report": "assets/qa/license-report.json",
            },
        },
    }
    manifest = {
        "version": 1,
        "generated_at": "2026-04-21T20:00:00Z",
        "assets": [
            {
                "id": "ui-kenney-kit",
                "path": "assets/sprites/kenney-ui.png",
                "category": "ui",
                "source_route": "source-open-curated",
                "source_type": "sourced",
                "qa_status": "passed",
                "license": "CC0",
                "author_or_origin": "Kenney",
                "workflow_ref": "assets/workflows/kenney-ui.json",
                "import_report_ref": "assets/qa/import-report.json",
                "license_report_ref": "assets/qa/license-report.json",
                "attribution_required": False,
                "source_url": "https://kenney.nl/assets",
            },
            {
                "id": "menu-click-sfx",
                "path": "assets/audio/menu-click.ogg",
                "category": "audio",
                "source_route": "source-mixed-license",
                "source_type": "sourced",
                "qa_status": "passed",
                "license": "CC-BY",
                "author_or_origin": "OpenGameArt contributor",
                "workflow_ref": "assets/workflows/menu-click.json",
                "import_report_ref": "assets/qa/import-report.json",
                "license_report_ref": "assets/qa/license-report.json",
                "attribution_required": True,
                "source_url": "https://opengameart.org/",
            },
            {
                "id": "hit-flash-vfx",
                "path": "assets/themes/hit-flash.tres",
                "category": "vfx",
                "source_route": "procedural-2d",
                "source_type": "procedural",
                "qa_status": "passed",
                "license": "MIT",
                "author_or_origin": "repo-authored",
                "workflow_ref": "assets/workflows/hit-flash.json",
                "import_report_ref": "assets/qa/import-report.json",
                "license_report_ref": "assets/qa/license-report.json",
                "attribution_required": False,
                "tool_chain": ["godot-shader", "particle-authoring"],
                "prompt_or_recipe": "Shader-based flash with additive blend and bounded mobile-safe parameters.",
                "preview_path": "assets/previews/hit-flash.png",
            },
            {
                "id": "arena-crate-prop",
                "path": "assets/models/arena-crate.glb",
                "category": "props",
                "source_route": "dcc-assembly",
                "source_type": "dcc-assembled",
                "qa_status": "passed",
                "license": "MIT",
                "author_or_origin": "repo-authored",
                "workflow_ref": "assets/workflows/arena-crate.json",
                "import_report_ref": "assets/qa/import-report.json",
                "license_report_ref": "assets/qa/license-report.json",
                "attribution_required": False,
                "tool_chain": ["blender_agent", "glb-export"],
                "prompt_or_recipe": "Low-poly arena crate assembled in Blender with clean UVs and mobile-safe texture sizing.",
                "preview_path": "assets/previews/arena-crate.png",
            },
        ],
    }
    import_report = {
        "version": 1,
        "generated_at": "2026-04-21T20:00:00Z",
        "report_kind": "import-optimization",
        "status": "passed",
        "checked_assets": [entry["path"] for entry in manifest["assets"]],
    }
    license_report = {
        "version": 1,
        "generated_at": "2026-04-21T20:00:00Z",
        "report_kind": "license-compliance",
        "status": "passed",
        "allowed_licenses": ["CC0", "CC-BY", "MIT", "OFL", "Apache-2.0"],
        "denied_licenses": ["CC-BY-NC", "CC-BY-ND", "GPL", "LGPL", "Proprietary", "Unknown", "Unlicensed"],
        "reviewed_assets": [entry["path"] for entry in manifest["assets"]],
    }

    write_json(dest / "assets" / "requirements.json", requirements)
    write_json(dest / "assets" / "pipeline.json", pipeline)
    write_json(dest / "assets" / "manifest.json", manifest)
    write_json(dest / "assets" / "qa" / "import-report.json", import_report)
    write_json(dest / "assets" / "qa" / "license-report.json", license_report)

    write_text(
        dest / "assets" / "PROVENANCE.md",
        "\n".join(
            [
                "# Asset Provenance",
                "",
                "| asset_path | source_or_workflow | license | author | acquired_or_generated_on | notes |",
                "| --- | --- | --- | --- | --- | --- |",
                "| assets/sprites/kenney-ui.png | https://kenney.nl/assets | CC0 | Kenney | 2026-04-21 | Curated UI source. |",
                "| assets/audio/menu-click.ogg | https://opengameart.org/ | CC-BY | OpenGameArt contributor | 2026-04-21 | Attribution required. |",
                "| assets/themes/hit-flash.tres | assets/workflows/hit-flash.json | MIT | repo-authored | 2026-04-21 | Procedural VFX. |",
                "| assets/models/arena-crate.glb | assets/workflows/arena-crate.json | MIT | repo-authored | 2026-04-21 | DCC-assembled prop. |",
                "",
            ]
        ),
    )
    write_text(
        dest / "assets" / "ATTRIBUTION.md",
        "\n".join(
            [
                "# Asset Attribution",
                "",
                "- assets/audio/menu-click.ogg — OpenGameArt contributor — CC-BY — https://opengameart.org/",
                "",
            ]
        ),
    )

    lock = {
        "version": 1,
        "process_contract_revision": "asset-pipeline-2026-04-21",
        "requirements_digest": json_digest(requirements),
        "pipeline_digest": json_digest(pipeline),
        "manifest_digest": json_digest(manifest),
    }
    write_json(dest / ".opencode" / "meta" / "asset-provenance-lock.json", lock)

    return write_fixture_contract(
        dest,
        slug="mixed-asset-truth",
        family=family,
        extra={
            "expected_asset_count": len(manifest["assets"]),
            "expected_source_routes": [
                "source-open-curated",
                "source-mixed-license",
                "procedural-2d",
                "dcc-assembly",
            ],
            "validator": "skills/asset-pipeline/scripts/validate_provenance.py",
        },
    )


BUILDERS: dict[str, Callable[[Path, dict[str, Any]], dict[str, Any]]] = {
    "mixed-asset-truth": build_mixed_asset_truth,
}


def build_fixture_family(slug: str, dest: Path) -> dict[str, Any]:
    family = fixture_index_by_slug().get(slug)
    if not isinstance(family, dict):
        raise RuntimeError(f"Asset fixture index does not contain family metadata for `{slug}`.")
    builder = BUILDERS.get(slug)
    if builder is None:
        known = ", ".join(sorted(BUILDERS))
        raise RuntimeError(f"No asset fixture builder exists for `{slug}`. Known builders: {known}")
    builder(dest, family)
    return read_json(dest / CONTRACT_PATH)

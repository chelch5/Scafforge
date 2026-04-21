from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path


ASSET_DIRECTORIES = (
    "briefs",
    "models",
    "sprites",
    "audio",
    "fonts",
    "themes",
    "previews",
    "workflows",
    "qa",
    "workfiles",
    "licenses",
)
ASSET_STARTER_PATHS = tuple(
    [f"assets/{subdir}" for subdir in ASSET_DIRECTORIES]
    + [
        "assets/requirements.json",
        "assets/pipeline.json",
        "assets/manifest.json",
        "assets/ATTRIBUTION.md",
        "assets/PROVENANCE.md",
        "assets/briefs/README.md",
        "assets/workflows/README.md",
        "assets/qa/import-report.json",
        "assets/qa/license-report.json",
        ".opencode/meta/asset-pipeline-bootstrap.json",
        ".opencode/meta/asset-provenance-lock.json",
    ]
)
ASSET_JSON_PATHS = (
    "assets/requirements.json",
    "assets/pipeline.json",
    "assets/manifest.json",
    "assets/qa/import-report.json",
    "assets/qa/license-report.json",
    ".opencode/meta/asset-pipeline-bootstrap.json",
    ".opencode/meta/asset-provenance-lock.json",
)
SOURCE_ROUTES = (
    "source-open-curated",
    "source-mixed-license",
    "procedural-2d",
    "procedural-layout",
    "procedural-world",
    "local-ai-2d",
    "local-ai-audio",
    "reconstruct-3d",
    "dcc-assembly",
)
PIPELINE_STAGES = ("optimize-import", "provenance-compliance")
DEFAULT_ALLOWED_LICENSES = ["CC0", "CC-BY", "MIT", "OFL", "Apache-2.0"]
DEFAULT_DENIED_LICENSES = [
    "CC-BY-NC",
    "CC-BY-ND",
    "GPL",
    "LGPL",
    "Proprietary",
    "Unknown",
    "Unlicensed",
]
KNOWN_LICENSES = tuple(sorted(set(DEFAULT_ALLOWED_LICENSES + DEFAULT_DENIED_LICENSES + ["CC-BY-SA"])))
MIXED_LICENSE_SOURCE_TOKENS = (
    "opengameart",
    "freesound",
    "itch.io",
    "itch ",
    "game-icons",
    "game icons",
    "cc-by",
    "cc by",
    "attribution",
)
CURATED_SOURCE_TOKENS = (
    "kenney",
    "quaternius",
    "poly haven",
    "polyhaven",
    "ambientcg",
    "google fonts",
)
LOCAL_AI_2D_TOKENS = (
    "comfyui",
    "invokeai",
    "automatic1111",
    "stable diffusion",
    "diffusers",
    "local ai image",
    "local image model",
)
LOCAL_AI_AUDIO_TOKENS = (
    "audiocraft",
    "local ai audio",
    "local ai music",
    "open-weight audio",
)
RECONSTRUCT_3D_TOKENS = (
    "reconstruct",
    "image-to-3d",
    "image to 3d",
    "text-to-3d",
    "text to 3d",
    "triposr",
    "trellis",
    "hunyuan3d",
    "scan",
)
DCC_TOKENS = (
    "blender",
    ".blend",
    ".glb",
    "geometry nodes",
    "kitbash",
    "uv unwrap",
    "material maker",
    "dcc",
)
LAYOUT_TOKENS = (
    "tilemap",
    "tileset",
    "wfc",
    "wave function collapse",
    "room",
    "layout",
    "dungeon",
    "biome layout",
)
WORLD_TOKENS = (
    "terrain",
    "terrain3d",
    "voxel",
    "heightmap",
    "biome",
    "world",
    "noise",
    "infinite",
)
PROCEDURAL_2D_TOKENS = (
    "procedural",
    "shader",
    "particle",
    "theme",
    "svg",
    "icon",
    "pixelorama",
    "aseprite",
    "audiostreamgenerator",
    "zzfx",
    "jsfxr",
)
REVIEW_REQUIRED_ROUTES = {"source-mixed-license", "local-ai-2d", "local-ai-audio", "reconstruct-3d", "dcc-assembly"}
IMPORT_COMMANDS = {
    "godot": "godot --headless --quit --path .",
    "generic": "run the repo-native headless import or asset validation command and record the result in assets/qa/import-report.json",
}
REQUIRED_SOURCE_TYPES = ("sourced", "procedural", "ai-generated", "reconstructed", "dcc-assembled")
QA_STATUSES = ("pending", "passed", "needs-review", "blocked", "failed")


def _normalize_text(value: str | None) -> str:
    if value is None:
        return ""
    return re.sub(r"\s+", " ", value).strip()


def _normalize_route_token(route: str) -> str:
    token = _normalize_text(route).lower().replace("_", "-").replace(" ", "-")
    token = re.sub(r"-{2,}", "-", token)
    return token.strip("-")


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        if not value or value in seen:
            continue
        seen.add(value)
        ordered.append(value)
    return ordered


def _json_digest(payload: object) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _read_bootstrap_provenance(repo_root: Path) -> dict[str, object]:
    path = repo_root / ".opencode" / "meta" / "bootstrap-provenance.json"
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def _contract_value(
    provenance: dict[str, object],
    explicit: str | None,
    field: str,
    fallback: str,
) -> str:
    explicit_text = _normalize_text(explicit)
    if explicit_text:
        return explicit_text
    finish = provenance.get("product_finish_contract")
    if isinstance(finish, dict):
        value = _normalize_text(str(finish.get(field, "")))
        if value:
            return value
    return fallback


def _target_platform(stack_label: str) -> str:
    lowered = stack_label.lower()
    if "android" in lowered:
        return "android"
    if "ios" in lowered:
        return "ios"
    if "web" in lowered:
        return "web"
    return "desktop"


def _art_style(stack_label: str, content_source_plan: str) -> str:
    lowered = f"{stack_label} {content_source_plan}".lower()
    if "pixel" in lowered:
        return "pixel-art"
    if "low poly" in lowered or "low-poly" in lowered:
        return "low-poly"
    if "realistic" in lowered or "pbr" in lowered:
        return "realistic"
    if "3d" in lowered:
        return "stylized-3d"
    if "2d" in lowered:
        return "stylized-2d"
    return "mixed"


def _license_filter(text: str) -> list[str]:
    lowered = text.lower()
    found = [license_name for license_name in KNOWN_LICENSES if license_name.lower() in lowered]
    allowed = [license_name for license_name in found if license_name not in DEFAULT_DENIED_LICENSES]
    return allowed or DEFAULT_ALLOWED_LICENSES


def _source_route_from_context(content_source_plan: str, licensing_text: str) -> str:
    lowered = f"{content_source_plan} {licensing_text}".lower()
    if any(token in lowered for token in MIXED_LICENSE_SOURCE_TOKENS):
        return "source-mixed-license"
    return "source-open-curated"


def _default_procedural_route(
    category: str,
    *,
    stack_label: str,
    content_source_plan: str,
) -> str:
    lowered = f"{stack_label} {content_source_plan}".lower()
    if category == "environments":
        if any(token in lowered for token in WORLD_TOKENS) or "3d" in lowered:
            return "procedural-world"
        return "procedural-layout"
    if category in {"props", "characters"}:
        if any(token in lowered for token in LAYOUT_TOKENS) or "3d" in lowered:
            return "procedural-layout"
        return "procedural-2d"
    return "procedural-2d"


def _canonical_route_name(
    route: str,
    *,
    category: str | None = None,
    stack_label: str = "",
    content_source_plan: str = "",
    licensing_text: str = "",
) -> str:
    normalized = _normalize_route_token(route)
    if normalized in SOURCE_ROUTES:
        return normalized

    procedural_route = _default_procedural_route(
        category or "generic",
        stack_label=stack_label,
        content_source_plan=content_source_plan,
    )
    sourced_route = _source_route_from_context(content_source_plan, licensing_text)
    lowered_context = f"{content_source_plan} {licensing_text}".lower()

    direct_map = {
        "third-party-open-licensed": sourced_route,
        "free-open": sourced_route,
        "source-open": "source-open-curated",
        "source-curated": "source-open-curated",
        "source-reviewed": "source-mixed-license",
        "codex-derived": procedural_route,
        "procedural-repo-authored": procedural_route,
        "godot-native-authored": procedural_route,
        "godot-builtin": procedural_route,
        "blender-mcp-generated": "reconstruct-3d" if any(token in lowered_context for token in RECONSTRUCT_3D_TOKENS) else "dcc-assembly",
        "blender-mcp": "reconstruct-3d" if any(token in lowered_context for token in RECONSTRUCT_3D_TOKENS) else "dcc-assembly",
        "local-ai-image": "local-ai-2d",
        "local-ai-sprite": "local-ai-2d",
        "local-ai-sound": "local-ai-audio",
        "image-to-3d": "reconstruct-3d",
        "text-to-3d": "reconstruct-3d",
    }
    if normalized in direct_map:
        return direct_map[normalized]
    return normalized or "source-open-curated"


def _route_family(route: str) -> str:
    if route.startswith("source-"):
        return "sourced"
    if route.startswith("procedural-"):
        return "procedural"
    if route.startswith("local-ai-"):
        return "local-ai"
    if route in {"reconstruct-3d", "dcc-assembly"}:
        return "dcc"
    return "mixed"


def _route_choice(primary: str, *fallbacks: str) -> dict[str, object]:
    ordered = _unique([primary, *fallbacks])
    payload: dict[str, object] = {
        "primary": ordered[0],
        "fallback_routes": ordered[1:],
    }
    if len(ordered) > 1:
        payload["fallback"] = ordered[1]
    return payload


def _infer_routes(
    stack_label: str,
    content_source_plan: str,
    placeholder_policy: str = "",
    licensing_or_provenance_constraints: str = "",
) -> tuple[dict[str, dict[str, object]], list[str]]:
    lowered = f"{stack_label} {content_source_plan} {placeholder_policy} {licensing_or_provenance_constraints}".lower()
    uses_dcc = any(token in lowered for token in DCC_TOKENS)
    uses_reconstruct = any(token in lowered for token in RECONSTRUCT_3D_TOKENS)
    uses_curated_open = any(token in lowered for token in CURATED_SOURCE_TOKENS)
    uses_mixed_license = any(token in lowered for token in MIXED_LICENSE_SOURCE_TOKENS)
    uses_source = uses_curated_open or uses_mixed_license or "licensed" in lowered or "free/open" in lowered
    uses_local_ai_2d = any(token in lowered for token in LOCAL_AI_2D_TOKENS)
    uses_local_ai_audio = any(token in lowered for token in LOCAL_AI_AUDIO_TOKENS)
    uses_procedural_2d = any(token in lowered for token in PROCEDURAL_2D_TOKENS)
    uses_layout = any(token in lowered for token in LAYOUT_TOKENS)
    uses_world = any(token in lowered for token in WORLD_TOKENS)
    is_3d = any(token in lowered for token in ("3d", "low poly", "low-poly", ".glb", ".blend"))
    native_only = any(
        token in lowered
        for token in (
            "no external assets",
            "no external asset",
            "100% godot",
            "100% godot engine features",
            "godot native capabilities",
            "godot native features",
            "godot built-in",
            "godot built in",
            "nothing to track",
        )
    )
    engine_authored_audio = any(
        token in lowered
        for token in ("audiostreamgenerator", "procedural sfx", "procedural audio", "godot audio", "zzfx", "jsfxr")
    )
    sourced_route = _source_route_from_context(content_source_plan, licensing_or_provenance_constraints) if uses_source else "source-open-curated"

    category_candidates: dict[str, list[str]] = {}
    if native_only:
        for category in ("characters", "environments", "props", "ui", "audio", "vfx"):
            category_candidates[category] = [
                _default_procedural_route(
                    category,
                    stack_label=stack_label,
                    content_source_plan=content_source_plan,
                ),
                "source-open-curated",
            ]
    else:
        category_candidates["characters"] = (
            ["reconstruct-3d", "dcc-assembly", sourced_route, _default_procedural_route("characters", stack_label=stack_label, content_source_plan=content_source_plan)]
            if uses_reconstruct
            else ["dcc-assembly", sourced_route, _default_procedural_route("characters", stack_label=stack_label, content_source_plan=content_source_plan)]
            if uses_dcc or (is_3d and not uses_local_ai_2d and not uses_source)
            else ["local-ai-2d", sourced_route, "procedural-2d"]
            if uses_local_ai_2d and not is_3d
            else [sourced_route, "dcc-assembly" if is_3d else "procedural-2d", _default_procedural_route("characters", stack_label=stack_label, content_source_plan=content_source_plan)]
            if uses_source
            else [_default_procedural_route("characters", stack_label=stack_label, content_source_plan=content_source_plan), "source-open-curated", "dcc-assembly" if is_3d else "procedural-2d"]
        )
        category_candidates["environments"] = (
            ["procedural-world", sourced_route, "dcc-assembly" if is_3d else "procedural-layout"]
            if uses_world
            else ["procedural-layout", sourced_route, "procedural-world" if is_3d else "procedural-2d"]
            if uses_layout
            else [sourced_route, "procedural-world" if is_3d else "procedural-layout", "dcc-assembly" if is_3d else "procedural-2d"]
            if uses_source
            else ["local-ai-2d", "source-open-curated", "procedural-layout"]
            if uses_local_ai_2d and not is_3d
            else ["procedural-world" if is_3d else "procedural-layout", "source-open-curated", "dcc-assembly" if is_3d else "procedural-2d"]
        )
        category_candidates["props"] = (
            ["reconstruct-3d", "dcc-assembly", sourced_route, "procedural-layout"]
            if uses_reconstruct
            else ["dcc-assembly", sourced_route, "procedural-layout"]
            if uses_dcc or (is_3d and not uses_source)
            else [sourced_route, "dcc-assembly" if is_3d else "procedural-2d", "procedural-layout"]
            if uses_source
            else ["local-ai-2d", "source-open-curated", "procedural-2d"]
            if uses_local_ai_2d and not is_3d
            else ["procedural-layout" if is_3d else "procedural-2d", "source-open-curated", "dcc-assembly" if is_3d else "procedural-2d"]
        )
        category_candidates["ui"] = (
            ["procedural-2d", sourced_route, "local-ai-2d"]
            if uses_procedural_2d
            else [sourced_route, "procedural-2d", "local-ai-2d"]
            if uses_source
            else ["local-ai-2d", "source-open-curated", "procedural-2d"]
            if uses_local_ai_2d
            else ["procedural-2d", "source-open-curated", "local-ai-2d"]
        )
        category_candidates["audio"] = (
            ["local-ai-audio", sourced_route, "procedural-2d"]
            if uses_local_ai_audio
            else ["procedural-2d", sourced_route, "local-ai-audio"]
            if engine_authored_audio
            else [sourced_route, "procedural-2d", "local-ai-audio"]
            if uses_source
            else ["source-open-curated", "procedural-2d", "source-mixed-license"]
        )
        category_candidates["vfx"] = (
            ["procedural-2d", sourced_route, "local-ai-2d"]
            if uses_procedural_2d or uses_layout or uses_world
            else [sourced_route, "procedural-2d", "local-ai-2d"]
            if uses_source
            else ["local-ai-2d", "procedural-2d", "source-open-curated"]
            if uses_local_ai_2d
            else ["procedural-2d", "source-open-curated", "local-ai-2d"]
        )

    canonical_routes: dict[str, dict[str, object]] = {}
    brief_targets: list[str] = []
    for category, candidates in category_candidates.items():
        canonical_candidates = _unique(
            [
                _canonical_route_name(
                    candidate,
                    category=category,
                    stack_label=stack_label,
                    content_source_plan=content_source_plan,
                    licensing_text=licensing_or_provenance_constraints,
                )
                for candidate in candidates
            ]
        )
        choice = _route_choice(canonical_candidates[0], *canonical_candidates[1:])
        choice["asset_class"] = _asset_class(category, str(choice["primary"]), _art_style(stack_label, content_source_plan))
        choice["required_pipeline_stages"] = list(PIPELINE_STAGES)
        choice["escalation_policy"] = {
            "prefer_deterministic_and_curated_first": True,
            "allow_local_ai_only_after_curated_and_procedural_gap": True,
            "stop_and_ask_when": _stop_and_ask_reason(category),
        }
        canonical_routes[category] = choice
        if _requires_brief(str(choice["primary"])):
            brief_targets.append(category)
    return canonical_routes, brief_targets


def _asset_class(category: str, route: str, art_style: str) -> str:
    if category == "audio":
        return "audio"
    if category == "ui":
        return "ui"
    if category == "vfx":
        return "vfx"
    if route in {"dcc-assembly", "reconstruct-3d"}:
        return "3d" if art_style != "pixel-art" else "2d"
    return "2d" if art_style == "pixel-art" else "mixed"


def _requires_brief(route: str) -> bool:
    return route in {"dcc-assembly", "reconstruct-3d", "local-ai-2d", "local-ai-audio"}


def _stop_and_ask_reason(category: str) -> str:
    reasons = {
        "characters": "ask for human direction when the brief requires a hero character, facial likeness, or animation fidelity beyond the seeded quality bar",
        "environments": "ask for human direction when the environment style, scale, or traversal readability is still unresolved",
        "props": "ask for human direction when collision silhouette or gameplay readability conflicts with the chosen source route",
        "ui": "ask for human direction when accessibility, branding, or icon semantics remain ambiguous",
        "audio": "ask for human direction when commercial-use policy or music style is unresolved",
        "vfx": "ask for human direction when gameplay telegraphing and visual spectacle pull in different directions",
    }
    return reasons[category]


def _category_required_outputs(category: str, route: str) -> list[str]:
    mapping = {
        "characters": ["character-artifact", "preview-artifact", "workflow-record"],
        "environments": ["environment-artifact", "preview-artifact", "import-proof"],
        "props": ["prop-artifact", "preview-artifact", "import-proof"],
        "ui": ["ui-artifact", "attribution-proof", "import-proof"],
        "audio": ["audio-artifact", "license-proof", "import-proof"],
        "vfx": ["vfx-artifact", "preview-artifact", "import-proof"],
    }
    outputs = list(mapping[category])
    if route.startswith("source-") and "attribution-proof" not in outputs:
        outputs.append("attribution-proof")
    return outputs


def _quality_bar(category: str, target_platform: str) -> str:
    mobile_suffix = " within mobile-ready texture, memory, and import budgets" if target_platform in {"android", "ios"} else ""
    mapping = {
        "characters": f"ship-ready silhouette, readable gameplay role, and clean engine import{mobile_suffix}",
        "environments": f"coherent traversal readability, stable tiling, and clean engine import{mobile_suffix}",
        "props": f"clear gameplay silhouette, bounded poly budget, and clean engine import{mobile_suffix}",
        "ui": "readable at target resolution with clear states, scalable vector-or-spritesheet sources, and explicit attribution when required",
        "audio": "headless-importable engine format, bounded duration, and explicit license/provenance coverage",
        "vfx": f"gameplay-readable telegraphing, controllable performance cost, and clean engine import{mobile_suffix}",
    }
    return mapping[category]


def _license_policy_for_route(route: str) -> str:
    if route == "source-mixed-license":
        return "allowlist-plus-attribution-review"
    if route == "source-open-curated":
        return "allowlist-only"
    if route.startswith("local-ai-"):
        return "open-tool-and-open-weight-allowlist-only"
    return "repo-authored-or-cleared-inputs-only"


def _scale_or_resolution_target(category: str, target_platform: str, art_style: str) -> str:
    if category == "audio":
        return "prefer OGG or WAV sized for rapid engine import and mobile-safe download budgets" if target_platform in {"android", "ios"} else "prefer OGG or WAV with engine-native import settings"
    if category in {"characters", "props"} and art_style != "pixel-art":
        return "512-1024 textures and mobile-safe mesh budgets" if target_platform in {"android", "ios"} else "1024-2048 textures and project-defined mesh budgets"
    if category == "ui":
        return "vector-first or resolution-independent UI surfaces"
    return "512-1024 source resolution" if target_platform in {"android", "ios"} else "1024-2048 source resolution"


def _fallback_ladders() -> dict[str, dict[str, object]]:
    return {
        "fonts": {
            "preferred_routes": ["source-open-curated", "source-mixed-license"],
            "escalate_to": [],
            "stop_and_ask_when": "the product needs a custom brand font instead of a curated open family",
        },
        "icons": {
            "preferred_routes": ["procedural-2d", "source-open-curated", "source-mixed-license", "local-ai-2d"],
            "escalate_to": ["local-ai-2d"],
            "stop_and_ask_when": "icon semantics or accessibility states are still ambiguous",
        },
        "ui-kits": {
            "preferred_routes": ["procedural-2d", "source-open-curated", "source-mixed-license", "local-ai-2d"],
            "escalate_to": ["local-ai-2d"],
            "stop_and_ask_when": "the style system needs bespoke branding that deterministic composition cannot satisfy",
        },
        "sprites-tiles": {
            "preferred_routes": ["source-open-curated", "procedural-layout", "source-mixed-license", "local-ai-2d"],
            "escalate_to": ["local-ai-2d"],
            "stop_and_ask_when": "the required animation count or style cohesion remains unresolved after curated/procedural passes",
        },
        "vfx": {
            "preferred_routes": ["procedural-2d", "source-open-curated", "local-ai-2d"],
            "escalate_to": ["local-ai-2d"],
            "stop_and_ask_when": "gameplay telegraph clarity conflicts with spectacle goals",
        },
        "sfx": {
            "preferred_routes": ["procedural-2d", "source-open-curated", "source-mixed-license", "local-ai-audio"],
            "escalate_to": ["local-ai-audio"],
            "stop_and_ask_when": "music or signature audio identity is still unresolved",
        },
        "props": {
            "preferred_routes": ["source-open-curated", "dcc-assembly", "reconstruct-3d", "source-mixed-license"],
            "escalate_to": ["dcc-assembly", "reconstruct-3d"],
            "stop_and_ask_when": "the prop must carry hero-level story detail or exact likeness",
        },
        "terrain": {
            "preferred_routes": ["procedural-world", "source-open-curated", "dcc-assembly"],
            "escalate_to": ["dcc-assembly"],
            "stop_and_ask_when": "terrain readability, streaming limits, or biome direction remain unresolved",
        },
        "environments": {
            "preferred_routes": ["procedural-layout", "procedural-world", "source-open-curated", "dcc-assembly", "source-mixed-license"],
            "escalate_to": ["dcc-assembly"],
            "stop_and_ask_when": "layout coverage and art-direction goals diverge in a way the current route cannot resolve truthfully",
        },
        "characters": {
            "preferred_routes": ["source-open-curated", "dcc-assembly", "reconstruct-3d", "source-mixed-license"],
            "escalate_to": ["dcc-assembly", "reconstruct-3d"],
            "stop_and_ask_when": "the brief needs hero-character quality, facial likeness, or complex animation polish",
        },
    }


def _research_distillation() -> list[dict[str, object]]:
    return [
        {
            "capability": "source-open-curated",
            "default_choices": ["Kenney", "Quaternius", "Poly Haven", "ambientCG", "Google Fonts"],
            "non_default_exceptions": ["OpenGameArt-style and similar sources belong on source-mixed-license when attribution or per-asset commercial review is required."],
            "proof_requirements": ["manifest source_url", "explicit license", "author_or_origin", "license report allowlist pass"],
        },
        {
            "capability": "source-mixed-license",
            "default_choices": ["OpenGameArt", "Freesound", "itch.io free assets", "Game-icons"],
            "non_default_exceptions": ["Deny by default when the license is unknown, non-commercial, no-derivatives, or otherwise unsupported by the repo policy."],
            "proof_requirements": ["attribution_required=true", "license report review record", "ATTRIBUTION.md entry"],
        },
        {
            "capability": "procedural-2d",
            "default_choices": ["Godot shaders", "Godot particles", "Theme resources", "Pixelorama/Aseprite-style sprite cleanup"],
            "non_default_exceptions": ["Do not escalate to local AI for routine UI chrome or simple icons before deterministic composition is exhausted."],
            "proof_requirements": ["workflow record", "preview when not trivially inspectable", "import report success"],
        },
        {
            "capability": "procedural-layout",
            "default_choices": ["TileMap/TileSet", "Wave Function Collapse", "room-layout generators"],
            "non_default_exceptions": ["Escalate to human review when layout readability and authored encounter quality still conflict."],
            "proof_requirements": ["workflow record", "preview or contact sheet", "import report success"],
        },
        {
            "capability": "procedural-world",
            "default_choices": ["FastNoiseLite", "Terrain3D", "godot_voxel-style chunk systems"],
            "non_default_exceptions": ["Treat world-scale generation as bounded and budgeted; do not imply autonomous AAA-world authoring."],
            "proof_requirements": ["workflow record", "optimization report coverage", "import report success"],
        },
        {
            "capability": "local-ai-2d",
            "default_choices": ["ComfyUI", "InvokeAI", "AUTOMATIC1111", "Diffusers wrappers"],
            "non_default_exceptions": ["Hosted commercial APIs remain denied by default; approved exceptions belong in later plan work, not this baseline."],
            "proof_requirements": ["tool_chain", "model_or_checkpoint", "prompt_or_recipe", "workflow record", "preview artifact", "license report pass"],
        },
        {
            "capability": "local-ai-audio",
            "default_choices": ["local/open-source orchestration with open-weight audio models"],
            "non_default_exceptions": ["Prefer procedural SFX and curated sourced audio first; treat hosted commercial audio generation as denied by default."],
            "proof_requirements": ["tool_chain", "model_or_checkpoint", "prompt_or_recipe", "license report pass"],
        },
        {
            "capability": "reconstruct-3d",
            "default_choices": ["TripoSR-style reconstruction", "Hunyuan3D/TRELLIS-style local reconstruction stacks"],
            "non_default_exceptions": ["Reconstruction is a bootstrap lane, not final truth without cleanup, QA, and optimization."],
            "proof_requirements": ["workflow record", "tool_chain", "preview artifact", "import report success"],
        },
        {
            "capability": "dcc-assembly",
            "default_choices": ["Blender-driven DCC assembly", "Geometry Nodes", "Material Maker-informed material cleanup"],
            "non_default_exceptions": ["Treat Blender-MCP as execution and cleanup infrastructure, not as a semantic guarantee of final asset quality."],
            "proof_requirements": ["workflow record", "preview artifact", "import report success", "optimization stage complete"],
        },
    ]


def _ownership_map() -> dict[str, dict[str, str]]:
    return {
        "assets/requirements.json": {
            "authority": "authoritative",
            "owns": "requested asset intent, category needs, quality bar, and route preferences from the project brief",
        },
        "assets/pipeline.json": {
            "authority": "authoritative",
            "owns": "category-level route selection, fallback ordering, pipeline stage policy, and compliance configuration",
        },
        "assets/manifest.json": {
            "authority": "authoritative",
            "owns": "per-asset provenance, compliance, workflow, and import truth",
        },
        ".opencode/meta/asset-provenance-lock.json": {
            "authority": "authoritative",
            "owns": "pipeline contract revision and manifest or pipeline digest truth",
        },
        "assets/ATTRIBUTION.md": {
            "authority": "derived",
            "owns": "human-facing attribution summary built from the manifest",
        },
        "assets/PROVENANCE.md": {
            "authority": "derived",
            "owns": "human-facing provenance ledger built from the manifest and lock",
        },
        "assets/qa/import-report.json": {
            "authority": "derived",
            "owns": "latest import and optimization verification result",
        },
        "assets/qa/license-report.json": {
            "authority": "derived",
            "owns": "latest license and compliance verification result",
        },
    }


def _requirements_payload(pipeline: dict[str, object]) -> dict[str, object]:
    routes = pipeline.get("routes", {})
    target_platform = str(pipeline.get("target_platform", "desktop"))
    art_style = str(pipeline.get("art_style", "mixed"))
    categories: list[dict[str, object]] = []
    if isinstance(routes, dict):
        for category, choice in routes.items():
            if not isinstance(category, str) or not isinstance(choice, dict):
                continue
            primary = str(choice.get("primary", "source-open-curated"))
            fallback_routes = choice.get("fallback_routes", [])
            if not isinstance(fallback_routes, list):
                fallback_routes = []
            categories.append(
                {
                    "id": category,
                    "asset_class": choice.get("asset_class", "mixed"),
                    "required_outputs": _category_required_outputs(category, primary),
                    "quality_bar": _quality_bar(category, target_platform),
                    "license_policy": _license_policy_for_route(primary),
                    "preferred_source_routes": [primary],
                    "fallback_routes": [str(item) for item in fallback_routes if isinstance(item, str)],
                    "engine_constraints": {
                        "target_platform": target_platform,
                        "texture_max_size": pipeline.get("texture_max_size"),
                        "model_max_tris": pipeline.get("model_max_tris"),
                        "asset_pipeline_stages": list(PIPELINE_STAGES),
                    },
                    "style_notes": f"Keep outputs aligned to the repo art style `{art_style}` and the content source plan.",
                    "scale_or_resolution_target": _scale_or_resolution_target(category, target_platform, art_style),
                }
            )
    return {
        "version": 1,
        "project_asset_profile": {
            "stack_label": pipeline.get("stack_label"),
            "deliverable_kind": pipeline.get("deliverable_kind"),
            "placeholder_policy": pipeline.get("placeholder_policy"),
            "art_style": art_style,
            "target_platform": target_platform,
            "route_policy": {
                "prefer_deterministic_and_curated_first": True,
                "commercial_api_generation_default": "denied",
                "canonical_truth_owner": "assets/manifest.json",
            },
            "quality_contract": {
                "finish_acceptance_signals": pipeline.get("finish_acceptance_signals"),
                "content_source_plan": pipeline.get("content_source_plan"),
            },
        },
        "categories": categories,
    }


def _manifest_payload() -> dict[str, object]:
    return {
        "version": 1,
        "generated_at": _now_iso(),
        "assets": [],
        "source_type_vocabulary": list(REQUIRED_SOURCE_TYPES),
        "qa_status_vocabulary": list(QA_STATUSES),
    }


def _import_report_payload(pipeline: dict[str, object]) -> dict[str, object]:
    stack_label = str(pipeline.get("stack_label", ""))
    import_command = IMPORT_COMMANDS["godot"] if "godot" in stack_label.lower() else IMPORT_COMMANDS["generic"]
    return {
        "version": 1,
        "generated_at": _now_iso(),
        "report_kind": "import-optimization",
        "status": "pending",
        "summary": "No asset import or optimization run has been recorded yet.",
        "stack_label": pipeline.get("stack_label"),
        "import_command": import_command,
        "checked_assets": [],
        "optimization_rules": {
            "2d": ["lossless compression first", "palette reduction only when the style can tolerate it"],
            "3d": ["validate glTF structure", "resize oversized textures", "record mesh or material optimization status"],
            "audio": ["prefer engine-native compressed formats", "trim silence and record normalization decisions"],
        },
    }


def _license_report_payload(pipeline: dict[str, object]) -> dict[str, object]:
    return {
        "version": 1,
        "generated_at": _now_iso(),
        "report_kind": "license-compliance",
        "status": "pending",
        "summary": "No asset license verification run has been recorded yet.",
        "allowed_licenses": list(pipeline.get("license_filter", DEFAULT_ALLOWED_LICENSES)),
        "denied_licenses": list(DEFAULT_DENIED_LICENSES),
        "review_required_routes": sorted(REVIEW_REQUIRED_ROUTES),
        "reviewed_assets": [],
    }


def _provenance_markdown(
    *,
    placeholder_policy: str,
    licensing_or_provenance_constraints: str,
    finish_acceptance_signals: str,
) -> str:
    return "\n".join(
        (
            "# Asset Provenance",
            "",
            "Derived human ledger for asset provenance. `assets/manifest.json` owns per-asset truth and `.opencode/meta/asset-provenance-lock.json` owns the pipeline-contract digest state.",
            "",
            "## Rules",
            "",
            "- Update the manifest first; treat this file as a rendered or synchronized ledger, not the only truth surface.",
            "- Every entry must use a repo-relative path under `assets/` or a Godot `res://` import path.",
            "- Generated assets must record the exact workflow, tool chain, and model/checkpoint data in the manifest.",
            "- Third-party assets must keep the source URL, precise license value, and author or origin in the manifest.",
            f"- Placeholder policy: {placeholder_policy}",
            f"- Licensing/provenance constraints: {licensing_or_provenance_constraints}",
            f"- Finish acceptance signals: {finish_acceptance_signals}",
            "",
            "| asset_path | source_or_workflow | license | author | acquired_or_generated_on | notes |",
            "| --- | --- | --- | --- | --- | --- |",
            "",
        )
    )


def _attribution_markdown() -> str:
    return "\n".join(
        (
            "# Asset Attribution",
            "",
            "Derived human-facing attribution summary. `assets/manifest.json` is authoritative for attribution-required assets.",
            "",
            "## Required entries",
            "",
            "- Add one line per asset where `attribution_required` is `true` in the manifest.",
            "- Include the asset path, author or origin, source URL when available, and exact attribution text required by the source license.",
            "",
        )
    )


def _briefs_readme(pipeline: dict[str, object]) -> str:
    brief_targets = pipeline.get("brief_targets", [])
    route_line = ", ".join(brief_targets) if isinstance(brief_targets, list) and brief_targets else "none yet"
    return "\n".join(
        (
            "# Asset Briefs",
            "",
            "Write one brief per high-complexity asset route such as `dcc-assembly`, `reconstruct-3d`, or approved local-AI generation.",
            "",
            f"- Current brief-target categories: {route_line}",
            "- Store briefs as `assets/briefs/<asset-name>.md`.",
            "- Reference the owning category from `assets/requirements.json` and the selected route from `assets/pipeline.json`.",
            "- Record the matching workflow file under `assets/workflows/` and the final asset entry in `assets/manifest.json`.",
            "",
        )
    )


def _workflows_readme() -> str:
    return "\n".join(
        (
            "# Asset Workflows",
            "",
            "Store structured workflow definitions or run records here.",
            "",
            "- Use JSON by default for machine-readable workflows and run records.",
            "- Prefer one file per asset or per repeatable workflow recipe.",
            "- Reference these files from `assets/manifest.json` via `workflow_ref`.",
            "- Keep prompts, recipes, node-graph exports, or Blender/DCC step logs here instead of burying them in ticket prose.",
            "",
        )
    )


def _pipeline_payload(
    *,
    stack_label: str,
    deliverable_kind: str,
    placeholder_policy: str,
    content_source_plan: str,
    licensing_or_provenance_constraints: str,
    finish_acceptance_signals: str,
) -> dict[str, object]:
    routes, brief_targets = _infer_routes(
        stack_label,
        content_source_plan,
        placeholder_policy,
        licensing_or_provenance_constraints,
    )
    target_platform = _target_platform(stack_label)
    is_mobile = target_platform in {"android", "ios"}
    source_routes_in_use = sorted(
        {
            str(choice.get("primary"))
            for choice in routes.values()
            if isinstance(choice, dict) and isinstance(choice.get("primary"), str)
        }
    )
    pipeline_stages_in_use = list(PIPELINE_STAGES)
    return {
        "version": 2,
        "taxonomy_version": "asset-capability-2026-04-21",
        "stack_label": stack_label,
        "deliverable_kind": deliverable_kind,
        "placeholder_policy": placeholder_policy,
        "art_style": _art_style(stack_label, content_source_plan),
        "target_platform": target_platform,
        "route_mode": "hybrid" if len(source_routes_in_use) > 1 else "single-route",
        "content_source_plan": content_source_plan,
        "licensing_or_provenance_constraints": licensing_or_provenance_constraints,
        "finish_acceptance_signals": finish_acceptance_signals,
        "capability_taxonomy": {
            "source_routes": list(SOURCE_ROUTES),
            "pipeline_stages": list(PIPELINE_STAGES),
            "legacy_route_mapping": {
                "third-party-open-licensed": "source-open-curated or source-mixed-license depending on attribution or commercial review needs",
                "procedural-repo-authored": "procedural-2d, procedural-layout, or procedural-world by asset class",
                "godot-native-authored": "procedural-2d, procedural-layout, or procedural-world by asset class",
                "blender-mcp-generated": "dcc-assembly by default, optionally reconstruct-3d when the workflow is reconstruction-led",
            },
        },
        "route_policy": {
            "prefer_deterministic_and_curated_first": True,
            "commercial_api_generation_default": "denied",
            "unsupported_source_default": "deny",
        },
        "routes": routes,
        "source_routes_in_use": source_routes_in_use,
        "pipeline_stages_in_use": pipeline_stages_in_use,
        "route_families": sorted({_route_family(str(choice["primary"])) for choice in routes.values() if isinstance(choice, dict) and "primary" in choice}),
        "brief_targets": brief_targets,
        "canonical_ownership": _ownership_map(),
        "research_distillation": _research_distillation(),
        "fallback_ladders": _fallback_ladders(),
        "provenance_requirements": {
            "authoritative_manifest": "assets/manifest.json",
            "requirements_path": "assets/requirements.json",
            "pipeline_path": "assets/pipeline.json",
            "lock_path": ".opencode/meta/asset-provenance-lock.json",
            "attribution_path": "assets/ATTRIBUTION.md",
            "provenance_path": "assets/PROVENANCE.md",
            "workflow_dir": "assets/workflows",
            "previews_dir": "assets/previews",
            "qa": {
                "import_report": "assets/qa/import-report.json",
                "license_report": "assets/qa/license-report.json",
            },
            "required_generated_fields": ["tool_chain", "workflow_ref", "import_report_ref", "license_report_ref"],
            "required_ai_fields": ["tool_chain", "model_or_checkpoint", "prompt_or_recipe"],
            "required_sourced_fields": ["source_url", "license", "author_or_origin"],
            "route_specific_finish_proof_required": True,
        },
        "compliance_policy": {
            "allowed_licenses": _license_filter(licensing_or_provenance_constraints),
            "denied_licenses": list(DEFAULT_DENIED_LICENSES),
            "source_allowlist": ["Kenney", "Quaternius", "Poly Haven", "ambientCG", "Google Fonts"],
            "source_review_required": ["OpenGameArt", "Freesound", "itch.io free assets", "Game-icons"],
            "commercial_api_generation": "denied-by-default",
        },
        "qa_rules": {
            "preview_required_for_routes": ["dcc-assembly", "reconstruct-3d", "local-ai-2d", "local-ai-audio"],
            "import_report_path": "assets/qa/import-report.json",
            "license_report_path": "assets/qa/license-report.json",
            "optimization_stage": {
                "2d": "optimize textures and sprite sheets before recording import proof",
                "3d": "optimize meshes, materials, and texture sizes before recording import proof",
                "audio": "trim, normalize, and convert to engine-ready formats before recording import proof",
            },
            "stack_specific_expectations": {
                "godot": {
                    "headless_import_command": IMPORT_COMMANDS["godot"],
                    "record_import_success_in": "assets/qa/import-report.json",
                }
            },
        },
        "tool_license_policy": {
            "allow_open_source_tools": True,
            "allow_commercial_tools": False,
            "notes": "Record tool licenses separately from model or checkpoint licenses when AI-assisted generation is used.",
        },
        "model_license_policy": {
            "allow_open_weights": True,
            "allow_noncommercial_weights": False,
            "notes": "Commercial APIs and non-commercial model weights remain denied by default in this baseline.",
        },
        "license_filter": _license_filter(licensing_or_provenance_constraints),
        "texture_max_size": 1024 if is_mobile else 2048,
        "model_max_tris": 5000 if is_mobile else 12000,
        "initialized_by": "skills/asset-pipeline/scripts/init_asset_pipeline.py",
    }


def _lock_payload(
    *,
    requirements: dict[str, object],
    pipeline: dict[str, object],
    manifest: dict[str, object],
) -> dict[str, object]:
    return {
        "version": 1,
        "generated_at": _now_iso(),
        "process_contract_revision": "asset-pipeline-2026-04-21",
        "requirements_path": "assets/requirements.json",
        "requirements_digest": _json_digest(requirements),
        "pipeline_path": "assets/pipeline.json",
        "pipeline_digest": _json_digest(pipeline),
        "manifest_path": "assets/manifest.json",
        "manifest_digest": _json_digest(manifest),
        "authoritative_truth": {
            "manifest": "assets/manifest.json",
            "lock": ".opencode/meta/asset-provenance-lock.json",
        },
        "derived_surfaces": {
            "provenance": "assets/PROVENANCE.md",
            "attribution": "assets/ATTRIBUTION.md",
            "import_report": "assets/qa/import-report.json",
            "license_report": "assets/qa/license-report.json",
        },
    }


def _bootstrap_metadata(
    pipeline: dict[str, object],
    lock: dict[str, object],
) -> dict[str, object]:
    routes = pipeline.get("routes", {})
    primary_routes = {
        category: choice.get("primary")
        for category, choice in routes.items()
        if isinstance(choice, dict) and isinstance(choice.get("primary"), str)
    }
    required_agents: list[str] = []
    required_skills: list[str] = []
    required_mcp_servers: list[str] = []
    suggested_agents: list[str] = ["asset-strategist", "import-optimizer", "provenance-auditor"]
    suggested_skills: list[str] = []
    if "dcc-assembly" in primary_routes.values():
        required_agents.append("blender-asset-creator")
        required_skills.extend(["asset-description", "blender-mcp-workflow"])
        required_mcp_servers.append("blender_agent")
        suggested_agents.append("blender-asset-creator")
        suggested_skills.extend(["asset-description", "blender-mcp-workflow"])
    if any(route in {"source-open-curated", "source-mixed-license"} for route in primary_routes.values()):
        suggested_agents.append("asset-sourcer")
    if any(route == "source-mixed-license" for route in primary_routes.values()):
        suggested_agents.append("provenance-auditor")
    if any(str(route).startswith("procedural-") for route in primary_routes.values()):
        suggested_agents.append("world-builder")
    if any(route == "local-ai-2d" for route in primary_routes.values()):
        suggested_agents.append("texture-ui-generator")
    if any(route == "local-ai-audio" for route in primary_routes.values()):
        suggested_agents.append("audio-generator")
    return {
        "version": 2,
        "asset_root": "assets",
        "requirements_path": "assets/requirements.json",
        "pipeline_path": "assets/pipeline.json",
        "manifest_path": "assets/manifest.json",
        "attribution_path": "assets/ATTRIBUTION.md",
        "provenance_path": "assets/PROVENANCE.md",
        "briefs_dir": "assets/briefs",
        "workflows_dir": "assets/workflows",
        "previews_dir": "assets/previews",
        "qa_paths": {
            "import_report": "assets/qa/import-report.json",
            "license_report": "assets/qa/license-report.json",
        },
        "lock_path": ".opencode/meta/asset-provenance-lock.json",
        "process_contract_revision": lock.get("process_contract_revision"),
        "stack_label": pipeline.get("stack_label"),
        "target_platform": pipeline.get("target_platform"),
        "route_mode": pipeline.get("route_mode"),
        "routes": primary_routes,
        "source_routes_in_use": pipeline.get("source_routes_in_use", []),
        "pipeline_stages_in_use": pipeline.get("pipeline_stages_in_use", []),
        "route_families": pipeline.get("route_families", []),
        "brief_targets": pipeline.get("brief_targets", []),
        "requires_blender_mcp": route_map_requires_blender(primary_routes),
        "required_agents": sorted(set(required_agents)),
        "required_skills": sorted(set(required_skills)),
        "required_mcp_servers": sorted(set(required_mcp_servers)),
        "suggested_agents": sorted(set(suggested_agents)),
        "suggested_skills": sorted(set(suggested_skills)),
        "canonical_ownership": pipeline.get("canonical_ownership", {}),
        "provenance_requirements": pipeline.get("provenance_requirements", {}),
        "compliance_policy": pipeline.get("compliance_policy", {}),
        "initialized_by": "skills/asset-pipeline/scripts/init_asset_pipeline.py",
    }


def route_map_requires_blender(routes: dict[str, object]) -> bool:
    for choice in routes.values():
        primary = choice.get("primary") if isinstance(choice, dict) else choice
        if isinstance(primary, str) and _canonical_route_name(primary) == "dcc-assembly":
            return True
    return False


def preview_asset_pipeline(
    *,
    stack_label: str,
    deliverable_kind: str,
    placeholder_policy: str,
    content_source_plan: str,
    licensing_or_provenance_constraints: str,
    finish_acceptance_signals: str,
) -> tuple[dict[str, object], dict[str, object]]:
    pipeline = _pipeline_payload(
        stack_label=stack_label,
        deliverable_kind=deliverable_kind,
        placeholder_policy=placeholder_policy,
        content_source_plan=content_source_plan,
        licensing_or_provenance_constraints=licensing_or_provenance_constraints,
        finish_acceptance_signals=finish_acceptance_signals,
    )
    manifest = _manifest_payload()
    requirements = _requirements_payload(pipeline)
    lock = _lock_payload(requirements=requirements, pipeline=pipeline, manifest=manifest)
    return pipeline, _bootstrap_metadata(pipeline, lock)


def _write_text(path: Path, content: str, *, force: bool) -> bool:
    if path.exists() and not force:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return True


def initialize_asset_pipeline(
    repo_root: Path,
    *,
    stack_label: str,
    deliverable_kind: str,
    placeholder_policy: str,
    content_source_plan: str,
    licensing_or_provenance_constraints: str,
    finish_acceptance_signals: str,
    force: bool = False,
) -> list[Path]:
    repo_root = repo_root.expanduser().resolve()
    asset_root = repo_root / "assets"
    meta_root = repo_root / ".opencode" / "meta"
    created: list[Path] = []

    pipeline = _pipeline_payload(
        stack_label=stack_label,
        deliverable_kind=deliverable_kind,
        placeholder_policy=placeholder_policy,
        content_source_plan=content_source_plan,
        licensing_or_provenance_constraints=licensing_or_provenance_constraints,
        finish_acceptance_signals=finish_acceptance_signals,
    )
    requirements = _requirements_payload(pipeline)
    manifest = _manifest_payload()
    import_report = _import_report_payload(pipeline)
    license_report = _license_report_payload(pipeline)
    lock = _lock_payload(requirements=requirements, pipeline=pipeline, manifest=manifest)
    metadata = _bootstrap_metadata(pipeline, lock)

    for subdir in ASSET_DIRECTORIES:
        directory = asset_root / subdir
        directory.mkdir(parents=True, exist_ok=True)
        keep_path = directory / ".gitkeep"
        if _write_text(keep_path, "", force=force):
            created.append(keep_path)

    json_targets = {
        asset_root / "requirements.json": requirements,
        asset_root / "pipeline.json": pipeline,
        asset_root / "manifest.json": manifest,
        asset_root / "qa" / "import-report.json": import_report,
        asset_root / "qa" / "license-report.json": license_report,
        meta_root / "asset-pipeline-bootstrap.json": metadata,
        meta_root / "asset-provenance-lock.json": lock,
    }
    for path, payload in json_targets.items():
        if _write_text(path, json.dumps(payload, indent=2) + "\n", force=force):
            created.append(path)

    text_targets = {
        asset_root / "PROVENANCE.md": _provenance_markdown(
            placeholder_policy=placeholder_policy,
            licensing_or_provenance_constraints=licensing_or_provenance_constraints,
            finish_acceptance_signals=finish_acceptance_signals,
        ),
        asset_root / "ATTRIBUTION.md": _attribution_markdown(),
        asset_root / "briefs" / "README.md": _briefs_readme(pipeline),
        asset_root / "workflows" / "README.md": _workflows_readme(),
    }
    for path, content in text_targets.items():
        if _write_text(path, content, force=force):
            created.append(path)

    return created


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Seed repo-local asset pipeline surfaces for game projects.")
    parser.add_argument("repo_root", help="Repository root to initialize.")
    parser.add_argument("--stack-label", default="")
    parser.add_argument("--deliverable-kind", default="")
    parser.add_argument("--placeholder-policy", default="")
    parser.add_argument("--content-source-plan", default="")
    parser.add_argument("--licensing-or-provenance-constraints", default="")
    parser.add_argument("--finish-acceptance-signals", default="")
    parser.add_argument("--force", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).expanduser().resolve()
    provenance = _read_bootstrap_provenance(repo_root)
    stack_label = _normalize_text(args.stack_label or str(provenance.get("stack_label", ""))) or "framework-agnostic"
    deliverable_kind = _contract_value(
        provenance,
        args.deliverable_kind,
        "deliverable_kind",
        "prototype unless the normalized brief records a stricter final product bar",
    )
    placeholder_policy = _contract_value(
        provenance,
        args.placeholder_policy,
        "placeholder_policy",
        "placeholder_ok unless the normalized brief records a stricter finish policy",
    )
    content_source_plan = _contract_value(
        provenance,
        args.content_source_plan,
        "content_source_plan",
        "record whether content is authored, licensed, procedural, mixed, or intentionally absent",
    )
    licensing_or_provenance_constraints = _contract_value(
        provenance,
        args.licensing_or_provenance_constraints,
        "licensing_or_provenance_constraints",
        "record any asset or content provenance constraints here",
    )
    finish_acceptance_signals = _contract_value(
        provenance,
        args.finish_acceptance_signals,
        "finish_acceptance_signals",
        "record the explicit finish-proof signals that must be met before the repo is treated as finished",
    )

    created = initialize_asset_pipeline(
        repo_root,
        stack_label=stack_label,
        deliverable_kind=deliverable_kind,
        placeholder_policy=placeholder_policy,
        content_source_plan=content_source_plan,
        licensing_or_provenance_constraints=licensing_or_provenance_constraints,
        finish_acceptance_signals=finish_acceptance_signals,
        force=args.force,
    )
    print(f"Initialized asset pipeline in {repo_root} ({len(created)} files written)")
    for path in created:
        print(f"- {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

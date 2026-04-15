"""Audit opencode.jsonc configuration for missing or incorrect fields.

Finding codes emitted:
  CONFIG001  model field missing or unparseable in opencode.jsonc
  CONFIG002  default_agent field missing from opencode.jsonc
  CONFIG003  external_directory permission not configured
  CONFIG004  common bash commands missing from permission allowlist
  CONFIG005  permission section missing entirely
  CONFIG006  model field missing
  CONFIG007  unsubstituted placeholder in model field
  CONFIG008  model field not in provider/model format
  CONFIG009  default_agent contains unsubstituted placeholder
  CONFIG010  missing asset-pipeline starter surfaces on a managed game repo
  CONFIG011  blender_agent enabled for a non-Blender asset route
  CONFIG012  blender_agent disabled for a Blender-required asset route
  CONFIG013  asset route metadata drift against the canonical finish contract
"""

from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
import json
import re
from dataclasses import dataclass
from pathlib import Path
import sys
from typing import Any

from shared_verifier_types import Finding

EXPECTED_BASH_COMMANDS = {
    "mkdir *",
    "echo *",
    "touch *",
    "cp *",
    "mv *",
}
ASSET_PIPELINE_INIT_PATH = (
    Path(__file__).resolve().parents[2] / "asset-pipeline" / "scripts" / "init_asset_pipeline.py"
)
ANDROID_SCAFFOLD_PATH = (
    Path(__file__).resolve().parents[2] / "repo-scaffold-factory" / "scripts" / "android_scaffold.py"
)
DEFAULT_FINISH_CONTRACT_FIELD_VALUES = {
    "deliverable_kind": "prototype unless the normalized brief records a stricter final product bar",
    "placeholder_policy": "placeholder_ok unless the normalized brief records a stricter finish policy",
    "visual_finish_target": "record the project-specific visual finish bar here, or state that no consumer-facing visual bar applies",
    "audio_finish_target": "record the project-specific audio finish bar here, or state that no audio bar applies",
    "content_source_plan": "record whether content is authored, licensed, procedural, mixed, or intentionally absent",
    "licensing_or_provenance_constraints": "record any asset or content provenance constraints here",
    "finish_acceptance_signals": "record the explicit finish-proof signals that must be met before the repo is treated as finished",
}
FINISH_CONTRACT_FIELDS = tuple(DEFAULT_FINISH_CONTRACT_FIELD_VALUES.keys())


@dataclass
class ConfigSurfaceAuditContext:
    repo_root: Path
    findings: list[Finding]


def _load_module(name: str, path: Path):
    spec = spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module from {path}")
    module = module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


ASSET_PIPELINE_INIT = _load_module(
    "scafforge_asset_pipeline_init_for_audit",
    ASSET_PIPELINE_INIT_PATH,
)
ANDROID_SCAFFOLD = _load_module(
    "scafforge_android_scaffold_for_audit",
    ANDROID_SCAFFOLD_PATH,
)


def _strip_jsonc_comments(text: str) -> str:
    """Remove // and /* */ comments and trailing commas from JSONC content.

    Handles // inside strings (e.g. URLs) by tracking whether we are inside
    a JSON string literal.
    """
    import re
    # Remove block comments (non-greedy, may span lines)
    # Simple approach: only outside strings. For robustness, use a state machine.
    result_chars: list[str] = []
    i = 0
    in_string = False
    length = len(text)
    while i < length:
        c = text[i]
        if in_string:
            result_chars.append(c)
            if c == "\\" and i + 1 < length:
                i += 1
                result_chars.append(text[i])
            elif c == '"':
                in_string = False
            i += 1
        elif c == '"':
            in_string = True
            result_chars.append(c)
            i += 1
        elif c == "/" and i + 1 < length and text[i + 1] == "/":
            # Line comment — skip to end of line
            while i < length and text[i] != "\n":
                i += 1
        elif c == "/" and i + 1 < length and text[i + 1] == "*":
            # Block comment — skip to */
            i += 2
            while i + 1 < length and not (text[i] == "*" and text[i + 1] == "/"):
                i += 1
            i += 2  # skip */
        else:
            result_chars.append(c)
            i += 1
    result = "".join(result_chars)
    # Remove trailing commas before } or ]
    result = re.sub(r",\s*([}\]])", r"\1", result)
    return result


def _load_opencode_config(repo_root: Path) -> dict[str, Any] | None:
    config_path = repo_root / "opencode.jsonc"
    if not config_path.exists():
        return None
    try:
        raw = config_path.read_text(encoding="utf-8")
        cleaned = _strip_jsonc_comments(raw)
        return json.loads(cleaned)
    except (json.JSONDecodeError, OSError):
        return None


def _read_json(path: Path) -> Any:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def _finish_contract_field(brief_text: str, field: str) -> str | None:
    match = re.search(
        rf"^\s*-\s*{re.escape(field)}\s*:\s*(.+)$",
        brief_text,
        re.IGNORECASE | re.MULTILINE,
    )
    return match.group(1).strip() if match else None


def _finish_contract_value_is_placeholder(value: str | None) -> bool:
    lowered = " ".join((value or "").lower().split())
    return (
        not lowered
        or lowered.startswith("record ")
        or "__" in (value or "")
        or "unless the normalized brief records" in lowered
    )


def _infer_stack_label(repo_root: Path, provenance: dict[str, Any], brief_text: str) -> str:
    stack_label = str(provenance.get("stack_label", "")).strip() if isinstance(provenance, dict) else ""
    if stack_label and stack_label != "framework-agnostic":
        return stack_label
    lowered = brief_text.lower()
    if ANDROID_SCAFFOLD.repo_declares_godot_android(repo_root):
        if any(token in lowered for token in ("3d", "blender", "low-poly", "low poly", ".glb")):
            return "godot-3d-android-game"
        if any(token in lowered for token in ("2d", "sprite", "tilemap", "shader")):
            return "godot-2d-android-game"
        return "godot-android-game"
    return stack_label or "framework-agnostic"


def _effective_finish_contract(repo_root: Path) -> tuple[str, dict[str, str]]:
    provenance = _read_json(repo_root / ".opencode" / "meta" / "bootstrap-provenance.json")
    brief_text = _read_text(repo_root / "docs" / "spec" / "CANONICAL-BRIEF.md")
    stack_label = _infer_stack_label(repo_root, provenance if isinstance(provenance, dict) else {}, brief_text)
    payload: dict[str, str] = {}
    provenance_contract = (
        provenance.get("product_finish_contract")
        if isinstance(provenance, dict) and isinstance(provenance.get("product_finish_contract"), dict)
        else {}
    )
    for field in FINISH_CONTRACT_FIELDS:
        value = provenance_contract.get(field) if isinstance(provenance_contract, dict) else None
        if isinstance(value, str) and value.strip() and not _finish_contract_value_is_placeholder(value):
            payload[field] = value.strip()
        brief_value = _finish_contract_field(brief_text, field)
        if brief_value and (field not in payload or _finish_contract_value_is_placeholder(payload.get(field))):
            payload[field] = brief_value
        if field not in payload:
            payload[field] = DEFAULT_FINISH_CONTRACT_FIELD_VALUES[field]
    return stack_label, payload


def _primary_routes_from_pipeline(pipeline: dict[str, Any]) -> dict[str, str]:
    routes = pipeline.get("routes")
    if not isinstance(routes, dict):
        return {}
    primary_routes: dict[str, str] = {}
    for category, choice in routes.items():
        if not isinstance(category, str) or not isinstance(choice, dict):
            continue
        primary = choice.get("primary")
        if isinstance(primary, str) and primary.strip():
            primary_routes[category] = primary.strip()
    return primary_routes


def _asset_pipeline_findings(root: Path, config: dict[str, Any], findings: list[Finding]) -> None:
    if not ANDROID_SCAFFOLD.repo_declares_godot_android(root):
        return

    stack_label, finish_contract = _effective_finish_contract(root)
    pipeline_preview, bootstrap_preview = ASSET_PIPELINE_INIT.preview_asset_pipeline(
        stack_label=stack_label,
        deliverable_kind=finish_contract["deliverable_kind"],
        placeholder_policy=finish_contract["placeholder_policy"],
        content_source_plan=finish_contract["content_source_plan"],
        licensing_or_provenance_constraints=finish_contract["licensing_or_provenance_constraints"],
        finish_acceptance_signals=finish_contract["finish_acceptance_signals"],
    )
    expected_primary_routes = bootstrap_preview.get("routes", {})
    expected_blender = bootstrap_preview.get("requires_blender_mcp") is True

    missing_paths: list[str] = []
    invalid_paths: list[str] = []
    for relative in getattr(ASSET_PIPELINE_INIT, "ASSET_STARTER_PATHS", ()):
        path = root / relative
        if not path.exists():
            missing_paths.append(relative)
    for relative in getattr(ASSET_PIPELINE_INIT, "ASSET_JSON_PATHS", ()):
        payload = _read_json(root / relative)
        if payload is None:
            invalid_paths.append(relative)
    provenance_path = root / "assets" / "PROVENANCE.md"
    if provenance_path.exists():
        provenance_text = provenance_path.read_text(encoding="utf-8")
        if "| asset_path | source_or_workflow |" not in provenance_text:
            invalid_paths.append("assets/PROVENANCE.md")
    if missing_paths or invalid_paths:
        evidence: list[str] = []
        if missing_paths:
            evidence.append(f"Missing asset starter surfaces: {', '.join(missing_paths)}")
        if invalid_paths:
            evidence.append(f"Invalid asset starter surfaces: {', '.join(invalid_paths)}")
        findings.append(Finding(
            code="CONFIG010",
            severity="warning",
            problem="A managed game repo is missing canonical asset-pipeline starter surfaces.",
            root_cause="Legacy scaffold or repair runs did not propagate the deterministic asset route metadata and starter layout into the repo.",
            files=missing_paths or invalid_paths or ["assets/pipeline.json"],
            safer_pattern="Backfill the rendered asset starter surfaces from the current package during managed repair and keep them aligned to the canonical finish contract.",
            evidence=evidence,
            remediation_action="repair",
            remediation_target="assets/pipeline.json",
        ))

    actual_pipeline = _read_json(root / "assets/pipeline.json")
    actual_meta = _read_json(root / ".opencode/meta/asset-pipeline-bootstrap.json")
    actual_primary_routes = _primary_routes_from_pipeline(actual_pipeline) if isinstance(actual_pipeline, dict) else {}
    actual_meta_routes = actual_meta.get("routes") if isinstance(actual_meta, dict) and isinstance(actual_meta.get("routes"), dict) else {}
    if (
        actual_primary_routes
        and expected_primary_routes
        and actual_primary_routes != expected_primary_routes
    ) or (
        actual_meta_routes
        and expected_primary_routes
        and actual_meta_routes != expected_primary_routes
    ):
        findings.append(Finding(
            code="CONFIG013",
            severity="warning",
            problem="Asset route metadata drifts from the current canonical finish contract.",
            root_cause="The repo's seeded asset route metadata no longer matches the route implied by the canonical brief and should be regenerated by current Scafforge templates.",
            files=["assets/pipeline.json", ".opencode/meta/asset-pipeline-bootstrap.json"],
            safer_pattern="Regenerate machine-readable asset route metadata from the canonical finish contract during repair instead of preserving stale starter metadata.",
            evidence=[
                f"Expected primary routes: {expected_primary_routes}",
                f"assets/pipeline.json primary routes: {actual_primary_routes or '<missing>'}",
                f".opencode/meta/asset-pipeline-bootstrap.json routes: {actual_meta_routes or '<missing>'}",
            ],
            remediation_action="repair",
            remediation_target="assets/pipeline.json",
        ))

    mcp = config.get("mcp", {})
    if not isinstance(mcp, dict):
        mcp = {}
    blender_agent = mcp.get("blender_agent", {})
    if not isinstance(blender_agent, dict):
        blender_agent = {}
    blender_enabled = blender_agent.get("enabled")
    if expected_blender and blender_enabled is not True:
        findings.append(Finding(
            code="CONFIG012",
            severity="warning",
            problem="blender_agent is disabled even though the current asset route requires Blender-MCP.",
            root_cause="The generated OpenCode configuration did not stay aligned with the repo's canonical asset route metadata.",
            files=["opencode.jsonc"],
            safer_pattern="Enable blender_agent only when the inferred asset route requires Blender-MCP and the host exposes the required Blender MCP paths.",
            evidence=[
                f"Expected blender route: {expected_blender}",
                f"blender_agent.enabled = {blender_enabled!r}",
                f"Expected primary routes: {expected_primary_routes}",
            ],
            remediation_action="repair",
            remediation_target="opencode.jsonc",
        ))
    if not expected_blender and blender_enabled is True:
        findings.append(Finding(
            code="CONFIG011",
            severity="warning",
            problem="blender_agent is enabled for a repo whose current asset route does not require Blender-MCP.",
            root_cause="The generated OpenCode configuration is coupling Blender enablement to host discovery instead of the repo's canonical asset strategy.",
            files=["opencode.jsonc"],
            safer_pattern="Disable blender_agent for non-Blender routes even if Blender happens to be installed on the current host.",
            evidence=[
                f"Expected blender route: {expected_blender}",
                f"blender_agent.enabled = {blender_enabled!r}",
                f"Preview pipeline route mode: {pipeline_preview.get('route_mode')}",
                f"Expected primary routes: {expected_primary_routes}",
            ],
            remediation_action="repair",
            remediation_target="opencode.jsonc",
        ))


def run_config_surface_audits(root: Path, findings: list[Finding], ctx: ConfigSurfaceAuditContext) -> None:
    config = _load_opencode_config(root)
    config_file = "opencode.jsonc"

    if config is None:
        findings.append(Finding(
            code="CONFIG001",
            severity="error",
            problem="opencode.jsonc is missing or unparseable.",
            root_cause="The configuration file was not created during scaffold or has been corrupted.",
            files=[config_file],
            safer_pattern="Run scafforge-repair to regenerate opencode.jsonc from the current template.",
            evidence=["File missing or JSON parse failed"],
            remediation_action="repair",
            remediation_target=config_file,
        ))
        return

    # CONFIG006: model field missing
    model_value = config.get("model")
    if not isinstance(model_value, str) or not model_value.strip():
        findings.append(Finding(
            code="CONFIG006",
            severity="error",
            problem="opencode.jsonc is missing the 'model' field.",
            root_cause="The template used to scaffold this repo did not include a model assignment, "
                       "or repair has not yet propagated the updated template.",
            files=[config_file],
            safer_pattern="opencode.jsonc must contain a top-level 'model' field in provider/model format "
                          "(e.g. 'minimax-coding-plan/MiniMax-M2.7').",
            evidence=[f"Current config keys: {list(config.keys())}"],
            remediation_action="repair",
            remediation_target=config_file,
        ))
    elif "__" in model_value:
        # CONFIG007: unsubstituted placeholder in model field
        findings.append(Finding(
            code="CONFIG007",
            severity="error",
            problem=f"opencode.jsonc 'model' field contains unsubstituted placeholder: {model_value}",
            root_cause="Template placeholder substitution failed during scaffold or repair.",
            files=[config_file],
            safer_pattern="The model field must be a resolved provider/model string, not a placeholder.",
            evidence=[f"model = {model_value!r}"],
            remediation_action="repair",
            remediation_target=config_file,
        ))
    elif "/" not in model_value:
        # CONFIG008: model field not in provider/model format
        findings.append(Finding(
            code="CONFIG008",
            severity="warning",
            problem=f"opencode.jsonc 'model' field is not in provider/model format: {model_value}",
            root_cause="The model field should use provider/model format (e.g. 'minimax-coding-plan/MiniMax-M2.7') "
                       "for correct provider routing.",
            files=[config_file],
            safer_pattern="Use 'provider/model' format for the model field.",
            evidence=[f"model = {model_value!r}"],
            remediation_action="repair",
            remediation_target=config_file,
        ))

    # CONFIG002: default_agent field
    agent_value = config.get("default_agent")
    if not isinstance(agent_value, str) or not agent_value.strip():
        findings.append(Finding(
            code="CONFIG002",
            severity="error",
            problem="opencode.jsonc is missing the 'default_agent' field.",
            root_cause="The template used to scaffold this repo did not include a default_agent assignment. "
                       "Without this, opencode falls back to the built-in 'build' agent instead of the "
                       "project's team-leader.",
            files=[config_file],
            safer_pattern="opencode.jsonc must contain a top-level 'default_agent' field pointing to "
                          "the team-leader agent (e.g. 'myproject-team-leader').",
            evidence=[f"Current config keys: {list(config.keys())}"],
            remediation_action="repair",
            remediation_target=config_file,
        ))
    elif "__" in agent_value:
        findings.append(Finding(
            code="CONFIG009",
            severity="error",
            problem=f"opencode.jsonc 'default_agent' contains unsubstituted placeholder: {agent_value}",
            root_cause="Template placeholder substitution failed during scaffold or repair.",
            files=[config_file],
            safer_pattern="The default_agent field must be a resolved agent name, not a placeholder.",
            evidence=[f"default_agent = {agent_value!r}"],
            remediation_action="repair",
            remediation_target=config_file,
        ))

    # CONFIG003: external_directory permission
    permission = config.get("permission", {})
    if not isinstance(permission, dict):
        permission = {}

    ext_dir = permission.get("external_directory")
    if ext_dir != "allow":
        findings.append(Finding(
            code="CONFIG003",
            severity="warning",
            problem="opencode.jsonc does not grant 'external_directory' permission.",
            root_cause="Without external_directory: allow, agents running in non-interactive mode "
                       "cannot access system tooling paths (JDK, Godot templates, Android SDK, etc.). "
                       "This causes auto-rejection of external path reads.",
            files=[config_file],
            safer_pattern="Add '\"external_directory\": \"allow\"' to the permission block in opencode.jsonc.",
            evidence=[f"permission.external_directory = {ext_dir!r}"],
            remediation_action="repair",
            remediation_target=config_file,
        ))

    # CONFIG004: common bash commands
    bash_perms = permission.get("bash", {})
    if not isinstance(bash_perms, dict):
        bash_perms = {}

    allowed_commands = {k for k, v in bash_perms.items() if v == "allow"}

    # CONFIG005: wildcard bash allow overrides all per-command denials
    if bash_perms.get("*") == "allow":
        findings.append(Finding(
            code="CONFIG005",
            severity="error",
            problem="opencode.jsonc bash permission wildcard '*' is set to 'allow', overriding all per-command denials.",
            root_cause="A wildcard allow in the bash permission block effectively disables the allowlist. "
                       "The template uses '\"*\": \"deny\"' as the default and only allows specific commands.",
            files=[config_file],
            safer_pattern="Set '\"*\": \"deny\"' in the bash permission block and allow specific commands explicitly.",
            evidence=[f"bash permissions: {list(bash_perms.keys())[:10]}"],
            remediation_action="repair",
            remediation_target=config_file,
        ))

    missing_commands = EXPECTED_BASH_COMMANDS - allowed_commands
    if missing_commands:
        findings.append(Finding(
            code="CONFIG004",
            severity="warning",
            problem=f"opencode.jsonc bash permissions missing common commands: {sorted(missing_commands)}",
            root_cause="The template used to scaffold this repo had a limited bash allowlist. "
                       "Agents need mkdir, cp, mv, etc. to create build directories and manage files.",
            files=[config_file],
            safer_pattern="Add the missing commands to the bash permission allowlist in opencode.jsonc.",
            evidence=[f"Missing: {sorted(missing_commands)}", f"Present: {sorted(allowed_commands)}"],
            remediation_action="repair",
            remediation_target=config_file,
        ))

    _asset_pipeline_findings(root, config, findings)

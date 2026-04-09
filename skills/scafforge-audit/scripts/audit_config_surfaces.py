"""Audit opencode.jsonc configuration for missing or incorrect fields.

Finding codes emitted:
  CONFIG001  model field missing from opencode.jsonc
  CONFIG002  default_agent field missing from opencode.jsonc
  CONFIG003  external_directory permission not configured
  CONFIG004  common bash commands missing from permission allowlist
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from shared_verifier_types import Finding

EXPECTED_BASH_COMMANDS = {
    "mkdir *",
    "echo *",
    "touch *",
    "cp *",
    "mv *",
}


@dataclass
class ConfigSurfaceAuditContext:
    repo_root: Path
    findings: list[Finding]


def _strip_jsonc_comments(text: str) -> str:
    """Remove // and /* */ comments and trailing commas from JSONC content."""
    import re
    # Remove block comments (non-greedy, may span lines)
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
    lines = []
    for line in text.splitlines():
        stripped = line.lstrip()
        if stripped.startswith("//"):
            continue
        comment_pos = line.find("//")
        if comment_pos >= 0:
            prefix = line[:comment_pos]
            if prefix.count('"') % 2 == 0:
                line = prefix.rstrip()
        lines.append(line)
    result = "\n".join(lines)
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

    # CONFIG001: model field
    model_value = config.get("model")
    if not isinstance(model_value, str) or not model_value.strip():
        findings.append(Finding(
            code="CONFIG001",
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
        findings.append(Finding(
            code="CONFIG001",
            severity="error",
            problem=f"opencode.jsonc 'model' field contains unsubstituted placeholder: {model_value}",
            root_cause="Template placeholder substitution failed during scaffold or repair.",
            files=[config_file],
            safer_pattern="The model field must be a resolved provider/model string, not a placeholder.",
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
            code="CONFIG002",
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

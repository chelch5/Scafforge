from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOOTSTRAP = ROOT / "skills" / "repo-scaffold-factory" / "scripts" / "bootstrap_repo_scaffold.py"
CHECKLIST = ROOT / "skills" / "repo-scaffold-factory" / "references" / "opencode-conformance-checklist.json"
AUDIT = ROOT / "skills" / "scafforge-audit" / "scripts" / "audit_repo_process.py"
REPAIR = ROOT / "skills" / "scafforge-repair" / "scripts" / "apply_repo_process_repair.py"
PUBLIC_REPAIR = ROOT / "skills" / "scafforge-repair" / "scripts" / "run_managed_repair.py"
REGENERATE = ROOT / "skills" / "scafforge-repair" / "scripts" / "regenerate_restart_surfaces.py"


def run(command: list[str], cwd: Path, *, env: dict[str, str] | None = None) -> None:
    result = subprocess.run(command, cwd=cwd, check=False, capture_output=True, text=True, env=env)
    if result.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(command)}\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}")


def run_json(command: list[str], cwd: Path, *, env: dict[str, str] | None = None) -> dict:
    result = subprocess.run(command, cwd=cwd, check=False, capture_output=True, text=True, env=env)
    if result.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(command)}\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}")
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Command did not return valid JSON: {' '.join(command)}\nSTDOUT:\n{result.stdout}") from exc


def seed_uv_python_fixture(
    dest: Path,
    *,
    dependency_block: list[str] | None = None,
    include_pytest_tool_config: bool = False,
) -> None:
    dependency_lines = dependency_block or [
        "[project.optional-dependencies]",
        'dev = ["pytest>=8.0.0"]',
    ]
    pyproject_lines = [
        "[project]",
        'name = "smoke-python"',
        'version = "0.1.0"',
        'requires-python = ">=3.11"',
        "",
        *dependency_lines,
        "",
    ]
    if include_pytest_tool_config:
        pyproject_lines.extend(
            [
                "[tool.pytest.ini_options]",
                'pythonpath = ["src"]',
                "",
            ]
        )

    (dest / "pyproject.toml").write_text(
        "\n".join(pyproject_lines) + "\n",
        encoding="utf-8",
    )
    (dest / "uv.lock").write_text("version = 1\n", encoding="utf-8")
    venv_dir = dest / ".venv"
    venv_dir.mkdir(parents=True, exist_ok=True)
    (venv_dir / "pyvenv.cfg").write_text(
        "\n".join(
            [
                "home = /usr/bin",
                "implementation = CPython",
                "uv = 0.10.12",
                "version_info = 3.12.3",
                "include-system-site-packages = false",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def seed_dependency_group_python_fixture(dest: Path) -> None:
    seed_uv_python_fixture(
        dest,
        dependency_block=[
            "[dependency-groups]",
            'dev = ["pytest>=8.0.0"]',
        ],
    )


def seed_uv_native_dev_dependency_fixture(dest: Path) -> None:
    seed_uv_python_fixture(
        dest,
        dependency_block=[
            "[tool.uv.dev-dependencies]",
            'pytest = ">=8.0.0"',
        ],
    )


def seed_bootstrap_deadlock(dest: Path) -> None:
    workflow_path = dest / ".opencode" / "state" / "workflow-state.json"
    workflow = json.loads(workflow_path.read_text(encoding="utf-8"))
    artifact_rel = ".opencode/state/bootstrap/synthetic-bootstrap-deadlock.md"
    artifact_path = dest / artifact_rel
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    artifact_path.write_text(
        "\n".join(
            [
                "# Environment Bootstrap",
                "",
                "## Missing Prerequisites",
                "",
                "- None",
                "",
                "## Commands",
                "",
                "### 1. pip install editable project",
                "",
                "- command: `python3 -m pip install -e .`",
                "",
                "#### stderr",
                "",
                "~~~~text",
                "/usr/bin/python3: No module named pip",
                "~~~~",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    workflow["bootstrap"] = {
        "status": "failed",
        "last_verified_at": "2026-03-25T00:23:01Z",
        "environment_fingerprint": "synthetic-bootstrap-deadlock",
        "proof_artifact": artifact_rel,
    }
    workflow_path.write_text(json.dumps(workflow, indent=2) + "\n", encoding="utf-8")


def seed_legacy_bootstrap_tool(dest: Path) -> None:
    tool_path = dest / ".opencode" / "tools" / "environment_bootstrap.ts"
    tool_path.write_text(
        "\n".join(
            [
                'import { tool } from "@opencode-ai/plugin"',
                "",
                "export default tool({",
                '  description: "legacy bootstrap fixture",',
                "  args: {},",
                "  async execute() {",
                '    const command = { argv: ["python3", "-m", "pip", "install", "-e", "."] }',
                "    return JSON.stringify(command)",
                "  },",
                "})",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def seed_legacy_model_drift(dest: Path) -> None:
    legacy_minimax = "minimax-coding-plan/" + "MiniMax-M2." + "5"

    profile_dir = dest / ".opencode" / "skills" / "model-operating-profile"
    shutil.rmtree(profile_dir, ignore_errors=True)

    provenance_path = dest / ".opencode" / "meta" / "bootstrap-provenance.json"
    provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
    provenance["runtime_models"] = {
        "provider": "minimax-coding-plan",
        "planner": legacy_minimax,
        "implementer": legacy_minimax,
        "utility": legacy_minimax,
    }
    provenance_path.write_text(json.dumps(provenance, indent=2) + "\n", encoding="utf-8")

    (dest / "docs" / "process" / "model-matrix.md").write_text(
        "\n".join(
            [
                "# Model Matrix",
                "",
                "- provider: `minimax-coding-plan`",
                f"- team lead / planner / reviewers: `{legacy_minimax}`",
                f"- implementer: `{legacy_minimax}`",
                f"- utilities, docs, and QA helpers: `{legacy_minimax}`",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (dest / "START-HERE.md").write_text(
        (dest / "START-HERE.md").read_text(encoding="utf-8").replace("openrouter/openai/gpt-5-mini", legacy_minimax),
        encoding="utf-8",
    )
    (dest / "docs" / "spec" / "CANONICAL-BRIEF.md").write_text(
        (dest / "docs" / "spec" / "CANONICAL-BRIEF.md").read_text(encoding="utf-8").replace("openrouter/openai/gpt-5-mini", legacy_minimax),
        encoding="utf-8",
    )
    team_leader = next((dest / ".opencode" / "agents").glob("*team-leader*.md"))
    team_text = team_leader.read_text(encoding="utf-8")
    team_text = team_text.replace("temperature: 1.0", "temperature: 0.2")
    team_text = team_text.replace("top_p: 0.95", "top_p: 0.7")
    if "top_k: 40\n" in team_text:
        team_text = team_text.replace("top_k: 40\n", "")
    team_text = team_text.replace("model: openrouter/anthropic/claude-sonnet-4.5", f"model: {legacy_minimax}")
    team_leader.write_text(team_text, encoding="utf-8")


def seed_failed_repair_cycle(dest: Path, diagnosis_pack: Path) -> None:
    manifest_path = diagnosis_pack / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["ticket_recommendations"] = [
        {
            "source_finding_code": "SKILL001",
            "route": "scafforge-repair",
            "title": "Regenerate placeholder repo-local skills",
        }
    ]
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    provenance_path = dest / ".opencode" / "meta" / "bootstrap-provenance.json"
    provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
    repair_history = provenance.setdefault("repair_history", [])
    repair_history.append(
        {
            "repaired_at": "2099-01-01T00:00:00Z",
            "summary": "Synthetic repair pass after diagnosis that left placeholder skills in place",
        }
    )
    provenance_path.write_text(json.dumps(provenance, indent=2) + "\n", encoding="utf-8")


def seed_workflow_overclaim(dest: Path) -> Path:
    manifest_path = dest / "tickets" / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    active_ticket = manifest["active_ticket"]
    manifest["tickets"].append(
        {
            "id": "WFLOW-DEP",
            "title": "Synthetic dependent ticket",
            "wave": 99,
            "lane": "workflow",
            "parallel_safe": True,
            "overlap_risk": "low",
            "stage": "planning",
            "status": "ready",
            "depends_on": [active_ticket],
            "summary": "Synthetic dependent ticket for handoff overclaim coverage.",
            "acceptance": ["Dependency claim remains blocked until the active ticket is done."],
            "decision_blockers": [],
            "artifacts": [],
            "resolution_state": "open",
            "verification_state": "suspect",
            "follow_up_ticket_ids": [],
        }
    )
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    overclaim = (
        "Active work is only blocked by a tool/env mismatch, not a code defect. "
        "The downstream dependency is now unblocked and ready to proceed."
    )
    for relative in ("START-HERE.md", ".opencode/state/latest-handoff.md"):
        path = dest / relative
        original = path.read_text(encoding="utf-8") if path.exists() else (dest / "START-HERE.md").read_text(encoding="utf-8")
        path.parent.mkdir(parents=True, exist_ok=True)
        if "## Next Action" in original:
            updated = original.replace("## Next Action", f"## Next Action\n\n{overclaim}\n")
        else:
            updated = original.rstrip() + f"\n\n## Next Action\n\n{overclaim}\n"
        path.write_text(updated, encoding="utf-8")

    log_path = dest / "session-log.md"
    log_path.write_text(
        "\n".join(
            [
                "Active ticket: `EXEC-001` — stage `planning`, status `ready`.",
                "`approved_plan: false`",
                "Cannot move EXEC-005 to implementation before it passes through plan_review.",
                "Cannot move EXEC-005 to implementation before it passes through plan_review.",
                'Workaround needed again — using the `todo` bypass: {"stage": "todo"}',
                "Unable to run verification commands — The bash tool is blocked by permission rules in this environment.",
                "Result: PASS (scoped)",
                "Verified by running the scoped command above",
                "Later evidence: 126 tests collected and the service imports cleanly.",
                "Final summary: tool/env mismatch, not a code defect. EXEC-002 is now unblocked.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return log_path


def seed_legacy_smoke_test_tool(dest: Path) -> None:
    tool_path = dest / ".opencode" / "tools" / "smoke_test.ts"
    tool_path.write_text(
        "\n".join(
            [
                'import { tool } from "@opencode-ai/plugin"',
                "",
                "export default tool({",
                '  description: "legacy smoke-test fixture",',
                "  args: {},",
                "  async execute() {",
                '    return JSON.stringify({ argv: [\"python3\", \"-m\", \"pytest\"] })',
                "  },",
                "})",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def seed_legacy_smoke_override_tool(dest: Path) -> None:
    tool_path = dest / ".opencode" / "tools" / "smoke_test.ts"
    tool_path.write_text(
        "\n".join(
            [
                'import { tool } from "@opencode-ai/plugin"',
                "",
                "type CommandSpec = {",
                "  argv: string[]",
                "}",
                "",
                "async function detectCommands(args: { command_override?: string[] }): Promise<CommandSpec[]> {",
                "  if (Array.isArray(args.command_override) && args.command_override.length > 0) {",
                "    return [{ argv: args.command_override }]",
                "  }",
                '  return [{ argv: ["uv", "run", "python", "-m", "pytest"] }]',
                "}",
                "",
                "export default tool({",
                '  description: "legacy smoke override fixture",',
                "  args: {",
                "    command_override: tool.schema.array(tool.schema.string()).optional(),",
                "  },",
                "  async execute(args) {",
                "    const commands = await detectCommands(args)",
                "    return JSON.stringify(commands)",
                "  },",
                "})",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def seed_legacy_smoke_acceptance_tool(dest: Path) -> None:
    tool_path = dest / ".opencode" / "tools" / "smoke_test.ts"
    tool_path.write_text(
        "\n".join(
            [
                'import { tool } from "@opencode-ai/plugin"',
                "",
                "type CommandSpec = {",
                "  argv: string[]",
                "}",
                "",
                "async function detectCommands(args: { test_paths?: string[] }): Promise<CommandSpec[]> {",
                "  const testTargets = Array.isArray(args.test_paths) ? args.test_paths : []",
                "  return [{ argv: ['uv', 'run', 'python', '-m', 'pytest', ...testTargets] }]",
                "}",
                "",
                "export default tool({",
                '  description: "legacy smoke acceptance fixture",',
                "  args: {",
                "    test_paths: tool.schema.array(tool.schema.string()).optional(),",
                "  },",
                "  async execute(args) {",
                "    const commands = await detectCommands(args)",
                "    return JSON.stringify(commands)",
                "  },",
                "})",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def seed_legacy_review_contract(dest: Path) -> None:
    workflow_doc = dest / "docs" / "process" / "workflow.md"
    workflow_text = workflow_doc.read_text(encoding="utf-8")
    workflow_text = workflow_text.replace("`todo`, `ready`, `plan_review`, `in_progress`, `blocked`, `review`, `qa`, `smoke_test`, `done`", "`todo`, `ready`, `in_progress`, `blocked`, `review`, `qa`, `smoke_test`, `done`")
    workflow_text = workflow_text.replace("`plan_review`", "plan review")
    workflow_text = workflow_text.replace("the assigned ticket must already be in plan review and ", "")
    workflow_doc.write_text(workflow_text, encoding="utf-8")
    workflow_tool = dest / ".opencode" / "lib" / "workflow.ts"
    workflow_tool.write_text(workflow_tool.read_text(encoding="utf-8").replace('"plan_review"', '"review"'), encoding="utf-8")


def seed_legacy_stage_transition_contract(dest: Path) -> None:
    ticket_update = dest / ".opencode" / "tools" / "ticket_update.ts"
    ticket_text = ticket_update.read_text(encoding="utf-8")
    ticket_text = ticket_text.replace('ticket.stage !== "plan_review"', 'ticket.status !== "plan_review"')
    ticket_text = ticket_text.replace("const requested = resolveRequestedTicketProgress(ticket, { stage: args.stage, status: args.status })", "const requested = { stage: args.stage || ticket.stage, status: args.status || ticket.status }")
    ticket_text = ticket_text.replace(
        "    const lifecycleBlocker = validateLifecycleStageStatus(targetStage, targetStatus)\n    if (lifecycleBlocker) {\n      throw new Error(lifecycleBlocker)\n    }\n",
        "",
    )
    ticket_update.write_text(ticket_text, encoding="utf-8")

    workflow_tool = dest / ".opencode" / "lib" / "workflow.ts"
    workflow_text = workflow_tool.read_text(encoding="utf-8")
    workflow_text = workflow_text.replace('export const LIFECYCLE_STAGES = new Set(["planning", "plan_review", "implementation", "review", "qa", "smoke-test", "closeout"])\n', "")
    workflow_text = workflow_text.replace(
        '    return `Unsupported ticket stage: ${stage}. Use planning, plan_review, implementation, review, qa, smoke-test, or closeout.`\n',
        "    return null\n",
    )
    workflow_tool.write_text(workflow_text, encoding="utf-8")

    stage_gate = dest / ".opencode" / "plugins" / "stage-gate-enforcer.ts"
    stage_gate_text = stage_gate.read_text(encoding="utf-8")
    stage_gate_text = stage_gate_text.replace('ticket.stage !== "plan_review"', 'ticket.status !== "plan_review"')
    stage_gate_text = stage_gate_text.replace("resolveRequestedTicketProgress,\n", "")
    stage_gate_text = stage_gate_text.replace("validateLifecycleStageStatus,\n", "")
    stage_gate_text = stage_gate_text.replace(
        "        const requested = resolveRequestedTicketProgress(ticket, {\n          stage: typeof output.args.stage === \"string\" ? output.args.stage : undefined,\n          status: typeof output.args.status === \"string\" ? output.args.status : undefined,\n        })\n        const lifecycleBlocker = validateLifecycleStageStatus(requested.stage, requested.status)\n        if (lifecycleBlocker) {\n          throw new Error(lifecycleBlocker)\n        }\n",
        "        const requested = {\n          stage: typeof output.args.stage === \"string\" ? output.args.stage : ticket.stage,\n          status: typeof output.args.status === \"string\" ? output.args.status : ticket.status,\n        }\n",
    )
    stage_gate.write_text(stage_gate_text, encoding="utf-8")


def seed_smoke_artifact_bypass(dest: Path) -> None:
    artifact_write = dest / ".opencode" / "tools" / "artifact_write.ts"
    artifact_write.write_text(
        artifact_write.read_text(encoding="utf-8").replace(
            "Write the full body for a canonical planning, implementation, review, or QA artifact.",
            "Write the full body for a canonical planning, implementation, review, QA, or smoke-test artifact.",
        ),
        encoding="utf-8",
    )

    artifact_register = dest / ".opencode" / "tools" / "artifact_register.ts"
    artifact_register.write_text(
        artifact_register.read_text(encoding="utf-8").replace(
            "Register an existing canonical planning, implementation, review, or QA artifact.",
            "Register an existing canonical planning, implementation, review, QA, or smoke-test artifact.",
        ),
        encoding="utf-8",
    )

    stage_gate = dest / ".opencode" / "plugins" / "stage-gate-enforcer.ts"
    stage_gate_text = stage_gate.read_text(encoding="utf-8")
    stage_gate_text = stage_gate_text.replace('const RESERVED_ARTIFACT_STAGES = new Set(["smoke-test"])\n', "")
    stage_gate_text = stage_gate_text.replace(
        "        if (RESERVED_ARTIFACT_STAGES.has(stage)) {\n          const owner = stage === \"smoke-test\" ? \"smoke_test\" : \"handoff_publish\"\n          throw new Error(`Use ${owner} to create ${stage} artifacts. Generic artifact_register is not allowed for that stage.`)\n        }\n\n",
        "",
    )
    stage_gate_text = stage_gate_text.replace(
        "        if (RESERVED_ARTIFACT_STAGES.has(stage)) {\n          const owner = stage === \"smoke-test\" ? \"smoke_test\" : \"handoff_publish\"\n          throw new Error(`Use ${owner} to create ${stage} artifacts. Generic artifact_write is not allowed for that stage.`)\n        }\n",
        "",
    )
    stage_gate.write_text(stage_gate_text, encoding="utf-8")

    ticket_lookup = dest / ".opencode" / "tools" / "ticket_lookup.ts"
    ticket_lookup.write_text(
        ticket_lookup.read_text(encoding="utf-8").replace(
            "Use the smoke_test tool to produce the current smoke-test artifact. Do not fabricate a PASS artifact through generic artifact tools.",
            "Use a smoke-test artifact to record current results.",
        ),
        encoding="utf-8",
    )


def seed_handoff_ownership_conflict(dest: Path) -> None:
    stage_gate = dest / ".opencode" / "plugins" / "stage-gate-enforcer.ts"
    stage_gate.write_text(
        stage_gate.read_text(encoding="utf-8").replace(
            'const RESERVED_ARTIFACT_STAGES = new Set(["smoke-test"])',
            'const RESERVED_ARTIFACT_STAGES = new Set(["smoke-test", "handoff"])',
        ),
        encoding="utf-8",
    )


def seed_recovered_verification_log(dest: Path) -> Path:
    log_path = dest / "recovered-session-log.md"
    log_path.write_text(
        "\n".join(
            [
                "Unable to run verification commands — The bash tool is blocked by permission rules in this environment.",
                "Bootstrap was repaired and validation was retried.",
                "SYNTAX OK",
                "12 passed in 0.42s",
                "Result: PASS (scoped)",
                "Verified by running the recovery command above.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return log_path


def seed_coordinator_artifact_log(dest: Path) -> Path:
    log_path = dest / "coordinator-authorship-log.md"
    log_path.write_text(
        "\n".join(
            [
                "## Assistant (Smoke-Team-Leader · MiniMax-M2.7 · 5.0s)",
                "",
                "**Tool: artifact_write**",
                "",
                "**Input:**",
                "```json",
                '{"ticket_id":"EXEC-005","path":".opencode/state/implementations/exec-005-implementation-implementation.md","kind":"implementation","stage":"implementation","content":"# impl"}',
                "```",
                "",
                "## Assistant (Smoke-Team-Leader · MiniMax-M2.7 · 4.0s)",
                "",
                "**Tool: artifact_write**",
                "",
                "**Input:**",
                "```json",
                '{"ticket_id":"EXEC-005","path":".opencode/state/qa/exec-005-qa-qa.md","kind":"qa","stage":"qa","content":"# qa"}',
                "```",
                "",
                "## Assistant (Smoke-Team-Leader · MiniMax-M2.7 · 3.8s)",
                "",
                "**Tool: artifact_write**",
                "",
                "**Input:**",
                "```json",
                '{"ticket_id":"EXEC-005","path":".opencode/state/smoke-tests/exec-005-smoke-test-smoke-test.md","kind":"smoke-test","stage":"smoke-test","content":"# smoke"}',
                "```",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return log_path


def write_python_wrapper(path: Path, *, allow_pytest: bool) -> None:
    real_python = sys.executable
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                f"#!{real_python}",
                "import subprocess",
                "import sys",
                f"REAL_PYTHON = {real_python!r}",
                "args = sys.argv[1:]",
                f"ALLOW_PYTEST = {allow_pytest!r}",
                'if not ALLOW_PYTEST and len(args) >= 2 and args[0] == "-m" and args[1] == "pytest":',
                "    sys.exit(1)",
                "raise SystemExit(subprocess.run([REAL_PYTHON, *args], check=False).returncode)",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    path.chmod(0o755)


def seed_failing_pytest_suite(dest: Path) -> None:
    seed_uv_python_fixture(dest)
    src_pkg = dest / "src" / "smoke_pkg"
    src_pkg.mkdir(parents=True, exist_ok=True)
    (src_pkg / "__init__.py").write_text("__all__ = ['ok']\n", encoding="utf-8")
    tests_dir = dest / "tests"
    tests_dir.mkdir(parents=True, exist_ok=True)
    (tests_dir / "test_sample.py").write_text("def test_smoke():\n    assert True\n", encoding="utf-8")

    venv_bin = dest / ".venv" / "bin"
    venv_bin.mkdir(parents=True, exist_ok=True)
    write_python_wrapper(venv_bin / "python", allow_pytest=True)
    (venv_bin / "pytest").write_text(
        "\n".join(
            [
                f"#!{sys.executable}",
                "import sys",
                "args = sys.argv[1:]",
                'if "--version" in args:',
                '    print("pytest 8.1.0")',
                "    raise SystemExit(0)",
                'if "--collect-only" in args:',
                '    print("2 tests collected")',
                "    raise SystemExit(0)",
                'print("1 failed, 1 passed in 0.10s")',
                "raise SystemExit(1)",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (venv_bin / "pytest").chmod(0o755)


def seed_missing_pytest_env(dest: Path) -> None:
    seed_uv_python_fixture(dest)
    src_pkg = dest / "src" / "smoke_pkg"
    src_pkg.mkdir(parents=True, exist_ok=True)
    (src_pkg / "__init__.py").write_text("__all__ = ['ok']\n", encoding="utf-8")
    tests_dir = dest / "tests"
    tests_dir.mkdir(parents=True, exist_ok=True)
    (tests_dir / "test_sample.py").write_text("def test_smoke():\n    assert True\n", encoding="utf-8")
    write_python_wrapper(dest / ".venv" / "bin" / "python", allow_pytest=False)


def seed_pyproject_only_pytest_env(dest: Path) -> None:
    seed_uv_python_fixture(dest, include_pytest_tool_config=True)
    src_pkg = dest / "src" / "smoke_pkg"
    src_pkg.mkdir(parents=True, exist_ok=True)
    (src_pkg / "__init__.py").write_text("__all__ = ['ok']\n", encoding="utf-8")
    write_python_wrapper(dest / ".venv" / "bin" / "python", allow_pytest=False)


def seed_helper_tool_exposure(dest: Path) -> None:
    helper_tool = dest / ".opencode" / "tools" / "_workflow.ts"
    helper_tool.write_text(
        "\n".join(
            [
                'export function _workflow_validateHandoffNextAction() {',
                "  return null",
                "}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def seed_helper_tool_failure_log(dest: Path) -> Path:
    log_path = dest / "helper-tool-failure-log.md"
    log_path.write_text(
        "\n".join(
            [
                "Available tools: ticket_lookup, handoff_publish, _workflow_validateHandoffNextAction",
                "",
                "## Assistant (Smoke-Team-Leader · MiniMax-M2.7 · 2.0s)",
                "",
                "**Tool: _workflow_validateHandoffNextAction**",
                "",
                "**Input:**",
                "```json",
                '{"ticket_id":"SETUP-001"}',
                "```",
                "",
                "**Error:**",
                "```text",
                "TypeError: def.execute is not a function",
                "```",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return log_path


def seed_smoke_override_failure_log(dest: Path) -> Path:
    log_path = dest / "smoke-override-failure-log.md"
    log_path.write_text(
        "\n".join(
            [
                "## Assistant (Smoke-Team-Leader · MiniMax-M2.7 · 2.1s)",
                "",
                "**Tool: smoke_test**",
                "",
                "**Input:**",
                "```json",
                '{"ticket_id":"EXEC-008","scope":"ticket","command_override":["UV_CACHE_DIR=/tmp/uv-cache","uv","run","pytest","tests/hub/test_security.py","-q","--tb=no"]}',
                "```",
                "",
                "**Output:**",
                "```json",
                '{"ticket_id":"EXEC-008","passed":false,"failure_classification":"environment","blocker":"Error: ENOENT: no such file or directory, posix_spawn \\"UV_CACHE_DIR=/tmp/uv-cache\\""}',
                "```",
                "",
                "Artifact note: Error: ENOENT: no such file or directory, posix_spawn 'UV_CACHE_DIR=/tmp/uv-cache'",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return log_path


def seed_smoke_acceptance_scope_log(dest: Path) -> Path:
    log_path = dest / "smoke-acceptance-scope-log.md"
    log_path.write_text(
        "\n".join(
            [
                "Acceptance criterion:",
                "`UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/hub/test_security.py -q --tb=no` exits 0.",
                "",
                "## Assistant (Smoke-Team-Leader · MiniMax-M2.7 · 5.0s)",
                "",
                "**Tool: smoke_test**",
                "",
                "**Input:**",
                "```json",
                '{"ticket_id":"EXEC-008","scope":"targeted","test_paths":["tests/hub/test_security.py"]}',
                "```",
                "",
                "**Output:**",
                "```json",
                '{"ticket_id":"EXEC-008","passed":false,"failure_classification":"ticket","commands":[{"label":"python compileall","command":"uv run python -m compileall -q -x (^|/)(\\\\.git|\\\\.opencode)(/|$) .","exit_code":0,"duration_ms":100},{"label":"pytest","command":"uv run python -m pytest tests/hub/test_security.py","exit_code":1,"duration_ms":2500}]}',
                "```",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return log_path


def seed_pending_process_verification(dest: Path) -> None:
    manifest_path = dest / "tickets" / "manifest.json"
    workflow_path = dest / ".opencode" / "state" / "workflow-state.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    workflow = json.loads(workflow_path.read_text(encoding="utf-8"))
    ticket = manifest["tickets"][0]
    ticket["stage"] = "closeout"
    ticket["status"] = "done"
    ticket["resolution_state"] = "done"
    ticket["verification_state"] = "suspect"
    ticket["artifacts"] = [
        {
            "kind": "smoke-test",
            "stage": "smoke-test",
            "path": ".opencode/state/artifacts/history/demo/smoke-test/demo.md",
            "summary": "legacy smoke proof",
            "created_at": "2026-03-20T00:00:00Z",
            "trust_state": "current",
        }
    ]
    manifest["active_ticket"] = ticket["id"]
    workflow["active_ticket"] = ticket["id"]
    workflow["stage"] = "closeout"
    workflow["status"] = "done"
    workflow["pending_process_verification"] = True
    workflow["process_last_changed_at"] = "2026-03-25T00:00:00Z"
    workflow_path.write_text(json.dumps(workflow, indent=2) + "\n", encoding="utf-8")
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def seed_restart_surface_drift(dest: Path) -> None:
    manifest_path = dest / "tickets" / "manifest.json"
    workflow_path = dest / ".opencode" / "state" / "workflow-state.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    workflow = json.loads(workflow_path.read_text(encoding="utf-8"))
    ticket = manifest["tickets"][0]
    proof_rel = ".opencode/state/bootstrap/synthetic-bootstrap-proof.md"
    proof_path = dest / proof_rel
    proof_path.parent.mkdir(parents=True, exist_ok=True)
    proof_path.write_text("# Bootstrap Proof\n", encoding="utf-8")

    workflow["bootstrap"] = {
        "status": "failed",
        "last_verified_at": "2026-03-25T23:02:26Z",
        "environment_fingerprint": "synthetic-bootstrap",
        "proof_artifact": proof_rel,
    }
    workflow["pending_process_verification"] = True
    workflow["state_revision"] = 122
    workflow["lane_leases"] = [
        {
            "ticket_id": ticket["id"],
            "lane": ticket["lane"],
            "owner_agent": "synthetic-team-leader",
            "write_lock": True,
            "claimed_at": "2026-03-25T23:00:24Z",
            "allowed_paths": ["."],
        }
    ]
    workflow_path.write_text(json.dumps(workflow, indent=2) + "\n", encoding="utf-8")

    (dest / "START-HERE.md").write_text(
        "\n".join(
            [
                "# START HERE",
                "",
                "<!-- SCAFFORGE:START_HERE_BLOCK START -->",
                "## What This Repo Is",
                "",
                "Smoke Example",
                "",
                "## Current Or Next Ticket",
                "",
                f"- ID: {ticket['id']}",
                f"- Title: {ticket['title']}",
                f"- Wave: {ticket['wave']}",
                f"- Lane: {ticket['lane']}",
                f"- Stage: {ticket['stage']}",
                "- Status: ready",
                f"- Resolution: {ticket['resolution_state']}",
                f"- Verification: {ticket['verification_state']}",
                "",
                "## Generation Status",
                "",
                "- handoff_status: ready for continued development",
                f"- process_version: {workflow['process_version']}",
                f"- parallel_mode: {workflow['parallel_mode']}",
                "- pending_process_verification: false",
                "- bootstrap_status: ready",
                "- bootstrap_proof: None",
                "",
                "## Post-Generation Audit Status",
                "",
                "- audit_or_repair_follow_up: none recorded",
                "- reopened_tickets: none",
                "- done_but_not_fully_trusted: none",
                "- pending_reverification: none",
                "",
                "## Known Risks",
                "",
                "- None recorded.",
                "",
                "## Next Action",
                "",
                "Continue the required internal lifecycle from the current ticket stage.",
                "<!-- SCAFFORGE:START_HERE_BLOCK END -->",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (dest / ".opencode" / "state" / "context-snapshot.md").write_text(
        "\n".join(
            [
                "# Context Snapshot",
                "",
                "## Project",
                "",
                "Smoke Example",
                "",
                "## Active Ticket",
                "",
                f"- ID: {ticket['id']}",
                f"- Title: {ticket['title']}",
                f"- Stage: {ticket['stage']}",
                "- Status: ready",
                f"- Resolution: {ticket['resolution_state']}",
                f"- Verification: {ticket['verification_state']}",
                "- Approved plan: no",
                "- Needs reverification: no",
                "",
                "## Bootstrap",
                "",
                "- status: ready",
                "- last_verified_at: 2026-03-25T22:00:00Z",
                "- proof_artifact: None",
                "",
                "## Process State",
                "",
                f"- process_version: {workflow['process_version']}",
                "- pending_process_verification: false",
                f"- parallel_mode: {workflow['parallel_mode']}",
                "- state_revision: 113",
                "",
                "## Lane Leases",
                "",
                "- No active lane leases",
                "",
                "## Recent Artifacts",
                "",
                "- No artifacts recorded yet",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (dest / ".opencode" / "state" / "latest-handoff.md").write_text(
        "\n".join(
            [
                "# START HERE",
                "",
                "<!-- SCAFFORGE:START_HERE_BLOCK START -->",
                "## What This Repo Is",
                "",
                "Smoke Example",
                "",
                "## Current Or Next Ticket",
                "",
                f"- ID: {ticket['id']}",
                f"- Title: {ticket['title']}",
                f"- Wave: {ticket['wave']}",
                f"- Lane: {ticket['lane']}",
                f"- Stage: {ticket['stage']}",
                "- Status: ready",
                f"- Resolution: {ticket['resolution_state']}",
                f"- Verification: {ticket['verification_state']}",
                "",
                "## Generation Status",
                "",
                "- handoff_status: ready for continued development",
                f"- process_version: {workflow['process_version']}",
                f"- parallel_mode: {workflow['parallel_mode']}",
                "- pending_process_verification: false",
                "- bootstrap_status: ready",
                "- bootstrap_proof: None",
                "",
                "## Post-Generation Audit Status",
                "",
                "- audit_or_repair_follow_up: none recorded",
                "- reopened_tickets: none",
                "- done_but_not_fully_trusted: none",
                "- pending_reverification: none",
                "",
                "## Known Risks",
                "",
                "- None recorded.",
                "",
                "## Next Action",
                "",
                "Continue the required internal lifecycle from the current ticket stage.",
                "<!-- SCAFFORGE:START_HERE_BLOCK END -->",
                "",
            ]
        ),
        encoding="utf-8",
    )


def seed_bootstrap_guidance_drift(dest: Path) -> None:
    workflow_path = dest / ".opencode" / "state" / "workflow-state.json"
    workflow = json.loads(workflow_path.read_text(encoding="utf-8"))
    workflow["bootstrap"] = {
        "status": "failed",
        "last_verified_at": "2026-03-25T23:02:26Z",
        "environment_fingerprint": "synthetic-bootstrap",
        "proof_artifact": ".opencode/state/bootstrap/synthetic-bootstrap-proof.md",
    }
    workflow_path.write_text(json.dumps(workflow, indent=2) + "\n", encoding="utf-8")

    ticket_lookup = dest / ".opencode" / "tools" / "ticket_lookup.ts"
    ticket_lookup.write_text(
        ticket_lookup.read_text(encoding="utf-8").replace(
            "Bootstrap is ${bootstrapStatus}. Run environment_bootstrap first, then rerun ticket_lookup before attempting lifecycle transitions.",
            "Bootstrap is ${bootstrapStatus}. Continue normal lifecycle routing after checking the current stage.",
        ),
        encoding="utf-8",
    )

    team_leader = next((dest / ".opencode" / "agents").glob("*team-leader*.md"))
    team_leader.write_text(
        team_leader.read_text(encoding="utf-8").replace(
            "If `ticket_lookup.bootstrap.status` is not `ready`, treat `environment_bootstrap` as the next required tool call, rerun `ticket_lookup` after it completes, and do not continue normal lifecycle routing until bootstrap succeeds.\n",
            "",
        ),
        encoding="utf-8",
    )

    ticket_execution = dest / ".opencode" / "skills" / "ticket-execution" / "SKILL.md"
    ticket_execution.write_text(
        ticket_execution.read_text(encoding="utf-8").replace(
            "- if `ticket_lookup.bootstrap.status` is not `ready`, stop normal lifecycle routing, run `environment_bootstrap`, then rerun `ticket_lookup` before any `ticket_update`\n",
            "",
        ),
        encoding="utf-8",
    )


def seed_split_lease_guidance(dest: Path) -> None:
    workflow_doc = dest / "docs" / "process" / "workflow.md"
    workflow_doc.write_text(
        workflow_doc.read_text(encoding="utf-8").replace(
            "- the team leader owns `ticket_claim` and `ticket_release`; planning, implementation, review, QA, and optional handoff specialists write only under the already-active ticket lease\n",
            "",
        ),
        encoding="utf-8",
    )
    implementer = next((dest / ".opencode" / "agents").glob("*implementer*.md"))
    implementer.write_text(
        implementer.read_text(encoding="utf-8").replace(
            "  environment_bootstrap: allow\n",
            "  environment_bootstrap: allow\n  ticket_claim: allow\n  ticket_release: allow\n",
        ).replace(
            "- the team leader already owns lease claim and release; if the required ticket lease is missing, return a blocker instead of claiming it yourself\n",
            "- claim the assigned ticket with `ticket_claim` before write-capable work and release it with `ticket_release` when the bounded implementation pass is complete\n",
        ),
        encoding="utf-8",
    )


def seed_resume_truth_hierarchy_drift(dest: Path) -> None:
    latest_handoff = dest / ".opencode" / "state" / "latest-handoff.md"
    if latest_handoff.exists():
        latest_handoff.unlink()

    resume = dest / ".opencode" / "commands" / "resume.md"
    resume.write_text(
        resume.read_text(encoding="utf-8").replace(
            "Resume from `tickets/manifest.json` and `.opencode/state/workflow-state.json` first. Use `START-HERE.md`, `.opencode/state/context-snapshot.md`, and `.opencode/state/latest-handoff.md` only as derived restart surfaces that must agree with canonical state.\n",
            "Resume from `START-HERE.md` first and use the other workflow files as support when needed.\n",
        ).replace(
            "- Treat the active open ticket as the primary lane even when historical reverification is pending.\n",
            "",
        ),
        encoding="utf-8",
    )

    workflow_doc = dest / "docs" / "process" / "workflow.md"
    workflow_doc.write_text(
        workflow_doc.read_text(encoding="utf-8").replace(
            "- open active-ticket work remains the primary foreground lane; post-migration reverification is a follow-up path, not a reason to ignore an already-open active ticket\n",
            "",
        ),
        encoding="utf-8",
    )


def seed_invocation_log_coordinator_artifacts(dest: Path) -> None:
    log_path = dest / ".opencode" / "state" / "invocation-log.jsonl"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    events = [
        {
            "event": "tool.execute.before",
            "timestamp": "2026-03-26T00:00:00Z",
            "agent": "smoke-team-leader",
            "tool": "artifact_write",
            "args": {
                "ticket_id": "SETUP-001",
                "stage": "planning",
                "kind": "planning",
                "path": ".opencode/state/plans/setup-001-planning-plan.md",
            },
        },
        {
            "event": "tool.execute.before",
            "timestamp": "2026-03-26T00:01:00Z",
            "agent": "smoke-team-leader",
            "tool": "artifact_write",
            "args": {
                "ticket_id": "SETUP-001",
                "stage": "qa",
                "kind": "qa",
                "path": ".opencode/state/qa/setup-001-qa-qa.md",
            },
        },
    ]
    log_path.write_text("".join(json.dumps(event) + "\n" for event in events), encoding="utf-8")


def seed_open_active_ticket_with_pending_verification(dest: Path) -> None:
    manifest_path = dest / "tickets" / "manifest.json"
    workflow_path = dest / ".opencode" / "state" / "workflow-state.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    workflow = json.loads(workflow_path.read_text(encoding="utf-8"))
    active_ticket = manifest["tickets"][0]
    active_ticket["stage"] = "implementation"
    active_ticket["status"] = "in_progress"
    active_ticket["resolution_state"] = "open"
    active_ticket["verification_state"] = "suspect"
    manifest["tickets"].append(
        {
            "id": "DONE-900",
            "title": "Historical done ticket requiring reverification",
            "wave": 9,
            "lane": "repo-foundation",
            "parallel_safe": False,
            "overlap_risk": "high",
            "stage": "closeout",
            "status": "done",
            "depends_on": [],
            "summary": "Historical done ticket",
            "acceptance": ["remains trusted after reverification"],
            "decision_blockers": [],
            "artifacts": [
                {
                    "kind": "smoke-test",
                    "stage": "smoke-test",
                    "path": ".opencode/state/smoke-tests/done-900-smoke-test-smoke-test.md",
                    "summary": "legacy smoke proof",
                    "created_at": "2026-03-20T00:00:00Z",
                    "trust_state": "current",
                }
            ],
            "resolution_state": "done",
            "verification_state": "suspect",
            "follow_up_ticket_ids": [],
        }
    )
    workflow["active_ticket"] = active_ticket["id"]
    workflow["stage"] = "implementation"
    workflow["status"] = "in_progress"
    workflow["pending_process_verification"] = True
    workflow["process_last_changed_at"] = "2026-03-25T00:00:00Z"
    workflow["bootstrap"] = {
        "status": "ready",
        "last_verified_at": "2026-03-26T00:00:00Z",
        "environment_fingerprint": "synthetic-ready-bootstrap",
        "proof_artifact": ".opencode/state/bootstrap/synthetic-ready-bootstrap.md",
    }
    proof_path = dest / ".opencode" / "state" / "bootstrap" / "synthetic-ready-bootstrap.md"
    proof_path.parent.mkdir(parents=True, exist_ok=True)
    proof_path.write_text("# Ready Bootstrap\n", encoding="utf-8")
    workflow_path.write_text(json.dumps(workflow, indent=2) + "\n", encoding="utf-8")
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def seed_reverification_deadlock(dest: Path) -> None:
    stage_gate = dest / ".opencode" / "plugins" / "stage-gate-enforcer.ts"
    text = stage_gate.read_text(encoding="utf-8")
    text = text.replace(
        '        const ticket = getTicket(manifest, ticketId)\n        if (ticket.status !== "done") {\n          throw new Error(`Ticket ${ticket.id} must already be done before ticket_reverify can restore trust.`)\n        }\n',
        '        await ensureTargetTicketWriteLease(ticketId)\n',
    )
    stage_gate.write_text(text, encoding="utf-8")


def seed_team_leader_workflow_drift(dest: Path) -> None:
    team_leader = next((dest / ".opencode" / "agents").glob("*team-leader*.md"))
    text = team_leader.read_text(encoding="utf-8")
    text = text.replace("Treat `ticket_lookup.transition_guidance` as the canonical next-step summary before you call `ticket_update`.\n", "")
    text = text.replace(
        "- do not probe alternate stage or status values when a lifecycle error repeats; re-run `ticket_lookup`, inspect `transition_guidance`, load `ticket-execution` if needed, and return a blocker instead of inventing a workaround\n",
        "",
    )
    text = text.replace(
        "- do not create planning, implementation, review, QA, or smoke-test artifacts yourself; route those bodies through the assigned specialist lane, and let `smoke_test` produce smoke-test artifacts\n",
        "",
    )
    text = text.replace("- use human slash commands only as entrypoints\n", "")
    team_leader.write_text(text, encoding="utf-8")


def seed_thin_ticket_execution(dest: Path) -> None:
    skill_path = dest / ".opencode" / "skills" / "ticket-execution" / "SKILL.md"
    skill_path.write_text(
        "\n".join(
            [
                "---",
                "name: ticket-execution",
                "description: Minimal workflow notes.",
                "---",
                "",
                "# Ticket Execution",
                "",
                "Follow the ticket workflow.",
                "",
                "1. planning",
                "2. implementation",
                "3. review",
                "4. qa",
                "5. done",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def verify_render(dest: Path, *, expect_full_repo: bool) -> None:
    checklist = json.loads(CHECKLIST.read_text(encoding="utf-8"))
    for relative in checklist["required_files"]:
        path = dest / relative
        if expect_full_repo or str(relative).startswith(".opencode") or str(relative) == "opencode.jsonc":
            if not path.exists():
                raise RuntimeError(f"Missing expected file: {path}")

    for relative in checklist["required_directories"]:
        path = dest / relative
        if expect_full_repo or str(relative).startswith(".opencode"):
            if not path.exists():
                raise RuntimeError(f"Missing expected directory: {path}")

    manifest = json.loads((dest / "tickets" / "manifest.json").read_text(encoding="utf-8")) if expect_full_repo else None
    if manifest is not None:
        if "tickets" not in manifest:
            raise RuntimeError("tickets/manifest.json is missing a tickets key")
        if manifest.get("version") != 3:
            raise RuntimeError("tickets/manifest.json should use version 3")
        if not manifest["tickets"]:
            raise RuntimeError("tickets/manifest.json must contain at least one ticket")
        first_ticket = manifest["tickets"][0]
        for key in ("wave", "parallel_safe", "overlap_risk", "decision_blockers", "resolution_state", "verification_state"):
            if key not in first_ticket:
                raise RuntimeError(f"tickets/manifest.json first ticket is missing `{key}`")

        workflow = json.loads((dest / ".opencode" / "state" / "workflow-state.json").read_text(encoding="utf-8"))
        for key in ("process_version", "pending_process_verification", "parallel_mode", "ticket_state", "bootstrap", "lane_leases", "state_revision"):
            if key not in workflow:
                raise RuntimeError(f".opencode/state/workflow-state.json is missing `{key}`")
        active_ticket = manifest.get("active_ticket")
        if not isinstance(workflow.get("ticket_state"), dict):
            raise RuntimeError(".opencode/state/workflow-state.json must contain a ticket_state map")
        if isinstance(active_ticket, str) and active_ticket not in workflow["ticket_state"]:
            raise RuntimeError("workflow-state ticket_state must contain the active ticket entry")
        active_ticket_state = workflow["ticket_state"].get(active_ticket, {}) if isinstance(active_ticket, str) else {}
        for key in ("reopen_count", "needs_reverification"):
            if key not in active_ticket_state:
                raise RuntimeError(f"workflow-state active ticket entry is missing `{key}`")

        agents_dir = dest / ".opencode" / "agents"
        agent_names = {path.name for path in agents_dir.glob("*.md")}
        required_agent_suffixes = checklist.get("required_agent_suffixes")
        if not required_agent_suffixes:
            raise RuntimeError("opencode-conformance-checklist.json is missing required_agent_suffixes")
        for suffix in required_agent_suffixes:
            if not any(name.endswith(f"{suffix}.md") for name in agent_names):
                raise RuntimeError(f"Missing expected agent with suffix `{suffix}`")

        skills_dir = dest / ".opencode" / "skills"
        required_skill_ids = checklist.get("required_skill_ids")
        if not required_skill_ids:
            raise RuntimeError("opencode-conformance-checklist.json is missing required_skill_ids")
        for skill_id in required_skill_ids:
            skill_file = skills_dir / skill_id / "SKILL.md"
            if not skill_file.exists():
                raise RuntimeError(f"Missing expected local skill `{skill_id}`")

        start_here = (dest / "START-HERE.md").read_text(encoding="utf-8")
        for heading in ("## Current Or Next Ticket", "## Generation Status", "## Post-Generation Audit Status"):
            if heading not in start_here:
                raise RuntimeError(f"START-HERE.md is missing required section `{heading}`")
        for forbidden in ("## Process Contract", "## Current Ticket"):
            if forbidden in start_here:
                raise RuntimeError(f"START-HERE.md still contains deprecated section `{forbidden}`")

        context_snapshot = (dest / ".opencode" / "state" / "context-snapshot.md").read_text(encoding="utf-8")
        for heading in ("## Active Ticket", "## Bootstrap", "## Process State", "## Lane Leases"):
            if heading not in context_snapshot:
                raise RuntimeError(f"context-snapshot.md is missing required section `{heading}`")


def main() -> int:
    workspace = Path(tempfile.mkdtemp(prefix="scafforge-smoke-"))
    try:
        full_dest = workspace / "full"
        opencode_dest = workspace / "opencode"

        common = [
            sys.executable,
            str(BOOTSTRAP),
            "--project-name",
            "Smoke Example",
            "--project-slug",
            "smoke-example",
            "--agent-prefix",
            "smoke",
            "--model-provider",
            "openrouter",
            "--planner-model",
            "openrouter/anthropic/claude-sonnet-4.5",
            "--implementer-model",
            "openrouter/openai/gpt-5-codex",
            "--utility-model",
            "openrouter/openai/gpt-5-mini",
            "--stack-label",
            "framework-agnostic",
            "--force",
        ]

        run(common + ["--dest", str(full_dest), "--scope", "full"], ROOT)
        run(common + ["--dest", str(opencode_dest), "--scope", "opencode"], ROOT)

        verify_render(full_dest, expect_full_repo=True)
        verify_render(opencode_dest, expect_full_repo=False)

        generated_ticket_update = (full_dest / ".opencode" / "tools" / "ticket_update.ts").read_text(encoding="utf-8")
        if '"plan_review"' not in generated_ticket_update:
            raise RuntimeError("Generated ticket_update.ts should expose the explicit plan_review status")
        generated_bootstrap = (full_dest / ".opencode" / "tools" / "environment_bootstrap.ts").read_text(encoding="utf-8")
        for expected in ("[project.optional-dependencies]", "[dependency-groups]", "[tool.uv.dev-dependencies]", "[tool.pytest.ini_options]"):
            if expected not in generated_bootstrap:
                raise RuntimeError(f"Generated environment_bootstrap.ts should detect {expected} when resolving Python bootstrap inputs")
        if "defaultBootstrapProofPath" not in generated_bootstrap or "normalizeRepoPath" not in generated_bootstrap:
            raise RuntimeError("Generated environment_bootstrap.ts should persist bootstrap proof through canonical artifact-path helpers")
        generated_smoke_test = (full_dest / ".opencode" / "tools" / "smoke_test.ts").read_text(encoding="utf-8")
        if 'join(root, ".venv", "bin", "python")' not in generated_smoke_test:
            raise RuntimeError("Generated smoke_test.ts should support repo-local .venv Python execution")
        if "[tool.pytest.ini_options]" not in generated_smoke_test:
            raise RuntimeError("Generated smoke_test.ts should detect pyproject-only pytest configuration, not only tests/ or pytest.ini")
        for expected in ("scope:", "test_paths:", "args.scope", "args.test_paths"):
            if expected not in generated_smoke_test:
                raise RuntimeError("Generated smoke_test.ts should expose scoped smoke inputs and thread them into execution")
        if "defaultArtifactPath" not in generated_smoke_test or "normalizeRepoPath" not in generated_smoke_test:
            raise RuntimeError("Generated smoke_test.ts should persist smoke artifacts through canonical artifact-path helpers")
        generated_stage_gate = (full_dest / ".opencode" / "plugins" / "stage-gate-enforcer.ts").read_text(encoding="utf-8")
        if 'const RESERVED_ARTIFACT_STAGES = new Set(["smoke-test"])' not in generated_stage_gate:
            raise RuntimeError("Generated stage-gate-enforcer.ts should reserve smoke-test artifacts to their owning tool")
        if "Generic artifact_write is not allowed for that stage." not in generated_stage_gate:
            raise RuntimeError("Generated stage-gate-enforcer.ts should block generic artifact_write for smoke-test")
        if 'type: "BLOCKER"' not in generated_stage_gate or "missing_write_lease" not in generated_stage_gate:
            raise RuntimeError("Generated stage-gate-enforcer.ts should emit structured blockers for missing lease conditions")
        generated_workflow = (full_dest / ".opencode" / "lib" / "workflow.ts").read_text(encoding="utf-8")
        if (full_dest / ".opencode" / "tools" / "_workflow.ts").exists():
            raise RuntimeError("Generated helper workflow library should stay private under .opencode/lib instead of leaking a callable _workflow.ts tool")
        if "tool({" in generated_workflow:
            raise RuntimeError("Generated workflow library should remain helper-only and must not expose a model-callable tool surface")
        if "refreshRestartSurfaces" not in generated_workflow:
            raise RuntimeError("Generated workflow.ts should refresh derived restart surfaces after workflow mutations")
        if "latestHandoffPath" not in generated_workflow:
            raise RuntimeError("Generated workflow.ts should own the latest-handoff restart surface")
        if "Historical done-ticket reverification stays secondary until the active open ticket is resolved." not in generated_workflow:
            raise RuntimeError("Generated workflow.ts should keep the active open ticket primary when process verification is pending")
        if "Cannot publish dependency-readiness claims" not in generated_workflow or "Cannot publish causal claims" not in generated_workflow:
            raise RuntimeError("Generated workflow.ts should truthfully gate handoff claims against canonical state and smoke evidence")
        generated_ticket_lookup = (full_dest / ".opencode" / "tools" / "ticket_lookup.ts").read_text(encoding="utf-8")
        if "transition_guidance" not in generated_ticket_lookup:
            raise RuntimeError("Generated ticket_lookup.ts should expose transition_guidance")
        if "Do not fabricate a PASS artifact through generic artifact tools." not in generated_ticket_lookup:
            raise RuntimeError("Generated ticket_lookup.ts should warn against generic PASS artifact fabrication")
        if "Run environment_bootstrap first, then rerun ticket_lookup before attempting lifecycle transitions." not in generated_ticket_lookup:
            raise RuntimeError("Generated ticket_lookup.ts should short-circuit lifecycle guidance to environment_bootstrap when bootstrap is not ready")
        generated_team_leader = next((full_dest / ".opencode" / "agents").glob("*team-leader*.md")).read_text(encoding="utf-8")
        if "do not create planning, implementation, review, QA, or smoke-test artifacts yourself" not in generated_team_leader:
            raise RuntimeError("Generated team leader prompt should forbid coordinator-authored specialist artifacts")
        if "If `ticket_lookup.bootstrap.status` is not `ready`, treat `environment_bootstrap` as the next required tool call" not in generated_team_leader:
            raise RuntimeError("Generated team leader prompt should make bootstrap-first routing explicit")
        if "grant a write lease with `ticket_claim` before any specialist writes planning, implementation, review, QA, or handoff artifact bodies or makes code changes" not in generated_team_leader:
            raise RuntimeError("Generated team leader prompt should own the lease claim path")
        generated_ticket_execution = (full_dest / ".opencode" / "skills" / "ticket-execution" / "SKILL.md").read_text(encoding="utf-8")
        if "slash commands are human entrypoints" not in generated_ticket_execution:
            raise RuntimeError("Generated ticket-execution skill should mark slash commands as human entrypoints only")
        if "if `ticket_lookup.bootstrap.status` is not `ready`, stop normal lifecycle routing, run `environment_bootstrap`, then rerun `ticket_lookup` before any `ticket_update`" not in generated_ticket_execution:
            raise RuntimeError("Generated ticket-execution skill should treat bootstrap readiness as a pre-lifecycle gate")
        if "the team leader claims and releases write leases" not in generated_ticket_execution:
            raise RuntimeError("Generated ticket-execution skill should encode the coordinator-owned lease model")
        generated_resume = (full_dest / ".opencode" / "commands" / "resume.md").read_text(encoding="utf-8")
        if "Resume from `tickets/manifest.json` and `.opencode/state/workflow-state.json` first." not in generated_resume:
            raise RuntimeError("Generated /resume command should treat manifest and workflow-state as canonical")
        if ".opencode/state/latest-handoff.md" not in generated_resume:
            raise RuntimeError("Generated /resume command should mention latest-handoff as a derived restart surface")
        generated_implementer = next((full_dest / ".opencode" / "agents").glob("*implementer*.md")).read_text(encoding="utf-8")
        if "ticket_claim: allow" in generated_implementer or "ticket_release: allow" in generated_implementer:
            raise RuntimeError("Generated implementer should not own ticket claim or release")
        latest_handoff = (full_dest / ".opencode" / "state" / "latest-handoff.md").read_text(encoding="utf-8")
        if "bootstrap recovery required" not in latest_handoff:
            raise RuntimeError("Generated latest-handoff should be seeded from the managed restart narrative")
        invocation_tracker = (full_dest / ".opencode" / "plugins" / "invocation-tracker.ts").read_text(encoding="utf-8")
        if "agent: input.agent ?? null" not in invocation_tracker:
            raise RuntimeError("Generated invocation-tracker.ts should record agent ownership on command and tool events")
        generated_handoff_publish = (full_dest / ".opencode" / "tools" / "handoff_publish.ts").read_text(encoding="utf-8")
        if "validateHandoffNextAction" not in generated_handoff_publish:
            raise RuntimeError("Generated handoff_publish.ts should validate custom next_action claims before publishing")
        if generated_handoff_publish.find("const handoffBlocker = await validateHandoffNextAction") >= generated_handoff_publish.find("await refreshRestartSurfaces"):
            raise RuntimeError("Generated handoff_publish.ts should validate next_action claims before refreshing restart surfaces")
        generated_artifact_write = (full_dest / ".opencode" / "tools" / "artifact_write.ts").read_text(encoding="utf-8")
        if "expectedPath = defaultArtifactPath" not in generated_artifact_write or "canonicalizeRepoPath(args.path)" not in generated_artifact_write:
            raise RuntimeError("Generated artifact_write.ts should enforce canonical artifact paths")
        generated_artifact_register = (full_dest / ".opencode" / "tools" / "artifact_register.ts").read_text(encoding="utf-8")
        if "expectedPath = defaultArtifactPath" not in generated_artifact_register or "canonicalizeRepoPath(args.path)" not in generated_artifact_register:
            raise RuntimeError("Generated artifact_register.ts should enforce canonical artifact paths")

        initial_audit = run_json([sys.executable, str(AUDIT), str(full_dest), "--format", "json", "--emit-diagnosis-pack"], ROOT)
        initial_codes = {finding["code"] for finding in initial_audit.get("findings", [])}
        if "SKILL001" not in initial_codes:
            raise RuntimeError("Audit should flag placeholder repo-local skills with SKILL001 on the base scaffold output")
        diagnosis_root = full_dest / "diagnosis"
        diagnosis_dirs = sorted(path for path in diagnosis_root.iterdir() if path.is_dir()) if diagnosis_root.exists() else []
        if not diagnosis_dirs:
            raise RuntimeError("Audit should create a diagnosis/<timestamp> folder when diagnosis-pack emission is enabled")
        diagnosis_pack = diagnosis_dirs[-1]
        required_reports = [
            "01-initial-codebase-review.md",
            "02-scafforge-process-failures.md",
            "03-scafforge-prevention-actions.md",
            "04-live-repo-repair-plan.md",
            "manifest.json",
        ]
        for relative in required_reports:
            if not (diagnosis_pack / relative).exists():
                raise RuntimeError(f"Diagnosis pack is missing expected file: {diagnosis_pack / relative}")

        diagnosis_manifest = json.loads((diagnosis_pack / "manifest.json").read_text(encoding="utf-8"))
        if "ticket_recommendations" not in diagnosis_manifest:
            raise RuntimeError("Diagnosis pack manifest should include ticket_recommendations")
        if diagnosis_manifest.get("report_files", {}).get("report_4") != "04-live-repo-repair-plan.md":
            raise RuntimeError("Diagnosis pack manifest should map report_4 to 04-live-repo-repair-plan.md")

        restart_surface_dest = workspace / "restart-surface-drift"
        shutil.copytree(full_dest, restart_surface_dest)
        seed_restart_surface_drift(restart_surface_dest)
        restart_surface_audit = run_json([sys.executable, str(AUDIT), str(restart_surface_dest), "--format", "json", "--no-diagnosis-pack"], ROOT)
        restart_surface_codes = {finding["code"] for finding in restart_surface_audit.get("findings", [])}
        if "WFLOW010" not in restart_surface_codes:
            raise RuntimeError("A repo whose START-HERE or context snapshot drifts from canonical workflow state should emit WFLOW010")

        bootstrap_guidance_dest = workspace / "bootstrap-guidance-drift"
        shutil.copytree(full_dest, bootstrap_guidance_dest)
        seed_bootstrap_guidance_drift(bootstrap_guidance_dest)
        bootstrap_guidance_audit = run_json([sys.executable, str(AUDIT), str(bootstrap_guidance_dest), "--format", "json", "--no-diagnosis-pack"], ROOT)
        bootstrap_guidance_codes = {finding["code"] for finding in bootstrap_guidance_audit.get("findings", [])}
        if "WFLOW011" not in bootstrap_guidance_codes:
            raise RuntimeError("A repo whose workflow surfaces do not route failed bootstrap to environment_bootstrap first should emit WFLOW011")

        split_lease_dest = workspace / "split-lease-guidance"
        shutil.copytree(full_dest, split_lease_dest)
        seed_split_lease_guidance(split_lease_dest)
        split_lease_audit = run_json([sys.executable, str(AUDIT), str(split_lease_dest), "--format", "json", "--no-diagnosis-pack"], ROOT)
        split_lease_codes = {finding["code"] for finding in split_lease_audit.get("findings", [])}
        if "WFLOW012" not in split_lease_codes:
            raise RuntimeError("A repo whose prompts split lease ownership between coordinator and workers should emit WFLOW012")

        resume_truth_dest = workspace / "resume-truth-hierarchy"
        shutil.copytree(full_dest, resume_truth_dest)
        seed_resume_truth_hierarchy_drift(resume_truth_dest)
        resume_truth_audit = run_json([sys.executable, str(AUDIT), str(resume_truth_dest), "--format", "json", "--no-diagnosis-pack"], ROOT)
        resume_truth_codes = {finding["code"] for finding in resume_truth_audit.get("findings", [])}
        if "WFLOW013" not in resume_truth_codes:
            raise RuntimeError("A repo whose resume surfaces treat derived handoff text as canonical should emit WFLOW013")

        invocation_log_dest = workspace / "invocation-log-coordinator-artifacts"
        shutil.copytree(full_dest, invocation_log_dest)
        seed_invocation_log_coordinator_artifacts(invocation_log_dest)
        invocation_log_audit = run_json([sys.executable, str(AUDIT), str(invocation_log_dest), "--format", "json", "--no-diagnosis-pack"], ROOT)
        invocation_log_codes = {finding["code"] for finding in invocation_log_audit.get("findings", [])}
        if "WFLOW014" not in invocation_log_codes:
            raise RuntimeError("A repo whose invocation log shows coordinator-authored specialist artifacts should emit WFLOW014")

        restart_repair_dest = workspace / "restart-surface-repair"
        shutil.copytree(full_dest, restart_repair_dest)
        seed_restart_surface_drift(restart_repair_dest)
        run_json([sys.executable, str(REPAIR), str(restart_repair_dest)], ROOT)
        repaired_start_here = (restart_repair_dest / "START-HERE.md").read_text(encoding="utf-8")
        if "- bootstrap_status: failed" not in repaired_start_here or "- pending_process_verification: true" not in repaired_start_here:
            raise RuntimeError("Repair should refresh START-HERE.md from canonical workflow state after managed surface replacement")
        repaired_context_snapshot = (restart_repair_dest / ".opencode" / "state" / "context-snapshot.md").read_text(encoding="utf-8")
        if "- state_revision: 122" not in repaired_context_snapshot or "synthetic-team-leader" not in repaired_context_snapshot:
            raise RuntimeError("Repair should refresh context-snapshot.md with current revision and active lane-lease facts")
        repaired_latest_handoff = (restart_repair_dest / ".opencode" / "state" / "latest-handoff.md").read_text(encoding="utf-8")
        if "- bootstrap_status: failed" not in repaired_latest_handoff or "- pending_process_verification: true" not in repaired_latest_handoff:
            raise RuntimeError("Repair should refresh latest-handoff.md from canonical workflow state after managed surface replacement")
        repaired_restart_audit = run_json([sys.executable, str(AUDIT), str(restart_repair_dest), "--format", "json", "--no-diagnosis-pack"], ROOT)
        repaired_restart_codes = {finding["code"] for finding in repaired_restart_audit.get("findings", [])}
        if "WFLOW010" in repaired_restart_codes:
            raise RuntimeError("Repair should clear WFLOW010 by regenerating START-HERE.md, context-snapshot.md, and latest-handoff.md from canonical state")

        public_repair_dest = workspace / "public-repair-runner"
        shutil.copytree(full_dest, public_repair_dest)
        public_repair = subprocess.run(
            [sys.executable, str(PUBLIC_REPAIR), str(public_repair_dest), "--skip-verify"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        if public_repair.returncode == 0:
            raise RuntimeError("Public managed repair runner should fail closed until required follow-on stages are marked complete")
        public_repair_payload = json.loads(public_repair.stdout)
        if public_repair_payload["execution_record"]["handoff_allowed"]:
            raise RuntimeError("Public managed repair runner must block handoff while required follow-on stages remain unexecuted")
        if "handoff-brief" not in public_repair_payload["execution_record"]["required_follow_on_stages"]:
            raise RuntimeError("Public managed repair runner should require handoff-brief before allowing restart handoff")
        if not (public_repair_dest / ".opencode" / "meta" / "repair-execution.json").exists():
            raise RuntimeError("Public managed repair runner should persist a machine-readable repair execution record")

        repeat_dest = workspace / "repeat-cycle"
        shutil.copytree(full_dest, repeat_dest)
        repeat_diagnosis_root = repeat_dest / "diagnosis"
        repeat_diagnosis_dirs = sorted(path for path in repeat_diagnosis_root.iterdir() if path.is_dir())
        seed_failed_repair_cycle(repeat_dest, repeat_diagnosis_dirs[-1])
        repeated_cycle_audit = run_json([sys.executable, str(AUDIT), str(repeat_dest), "--format", "json"], ROOT)
        repeated_cycle_codes = {finding["code"] for finding in repeated_cycle_audit.get("findings", [])}
        if "CYCLE001" not in repeated_cycle_codes:
            raise RuntimeError("A repo with a prior diagnosis pack, later repair history, and repeated workflow drift should emit CYCLE001")

        chronology_dest = workspace / "chronology"
        shutil.copytree(full_dest, chronology_dest)
        transcript_log = seed_workflow_overclaim(chronology_dest)
        chronology_audit = run_json(
            [sys.executable, str(AUDIT), str(chronology_dest), "--format", "json", "--supporting-log", str(transcript_log)],
            ROOT,
        )
        chronology_codes = {finding["code"] for finding in chronology_audit.get("findings", [])}
        for expected in ("WFLOW002", "SESSION001", "SESSION002", "SESSION003", "SESSION004"):
            if expected not in chronology_codes:
                raise RuntimeError(f"Audit should emit {expected} when handoff overclaims and transcript chronology proves thrash, bypass-seeking, or evidence-free PASS claims")

        recovered_dest = workspace / "recovered-verification"
        shutil.copytree(full_dest, recovered_dest)
        recovered_log = seed_recovered_verification_log(recovered_dest)
        recovered_audit = run_json(
            [sys.executable, str(AUDIT), str(recovered_dest), "--format", "json", "--supporting-log", str(recovered_log)],
            ROOT,
        )
        recovered_codes = {finding["code"] for finding in recovered_audit.get("findings", [])}
        if "SESSION004" in recovered_codes:
            raise RuntimeError("A transcript with later real recovery evidence should not emit SESSION004")

        failing_suite_dest = workspace / "failing-suite"
        shutil.copytree(full_dest, failing_suite_dest)
        seed_failing_pytest_suite(failing_suite_dest)
        failing_suite_audit = run_json([sys.executable, str(AUDIT), str(failing_suite_dest), "--format", "json", "--no-diagnosis-pack"], ROOT)
        failing_suite_codes = {finding["code"] for finding in failing_suite_audit.get("findings", [])}
        if "EXEC003" not in failing_suite_codes:
            raise RuntimeError("A repo whose tests collect successfully but fail at runtime should emit EXEC003")

        missing_pytest_dest = workspace / "missing-pytest"
        shutil.copytree(full_dest, missing_pytest_dest)
        seed_missing_pytest_env(missing_pytest_dest)
        stripped_env = dict(os.environ)
        stripped_env["PATH"] = ""
        missing_pytest_audit = run_json(
            [sys.executable, str(AUDIT), str(missing_pytest_dest), "--format", "json", "--no-diagnosis-pack"],
            ROOT,
            env=stripped_env,
        )
        missing_pytest_codes = {finding["code"] for finding in missing_pytest_audit.get("findings", [])}
        if "ENV002" not in missing_pytest_codes:
            raise RuntimeError("A Python repo with tests but no usable pytest command should emit ENV002")

        pending_verification_dest = workspace / "pending-process-verification"
        shutil.copytree(full_dest, pending_verification_dest)
        seed_pending_process_verification(pending_verification_dest)
        pending_verification_audit = run_json([sys.executable, str(AUDIT), str(pending_verification_dest), "--format", "json", "--no-diagnosis-pack"], ROOT)
        pending_verification_codes = {finding["code"] for finding in pending_verification_audit.get("findings", [])}
        if "WFLOW008" not in pending_verification_codes:
            raise RuntimeError("A repo with pending_process_verification and affected done tickets should emit WFLOW008")

        active_priority_dest = workspace / "active-ticket-priority"
        shutil.copytree(full_dest, active_priority_dest)
        seed_open_active_ticket_with_pending_verification(active_priority_dest)
        run_json([sys.executable, str(REGENERATE), str(active_priority_dest)], ROOT)
        active_priority_start_here = (active_priority_dest / "START-HERE.md").read_text(encoding="utf-8")
        if "Keep SETUP-001 as the foreground ticket and continue its lifecycle from implementation." not in active_priority_start_here:
            raise RuntimeError("Restart regeneration should keep an open active ticket primary even when backlog process verification is pending")

        reverification_deadlock_dest = workspace / "reverification-deadlock"
        shutil.copytree(full_dest, reverification_deadlock_dest)
        seed_reverification_deadlock(reverification_deadlock_dest)
        reverification_deadlock_audit = run_json([sys.executable, str(AUDIT), str(reverification_deadlock_dest), "--format", "json", "--no-diagnosis-pack"], ROOT)
        reverification_deadlock_codes = {finding["code"] for finding in reverification_deadlock_audit.get("findings", [])}
        if "WFLOW009" not in reverification_deadlock_codes:
            raise RuntimeError("A repo whose reverification contract still requires closed tickets to hold a normal write lease should emit WFLOW009")

        redirected_output_dest = workspace / "redirected-output"
        shutil.copytree(full_dest, redirected_output_dest)
        redirected_output_audit = run_json(
            [
                sys.executable,
                str(AUDIT),
                str(redirected_output_dest),
                "--format",
                "json",
                "--emit-diagnosis-pack",
                "--diagnosis-output-dir",
                "/proc/scafforge-denied-output",
            ],
            ROOT,
        )
        redirected_output_codes = {finding["code"] for finding in redirected_output_audit.get("findings", [])}
        if "ENV004" not in redirected_output_codes:
            raise RuntimeError("An unwritable diagnosis output path should emit ENV004 and fall back to a writable location")
        diagnosis_pack_path = redirected_output_audit.get("diagnosis_pack", {}).get("path", "")
        if not diagnosis_pack_path.startswith("/tmp/scafforge-diagnosis/"):
            raise RuntimeError("Audit should redirect unwritable diagnosis-pack output to /tmp/scafforge-diagnosis")

        python_dest = workspace / "python-uv"
        shutil.copytree(full_dest, python_dest)
        seed_uv_python_fixture(python_dest)
        python_audit = run_json([sys.executable, str(AUDIT), str(python_dest), "--format", "json"], ROOT)
        python_codes = {finding["code"] for finding in python_audit.get("findings", [])}
        if "BOOT001" in python_codes:
            raise RuntimeError("A uv-shaped repo with the current bootstrap template should not emit BOOT001")

        legacy_smoke_dest = workspace / "legacy-smoke"
        shutil.copytree(python_dest, legacy_smoke_dest)
        seed_legacy_smoke_test_tool(legacy_smoke_dest)
        legacy_smoke_audit = run_json([sys.executable, str(AUDIT), str(legacy_smoke_dest), "--format", "json"], ROOT)
        legacy_smoke_codes = {finding["code"] for finding in legacy_smoke_audit.get("findings", [])}
        if "WFLOW001" not in legacy_smoke_codes:
            raise RuntimeError("A uv-shaped repo with a legacy system-python smoke_test tool should emit WFLOW001")

        legacy_smoke_override_dest = workspace / "legacy-smoke-override"
        shutil.copytree(full_dest, legacy_smoke_override_dest)
        seed_legacy_smoke_override_tool(legacy_smoke_override_dest)
        legacy_smoke_override_audit = run_json([sys.executable, str(AUDIT), str(legacy_smoke_override_dest), "--format", "json"], ROOT)
        legacy_smoke_override_codes = {finding["code"] for finding in legacy_smoke_override_audit.get("findings", [])}
        if "WFLOW016" not in legacy_smoke_override_codes:
            raise RuntimeError("A repo whose smoke_test tool passes command_override directly into argv should emit WFLOW016")

        legacy_review_dest = workspace / "legacy-review"
        shutil.copytree(full_dest, legacy_review_dest)
        seed_legacy_review_contract(legacy_review_dest)
        legacy_review_audit = run_json([sys.executable, str(AUDIT), str(legacy_review_dest), "--format", "json"], ROOT)
        legacy_review_codes = {finding["code"] for finding in legacy_review_audit.get("findings", [])}
        if "WFLOW003" not in legacy_review_codes:
            raise RuntimeError("A repo with plan-review docs but no explicit plan_review workflow contract should emit WFLOW003")

        legacy_transition_dest = workspace / "legacy-transition"
        shutil.copytree(full_dest, legacy_transition_dest)
        seed_legacy_stage_transition_contract(legacy_transition_dest)
        legacy_transition_audit = run_json([sys.executable, str(AUDIT), str(legacy_transition_dest), "--format", "json"], ROOT)
        legacy_transition_codes = {finding["code"] for finding in legacy_transition_audit.get("findings", [])}
        if "WFLOW004" not in legacy_transition_codes:
            raise RuntimeError("A repo with status-gated implementation or unvalidated lifecycle stages should emit WFLOW004")

        smoke_bypass_dest = workspace / "smoke-bypass"
        shutil.copytree(full_dest, smoke_bypass_dest)
        seed_smoke_artifact_bypass(smoke_bypass_dest)
        smoke_bypass_audit = run_json([sys.executable, str(AUDIT), str(smoke_bypass_dest), "--format", "json"], ROOT)
        smoke_bypass_codes = {finding["code"] for finding in smoke_bypass_audit.get("findings", [])}
        if "WFLOW005" not in smoke_bypass_codes:
            raise RuntimeError("A repo that allows smoke-test proof through generic artifact tools should emit WFLOW005")

        handoff_conflict_dest = workspace / "handoff-conflict"
        shutil.copytree(full_dest, handoff_conflict_dest)
        seed_handoff_ownership_conflict(handoff_conflict_dest)
        handoff_conflict_audit = run_json([sys.executable, str(AUDIT), str(handoff_conflict_dest), "--format", "json"], ROOT)
        handoff_conflict_codes = {finding["code"] for finding in handoff_conflict_audit.get("findings", [])}
        if "WFLOW007" not in handoff_conflict_codes:
            raise RuntimeError("A repo whose docs-handoff path conflicts with plugin enforcement should emit WFLOW007")

        team_leader_dest = workspace / "team-leader-drift"
        shutil.copytree(full_dest, team_leader_dest)
        seed_team_leader_workflow_drift(team_leader_dest)
        team_leader_audit = run_json([sys.executable, str(AUDIT), str(team_leader_dest), "--format", "json"], ROOT)
        team_leader_codes = {finding["code"] for finding in team_leader_audit.get("findings", [])}
        if "WFLOW006" not in team_leader_codes:
            raise RuntimeError("A repo whose team leader prompt omits transition guidance, stop rules, or command boundaries should emit WFLOW006")

        helper_tool_dest = workspace / "helper-tool-exposure"
        shutil.copytree(full_dest, helper_tool_dest)
        seed_helper_tool_exposure(helper_tool_dest)
        helper_tool_log = seed_helper_tool_failure_log(helper_tool_dest)
        helper_tool_audit = run_json(
            [sys.executable, str(AUDIT), str(helper_tool_dest), "--format", "json", "--supporting-log", str(helper_tool_log)],
            ROOT,
        )
        helper_tool_codes = {finding["code"] for finding in helper_tool_audit.get("findings", [])}
        if "WFLOW015" not in helper_tool_codes:
            raise RuntimeError("A repo whose runtime exposes helper-only workflow internals or transcript-level missing-execute failures should emit WFLOW015")

        smoke_override_log_dest = workspace / "smoke-override-log"
        shutil.copytree(full_dest, smoke_override_log_dest)
        smoke_override_log = seed_smoke_override_failure_log(smoke_override_log_dest)
        smoke_override_audit = run_json(
            [sys.executable, str(AUDIT), str(smoke_override_log_dest), "--format", "json", "--supporting-log", str(smoke_override_log)],
            ROOT,
        )
        smoke_override_codes = {finding["code"] for finding in smoke_override_audit.get("findings", [])}
        if "WFLOW016" not in smoke_override_codes:
            raise RuntimeError("A transcript where smoke_test treats KEY=VALUE as the executable should emit WFLOW016")

        legacy_smoke_acceptance_dest = workspace / "legacy-smoke-acceptance"
        shutil.copytree(full_dest, legacy_smoke_acceptance_dest)
        seed_legacy_smoke_acceptance_tool(legacy_smoke_acceptance_dest)
        legacy_smoke_acceptance_audit = run_json([sys.executable, str(AUDIT), str(legacy_smoke_acceptance_dest), "--format", "json"], ROOT)
        legacy_smoke_acceptance_codes = {finding["code"] for finding in legacy_smoke_acceptance_audit.get("findings", [])}
        if "WFLOW017" not in legacy_smoke_acceptance_codes:
            raise RuntimeError("A repo whose smoke_test tool ignores ticket acceptance commands should emit WFLOW017")

        smoke_acceptance_log_dest = workspace / "smoke-acceptance-log"
        shutil.copytree(full_dest, smoke_acceptance_log_dest)
        smoke_acceptance_log = seed_smoke_acceptance_scope_log(smoke_acceptance_log_dest)
        smoke_acceptance_audit = run_json(
            [sys.executable, str(AUDIT), str(smoke_acceptance_log_dest), "--format", "json", "--supporting-log", str(smoke_acceptance_log)],
            ROOT,
        )
        smoke_acceptance_codes = {finding["code"] for finding in smoke_acceptance_audit.get("findings", [])}
        if "WFLOW017" not in smoke_acceptance_codes:
            raise RuntimeError("A transcript where smoke_test ignores a ticket-defined smoke command should emit WFLOW017")

        coordinator_artifact_dest = workspace / "coordinator-artifacts"
        shutil.copytree(full_dest, coordinator_artifact_dest)
        coordinator_log = seed_coordinator_artifact_log(coordinator_artifact_dest)
        coordinator_audit = run_json(
            [sys.executable, str(AUDIT), str(coordinator_artifact_dest), "--format", "json", "--supporting-log", str(coordinator_log)],
            ROOT,
        )
        coordinator_codes = {finding["code"] for finding in coordinator_audit.get("findings", [])}
        if "SESSION005" not in coordinator_codes:
            raise RuntimeError("A transcript where the coordinator writes specialist artifacts should emit SESSION005")

        thin_skill_dest = workspace / "thin-ticket-skill"
        shutil.copytree(full_dest, thin_skill_dest)
        seed_thin_ticket_execution(thin_skill_dest)
        thin_skill_audit = run_json([sys.executable, str(AUDIT), str(thin_skill_dest), "--format", "json"], ROOT)
        thin_skill_codes = {finding["code"] for finding in thin_skill_audit.get("findings", [])}
        if "SKILL002" not in thin_skill_codes:
            raise RuntimeError("A repo with a thin ticket-execution skill should emit SKILL002")

        deadlock_dest = workspace / "python-deadlock"
        shutil.copytree(python_dest, deadlock_dest)
        seed_bootstrap_deadlock(deadlock_dest)
        deadlock_audit = run_json([sys.executable, str(AUDIT), str(deadlock_dest), "--format", "json", "--emit-diagnosis-pack"], ROOT)
        deadlock_codes = {finding["code"] for finding in deadlock_audit.get("findings", [])}
        if "BOOT001" not in deadlock_codes:
            raise RuntimeError("A failed bootstrap artifact with missing pip should emit BOOT001")
        recommendations = (
            deadlock_audit.get("diagnosis_pack", {})
            .get("manifest", {})
            .get("ticket_recommendations", [])
        )
        if not any(item.get("source_finding_code") == "BOOT001" and item.get("route") == "scafforge-repair" for item in recommendations):
            raise RuntimeError("BOOT001 should route to scafforge-repair in the diagnosis pack")

        model_dest = workspace / "model-drift"
        shutil.copytree(full_dest, model_dest)
        seed_legacy_model_drift(model_dest)
        model_audit = run_json([sys.executable, str(AUDIT), str(model_dest), "--format", "json"], ROOT)
        model_findings = {finding["code"]: finding for finding in model_audit.get("findings", [])}
        model_codes = set(model_findings)
        if "MODEL001" not in model_codes:
            raise RuntimeError("A repo with deprecated MiniMax surfaces and no model-operating-profile should emit MODEL001")
        if model_findings["MODEL001"].get("severity") != "error":
            raise RuntimeError("Deprecated package-managed MiniMax drift should emit MODEL001 as an error, not a warning")

        repair_dest = workspace / "repair"
        shutil.copytree(full_dest, repair_dest)
        shutil.rmtree(repair_dest / "diagnosis", ignore_errors=True)
        (repair_dest / "docs" / "process" / "workflow.md").write_text("# drifted workflow\n", encoding="utf-8")
        seed_legacy_bootstrap_tool(repair_dest)
        repair_payload = run_json([sys.executable, str(REPAIR), str(repair_dest)], ROOT)
        if repair_payload.get("verification", {}).get("clean") is True:
            raise RuntimeError("Deterministic repair verification should not report clean while pending process verification or placeholder local-skill follow-up remains")
        if repair_payload.get("verification", {}).get("pending_process_verification") is not True:
            raise RuntimeError("Repair verification should report pending_process_verification when the workflow state reopens backlog trust checks")

        repaired_workflow = json.loads((repair_dest / ".opencode" / "state" / "workflow-state.json").read_text(encoding="utf-8"))
        if repaired_workflow.get("process_version") != 6:
            raise RuntimeError("Repair should update workflow-state to process version 6")
        if repaired_workflow.get("pending_process_verification") is not True:
            raise RuntimeError("Repair should reopen post-migration verification")
        if not repaired_workflow.get("process_last_changed_at"):
            raise RuntimeError("Repair should record process_last_changed_at")
        for key in ("bootstrap", "lane_leases", "state_revision"):
            if key not in repaired_workflow:
                raise RuntimeError(f"Repair should preserve workflow key `{key}`")

        repaired_provenance = json.loads((repair_dest / ".opencode" / "meta" / "bootstrap-provenance.json").read_text(encoding="utf-8"))
        if not repaired_provenance.get("repair_history"):
            raise RuntimeError("Repair should append repair_history")
        managed_surfaces = repaired_provenance.get("managed_surfaces", {})
        replace_on_retrofit = managed_surfaces.get("replace_on_retrofit", [])
        project_specific_follow_up = managed_surfaces.get("project_specific_follow_up", [])
        if "opencode.jsonc" not in replace_on_retrofit:
            raise RuntimeError("Repair provenance should list opencode.jsonc as a deterministic managed surface")
        if ".opencode/skills" not in project_specific_follow_up:
            raise RuntimeError("Repair provenance should mark .opencode/skills as a project-specific follow-up surface")

        repaired_workflow_doc = (repair_dest / "docs" / "process" / "workflow.md").read_text(encoding="utf-8")
        if "# Workflow" not in repaired_workflow_doc:
            raise RuntimeError("Repair should restore docs/process/workflow.md from the scaffold")
        repaired_bootstrap_tool = (repair_dest / ".opencode" / "tools" / "environment_bootstrap.ts").read_text(encoding="utf-8")
        for expected in ("[project.optional-dependencies]", "[dependency-groups]", "[tool.uv.dev-dependencies]", "[tool.pytest.ini_options]"):
            if expected not in repaired_bootstrap_tool:
                raise RuntimeError("Repair should restore the broadened environment_bootstrap surface for alternate dev layouts and pyproject-only pytest detection")
        repaired_handoff = (repair_dest / ".opencode" / "tools" / "handoff_publish.ts").read_text(encoding="utf-8")
        if "validateHandoffNextAction" not in repaired_handoff or repaired_handoff.find("const handoffBlocker = await validateHandoffNextAction") >= repaired_handoff.find("await refreshRestartSurfaces"):
            raise RuntimeError("Repair should restore truthful handoff gating before restart-surface publication")

        print("Scafforge smoke test passed.")
        return 0
    finally:
        shutil.rmtree(workspace, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any


def rewrite_tool_imports(text: str) -> str:
    return text.replace('from "../lib/workflow"', 'from "../lib/workflow.ts"')


def require_node() -> str:
    node = shutil.which("node")
    if node:
        return node
    raise RuntimeError("Node.js is required to execute generated repo tools for pivot runtime support.")


def require_repo_path(repo_root: Path, relative_path: str) -> Path:
    path = (repo_root / relative_path).resolve()
    if not path.exists():
        raise RuntimeError(f"Generated repo path does not exist: {relative_path}")
    try:
        path.relative_to(repo_root)
    except ValueError as exc:
        raise RuntimeError(f"Generated repo path must stay inside the repo root: {relative_path}") from exc
    return path


def prepare_runtime_mirror(repo_root: Path, tool_path: Path, workflow_path: Path, temp_root: Path) -> Path:
    mirrored_tool = temp_root / ".opencode" / "tools" / tool_path.name
    mirrored_tool.parent.mkdir(parents=True, exist_ok=True)
    mirrored_tool.write_text(rewrite_tool_imports(tool_path.read_text(encoding="utf-8")), encoding="utf-8")

    mirrored_workflow = temp_root / ".opencode" / "lib" / "workflow.ts"
    mirrored_workflow.parent.mkdir(parents=True, exist_ok=True)
    mirrored_workflow.write_text(workflow_path.read_text(encoding="utf-8"), encoding="utf-8")

    plugin_dir = temp_root / "node_modules" / "@opencode-ai" / "plugin"
    plugin_dir.mkdir(parents=True, exist_ok=True)
    (plugin_dir / "package.json").write_text('{"name":"@opencode-ai/plugin","type":"module"}\n', encoding="utf-8")
    (plugin_dir / "index.js").write_text(
        "\n".join(
            [
                "function chain() {",
                "  return {",
                "    describe() { return this },",
                "    optional() { return this },",
                "    int() { return this },",
                "  }",
                "}",
                "const schema = {",
                "  string: () => chain(),",
                "  boolean: () => chain(),",
                "  enum: () => chain(),",
                "  array: () => chain(),",
                "  number: () => chain(),",
                "}",
                "export function tool(definition) {",
                "  return definition",
                "}",
                "tool.schema = schema",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return mirrored_tool


def run_generated_tool(repo_root: Path, relative_tool_path: str, args: dict[str, object]) -> dict[str, Any]:
    node = require_node()
    tool_path = require_repo_path(repo_root, relative_tool_path)
    workflow_path = require_repo_path(repo_root, ".opencode/lib/workflow.ts")

    with tempfile.TemporaryDirectory(prefix="scafforge-pivot-runtime-") as temp_dir:
        temp_root = Path(temp_dir)
        mirrored_tool = prepare_runtime_mirror(repo_root, tool_path, workflow_path, temp_root)
        runner = temp_root / "tool-runner.mjs"
        runner.write_text(
            "\n".join(
                [
                    'import { pathToFileURL } from "node:url"',
                    "const toolPath = process.env.SCAFFORGE_TOOL_PATH",
                    "if (!toolPath) throw new Error('Missing SCAFFORGE_TOOL_PATH')",
                    "const mod = await import(pathToFileURL(toolPath).href)",
                    "const rawArgs = process.env.SCAFFORGE_TOOL_ARGS || '{}'",
                    "const payload = await mod.default.execute(JSON.parse(rawArgs))",
                    "console.log(payload)",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        env = os.environ.copy()
        env["SCAFFORGE_TOOL_PATH"] = str(mirrored_tool)
        env["SCAFFORGE_TOOL_ARGS"] = json.dumps(args)
        env["NODE_PATH"] = str(temp_root / "node_modules")
        result = subprocess.run(
            [node, "--experimental-strip-types", str(runner)],
            cwd=repo_root,
            check=False,
            capture_output=True,
            text=True,
            env=env,
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"Generated tool execution failed for {relative_tool_path}\n"
                f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
            )
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                f"Generated tool did not return valid JSON for {relative_tool_path}\nSTDOUT:\n{result.stdout}"
            ) from exc

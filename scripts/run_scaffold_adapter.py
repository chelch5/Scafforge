from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ADAPTER_CONTRACT_VERSION = "scafforge-core.scaffold-adapter.v1"
SCAFFOLD_PROFILE_MINIMAL = "minimal-operable"
SCAFFOLD_PROFILE_FULL = "full-specialization"
SCAFFOLD_PROFILES = {SCAFFOLD_PROFILE_MINIMAL, SCAFFOLD_PROFILE_FULL}
ROOT = Path(__file__).resolve().parents[1]
BOOTSTRAP = ROOT / "skills" / "repo-scaffold-factory" / "scripts" / "bootstrap_repo_scaffold.py"
VERIFY = ROOT / "skills" / "repo-scaffold-factory" / "scripts" / "verify_generated_scaffold.py"
OUTPUT_RELATIVE = Path(".opencode") / "state" / "scaffold-adapter-output.json"
VERIFY_RELATIVE = Path(".opencode") / "state" / "scaffold-adapter-verification.json"
FINISH_CONTRACT_FIELDS = (
    "deliverable_kind",
    "placeholder_policy",
    "visual_finish_target",
    "audio_finish_target",
    "content_source_plan",
    "licensing_or_provenance_constraints",
    "finish_acceptance_signals",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Backend-callable Scafforge Core scaffold adapter.")
    parser.add_argument("--input", required=True, help="Path to scaffold adapter JSON input.")
    return parser.parse_args()


def read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"Unable to read JSON input {path}: {error}") from error
    if not isinstance(payload, dict):
        raise ValueError("Adapter input must be a JSON object.")
    return payload


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "scafforge-project"


def repo_id_from_slug(slug: str) -> str:
    return f"repo_{slug.replace('-', '_')}"


def artifact(label: str, ref: str) -> dict[str, str]:
    return {"label": label, "ref": ref}


def blocked(reason: str, input_payload: dict[str, Any] | None = None, blockers: list[str] | None = None) -> dict[str, Any]:
    scaffold_profile = None
    if input_payload:
        scaffold_profile = str(input_payload.get("scaffold_profile") or SCAFFOLD_PROFILE_FULL).strip()
    return {
        "adapter_contract_version": ADAPTER_CONTRACT_VERSION,
        "status": "blocked",
        "generated_repo_path": None,
        "repo_id": None,
        "scaffold_profile": scaffold_profile,
        "specialization_status": None,
        "proof_refs": [],
        "roadmap_ref": None,
        "ticket_manifest_ref": None,
        "validation_status": "blocked",
        "blockers": blockers or [reason],
        "idempotency_key": input_payload.get("idempotency_key") if input_payload else None,
        "created_at": now_iso(),
    }


def validate_input(payload: dict[str, Any]) -> list[str]:
    required = ["approved_brief_path", "target_repo_root", "repo_slug", "idempotency_key", "operator_identity"]
    blockers = [f"{field} is required" for field in required if not str(payload.get(field, "")).strip()]
    scaffold_profile = str(payload.get("scaffold_profile") or SCAFFOLD_PROFILE_FULL).strip()
    if scaffold_profile not in SCAFFOLD_PROFILES:
        blockers.append(
            "scaffold_profile must be one of: "
            + ", ".join(sorted(SCAFFOLD_PROFILES))
        )
    approved_brief = Path(str(payload.get("approved_brief_path", ""))).expanduser()
    if not approved_brief.exists():
        blockers.append(f"approved_brief_path does not exist: {approved_brief}")
    blockers.extend(validate_finish_contract(payload))
    return blockers


def validate_finish_contract(payload: dict[str, Any]) -> list[str]:
    has_nested_contract = "product_finish_contract" in payload
    has_top_level_contract = any(field in payload for field in FINISH_CONTRACT_FIELDS)
    if not has_nested_contract and not has_top_level_contract:
        return []

    contract = payload.get("product_finish_contract")
    if has_nested_contract and not isinstance(contract, dict):
        return ["product_finish_contract must be an object when supplied"]

    blockers: list[str] = []
    for field in FINISH_CONTRACT_FIELDS:
        value = finish_contract_value(payload, field)
        if value is None:
            blockers.append(f"product_finish_contract.{field} is required when a product finish contract is supplied")
    return blockers


def load_existing_output(repo_root: Path, idempotency_key: str) -> dict[str, Any] | None:
    output_path = repo_root / OUTPUT_RELATIVE
    if not output_path.exists():
        return None
    try:
        payload = read_json(output_path)
    except ValueError:
        return None
    if payload.get("idempotency_key") == idempotency_key:
        payload["idempotent_replay"] = True
        return payload
    return None


def run_command(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def run_in_repo(repo_root: Path, command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=repo_root,
        text=True,
        capture_output=True,
        check=False,
    )


def ensure_generated_repo_git_worktree(repo_root: Path) -> list[str]:
    if (repo_root / ".git").exists():
        return []

    git = shutil.which("git")
    if git is None:
        return ["git executable is required to initialize generated repo worktrees."]

    init = run_in_repo(repo_root, [git, "init", "-b", "main"])
    if init.returncode == 0:
        return []

    fallback = run_in_repo(repo_root, [git, "init"])
    if fallback.returncode != 0:
        return [fallback.stderr or fallback.stdout or init.stderr or init.stdout or "git init failed."]

    rename = run_in_repo(repo_root, [git, "branch", "-m", "main"])
    if rename.returncode != 0:
        return [rename.stderr or rename.stdout or "git branch -m main failed."]

    return []


def write_adapter_output(repo_root: Path, payload: dict[str, Any]) -> None:
    output_path = repo_root / OUTPUT_RELATIVE
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def build_output(
    repo_root: Path,
    repo_id: str,
    idempotency_key: str,
    verify_payload: dict[str, Any],
    scaffold_profile: str,
) -> dict[str, Any]:
    specialization_status = (
        "pending" if scaffold_profile == SCAFFOLD_PROFILE_MINIMAL else "selected"
    )
    return {
        "adapter_contract_version": ADAPTER_CONTRACT_VERSION,
        "status": "completed",
        "generated_repo_path": str(repo_root),
        "repo_id": repo_id,
        "scaffold_profile": scaffold_profile,
        "minimal_operable_status": (
            "passed" if verify_payload.get("verification_passed") is True else "failed"
        ),
        "specialization_status": specialization_status,
        "profile_next_actions": (
            [
                "Run project-skill-bootstrap.",
                "Run opencode-team-bootstrap.",
                "Run agent-prompt-engineering.",
                "Run ticket-pack-builder.",
                "Run final greenfield-continuation verification before handoff.",
            ]
            if scaffold_profile == SCAFFOLD_PROFILE_MINIMAL
            else ["Continue the same-session full-specialization stages before final continuation proof."]
        ),
        "proof_refs": [
            artifact("Bootstrap provenance", ".opencode/meta/bootstrap-provenance.json"),
            artifact("Bootstrap verification", str(VERIFY_RELATIVE).replace("\\", "/")),
            artifact("Adapter output", str(OUTPUT_RELATIVE).replace("\\", "/")),
        ],
        "roadmap_ref": artifact("Ticket board", "tickets/BOARD.md"),
        "ticket_manifest_ref": artifact("Ticket manifest", "tickets/manifest.json"),
        "validation_status": "passed" if verify_payload.get("verification_passed") is True else "failed",
        "blockers": [],
        "idempotency_key": idempotency_key,
        "created_at": now_iso(),
    }


def run_adapter(input_path: Path) -> tuple[int, dict[str, Any]]:
    try:
        payload = read_json(input_path)
    except ValueError as error:
        return 2, blocked(str(error))

    blockers = validate_input(payload)
    if blockers:
        return 2, blocked("Invalid adapter input.", payload, blockers)

    project_name = str(payload.get("project_name") or payload.get("repo_slug") or "Scafforge Project").strip()
    repo_slug = slugify(str(payload["repo_slug"]))
    target_repo_root = Path(str(payload["target_repo_root"])).expanduser().resolve()
    repo_root = target_repo_root / repo_slug
    idempotency_key = str(payload["idempotency_key"]).strip()
    scaffold_profile = str(payload.get("scaffold_profile") or SCAFFOLD_PROFILE_FULL).strip()
    if scaffold_profile == SCAFFOLD_PROFILE_FULL:
        return 2, blocked(
            "Full specialization is not completed by this adapter.",
            payload,
            [
                "full-specialization requires project-skill-bootstrap, opencode-team-bootstrap, agent-prompt-engineering, ticket-pack-builder, and final continuation proof before it can be marked completed."
            ],
        )
    existing = load_existing_output(repo_root, idempotency_key)
    if existing:
        return 0, existing
    if repo_root.exists() and any(repo_root.iterdir()):
        return 2, blocked(
            "Generated repo collision.",
            payload,
            [f"{repo_root} already exists and was not created by idempotency key {idempotency_key}."],
        )

    stack_label = str(payload.get("stack_label") or payload.get("project_family") or "framework-agnostic")
    command = [
        sys.executable,
        str(BOOTSTRAP),
        "--dest",
        str(repo_root),
        "--project-name",
        project_name,
        "--project-slug",
        repo_slug,
        "--agent-prefix",
        repo_slug,
        "--model-provider",
        str(payload.get("model_provider") or "openrouter"),
        "--planner-model",
        str(payload.get("planner_model") or "openai/gpt-5-mini"),
        "--implementer-model",
        str(payload.get("implementer_model") or "openai/gpt-5-mini"),
        "--utility-model",
        str(payload.get("utility_model") or "openai/gpt-5-mini"),
        "--stack-label",
        stack_label,
        "--scope",
        "full",
        "--scaffold-profile",
        scaffold_profile,
    ]
    append_finish_contract_args(command, payload)
    command.append("--force")
    bootstrap = run_command(command)
    if bootstrap.returncode != 0:
        return 2, blocked("Scaffold bootstrap failed.", payload, [bootstrap.stderr or bootstrap.stdout])

    approved_brief_path = Path(str(payload["approved_brief_path"])).expanduser().resolve()
    approved_brief_target = repo_root / "docs" / "spec" / "APPROVED-BRIEF.json"
    approved_brief_target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(approved_brief_path, approved_brief_target)

    git_blockers = ensure_generated_repo_git_worktree(repo_root)
    if git_blockers:
        return 2, blocked("Generated repo git initialization failed.", payload, git_blockers)

    verify = run_command([
        sys.executable,
        str(VERIFY),
        str(repo_root),
        "--verification-kind",
        "bootstrap-lane",
        "--format",
        "json",
    ])
    try:
        verify_payload = json.loads(verify.stdout)
    except json.JSONDecodeError:
        verify_payload = {
            "verification_passed": False,
            "findings": [{"problem": "Verifier returned non-JSON output.", "evidence": [verify.stdout, verify.stderr]}],
        }
    (repo_root / VERIFY_RELATIVE).write_text(json.dumps(verify_payload, indent=2) + "\n", encoding="utf-8")
    if verify.returncode != 0 or verify_payload.get("verification_passed") is not True:
        blockers = [
            str(finding.get("problem", "Scaffold verification failed."))
            for finding in verify_payload.get("findings", [])
            if isinstance(finding, dict)
        ]
        return 2, blocked("Scaffold verification failed.", payload, blockers or [verify.stderr or verify.stdout])

    output = build_output(
        repo_root,
        repo_id_from_slug(repo_slug),
        idempotency_key,
        verify_payload,
        scaffold_profile,
    )
    write_adapter_output(repo_root, output)
    return 0, output


def finish_contract_value(payload: dict[str, Any], key: str) -> str | None:
    value = payload.get(key)
    if value is None:
        contract = payload.get("product_finish_contract")
        if isinstance(contract, dict):
            value = contract.get(key)
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def append_finish_contract_args(command: list[str], payload: dict[str, Any]) -> None:
    finish_args = {
        "deliverable_kind": "--deliverable-kind",
        "placeholder_policy": "--placeholder-policy",
        "visual_finish_target": "--visual-finish-target",
        "audio_finish_target": "--audio-finish-target",
        "content_source_plan": "--content-source-plan",
        "licensing_or_provenance_constraints": "--licensing-or-provenance-constraints",
        "finish_acceptance_signals": "--finish-acceptance-signals",
    }
    for key in FINISH_CONTRACT_FIELDS:
        value = finish_contract_value(payload, key)
        if value is not None:
            command.extend([finish_args[key], value])


def main() -> int:
    args = parse_args()
    exit_code, payload = run_adapter(Path(args.input).expanduser().resolve())
    print(json.dumps(payload, indent=2))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())

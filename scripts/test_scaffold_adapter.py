from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ADAPTER = ROOT / "scripts" / "run_scaffold_adapter.py"


def run_adapter(input_path: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(ADAPTER), "--input", str(input_path)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def adapter_input(
    *,
    brief_path: Path,
    generated_root: Path,
    repo_slug: str,
    project_name: str,
    scaffold_profile: str,
    idempotency_key: str,
    project_family: str = "web-app",
    stack_label: str | None = None,
    finish_contract: dict[str, object] | None = None,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "adapter_contract_version": "scafforge-core.scaffold-adapter.v1",
        "approved_brief_path": str(brief_path),
        "target_repo_root": str(generated_root),
        "repo_slug": repo_slug,
        "project_name": project_name,
        "project_family": project_family,
        "lifecycle_preference": "durable",
        "scaffold_profile": scaffold_profile,
        "idempotency_key": idempotency_key,
        "operator_identity": "test",
    }
    if stack_label is not None:
        payload["stack_label"] = stack_label
    if finish_contract is not None:
        payload["product_finish_contract"] = finish_contract
    return payload


def assert_common_completed_payload(payload: dict[str, object]) -> Path:
    assert payload["adapter_contract_version"] == "scafforge-core.scaffold-adapter.v1"
    assert payload["status"] == "completed"
    assert payload["minimal_operable_status"] == "passed"
    repo_root = Path(str(payload["generated_repo_path"]))
    assert repo_root.exists()
    assert (repo_root / "tickets" / "manifest.json").exists()
    assert (repo_root / "tickets" / "BOARD.md").exists()
    assert (repo_root / "START-HERE.md").exists()
    assert (repo_root / ".opencode" / "state" / "workflow-state.json").exists()
    assert (repo_root / ".opencode" / "state" / "scaffold-adapter-verification.json").exists()
    assert (repo_root / "docs" / "spec" / "APPROVED-BRIEF.json").exists()
    assert (repo_root / ".git").exists()
    return repo_root


def main() -> int:
    temp_root = Path(tempfile.mkdtemp(prefix="scafforge-core-adapter-"))
    try:
        brief_path = temp_root / "approved-brief.json"
        write_json(
            brief_path,
            {
                "project_name": "Adapter Contract Probe",
                "project_family": "web-app",
                "brief": "Create a small adapter contract proof repo.",
            },
        )
        full_input_path = temp_root / "adapter-input-full.json"
        generated_root = temp_root / "generated"
        write_json(
            full_input_path,
            adapter_input(
                brief_path=brief_path,
                generated_root=generated_root,
                repo_slug="adapter-contract-probe",
                project_name="Adapter Contract Probe",
                scaffold_profile="full-specialization",
                idempotency_key="idem_adapter_contract_probe",
            ),
        )

        first = run_adapter(full_input_path)
        assert first.returncode == 2
        first_payload = json.loads(first.stdout)
        assert first_payload["status"] == "blocked"
        assert first_payload["scaffold_profile"] == "full-specialization"
        assert "full-specialization requires" in first_payload["blockers"][0]

        second = run_adapter(full_input_path)
        assert second.returncode == 2
        second_payload = json.loads(second.stdout)
        assert second_payload["status"] == "blocked"

        minimal_input_path = temp_root / "adapter-input-minimal.json"
        write_json(
            minimal_input_path,
            adapter_input(
                brief_path=brief_path,
                generated_root=generated_root,
                repo_slug="adapter-contract-minimal",
                project_name="Adapter Contract Minimal",
                scaffold_profile="minimal-operable",
                idempotency_key="idem_adapter_contract_minimal",
                project_family="android_game",
                stack_label="godot-android-game",
                finish_contract={
                    "deliverable_kind": "complete Android educational game",
                    "placeholder_policy": "no_placeholders",
                    "visual_finish_target": "ship-ready child-friendly Android UI with no placeholder visuals",
                    "audio_finish_target": "spoken prompts, positive feedback, and looping music are present and validated",
                    "content_source_plan": "local procedural content and generated assets, with provenance recorded",
                    "licensing_or_provenance_constraints": "no external licensed assets required for this proof",
                    "finish_acceptance_signals": "A child can launch the Android build, complete a playable learning round, hear voice/music/feedback, and reach a reward flow.",
                },
            ),
        )
        minimal = run_adapter(minimal_input_path)
        if minimal.returncode != 0:
            raise AssertionError(minimal.stderr or minimal.stdout)
        minimal_payload = json.loads(minimal.stdout)
        minimal_repo_root = assert_common_completed_payload(minimal_payload)
        assert minimal_payload["scaffold_profile"] == "minimal-operable"
        assert minimal_payload["specialization_status"] == "pending"
        minimal_workflow = json.loads(
            (minimal_repo_root / ".opencode" / "state" / "workflow-state.json").read_text(encoding="utf-8")
        )
        assert minimal_workflow["scaffold_profile"]["name"] == "minimal-operable"
        assert minimal_workflow["scaffold_profile"]["specialization_status"] == "pending"
        minimal_provenance = json.loads(
            (minimal_repo_root / ".opencode" / "meta" / "bootstrap-provenance.json").read_text(encoding="utf-8")
        )
        assert minimal_provenance["profile_contract"]["minimal_operable_next_move"] == "environment_bootstrap"
        assert minimal_provenance["product_finish_contract"]["placeholder_policy"] == "no_placeholders"
        assert minimal_provenance["product_finish_contract"]["requires_visual_proof"] is True
        minimal_manifest = json.loads(
            (minimal_repo_root / "tickets" / "manifest.json").read_text(encoding="utf-8")
        )
        minimal_ticket_ids = {
            str(ticket.get("id"))
            for ticket in minimal_manifest["tickets"]
            if isinstance(ticket, dict)
        }
        assert {"VISUAL-001", "AUDIO-001", "ANDROID-001", "FINISH-VALIDATE-001", "RELEASE-001"} <= minimal_ticket_ids

        malformed_contract_input = temp_root / "malformed-contract-input.json"
        write_json(
            malformed_contract_input,
            adapter_input(
                brief_path=brief_path,
                generated_root=generated_root,
                repo_slug="adapter-contract-malformed",
                project_name="Adapter Contract Malformed",
                scaffold_profile="minimal-operable",
                idempotency_key="idem_adapter_contract_malformed",
                stack_label="godot-android-game",
                finish_contract={"placeholder_policy": "no_placeholders"},
            ),
        )
        malformed_contract = run_adapter(malformed_contract_input)
        assert malformed_contract.returncode == 2
        malformed_payload = json.loads(malformed_contract.stdout)
        assert malformed_payload["status"] == "blocked"
        assert any(
            "product_finish_contract.deliverable_kind" in blocker
            for blocker in malformed_payload["blockers"]
        )

        invalid_contract_type_input = temp_root / "invalid-contract-type-input.json"
        invalid_contract_payload = adapter_input(
            brief_path=brief_path,
            generated_root=generated_root,
            repo_slug="adapter-contract-invalid",
            project_name="Adapter Contract Invalid",
            scaffold_profile="minimal-operable",
            idempotency_key="idem_adapter_contract_invalid",
            stack_label="godot-android-game",
        )
        invalid_contract_payload["product_finish_contract"] = "no_placeholders"
        write_json(invalid_contract_type_input, invalid_contract_payload)
        invalid_contract_type = run_adapter(invalid_contract_type_input)
        assert invalid_contract_type.returncode == 2
        invalid_contract_payload_out = json.loads(invalid_contract_type.stdout)
        assert invalid_contract_payload_out["status"] == "blocked"
        assert any(
            "product_finish_contract must be an object" in blocker
            for blocker in invalid_contract_payload_out["blockers"]
        )

        invalid_input = temp_root / "invalid-input.json"
        write_json(invalid_input, {"repo_slug": "invalid", "scaffold_profile": "not-a-profile"})
        invalid = run_adapter(invalid_input)
        assert invalid.returncode == 2
        invalid_payload = json.loads(invalid.stdout)
        assert invalid_payload["status"] == "blocked"
        assert invalid_payload["blockers"]
        return 0
    finally:
        shutil.rmtree(temp_root, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sys


SHARED_VERIFIER_PATH = Path(__file__).resolve().parents[2] / "scafforge-audit" / "scripts" / "shared_verifier.py"


def load_shared_verifier():
    spec = spec_from_file_location("scafforge_generated_scaffold_verifier", SHARED_VERIFIER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load shared verifier from {SHARED_VERIFIER_PATH}")
    module = module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


SHARED_VERIFIER = load_shared_verifier()
verify_greenfield_bootstrap_lane = SHARED_VERIFIER.verify_greenfield_bootstrap_lane
verify_greenfield_continuation = SHARED_VERIFIER.verify_greenfield_continuation


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Verify that a generated scaffold is immediately continuable before greenfield handoff."
    )
    parser.add_argument("repo_root", help="Generated repository root to verify.")
    parser.add_argument("--format", choices=("text", "json", "both"), default="text")
    parser.add_argument(
        "--verification-kind",
        choices=("bootstrap-lane", "greenfield-continuation"),
        default="greenfield-continuation",
        help="Which greenfield proof layer to verify.",
    )
    return parser.parse_args()


def findings_payload(verification_kind: str, findings: list[object]) -> dict[str, object]:
    payload = {
        "repo_root": None,
        "verification_kind": verification_kind,
        "verification_passed": not findings,
        "finding_count": len(findings),
        "findings": [asdict(finding) for finding in findings],
    }
    if verification_kind == "greenfield_continuation":
        payload["immediately_continuable"] = not findings
    if verification_kind == "greenfield_bootstrap_lane":
        payload["bootstrap_lane_valid"] = not findings
    return payload


def render_text(repo_root: Path, verification_kind: str, findings: list[object]) -> str:
    if not findings:
        if verification_kind == "greenfield_bootstrap_lane":
            return f"PASS: {repo_root} preserves one valid bootstrap lane."
        return f"PASS: {repo_root} is immediately continuable."

    if verification_kind == "greenfield_bootstrap_lane":
        lines = [f"FAIL: {repo_root} does not preserve one valid bootstrap lane.", ""]
    else:
        lines = [f"FAIL: {repo_root} is not immediately continuable.", ""]
    for finding in findings:
        lines.append(f"[{finding.code}] {finding.problem}")
        if finding.evidence:
            lines.append(f"  Evidence: {finding.evidence[0]}")
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).expanduser().resolve()
    verification_kind = (
        "greenfield_bootstrap_lane"
        if args.verification_kind == "bootstrap-lane"
        else "greenfield_continuation"
    )
    findings = (
        verify_greenfield_bootstrap_lane(repo_root)
        if verification_kind == "greenfield_bootstrap_lane"
        else verify_greenfield_continuation(repo_root)
    )
    payload = findings_payload(verification_kind, findings)
    payload["repo_root"] = str(repo_root)

    if args.format in {"text", "both"}:
        print(render_text(repo_root, verification_kind, findings))
    if args.format in {"json", "both"}:
        if args.format == "both":
            print()
        print(json.dumps(payload, indent=2))

    return 0 if not findings else 2


if __name__ == "__main__":
    raise SystemExit(main())

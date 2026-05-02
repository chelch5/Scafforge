# Scafforge Core

Scafforge Core is the standalone scaffold package at the heart of the Scafforge ecosystem. In the canonical workspace it lives at `platform/scafforge-core/`, but it remains a complete product when cloned and opened by itself.

Scafforge Core turns raw project inputs into OpenCode-oriented repos with explicit truth ownership, deterministic workflow contracts, and one legal next move for the operator.

Scafforge Core is not the generated project, not a generic skill warehouse, and not the adjacent services that may later wrap the package. Package-vs-output boundary rules live in [AGENTS.md](AGENTS.md), and the current repo-wide document map lives in [references/documentation-authority-map.md](references/documentation-authority-map.md).

## What to read first

| Need | Read |
| --- | --- |
| Quick orientation | `README.md` |
| Package boundaries, authority, and standing rules | `AGENTS.md` |
| Human/operator routing | `USERGUIDE.md` |
| System structure and adjacent-service boundaries | `architecture.md` |
| Canonical contract detail | `references/*.md` via the documentation authority map |

The package competence bar is defined in [references/competence-contract.md](references/competence-contract.md). If the workflow stops exposing one legal next move, treat that as package evidence, not operator failure.

## What Scafforge ships

The package repo contains:

- `skills/` for package skills and template assets
- `references/` for durable contracts, ADRs, and matrices
- `scripts/` and `tests/` for validation and proof harnesses
- `active-audits/` for copied diagnosis evidence from generated repos
- `docs/plans/scafforge-core/` for the live package implementation portfolio (see bootstrap repo `docs/plans/`)

Generated repos inherit OpenCode-oriented operating surfaces such as `.opencode/agents/`, `.opencode/tools/`, `.opencode/plugins/`, `.opencode/commands/`, `.opencode/skills/`, `tickets/`, `docs/spec/CANONICAL-BRIEF.md`, `START-HERE.md`, and `.opencode/skills/model-operating-profile/SKILL.md`.

## Scaffold Profiles

Scafforge now has two first-class greenfield profiles:

- `minimal-operable` renders the managed scaffold surfaces needed for a durable restart: canonical brief, `START-HERE.md`, workflow state, ticket manifest and board, bootstrap provenance, validation hooks, and one legal next move (`environment_bootstrap`).
- `full-specialization` starts from the minimal-operable scaffold and continues through repo-local skills, project-specific agents, prompt hardening, backlog generation, final continuation verification, and handoff publication.

The minimal profile lets an adjacent backend stop after bootstrap-lane proof when it needs a fast durable scaffold. The full profile remains the default human-facing one-shot path for a ready-to-develop generated repo.

## Default Lifecycle

Greenfield generation is one kickoff run. Full-specialization continues from the minimal-operable scaffold in that same run.

```text
scaffold-kickoff
  -> spec-pack-normalizer
  -> repo-scaffold-factory:minimal-operable
  -> repo-scaffold-factory:verify-bootstrap-lane
  -> project-skill-bootstrap
  -> opencode-team-bootstrap
  -> agent-prompt-engineering
  -> ticket-pack-builder
  -> repo-scaffold-factory:verify-generated-scaffold
  -> handoff-brief
```

This path allows one batched blocking-decision round and then completes in one uninterrupted same-session generation run. No second Scafforge generation pass is required before development begins. Greenfield completion requires immediate continuation proof, not only surface agreement.

For game and asset-heavy repos, `asset-pipeline` is an optional extension after `project-skill-bootstrap` and before `opencode-team-bootstrap`.

## Lifecycle boundaries

Generation, audit, repair, and pivot are separate lifecycle stages.

- `scaffold-kickoff` is the only public generation entrypoint.
- `scafforge-audit`, `scafforge-repair`, and `scafforge-pivot` are later lifecycle tools, not part of the initial generation cycle.
- `scafforge-audit` always validates review evidence before findings become canonical and emits the full diagnosis pack.
- `skills/scafforge-repair/scripts/run_managed_repair.py` is the public repair contract entrypoint.
- `skills/scafforge-repair/scripts/apply_repo_process_repair.py` is the deterministic refresh engine for the first managed-repair phase only.
- `scafforge-pivot` is the public pivot contract for canonical-truth changes.

## Validation and release proof

Package validation entrypoints are:

- `npm run validate:contract`
- `npm run validate:smoke`
- `python3 scripts/integration_test_scafforge.py`
- `python3 scripts/validate_gpttalker_migration.py`

These commands prove the Scafforge package. They do not replace stack-specific release proof in generated repos. The authoritative Tier 1 stack proof contract lives in [references/stack-adapter-contract.md](references/stack-adapter-contract.md), and the package-owned answer for what "done" means per repo family lives in [references/validation-proof-matrix.json](references/validation-proof-matrix.json).

## Adjacent orchestration wrapper

An adjacent orchestration service may invoke `scaffold-kickoff` from a persisted approved brief and then schedule downstream PR-based phases.

- It owns job envelopes, idempotency or retry tokens, PR automation, and pause or resume controls.
- It stays read-only with respect to generated `tickets/manifest.json` and `.opencode/state/workflow-state.json`.
- `minimal-operable-verified` means bootstrap-lane proof passed with specialization truthfully pending.
- `scaffold-verified` means the full-specialization pass cleared VERIFY009 and has zero blocking VERIFY010 or VERIFY011 findings before downstream PR work begins.

The backend-callable scaffold adapter is `scripts/run_scaffold_adapter.py`. It accepts a versioned JSON input containing an approved brief path, target generated-repo root, repo slug, lifecycle preference, scaffold profile, idempotency key, and operator identity. It returns `scafforge-core.scaffold-adapter.v1` JSON with generated repo path, repo id, scaffold profile, minimal-operable status, specialization status, proof refs, roadmap ref, ticket manifest ref, validation status, blockers, and idempotency key. The adapter writes bootstrap-lane verification evidence into the generated repo and returns an idempotent replay for repeated calls with the same key.

## Adjacent control plane

An adjacent control plane is a client of orchestration truth, not a second workflow engine.

- It may render orchestration jobs, generated-repo truth projections, package investigations, and provider/router summaries.
- It must route approvals, overrides, pause/resume, retry, merge-approval, and router-policy changes through backend APIs.
- It must fail closed to read-only when auth, trust, or connectivity is ambiguous instead of falling back to direct GitHub, WSL, SSH, or repo-local mutation.
- CLI and API fallback must remain usable without the GUI.

Relevant operator references:

- [references/control-plane-client-contract.md](references/control-plane-client-contract.md)
- [references/control-plane-operator-workflows.md](references/control-plane-operator-workflows.md)

## Package maintenance rule

Contract changes are not done until the affected root docs, references, generated-template docs, and validator expectations move together in the same change set. Use [AGENTS.md](AGENTS.md) for the standing rule and [USERGUIDE.md](USERGUIDE.md) for the lightweight contributor checklist.

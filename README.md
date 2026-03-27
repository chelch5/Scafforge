# Scafforge v1

Scafforge is a strong-host skill bundle for coding agents. Install the skills into a compatible host, point the host at a repo with specs, plans, or design docs, and let the skill chain generate or repair a complete OpenCode-shaped project workspace for downstream execution.

The generated output is intentionally shaped for OpenCode-style repos with agents, tools, plugins, commands, local skills, ticketing, provenance, and a structured truth hierarchy.

Weak-model first remains the product bias. The package is designed to make weaker or cheaper models more reliable through deterministic workflow contracts, explicit truth ownership, and narrow guarded roles.

## Installation

Copy or symlink each folder under `skills/` into the host's skill directory. Keep each skill directory intact so its `SKILL.md`, `scripts/`, `assets/`, and `references/` remain together.

Scafforge should be treated as a skill bundle, not as a CLI product.

## Usage

1. Open a repo that contains specs, plans, notes, or design docs.
2. Tell the agent to scaffold, retrofit, repair, or diagnose the project, or invoke `scaffold-kickoff`.
3. The agent reads the inputs, asks one batched round of blocking decisions when needed, and routes through the correct skill path.
4. Output: a complete project repo or an evidence-backed diagnosis and repair path.

## Default scaffold chain

Greenfield generation is one kickoff run. The default chain is:

```text
scaffold-kickoff
  -> spec-pack-normalizer
  -> repo-scaffold-factory
  -> project-skill-bootstrap
  -> opencode-team-bootstrap
  -> agent-prompt-engineering
  -> ticket-pack-builder
  -> handoff-brief
```

This pass allows one batched blocking-decision round and then completes in one uninterrupted same-session generation run. No second Scafforge generation pass is required before development begins.

`scaffold-kickoff` remains the single public entrypoint for:
- greenfield scaffold
- retrofit scaffold
- managed repair or update
- diagnosis or review of an in-progress repo

## What the agent does

The package splits work between deterministic scripts and host reasoning:

- scripts handle mechanical scaffold generation, workflow audits, and deterministic managed-surface repair
- the host agent handles spec reading, decision packets, agent-team design, prompt hardening, ticket creation, and synthesized local skills

In the standard greenfield path, `agent-prompt-engineering` always runs before `ticket-pack-builder`. The pass may be light or heavy depending on the chosen models and project-specific coordination risk, but it is not skipped.

## What the generated repo contains

A full greenfield run produces:

- `docs/spec/CANONICAL-BRIEF.md`
- `tickets/manifest.json` and `tickets/BOARD.md`
- `.opencode/agents/`
- `.opencode/tools/`
- `.opencode/plugins/`
- `.opencode/commands/`
- `.opencode/skills/`
- `.opencode/state/`
- `.opencode/meta/bootstrap-provenance.json`
- `START-HERE.md`
- root docs such as `README.md` and `AGENTS.md`

## Truth hierarchy

Generated repos use a structured truth hierarchy so state does not drift:

| File | Owns |
|------|------|
| `docs/spec/CANONICAL-BRIEF.md` | Durable project facts, constraints, decisions, unresolved questions |
| `tickets/manifest.json` | Machine-readable queue state and registered artifact metadata |
| `tickets/BOARD.md` | Derived human-readable board |
| `.opencode/state/workflow-state.json` | Transient stage, approval, and process-version state |
| `.opencode/state/artifacts/` | Canonical artifact bodies, historical snapshots, and mirrored registry state |
| `.opencode/meta/bootstrap-provenance.json` | Scaffold provenance, synthesis history, and repair history |
| `START-HERE.md` | Top-level derived restart surface |

`START-HERE.md`, `.opencode/state/context-snapshot.md`, and `.opencode/state/latest-handoff.md` are derived restart surfaces. They must agree with `tickets/manifest.json` and `.opencode/state/workflow-state.json`; they do not outrank them.

## Package skills

| Skill | What it does |
|-------|-------------|
| `scaffold-kickoff` | Public entrypoint that classifies the run type and routes the chain |
| `spec-pack-normalizer` | Reads messy inputs, extracts facts, asks about ambiguities, writes the canonical brief |
| `repo-scaffold-factory` | Generates the base template tree and structural repo surfaces |
| `opencode-team-bootstrap` | Designs the project-specific agent team and operating layer |
| `ticket-pack-builder` | Creates or repairs a wave-based ticket backlog and remediation follow-up |
| `project-skill-bootstrap` | Creates project-local skills from repo evidence and stack needs |
| `agent-prompt-engineering` | Hardens prompts for generated agents, commands, and workflow surfaces |
| `scafforge-audit` | Runs read-only workflow diagnosis, review validation, and the diagnosis pack |
| `scafforge-repair` | Applies safe workflow-contract repair and managed-surface refreshes |
| `handoff-brief` | Publishes `START-HERE.md` and the restart surface |

## Diagnosis and repair

Generation, audit, and repair are separate lifecycle stages.

- `scaffold-kickoff` is the only public generation entrypoint.
- Initial generation ends at `handoff-brief`.
- `scafforge-audit` and `scafforge-repair` are later lifecycle tools, not part of the initial generation cycle.

- `scafforge-audit` is read-only and always validates review evidence, runs the audit script, and emits the four-report diagnosis pack in the subject repo's `diagnosis/` folder.
- `scafforge-repair` is the public repair contract: it must apply safe managed-surface repairs, continue into any required local-skill or agent/prompt/ticket follow-up, record provenance, and route ticket follow-up when needed.
- Source-layer `EXEC*` follow-up and visible `pending_process_verification` are not, by themselves, proof that managed repair failed. They remain live repo follow-up after the managed workflow layer is repaired.
- `skills/scafforge-repair/scripts/run_managed_repair.py` is the public fail-closed repair runner. It emits the machine-readable repair plan and execution record, reruns verification, and blocks handoff when required downstream stages still have not run.
- `skills/scafforge-repair/scripts/apply_repo_process_repair.py` is the deterministic refresh engine for the first repair phase only. Invoking that script alone does not satisfy the full repair contract unless no downstream regeneration or ticket follow-up is required.
- When the diagnosis identifies package defects or prevention gaps, the user manually copies the diagnosis pack into the Scafforge dev repo, package changes are implemented there, and repair happens only after returning to the subject repo with the updated package surface.
- If repeated diagnosis packs report the same repair-routed findings and no newer package or process-version change exists, stop auditing the subject repo and fix the Scafforge package first.

PR comments, review threads, and check metadata are optional evidence only. They do not become canonical findings until the repo validates them.

## Generated repo-local skills

Scafforge ships the scaffold logic that creates `.opencode/skills/` inside generated repos. Those local skills belong to the output repo operating layer, not to Scafforge's own top-level package skill taxonomy.

Baseline generated local skills include:

- `project-context`
- `repo-navigation`
- `stack-standards`
- `model-operating-profile`
- `ticket-execution`
- `review-audit-bridge`
- `docs-and-handoff`
- `workflow-observability`
- `research-delegation`
- `local-git-specialist`
- `isolation-guidance`

`review-audit-bridge` remains repo-local generated functionality. It helps the live repo review itself, recommend remediation tickets, and emit process-log output without becoming a top-level Scafforge skill.

## Existing repo path

For repos that already have code, start at `scaffold-kickoff` and let it classify the path:

```text
retrofit
  -> spec-pack-normalizer (if needed)
  -> opencode-team-bootstrap
  -> project-skill-bootstrap
  -> ticket-pack-builder
  -> scafforge-audit
  -> handoff-brief

managed repair or update
  -> scafforge-repair
  -> project-skill-bootstrap (if repair is needed)
  -> opencode-team-bootstrap (if project-specific drift remains)
  -> agent-prompt-engineering (if prompts or model-profile surfaces changed)
  -> ticket-pack-builder (if follow-up is needed)
  -> handoff-brief

diagnosis or review
  -> scafforge-audit
  -> manual diagnosis-pack handoff into the Scafforge dev repo when package work is required
  -> scafforge-repair (only if recommended and the required package changes already exist)
  -> handoff-brief
```

## Design principles

- One orchestrated cycle instead of scaffold-now-enrich-later by default
- Agent does creative work, scripts do deterministic mechanical work
- Structured truth hierarchy with exact ownership boundaries
- Weak-model first workflow contracts
- Discovery as research, not deployment
- One kickoff run for full-depth generation
- No standalone package-level refinement route

---
name: repo-navigation
description: Navigate the canonical docs, ticket files, and OpenCode operating surfaces for this repo. Use when an agent needs to find where process, state, or handoff information lives without scanning the entire repository.
---

# Repo Navigation

Before navigating, call `skill_ping` with `skill_id: "repo-navigation"` and `scope: "project"`.

Canonical paths:

- `README.md`
- `START-HERE.md`
- `AGENTS.md`
- `docs/spec/CANONICAL-BRIEF.md`
- `docs/process/workflow.md`
- `docs/process/agent-catalog.md`
- `docs/process/model-matrix.md`
- `tickets/README.md`
- `tickets/manifest.json`
- `tickets/BOARD.md`
- `.opencode/state/workflow-state.json`
- `.opencode/state/artifacts/registry.json`
- `.opencode/meta/bootstrap-provenance.json`

Navigation notes:

- Gameplay code and scenes live under `scripts/` and `scenes/`.
- Android release work should route through `tickets/ANDROID-001.md`, `tickets/RELEASE-001.md`, and `.opencode/skills/android-build-and-test/SKILL.md`.
- Repair and verification context lives under `diagnosis/`, `.opencode/meta/repair-execution.json`, and `.opencode/meta/repair-follow-on-state.json`.

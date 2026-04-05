---
name: project-context
description: Load the local source-of-truth docs for this repo. Use when an OpenCode agent needs the project mission, canonical brief, workflow, ticket state, or current operating status before planning, implementing, reviewing, or handing off work.
---

# Project Context

Before reading anything else, call `skill_ping` with `skill_id: "project-context"` and `scope: "project"`.

Read these first:

1. `START-HERE.md`
2. `AGENTS.md`
3. `docs/spec/CANONICAL-BRIEF.md`
4. `docs/process/workflow.md`
5. `docs/process/agent-catalog.md`
6. `docs/process/model-matrix.md`
7. `tickets/README.md`
8. `tickets/manifest.json`
9. `tickets/BOARD.md`

Project focus:

- This repo is a Godot Android 2D platformer focused on a readable, fair first playable vertical slice.
- Treat movement feel, glitch telegraphing, checkpoint flow, and touch readability as correctness-critical, not polish.
- Treat `docs/spec/CANONICAL-BRIEF.md`, `tickets/manifest.json`, and `.opencode/state/workflow-state.json` as the canonical truth hierarchy before using any derived restart prose.

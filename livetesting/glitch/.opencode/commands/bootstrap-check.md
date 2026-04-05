---
description: Verify and refresh environment bootstrap readiness for the current repo
agent: glitch-team-leader
model: minimax-coding-plan/MiniMax-M2.7
---

Resolve the current workflow state, inspect bootstrap readiness, and route the environment bootstrap lane if runtime, dependency, or verification prerequisites are missing or stale.

Rules:

- Treat this slash command as a human entrypoint only.
- Use `ticket_lookup` and `environment_bootstrap` instead of manual dependency improvisation.
- Keep bootstrap proof global to the repo and register the resulting artifact.
- If bootstrap is already ready, summarize the current proof and stop.

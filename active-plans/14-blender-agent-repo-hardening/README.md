# Blender-Agent Repo Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Status:** DONE
**Implementation Outcome:** The adjacent `blender-agent` repo was hardened on 2026-04-22 and merged through PR `#3`, including machine-readable capability/proof artifacts, tighter client docs, and headless-proof validation.
**Goal:** Harden the separate `blender-agent` repository into a truthful, testable, headless-capable Blender automation system with stable tool contracts, stronger QA, and packaging that Scafforge can rely on honestly.

**Architecture:** `blender-agent` already has a substantial internal plan pack and a large skill set. This Scafforge-side plan does not replace those plans. It turns them into a cross-repo execution program focused on the gaps that matter most to Scafforge: honest tool maturity, Linux/headless viability, deterministic QA/export behavior, and stable packaging/integration contracts.

**Tech Stack / Surfaces:** the adjacent `blender-agent` repo, `mcp-server/`, `skills-src/`, `packaged-skills/`, the repo’s `plans/`, packaging/install docs, CI/test surfaces.
**Depends On:** `04-asset-quality-and-blender-excellence` for Scafforge-side quality requirements.
**Unblocks:** truthful Blender integration in Scafforge’s asset and quality plans, and safer Blender-based downstream workflows.
**Primary Sources:** the `blender-agent` repo root docs, `mcp-server/TOOL_IMPLEMENTATION_STATUS.md`, `plans/03-mcp-server-hardening.md`, `plans/05-quality-and-engine-validation.md`, and the skill inventory under `skills-src/`.

---

## Problem statement

`blender-agent` already admits the right thing: it is a strong baseline, not a finished system. Its own repo documents certified, partial, and experimental tool families. That honesty is good, but Scafforge still needs a real cross-repo plan that says:

- what must improve there before Scafforge relies on it more heavily
- how headless or Linux-first operation should be validated
- which server, skill, QA, and packaging changes matter most

## Required deliverables

- a repo-level hardening priority map for `blender-agent`
- a stable contract for certified versus partial versus preview tool families
- stronger headless/runtime validation guidance
- QA/export validation tied to game-engine handoff reality
- packaging and installation guidance that works for the clients Scafforge cares about
- a post-hardening handoff back into Scafforge’s Blender support references
- a baseline status snapshot in this plan folder so implementation can compare the hardened surface against a frozen starting point

## Adjacent repo surfaces likely to change during implementation

- `blender-agent/README.md`
- `blender-agent/mcp-server/TOOL_IMPLEMENTATION_STATUS.md`
- `blender-agent/mcp-server/src/blender_mcp_server/server.py`
- `blender-agent/mcp-server/src/blender_mcp_server/server_v2.py`
- `blender-agent/mcp-server/src/blender_mcp_server/runner.py`
- `blender-agent/mcp-server/src/blender_mcp_server/security.py`
- `blender-agent/mcp-server/src/blender_mcp_server/bridge_runtime.py`
- fixture and test surfaces under `mcp-server/tests/`
- `skills-src/` and packaged-skill outputs
- install/package docs and cross-client integration notes

## Priority truths already visible in the repo

- the default shipped API is still legacy v1
- v2 exists but is explicitly preview/transition surface
- live-session features depend on a running Blender add-on runtime
- many tool families remain partial or experimental

Scafforge should treat these as constraints, not as bugs to ignore.

## Phase plan

### Phase 1: Freeze the public contract honestly

- [ ] Audit the certified, partial, experimental, and preview tool lists and make sure docs, code, and tests agree.
- [ ] Decide which tool names are too broad for the currently supported behavior and need narrower contracts.
- [ ] Define when v2 is allowed to be used and when Scafforge must still target the v1 shipped API.
- [ ] Record the v1-versus-v2 boundary in a structured machine-readable contract artifact inside `blender-agent`, such as `mcp-server/capability-contract.json`, not only as prose scattered across README text.
- [ ] Freeze a baseline snapshot of the current maturity table and hardening priorities in this plan folder before implementation starts.
- [ ] Ensure no packaging or README claim outruns the actual maturity table.

### Phase 2: Harden the server runtime and safety posture

- [ ] Prioritize the server hardening tasks already called out in the repo’s own plan: runner isolation, structured result envelopes, security mode separation, and payload validation.
- [ ] Improve unsafe/Python escape-hatch gating and observability.
- [ ] Ensure headless runs and dry-run behavior do not depend on interactive Blender assumptions.
- [ ] Make warnings, diagnostics, and partial-execution signals machine-readable.

### Phase 3: Certify the highest-value tool families

- [ ] Choose the tool families Scafforge needs most: scene organization, modifiers, UVs, materials, export, render preview, and QA.
- [ ] Build representative fixture coverage for each certified lane.
- [ ] Downgrade or narrow any tool whose advertised category is broader than what the tests prove.
- [ ] Keep deterministic naming, transforms, and object/report behavior as explicit validation targets.

### Phase 4: Strengthen QA and engine handoff

- [ ] Expand `quality_validate` into profile-based QA that matches the repo’s own quality plan (`draft`, `game_asset`, `hero_asset`, `animation_export`).
- [ ] Validate export presets and handoff assumptions for Godot, Unity, and Unreal against stable interchange artifacts.
- [ ] Treat Unity and Unreal validation as interchange-format structural verification only by default; any real engine-runtime import testing requires a separately approved exception and must not be assumed in the base plan.
- [ ] Ensure export and QA results are suitable for Scafforge to consume as evidence later.
- [ ] Add screenshot/render or preview artifacts where they materially improve trust.

### Phase 5: Redesign or prune the skill layer where necessary

- [ ] Compare `skills-src/` against the real tool maturity table and remove any promise the server cannot keep.
- [ ] Rewrite skills as deterministic playbooks that match the certified tool contracts.
- [ ] Ensure art-critique and quality skills are grounded in real QA or render surfaces, not only subjective language.
- [ ] Keep packaged skills synchronized with the validated source skills.

### Phase 6: Packaging, install, and Linux/headless readiness

- [ ] Define the supported installation paths for Codex, Claude Code, and Opencode clearly.
- [ ] Treat other MCP hosts as out of scope for this plan unless a follow-on plan explicitly adds them.
- [ ] Add or harden Linux-first/headless setup and CI notes where the repo still assumes an interactive Windows workstation.
- [ ] Make sure the repo can explain what works in a fully headless Blender environment versus what still needs local GUI/runtime support.
- [ ] Ensure packaging does not duplicate server code or drift between clients.
- [ ] Name the concrete headless test infrastructure in `blender-agent`, such as a dedicated `mcp-server/tests/headless/` lane or equivalent, and define what a passing headless run looks like.
- [ ] Require evidence from a real background Blender invocation path, such as `blender --background`-backed tests or an equivalent CI lane, before claiming Linux/headless support.
- [ ] Require a concrete cross-repo handoff proof package, such as `HARDENING-PROOF.json` in the `blender-agent` repo root, with at minimum: capability table version, structured v1/v2 contract path, certified tool families, and headless-proof artifact locations.
- [ ] Define the acceptable headless proof format for Scafforge handoff: either a committed structured result artifact such as `mcp-server/tests/headless/results.json` or a named CI workflow result tied back to the hardened capability table.
- [ ] As a final handoff step, re-evaluate Scafforge’s Blender references against the hardened `blender-agent` capability table.
- [ ] Treat Scafforge-side doc updates as blocked until `blender-agent` can point to both a post-hardening capability table and a concrete headless-validation proof artifact or CI result that matches the narrowed contract.
- [ ] Verify that plan `04` already created `skills/project-skill-bootstrap/references/blender-support-matrix.md` before updating it here; if it does not exist yet, stop and resolve the plan `04` dependency first.
- [ ] Update `skills/project-skill-bootstrap/references/blender-support-matrix.md` as a deliberate second-pass refresh after hardening, not as a one-time snapshot of the pre-hardening state from plan `04`.

## Validation and proof requirements

- `blender-agent` docs, tool tables, and tests agree on certified versus partial behavior
- the highest-value tool families have fixture-backed validation
- QA/export evidence is good enough for Scafforge to consume honestly
- Linux/headless support claims are explicit and tested rather than implied
- Scafforge’s own Blender support references are updated to match the post-hardening certified surface
- Scafforge only updates its own Blender references after receiving a concrete `blender-agent` proof package: hardened capability/status docs plus background-Blender headless validation evidence
- this plan folder contains a frozen baseline summary of the pre-hardening `blender-agent` surface for comparison

## Risks and guardrails

- Do not treat v2 preview wrappers as the default shipped contract before they are ready.
- Do not let Scafforge depend on partial tools as if they were certified.
- Do not oversell headless support before real Blender-backed validation exists.
- Keep client packaging thin; do not reintroduce duplicated server implementations.

## Documentation updates required when this plan is implemented

- `blender-agent` root docs and plan/index docs
- server capability and status docs
- install/package guidance
- `skills/project-skill-bootstrap/references/blender-mcp-workflow-reference.md`
- `skills/project-skill-bootstrap/references/blender-support-matrix.md`

## Completion criteria

- `blender-agent` has a clearer, narrower, more trustworthy public contract
- the server and skill layers are better aligned to tested behavior
- QA/export and engine handoff are more reliable
- Scafforge can reference the repo without pretending it is more complete than it is

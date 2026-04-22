# Meta-Skill-Engineering Repo Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Status:** DONE
**Implementation Outcome:** The adjacent `Meta-Skill-Engineering` repo was hardened on 2026-04-22 and merged through PR `#19`, including the expanded Studio CLI contract, evaluation-methodology docs, and validation coverage.
**Goal:** Harden the separate `Meta-Skill-Engineering` repository into a fully agent-usable skill-engineering platform with a complete CLI surface, stronger evaluation methodology, and clearer automation workflows.

**Architecture:** Treat Meta-Skill-Engineering as its own product, not as an abstract extension of Scafforge. The repo already has a partial Studio CLI/TUI/GUI and a broad skill suite. This plan turns that into a complete, automatable, headless-friendly control surface, while also adapting useful evaluation techniques from the embedded `plugin-eval` work into the wider suite.

**Tech Stack / Surfaces:** the adjacent `Meta-Skill-Engineering` repo, `scripts/meta-skill-studio.py`, `scripts/meta_skill_studio/`, root skill packages, `active-plans/improvingmseskills/plugin-eval/` inside the MSE repo, Windows WPF surfaces, repo docs.
**Depends On:** plan `12` Phase 2 must produce `active-plans/12-skill-system-expansion-and-meta-skill-engineering/references/external-source-evaluation-rubric.md` before this plan finalizes plugin-eval disposition decisions or the external-source evaluation methodology.
**Unblocks:** stronger Scafforge meta-skill integration, better skill evaluation workflows, and reliable AI-agent use of the full Meta-Skill-Engineering suite.
**Primary Sources:** `references/meta-skill-engineering-extra-plan-intake.md`, the `Meta-Skill-Engineering` repo’s `README.md` and `AGENTS.md`, `scripts/meta-skill-studio.py`, and the `plugin-eval` reference bundle under `active-plans/improvingmseskills/plugin-eval/` in the MSE repo.

---

## Problem statement

Meta-Skill-Engineering already contains:

- 17 top-level repo-owned skill packages
- a Python-based Meta Skill Studio with TUI, GUI, and CLI modes
- a Windows WPF edition
- automation scripts and library tiers
- a locally embedded `plugin-eval` bundle with richer evaluation ideas

But it does not yet appear to have one complete answer for:

- how an AI agent can drive **all** suite features from CLI alone
- how evaluation, benchmarking, observed usage, and comparison become first-class repo capabilities
- how the Studio surface, WPF surface, and scripts align to the same suite contract

## Required deliverables

- a full feature inventory for the Meta Skill Studio CLI, written to a named repo document
- a repo-wide CLI contract that covers the suite’s major workflows, not only a subset, with a concrete required verb inventory
- an evaluation-method upgrade path based on useful `plugin-eval` techniques, recorded in a named disposition document
- a clearer automation and packaging story for headless agent use
- repo docs that explain the suite as an agent-usable platform, not only a local UI app
- a surface-authority document that states which interfaces are authoritative and which are convenience shells
- a named validation story for CLI coverage and artifact presence

## Useful `plugin-eval` techniques that should be adapted

The current `plugin-eval` bundle contains methods that appear worth lifting into the wider suite:

- canonical result-schema thinking instead of ad hoc text-only evaluation output
- explicit budget modeling and estimated-vs-observed usage comparison
- a measurement-plan artifact, not only a pass/fail result
- beginner-friendly `start` / router-style command entrypoints
- fixture-driven evaluation and benchmark harnesses
- before/after comparison outputs
- improvement-brief generation tied directly to evaluation findings
- extension/metric-pack design for new evaluators

This plan should decide which of those belong repo-wide and which stay specialized to plugin/skill evaluation.

## Adjacent repo surfaces likely to change during implementation

- the adjacent `Meta-Skill-Engineering` repo's `README.md`
- the adjacent `Meta-Skill-Engineering` repo's `AGENTS.md`
- the adjacent `Meta-Skill-Engineering` repo's `scripts/meta-skill-studio.py`
- the adjacent `Meta-Skill-Engineering` repo's `scripts/meta_skill_studio/app.py`
- the adjacent `Meta-Skill-Engineering` repo's `scripts/meta_skill_studio/tui.py`
- the adjacent `Meta-Skill-Engineering` repo's `scripts/meta_skill_studio/gui.py`
- the adjacent `Meta-Skill-Engineering` repo's `scripts/meta_skill_studio/opencode_sdk_bridge.mjs`
- the adjacent `Meta-Skill-Engineering` repo's `windows-wpf/` surface
- repo automation scripts under `scripts/`
- the embedded `plugin-eval` bundle and any repo-wide evaluation surfaces derived from it

## Phase plan

### Phase 1: Inventory the actual suite and CLI surface

- [ ] Build a feature inventory covering root skill packages, Studio actions, automation scripts, library operations, and WPF-only capabilities.
- [ ] Compare that inventory to the current `--action` surface in `meta-skill-studio.py`.
- [ ] Identify every major workflow that an AI agent cannot currently drive end-to-end through CLI alone.
- [ ] Distinguish between “feature exists but has no CLI action,” “feature only exists in WPF,” and “feature is not implemented at all.”
- [ ] Publish the inventory as `docs/cli/feature-inventory.md` in the MSE repo so later phases can audit against it instead of relying on implicit knowledge.
- [ ] Identify blocking CLI bugs from `references/meta-skill-engineering-extra-plan-intake.md` during this inventory pass so Phase 2 verification does not proceed on a broken foundation.
- [ ] Resolve or explicitly gate those blocking CLI bugs before Phase 2 verification can be signed off; do not defer that prerequisite to a later generic triage phase.

### Phase 2: Define the full CLI contract

- [ ] Redesign the CLI around stable, agent-usable verbs with predictable outputs.
- [ ] Ensure the CLI can cover create, improve, test/evaluate, benchmark, catalog curation, provenance, safety review, packaging, install, and lifecycle work.
- [ ] Add a machine-readable JSON mode or stable artifact mode for every major workflow.
- [ ] Remove hidden dependence on TUI/GUI for essential functionality.
- [ ] Declare the Python Studio CLI the headless, cross-platform-compatible execution surface and prohibit Windows-only runtime dependencies from leaking into it.
- [ ] Publish a minimum required `--action` inventory at `docs/cli/action-contract.md` as the definition of "complete CLI coverage" so validation can audit the contract concretely.

### Phase 3: Adapt the right evaluation techniques from `plugin-eval`

- [ ] Decide which `plugin-eval` concepts become repo-wide standards: result schemas, measurement plans, observed-usage ingestion, compare reports, improvement briefs, or metric packs.
- [ ] Document the canonical evaluation artifact shape for Meta-Skill-Engineering workflows.
- [ ] Integrate or mirror the improvement-brief pattern so evaluation outputs can directly feed improvement work.
- [ ] Keep specialized plugin-only logic scoped where it belongs rather than blindly spreading everything.
- [ ] Record adopted-versus-rejected decisions for each candidate technique in `docs/evaluation/plugin-eval-disposition.md` inside the MSE repo, with reasons.

### Phase 4: Align Studio, WPF, scripts, and headless automation

- [ ] Ensure the Python Studio, WPF shell, and automation scripts refer to the same workflow contract and terminology.
- [ ] Decide which surfaces are convenience UIs and which are authoritative execution paths.
- [ ] Make sure headless agent usage is a first-class path, not a degraded afterthought.
- [ ] Ensure the repo can run its core workflows without requiring the WPF shell.
- [ ] Publish a surface-authority document at `docs/architecture/surface-authority.md` that explicitly states which interface is authoritative for execution and which are convenience shells layered on top.
- [ ] Reaffirm that the Python Studio CLI remains Linux/headless-compatible even while WPF stays Windows-specific.
- [ ] Treat this phase and Phase 3 as parallel-capable once Phase 2’s CLI contract is stable.
- [ ] Only touch `scripts/meta_skill_studio/opencode_sdk_bridge.mjs` if it is confirmed to be part of the authoritative CLI automation path; otherwise leave it out of scope for this hardening pass.

### Phase 5: Triage the current Studio quality issues

- [ ] Turn the issues listed in `references/meta-skill-engineering-extra-plan-intake.md` into grouped workstreams: blocking bugs, workflow UX defects, architecture problems, and lower-priority polish.
- [ ] Identify which issues are symptoms of missing suite contracts versus isolated UI defects.
- [ ] Ensure the CLI and core workflow hardening land before spending heavy effort on surface polish.
- [ ] Ensure all issues in `references/meta-skill-engineering-extra-plan-intake.md` receive an explicit triage disposition by the end of this phase, even if only a subset blocks earlier CLI verification.
- [ ] Keep WPF-specific fixes tied to the same underlying workflow truth where possible.

### Phase 6: Documentation and packaging hardening

- [ ] Rewrite root docs so the repo is understandable as a CLI- and automation-capable suite.
- [ ] Document the preferred agent/operator workflow for the repo.
- [ ] Document installation, auth/runtime prerequisites, and artifact locations.
- [ ] Ensure package or release notes accurately describe what is fully usable from CLI, TUI, GUI, and WPF.

## Validation and proof requirements

- an AI agent can drive all core suite workflows through CLI or documented automation scripts
- evaluation outputs are more structured than ad hoc prose
- useful `plugin-eval` techniques are intentionally adapted or intentionally rejected with reasons
- the repo can explain which surfaces are authoritative versus convenience UIs
- the required `--action` inventory is published and auditable as the definition of CLI completeness
- the auditable proof artifacts are `docs/cli/feature-inventory.md`, `docs/cli/action-contract.md`, `docs/evaluation/plugin-eval-disposition.md`, and `docs/architecture/surface-authority.md`

## Risks and guardrails

- Do not treat the WPF shell as the only real product path.
- Do not copy `plugin-eval` features blindly without deciding which belong repo-wide.
- Do not let the CLI become a second, contradictory workflow contract.
- Keep root skill inventory and library/workbench areas distinct, as required by the repo’s own `AGENTS.md`.

## Documentation updates required when this plan is implemented

- Meta-Skill-Engineering root docs and operator guidance
- Studio/CLI docs
- evaluation methodology references
- check `skills/project-skill-bootstrap/references/local-skill-catalog.md` and `AGENTS.md` in Scafforge if the MSE repo introduces a new intake or evaluation path that Scafforge explicitly references

## Completion criteria

- Meta-Skill-Engineering has a genuinely complete CLI/control surface for its core workflows
- repo-wide evaluation methodology is stronger and more structured
- Studio, scripts, and WPF surfaces align to the same workflow truth
- the repo is easier for an AI agent to operate headlessly and deterministically

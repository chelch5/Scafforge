# Asset Quality And Blender Excellence Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Status:** DONE
**Goal:** Raise the visual quality bar for generated repos so Scafforge stops accepting technically present but visually embarrassing assets, menus, scenes, and motion.

**Architecture:** Quality is a contract, not a vibe. This plan introduces explicit visual review criteria, screenshot/render evidence requirements, a conditional visual-proof gate for the repo types that need it, truthful Blender support limits, and distilled design guidance for generated interactive repos. Asset acquisition stays in `03`; this plan defines whether the resulting output actually looks acceptable.

**Tech Stack / Surfaces:** `skills/asset-pipeline/`, `skills/project-skill-bootstrap/`, generated template skills/plugins/docs, the adjacent `blender-agent` repository, copied Game Studio and Remotion source material.
**Depends On:** `03-asset-pipeline-architecture` for canonical asset state surfaces and manifest schema; discovery can start earlier, but schema-bearing Blender evidence rules must align to `03`.
**Unblocks:** stronger completion gating in `05-completion-validation-matrix`, better downstream UX quality in `07-autonomous-downstream-orchestration`, and truthful Blender usage throughout the system.
**Primary Sources:** spinner critique in `_source-material/asset-pipeline/assetsplanning/spinner.md`, copied Game Studio/Remotion notes under `_source-material/asset-pipeline/assetsplanning/pipeline/stolenfromcodex/`, the adjacent `blender-agent` repo, visual quality research notes in this folder.

---

## Problem statement

Scafforge currently lacks a clear contract for:

- UI composition and menu ergonomics
- visual hierarchy and readability
- intentional style direction
- Blender output quality and support limits
- screenshot/render review before a repo can claim completion
- how visual proof becomes machine-checkable without breaking non-visual repos

That is why downstream repos can be “working” while obviously looking wrong.

## Required deliverables

- a visual acceptance rubric for generated repos
- screenshot and render evidence requirements
- a conditional visual-proof gate design for the stacks and repo types that need it
- a Blender capability/support matrix based on the real `blender-agent` surface
- generated-repo guidance for menu/layout quality, especially for game and interactive repos
- distilled Scafforge-owned guidance extracted from external plugin material instead of copied bundles
- a fixture and harness contract for visually broken examples

## Package and adjacent surfaces likely to change during implementation

- `skills/asset-pipeline/SKILL.md`
- `skills/project-skill-bootstrap/references/blender-mcp-workflow-reference.md`
- `skills/project-skill-bootstrap/references/blender-support-matrix.md`
- `skills/project-skill-bootstrap/references/local-skill-catalog.md`
- `skills/repo-scaffold-factory/assets/project-template/.opencode/plugins/stage-gate-enforcer.ts`
- `skills/repo-scaffold-factory/assets/project-template/.opencode/skills/stack-standards/`
- `skills/repo-scaffold-factory/assets/project-template/docs/process/workflow.md`
- `skills/agent-prompt-engineering/references/examples.md`
- `skills/agent-prompt-engineering/references/prompt-contracts.md`
- `scripts/validate_scafforge_contract.py`
- `scripts/integration_test_scafforge.py`
- `tests/fixtures/visual-proof/`
- package docs and integration notes that refer to the adjacent `blender-agent` repo by logical identity, never by an absolute local filesystem path

## Quality dimensions this plan must own

- screen-fit and responsive layout
- menu readability and affordance clarity
- typography, spacing, and hierarchy
- 2D asset clarity and stylistic consistency
- 3D silhouette, material readability, and finish
- animation/motion “juice” where the product type requires it
- screenshot/render evidence sufficient for review

## Visual-proof gate design target

This plan should not add a universal screenshot requirement to every generated repo.

- Visual proof is required only for repo types that claim visually reviewable output: games, interactive apps, UI-heavy products, and asset-heavy repos.
- The repo should advertise that need through a machine-readable flag such as `requires_visual_proof` in bootstrap provenance or a closely related generated truth surface.
- The gate should extend existing evidence checks in `stage-gate-enforcer.ts` rather than inventing a parallel approval system.
- The first implementation should treat visual proof as a structured artifact or artifact field, not as an implicit human assumption.

## Blender contract output location

Phase 3 must write its support matrix to:

- `skills/project-skill-bootstrap/references/blender-support-matrix.md`

`blender-mcp-workflow-reference.md` should remain the procedural workflow note and link to the matrix rather than being overloaded into both roles.

## Distillation guardrail

Source material may mention paid or proprietary tooling. Package output must not inherit that by accident.

- Generated guidance must only recommend free/open-source design and art tools by default.
- Paid-tool references in source material, such as Affinity Designer in the spinner critique, must not appear in package or generated output.
- Distilled output should prefer tools such as Inkscape, Krita, GIMP, Blender, and other free/open alternatives unless a later plan explicitly scopes an exception.

## Phase plan

### Phase 1: Define the visual quality rubric

- [ ] Write a quality rubric with named failure categories instead of generic “looks bad” language.
- [ ] Split the rubric by surface: 2D UI, 2D game art, 3D props, scenes, and presentation/motion.
- [ ] Define what counts as a blocker versus a polish issue for each category.
- [ ] Ensure the rubric is strict enough to catch spinner/womanvshorse-style failures without forcing one art style.

### Phase 2: Translate the rubric into generated-repo guidance

- [ ] Update generated template guidance so repos know what “screen-fit,” “menu centered,” “visual hierarchy,” and “proof of appearance” actually mean.
- [ ] Add layout guidance for common interactive surfaces such as menus, title screens, HUDs, and modal overlays.
- [ ] Require generated repos to capture screenshots or short visual summaries at specific checkpoints where visual regression matters.
- [ ] Extend `stage-gate-enforcer.ts` through an explicit visual-proof hook that checks structured visual-evidence artifacts only when the repo is marked as requiring visual proof.
- [ ] Reuse existing evidence-validation flow where possible instead of adding a second approval path that could drift.

### Phase 3: Define a truthful Blender contract

- [ ] Audit the real `blender-agent` capability surface and document what it can currently prove, not what we wish it did.
- [ ] Split Blender usage into supported lanes such as hard-surface prop work, basic material/lookdev, export, and QA, versus unsupported or experimental lanes.
- [ ] Define what evidence a Blender-derived asset must emit before it can be considered usable in a generated repo.
- [ ] Coordinate those Blender evidence fields with plan `03` so they align to `assets/manifest.json` and related asset-truth surfaces rather than inventing a conflicting schema.
- [ ] Document where the asset pipeline should stop and fall back to sourced assets or simpler routes instead of pretending the Blender path is magical.

### Phase 4: Distill useful external design knowledge into Scafforge-owned guidance

- [ ] Review the copied Game Studio and Remotion materials and extract only the concepts that materially improve Scafforge guidance.
- [ ] Re-express those concepts in Scafforge language and file locations instead of copying external bundles wholesale.
- [ ] Decide which ideas belong in generated template skills, which belong in package references, and which remain only as source material.
- [ ] Keep all resulting tool recommendations free/open-source by default and exclude proprietary tool references from shipped output.
- [ ] Ensure the resulting guidance is narrow enough for weak models to follow and does not create redundant skill sprawl.

### Phase 5: Add visual review to validation and audit

- [ ] Define when screenshot or render evidence is mandatory by repo type.
- [ ] Ensure visual failures can show up in validation, audit, and handoff language as first-class blockers.
- [ ] Add at least one intentionally ugly fixture pack under `tests/fixtures/visual-proof/` with metadata that states the expected rubric failures.
- [ ] Extend `scripts/integration_test_scafforge.py` to exercise that fixture contract, even if the first pass validates file presence, metadata, and artifact wiring rather than image analysis.
- [ ] Confirm the system cannot mark a visually broken repo “complete” just because tests pass.

## Validation and proof requirements

- generated repos that need visual quality proof must emit screenshots or renders
- spinner-style screen-fit failures are caught by the quality rubric
- Blender-derived assets are assessed against a truthful support matrix
- copied external plugin ideas are distilled into Scafforge-owned guidance instead of being treated as shipped product behavior
- `scripts/validate_scafforge_contract.py` and `scripts/integration_test_scafforge.py` both know about the visual-proof contract where applicable

## Risks and guardrails

- Do not confuse style choice with quality. The contract should judge intent, readability, and finish, not only realism.
- Do not promise that Blender can make everything. Document supported lanes and stop there.
- Do not build a generic “art critic” with no evidence model. Every failure category needs concrete review language.
- Do not let absolute local repo paths leak into package or generated documentation.
- Keep design guidance concise enough for generated repos; do not dump giant art-theory essays into template skills.

## Documentation updates required when this plan is implemented

- asset-pipeline docs
- project-skill-bootstrap references
- generated template skills/plugins/docs related to standards and stage gates
- package docs that describe Blender support
- root documentation sweep outputs where visual proof becomes part of the contract

## Completion criteria

- Scafforge has a named visual quality rubric
- visual proof becomes part of completion for the stacks that need it
- Blender support is documented honestly and can be validated
- generated repos receive clearer design and menu-quality guidance than they do today

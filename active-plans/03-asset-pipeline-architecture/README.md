# Asset Pipeline Architecture Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Status:** TODO
**Goal:** Replace the current coarse asset-route concept with a real Scafforge asset operating framework that can classify, generate, source, validate, and prove asset truth in generated repositories.

**Architecture:** Move from four vague route labels to a capability-based asset system with explicit source routes, explicit pipeline stages, and machine-readable provenance ownership. Generated repos should receive canonical asset requirements, manifests, workflow locks, provenance/compliance records, optimization reports, and import QA surfaces. The pipeline must prefer deterministic and curated free/open paths first, local/open AI generation second, and DCC cleanup/export where necessary.

**Tech Stack / Surfaces:** `skills/asset-pipeline/`, generated repo template assets, provenance validators, license/compliance rules, import optimization tools, generated docs.
**Depends On:** `02-downstream-reliability-hardening` and `05-completion-validation-matrix` should inform proof gates, but taxonomy work can begin now.
**Unblocks:** `04-asset-quality-and-blender-excellence`, parts of `07-autonomous-downstream-orchestration`, and downstream asset-related repair improvements.
**Primary Sources:** `skills/asset-pipeline/*`, `active-plans/_source-material/asset-pipeline/assetsplanning/game-asset-generation-research.md`, `active-plans/_source-material/asset-pipeline/assetsplanning/research-about-video-game-art-assets-designs-and-a.md`, `active-plans/_source-material/asset-pipeline/assetsplanning/pipeline/asset-pipeline-agent-research-2026-04-14.md`, `active-plans/03-asset-pipeline-architecture/references/route-and-provenance-notes.md`.

---

## Problem statement

The current asset system can suggest where an asset might come from, but it does not yet provide durable answers for:

- which route should be selected and why
- how old route names map to the new taxonomy
- how source license and model/tool provenance are recorded
- which file owns machine truth when pipeline, manifest, and markdown disagree
- how generated files are optimized and imported into the engine
- how an agent knows what fallback comes next when a route fails
- how a repo proves it is using commercially acceptable and technically valid assets

That is why broken imports and low-confidence asset handling keep leaking into downstream repos.

## Required deliverables

- a capability taxonomy that explicitly maps from the current route family model to the new system
- a clear split between source routes and pipeline stages
- canonical asset state surfaces for generated repos
- a canonical ownership table that says which asset files are authoritative versus derived
- minimum schema sketches for `assets/requirements.json` and `assets/manifest.json`
- license/compliance rules with deny-by-default handling for unsupported sources
- tool/model/workflow provenance for generated assets
- import and optimization QA rules
- fallback ladders by asset category
- a migration decision for `assets/import-reports/` versus `assets/qa/`
- a concrete fixture location and harness contract for mixed-asset validation
- a research-distillation table that turns the cited asset-research files into explicit Scafforge route choices and non-default exceptions

## Canonical asset surfaces this plan should introduce

Generated repos should converge on these surfaces:

- `assets/requirements.json`
- `assets/pipeline.json`
- `assets/manifest.json`
- `assets/ATTRIBUTION.md`
- `assets/PROVENANCE.md`
- `assets/workflows/`
- `assets/previews/`
- `assets/qa/import-report.json`
- `assets/qa/license-report.json`
- `.opencode/meta/asset-provenance-lock.json`

## Canonical asset truth ownership

This plan must declare which file owns what instead of leaving multiple machine-readable files in competition:

- `assets/requirements.json`
  - authoritative for requested asset intent, category needs, quality bar, and route preferences from the project brief
- `assets/pipeline.json`
  - authoritative for category-level route selection, fallback ordering, and pipeline configuration
- `assets/manifest.json`
  - authoritative machine-readable per-asset provenance, compliance, and import-truth record
- `.opencode/meta/asset-provenance-lock.json`
  - authoritative lock for process version, manifest digest, and pipeline-contract revision
- `assets/ATTRIBUTION.md`
  - derived human-facing attribution summary built from the manifest
- `assets/PROVENANCE.md`
  - derived human ledger built from the manifest and lock
- `assets/qa/import-report.json`
  - derived machine report for the latest import/optimization verification run
- `assets/qa/license-report.json`
  - derived machine report for the latest license/compliance verification run

If these files disagree, `assets/manifest.json` owns per-asset truth and `.opencode/meta/asset-provenance-lock.json` owns process-version truth.

## Package surfaces likely to change during implementation

- `skills/asset-pipeline/SKILL.md`
- `skills/asset-pipeline/agents/`
- `skills/asset-pipeline/references/PROVENANCE-template.md`
- `skills/asset-pipeline/references/asset-description-skill.md`
- `skills/asset-pipeline/scripts/init_asset_pipeline.py`
- `skills/asset-pipeline/scripts/validate_provenance.py`
- `skills/repo-scaffold-factory/assets/project-template/`
- `skills/repo-scaffold-factory/assets/project-template/docs/process/`
- `skills/project-skill-bootstrap/references/local-skill-catalog.md`
- `references/stack-adapter-contract.md`
- `scripts/validate_scafforge_contract.py`
- `scripts/integration_test_scafforge.py`
- `tests/fixtures/` for mixed-asset validation coverage

## Proposed capability taxonomy

This plan should replace route guesswork with two explicit groups instead of one flat list.

### Source routes

- `source-open-curated`
- `source-mixed-license`
- `procedural-2d`
- `procedural-layout`
- `procedural-world`
- `local-ai-2d`
- `local-ai-audio`
- `reconstruct-3d`
- `dcc-assembly`

### Pipeline stages

- `optimize-import`
- `provenance-compliance`

The purpose is not to advertise every tool. The purpose is to make route choice, fallback, and proof explicit.

## Research distillation decisions

The cited research files should not remain passive bibliography. The first implementation pass should distill them into explicit route guidance:

- curated open fallback sources for `source-open-curated` should explicitly include families such as Kenney, Quaternius, Poly Haven, and carefully reviewed OpenGameArt-style sources where license handling differs per asset
- author-time procedural and programmable content tools should inform `procedural-2d`, `procedural-layout`, `procedural-world`, and `dcc-assembly`, including Godot-native generation patterns, Pixelorama or Aseprite-style sprite pipelines, Material Maker-style procedural materials, and Blender-driven DCC assembly
- local/open image-generation orchestration options such as ComfyUI, InvokeAI, and AUTOMATIC1111 should inform `local-ai-2d` as implementation options, not as hard-coded package brand dependencies
- hosted commercial services such as Minimax, OpenAI image or audio APIs, Meshy, Sprixen, or Scenario may remain research-backed optional lanes, but they are not package-default source routes unless a later plan explicitly approves and scopes that exception

The point is to turn research into route policy, fallback order, and proof requirements rather than into a shopping list.

## Old-to-new mapping that implementation must respect

The first implementation pass should treat the current canonical route names as inputs that need explicit migration:

- `third-party-open-licensed`
  - maps to `source-open-curated` by default
  - may map to `source-mixed-license` when the source requires per-asset attribution or commercial review
- `procedural-repo-authored`
  - maps to one of `procedural-2d`, `procedural-layout`, or `procedural-world` based on the asset class
- `godot-native-authored`
  - maps to the same procedural capability split above; the new taxonomy should not keep an engine-specific route label as canonical
- `blender-mcp-generated`
  - maps to `dcc-assembly` in the first pass
  - may also tag `reconstruct-3d` when the workflow is image/scan reconstruction rather than assembly/export

Implementation must update these code locations together:

- `_canonical_route_name()` in `skills/asset-pipeline/scripts/init_asset_pipeline.py`
- `_route_family()` in the same file
- `_bootstrap_metadata()` conditionals that currently look for legacy canonical route names

## Minimum schema sketch for new canonical JSON files

### `assets/requirements.json`

Required top-level fields:

- `version`: integer
- `project_asset_profile`: object
- `categories`: array

Required category fields:

- `id`: string
- `asset_class`: string
- `required_outputs`: array of strings
- `quality_bar`: string
- `license_policy`: string
- `preferred_source_routes`: array of strings
- `fallback_routes`: array of strings

Optional category fields:

- `engine_constraints`: object
- `style_notes`: string
- `scale_or_resolution_target`: string

### `assets/manifest.json`

Required top-level fields:

- `version`: integer
- `generated_at`: string
- `assets`: array

Required asset-entry fields:

- `id`: string
- `path`: string
- `category`: string
- `source_route`: string
- `source_type`: string
- `qa_status`: string
- `license`: string
- `author_or_origin`: string
- `workflow_ref`: string
- `import_report_ref`: string
- `license_report_ref`: string
- `attribution_required`: boolean

Optional asset-entry fields:

- `source_url`: string
- `tool_chain`: array of strings
- `model_or_checkpoint`: string
- `prompt_or_recipe`: string
- `workfile_path`: string
- `preview_path`: string

The required `source_type` vocabulary should distinguish at least: `sourced`, `procedural`, `ai-generated`, `reconstructed`, and `dcc-assembled`.

## Free/open-source default ruling

This plan is not allowed to turn commercial APIs into the default asset route.

- `local-ai-2d` means local/open-source tooling plus open-weight models by default.
- `local-ai-audio` means local/open-source tooling plus open-weight models by default.
- Commercial API generation remains denied by default in the package contract.
- Commercial services such as Minimax, Meshy, Scenario, OpenAI image generation, or similar hosted providers may remain in research/reference notes and optional exception lanes, but they are not package-default capability routes unless a later plan explicitly approves and scopes that exception.

## Phase plan

### Phase 1: Replace the current route model

- [ ] Audit the current `asset-pipeline` skill and identify where route selection is currently too coarse or keyword-driven.
- [ ] Replace the current route family wording with the capability taxonomy above or a refined version that still keeps the same operational split.
- [ ] Update the route-normalization code and bootstrap metadata using the explicit old-to-new mapping above instead of ad hoc renaming.
- [ ] Document what each capability owns, what it requires as input, and what evidence it must emit.
- [ ] Update the bootstrap logic so route choice is recorded explicitly instead of inferred later from vague text.

### Phase 2: Define the canonical asset state model

- [ ] Design the file contract for `requirements`, `pipeline`, `manifest`, `workflow`, `preview`, and QA surfaces.
- [ ] Define which fields are authoritative in machine-readable JSON versus derived in markdown summaries.
- [ ] Ensure the manifest can distinguish sourced assets, procedural assets, AI-generated assets, reconstructed assets, and Blender-assembled assets.
- [ ] Keep `assets/pipeline.json` as the category-level route/config surface and `assets/manifest.json` as the per-asset truth surface; do not collapse them into one file.
- [ ] Define `assets/workflows/` as structured workflow definitions or run records, not an empty placeholder directory.
- [ ] Define how generated repos are expected to use the state model during greenfield generation, later repair, and final handoff.
- [ ] Distill the cited research files into an explicit route-and-tool guidance table so future implementation is not forced to rediscover the same ecosystem map.

### Phase 3: Build provenance and compliance rules

- [ ] Expand provenance from “file listed in `PROVENANCE.md`” into source URL, author, license, tool, model, prompt/workflow, and version lock where applicable.
- [ ] Define an allowlist/denylist policy for asset sources and model licenses.
- [ ] Keep commercial API generation denied by default for the local-AI capabilities unless a later plan explicitly approves an exception.
- [ ] Make sure mixed-license sources such as OpenGameArt or Freesound require explicit attribution and commercial-policy handling.
- [ ] Define how generated repos build `ATTRIBUTION.md` and machine-readable license reports from the authoritative manifest.

### Phase 4: Add optimization and import QA to the contract

- [ ] Specify a standard optimization stage for 2D, 3D, and audio assets where the stack supports it.
- [ ] Define import-report expectations for Godot and any other stack Scafforge claims to support in asset-heavy contexts.
- [ ] Deprecate `assets/import-reports/` in favor of `assets/qa/import-report.json` and define the migration/update behavior for already-generated repos.
- [ ] Require preview artifacts or contact-sheet style outputs for human audit when assets are not trivially inspectable.
- [ ] Ensure import success and optimization status are recorded in the QA surfaces, not left as transient console output.

### Phase 5: Define fallback ladders by asset category

- [ ] Write category-specific fallback ladders for fonts, icons, UI kits, sprites/tiles, VFX, SFX, props, terrain, environments, and characters.
- [ ] Prefer vector or SVG-first routes for simple icons, UI symbols, and flat game art before escalating to raster generation or heavier DCC work.
- [ ] Make deterministic/procedural and curated open sources the default first choices before local AI generation.
- [ ] Define the exact moment an agent is allowed to escalate to local AI generation or Blender assembly.
- [ ] Document where the pipeline should stop and ask for human input instead of hallucinating a route.

### Phase 6: Integrate with audit, repair, and validation

- [ ] Ensure asset-state surfaces can be consumed by `scafforge-audit` and `scafforge-repair`.
- [ ] Update package validation so missing provenance, banned licenses, or missing import QA fail cleanly.
- [ ] Add validator contract checks that explicitly mention `assets/requirements.json`, `assets/manifest.json`, `assets/qa/import-report.json`, `assets/qa/license-report.json`, `.opencode/meta/asset-provenance-lock.json`, and any still-supported Blender asset agent surfaces.
- [ ] Add a mixed-asset fixture pack under `tests/fixtures/assets/` plus a harness entry in `scripts/integration_test_scafforge.py` so sourced, procedural, and generated assets can be validated together.
- [ ] Confirm the handoff and restart surfaces can summarize asset truth without making the operator read the full manifest.

## Validation and proof requirements

- a generated repo receives canonical asset state surfaces, not only `PROVENANCE.md`
- the validator rejects missing provenance, unsupported licenses, and missing QA reports
- mixed-source asset projects can be represented truthfully in one manifest
- audit and repair can consume the same asset-truth surfaces without inventing new state
- the route taxonomy is understandable to weaker models because source routes and pipeline stages are not conflated

## Risks and guardrails

- Do not turn the pipeline into a brand list. Capability and proof matter more than which product name is fashionable.
- Do not promise autonomous AAA asset generation; the pipeline must stay honest about supported routes.
- Do not overload `PROVENANCE.md` as the only truth surface.
- Do not let source routes and pipeline stages collapse into one flat vocabulary.
- Keep the pipeline navigable to weaker models: few core concepts, explicit fallbacks, and no hidden policy.

## Documentation updates required when this plan is implemented

- `skills/asset-pipeline/SKILL.md`
- asset-pipeline reference notes and templates
- project-template asset docs and process docs
- package references that describe supported asset handling
- any generated repo contributor docs that currently describe asset work too vaguely

## Completion criteria

- Scafforge can classify asset work by capability rather than guesswork
- generated repos receive canonical asset requirements, state, and QA surfaces
- provenance and compliance are machine-checkable
- fallback ladders exist for the asset categories Scafforge claims to support
- the package can explain which asset files are authoritative and which are derived

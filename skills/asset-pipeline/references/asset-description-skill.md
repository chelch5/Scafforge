---
name: asset-description
description: Guide an agent through writing a precise, actionable asset brief that maps to the repo's canonical asset requirements, route choice, workflow record, and QA contract.
---

# Asset Description Skill

Use this skill to produce a structured asset brief that is actionable by either:

- a `dcc-assembly` or `reconstruct-3d` Blender/DCC lane
- a curated sourcing lane
- an approved local/open AI generation lane

## Brief format

Create one file per asset in `assets/briefs/<asset-name>.md`:

```markdown
# Asset Brief: <Name>

## Identity
- **Name**: horse-enemy-base
- **Category**: character
- **Manifest ID**: character-horse-enemy-base
- **Requirements category**: characters
- **Selected source route**: dcc-assembly
- **Target engine**: Godot 4.x
- **Export format**: .glb

## Visual description
<2-4 sentences describing the silhouette, materials, palette, and distinguishing features.>

## Technical constraints
- **Triangle budget**: 2000-5000 tris
- **Texture size**: 512x512 max
- **Material slots**: 1-2
- **Rigging**: none / basic
- **Animation**: none / idle / walk
- **Scale reference**: 2m tall in Godot units

## Workflow contract
- **Workflow record**: `assets/workflows/<asset-name>.json`
- **Preview output**: `assets/previews/<asset-name>.png`
- **Import report ref**: `assets/qa/import-report.json`
- **License report ref**: `assets/qa/license-report.json`
- **Manifest path**: `assets/manifest.json`

## Color palette
- Primary: #8B4513
- Secondary: #2F2F2F
- Accent: #FF4444

## Route-specific execution notes
1. project_initialize — new file, metric units, explicit `output_blend`
2. mesh or scene edits — each mutating step must reuse the last `persistence.saved_blend`
3. material and UV steps — continue the same saved-blend chain
4. render_preview — generate a QA preview
5. quality_validate — prove the asset meets the brief
6. export_asset — emit the engine-ready artifact

## Acceptance criteria
- [ ] Output path and manifest ID are decided before creation starts
- [ ] Workflow record path is named up front
- [ ] Preview path is named up front
- [ ] Triangle and texture budgets are explicit
- [ ] Import proof will be recorded in `assets/qa/import-report.json`
- [ ] License or attribution requirements will be recorded in `assets/manifest.json`
- [ ] Preview artifact will be generated when the result is not trivially inspectable
```

## Procedure

### 1. Gather requirements

Read:

- `assets/requirements.json`
- `assets/pipeline.json`
- `assets/manifest.json` if a placeholder entry already exists

Extract:

- selected source route
- quality bar
- target platform constraints
- whether attribution is expected
- whether model/tool provenance must be recorded

### 2. Write the brief

Key principles:

- be specific and measurable
- keep the brief aligned to the chosen source route
- name the workflow, preview, and QA surfaces before work starts
- keep the brief compatible with the category-level fallback plan

### 3. Validate the brief

Before creation begins:

- check budgets against the requirements category
- check the selected route is still the route recorded in `assets/pipeline.json`
- check the workflow record path is machine-readable and repo-local
- check the output shape matches the import QA contract

### 4. Route to execution

- `dcc-assembly` or `reconstruct-3d`: hand the brief to `blender-asset-creator`
- `source-open-curated` or `source-mixed-license`: use the brief as license-aware sourcing criteria
- `local-ai-2d` or `local-ai-audio`: use the brief as the pinned workflow/prompt contract
- `procedural-*`: use the brief as the authored generation recipe

## Output

- `assets/briefs/<asset-name>.md`
- matching workflow record path under `assets/workflows/`
- a future manifest entry shape that is already implied by the brief

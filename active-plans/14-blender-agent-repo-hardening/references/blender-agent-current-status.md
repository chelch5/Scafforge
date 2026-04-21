# Blender-Agent Current Status Snapshot

This file freezes the starting point observed from the adjacent `blender-agent` repo while plan `14` was being written and tightened. It is not the final source of truth for that repo. It exists so plan implementation can compare the hardened surface against a known baseline rather than rediscovering the starting state later.

## Current top-level maturity picture

- the default shipped API is still the legacy v1 server
- `server_v2.py` exists, but it is a preview or transition surface rather than the certified default runtime
- live-session features depend on the Blender add-on being installed and actively running
- the repo already distinguishes certified, partial, preview, and experimental maturity states, but the plan assumes those boundaries still need hardening and proof alignment

## Legacy v1 API snapshot

### Certified

- `environment_probe`
- `project_initialize`
- `addon_configure`
- `scene_query`
- `scene_batch_edit`
- `modifier_stack_edit`
- `uv_workflow`
- `material_pbr_build`
- `render_preview`

### Partial

- `mesh_edit_batch`
- `node_graph_build`
- `bake_maps`
- `armature_animation`
- `simulation_cache`
- `asset_publish`
- `import_asset`
- `export_asset`
- `quality_validate`
- `data_access`
- `blender_live_status`
- `blender_live_operator`
- `blender_live_data`
- `blender_live_capture`

### Experimental

- `blender_python`

## V2 snapshot

### Stable helpers

- `blender_capability_discover`
- `blender_session_list`
- `blender_session_inspect`

### Preview session tools

- `blender_session_create`
- `blender_session_attach`
- `blender_session_close`
- `blender_session_pause`
- `blender_session_resume`
- `blender_session_checkpoint`

### Preview workflow wrappers

- `scene_bootstrap`
- `scene_edit`
- `modifier_workflow`
- `uv_workflow`
- `material_pbr_build`
- `bake_maps`
- `rigging_animation`
- `qa_export`
- `render`
- `import_export`

### Partial unrestricted execution

- `blender_python_run`
- `blender_addon_manage`

## Hardening priorities already called out upstream

From the adjacent repo plans, the current priority themes are:

- keep dry-run independent from local Blender discovery
- improve result envelopes so warnings and diagnostics are machine-usable
- split `safe`, `unsafe`, and `disabled` execution modes cleanly
- validate payloads more aggressively before scene mutation
- certify high-value lanes with fixtures, especially scene organization, modifiers, UV, materials, export, render preview, and QA
- evolve `quality_validate` into profile-based structured findings
- validate engine handoff through stable interchange artifacts rather than loose assumptions

## Implication for Scafforge

Scafforge should continue to treat `blender-agent` as a bounded adjacent capability with a real maturity table, not as a generic "Blender can do anything" surface. Plan `14` exists to make the post-hardening contract narrower, more machine-readable, and easier for Scafforge to consume honestly.

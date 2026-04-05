---
name: stack-standards
description: Hold the project-local standards for languages, frameworks, validation, and runtime assumptions. Use when planning or implementing work that should follow repo-specific engineering conventions.
---

# Stack Standards

Before applying these rules, call `skill_ping` with `skill_id: "stack-standards"` and `scope: "project"`.

Current stack label: `godot-android-2d`

## Godot Android Standards

This repo targets a Godot-built Android 2D platformer. Default implementation work should stay in GDScript unless canonical truth changes that decision.

### Implementation rules

- Prefer small, readable GDScript changes over abstraction-heavy patterns that make scene wiring harder to trace.
- Keep node paths, exported properties, and autoload names synchronized with the scene tree; treat missing references as correctness bugs.
- When editing `project.godot`, `export_presets.cfg`, `android/`, autoload registration, or shared resources, assume the change is high risk and validate it explicitly.
- Preserve the fairness contract: movement, hazards, glitch telegraphs, and touch controls must stay readable and recoverable.
- Hand-authored rooms and curated glitch behavior are preferred over generic procedural systems.

### Quality Gate Commands

Use the smallest Godot-native command set that proves the touched surface still loads and that release-facing Android work stays explicit.

- Project load check: `godot --headless --log-file /tmp/glitch-godot-headless.log --path . --quit`
- Import and reference refresh: `godot --headless --log-file /tmp/glitch-godot-import.log --path . --import`
- Android debug export: `godot --headless --path . --export-debug Android build/android/glitch-debug.apk`
- APK structure proof: `unzip -l build/android/glitch-debug.apk`

Pick the smallest command that matches the touched surface:

- Gameplay, scene, autoload, or project-config edits: run the project load check.
- New resources, moved scenes, or import-sensitive changes: run the import refresh as well.
- Android export or release-readiness work: run the Android debug export and APK structure proof, or return the missing prerequisite as a blocker.

### Validation rules

- Do not claim a scene, script, or export surface is valid without command output captured in the stage artifact.
- If Godot, Android SDK pieces, export templates, or signing prerequisites are missing, return a blocker instead of substituting a generic test command.
- Keep Android release proof explicit. `ANDROID-001` owns export surfaces; `RELEASE-001` owns the debug APK proof path.

### Touch and gameplay standards

- Favour clear touch targets, legible HUD layout, and telegraphed hazard timing over ornamental complexity.
- Keep baseline platforming trustworthy before layering glitch modifiers on top.
- When a change affects controls, hazard readability, or glitch behavior, call that out in implementation and review evidence explicitly.

# 03 — Scafforge Prevention Actions
**Spinner | Scafforge Audit | 2026-04-08**

---

## 1. Summary

Four package-level changes are required. The most important is **export_presets.cfg generation**
for Godot/Android repos. The second is scoping REF-003 out of node_modules. The third is
workflow-state sync discipline. The fourth is ticket scope isolation for release-lane tickets.

---

## 2. ACTION-001: Generate export_presets.cfg in Godot/Android Scaffold

**Source finding:** EXEC-GODOT-005  
**Responsible component:** Godot/Android stack adapter  
**Scafforge skill:** `repo-scaffold-factory` (template assets) + Godot adapter manifest  
**Priority:** CRITICAL

### Full Analysis: Three Solutions

#### Solution 1 (RECOMMENDED): Generate export_presets.cfg from a known template

`export_presets.cfg` is a plain text INI-format file. Its format is documented and
the required fields for a minimal Android debug export are known. An agent CAN generate
a minimum viable `export_presets.cfg` without the Godot editor.

**Minimum viable contents for Godot 4.x Android debug:**

```ini
[preset.0]

name="Android"
platform="Android"
runnable=true
dedicated_server=false
custom_features=""
export_filter="all_resources"
include_filter=""
exclude_filter=""
export_path=""
encryption_include_filters=""
encryption_exclude_filters=""
script_export_mode=1

[preset.0.options]

custom_build/use_custom_build=false
custom_build/export_format=0
architectures/armeabi-v7a=true
architectures/arm64-v8a=true
architectures/x86=false
architectures/x86_64=false
keystore/debug=""
keystore/debug_user="androiddebugkey"
keystore/debug_password="android"
keystore/release=""
keystore/release_user=""
keystore/release_password=""
version/code=1
version/name="1.0"
package/name="__PACKAGE_NAME__"
package/signed=true
launcher_icons/main_192x192=""
launcher_icons/adaptive_foreground_432x432=""
launcher_icons/adaptive_background_432x432=""
graphics/opengl_debug=false
one_click_deploy/clear_previous_install=false
```

**What the editor adds that AI cannot:** The editor adds the full `gradlebuilds/` path
resolution and Android SDK/NDK path discovery from host settings. However, for a **debug**
build using the default debug keystore, the template above is sufficient for Godot 4.2
to proceed past the "export_presets.cfg absent" error.

**Caveat:** After generating this file, a secondary error may appear about missing
Godot export templates (`.export_templates/`). That is a separate host-side install step.

**Implementation:** The Godot/Android adapter in Scafforge should emit `export_presets.cfg`
as a scaffold template output with `__PACKAGE_NAME__` substituted from the project brief
(e.g., `com.example.spinner` derived from the project slug).

#### Solution 2: Scafforge generates during greenfield scaffold

The `repo-scaffold-factory` template for the `Godot 4.x Android 2D` stack label should
include `export_presets.cfg` as a template asset. This is the cleanest long-term solution:

- Location: `skills/repo-scaffold-factory/assets/project-template/export_presets.cfg.tmpl`
- Substitution variables: `__PROJECT_NAME__`, `__PACKAGE_NAME__`, `__VERSION_CODE__`
- Integration: The Godot/Android adapter applies this template when `stack_label` contains
  `Android`
- `scafforge-repair` should also detect missing `export_presets.cfg` and offer to restore it

This is compatible with Solution 1 — Solution 1 defines the content, Solution 2 defines
where in the Scafforge pipeline it should be emitted.

#### Solution 3 (NOT RECOMMENDED for MVP): Human uses Godot editor

In the Godot editor: Project → Export → Add preset → Android → Save. The editor GUI:
1. Discovers the locally installed Android SDK
2. Populates `ANDROID_SDK_ROOT` into the preset
3. Validates the debug keystore path and credentials
4. Writes the fully completed `export_presets.cfg`

**Why this should not be the only solution:** It requires the Godot editor on the
development machine, requires manual GUI interaction, and is not repeatable by an agent.
For developer environments without the editor (CI, clean machines, agent-only workflows),
this path is unavailable. The INI format is documented and AI-generatable.

### Recommended Approach

**Solution 1 + Solution 2 combined:**
1. Define the minimum viable `export_presets.cfg` template in the Godot/Android adapter
2. Emit it during `repo-scaffold-factory` greenfield pass when `Godot 4.x Android 2D`
3. `scafforge-repair` detects absence and offers remediation
4. Document that `export_presets.cfg` is generated but host-side export templates must
   still be installed via the Godot editor or CI tooling

**Responsible Scafforge component:**  
`skills/repo-scaffold-factory/assets/project-template/export_presets.cfg` (new template file)  
`adapters/manifest.json` Godot/Android section (add export_presets.cfg to required scaffold outputs)  
`skills/scafforge-audit/scripts/audit_execution_surfaces.py` (EXEC-GODOT-005 checker:
  treat missing `export_presets.cfg` as BLOCKER before Android lane work begins)

---

## 3. ACTION-002: Exclude node_modules from REF-003 Import Scanner

**Source finding:** REF-003  
**Responsible component:** `skills/scafforge-audit/scripts/audit_execution_surfaces.py`  
or the import resolution checker  
**Priority:** Medium

The REF-003 checker should add:
```python
IMPORT_SCAN_EXCLUSIONS = [
    "**/node_modules/**",
    "**/.git/**",
    "**/vendor/**",
]
```

Node modules are third-party compiled dependencies, not project source files. TypeScript
packages routinely have source `.ts` files importing compiled `.js` paths that do not
exist in the source tree (they are generated at build time). The checker should not flag
these as missing local modules.

---

## 4. ACTION-003: Workflow-State Sync on Artifact Write

**Source finding:** SESSION006  
**Responsible component:** `artifact_write` tool in `repo-scaffold-factory` OpenCode plugin  
**Priority:** High

The SESSION006 trap occurred because `artifact_write` recorded artifacts AND updated the
manifest ticket stage, but did NOT update `workflow-state.json`'s top-level `stage` field
in the same write. A subsequent session read the stale stage and got a contradictory picture.

**Fix:** When `artifact_write` transitions a ticket stage (e.g., implementation → review),
it must update `workflow-state.json.stage` in the same atomic write operation that
updates the manifest. The two sources of truth must not be allowed to diverge.

Additionally, `ticket_lookup.transition_guidance` should detect the stale-state case
(workflow-state stage disagrees with manifest artifact set) and return a diagnostic message
rather than a literal "cannot advance" blocker.

---

## 5. ACTION-004: Ticket Scope Isolation for Release-Lane Tickets

**Source finding:** WFLOW023  
**Responsible component:** `ticket-pack-builder` (backlog generation), skill: `ticket-pack-builder`  
**Priority:** Medium

RELEASE-001's acceptance criteria required APK creation, which depended on
`export_presets.cfg` being present — a prerequisite that no ticket owned.

**Fix:** When `ticket-pack-builder` generates a release-readiness ticket for a Godot
Android target, it should:
1. Check whether `export_presets.cfg` is present or a prior ticket has committed to creating it
2. If no, generate a prerequisite ticket (e.g., `ANDROID-EXPORT-SETUP`) that creates
   the file before the APK-build ticket can begin
3. Set `depends_on: [ANDROID-EXPORT-SETUP]` on the APK build ticket
4. Never generate acceptance criteria that require deliverables from untracked prerequisite work

---

## 6. Validation for Each Action

| Action | Validation Method |
|---|---|
| ACTION-001 (export_presets.cfg) | Run Scafforge greenfield scaffold for a Godot Android test repo; verify export_presets.cfg is emitted; verify `godot4 --export-debug` proceeds past the "absent" error |
| ACTION-002 (REF-003 exclusion) | Rerun audit on Spinner; verify REF-003 no longer fires for node_modules/ paths |
| ACTION-003 (workflow-state sync) | Integration test: write implementation artifact, verify workflow-state.json stage updates atomically; resume session and verify ticket_lookup returns correct current stage |
| ACTION-004 (ticket scope isolation) | Generate Godot Android backlog without prior export config; verify ANDROID-EXPORT-SETUP ticket is emitted before the APK build ticket |

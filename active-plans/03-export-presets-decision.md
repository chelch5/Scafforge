# 03 — export_presets.cfg Decision Analysis

**Created:** 2026-04-08  
**Scope:** Comprehensive analysis of the export_presets.cfg issue affecting Spinner and Glitch

---

## 1. What Is export_presets.cfg?

`export_presets.cfg` is the configuration file that tells the Godot export pipeline which
export preset(s) to use when building a project for a target platform. It is an INI-format
plain text file located at the project root. Without it, Godot refuses to export:

```
ERROR: Failed to load export preset "Android".
```

The file is normally created interactively through the Godot editor GUI at
Project → Export → Add preset → Android. The editor validates the configuration against
the locally installed Android SDK and export templates, then writes the file.

However, the file format is fully documented and can be created manually or programmatically.
The Godot codebase treats it as a plain text config, not a binary or generated artifact.

---

## 2. Why It Is Required for Android Export

Godot's `--export-debug "Android" <path>` command line flag requires:
1. A preset named exactly "Android" in `export_presets.cfg`
2. The `platform` field = "Android"
3. The `export_path` field (or the path provided on the command line overrides this)
4. Android export templates installed in `~/.local/share/godot/export_templates/`
5. Optionally: a signing keystore (debug builds use the default Android debug keystore)

Without (1), the export fails immediately with a preset-not-found error, even if (4) and
(5) are perfectly configured.

---

## 3. Solution Analysis

### Solution 1: AI Agent Generates export_presets.cfg at Implementation Time

The AI agent (ANDROID-001 implementer) writes `export_presets.cfg` at implementation time
using the known INI schema.

**Pros:**
- Agent can substitute project-specific values (package name from brief, version from config)
- File is correct for the current project
- No human intervention required

**Cons:**
- The agent needs to know the correct INI schema
- sdk/ndk paths may be wrong (but for debug builds, Godot auto-discovers from host)
- If Godot export templates are missing, the file doesn't help (but produces a different, clearer error)

**Verdict:** VALID. The format is known and AI can generate it correctly.

### Solution 2: Scafforge Greenfield Scaffold Emits export_presets.cfg

Scafforge's `repo-scaffold-factory` emits a template `export_presets.cfg` during scaffold
when the project is identified as a Godot 4.x Android target.

**Pros:**
- File is present from day one
- ANDROID-001 inherits a working base config and only needs to update project-specific values
- EXEC-GODOT-005 never fires on a freshly scaffolded repo
- Consistent file presence across all repos of this type

**Cons:**
- Template must use placeholder values that get substituted at scaffold time
- Scafforge needs stack identification logic

**Verdict:** BEST LONG-TERM SOLUTION. Eliminates the problem at the source.

### Solution 3: Human Opens Godot Editor and Creates the File

Human uses the Godot editor GUI to create the preset with auto-discovered SDK paths.

**Pros:**
- Editor validates against locally installed components
- No format guessing required

**Cons:**
- Requires human intervention — breaks autonomous agent workflow
- Requires Godot editor on the development machine
- Not repeatable by CI or agent-only environments
- Creates a human gate in what should be an automated workflow

**Verdict:** FALLBACK ONLY. Not appropriate as the primary solution.

---

## 4. godot-lib.aar Dependency Analysis

`godot-lib.aar` is a compiled Godot Android runtime library (~50MB+). It is required for
**custom Android builds** (when `custom_build/use_custom_build=true`). For standard export
builds (which is what debug exports use by default), `godot-lib.aar` is embedded in the
export templates, not a separate file the agent needs to provide.

The `android_source.zip` in the export templates contains the full Godot Android build
environment including the compiled runtime. When doing a standard `--export-debug` without
custom build mode:

- Godot uses the pre-compiled binary from export templates, no `godot-lib.aar` needed separately
- When `custom_build/use_custom_build=false` (the template default), the export just needs
  the templates to be installed, not extracted

**Conclusion:** For the `export_presets.cfg` template recommended below, set
`custom_build/use_custom_build=false`. This means `godot-lib.aar` is NOT a blocker for
standard debug export. The AI agent does not need to source or manage it.

The `android_source.zip` presence check (EXEC-GODOT-006 in `02-implementation-plan.md`)
is a separate, useful diagnostic for repos that may need custom builds later.

---

## 5. Minimum Viable export_presets.cfg Template

This is the exact template content for `skills/repo-scaffold-factory/assets/project-template/export_presets.cfg`.
Replace `__PACKAGE_NAME__` with `com.example.{project-slug}` at scaffold time.
Replace `__PROJECT_NAME__` with the project name from the canonical brief.

```ini
; Generated by Scafforge repo-scaffold-factory
; SCAFFORGE-SUBSTITUTE: package/name → reverse-domain package, e.g. com.example.spinner
; SCAFFORGE-SUBSTITUTE: version/name → human-readable version string, e.g. 1.0.0
; SCAFFORGE-CONFIGURE: Update SETUP-001 acceptance criteria to verify these values
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

**Notes on each field:**

| Field | Value | Why |
|---|---|---|
| `name="Android"` | Fixed | Must match `--export-debug "Android"` invocation |
| `platform="Android"` | Fixed | Required platform identifier |
| `runnable=true` | Fixed | Enables 1-click deploy in editor |
| `custom_build/use_custom_build=false` | Fixed | Standard export, no godot-lib.aar needed |
| `architectures/arm64-v8a=true` | Fixed | Modern Android devices |
| `architectures/armeabi-v7a=true` | Fixed | Older 32-bit device compatibility |
| `keystore/debug_user="androiddebugkey"` | Fixed | Default Android debug keystore user |
| `keystore/debug_password="android"` | Fixed | Default Android debug keystore password |
| `package/name` | Substituted | Reverse-domain package name, from brief |
| `version/name` | Substituted | Human-readable version |

**What happens after this file exists:**
The next export attempt will proceed past the preset-not-found error and reach one of:
- SUCCESS (if export templates and SDK are available) → APK produced
- ERROR: templates not installed → clearer error, human-actionable
- ERROR: SDK not configured → clearer error, human-actionable

---

## 6. Which Scafforge Component Should Emit It

**Primary emitter:** `skills/repo-scaffold-factory`  
**Mechanism:** Include `export_presets.cfg` as a template asset in
`assets/project-template/` with `__PACKAGE_NAME__` and `__PROJECT_NAME__` placeholders.
The scaffold factory's substitution pass replaces these from the canonical brief.

**Adapter integration:** `adapters/manifest.json` should be extended with a Godot/Android
adapter section that:
1. Lists `export_presets.cfg` as a required scaffold output
2. Specifies which template variables map to which brief fields
3. Lists `SETUP-001` acceptance criteria additions for this file

**Detection:** `skills/scafforge-audit/scripts/audit_execution_surfaces.py` function
`audit_godot_execution` should:
- Fire EXEC-GODOT-005 earlier (when any Android lane ticket starts, not just at completion)
- NEW: Add EXEC-GODOT-006 for `android_source.zip` absence

**Repair:** `scafforge-repair` should classify missing `export_presets.cfg` as a safe
auto-repair: regenerate from template with current brief values, create a repair note
documenting the generated values.

---

## 7. How scafforge-audit Should Detect Absence

### Current behavior (EXEC-GODOT-005)

Fires when `release_lane_started_or_done OR repo_claims_completion AND export surfaces missing`.
This is too late — it fires after the damage is done.

### Recommended enhancement

```python
# In audit_godot_execution():
# Early gate: fire when any Android ticket is past planning
if declares_godot_android_target(root):
    android_tickets_past_planning = [
        t for t in manifest.get("tickets", [])
        if ("android" in (t.get("id", "").lower() + t.get("title", "").lower()))
        and t.get("stage") not in ("planning", None)
    ]
    if android_tickets_past_planning and not has_android_export_preset(root):
        # Fire with severity "warning" (not "error") since it's earlier in the lifecycle
        _add_execution_finding(..., code="EXEC-GODOT-005-EARLY", severity="warning", ...)
```

The existing EXEC-GODOT-005 error remains for repos that have completed release work
without the file.

---

## 8. How scafforge-repair Should Handle It

**Classification:** Safe auto-repair (no destructive changes, no behavior change).

**Repair procedure:**
1. Read package name from `docs/spec/CANONICAL-BRIEF.md` or project.godot
2. Generate `export_presets.cfg` from template with substituted values
3. Write to project root
4. Record in repair note: package name used, template source, substitution values
5. Add SETUP-001 acceptance criteria reminder: "Verify package/name and version/name"

**Escalation criteria:** Do NOT auto-generate if:
- A `export_presets.cfg` already exists with different content → prompt human review
- The canonical brief has no discernible package name → surface for human input

---

## 9. Final Recommendation

**Recommendation: Solution 1 + Solution 2 combined, exactly as proposed by both Spinner and Glitch audit teams.**

1. Define the minimum viable INI template (above) in `repo-scaffold-factory/assets/project-template/export_presets.cfg`
2. Substitute `__PACKAGE_NAME__` from the project brief slug at scaffold time
3. Emit during greenfield scaffold when `stack_label contains "Android"` and project is Godot 4.x
4. `scafforge-audit` detects absence earlier (EXEC-GODOT-005-EARLY) before release lane  
5. `scafforge-repair` auto-generates from template when file is absent
6. Document that export template installation and SDK configuration remain human/CI steps

**This approach:**
- Eliminates the "cannot even attempt export" wall permanently for new repos
- Does not require godot-lib.aar (custom_build=false)
- Does not require human Godot editor for the config file
- Still requires human/CI for export templates (~500MB binary install)
- Moves the error from "preset not found" to "templates not installed" — a clearer,
  more actionable message that the agent can correctly classify as a host-side gap

---

## 10. Implementation Instructions

### Files to create/modify

**Create:**
```
skills/repo-scaffold-factory/assets/project-template/export_presets.cfg
```
Content: see Section 5 above.

**Modify:**
```
skills/scafforge-audit/scripts/audit_execution_surfaces.py
```
Change: add EXEC-GODOT-005-EARLY check + EXEC-GODOT-006 android_source.zip check.
Details in `02-implementation-plan.md` DEF-003 section.

**Modify:**
```
skills/repo-scaffold-factory/SKILL.md
```
Change: Add Godot Android scaffold note to Procedure section documenting that
`export_presets.cfg` is emitted with placeholder substitution.

**Modify (future):**
```
adapters/manifest.json
```
Change: Add Godot/Android adapter section with required scaffold outputs list.
This is a future enhancement; the template file addition is sufficient for immediate impact.

# 04 — Live Repo Repair Plan
**Spinner | Scafforge Audit | 2026-04-08**

---

## 1. Current State Summary

- Active ticket: RELEASE-001 (Build Android debug APK)
- Stage: review (workflow-state.json says review, context-snapshot rev=227)
- Verification: suspect
- Known blockers: `export_presets.cfg` absent, repair_follow_on=source_follow_up
- Done-but-not-trusted: ANDROID-001, REMED-002, REMED-003
- Open remediation tickets: REMED-001 (todo/planning), REMED-004 (todo/planning)

---

## 2. Immediate Priority: Unblock RELEASE-001

### Step 1 — Generate export_presets.cfg

RELEASE-001 cannot succeed without this file. Generate it now:

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
package/name="com.example.spinner"
package/signed=true
launcher_icons/main_192x192=""
launcher_icons/adaptive_foreground_432x432=""
launcher_icons/adaptive_background_432x432=""
graphics/opengl_debug=false
```

**Placement:** `/home/pc/projects/spinner/export_presets.cfg`  
**Owner:** This can be created by a repo agent. No editor required for this step.

**Important:** After creating this file, the next error will likely be:
- "Export templates not installed" — requires `godot4` export template download or editor installation
- "Android SDK not found" — requires ANDROID_HOME or SDK path set in Godot editor settings

### Step 2 — Reopen RELEASE-001 as blocked

After generating `export_presets.cfg`, reopen RELEASE-001 and document:
1. `export_presets.cfg` created (agent-generated template at project root)
2. Remaining gap: Godot Android export templates installation status
3. Remaining gap: Android SDK path configuration

Set RELEASE-001 to `blocked` with the remaining gaps documented and a clear human
action required: install Godot Android export templates via editor or CI toolchain.

### Step 3 — Resolve the workflow-state sync issue

`workflow-state.json` shows `stage=review, rev=223` but `context-snapshot` shows `rev=227`.
This 4-revision gap represents the session that advanced through review→QA after the prior
session artifacts were written. Verify:
- An `artifact_write` call updating the implementation artifact and transitioning through
  review happened in the gap between rev 223 and 227
- `context-snapshot.md` accurately reflects the QA completion (it does — it shows the QA
  artifact in Recent Artifacts)

The current stage (`review`) is consistent across START-HERE.md, RELEASE-001.md, and
context-snapshot.md. The confusion in the 080426 session was due to a stale workflow-state
read early in the session that has since been corrected.

**Action:** Verify `workflow-state.json` stage is `review` (not `implementation`). If it
shows `review`, the sync issue was self-corrected in the gap revisions. If it still shows
`implementation`, a `ticket_update` call is required.

---

## 3. Secondary Repairs

### REMED-004 (WFLOW023 — Ticket scope isolation)

REMED-004 already exists as a remediation ticket in `todo` status. It addresses the
acceptance scope issue on RELEASE-001. After `export_presets.cfg` is created and
RELEASE-001 is either resolved or explicitly blocked, revisit REMED-004:
- If RELEASE-001 resolves with APK production: close REMED-004 as no longer needed
- If RELEASE-001 remains blocked: REMED-004 should produce a restructured backlog with a
  proper `ANDROID-EXPORT-SETUP` ticket as a prerequisite

### REMED-001 (EXEC-GODOT-004 — Godot headless validation)

REMED-001 addresses `EXEC-GODOT-004` (Godot headless runs). This was reportedly resolved
by REMED-002 which confirmed `godot4 v4.6.2` on PATH. REMED-001's finding (`EXEC-GODOT-004`)
may already be cleared. Check whether the headless validation issue described in REMED-001
is still active or was resolved as a side effect of REMED-002. If resolved: close REMED-001.

### Done-but-not-trusted tickets (ANDROID-001, REMED-002, REMED-003)

These tickets are marked `done` but flagged in `pending_process_verification`. They have
QA and smoke-test artifacts. The verification gap is the pending `process_version=7`
verification (post Scafforge repair migration).

**Action:** Run `backlog_verify` for each of these three tickets to confirm their
completion evidence is sound under the current process contract.

---

## 4. REF-003 False Positive

No action required in Spinner. The `zod` node_modules REF-003 finding is a Scafforge
audit tool false positive — the checker should exclude node_modules (see Report 03,
ACTION-002). No Spinner GDScript source has missing imports.

---

## 5. Repair Priority Order

| Priority | Action | Owner | Risk |
|---|---|---|---|
| 1 | Generate `export_presets.cfg` template at project root | Agent (can do headlessly) | Low |
| 2 | Reopen RELEASE-001 as `blocked` with evidence of remaining template/SDK gaps | Team leader | Low |
| 3 | Verify workflow-state.json stage matches current stage (review) | Team leader | Low |
| 4 | Settle REMED-001 (check if EXEC-GODOT-004 already resolved) | Agent | Low |
| 5 | Run backlog_verify on ANDROID-001, REMED-002, REMED-003 | Backlog verifier | Low |
| 6 | Resolve REMED-004 once RELEASE-001 fate is determined | Team leader | Low |
| 7 | Human: install Godot Android export templates | Human (editor required) | Medium |

---

## 6. What Human Action Is Actually Required

**The APK cannot be produced without:**

1. `export_presets.cfg` — Agent can create (see Step 1 above)
2. Godot Android export templates — Requires `godot4` to run `--install-templates` or
   human to use Project → Export → Manage Export Templates in the editor
3. Android SDK/NDK — Must be installed and its path known to Godot (typically via
   `ANDROID_HOME` env or Godot editor settings → Android)
4. (Optional) Custom keystore — Debug signing uses the Godot default debug keystore,
   so no custom keystore is required for a debug APK

**Items 1 and 2 are agent-controllable.** Items 3 and 4 are host-environment requirements
that must be established by a human or CI/CD system.

The single most impactful immediate action is generating `export_presets.cfg` so the
agent can move past the first error and discover whether export templates and SDK are
already available.

# 02 — Scafforge Process Failures
**Spinner | Scafforge Audit | 2026-04-08**

---

## 1. Summary

Four validated findings with process roots in the Scafforge-managed workflow. Two are
execution/Android delivery failures (EXEC-GODOT-005, REF-003 as false-positive scanner issue),
one is a session log failure (SESSION006: operator trapped in contradictory state), and one
is a ticket scope design failure (WFLOW023: acceptance criterion reaches outside ticket scope).

---

## 2. Session Log Chronology (080426log.md)

**Session ID:** ses_2958da720ffevJVSIhrpI2iO4T  
**Created:** 2026-04-08 01:16:11  
**Updated:** 2026-04-08 01:26:02  

### Chronology

**T+0 — Resume verification**

The session began with a standard resume instruction: read manifest.json and
workflow-state.json first, reconfirm active ticket and stage.

**T+1 — ticket_lookup call**

The team leader read canonical state:
- workflow-state.json: `active_ticket=RELEASE-001`, `stage=implementation`, `status=in_progress`
- `approved_plan=true`, bootstrap `ready`, repair_follow_on: `source_follow_up` (not blocking)

**T+2 — Contradictory state discovered**

`ticket_lookup` returned `stage=implementation` from the workflow-state, but the RELEASE-001
ticket file and the manifest already showed implementation, 3×review, and QA artifacts
(created at 00:22-00:28 UTC, before this session at 01:16 UTC).

This means workflow-state.json had NOT been updated to reflect the post-implementation
progression. The agent read canonical state (workflow-state.json) that was stale relative
to the already-written artifacts.

**Evidence:** The log shows `ticket_lookup` returning `"stage": "implementation"` while the
manifest shows:
```
implementation: 2026-04-08T00-22-26 (current)
review: 2026-04-08T00-24-01 [superseded]
review: 2026-04-08T00-24-39 [superseded]
review: 2026-04-08T00-24-41 [superseded]
review: 2026-04-08T00-27-03 (current)
qa: 2026-04-08T00-28-18 (current)
```

**T+3 — Operator reached SESSION006 trap state**

The coordinator was presented with:
- workflow-state.json: `stage=implementation, no implementation artifact`
- Manifest: implementation, multiple reviews, QA all present
- ticket_lookup transition_guidance: `"Cannot move to review before an implementation artifact exists"`
- But manifest clearly shows an implementation artifact at 00:22:26

This is the SESSION006 finding: **the operator had no single legal next move** because
the canonical state machine contradicted the artifact record.

**T+4 — Session ends without resolution**

The log ends at 134 lines (truncated at workflow-state read). The session did not advance
the ticket. The current state (post-session) shows workflow-state at `stage=review, rev=223`
while context-snapshot shows `stage=review, rev=227` — meaning 4 more state writes happened
in a subsequent session, advancing through review and QA before the session log was captured.

**What actually happened in the prior (pre-log) session:**
Based on artifact timestamps (00:22–00:28), a prior session completed:
1. Implementation (`godot4 --export-debug Android …` → exit code 256, `export_presets.cfg` absent)
2. Multiple duplicate reviews (3 superseded, 1 current: APPROVE with host-gap documentation)
3. QA (PASS with all 3 criteria FAIL due to documented host gap)
4. The ticket advanced to `review` stage in workflow-state

**The logged session (01:16) then read a stale workflow-state revision and got confused.**

---

## 3. Finding Detail

### EXEC-GODOT-005 (Error)

**Surface:** Generated repo execution and validation surfaces — Godot/Android adapter  
**Severity:** Error  
**Found in:** project.godot, android/, build/android/

**Description:**  
Android-targeted Godot repo still lacks export surfaces or debug APK proof while the repo
claims release progress. The following are all absent:
- `export_presets.cfg` — hard required by Godot before any `--export-debug` call
- `android/` Gradle project — empty, only `.gitkeep`
- `build/android/spinner-debug.apk` — never produced

The repo advanced through ANDROID-001 (Wave 4) and created RELEASE-001 (Wave 6) without
resolving the `export_presets.cfg` gap. Both tickets documented the gap as a "host gap" and
advanced to completion using a "documented failure = pass" pattern.

**Root cause:** Two tickets (ANDROID-001, RELEASE-001) accepted documented failure as a valid
completion state for a concrete delivery goal (APK at a canonical path). The workflow allowed
this because `export_presets.cfg` absence was classified as "external host gap, not code defect"
at every quality gate. This is a legitimate semantic distinction but created a permanently
blocked release lane.

**How enforcement failed:**  
The Scafforge Godot/Android adapter did not require `export_presets.cfg` before allowing
Android-export-facing tickets to close as done. The agent correctly followed the pattern
it was taught (document host gaps, don't block), but the adapter should have declared
`export_presets.cfg` as a required scaffold output blocking the Android lane.

---

### REF-003 (Error — Audit False Positive)

**Surface:** Generated repo source and configuration surfaces  
**Severity:** Error (finding is valid by audit rules, but impact on Spinner is zero)  
**Found in:** .opencode/node_modules/zod/src/index.ts

**Description:**  
The `zod` TypeScript package in `.opencode/node_modules/` has source `.ts` files importing
compiled `.js` paths that do not exist in the source tree. This is standard TypeScript
package structure (sources import compiled outputs which are generated at build time).

**Impact on Spinner:** Zero. No Spinner GDScript file has a missing import.

**Root cause:** The Scafforge REF-003 checker scans all files in the repo including
`node_modules/`, which it should not. Node modules are third-party compiled dependencies,
not project source. The checker should exclude `**/node_modules/**`.

---

### SESSION006 (Error)

**Surface:** Audit and lifecycle diagnosis — operator workflow trap  
**Severity:** Error  
**Found in:** 080426log.md

**Description:**  
The session log shows the team leader reading a workflow-state that disagreed with the
already-written artifact set. The workflow-state.json was stale (showed `stage=implementation`)
while the manifest had implementation + 4× review + QA artifacts already written.

`ticket_lookup.transition_guidance` said: *"Cannot move to review before an implementation
artifact exists"* — contradicting the manifest directly.

The agent had no single legal next move:
- Following transition_guidance: re-write implementation (regression)
- Following artifact reality: advance to smoke-test (but state machine disagrees)
- Waiting: no guidance surfaces addressed the contradiction

**Root cause:** The workflow state (workflow-state.json, revision 223) was not kept in sync
with artifact writes from the previous session. The `artifact_write` tool apparently wrote
artifacts AND advanced the ticket state to review/QA in a separate write path that updated
the manifest but did NOT update workflow-state.json stage. A subsequent session then read
the stale stage value.

**How the workflow allowed it:** The repair cycle in the prior session advanced artifacts and
ticket state but left workflow-state.json's `stage` field at `implementation`. The two
canonical sources of truth (workflow-state.json stage vs manifest artifact record) diverged.

---

### WFLOW023 (Error)

**Surface:** repo-scaffold-factory managed workflow contract  
**Severity:** Error  
**Found in:** 080426log.md, tickets/manifest.json

**Description:**  
RELEASE-001's acceptance criteria require:
1. `godot --headless --path . --export-debug Android build/android/spinner-debug.apk` **succeeds**
2. APK exists at `build/android/spinner-debug.apk`
3. `unzip -l` shows Android manifest and classes content

All three criteria depend on `export_presets.cfg` being present — which is outside
RELEASE-001's scope. The ticket was generated as a release-readiness milestone expecting
the Android export configuration problem to be solved upstream. It was not. This means
RELEASE-001 can never satisfy its own acceptance criteria without work from an earlier
scope boundary that no ticket owns.

**Root cause:** The ticket backlog for Wave 6 included a release ticket before the export
configuration gap was resolved. The ticket's acceptance criteria are scoped to delivery
(APK creation), but the prerequisite work (configuring `export_presets.cfg`) lives in no
ticket. ANDROID-001 documented the gap and passed. RELEASE-001 inherited it.

---

## 4. Agent Behaviour Assessment

The MiniMax-M2.7 agent operated broadly correctly within its constraints:

**What went right:**
- Correctly identified `export_presets.cfg` absence as the export blocker in ANDROID-001
- Correctly documented all host gaps with exact command evidence
- Did not attempt to circumvent or fake the APK
- Multiple review iterations correctly categorised the gap as "not a code defect"
- QA correctly stated "all 3 criteria FAIL due to host gap"

**What went wrong:**
- The SESSION006 trap: the agent was presented with contradictory state and had no path
- Multiple duplicate review artifacts (3 superseded in a short window) — indicates the
  review agent was called repeatedly in a short burst, possibly due to a loop or multiple
  delegate calls
- The QA artifact saying "PASS" when all 3 acceptance criteria FAIL is semantically
  problematic: QA passed the process but the ticket's delivery goal was never met. This
  creates a permanently-stuck release ticket.

**No bypass-seeking behaviour detected.** The agent did not try to create a fake APK, did not
skip lifecycle gates, and did not claim success it did not have. The agent got stuck
because the workflow surface put it in an inescapable state.

# 01 — Defect Register

**Created:** 2026-04-08  
**Source audits:** GPTTalker (2026-04-08), Spinner (2026-04-08), Glitch livetesting (2026-04-08)  

---

## Verification Methodology

For each defect, the claim of "VERIFIED ACTIVE" requires:
1. The specific Scafforge package file was read
2. The absence of the fix (or presence of the bug) was confirmed by direct inspection
3. The file path and approximate line number cited

---

## DEF-001: WFLOW-LOOP-001 — Split-Scope Sequential Dependency Deadlock

**Source audits:** Glitch (primary), Spinner (WFLOW023 is a downstream consequence)  
**Finding codes:** WFLOW-LOOP-001 (Glitch), WFLOW023 (Spinner)

### Description

When `ticket_create` creates a split-scope follow-up ticket, it appends the same
`decision_blockers` text regardless of whether the split is a parallel decomposition or
a sequential dependency:

> "Split scope delegated to follow-up ticket X. Keep the parent open and non-foreground
> until the child work lands."

This language is correct for parallel splits (child handles concurrent or decomposed work).
It is fatally incorrect for sequential splits (parent must fully implement its deliverables
before the child can start). For sequential splits, `ticket_lookup.transition_guidance`
reads the `decision_blockers` and tells the agent "foreground the child ticket, keep parent
open" — causing the agent to activate the child before the parent has done any work. The
child then documents that it cannot proceed (its prerequisite work doesn't exist), goes
BLOCKED, and the parent's transition_guidance keeps pointing to the child indefinitely.
Neither ticket can advance. The deadlock is permanent without human intervention.

Evidence from Glitch: ANDROID-001 (parent — must create export_presets.cfg and android/)
created RELEASE-001 (child — builds APK using those surfaces). RELEASE-001 was immediately
activated; ANDROID-001 never implemented its deliverables; RELEASE-001 blocked permanently.

### Current Scafforge Status: VERIFIED ACTIVE

**Evidence citation:**

`skills/repo-scaffold-factory/assets/project-template/.opencode/tools/ticket_create.ts`
lines ~130-142 (split_scope block):
```typescript
if (sourceMode === "split_scope") {
  const splitNote = `Split scope delegated to follow-up ticket ${ticket.id}. Keep the parent open and non-foreground until the child work lands.`
  if (!sourceTicket.decision_blockers.includes(splitNote)) {
    sourceTicket.decision_blockers.push(splitNote)
  }
}
```
No `split_kind` field exists. One template text serves all split types.

`skills/repo-scaffold-factory/assets/project-template/.opencode/tools/ticket_lookup.ts`
lines ~47-62 (split children routing block):
```typescript
if (splitChildren.length > 0 && ticket.status !== "done") {
  const foregroundChild = splitChildren[0]
  return {
    ...base,
    recommended_action: `Keep ${ticket.id} open as a split parent and foreground child ticket ${foregroundChild.id} instead of advancing the parent lane directly.`,
    recommended_ticket_update: { ticket_id: foregroundChild.id, activate: true },
  }
}
```
No check: "can the child proceed?", "is the parent done with its deliverables?", "is this a sequential split?"

`skills/repo-scaffold-factory/assets/project-template/.opencode/lib/workflow.ts`
lines ~1114-1116:
```typescript
export function openSplitScopeChildren(manifest: Manifest, ticketId: string): Ticket[] {
  return splitScopeChildren(manifest, ticketId).filter((item) => item.status !== "done" && item.resolution_state !== "superseded")
}
```
No `split_kind` field in the Ticket schema. The function returns ALL open children regardless of type.

### Root Cause in Scafforge Package

`ticket_create.ts` — uses identical decision_blockers template for all split types  
`ticket_lookup.ts` — transition_guidance routes to child unconditionally when children exist  
`workflow.ts` — Ticket schema has no `split_kind` field; no sequential validation logic

### Impact

Any repo that creates a split-scope ticket where the child depends on the parent's
deliverables will enter a permanent deadlock. Manifests as: parent says "go to child",
child says "blocked on parent", no forward path without operator intervention. Both
Spinner and Glitch confirmed this pattern.

### Priority: P0 — System-breaking

---

## DEF-002: SESSION006 — Stage/Artifact Divergence in Workflow State

**Source audit:** Spinner (primary)  
**Finding code:** SESSION006

### Description

`artifact_register.ts` updates `manifest.tickets[].artifacts` (adding the artifact record
to the manifest) but does NOT update `manifest.tickets[].stage` or `workflow-state.json`'s
stage-tracking fields. Only `ticket_update` advances the stage. If any session writes
artifacts via `artifact_write + artifact_register` without a corresponding `ticket_update`
stage advancement, or if `ticket_update` fails after artifacts are registered, manifests
can diverge: `workflow-state.json` stage (e.g., "implementation") disagrees with the
artifact record which shows review and QA artifacts.

When a subsequent session reads the stale state, `ticket_lookup.transition_guidance` uses
`ticket.stage` from the manifest (which may also be stale if artifact_register doesn't
update it). The guidance then produces contradictory instructions: "cannot move to review
before implementation artifact exists" even though an implementation artifact IS in the
manifest. The agent has no single legal next move.

`ticket_lookup` has a contradiction rule ("when manifest and workflow-state disagree about
ticket stage, trust manifest") but does not surface a recovery action when the manifest's
own stage field disagrees with its own artifact set.

### Current Scafforge Status: VERIFIED ACTIVE

**Evidence citation:**

`skills/repo-scaffold-factory/assets/project-template/.opencode/tools/artifact_register.ts`
lines ~40-60: `saveManifest(manifest)` and `saveArtifactRegistry(registry)` are called, but
there is NO call to `saveWorkflowBundle`, `loadWorkflowState`, or any stage-update path.
The artifact is registered in manifest.ticket.artifacts but manifest.ticket.stage is not
advanced. Stage advancement must be done separately via `ticket_update`.

`skills/repo-scaffold-factory/assets/project-template/.opencode/tools/ticket_lookup.ts`
lines ~160-200: The `case "implementation"` block calls `validateImplementationArtifactEvidence(ticket)`.
If an implementation artifact exists, it returns "move to review". But if `ticket.stage`
is already "implementation" while review and QA artifacts are also in the manifest, the
switch falls into the "implementation" case regardless — there is no cross-check for
artifacts from later stages indicating the ticket has already progressed further.

No diagnostic path exists in transition_guidance for "manifest.stage=X but manifest.artifacts
include artifacts from stages Y and Z which are later than X."

### Root Cause in Scafforge Package

`ticket_lookup.ts` — transition_guidance switch uses `ticket.stage` without verifying
it is consistent with the artifact record; no stale-stage detection  
`artifact_register.ts` — registers artifact without triggering stage consistency check

### Impact

Agent sessions that resume after a partial-completion prior session can get directed to
re-do already-completed work (re-write implementation) or get a deadlock with no legal
move. Spinner SESSION006 manifested this exactly.

### Priority: P1 — Workflow-blocking

---

## DEF-003: EXEC-GODOT-005-SCAFFOLD — No export_presets.cfg in Godot Android Greenfield Scaffold

**Source audits:** Spinner, Glitch  
**Finding code:** EXEC-GODOT-005

### Description

Scafforge's `repo-scaffold-factory` does not emit `export_presets.cfg` during greenfield
scaffold for Godot Android repos. The audit code `EXEC-GODOT-005` correctly fires when
the file is absent AND the release lane has started, but its trigger condition
(`release_lane_started_or_done = True`) means it only fires AFTER the damage is done —
not at scaffold time when the file should have been created.

Both Spinner and Glitch reached Android/release work without `export_presets.cfg` existing.
Both documented its absence as a "host gap" and advanced tickets to completion. In Glitch,
WFLOW-LOOP-001 (DEF-001) compounded the problem by preventing ANDROID-001 from even running.

The file is a plain-text INI file with a documented format. An AI agent CAN generate a
minimal valid `export_presets.cfg` for Android debug export without the Godot editor.
Scafforge should emit this file as a template during scaffold.

### Current Scafforge Status: VERIFIED ACTIVE

**Evidence citation:**

`ls skills/repo-scaffold-factory/assets/project-template/` — no `export_presets.cfg` file present.

`skills/repo-scaffold-factory/assets/project-template/.opencode/tools/environment_bootstrap.ts`
line ~675: checks for `godot-export-templates` but does NOT check for or generate
`export_presets.cfg`.

`adapters/manifest.json` — no Godot-specific adapter section; no required scaffold outputs
list for Godot Android.

`skills/scafforge-audit/scripts/audit_execution_surfaces.py` lines ~831-868:
EXEC-GODOT-005 fires only if `release_lane_started_or_done(manifest) or repo_claims_completion(manifest)`.
There is no earlier gate at scaffold or environment-bootstrap time.

### Root Cause in Scafforge Package

`skills/repo-scaffold-factory/assets/project-template/` — no `export_presets.cfg` template asset  
`adapters/manifest.json` — no Godot/Android adapter section  
`skills/scafforge-audit/scripts/audit_execution_surfaces.py` — EXEC-GODOT-005 fires too late  
`skills/repo-scaffold-factory/assets/project-template/.opencode/tools/environment_bootstrap.ts` — no android_source.zip check

### Impact

Every Godot Android repo generated by Scafforge lacks `export_presets.cfg`. Downstream
tickets (ANDROID-001, RELEASE-001) hit the same wall, document it as a host gap, and
advance to completion without ever actually building an APK. The release lane is permanently
blocked until human intervention creates the file.

### Priority: P1 — Workflow-blocking

---

## DEF-004: WFLOW023 — ticket-pack-builder Generates Release Tickets Without Prerequisite Export Setup

**Source audits:** Spinner (primary), Glitch  
**Finding code:** WFLOW023

### Description

`ticket-pack-builder` generates Godot Android release-lane tickets (ANDROID-001, RELEASE-001)
with acceptance criteria that require APK delivery (`godot --export-debug` succeeds, APK
exists at canonical path) without checking whether `export_presets.cfg` is present or
whether any upstream ticket has committed to creating it. As a result, RELEASE-001 is
generated with acceptance criteria that can never be satisfied: the ticket owns APK
delivery, but the prerequisite export configuration is outside its scope and no ticket
created to resolve it.

The correct behavior: if `export_presets.cfg` does not yet exist and no prior ticket
has created it, ticket-pack-builder should generate a prerequisite ticket (e.g.,
`ANDROID-EXPORT-SETUP`) before the APK build ticket, and set `depends_on: [ANDROID-EXPORT-SETUP]`
on the APK ticket.

### Current Scafforge Status: VERIFIED ACTIVE

**Evidence citation:**

`skills/ticket-pack-builder/SKILL.md` — no Godot-specific export prerequisite check before
generating Android lane tickets. The procedure generates tickets based on project brief
stack label, not on existing file state. Generated release tickets inherit acceptance
criteria templates that assume platform configuration is already done.

`skills/ticket-pack-builder/scripts/apply_remediation_follow_up.py` — remediation follow-up
logic does not check for missing export_presets.cfg when generating Android remediation tickets.

### Root Cause in Scafforge Package

`skills/ticket-pack-builder/SKILL.md` — no Android export prerequisite gate logic  
`skills/ticket-pack-builder/scripts/` — no pre-generation check for export_presets.cfg state

### Impact

RELEASE-001 type tickets are generated with structural acceptance criteria they can never
satisfy (because the export configuration prerequisite is unowned). This creates permanently
blocked tickets even when all other prerequisites are met.

### Priority: P1 — Workflow-blocking

---

## DEF-005: REF-003-FP — node_modules Not Excluded from Import Scanner

**Source audits:** Spinner (primary), Glitch, GPTTalker  
**Finding code:** REF-003 (false positive in all three repos)

### Description

The `audit_execution_surfaces.py` REF-003 checker scans for TypeScript imports that
reference compiled `.js` files that don't exist in the repo. TypeScript packages in
`node_modules/` routinely have source `.ts` files importing compiled-output paths
(e.g., `./ZodError.js`, `./external.js`) that are generated at build time and are not
vendored alongside the sources. The checker incorrectly flags these as broken imports.

All three audited repos triggered REF-003 false positives in `node_modules/zod/src/`.
This is noise that obscures real findings in every repo using npm/yarn.

### Current Scafforge Status: VERIFIED ACTIVE

**Evidence citation:**

`skills/scafforge-audit/scripts/audit_execution_surfaces.py` — grep for `node_modules`:
```
$ grep -n "node_modules" skills/scafforge-audit/scripts/audit_execution_surfaces.py
(no output)
```
No exclusion exists. The import scanner walks all files in the repo tree without excluding
`node_modules/`, `vendor/`, or `.git/`.

### Root Cause in Scafforge Package

`skills/scafforge-audit/scripts/audit_execution_surfaces.py` — no `SCAN_EXCLUSIONS`
pattern list in the import resolution checker

### Impact

Generates false-positive REF-003 findings in every repo that uses npm or yarn. Obscures
real import errors. Erodes trust in audit results. Adds noise to disposition bundles.

### Priority: P2 — Quality/reliability

---

## DEF-006: SESSION005 — Team-Leader Template Advisory (Not Imperative) on Coordinator Artifact Authorship

**Source audit:** Glitch  
**Finding code:** SESSION005

### Description

The team-leader agent template says "treat coordinator-authored planning, implementation,
review, or QA artifacts as suspect evidence that needs remediation" (advisory) but does NOT
contain an imperative prohibition: "You MUST NOT call `artifact_write` for planning,
implementation, review, or QA artifacts."

Additionally, the delegation pattern used by the team leader asks specialist agents to
"return the full artifact content" in their final message rather than "write the artifact
yourself via artifact_write and call artifact_register with the path." This makes it
easy for the team leader to receive the planned content as a string and write it using
artifact_write itself — which is a role boundary violation.

In Glitch, the team leader explicitly wrote the planning artifact itself after receiving
it as content from the planner subagent. The audit log shows the coordinator writing
`.opencode/state/plans/release-001-planning-plan.md` directly.

### Current Scafforge Status: VERIFIED ACTIVE — partially

**Evidence citation:**

`skills/repo-scaffold-factory/assets/project-template/.opencode/agents/__AGENT_PREFIX__-team-leader.md`
line ~191:
```
- treat coordinator-authored planning, implementation, review, or QA artifacts as suspect
  evidence that needs remediation, not as proof of progression
```
This is advisory language. It says "if it happens, treat it as suspect" — not "do not do this."

The same file line ~194:
```
- require specialists that persist stage text to use artifact_write and then artifact_register
  with the supplied artifact stage and kind
```
This describes the correct pattern but doesn't explicitly prohibit the team leader from
also calling artifact_write.

No imperative MUST NOT statement exists in the template.

The `__AGENT_PREFIX__-planner.md` template does not include a rule requiring the planner
to call `artifact_write` itself rather than returning content to the parent.

### Root Cause in Scafforge Package

`__AGENT_PREFIX__-team-leader.md` — advisory language where imperative prohibition is needed  
`__AGENT_PREFIX__-planner.md` — delegation instruction pattern asks for content return instead of write-then-return-path

### Impact

Coordinator-authored artifacts bypass specialist ownership — the artifact content is
generated without the specialist agent's full context, tooling, and grounding. In Glitch,
the team leader wrote a RELEASE-001 plan that was based on planner output, but the planner
may have had a different (and more grounded) view of the planning requirements. The
artifact produced did not reflect full specialist analysis.

More broadly: if coordinators routinely write artifacts, stage artifact ownership becomes
meaningless as an evidence quality signal.

### Priority: P2 — Quality/reliability

---

## DEF-007: PROJ-VER-001 — No Godot 4.x config_version / Renderer Validation in Audit

**Source audit:** Glitch  
**Finding code:** PROJ-VER-001

### Description

`project.godot` in Glitch used `config_version=2` (Godot 2.x era format) and
`GLES2` renderer (Godot 3.x; removed in Godot 4). Godot 4.6.2 successfully parsed
this file due to lenient parsing, but the wrong renderer reference may cause silent
fallback behavior. No Scafforge audit check currently validates that `config_version=5`
and a Godot 4.x-valid renderer is specified.

For Godot 4.x, the valid renderer values are:
- `forward_plus`  
- `mobile`
- `gl_compatibility` (replaces GLES2/GLES3 from Godot 3.x)

### Current Scafforge Status: VERIFIED ACTIVE

**Evidence citation:**

`skills/scafforge-audit/scripts/audit_execution_surfaces.py` lines ~789-835:
The `audit_godot_execution` function checks EXEC-GODOT-001 (missing autoload scripts),
EXEC-GODOT-002 (broken scene references), EXEC-GODOT-003 (missing extends scripts),
EXEC-GODOT-004 (headless validation failure), and EXEC-GODOT-005 (Android export surfaces).
There is NO check for `config_version` or renderer format in `project.godot`.

### Root Cause in Scafforge Package

`skills/scafforge-audit/scripts/audit_execution_surfaces.py` — missing validation logic
for `config_version` and renderer in `audit_godot_execution`

### Impact

AI-generated Godot 4.x projects may have incorrect version format due to model training
data mixing Godot 3.x and 4.x examples. Export and rendering behavior may silently differ
from expected. Audit does not catch the mismatch.

### Priority: P2 — Quality/reliability

---

## DEF-008: EXEC-WARN-001 / Evidence Fabrication — No Mandatory Command Output in Remediation Review Artifacts

**Source audit:** Glitch  
**Finding code:** EXEC-WARN-001

### Description

REMED-002's review artifact explicitly stated "WARNING gone from headless output" but the
actual `godot-headless.log` still showed the WARNING. The reviewer wrote a claim without
actually running the validation command and checking its output. This is evidence fabrication.

Scafforge's reviewer agent template does not require that review artifacts for remediation
tickets include literal command output proving the original finding no longer reproduces.
Prose claims are accepted as review evidence.

The audit script `audit_execution_surfaces.py` does not currently check that remediation
ticket (those with `finding_source`) review artifacts contain command output evidence rather
than prose claims.

### Current Scafforge Status: VERIFIED ACTIVE

**Evidence citation:**

`skills/repo-scaffold-factory/assets/project-template/.opencode/agents/__AGENT_PREFIX__-reviewer-code.md`
— does not contain a rule requiring command output evidence specifically for remediation
tickets. The reviewer discipline rules do not distinguish between normal review artifacts
and remediation review artifacts.

`skills/scafforge-audit/scripts/audit_repo_process.py` — no check that looks for
remediation tickets with `finding_source` set and verifies their review artifact contains
command evidence vs prose.

### Root Cause in Scafforge Package

`__AGENT_PREFIX__-reviewer-code.md` — no enhanced evidence requirement for remediation reviews  
`audit_repo_process.py` — no remediation evidence gate check

### Impact

Findings can be marked resolved via fabricated evidence. This undermines the entire repair
cycle: scafforge-audit marks findings as addressed, scafforge-repair routes follow-up based
on those marks, and if evidence is fabricated then genuinely broken code goes undetected.
In Glitch, the persisting GlitchPhysicsModifier WARNING was invisible to subsequent sessions
because REMED-002 was "PASS."

### Priority: P2 — Quality/reliability

---

## DEF-009: EXEC001-TYPE — No Stack-Standards Guidance for Python TYPE_CHECKING Annotation Pattern

**Source audit:** GPTTalker  
**Finding code:** EXEC001

### Description

`src/hub/dependencies.py` in GPTTalker used unquoted return type annotations for two
functions that import their types under `TYPE_CHECKING`:

```python
# BROKEN:
async def get_relationship_service(...) -> RelationshipService:

# CORRECT pattern used elsewhere in same file:
async def get_cross_repo_service(...) -> "CrossRepoService":
```

When Python evaluates `get_relationship_service` at import time (FastAPI builds dependency
graphs at import), `RelationshipService` is not in the module namespace because
`TYPE_CHECKING` is `False` at runtime. This raises `NameError: name 'RelationshipService'
is not defined` and prevents `from src.hub.main import app` from succeeding.

This is a generated-repo source defect introduced by an implementer agent. The Scafforge
`stack-standards` skill for Python+FastAPI projects does not contain an explicit rule
about this pattern.

### Current Scafforge Status: VERIFIED ACTIVE (advisory gap)

**Evidence citation:**

`skills/repo-scaffold-factory/assets/project-template/.opencode/skills/stack-standards/SKILL.md`
— no specific guidance for TYPE_CHECKING import patterns in FastAPI dependency functions.
The generated skill gives general Python guidance but does not call out this specific
footgun.

Note: This is a guidance gap (P3 advisory), not a workflow failure. The defect itself was
in the generated repo's source code, not in the Scafforge managed workflow surface.

### Root Cause in Scafforge Package

`skills/repo-scaffold-factory/assets/project-template/.opencode/skills/stack-standards/SKILL.md`
— missing TYPE_CHECKING annotation guidance for FastAPI repos

### Impact

FastAPI+Python repos generated by Scafforge may have this annotation pattern introduced
by implementer agents who follow the file structure but miss the quoting requirement.
The hub service fails to start.

### Priority: P3 — Advisory

---

## Not-Verified / Historical Defects

### WFLOW010 — GPTTalker Restart Surface Format Drift

**Source:** GPTTalker audit  
**Status: UNVERIFIABLE as current package defect**

The GPTTalker repair cycle (2026-04-07T22:18:12Z) generated a START-HERE.md that the
WFLOW010 checker flagged because machine-parseable fields did not match the parser's
expectations. The current Scafforge `regenerate_restart_surfaces.py` calls
`handoff_publish.ts` via `run_generated_tool`, which generates the canonical
key-value format expected by `audit_restart_surfaces.py`. The current format IS correct.

The GPTTalker WFLOW010 was likely a one-time artifact of that specific repair cycle using
an older version of the template or a repair-generated START-HERE.md that predated the
current key-value format. Cannot be reproduced in a clean greenfield run with current package.

**Not included in implementation plan.** If WFLOW010 recurs in a freshly scaffolded repo,
revisit.

### WFLOW008 — GPTTalker pending_process_verification Stranded

**Status: UNVERIFIABLE as standalone package defect**

The `workflow.ts` `getProcessVerificationState` function DOES compute `clearable_now: true`
when `affectedDoneTickets.length === 0`, and `ticket_lookup` DOES surface the clear path
("Use ticket_update to clear pending_process_verification now…"). The WFLOW008 in 
GPTTalker was a symptom of WFLOW010 (stale START-HERE.md not showing the clearable_now
guidance). Not a separate package defect.

### WFLOW-LEASE-001 — Glitch Stale Write Lease

**Status: UNVERIFIABLE / not addressable at package level**

An agent session ended with an uncleaned write lease for ANDROID-001. Write lease lifetimes
are determined by session scope. Lease TTLs would require significant infrastructure
changes (timeout-based expiry). Documented as an operational hygiene note rather than a
fixable package defect. The `ticket_lookup` already warns about stale leases; adding a
lease age display to START-HERE.md would improve visibility.

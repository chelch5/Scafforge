# 02 — Implementation Plan

**Created:** 2026-04-08  
Ordered by priority. All file paths are absolute from Scafforge repo root.

---

## DEF-001 — WFLOW-LOOP-001: Split-Scope Sequential Dependency Deadlock (P0)

### Summary
`ticket_create` uses the same `decision_blockers` template for parallel and sequential
splits. `ticket_lookup` routes unconditionally to split children without checking whether
the child can yet proceed. No `split_kind` field exists on the Ticket schema.

### Exact Files to Modify

1. `skills/repo-scaffold-factory/assets/project-template/.opencode/lib/workflow.ts`
2. `skills/repo-scaffold-factory/assets/project-template/.opencode/tools/ticket_create.ts`
3. `skills/repo-scaffold-factory/assets/project-template/.opencode/tools/ticket_lookup.ts`

### Changes Required

#### File 1: `workflow.ts`

**What is wrong:** The `Ticket` type has no `split_kind` field. The ticket schema has no
way to distinguish parallel splits from sequential splits.

**Change 1a — Add `split_kind` to Ticket type:**

In the `Ticket` interface/type (wherever `source_mode` is declared), add:
```typescript
split_kind?: "parallel_fragment" | "sequential_dependent"
```

**Change 1b — Add `split_kind` to `createTicketRecord`:**

In `createTicketRecord(args)`, add:
```typescript
split_kind: args.split_kind,
```

**Change 1c — Modify `openSplitScopeChildren` to be split_kind-aware:**

The current function:
```typescript
export function openSplitScopeChildren(manifest: Manifest, ticketId: string): Ticket[] {
  return splitScopeChildren(manifest, ticketId).filter(
    (item) => item.status !== "done" && item.resolution_state !== "superseded"
  )
}
```

Add a new helper to distinguish sequential children:
```typescript
export function openSequentialSplitChildren(manifest: Manifest, ticketId: string): Ticket[] {
  return openSplitScopeChildren(manifest, ticketId).filter(
    (item) => item.split_kind === "sequential_dependent"
  )
}

export function openParallelSplitChildren(manifest: Manifest, ticketId: string): Ticket[] {
  return openSplitScopeChildren(manifest, ticketId).filter(
    (item) => item.split_kind !== "sequential_dependent"  // includes undefined (legacy parallel default)
  )
}
```

**Change 1d — In `ticket_update` write-time invariant**, add this assertion:
When `ticket_update` sets `activate: true` on a child ticket whose `split_kind ===
"sequential_dependent"`, verify the parent ticket is `status === "done"`. If not, throw:
```
BLOCKER: sequential_split_parent_not_done — <parent_id> must reach done before
<child_id> can be activated.
```

#### File 2: `ticket_create.ts`

**What is wrong:** Line ~130-142 adds the same `decision_blockers` text for all split
types, never sets `split_kind`.

**Change 2a — Add `split_kind` to `ticket_create` args:**
```typescript
split_kind: tool.schema.enum(["parallel_fragment", "sequential_dependent"])
  .describe("Whether the split child is an independent parallel fragment (can run at same time as parent) or a sequential dependent (parent must complete its deliverables first).")
  .optional(),
```

**Change 2b — Pass `split_kind` to `createTicketRecord`:**
```typescript
const ticket = createTicketRecord({
  // ... existing args ...
  split_kind: args.split_kind,
})
```

**Change 2c — Use different `decision_blockers` text based on `split_kind`:**

Replace the current:
```typescript
if (sourceTicket && sourceMode === "split_scope") {
  const splitNote = `Split scope delegated to follow-up ticket ${ticket.id}. Keep the parent open and non-foreground until the child work lands.`
  if (!sourceTicket.decision_blockers.includes(splitNote)) {
    sourceTicket.decision_blockers.push(splitNote)
  }
}
```

With:
```typescript
if (sourceTicket && sourceMode === "split_scope") {
  const isSequential = args.split_kind === "sequential_dependent"
  const splitNote = isSequential
    ? `Sequential split: this ticket (${sourceTicketId}) must complete its deliverables and reach done before follow-up ticket ${ticket.id} can begin. Do NOT foreground ${ticket.id} until this ticket is done.`
    : `Parallel split: scope delegated to follow-up ticket ${ticket.id}. Keep this ticket open and non-foreground until the child work lands.`
  if (!sourceTicket.decision_blockers.includes(splitNote)) {
    sourceTicket.decision_blockers.push(splitNote)
  }
}
```

#### File 3: `ticket_lookup.ts`

**What is wrong:** Lines ~47-62 — the split children routing block routes to the first
open child unconditionally, regardless of split_kind or whether the child can proceed.

**Change 3a — Split the routing logic by split_kind:**

Replace the current splitChildren block:
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

With:
```typescript
if (splitChildren.length > 0 && ticket.status !== "done") {
  const sequentialChildren = splitChildren.filter(c => c.split_kind === "sequential_dependent")
  const parallelChildren = splitChildren.filter(c => c.split_kind !== "sequential_dependent")

  // SEQUENTIAL: parent must complete first. Do NOT route to child; continue parent lifecycle.
  if (sequentialChildren.length > 0 && parallelChildren.length === 0) {
    const childIds = sequentialChildren.map(c => c.id).join(", ")
    // Fall through to normal lifecycle routing — do NOT return early here.
    // Add a warning to the base object so transition_guidance includes it.
    base.warnings.push(
      `Sequential split child ticket(s) ${childIds} are waiting on this ticket to complete. ` +
      `Continue this ticket's normal lifecycle. Do NOT activate the child until this ticket reaches done.`
    )
    // Do not return here — fall through to the stage switch
  } else if (parallelChildren.length > 0) {
    // PARALLEL: foreground the child as before
    const foregroundChild = parallelChildren[0]
    return {
      ...base,
      recommended_action: `Keep ${ticket.id} open as a split parent and foreground child ticket ${foregroundChild.id} instead of advancing the parent lane directly.`,
      recommended_ticket_update: { ticket_id: foregroundChild.id, activate: true },
    }
  }
}
```

Note: The `// Fall through to normal lifecycle routing` comment is critical — for sequential
split parents, transition_guidance must continue into the stage switch so the parent gets
proper lifecycle routing (planning → implementation → review → QA → done).

**Change 3b — In `ticket_update` (when activating a child), add invariant check:**

Already described in Change 1d above. Implement in `ticket_update.ts`:
```typescript
// After resolving the target ticket:
if (args.activate === true) {
  const ticketRecord = getTicket(manifest, args.ticket_id)
  if (ticketRecord.split_kind === "sequential_dependent" && ticketRecord.source_ticket_id) {
    const parentTicket = getTicket(manifest, ticketRecord.source_ticket_id)
    if (parentTicket.status !== "done") {
      throw new Error(
        `BLOCKER: sequential_split_parent_not_done — ${parentTicket.id} must reach done ` +
        `before sequential dependent ${ticketRecord.id} can be activated.`
      )
    }
  }
}
```

### Greenfield Prevention

New greenfield repos: ticket_create tool requires callers to specify `split_kind` for any
`source_mode: "split_scope"` ticket. The Scafforge skills (ticket-pack-builder, etc.) that
generate Android lane tickets should be updated to pass `split_kind: "sequential_dependent"`
for ANDROID-001 → RELEASE-001 splits.

### Repair Prevention

scafforge-repair: when applying repair to a repo with a stuck split-scope deadlock, the
repair runner should detect the deadlock pattern (parent has split children, all children
are blocked, parent has no implementation artifact) and offer to set `split_kind: "sequential_dependent"` on the child ticket to re-enable normal parent routing.

### Verification Steps

```bash
# 1. Verify split_kind field exists in ticket schema
grep -n "split_kind" skills/repo-scaffold-factory/assets/project-template/.opencode/lib/workflow.ts

# 2. Verify ticket_create tool has split_kind arg
grep -n "split_kind" skills/repo-scaffold-factory/assets/project-template/.opencode/tools/ticket_create.ts

# 3. Verify ticket_lookup handles sequential children differently from parallel
grep -n "sequential_dependent\|parallelChildren\|sequentialChildren" \
  skills/repo-scaffold-factory/assets/project-template/.opencode/tools/ticket_lookup.ts

# 4. Verify ticket_update rejects activating sequential child before parent is done
grep -n "sequential_split_parent_not_done" \
  skills/repo-scaffold-factory/assets/project-template/.opencode/tools/ticket_update.ts

# 5. Functional test: create a greenfield repo, create ticket A, create split_scope
#    sequential_dependent ticket B from A. Run ticket_lookup on A — verify it returns
#    lifecycle routing (e.g., "write planning artifact") NOT "activate B".
```

### Regression Guard

Integration test in `scripts/integration_test_scafforge.py`: Add a test scenario that
creates a parent ticket, creates a sequential_dependent split child, calls ticket_lookup on
the parent, and asserts the result does NOT contain `recommended_ticket_update.ticket_id == child_id`.

---

## DEF-002 — SESSION006: Stage/Artifact Divergence in Workflow State (P1)

### Summary
`artifact_register` updates manifest artifacts but not the manifest ticket's stage field.
`ticket_lookup` does not detect when `ticket.stage` is stale relative to the artifact record.

### Exact Files to Modify

1. `skills/repo-scaffold-factory/assets/project-template/.opencode/tools/ticket_lookup.ts`

### Changes Required

**What is wrong:** `buildTransitionGuidance` uses `ticket.stage` as the switch key but
does not cross-check whether the ticket has artifacts from stages *later* than `ticket.stage`.
If `ticket.stage = "implementation"` but the manifest's `ticket.artifacts` contains a
registered review artifact (or QA artifact), the ticket has clearly progressed further than
the stage field reflects. Instead of routing to "write implementation artifact", the guidance
should detect this and surface a recovery action.

**Change — Add stale-stage detection before the stage switch:**

Just before the `switch (ticket.stage)` block, add:

```typescript
// Stale-stage detection: detect when artifacts from later stages exist despite earlier stage.stage
const STAGE_ORDER = ["environment-bootstrap", "planning", "plan_review", "implementation", "review", "qa", "smoke-test", "closeout"] as const
const currentStageIndex = STAGE_ORDER.indexOf(ticket.stage as typeof STAGE_ORDER[number])
const latestArtifactStageIndex = ticket.artifacts.reduce((max, art) => {
  const idx = STAGE_ORDER.indexOf(art.stage as typeof STAGE_ORDER[number])
  return idx > max ? idx : max
}, -1)

if (currentStageIndex >= 0 && latestArtifactStageIndex > currentStageIndex) {
  const inferredStage = STAGE_ORDER[latestArtifactStageIndex]
  return {
    ...base,
    next_allowed_stages: [inferredStage],
    required_artifacts: [],
    next_action_kind: "ticket_update",
    next_action_tool: "ticket_update",
    delegate_to_agent: null,
    required_owner: "team-leader",
    recommended_action: `STALE STAGE DETECTED: manifest records ticket.stage="${ticket.stage}" but artifacts up to "${inferredStage}" are already registered. The stage field is behind the artifact record. Call ticket_update with stage="${inferredStage}" to align the stage field with the artifact record, then re-run ticket_lookup.`,
    current_state_blocker: `ticket.stage="${ticket.stage}" but latest artifact stage is "${inferredStage}" — stage field is stale.`,
    recommended_ticket_update: { ticket_id: ticket.id, stage: inferredStage, activate: true },
    warnings: [`Stale stage detected: manifest stage is "${ticket.stage}" but artifacts exist up to "${inferredStage}".`],
  }
}
```

This must be placed AFTER the bootstrap check, AFTER the splitChildren parallel check, and
BEFORE the stage switch. It must NOT trigger for sequential split parents (which may have
a legitimate earlier stage while children hold later artifacts).

### Greenfield Prevention

New repos: the stale-stage detection is always active and will surface the recovery path
immediately in any session that resumes after a previous session failed to call ticket_update.

### Repair Prevention

scafforge-repair: add a check in `apply_repo_process_repair.py` that detects stale-stage
tickets and emits them as workflow findings in the repair output, so the repair runner can
proactively call ticket_update for each stale ticket before regenerating restart surfaces.

### Verification Steps

```bash
# 1. Verify stale-stage detection block exists in ticket_lookup.ts
grep -n "STALE STAGE\|latestArtifactStageIndex\|currentStageIndex" \
  skills/repo-scaffold-factory/assets/project-template/.opencode/tools/ticket_lookup.ts

# 2. Integration test: create a ticket at stage=planning, register an implementation artifact
#    (bypassing ticket_update), call ticket_lookup — verify response contains
#    "STALE STAGE DETECTED" and recommended_ticket_update.stage="implementation"
```

### Regression Guard

Add a unit test where a ticket has `stage: "implementation"` but artifacts include a
"review" kind artifact. Verify that `buildTransitionGuidance` returns the stale-stage
recovery path rather than the normal "implementation" stage guidance.

---

## DEF-003 — EXEC-GODOT-005-SCAFFOLD: export_presets.cfg Not in Greenfield Scaffold (P1)

Full analysis in `03-export-presets-decision.md`. This section covers the package
implementation only.

### Summary
No `export_presets.cfg` is emitted when Scafforge scaffolds a Godot Android repo.
The file must be added as a template asset.

### Exact Files to Modify/Create

1. **NEW:** `skills/repo-scaffold-factory/assets/project-template/export_presets.cfg`
2. `skills/repo-scaffold-factory/SKILL.md` — add Godot-specific scaffold note
3. `skills/scafforge-audit/scripts/audit_execution_surfaces.py` — add android_source.zip check

### Changes Required

#### File 1: Create `skills/repo-scaffold-factory/assets/project-template/export_presets.cfg`

This file should contain the minimum viable Android debug preset. Key substitution variables
(`__PACKAGE_NAME__`, `__PROJECT_NAME__`) must be in the format that the scaffold factory
or adapter scripts can replace. The actual template content is specified in full in
`03-export-presets-decision.md`.

The file should be annotated with a comment indicating which variables need substitution:
```ini
; SCAFFORGE-TEMPLATE: Set package/name to reverse-domain package name, e.g. com.example.myapp
; SCAFFORGE-TEMPLATE: Set exporter version/name to your app version
[preset.0]
name="Android"
platform="Android"
...
```

#### File 2: `skills/scafforge-audit/scripts/audit_execution_surfaces.py`

**Current EXEC-GODOT-005 trigger:** `release_lane_started_or_done(manifest) or repo_claims_completion(manifest)`

**Change — Add earlier gate in `audit_godot_execution`:**

After the existing EXEC-GODOT-001/002/003/004 checks, BEFORE the EXEC-GODOT-005 block,
add a check that fires when `declares_godot_android_target(root)` AND
`android_lane_has_started(manifest)` (i.e., any Android-related ticket is past planning)
AND `export_presets.cfg` is absent:

```python
# Earlier gate: fire when Android lane is in flight, not just after release
if declares_godot_android_target(root) and android_lane_has_started(manifest):
    if not has_android_export_preset(root):
        _add_execution_finding(
            findings, ctx,
            code="EXEC-GODOT-005-EARLY",
            severity="warning",
            problem="Android export preset missing while Android lane is active.",
            ...
        )
```

**Note:** Don't remove the existing broader EXEC-GODOT-005 check — it catches repos that
were already scaffolded before this fix.

**Add `android_source.zip` check:**

In `audit_godot_execution`, after checking `godot-export-templates`:
```python
# Check for android_source.zip in export templates
templates_dirs = list(Path.home().rglob("export_templates/*/android_source.zip"))
if not templates_dirs:
    alt_path = list(Path.home().rglob("export_templates/*/android_source/app/libs/godot-lib.aar"))
    if not alt_path:
        _add_execution_finding(
            findings, ctx,
            code="EXEC-GODOT-006",
            severity="warning",
            problem="Godot Android source package not found in export templates.",
            root_cause="android_source.zip (or extracted godot-lib.aar) is required for custom Godot Android builds.",
            files=[project_file],
            safer_pattern="Install Godot Android export templates via Godot editor or CI script before starting Android lane work.",
            evidence=["No android_source.zip or godot-lib.aar found in ~/.local/share/godot/export_templates/"],
            root=root,
        )
```

#### File 3: `skills/repo-scaffold-factory/SKILL.md`

Add a note in the Godot Android scaffold procedure:
- When `stack_label` contains "Android" and the canonical brief indicates a Godot 4.x
  Android target, emit `export_presets.cfg` from the template asset with package name
  substituted from the brief.
- Mark two fields in `export_presets.cfg` as requiring team configuration in SETUP-001:
  `package/name` (must match app store listing) and `version/name` / `version/code`.

### Greenfield Prevention

New repos: `export_presets.cfg` is present from day one. ANDROID-001 can proceed without
hitting a wall. EXEC-GODOT-005 fires only for legacy repos missing the file.

### Repair Prevention

`scafforge-repair`: detect absence of `export_presets.cfg` in Godot Android repos.
Classify as a safe auto-repair (generate from template with values from canonical brief).
Document the generated values in a repair note.

### Verification Steps

```bash
# 1. Verify template file exists
ls skills/repo-scaffold-factory/assets/project-template/export_presets.cfg

# 2. Verify file contains required INI sections
grep "\[preset.0\]\|\[preset.0.options\]" \
  skills/repo-scaffold-factory/assets/project-template/export_presets.cfg

# 3. Verify audit has android_source check
grep -n "EXEC-GODOT-006\|android_source" \
  skills/scafforge-audit/scripts/audit_execution_surfaces.py

# 4. Greenfield test: scaffold a test repo with Godot Android stack label;
#    verify export_presets.cfg is present in output root
```

### Regression Guard

Smoke test: add a fixture that scaffolds a Godot Android repo and checks that
`export_presets.cfg` exists in the output. Add to `scripts/smoke_test_scafforge.py`.

---

## DEF-004 — WFLOW023: ticket-pack-builder Prerequisite Tracking for Android Export (P1)

### Summary
ticket-pack-builder generates release tickets with untracked prerequisite deliverables.

### Exact Files to Modify

1. `skills/ticket-pack-builder/SKILL.md`

### Changes Required

**What is wrong:** The Procedure section in `ticket-pack-builder/SKILL.md` generates
Android lane tickets (ANDROID-001, RELEASE-001) without checking whether export
configuration prerequisites are present or tracked.

**Change — Add Godot Android prerequisite check to ticket generation procedure:**

In the `# Procedure` section, in the subsection that handles Godot Android backlog
generation, add the following rule:

```
### Godot Android prereq gate

Before generating Android export or release tickets:

1. Check whether `export_presets.cfg` exists in the repo root.
2. If absent AND no prior ticket has committed to creating it:
   a. Generate a dedicated `ANDROID-EXPORT-SETUP` ticket (or equivalent) whose
      acceptance criteria include: `export_presets.cfg` exists with correct package name,
      platform, and Android preset.
   b. Set `depends_on: [ANDROID-EXPORT-SETUP]` on the APK-build ticket (ANDROID-001).
   c. Set `split_kind: "sequential_dependent"` on RELEASE-001 relative to ANDROID-001.
3. Acceptance criteria for APK-build and release tickets must reference only deliverables
   within that ticket's scope or explicit dependencies. Never generate acceptance criteria
   that require work from untracked upstream tasks.
```

The `split_kind: "sequential_dependent"` specification for RELEASE-001's relationship to
ANDROID-001 is critical — it ties into the DEF-001 fix so that RELEASE-001 is only
activated after ANDROID-001 reaches done.

### Greenfield Prevention

Newly generated backlogs for Godot Android repos include the prerequisite ANDROID-EXPORT-SETUP
ticket and correct dependency chain from the start.

### Repair Prevention

When repair runs ticket-pack-builder in remediation mode on an existing Godot Android repo,
it should apply the same check: if ANDROID-EXPORT-SETUP or equivalent is missing AND
export_presets.cfg doesn't exist, generate the prerequisite ticket.

### Verification Steps

```bash
# 1. Verify SKILL.md contains the Android prereq gate section
grep -n "ANDROID-EXPORT-SETUP\|Godot Android prereq\|split_kind.*sequential" \
  skills/ticket-pack-builder/SKILL.md

# 2. Functional test: generate a backlog for a Godot Android brief without export_presets.cfg;
#    verify the output ticket list includes ANDROID-EXPORT-SETUP before ANDROID-001
```

### Regression Guard

Add eval case to `skills/ticket-pack-builder/evals/behavior.jsonl`: prompt that generates
Android backlog for a Godot 4.x Android game without existing export_presets.cfg. The
required_patterns should include `ANDROID-EXPORT-SETUP` and `sequential_dependent`.

---

## DEF-005 — REF-003-FP: node_modules Not Excluded from Import Scanner (P2)

### Summary
The import scanner in `audit_execution_surfaces.py` has no exclusion list.
node_modules scan produces false-positive REF-003 in all npm repos.

### Exact Files to Modify

1. `skills/scafforge-audit/scripts/audit_execution_surfaces.py`

### Changes Required

**What is wrong:** The function that walks repo files for TypeScript/Python import
resolution does not exclude `node_modules/`, `vendor/`, or `.git/` directories.

**Change — Add SCAN_EXCLUSIONS to the import resolution section:**

Find the function that generates the list of files to scan for imports (likely the REF-003
checker is in or near `audit_ref003_imports` or similar). At the top of that function,
add a path exclusion filter:

```python
IMPORT_SCAN_EXCLUSIONS = frozenset([
    "node_modules",
    ".git",
    "vendor",
    "__pycache__",
    ".venv",
    "venv",
    ".tox",
    "dist",
    "build",
    ".opencode/node_modules",
])

def should_exclude_from_import_scan(path: Path, root: Path) -> bool:
    """Return True if path is inside a directory that should be excluded from import scanning."""
    try:
        relative = path.relative_to(root)
    except ValueError:
        return False
    return any(part in IMPORT_SCAN_EXCLUSIONS for part in relative.parts)
```

Then, wherever files are collected for import scanning (look for the REF-003 logic),
wrap the file collection with:
```python
files_to_scan = [f for f in all_files if not should_exclude_from_import_scan(f, root)]
```

### Verification Steps

```bash
# 1. Verify IMPORT_SCAN_EXCLUSIONS or should_exclude_from_import_scan exists
grep -n "node_modules\|SCAN_EXCLUSIONS\|exclude.*import" \
  skills/scafforge-audit/scripts/audit_execution_surfaces.py

# 2. Re-run audit on Spinner; verify REF-003 no longer fires for
#    .opencode/node_modules/zod paths
python3 skills/scafforge-audit/scripts/audit_execution_surfaces.py \
  --repo /home/pc/projects/spinner 2>&1 | grep REF-003
# Expected: no REF-003 output
```

### Regression Guard

Add a test fixture with a `.opencode/node_modules/zod/src/index.ts` file containing
broken TypeScript imports. Run audit on it. Assert that REF-003 does NOT fire.

---

## DEF-006 — SESSION005: Team-Leader Artifact_write Prohibition (P2)

### Summary
Team-leader template uses advisory language instead of imperative prohibition.
Delegation prompt instructs specialist to return content instead of write it.

### Exact Files to Modify

1. `skills/repo-scaffold-factory/assets/project-template/.opencode/agents/__AGENT_PREFIX__-team-leader.md`
2. `skills/repo-scaffold-factory/assets/project-template/.opencode/agents/__AGENT_PREFIX__-planner.md`

### Changes Required

#### File 1: `__AGENT_PREFIX__-team-leader.md`

**Change — Replace advisory with imperative prohibition.**

Find the current advisory line (~line 191):
```
- treat coordinator-authored planning, implementation, review, or QA artifacts as suspect
  evidence that needs remediation, not as proof of progression
```

Replace with (or add above it):
```
- you MUST NOT call artifact_write for planning, implementation, review, QA, or smoke-test
  artifact bodies; if you receive artifact content from a specialist's return value, route
  the specialist BACK to call artifact_write and artifact_register themselves; only then
  advance the ticket stage
- if a specialist returns full artifact body text instead of a registered path, treat it as
  a failed delegation and re-delegate with the corrected instruction pattern below
```

Add to the task delegation instruction section (for plan delegation):
```
Correct delegation instruction pattern:
  "Write the [planning/implementation/review/QA] artifact yourself using artifact_write
   at the canonical path, then call artifact_register to register it. Return ONLY the
   registered artifact path and a one-sentence summary. Do NOT return the full artifact body."

Incorrect (prohibited) delegation pattern:
  "Return the full artifact content in your final message ready for artifact_write."
```

#### File 2: `__AGENT_PREFIX__-planner.md`

**Change — Add explicit self-write instruction:**

In the `# Output contract` or `# Procedure` section, add:
```
You MUST write your planning artifact yourself using artifact_write at the canonical path,
then call artifact_register. Return ONLY the registered artifact path and a brief summary.
Do NOT return the full artifact body to the team leader for them to write on your behalf.
```

### Verification Steps

```bash
# 1. Verify imperative prohibition exists in team-leader template
grep -n "MUST NOT call artifact_write\|artifact_write.*forbidden\|must not.*artifact_write" \
  "skills/repo-scaffold-factory/assets/project-template/.opencode/agents/__AGENT_PREFIX__-team-leader.md"

# 2. Verify planner template instructs self-write
grep -n "write.*artifact_write\|artifact_write.*yourself\|Do NOT return.*body" \
  "skills/repo-scaffold-factory/assets/project-template/.opencode/agents/__AGENT_PREFIX__-planner.md"
```

### Regression Guard

Add an eval case to the planner's behavior.jsonl: prompt that asks the planner to produce
a planning artifact. The `forbidden_patterns` should include phrases like "Return the full
artifact body" or "ready for artifact_write" in the planner's output.

---

## DEF-007 — PROJ-VER-001: No Godot 4.x config_version / Renderer Validation (P2)

### Summary
audit_execution_surfaces.py has no check for `config_version=5` or invalid renderers
in Godot 4.x repos.

### Exact Files to Modify

1. `skills/scafforge-audit/scripts/audit_execution_surfaces.py`

### Changes Required

**Change — Add config_version and renderer validation to `audit_godot_execution`:**

After the existing EXEC-GODOT-001/002/003 checks in `audit_godot_execution`, add:

```python
# EXEC-GODOT-007: project.godot config_version check
project_text = ctx.read_text(project_file) if project_file.exists() else ""
config_version_match = re.search(r"^config_version\s*=\s*(\d+)", project_text, re.MULTILINE)
if config_version_match:
    version = int(config_version_match.group(1))
    if version < 5:
        _add_execution_finding(
            findings, ctx,
            code="EXEC-GODOT-007",
            severity="warning",
            problem=f"project.godot uses config_version={version} which is not the Godot 4.x format (requires config_version=5).",
            root_cause="AI model may have generated project.godot using Godot 3.x or 2.x format. Godot 4.x requires config_version=5.",
            files=[project_file],
            safer_pattern="Ensure project.godot contains config_version=5 for all Godot 4.x projects.",
            evidence=[f"config_version={version} found in project.godot"],
            root=root,
        )

# EXEC-GODOT-008: renderer validation
if "GLES2" in project_text or "GLES3" in project_text:
    bad_renderers = [r for r in ("GLES2", "GLES3") if r in project_text]
    _add_execution_finding(
        findings, ctx,
        code="EXEC-GODOT-008",
        severity="warning",
        problem=f"project.godot references obsolete renderer(s): {', '.join(bad_renderers)}. Godot 4.x uses forward_plus, mobile, or gl_compatibility.",
        root_cause="GLES2 and GLES3 were Godot 3.x renderer names. In Godot 4.x they are replaced by forward_plus, mobile, and gl_compatibility.",
        files=[project_file],
        safer_pattern="Use 'gl_compatibility' for mobile Android targets in Godot 4.x instead of GLES2.",
        evidence=bad_renderers,
        root=root,
    )
```

### Verification Steps

```bash
# 1. Verify EXEC-GODOT-007 and EXEC-GODOT-008 checks exist
grep -n "EXEC-GODOT-007\|EXEC-GODOT-008\|config_version\|GLES2.*renderer" \
  skills/scafforge-audit/scripts/audit_execution_surfaces.py

# 2. Test on Glitch repo
python3 skills/scafforge-audit/scripts/audit_execution_surfaces.py \
  --repo /home/pc/projects/Scafforge/livetesting/glitch 2>&1 | grep EXEC-GODOT-00
# Expected: EXEC-GODOT-007 fires (config_version=2), EXEC-GODOT-008 fires (GLES2)
```

### Regression Guard

Add a test fixture with a project.godot containing `config_version=2` and `GLES2`.
Assert EXEC-GODOT-007 and EXEC-GODOT-008 fire.

---

## DEF-008 — EXEC-WARN-001: No Mandatory Command Evidence in Remediation Review Artifacts (P2)

### Summary
Reviewer template allows prose-only review artifacts for remediation tickets.
No audit check enforces command output evidence for remediation reviews.

### Exact Files to Modify

1. `skills/repo-scaffold-factory/assets/project-template/.opencode/agents/__AGENT_PREFIX__-reviewer-code.md`
2. `skills/scafforge-audit/scripts/audit_repo_process.py`

### Changes Required

#### File 1: `__AGENT_PREFIX__-reviewer-code.md`

**Change — Add remediation review evidence requirement:**

In the review artifact generation section, add:
```
For remediation tickets (where the ticket has a finding_source field):
- You MUST include a ## Command Evidence section in your review artifact
- This section MUST contain the literal shell command run and its complete output
- The command must be the same command that originally produced the finding
- Example format:
  ## Command Evidence
  Command: `godot4 --headless --path . --quit 2>&1 | tail -20`
  Output:
  ```
  [actual output here]
  ```
- Prose statements like "the warning is now gone" are not sufficient without command output
- A review artifact for a remediation ticket that lacks ## Command Evidence will be marked
  as insufficient by the audit and may cause the ticket to be reopened
```

#### File 2: `audit_repo_process.py`

**Change — Add remediation evidence check:**

In the function that processes ticket findings (look for where `finding_source` is checked),
add a check that reads the review artifact for remediation tickets and verifies it contains
a `## Command Evidence` section:

```python
def check_remediation_review_evidence(ticket: dict, repo_root: Path, ctx: AuditContext) -> list[str]:
    """Return evidence strings if a remediation ticket's review artifact lacks command evidence."""
    if not ticket.get("finding_source"):
        return []
    review_artifacts = [a for a in ticket.get("artifacts", [])
                       if a.get("stage") == "review" and a.get("trust_state") == "current"]
    if not review_artifacts:
        return []
    latest_review = max(review_artifacts, key=lambda a: a.get("created_at", ""))
    artifact_path = repo_root / latest_review.get("path", "")
    if not artifact_path.exists():
        return [f"Review artifact for remediation ticket {ticket.get('id')} not found at {latest_review.get('path')}."]
    content = artifact_path.read_text(encoding="utf-8", errors="replace")
    if "## Command Evidence" not in content and "command evidence" not in content.lower():
        return [
            f"Remediation ticket {ticket.get('id')} (finding: {ticket.get('finding_source')}) "
            f"review artifact lacks '## Command Evidence' section. "
            f"Prose claims without command output are insufficient for remediation review."
        ]
    return []
```

Add a new finding code `EXEC-REMED-001` that fires when remediation review evidence is missing.

### Verification Steps

```bash
# 1. Verify reviewer template contains Command Evidence requirement
grep -n "Command Evidence\|finding_source\|remediation.*command" \
  "skills/repo-scaffold-factory/assets/project-template/.opencode/agents/__AGENT_PREFIX__-reviewer-code.md"

# 2. Verify audit script has remediation evidence check
grep -n "EXEC-REMED-001\|check_remediation_review_evidence\|Command Evidence" \
  skills/scafforge-audit/scripts/audit_repo_process.py

# 3. Test on Glitch: REMED-002 review artifact lacks command evidence
#    Expected: EXEC-REMED-001 fires for REMED-002
```

### Regression Guard

Add test fixture: a repo with a remediation ticket (finding_source set) and a review artifact
that contains only prose. Assert EXEC-REMED-001 fires. Add second fixture where the review
artifact contains `## Command Evidence` with actual output. Assert EXEC-REMED-001 does not fire.

---

## DEF-009 — EXEC001-TYPE: Python TYPE_CHECKING Stack-Standards Gap (P3)

### Summary
The generated Python+FastAPI stack-standards skill has no guidance for the TYPE_CHECKING
annotation pattern, leading implementer agents to use unquoted annotations.

### Exact Files to Modify

1. `skills/repo-scaffold-factory/assets/project-template/.opencode/skills/stack-standards/SKILL.md`

### Changes Required

**Change — Add TYPE_CHECKING annotation rule to Python+FastAPI section:**

In the Python/FastAPI stack standards section, add:

```markdown
### TYPE_CHECKING Import Pattern

When imports are guarded under `TYPE_CHECKING` for circular import avoidance:

```python
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .service import MyService
```

All return type annotations that reference TYPE_CHECKING-only names MUST use quoted strings:

```python
# CORRECT — string annotation is evaluated lazily, after runtime imports resolve
async def get_my_service(...) -> "MyService":
    ...

# BROKEN — unquoted annotation is evaluated at import time when TYPE_CHECKING is False
async def get_my_service(...) -> MyService:  # NameError at startup
    ...
```

FastAPI evaluates dependency function signatures at import time to build dependency graphs.
Any unquoted TYPE_CHECKING annotation will raise NameError before the app starts.

QA gate: Run `python -c "from src.<package>.main import app"` as a required smoke check
before closing any ticket that adds or modifies FastAPI dependency functions.
```

### Verification Steps

```bash
grep -n "TYPE_CHECKING\|quoted.*annotation\|string.*annotation" \
  "skills/repo-scaffold-factory/assets/project-template/.opencode/skills/stack-standards/SKILL.md"
```

### Regression Guard

Add to Python+FastAPI eval cases: a prompt that asks for a FastAPI dependency function
with a TYPE_CHECKING-guarded service. The `required_patterns` should include the quoted
annotation pattern (`-> "ServiceName":`) and `forbidden_patterns` should include an
unquoted annotation pattern (`-> ServiceName:` without quotes).

# 04 — Prevention Strategy

**Created:** 2026-04-08  
**Scope:** Systemic prevention for each defect class found across three audits

---

## 1. Ticket Split-Scope Routing Failures

### Class of defect
Split-scope tickets using the wrong template for the relationship type, causing
transition_guidance to route against the intended work order.

### Root cause
`ticket_create` applies identical `decision_blockers` text for all split types.
`ticket_lookup` reads that text and routes unconditionally to children.
No schema field records the semantic relationship between parent and child.

### Prevention package changes

**Primary:** Add `split_kind` to the Ticket schema (DEF-001 fix in `02-implementation-plan.md`).
Require `split_kind` on all split-scope `ticket_create` calls.

**Secondary — enforce at ticket generation time:**

All tools and skills that create split-scope tickets (`ticket-pack-builder`, `scaffold-kickoff`
generated backlogs, agent task delegation prompts) must be updated to pass `split_kind`.
The `ticket_create` tool should emit a `warnings: ["split_kind not specified; defaulting to
parallel_fragment — verify this is correct"]` when `split_kind` is absent from a split_scope
creation call.

**Tertiary — pre-activation invariant:**

`ticket_update` rejects `activate: true` for a `sequential_dependent` child whose parent
is not yet done. This is an unmissable safety gate even if the routing guidance is wrong.

**Repair path:**

scafforge-repair should detect the deadlock pattern (parent has split children with no
implementation artifact, children are blocked) and offer a targeted repair: set
`split_kind: "sequential_dependent"` on stuck sequential children and re-run
`ticket_lookup` to get routing unstuck.

**Audit check:**

Add a `ticket_graph` audit check that detects WFLOW-LOOP patterns: a parent and its split
child are both in non-done state but the child's plan says its prerequisites (from the parent)
don't exist. Flag as WFLOW-LOOP-001.

---

## 2. Workflow State Non-Atomic Stage Updates

### Class of defect
Artifact registration and stage advancement are separate operations. If stage advancement
fails or is skipped after artifact registration, the manifest stage field becomes stale
relative to the artifact record.

### Root cause
`artifact_register` updates `ticket.artifacts` but not `ticket.stage`.
`ticket_update` is required as a separate operation to advance the stage.
`ticket_lookup` does not detect when stage and artifact record disagree.

### Prevention package changes

**Primary:** Add stale-stage detection to `ticket_lookup` (DEF-002 fix in `02-implementation-plan.md`).
This is the main recovery gate: when divergence exists, surface it immediately with a
concrete repair action.

**Secondary — consider moving stage advancement into `artifact_register`:**

When registering an artifact for stage X, if the ticket's current stage is earlier than X,
automatically advance `ticket.stage` to X in the manifest write. This makes stage tracking
automatic and atomic.

Pseudo-implementation:
```typescript
// In artifact_register execute():
const STAGE_ADVANCEMENT = {"planning": "planning", "implementation": "implementation", "review": "review", "qa": "qa"}
if (STAGE_ADVANCEMENT[args.stage] && STAGE_ORDER.indexOf(args.stage) > STAGE_ORDER.indexOf(ticket.stage)) {
  ticket.stage = args.stage  // advance stage atomically with artifact registration
}
```

This is a bigger change with more unknowns (backward compatibility, parallel lane effects),
so it should be implemented in a follow-up after the stale-stage detection patch.

**Tertiary — test protocol:**

Every integration test should verify that a ticket's stage in manifest equals the highest
stage for which artifacts are registered, after a complete implementation cycle.

---

## 3. Restart Surface Drift

### Class of defect
Derived restart surfaces (START-HERE.md, context-snapshot.md, latest-handoff.md) disagree
with canonical workflow state.

### Root cause
Sessions that mutate workflow state may not always trigger `handoff_publish` to regenerate
derived surfaces. The repair runner calls `regenerate_restart_surfaces` but sessions that
crash or are incomplete may not.

### Prevention package changes

**Already largely addressed:** The current Scafforge `regenerate_restart_surfaces.py` calls
`handoff_publish.ts` which generates the canonical machine-parseable format. The WFLOW010
finding in GPTTalker was historical (pre-overhaul).

**Remaining gap — session lifecycle regeneration:**

Add a recommendation to the `ticket_update` tool (when advancing via `stage: "closeout"`)
to emit a `handoff_publish` call automatically. Currently, `handoff_publish` must be called
explicitly. Agents that skip it leave surfaces stale.

**Audit gate:**

`scafforge-audit` WFLOW010 already detects surface drift. This audit check is correct and
should be kept. The prevention is that `handoff_publish` is called as part of the stage-gate
enforcer: after every `ticket_update` that reaches `closeout`, the stage-gate-enforcer
plugin should trigger a `handoff_publish` automatically.

**Stage-gate enforcer enhancement:**

In `skills/repo-scaffold-factory/assets/project-template/.opencode/plugins/stage-gate-enforcer.ts`,
add a post-hook for `ticket_update` that triggers `handoff_publish` when the ticket
advances to `closeout`.

---

## 4. Coordinator Role Boundary Violations

### Class of defect
Team-leader writes specialist artifacts directly (coordinator artifact authorship).
Task delegation prompts ask specialists to return content instead of writing it themselves.

### Root cause
Advisory language ("treat as suspect") vs imperative prohibition ("you MUST NOT").
Delegation prompt design that incentivizes content return instead of self-write.

### Prevention package changes

**Primary:** Imperative prohibition in team-leader template (DEF-006 fix in `02-implementation-plan.md`).

**Secondary — delegation prompt standardization:**

All task delegation patterns in agent templates should follow the canonical pattern:
- Correct: "Write the artifact yourself. Return only the registered path and summary."
- Wrong: "Return the full artifact body in your final message."

Add a standard delegation prompt pattern to the team-leader template's delegation section
that ALL agent delegation follows.

**Tertiary — `artifact_write` tool role awareness (future):**

Consider adding an optional `author_role` argument to `artifact_write`. If the team-leader
calls `artifact_write` with `author_role: "coordinator"`, the tool logs a warning. If a
future version enforces this, it becomes a hard gate. This is a future enhancement.

**Audit check:**

`scafforge-audit` could detect coordinator-written artifacts by looking at tool call logs
(if available). In the absence of logs, check artifact paths: if a plan artifact exists but
no planner subagent log is present, emit SESSION005 as a warning.

---

## 5. Missing Godot/Android Execution Surfaces

### Class of defect
Godot Android repos are scaffolded without required export configuration.
Android export prerequisites are not validated early enough in the lifecycle.

### Root cause
No Godot/Android adapter in Scafforge that specifies required scaffold outputs.
EXEC-GODOT-005 fires too late (only after release lane starts).
ticket-pack-builder generates release tickets without prerequisite tracking.

### Prevention package changes (consolidated from DEF-003, DEF-004)

**Scaffold time:**
- `repo-scaffold-factory` emits `export_presets.cfg` template for Godot Android repos
- SETUP-001 accept criteria template for Godot Android includes: verify export_presets.cfg,
  verify export templates directory, verify android_source.zip availability

**Backlog generation:**
- `ticket-pack-builder` gates Android release tickets on `export_presets.cfg` existence
- RELEASE-001 is generated as `sequential_dependent` on ANDROID-001

**Audit time:**
- EXEC-GODOT-005-EARLY fires when Android tickets are active and export_presets.cfg missing
- EXEC-GODOT-006 fires when android_source.zip is absent from export templates

**Repair time:**
- `scafforge-repair` detects and auto-generates `export_presets.cfg` from template

**Future — Godot/Android adapter section in `adapters/manifest.json`:**

```json
{
  "godot-android": {
    "stack_labels": ["Godot 4.x Android", "godot android", "gdscript android"],
    "required_scaffold_outputs": [
      "export_presets.cfg",
      "android/.gitkeep",
      "build/android/.gitkeep"
    ],
    "setup_prerequisites": [
      "Godot export templates installed",
      "Android SDK configured",
      "android_source.zip in export templates"
    ],
    "template_substitutions": {
      "export_presets.cfg": {
        "__PACKAGE_NAME__": "canonical_brief.package_name",
        "__PROJECT_NAME__": "canonical_brief.project_name"
      }
    }
  }
}
```

---

## 6. Audit False Positives (node_modules)

### Class of defect
Import scanner files enumerate node_modules contents, flagging TypeScript packages'
compiled-import references as broken imports.

### Root cause
No exclusion list in the file enumeration phase of the import scanner.

### Prevention package changes

**Primary:** Add `IMPORT_SCAN_EXCLUSIONS` (DEF-005 fix in `02-implementation-plan.md`).

**General principle — scan exclusion scoping:**

Any audit checker that scans file contents should use a standardized exclusion helper.
The same `should_exclude_from_scan` function should be reusable across all audit checkers
that enumerate repo files. Define it in a shared `audit_shared_utils.py` module and import
it in each checker.

```python
# In a new file: skills/scafforge-audit/scripts/audit_shared_utils.py
SCAN_EXCLUSION_DIRS = frozenset([
    "node_modules", ".git", "vendor", "__pycache__",
    ".venv", "venv", ".tox", "dist", "build"
])

def iter_repo_files(root: Path, extensions: tuple[str, ...] | None = None) -> Iterator[Path]:
    """Yield files in root, excluding standard third-party and generated directories."""
    for path in root.rglob("*"):
        if path.is_file():
            if any(part in SCAN_EXCLUSION_DIRS for part in path.relative_to(root).parts):
                continue
            if extensions and path.suffix not in extensions:
                continue
            yield path
```

All audit checkers should use `iter_repo_files` rather than `root.rglob("*")` directly.

---

## 7. Model Reference Format

### Class of defect
Generated agent files may use incorrect model path formats.

### Root cause recommendation

The GPTTalker audit confirmed that all 20 agent files had correct `model: minimax-coding-plan/MiniMax-M2.7` format. No package defect was confirmed.

**Prevention — template validation:**

Add a check in `scripts/validate-skills.sh` (or the smoke test) that validates agent template files in `skills/repo-scaffold-factory/assets/project-template/.opencode/agents/` use the correct `__DEFAULT_MODEL__` placeholder (substituted at scaffold time, not hardcoded).

If any agent template contains a hardcoded model string instead of `__DEFAULT_MODEL__`,
flag it as a drift finding.

---

## 8. Immediately Continuable Greenfield Output Verification

### Class of defect
Generated repos may not be immediately continuable after scaffold.

### Prevention package changes

**Immediate continuability gate in `scaffold-kickoff` SKILL.md:**

The greenfield one-shot generation contract must include a post-generation verification step:
1. `ticket_lookup` returns a valid `next_action_tool` (not null, not "report_blocker")
2. `workflow-state.json` and `manifest.json` are syntactically valid JSON
3. `export_presets.cfg` exists for Godot Android repos
4. Bootstrap status is `ready` OR explicit blockers are documented with operator instructions
5. `START-HERE.md` contains all required machine-parseable fields

This verification should be automated in a post-scaffold script and the result recorded in
`.opencode/meta/bootstrap-provenance.json` under a `continuability_verification` key.

---

## 9. Repair Run Benefits

Every fix in this plan should benefit repair runs, not just greenfield:

| Fix | Benefits Repair |
|---|---|
| DEF-001 split_kind | Repair detects deadlock pattern and offers split_kind fix |
| DEF-002 stale-stage detection | Runs in any session; repair runner checks for stale tickets |
| DEF-003 export_presets.cfg | scafforge-repair auto-generates from template |
| DEF-004 ticket-pack-builder prereqs | Repair remediation mode generates missing ANDROID-EXPORT-SETUP ticket |
| DEF-005 node_modules exclusion | Runs in all audit executions including post-repair audits |
| DEF-006 team-leader prohibition | New agent template distributed to all repaired repos via managed surface replacement |
| DEF-007 Godot version check | Runs in all audit executions |
| DEF-008 remediation evidence gate | Adds EXEC-REMED-001 to repair audit output |
| DEF-009 TYPE_CHECKING guidance | stack-standards skill updated via managed surface replacement |

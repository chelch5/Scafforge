# 05 — Verification Suite

**Created:** 2026-04-08  
**Scope:** Concrete verification steps and sign-off criteria for all 9 defects

---

## How to Use This Document

For each defect, this file defines:
- **Verification step** — a concrete command or check confirming the fix is present
- **Integration scenario** — a real test case with observable expected behavior
- **Sign-off criteria** — what constitutes "this defect class is closed" for greenfield and repair

Run verification steps from the Scafforge repo root: `/home/pc/projects/Scafforge`

---

## DEF-001 — Split-Scope Routing (WFLOW-LOOP-001)

### Verification step

```bash
# 1. Confirm split_kind field exists in Ticket schema
grep -n "split_kind" skills/repo-scaffold-factory/assets/project-template/.opencode/lib/workflow.ts
# Expected: at least 2 hits — schema declaration and openSplitScopeChildren filter

# 2. Confirm ticket_create exposes split_kind arg
grep -n "split_kind" skills/repo-scaffold-factory/assets/project-template/.opencode/tools/ticket_create.ts
# Expected: multiple hits — arg declaration, validation, persistence

# 3. Confirm ticket_lookup routes to children only when appropriate
grep -n "split_kind" skills/repo-scaffold-factory/assets/project-template/.opencode/tools/ticket_lookup.ts
# Expected: at least 1 hit — conditional routing branch

# 4. Confirm no unconditional child routing remains
grep -n "openSplitScopeChildren" skills/repo-scaffold-factory/assets/project-template/.opencode/tools/ticket_lookup.ts
# Expected: only in context of split_kind check, not as standalone unconditional branch
```

### Integration scenario

1. Create a test repo with `scaffold-kickoff` Godot Android profile
2. Observe the generated tickets: there should be a split-scope parent (SCOPE-001) with two children
3. Check that `ticket_create.ts` was called with `split_kind: "sequential_dependent"` for the ANDROID-EXPORT child
4. Call `ticket_lookup` on the parent before any child work is done
5. **Expected:** `transition_guidance` says "Work on ANDROID-EXPORT-SETUP first; RELEASE-001 cannot start until parent scope prerequisites are complete"
6. Call `ticket_lookup` again on the same parent after ANDROID-EXPORT-SETUP reaches `done`
7. **Expected:** `transition_guidance` routes to RELEASE-001

### Sign-off criteria

**Greenfield:** A new Godot Android scaffold produces split-scope tickets with `split_kind` populated.
`ticket_lookup` on a sequential_dependent parent correctly gates until the controlling child is done.
No "loop-detected" audit finding in a fresh scaffold post-deference.

**Repair:** `scafforge-audit` emits WFLOW-LOOP-001 on a repo that has stale split-scope deadlock
(parent and sequential child both stuck, no artifacts). `scafforge-repair` offers a repair and
sets `split_kind` correctly.

---

## DEF-002 — Stale Stage Detection (SESSION006)

### Verification step

```bash
# 1. Confirm stale-stage detection logic exists in ticket_lookup
grep -n "stale_stage\|artifact.*stage.*advance\|stage confidence\|SESSION006" \
  skills/repo-scaffold-factory/assets/project-template/.opencode/tools/ticket_lookup.ts
# Expected: at least 1 hit indicating a cross-check between ticket.stage and artifact records

# 2. Confirm artifact_register does NOT silently advance stage without cross-check
grep -n "ticket\.stage\s*=" \
  skills/repo-scaffold-factory/assets/project-template/.opencode/tools/artifact_register.ts
# If this returns 0 results, stale-stage fix must be in ticket_lookup instead (acceptable)
```

### Integration scenario

1. Create a test manifest where ticket T001 has `stage: "planning"` but has a `review` artifact registered
2. Call `ticket_lookup` on T001
3. **Expected:** Response includes a warning or explicit note: "Stage mismatch detected — manifest shows 'planning' but artifact record shows 'review' artifact exists. Verify and advance stage with ticket_update."
4. Call `ticket_update` to advance stage, then call `ticket_lookup` again
5. **Expected:** Clean routing to `qa` stage

### Sign-off criteria

**Greenfield/Repair:** After a full implementation cycle (plan → impl → review → qa → closeout),
the ticket's stage in manifest equals the highest stage for which an artifact is registered.
No scenario should leave `ticket.stage = "planning"` with a review artifact present without
`ticket_lookup` surfacing it.

---

## DEF-003 — Missing export_presets.cfg Template (EXEC-GODOT-005-SCAFFOLD)

### Verification step

```bash
# 1. Confirm template exists
ls skills/repo-scaffold-factory/assets/project-template/export_presets.cfg
# Expected: file present

# 2. Confirm SCAFFORGE-SUBSTITUTE placeholders are present
grep "SCAFFORGE-SUBSTITUTE\|__PACKAGE_NAME__\|__PROJECT_NAME__" \
  skills/repo-scaffold-factory/assets/project-template/export_presets.cfg
# Expected: at least 2 hits

# 3. Confirm EXEC-GODOT-005 fires early (not just for release lane)
grep -n "release_lane_started_or_done\|android.*active\|GODOT-005" \
  skills/scafforge-audit/scripts/audit_execution_surfaces.py
# Expected: new early trigger condition present; old release_lane_only condition replaced or supplemented
```

### Integration scenario

1. Scaffold a Godot Android repo with `scaffold-kickoff`
2. Inspect generated files
3. **Expected:** `export_presets.cfg` is present in repo root with substituted package name
4. Run `scafforge-audit` on the resulting repo
5. **Expected:** EXEC-GODOT-005 does NOT fire (prerequisites present)

Negative scenario:
1. Delete `export_presets.cfg` from a scaffolded Godot Android repo
2. Run `scafforge-audit` when Android tickets are active (before release lane even started)
3. **Expected:** EXEC-GODOT-005 fires with clear remediation instructions

### Sign-off criteria

**Greenfield:** No Godot Android repo scaffolded by Scafforge is missing `export_presets.cfg`.
**Repair:** `scafforge-repair` detects when `export_presets.cfg` is absent in a Godot Android repo
and auto-generates it from template. Audit stops emitting EXEC-GODOT-005 after repair.

---

## DEF-004 — ticket-pack-builder Android Prereq Gap (WFLOW023)

### Verification step

```bash
# 1. Confirm Android export prereq check exists in skill
grep -n "export_presets\|ANDROID.*EXPORT\|export.*prerequisite\|SETUP-001" \
  skills/ticket-pack-builder/SKILL.md
# Expected: at least 1 hit

# 2. Confirm prereq ticket template or gating logic appears
grep -n "sequential_dependent\|android.*release\|release.*android" \
  skills/ticket-pack-builder/SKILL.md
# Expected: at least 1 hit linking Android export setup to release ticket
```

### Integration scenario

1. Ask `ticket-pack-builder` to generate a Godot Android backlog from scratch
2. Inspect the generated `tickets/manifest.json`
3. **Expected:** An ANDROID-EXPORT-SETUP (or equivalent) ticket is present with status `todo`
4. **Expected:** The first Android release ticket has `depends_on` referencing ANDROID-EXPORT-SETUP
5. Call `ticket_lookup` on the release ticket when ANDROID-EXPORT-SETUP is not yet done
6. **Expected:** `transition_guidance` routes to ANDROID-EXPORT-SETUP first, not to release ticket implementation

### Sign-off criteria

**Greenfield:** All Godot Android backlogs generated by ticket-pack-builder include an
explicit export prerequisites setup ticket that gates Android release tickets.
**Repair:** When `scafforge-repair` is run on a Godot Android repo missing the setup ticket,
it emits a remediation ticket ANDROID-EXPORT-SETUP-REMEDIATION.

---

## DEF-005 — node_modules False Positives (REF-003-FP)

### Verification step

```bash
# 1. Confirm IMPORT_SCAN_EXCLUSIONS or equivalent exists in audit checker
grep -n "node_modules\|SCAN_EXCLUSION\|should_exclude" \
  skills/scafforge-audit/scripts/audit_execution_surfaces.py
# Expected: at least 1 hit — node_modules in an exclusion list or check

# 2. Confirm the exclusion is applied before file scanning
grep -n "def.*iter_\|def.*scan_\|node_modules" \
  skills/scafforge-audit/scripts/audit_execution_surfaces.py | head -20
# Expected: node_modules check is in enumeration function, not in downstream logic
```

### Integration scenario

1. Clone or create a test repo with a `node_modules/` directory containing TypeScript packages
2. Run `scafforge-audit` on the repo
3. **Expected:** REF-003 is NOT emitted for any path under `node_modules/`
4. Introduce a genuine broken import in actual application source (not node_modules)
5. Run audit again
6. **Expected:** REF-003 IS emitted for the genuine broken import

### Sign-off criteria

**Greenfield/Repair:** After the node_modules exclusion patch, no audit run on the three
audited repos (GPTTalker, Spinner, Glitch) produces a REF-003 finding for a path under
`node_modules/`, `.venv/`, or `vendor/`. The fix closes false positives across all stack types.

---

## DEF-006 — Coordinator Role Boundary (SESSION005)

### Verification step

```bash
# 1. Confirm imperative prohibition exists in team-leader template
grep -n "MUST NOT.*artifact_write\|MUST NOT.*write.*artifact\|artifact_write.*coordinator" \
  skills/repo-scaffold-factory/assets/project-template/.opencode/agents/__AGENT_PREFIX__-team-leader.md
# Expected: at least 1 hit with imperative "MUST NOT" language

# 2. Confirm the delegation pattern is explicit (specialist writes, returns path only)
grep -n "return.*path\|register.*path\|artifact.*path.*only\|artifact.*body" \
  skills/repo-scaffold-factory/assets/project-template/.opencode/agents/__AGENT_PREFIX__-team-leader.md
# Expected: at least 1 hit clarifying delegation return contract
```

### Integration scenario

1. In a test session with a team-leader agent, issue a task that requires a plan artifact
2. Observe the team-leader's tool call sequence
3. **Expected:** Team-leader calls `delegate_to_specialist` (or equivalent), NOT `artifact_write`
4. **Expected:** The planner subagent calls `artifact_write` and returns only the artifact path
5. Inspect the written artifact — the author should be the planner, not the team-leader

### Sign-off criteria

**Greenfield:** The generated team-leader template contains imperative prohibition on
`artifact_write` for any stage artifacts. Delegation pattern explicitly states specialists
write their own artifacts.
**Repair:** When the managed repair replaces the team-leader agent, the new version has the
prohibition. Post-repair audit does not emit SESSION005 on any new artifacts.

---

## DEF-007 — Godot config_version Check (PROJ-VER-001)

### Verification step

```bash
# 1. Confirm config_version check exists in audit_godot_execution
grep -n "config_version\|PROJ-VER-001\|godot.*version.*check" \
  skills/scafforge-audit/scripts/audit_execution_surfaces.py
# Expected: at least 1 hit — config_version parse and version gate check

# 2. Confirm deprecated renderer check exists
grep -n "GLES2\|GLES3\|gles2\|deprecated.*renderer\|renderer.*deprecated" \
  skills/scafforge-audit/scripts/audit_execution_surfaces.py
# Expected: at least 1 hit
```

### Integration scenario

1. Run `scafforge-audit` on a repo containing a `project.godot` with `config_version=4` (outdated)
2. **Expected:** PROJ-VER-001 fires with remediation note: "project.godot uses config_version=4; Godot 4.x requires config_version=5"
3. Run `scafforge-audit` on the spinner repo (which has correct `config_version`)
4. **Expected:** PROJ-VER-001 does NOT fire

```bash
# Spot check on the spinner repo:
grep "config_version" /home/pc/projects/spinner/project.godot
# Expected: config_version=5
```

### Sign-off criteria

**Greenfield:** Scafforge-generated Godot repos produce `project.godot` with `config_version=5`.
**Repair:** `scafforge-audit` detects version mismatch on existing repos. After repair, audit
does not emit PROJ-VER-001 on any scaffolded repo.

---

## DEF-008 — Remediation Evidence Gate (EXEC-WARN-001)

### Verification step

```bash
# 1. Confirm reviewer-code template has remediation artifact evidence rule
grep -n "command.*output\|literal.*output\|remediation.*evidence\|EXEC-REMED-001" \
  skills/repo-scaffold-factory/assets/project-template/.opencode/agents/__AGENT_PREFIX__-reviewer-code.md
# Expected: at least 1 hit — rule requiring literal command output in remediation artifacts

# 2. Confirm audit_repo_process has remediation evidence check
grep -n "remediation.*evidence\|EXEC-REMED-001\|remediation.*artifact" \
  skills/scafforge-audit/scripts/audit_repo_process.py
# Expected: at least 1 hit
```

### Integration scenario

1. In a test session, create a remediation artifact that contains only narrative summary text
   (no command output, no file diffs, no literal output blocks)
2. Run `scafforge-audit` on the repo
3. **Expected:** EXEC-REMED-001 fires: "Remediation artifacts found with no literal command output; evidence is insufficient for closeout"
4. Update the remediation artifact to include literal command output
5. Run audit again
6. **Expected:** EXEC-REMED-001 does NOT fire

### Sign-off criteria

**Repair:** `scafforge-audit` detects remediation artifacts that contain only narrative text.
Post-repair reviewer-code agent contains the evidence rule. New remediation artifacts
produced by compliant agents include literal output blocks.

---

## DEF-009 — Python TYPE_CHECKING Annotation Guidance (EXEC001-TYPE)

### Verification step

```bash
# 1. Confirm stack-standards skill includes TYPE_CHECKING section
grep -n "TYPE_CHECKING\|type.*checking\|NameError\|forward.*ref\|quoted.*annotation" \
  skills/*/SKILL.md 2>/dev/null | grep -i "stack-standard\|python-conv"
# Expected: at least 1 hit in a Python standards skill

# Also check generated template agent skills
grep -rn "TYPE_CHECKING\|NameError.*annotation" \
  skills/repo-scaffold-factory/assets/project-template/.opencode/skills/ 2>/dev/null
# Expected: present in Python stack-specific template skill
```

### Integration scenario

1. In a GPTTalker-type Python FastAPI project, inspect agent-generated code for
   cross-module imports inside `if TYPE_CHECKING:` blocks
2. Verify those imports use quoted annotations: `def foo(x: "MyClass")` or `from __future__ import annotations`
3. Check that FastAPI dependency functions that use type hints for injected models do not
   require type imports at runtime when using `if TYPE_CHECKING:` guards

### Sign-off criteria

**Greenfield/Repair:** The Python stack-standards skill or local project skill contains explicit
guidance on `TYPE_CHECKING` usage and forward-reference annotation quoting. Any agent review
step that inspects Python FastAPI code applies this guidance.

---

## Full Suite Sign-Off Checklist

Run these after all 9 fixes are implemented:

```bash
# 1. Structural compliance
./scripts/validate-skills.sh

# 2. Smoke test
python3 scripts/smoke_test_scafforge.py

# 3. Integration test
python3 scripts/integration_test_scafforge.py

# 4. Contract validation
npm run validate:contract

# 5. Grep-based verification (run all 9 DEF verification steps above)

# 6. Re-run audit on each of the three audited repos and confirm:
#    - DEF-001: No WFLOW-LOOP-001 found
#    - DEF-003: No EXEC-GODOT-005 found (export_presets.cfg now present)
#    - DEF-005: No REF-003 false positives from node_modules/
#    - DEF-007: No PROJ-VER-001 on correct repos
```

The defect class is closed for the full suite when:
1. All 9 verification greps return expected results
2. `smoke_test_scafforge.py` passes
3. `integration_test_scafforge.py` passes
4. At least one greenfield Godot Android scaffold produces a repo with:
   - `export_presets.cfg` present
   - `split_kind` on all split-scope tickets
   - No WFLOW-LOOP-001, EXEC-GODOT-005, or REF-003 audit findings

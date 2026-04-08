# 00 — Plan Index: Cross-Repo Audit Implementation Plan

**Created:** 2026-04-08  
**Source audits:** GPTTalker (2026-04-08), Spinner (2026-04-08), Glitch (2026-04-08)  
**Plan author:** GitHub Copilot / Claude Sonnet 4.6  

---

## Total Defect Count

| Priority | Count | Description |
|---|---|---|
| P0 | 1 | System-breaking — permanent deadlock, no recovery path |
| P1 | 3 | Workflow-blocking — prevents ticket lifecycle completion |
| P2 | 4 | Quality/reliability — false positives, role violations, no enforcement |
| P3 | 1 | Advisory — guidance gap, no runtime failure |
| **Total** | **9** | Verified active package defects |

Not-verified or historical: 3 (WFLOW010-GPT, WFLOW008-GPT, WFLOW-LEASE-001)

---

## Defect Register

| ID | Finding Code | Source Repos | Description | Priority | Plan Document |
|---|---|---|---|---|---|
| DEF-001 | WFLOW-LOOP-001 | Glitch, Spinner | Split-scope uses parallel template for sequential dependencies → permanent deadlock | P0 | 02-implementation-plan.md |
| DEF-002 | SESSION006 | Spinner | artifact_register doesn't sync workflow-state stage; ticket_lookup can't detect stage/artifact divergence | P1 | 02-implementation-plan.md |
| DEF-003 | EXEC-GODOT-005-SCAFFOLD | Spinner, Glitch | export_presets.cfg not emitted during greenfield Godot Android scaffold | P1 | 02-implementation-plan.md + 03-export-presets-decision.md |
| DEF-004 | WFLOW023 | Spinner | ticket-pack-builder generates release tickets without prerequisite export setup tracking | P1 | 02-implementation-plan.md |
| DEF-005 | REF-003-FP | Spinner, Glitch, GPTTalker | node_modules not excluded from audit import scanner → false positive REF-003 in all npm repos | P2 | 02-implementation-plan.md |
| DEF-006 | SESSION005 | Glitch | Team-leader template advisory (not imperative) on coordinator artifact_write; delegation prompt asks planner to return content instead of writing it | P2 | 02-implementation-plan.md |
| DEF-007 | PROJ-VER-001 | Glitch | No check for config_version=5 or GLES2 renderer in Godot 4.x repos | P2 | 02-implementation-plan.md |
| DEF-008 | EXEC-WARN-001 | Glitch | No mandatory command output in remediation review artifacts; review can claim PASS without evidence | P2 | 02-implementation-plan.md |
| DEF-009 | EXEC001-TYPE | GPTTalker | No stack-standards guidance for Python TYPE_CHECKING annotation pattern | P3 | 02-implementation-plan.md |

---

## Implementation Sequence

Implement in strict priority order. Each group may be parallelized internally.

### Group 1 — P0: Must fix before any new Godot/Android repos are started
1. **DEF-001** — Split-scope sequential/parallel distinction (`ticket_create.ts`, `ticket_lookup.ts`, `workflow.ts`)

### Group 2 — P1: Should fix before Spinner or Glitch repair runs resume
2. **DEF-002** — Stage/artifact divergence detection in `ticket_lookup.ts` + `artifact_register.ts`
3. **DEF-003** — `export_presets.cfg` greenfield emission for Godot Android scaffold
4. **DEF-004** — `ticket-pack-builder` prerequisite tracking for Android export tickets

### Group 3 — P2: Fix before next round of audits to clean false positives
5. **DEF-005** — `node_modules` exclusion in `audit_execution_surfaces.py`
6. **DEF-006** — Team-leader prompt hardening: imperative artifact_write prohibition + delegation pattern fix
7. **DEF-007** — Godot 4.x `config_version` and renderer validation in audit
8. **DEF-008** — Remediation review evidence gate

### Group 4 — P3: Guidance improvement
9. **DEF-009** — Python TYPE_CHECKING stack-standards entry

---

## Plan Document Map

| File | Contents |
|---|---|
| `00-PLAN-INDEX.md` | This file — master index |
| `01-defect-register.md` | Full defect register with verification evidence |
| `02-implementation-plan.md` | Per-defect implementation instructions (P0→P3) |
| `03-export-presets-decision.md` | Full decision analysis for export_presets.cfg |
| `04-prevention-strategy.md` | Systemic prevention strategy for each defect class |
| `05-verification-suite.md` | Runnable verification checklist post-fix |

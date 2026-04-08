# Active Plans Index

## Scope

This plan suite now covers Scafforge package work only.

Rules for this directory:

- GPTTalker, spinner, and glitch are evidence inputs, not edit targets.
- Corrections from the earlier draft are folded into the active documents below. There is no separate corrections log.
- If a finding is already fixed in current package code, or is no longer strongly evidenced, it is removed instead of being parked as a "future idea".
- If a repo needs source-level work after these package changes land, that work must be surfaced through Scafforge audit and repair flows, not manual repo-local instructions in this directory.

## Evidence Baseline

This rewrite is based on current package code and current repo evidence:

- the previous `active-plans/` corpus was reread end to end and then discarded
- current generated runtime surfaces under `skills/repo-scaffold-factory/assets/project-template/.opencode/`
- current audit code under `skills/scafforge-audit/scripts/`
- current repair code under `skills/scafforge-repair/scripts/`
- current ticket-generation code under `skills/ticket-pack-builder/`
- current intake schema under `skills/spec-pack-normalizer/references/brief-schema.md`
- current greenfield and repair harness coverage in `scripts/smoke_test_scafforge.py`, `scripts/integration_test_scafforge.py`, and `skills/repo-scaffold-factory/scripts/verify_generated_scaffold.py`
- live verification against GPTTalker, spinner, and glitch

## Corrections Folded Into This Rewrite

These items were removed from the active defect set because current package code already covers them, or because current evidence does not justify keeping them in the main package plan bundle:

- `pending_process_verification` clearability already exists in `workflow.ts`, `ticket_update.ts`, and restart-surface rendering.
- machine-parseable restart-surface fields already exist in `handoff_publish.ts`, template `START-HERE.md`, and `audit_restart_surfaces.py`.
- planner artifact authorship is already explicit; the remaining prompt gap is on the coordinator side, not the planner side.
- the old repair/export wording was wrong: current audit detects missing Godot Android export surfaces, but current repair does not yet provision them.
- repo-local remediation playbooks were removed. This suite now defines package behavior only.
- null `active_ticket` handling, Zone.Identifier hygiene, and similar side issues are not in this bundle because they are not the current highest-confidence blockers for the package objective the user asked to plan.

## Active Package Defect Count

| Priority | Count | Meaning |
|---|---:|---|
| P0 | 1 | Lifecycle-breaking defect that can deadlock normal ticket routing |
| P1 | 4 | Package gap that blocks trustworthy repair, completion, or finished-product routing |
| P2 | 5 | Audit, prompt, or validation weakness that produces false positives or untrustworthy closure |
| Total | 10 | Verified active package defects in this plan suite |

### P0

- `WFLOW-LOOP-001` — split-scope sequencing still auto-foregrounds dependent child tickets

### P1

- `WFLOW-STAGE-001` — no deterministic stale-stage recovery path when artifacts are current but canonical stage/state is stale
- `ANDROID-SURFACE-001` — Godot Android export surfaces are detected but not scaffolded and repaired as owned repo-managed surfaces
- `TARGET-PROOF-001` — Godot Android completion still collapses runnable proof and deliverable proof into one debug APK bar
- `PRODUCT-FINISH-001` — intake, backlog, audit, and repair have no explicit finished-product contract for art, audio, style, and placeholder policy

### P2

- `REF-SCAN-001` — reference-integrity scan still walks dependency and build trees
- `EXEC-ENV-001` — broken repo-local Python environments can still fall through to system Python import failures
- `ARTIFACT-OWNERSHIP-001` — coordinator artifact authorship is still under-specified in the visible team-leader contract
- `EXEC-REMED-001` — remediation review still lacks mandatory command-output proof
- `PROJ-VER-001` — Godot 4.x config-version and renderer compatibility are still not audited explicitly

## Delivery Order

1. Fix lifecycle correctness first: split-scope routing and stale-stage recovery.
2. Fix the Android package contract second: repo-managed export surfaces, runnable proof, deliverable proof, and signing boundaries must move together.
3. Add the product-finish contract third: intake, backlog, audit, and repair routing must carry explicit finish requirements instead of silently accepting placeholder output.
4. Tighten audit accuracy and evidence enforcement fourth: dependency-tree exclusions, broken-env classification, coordinator artifact ownership, remediation review proof, and Godot 4 guards.
5. Close the loop in harnesses last: smoke, integration, and greenfield verification must fail on the newly encoded contracts.

## Document Map

| File | Purpose |
|---|---|
| `00-PLAN-INDEX.md` | Scope, priorities, corrections folded into the rewrite, and document map |
| `01-defect-register.md` | Verified active defects only, with current package evidence |
| `02-implementation-plan.md` | Exact package files and behavior changes required to close each active defect |
| `03-android-delivery-contract.md` | Full Godot Android contract for export surfaces, signing boundaries, runnable proof, and deliverable proof |
| `04-prevention-strategy.md` | How to keep this package from drifting back into the same failures |
| `05-verification-suite.md` | Required package-side proof for code, prompts, contracts, and harnesses |
| `06-product-finish-contract.md` | Finished-product contract for visual, audio, content-source, and placeholder policy |
| `07-host-boundaries-and-repair-contract.md` | Boundary between host prerequisites, repo-managed surfaces, repair ownership, and source follow-up |
| `08-cross-stack-generalization.md` | What in this bundle is universal versus Godot-specific |
| `09-acceptance-gates.md` | Final acceptance gates for this plan suite and expected post-fix behavior on the evidence repos |

## Non-Negotiable Outcome

When this bundle is implemented, Scafforge must be able to:

- repair workflow-surface defects without direct edits to subject repos
- scaffold and repair repo-managed Android export surfaces instead of only warning about them
- distinguish runnable proof from packaged deliverable proof for Godot Android repos
- carry explicit finished-product requirements for consumer-facing repos instead of silently treating placeholder or procedural output as final
- route remaining source-level work into canonical tickets and restart surfaces instead of vague commentary

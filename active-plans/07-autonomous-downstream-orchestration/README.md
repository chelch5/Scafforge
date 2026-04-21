# Autonomous Downstream Orchestration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Status:** TODO
**Goal:** Build the orchestration layer that accepts an approved brief, runs the standard Scafforge greenfield flow, drives downstream work through PR-based phases, and resumes safely after repair without breaking the package’s one-shot contract.

**Architecture:** The orchestration layer wraps Scafforge; it does not replace it. An adjacent service should own job intake, state transitions, PR and review automation, pause, retry, and resume controls, and evidence aggregation. Scafforge remains responsible for scaffold generation, repo contract surfaces, audit, repair, and handoff publication.

**Tech Stack / Surfaces:** adjacent orchestration service or repo, Scafforge skills, generated repo templates, GitHub PR and review workflows, package restart and handoff surfaces.
**Depends On:** `06-spec-factory-and-intake-mcp`, `09-sdk-model-router-and-provider-strategy`, `05-completion-validation-matrix`.
**Unblocks:** `10-viewer-control-plane-winui` and parts of the autonomous factory vision.
**Primary Sources:** `_source-material/autonomy/hugeupgrade/ScafforgeAutonomousOrchestrationDRAFTPLAN.md`, `_source-material/autonomy/hugeupgrade/scafforgeautonomousnotes.md`, current package workflow contracts in `AGENTS.md`, `references/one-shot-generation-contract.md`, and generated template plugins/docs.

---

## Problem statement

The current autonomous vision mixes together:

- spec approval
- Scafforge generation
- downstream execution
- review and merge gates
- recovery and resume

Without a clear wrapper contract, autonomy will either dissolve package boundaries or recreate them badly in a second hidden workflow engine.

## Required deliverables

- a state model for orchestration jobs
- a trigger contract from approved brief to scaffold kickoff
- phase-to-PR rules for downstream work
- reviewer and merge-gate rules
- failure routing into audit and repair
- safe resume semantics after repo repair or package improvement

## Per-phase dependency map

- Phase 1: contract design may begin now, but persistence and substrate implementation details are blocked on `09`
- Phase 2: blocked on `06` for approved-brief contract and on `05` for proof semantics
- Phase 3: design may begin now, but concrete phase and proof gating behavior is blocked on `05`
- Phase 4: blocked on `05` because merge gates depend on the validation and proof matrix
- Phase 5: design may begin now, but the package-defect branch must hand off to plan `08`
- Phase 6: fully blocked until `05`, `06`, and `09` are complete and the dry-run fixture contract exists

## Proposed orchestration state model

The service should converge on explicit states such as:

`approved-brief-received -> scaffold-running -> scaffold-verified -> phase-ready -> phase-in-progress -> pr-open -> review-blocked|merge-ready -> merged -> next-phase`

Failure and recovery branches must split, not collapse:

- repo-local path:
  - `blocked -> audit-requested -> repo-repair-pending -> revalidation-pending -> resume-ready`
- package-defect path:
  - `blocked -> audit-requested -> package-change-pending -> downstream-revalidation-pending -> resume-ready`

The key rule is that orchestration state is derived from package truth and review results, not invented independently in the UI.

## Package and adjacent surfaces likely to change during implementation

### Scafforge package surfaces

- `skills/scaffold-kickoff/SKILL.md`
- `skills/repo-scaffold-factory/`
- `skills/ticket-pack-builder/SKILL.md`
- `skills/scafforge-audit/`
- `skills/scafforge-repair/`
- `skills/handoff-brief/assets/templates/START-HERE.template.md`
- `skills/repo-scaffold-factory/assets/project-template/.opencode/plugins/stage-gate-enforcer.ts`
- generated process docs and ticket docs under the project template

### Adjacent orchestration surfaces

- orchestration service or repo
- job queue and state persistence
- GitHub PR and review integration
- worker runners that invoke Scafforge and downstream agents
- event stream for dashboards and operator controls

## Ownership boundaries this plan must preserve

- The spec factory owns idea-to-approved-brief workflow.
- Scafforge owns generation, audit, repair, ticket pack structure, and restart publication.
- The orchestration service owns job progression, phase scheduling, PR automation, and resumption.
- The control plane app is only a client of orchestration truth, not the owner of it.
- The orchestration service is read-only with respect to `tickets/manifest.json` and generated `.opencode/state/workflow-state.json`. If it needs grouping or scheduling metadata, that state must live in the orchestration service, not in the generated repo.

## Scaffold-verified gate rule

`scaffold-verified` is not a soft success label. It must mean the one-shot contract has cleared:

- VERIFY009 bootstrap blocker persistence and routing requirements
- zero blocking VERIFY010 execution-surface failures
- zero blocking VERIFY011 reference-integrity failures

No downstream phase may begin until those gates are satisfied.

## Phase plan

### Phase 1: Freeze the orchestration job contract

- [ ] Treat this phase as contract design only; persistence and substrate implementation details are blocked pending plan `09`.
- [ ] Define the job envelope: approved brief pointer, repo identity, branch strategy, execution mode, model/router policy, and operator permissions.
- [ ] Define the state transitions the orchestration layer is allowed to perform directly versus those it must infer from Scafforge or GitHub outputs.
- [ ] Decide where idempotency keys and retry tokens live so retries do not duplicate repo creation or PR spam.
- [ ] Specify the evidence each state must retain for later audit or operator review.

### Phase 2: Define the greenfield invocation boundary

- [ ] Specify exactly how an approved brief enters the Scafforge greenfield flow.
- [ ] Require `scaffold-verified` to mean VERIFY009 persistence confirmation plus zero blocking VERIFY010 and VERIFY011 failures.
- [ ] Record which generated artifacts the orchestration service must read to continue: tickets, restart surface, workflow state, and any package provenance.
- [ ] Define failure handling when the scaffold step fails before downstream repo execution even begins.

### Phase 3: Define phase-to-PR workflow rules

- [ ] Decide how downstream work is broken into phases and how those phases map to ticket bundles or ticket groups.
- [ ] Require every autonomous phase to end in an explicit PR or reviewable diff rather than a silent merge to main.
- [ ] Define branch naming, reviewer assignment, and evidence attachment rules for those PRs.
- [ ] Specify when a phase may be retried, split, paused, or escalated to a human reviewer.
- [ ] Keep the orchestration layer read-only with respect to canonical generated-repo ticket and workflow state; phase grouping lives only in orchestration-owned state.

### Phase 4: Define review and merge gating

- [ ] Write reviewer rules that cross-check PRs against the original spec, ticket requirements, validation artifacts, and stack-specific expectations.
- [ ] Decide which failures are fix-and-resubmit, which require audit, and which require human approval.
- [ ] Define merge policy for fully autonomous, merge-approval, and strict or human-in-the-loop operating modes.
- [ ] Ensure no PR can merge without the required stage-gate and validation evidence defined by plan `05`.

### Phase 5: Define failure routing and resume semantics

- [ ] Define the trigger matrix for when downstream failure routes into `scafforge-audit` rather than simple task retry.
- [ ] Define the repo-local repair branch and its resume trigger.
- [ ] Define the package-defect branch, where a package-owned finding moves the job into `package-change-pending` and waits for plan `08`’s meta-improvement loop to supply the resume trigger.
- [ ] Specify what must be revalidated before the orchestration service marks a repo `resume-ready`.
- [ ] Prevent the orchestration layer from losing causality when a repo-level fix and a package-level fix interact.

### Phase 6: Dry-run the whole wrapper path

- [ ] This phase is blocked until plans `05`, `06`, and `09` are complete.
- [ ] Define the dry-run fixture and harness contract first: stub approved brief, fake PR events, mock review outcomes, and mock audit outputs.
- [ ] Run a small approved brief through greenfield generation and the first downstream phase.
- [ ] Force at least one PR review rejection and verify the repo does not merge prematurely.
- [ ] Force both a repo-repair and a package-change case and confirm the state model remains truthful.
- [ ] Confirm the wrapper never violates the one-shot Scafforge generation contract by mutating package-owned truth itself.

## Validation and proof requirements

- an approved brief can trigger generation without bypassing Scafforge contracts
- every downstream phase has an explicit PR and review boundary
- failure and resume paths are visible and attributable
- the orchestration layer can be paused, retried, or resumed without corrupting package or repo truth
- package-defect and repo-local-repair branches remain distinguishable throughout the state machine

## Risks and guardrails

- Do not let the orchestration service become a second scaffold engine.
- Do not hide state in the control plane UI or chat transcripts.
- Do not merge phase work directly to main just because the service “thinks” it is safe.
- Preserve a strict distinction between package defects and repo-local bugs.
- Do not let orchestration-owned phase state leak back into canonical generated-repo workflow state.

## Documentation updates required when this plan is implemented

- package references describing how external orchestration calls Scafforge
- generated process docs and restart guidance where PR-phase rules surface in repos
- orchestration service docs in its own repo or workspace
- operator docs for pause, retry, and resume semantics
- `references/authority-adr.md`
- `references/one-shot-generation-contract.md`
- `AGENTS.md`

## Completion criteria

- an approved brief can move through scaffold, PR-based phase execution, review, and resume truthfully
- the orchestration wrapper preserves Scafforge’s authority boundaries
- review and merge gates are explicit and testable
- downstream recovery after audit or repair is part of the design, not an afterthought

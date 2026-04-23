# Meta Improvement Loop Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Status:** DONE
**Goal:** Create the Scafforge self-improvement loop that converts repeated downstream failures into package fixes through a controlled chain: audit -> investigate -> package fix -> review -> revalidate -> downstream repair/resume.

**Architecture:** Package mutation must remain high-trust and evidence-backed. The loop starts with audit evidence, produces a structured investigator report, opens a package change path with normal review, and only then revalidates both Scafforge and the affected downstream repo. Archive mining can feed this loop, but never bypass it.

**Tech Stack / Surfaces:** `skills/scafforge-audit/`, `skills/scafforge-repair/`, package-side investigation/fix roles or equivalent automation surfaces, GitHub issues/PRs, package validation commands, `active-audits/`, orchestration resume hooks.
**Depends On:** `02-downstream-reliability-hardening`, `05-completion-validation-matrix`, and `07-autonomous-downstream-orchestration`.
**Unblocks:** the credible self-improving factory story and long-running archive intelligence work.
**Primary Sources:** `_source-material/autonomy/hugeupgrade/ScafforgeAutonomousOrchestrationDRAFTPLAN.md`, `_source-material/autonomy/hugeupgrade/scafforgeautonomousnotes.md`, current audit/repair implementation, `AGENTS.md` sections on `active-audits/` and package authority.

---

## Problem statement

Right now, repeated downstream failures can be observed, but there is no disciplined path that says:

- when a failure graduates from repo-local bug to package evidence
- what evidence must exist before the package may change
- how a package fix is reviewed and validated
- when the affected downstream repo may resume

Without that, “self-improving” is just a slogan.

## Required deliverables

- a package-level escalation trigger matrix with draft thresholds, not just placeholders
- a structured evidence bundle emitted from audit
- an investigator contract with a root-cause report format and storage location
- a package-fix PR contract and review policy
- a GitHub issue-linkage rule for package-evidence failures that need visible tracking
- a revalidation protocol for both package and downstream repo
- a safe rule for how background archive mining feeds the same loop
- a concrete resume-ready signal that plan `07` can consume
- an archive-indexing strategy for logs, session files, and database exports that stays derived rather than canonical

## Package and adjacent surfaces likely to change during implementation

- `skills/scafforge-audit/SKILL.md`
- `skills/scafforge-audit/references/four-report-templates.md`
- `skills/scafforge-audit/scripts/disposition_bundle.py`
- `skills/scafforge-audit/scripts/run_audit.py`
- `skills/scafforge-audit/scripts/audit_reporting.py`
- `skills/scafforge-repair/SKILL.md`
- `skills/scafforge-repair/scripts/follow_on_tracking.py`
- `skills/scafforge-repair/scripts/run_managed_repair.py`
- `skills/scafforge-repair/scripts/regenerate_restart_surfaces.py`
- restore or create package-side `active-audits/` handling described by `AGENTS.md`
- `skills/skill-flow-manifest.json`
- `AGENTS.md` skill-boundary rules
- GitHub issue/PR workflow notes and conventions

## Core design rule

Package repair must not be confused with repo repair.

- `scafforge-repair` remains the generated-repo repair mechanism.
- The meta loop adds package-level investigation and package-level fix review on top of that.
- The downstream repo only resumes after package revalidation and targeted downstream revalidation have both passed.

## Draft escalation trigger matrix

The first implementation pass should not leave escalation thresholds blank.

Initial working rule:

- auto-escalate candidate package evidence when:
  - the same repair-routed failure family appears across **2 or more distinct repos** within the current active window, or
  - a managed-surface contradiction appears with severity `error`, or
  - a repeated `WFLOW`, `BOOT`, `CYCLE`, or explicitly package-managed `EXEC` family contradicts the current package contract
- keep repo-local `EXEC` and `REF` findings as source follow-up unless evidence shows the package allowed them through systematically
- severity floor for automatic escalation:
  - `error` always eligible
  - `warning` only eligible when repeated across distinct repos or when it contradicts an authoritative package contract

These values are deliberately conservative and may be refined during implementation, but they prevent “decide later” drift.

## Evidence bundle schema decision

This plan should extend the existing disposition bundle and audit-pack outputs rather than inventing a disconnected second artifact family.

Required top-level evidence bundle fields:

- `repo_name`
- `audit_generated_at`
- `diagnosis_kind`
- `triggering_finding_codes`
- `disposition_summary`
- `audit_pack_path`
- `report_paths`
- `restart_surface_refs`
- `workflow_state_ref`
- `bootstrap_or_provenance_refs`
- `candidate_package_surfaces`

The investigator input should be stored under:

- `active-audits/<repo-name>/`

with:

- copied raw audit pack materials kept immutable
- a machine-readable evidence manifest
- investigator and fixer sidecar artifacts

## Investigator and fixer output contract

The investigator output should not be prose-only.

Required outputs:

- markdown report
- machine-readable JSON sidecar

Required investigator fields:

- triggering finding codes
- originating audit pack timestamp
- downstream symptom summary
- package-owned cause hypothesis
- prevented-by analysis
- exact package surfaces to change
- revalidation plan
- no-action-required flag when the issue is already fixed or no package change is needed

If `scafforge-investigator` and `scafforge-package-fixer` are implemented as skills, this plan must also update:

- `skills/skill-flow-manifest.json`
- `AGENTS.md` Skill Boundary Rules

If implementation chooses scripts or another bounded automation surface instead, the plan must document that choice explicitly and explain why skill-manifest registration is not required.

## Resume-ready signal decision

Plan `08` owns the definition of the package-side resume-ready signal that plan `07` consumes.

The orchestration layer should only treat a downstream repo as resume-ready when:

- the package fix PR is merged
- package validators pass
- a fresh downstream audit runs with `--diagnosis-kind post_package_revalidation`
- the resulting revalidation artifact explicitly records `resume_ready: true`

Recommended machine-readable carrier:

- `active-audits/<repo-name>/revalidation/resume-ready.json`

with at minimum:

- `repo_name`
- `package_commit`
- `revalidation_audit_timestamp`
- `resume_ready`
- `remaining_repo_local_work`

## GitHub integration boundary

This plan may define documentation and conventions for GitHub issues/PR linkage, but execution responsibility lives in plan `07`’s orchestration service.

- plan `08` owns the causality chain and what must be linked
- plan `07` owns automation that opens or updates issues and PRs during the live orchestration loop

## active-audits restoration note

`AGENTS.md` already describes an `active-audits/` lifecycle, but the directory is currently absent in this repo. This plan therefore owns:

- restoring or creating the directory
- preserving the “copy evidence, do not edit raw audit files” rule
- standardizing the folder shape for investigator/fixer sidecar artifacts without mutating copied evidence

## Phase plan

### Phase 1: Define the escalation trigger matrix

- [x] Freeze the initial trigger matrix for repo-local vs package-evidence vs auto-escalate cases.
- [x] Record recurrence thresholds, severity thresholds, and contradiction thresholds that trigger escalation.
- [x] Ensure the trigger matrix references concrete failure families and proof artifacts rather than vague intuition.
- [x] Record how the orchestration layer and human operators see that escalation decision.

### Phase 2: Define the evidence bundle contract

- [x] Specify the audit outputs that must be bundled for package investigation: findings, logs, diffs, restart state, validation artifacts, and source repo metadata.
- [x] Extend the current disposition-bundle flow rather than creating a disconnected artifact family unless implementation proves that is impossible.
- [x] Formalize how those bundles are stored in `active-audits/` without editing the raw evidence.
- [x] Add enough provenance to map one downstream failure back to one package defect hypothesis.
- [x] Ensure the evidence bundle is concise enough to review but complete enough to support package fixes.

### Phase 3: Define the investigator role

- [x] Introduce a package-side investigator role or equivalent bounded automation surface that consumes evidence bundles and writes a root-cause report.
- [x] Standardize the report into sections: downstream symptom, package-owned cause, prevented-by analysis, required package changes, and revalidation plan.
- [x] Require the investigator to identify the exact Scafforge surface that needs change: skill instructions, template asset, validation logic, or documentation.
- [x] Require both a markdown report and a machine-readable JSON sidecar stored under `active-audits/<repo-name>/`.
- [x] Ensure the investigator can also conclude `no package change required` when evidence does not support escalation.

### Phase 4: Define the package-fix path

- [x] Introduce a package-side fixer role, skill, or workflow that turns the investigator report into a reviewable PR.
- [x] Require normal package review, validation, and documentation updates for that PR.
- [x] Define when the loop must also open or update a formal GitHub issue to track the package-level failure family and tie it to the evidence bundle plus fixer PR.
- [x] Link the PR back to the evidence bundle and any GitHub issue so the causality chain remains visible.
- [x] Prevent archive-mining outputs or investigator reports from mutating package code directly without that PR path.
- [x] Update `skills/skill-flow-manifest.json` and `AGENTS.md` skill-boundary rules if the new roles are implemented as package skills.

### Phase 5: Define revalidation and downstream resume

- [x] Require package validation after the fix using the canonical package commands and any new regression fixtures tied to the defect family.
- [x] Require a fresh downstream audit using `--diagnosis-kind post_package_revalidation` before the repo resumes.
- [x] Emit the concrete resume-ready signal described above so plan `07` can consume it without inventing its own package-state guess.
- [x] Ensure restart surfaces in both repos reflect the updated truth and do not overclaim success.

### Phase 6: Integrate background archive intelligence safely

- [x] Treat this phase as design-only until plan `07`’s event-stream and orchestration architecture are stable enough to define how archive mining runs.
- [x] Define how archive-mining or historical analysis produces suggestions, not direct package mutations.
- [x] Define how raw logs, session files, and any database-exported run metadata are categorized and indexed for archive analysis without replacing the copied evidence as canonical truth.
- [x] Decide whether archive search uses a derived retrieval or vector index, and keep that index explicitly non-authoritative relative to the raw archived materials.
- [x] Route archive-derived improvement candidates into the same trigger/investigation/fix pipeline.
- [x] Decide when archive findings become tickets versus immediate investigation requests.
- [x] Ensure the background loop can be paused or reviewed by a human without losing the evidence chain.

## Validation and proof requirements

- repeated downstream failures can trigger a structured package-level investigation
- investigator outputs identify concrete package surfaces and required revalidation
- package fixes land through reviewable PRs, not silent automation
- the downstream repo only resumes after package and downstream revalidation both pass
- the loop has regression fixtures and harness coverage rather than prose-only confidence

## Risks and guardrails

- Do not blur `scafforge-repair` and package-side fixing into one tool.
- Do not let archive mining write code or file changes directly.
- Do not escalate every downstream bug into package work; evidence quality matters.
- Do not resume downstream work on “package fix merged” alone; revalidation is mandatory.
- Do not create new package skills without registering them in the manifest and authority docs when they become real skills.

## Documentation updates required when this plan is implemented

- audit and repair docs
- package workflow docs covering investigation/fix roles
- `AGENTS.md` for `active-audits/` and package-improvement loop behavior
- `skills/skill-flow-manifest.json`
- GitHub issue/PR workflow notes where the package loop depends on them

## Completion criteria

- repeated downstream failures can become package work through a disciplined evidence-backed loop
- package fixes are reviewable, attributable, and revalidated
- downstream repos resume only after trustworthy revalidation
- the “self-improving” claim becomes a real process instead of an aspiration

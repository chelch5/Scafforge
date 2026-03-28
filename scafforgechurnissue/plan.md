# Scafforge Churn Remediation Plan

## Executive judgment

This is a Scafforge package-contract failure, not primarily a weak-model judgment failure.

The controlling diagnosis is `scafforgechurnissue/ScafforgeAudits/20260328-135857`, not the earlier repo-local recommendation in `20260328-125650`, and not the later false-clean post-repair verification in `20260328-131434`.

The user theory that audit and repair are "too localized" is directionally right, but it is not the whole problem. The deeper issue is that the managed package still encodes mutually inconsistent notions of:

1. what counts as trusted historical work
2. what state is canonical
3. what the legal next move is
4. what repair has actually completed

Because of that, Scafforge is violating its own competence bar: the generated repo does not always expose one reachable legal next move with one named owner and one blocker path.

## Evidence reviewed

I reviewed the following evidence basis before rewriting this plan:

- `scafforgechurnissue/instructions.md`
- all audit packs in `scafforgechurnissue/ScafforgeAudits/`
- all exported weak-agent sessions in `scafforgechurnissue/GPTTalkerAgentLogs/`
- the raw sampled log `scafforgechurnissue/GPTTalkerAgentLogs/2026-03-28T123330.log`
- the archived repair-gap analysis in `out/scafforge audit archive/GPTTalker Logs and Audits/GPTTalkerChurnlogs/20260327-014404/07-scafforge-repair-gap-analysis.md`
- the relevant Codex rollout logs in `scafforgechurnissue/CodexLogs/25/`, `26/`, `27/`, and `28/`
- the current Scafforge package code in:
  - `skills/repo-scaffold-factory/assets/project-template/.opencode/lib/workflow.ts`
  - `skills/repo-scaffold-factory/assets/project-template/.opencode/tools/ticket_update.ts`
  - `skills/repo-scaffold-factory/assets/project-template/.opencode/plugins/stage-gate-enforcer.ts`
  - `skills/repo-scaffold-factory/assets/project-template/.opencode/tools/handoff_publish.ts`
  - `skills/scafforge-audit/scripts/audit_repo_process.py`
  - `skills/scafforge-repair/scripts/run_managed_repair.py`
  - `skills/scafforge-repair/scripts/apply_repo_process_repair.py`
- this week's commit history from `2026-03-24` onward

## The obvious miss

Scafforge has kept treating this as "restart-surface drift" or "repo-local reconciliation."

The more obvious and more serious defect is simpler:

- when `pending_process_verification` is still `true`
- and `ticket_lookup.process_verification.affected_done_tickets` is `[]`
- the generated tooling does not expose one reachable legal next move

That is the core invariant break.

The weak agent eventually discovered the exact clearing condition in `session4.md:1392-1415`, then hit a package-generated catch-22 when it tried to perform the advertised clear operation in `session4.md:1580-1618`, and finally summarized the blockage explicitly in `session4.md:1903-1913`.

That single invariant failure explains the whole churn pattern:

- the weak agent gets trapped
- the audit misses the real contradiction
- repair republishes mixed truth
- later audits oscillate between "clean" and "package-first"

## Chronology that matters

### 1. March 25 already claimed this class was fixed

On March 25, package work explicitly said it was "adding coverage for the three specific failures we just fixed, namely hidden full-suite failures, pending-process-verification being misreported as clean, and the closed-ticket reverification deadlock" (`scafforgechurnissue/CodexLogs/25/rollout-2026-03-25T02-13-34-019d22c4-c6e2-7da2-8600-fc4f0d4c4589.jsonl:3233-3234`).

The same rollout then claimed:

- audit emits `WFLOW008` and `WFLOW009`
- repair keeps `pending_process_verification` visible
- closed-ticket trust restoration no longer dead-ends
- contract tests passed

See `...019d22c4...jsonl:3332-3335`.

Three days later, the March 28 GPTTalker session reproduced the same contradiction class anyway. That means the problem is not lack of awareness. It is lack of invariant-backed closure.

### 2. March 26 strengthened contract tests, but they still did not encode the live failure

On March 26, Scafforge added stronger contract and smoke assertions around truthful handoff gating and repair reporting, but the author explicitly noted the checks still failed on "real current gaps" in the template bootstrap/smoke surfaces (`scafforgechurnissue/CodexLogs/26/rollout-2026-03-26T16-28-05-019d2af9-7650-7c82-a905-7ad280bdbae3.jsonl:616-619`).

This matters because it shows the package was already in a mode of patching contract tests against discovered gaps, but the tests still did not encode the later March 28 contradiction:

- empty affected set
- flag still pending
- clear path unreachable
- handoff override still allowed

### 3. March 27 already documented that repair was only partial

The archived gap analysis states the repair runner "did part of the job, but not the part that actually unblocked this repo" and lists what it did not do:

- project-specific follow-on regeneration
- stale follow-up ticket reconciliation
- circular dependency cleanup
- source-layer fixes
- advancing to the next real ticket

It says the runner completed only `deterministic-refresh` and explicitly left these stages required-not-run:

- `project-skill-bootstrap`
- `opencode-team-bootstrap`
- `agent-prompt-engineering`
- `ticket-pack-builder`
- `handoff-brief`

See `out/scafforge audit archive/GPTTalker Logs and Audits/GPTTalkerChurnlogs/20260327-014404/07-scafforge-repair-gap-analysis.md`.

This is one of the strongest pieces of evidence in the whole pack: repair is partial by implementation, but often treated as if it had converged the system.

### 4. March 28 session exports show the contradiction evolving, not appearing suddenly

The split-truth pattern is already visible in `session01.md`:

- `pending_process_verification: true`
- `affected_done_tickets` limited to 5 EXEC tickets
- `done_but_not_fully_trusted` still listing 35 suspect tickets

See `session01.md:752-758`, `session01.md:1237-1265`.

By `session2.md`, the weak agent is already working inside this split model:

- canonical process verification shows 5 affected done tickets
- restart surfaces still list 33 suspect tickets
- the session treats restart-surface divergence as stale noise and keeps moving

See `session2.md:1231-1268`.

By `session3.md`, the contradiction gets sharper:

- `pending_process_verification` is still `true`
- `affected_done_tickets` later goes empty
- the session starts oscillating between "clearing condition is met" and "maybe backlog verifier still needs to run on the 34 suspect tickets"

See `session3.md:1374-1455`.

By `session4.md`, the conflict becomes undeniable:

- the agent sees `affected_done_tickets: []`
- correctly infers the clear condition is met
- uses the documented `ticket_update` path
- gets blocked by `missing_ticket_write_lease`
- cannot claim the closed ticket

See `session4.md:1374-1415`, `session4.md:1580-1618`, `session4.md:1903-1913`.

### 5. The audit packs on March 28 show boundary instability

The audit chronology is not just noisy. It shows unstable classification boundaries:

1. `20260328-104330`
   - 4 findings
   - transcript-backed reconciled
   - package-first
2. `20260328-113650`
   - 5 findings
   - post-package revalidation
   - still package-first
3. `20260328-115024`
   - 1 finding
   - says package work landed and repo should now run `scafforge-repair`
4. `20260328-122244`
   - clean
   - post-repair
5. `20260328-122636` and `20260328-123203`
   - clean
   - current-state-only
6. `20260328-125650`
   - deterministic script emitted `0` findings
   - humans reconciled that into a repo-local contradiction finding
   - still `package_work_required_first: false`
7. `20260328-131434`
   - post-repair verification says `finding_count: 0` and `result_state: clean`
   - but the same pack still carries `current_state_clean: false`
8. `20260328-135857`
   - transcript-backed
   - 3 findings
   - `package_work_required_first: true`
   - `repeat_audit_churn: true`

This is the strongest audit-meta evidence that the current approach is unstable.

## What is actually broken

### 1. A workflow-level mutation is routed through a ticket-level lease contract

This is the deepest mechanical defect.

`ticket_update.ts` already knows how to clear `pending_process_verification` safely by checking `ticketsNeedingProcessVerification()` (`ticket_update.ts:122-133`).

But `stage-gate-enforcer.ts` unconditionally requires a target-ticket write lease for every `ticket_update` (`stage-gate-enforcer.ts:84-95`, `305-308`), and the same stage gate forbids claiming closed tickets (`stage-gate-enforcer.ts:126-135`).

So the system advertises a legal clear path and then makes it unreachable on closed repos.

That is not a documentation bug. It is a direct contract contradiction.

### 2. Scafforge is using multiple incompatible truth models for "trust"

The package currently conflates at least three different things:

- `verification_state`
  - a ticket-level historical label
- `pending_process_verification` plus `ticketNeedsProcessVerification()`
  - a workflow-level current-process trust rule
- restart-surface summaries such as `done_but_not_fully_trusted`
  - derived human-facing guidance

`ticketNeedsProcessVerification()` is the richer workflow-level rule (`workflow.ts:941-957`).

But `renderStartHere()` still derives `done_but_not_fully_trusted` from raw `verification_state !== trusted/reverified` (`workflow.ts:1054-1100`, especially `1057`, `1096`, `1100`).

That is a category error.

It means the package can simultaneously claim:

- no affected done tickets remain
- pending process verification is still true
- 33 tickets are still not fully trusted
- all tickets are complete and the system is clean

No weak model can reason reliably through that without eventually picking the wrong truth source.

### 3. Handoff publication is still allowed to outrun canonical state

`validateHandoffNextAction()` only blocks narrow claim families:

- dependency-readiness claims
- "single cause" claims such as "not a code defect"

See `workflow.ts:657-682`.

It does not reject "all tickets complete and verified" or "system is in a clean state" while `pending_process_verification` remains true.

Then `handoff_publish.ts` accepts the override and republishes it into restart surfaces (`handoff_publish.ts:30-40`).

So Scafforge is allowing freeform prose to publish a state stronger than canonical truth.

That violates the generated-repo truth hierarchy described in `AGENTS.md`.

### 4. Audit still catches field drift better than contradiction cycles

The current audit script is too literal in the wrong places.

`audit_active_process_verification()` exits early if the affected set is empty (`audit_repo_process.py:1283-1298`). That means it misses the exact scenario where:

- pending flag is still true
- legal clear condition is satisfied
- tooling cannot actually clear it

`audit_restart_surface_drift()` compares parsed surface fields to expected values (`audit_repo_process.py:2598-2719`), but it does not reason about the higher-order contradiction where explicit handoff prose claims a cleaner state than canonical truth supports.

So the script can emit `0 findings` even though the operator is trapped inside a package-generated contradiction. That is exactly what happened before `20260328-125650` was manually reconciled, and again before `20260328-135857` overruled the false-clean interpretation.

### 5. Repair is partial by implementation but broader by narrative

`run_managed_repair.py` very clearly behaves like:

1. deterministic managed-surface refresh
2. verification
3. marking downstream stages as required-not-run

See:

- `derive_required_follow_on_stages()` in `run_managed_repair.py:104-142`
- `summarize_verification()` in `run_managed_repair.py:168-204`
- main flow in `run_managed_repair.py:246-320`

`apply_repo_process_repair.py` also regenerates restart surfaces using the same broad `suspect_done` logic (`apply_repo_process_repair.py:323-363`).

So there are two problems at once:

- repair does not fully converge the repo on its own
- its regenerated restart surfaces can still re-expose the same wrong trust summary

That is why deterministic refresh can repeatedly restore a flawed contract instead of eliminating it.

### 6. Package hardening is still patch accumulation, not invariant control

This week's commit history is a sequence of hardening patches:

- `903c22d` `Fix transcript-aware audit and workflow deadlocks`
- `e2af6ae` `Fix workflow restart surface drift`
- `805915d` `Refresh Scafforge workflow contract from GPTTalker diagnosis`
- `058bb1a` `Harden workflow contract and audit repair handling`
- `361ca42` `Harden audit repair loop and reconciliation contract`
- `ad9f3f0` `Route stale WFLOW024 revalidation to repair`

That is a lot of motion for the same family of failures to remain live three days later.

The pattern is clear:

- discover symptom
- patch local surface
- add or update finding/report wording
- still do not encode the full end-to-end contradiction as an executable regression

## What previous cycles got wrong

### Wrong turn 1: `20260328-125650` mis-scoped the problem as repo-local

That pack explicitly rejected the script's `0 findings`, which was good, but then still concluded:

- no package work required first
- do repo-local reconciliation
- if affected set empty, clear the flag and regenerate restart surfaces

See `scafforgechurnissue/ScafforgeAudits/20260328-125650/01-initial-codebase-review.md` and `04-live-repo-repair-plan.md`.

What it missed:

- the package still allowed contradictory handoff publication
- the restart renderer still used the wrong trust signal
- the clear path was still blocked behind closed-ticket lease enforcement

That pack diagnosed the visible contradiction, not the package behaviors that recreate it.

### Wrong turn 2: `20260328-131434` accepted a false-clean state

This is the clearest single proof that current audit and repair closeout semantics are broken.

The pack says:

- `finding_count: 0`
- `result_state: clean`
- `recommended_next_step: done`

But its own repair report says:

- `pending_process_verification` remains truthfully visible
- `current_state_clean` remains `false`

See:

- `scafforgechurnissue/ScafforgeAudits/20260328-131434/manifest.json`
- `scafforgechurnissue/ScafforgeAudits/20260328-131434/05-repair-execution-report.md`

That should be impossible.

If a pack can be both "clean" and "current_state_clean: false," then the diagnosis contract is not fail-closed.

### Wrong turn 3: earlier package work treated restart-surface truth drift and closed-ticket deadlocks as separate fixes

The March 25 log says the package had just fixed:

- clean-state misreporting
- closed-ticket reverification deadlock

See `scafforgechurnissue/CodexLogs/25/rollout-2026-03-25T02-13-34-019d22c4-c6e2-7da2-8600-fc4f0d4c4589.jsonl:3233-3335`.

The March 28 evidence proves they are not separate in practice. They are two manifestations of the same underlying split:

- one mutation path is impossible
- one publication path is too permissive
- one summary path is derived from the wrong signal

Fixing only one of those at a time just moves the contradiction around.

## User-level diagnosis by level

### Level 1: GPTTalker audit failure

The subject-repo audit is missing the real blocker because it still prioritizes:

- field drift
- current-state snapshots
- narrow tool-level routing hints

over:

- semantic contradictions
- unreachable legal next actions
- transcript-backed causal replay

That is why a weaker model can be honestly stuck while the raw audit still says "0 findings."

### Level 2: Scafforge audit meta failure

Scafforge's own diagnosis loop does not maintain stable precedence rules between:

- current-state-only clean packs
- transcript-backed contradiction evidence
- post-repair verification
- package-first versus repo-local classification

The result is audit churn:

- one pack says package-first
- the next says repo-local
- a later pack says clean
- the final reconciled pack says package-first again

That means the audit method is not reliably judging its own prior failures.

### Level 3: failure at fixing Scafforge

Scafforge has repeatedly repaired the visible layer of the problem without fixing the underlying state model.

The recurring miss is not "one more missing rule." It is that the package still lacks a small, enforced set of invariants spanning:

- ticket tools
- workflow state
- restart rendering
- handoff publication
- audit detection
- repair closeout

Until those are unified, more hardening will keep landing as disconnected patches.

## Non-negotiable invariants

These invariants should govern the next implementation pass. If a proposed fix does not strengthen one of these, it is probably too local.

1. A workflow-level mutation must not require an impossible ticket-level precondition.
2. Derived restart surfaces must be pure projections of canonical state, not stronger interpretations of it.
3. Freeform handoff prose must not be able to claim a cleaner state than canonical workflow state supports.
4. The restart trust summary must be computed from the same helper used by `ticket_lookup.process_verification`.
5. A post-repair verification pack cannot be `clean` unless `current_state_clean` is also `true`.
6. Transcript-backed contradiction recurrence must outrank raw `0 findings` script output.
7. A public `repair` flow must either actually orchestrate all required follow-on work or present itself as partial refresh, not convergence.
8. The generated repo must always expose one reachable legal next move.

## Recommended implementation program

### Phase 0: freeze the diagnosis basis

Instructions:

1. Treat `scafforgechurnissue/ScafforgeAudits/20260328-135857` as the controlling basis for this failure family.
2. Stop treating `20260328-131434` as successful proof of convergence.
3. Do not run more ordinary subject-repo audit/repair churn from the current package version.

Reasoning:

- `20260328-135857` is the first pack that correctly unifies transcript chronology, current state, and managed package code.
- It explicitly sets `package_work_required_first: true` and `repeat_audit_churn: true`.

### Phase 1: encode the failing invariants before more package edits

Instructions:

1. Add regression fixtures first, before modifying runtime behavior.
2. Encode at least these fixtures in `scripts/validate_scafforge_contract.py` and `scripts/smoke_test_scafforge.py`:
   - closed repo, `pending_process_verification: true`, affected set empty, clear path must still be reachable
   - explicit handoff clean-state override while canonical pending state remains true
   - many `verification_state: suspect` tickets with current backlog-verification artifacts; restart surfaces must not still report them as process-untrusted
   - post-repair verification cannot report `clean` when `current_state_clean` is false
   - transcript-backed contradiction cycle must not be demoted by a later raw `0 findings` pass
3. Replay the exact March 28 session4 shape rather than creating only abstract unit tests.

Reasoning:

- March 25 already thought this class was covered.
- That means future fixes must be protected by scenario-level regression, not just local assertions.

### Phase 2: separate workflow-state mutation from ticket-state mutation

Files:

- `skills/repo-scaffold-factory/assets/project-template/.opencode/tools/ticket_update.ts`
- `skills/repo-scaffold-factory/assets/project-template/.opencode/plugins/stage-gate-enforcer.ts`

Instructions:

1. Introduce a dedicated workflow-level mutation path for `pending_process_verification`, or add a narrow, explicit carve-out inside `ticket_update` plus stage gate for workflow-only mutations.
2. The carve-out must only apply when:
   - no ticket lifecycle field is changing
   - the target mutation is workflow-only
   - canonical `ticketsNeedingProcessVerification()` is empty
3. Do not require reopening or claiming a closed ticket just to clear a top-level workflow flag.
4. Audit all other completed-ticket follow-up paths for the same category error:
   - `ticket_reverify`
   - `ticket_create(post_completion_issue|process_verification)`
   - `issue_intake`
   - `ticket_reconcile`

Reasoning:

- Right now the package is routing a workflow-state transition through a ticket-lease contract that cannot be satisfied in exactly the state where the transition becomes legal.

### Phase 3: build one canonical process-verification summary helper

Files:

- `skills/repo-scaffold-factory/assets/project-template/.opencode/lib/workflow.ts`
- `.../.opencode/tools/ticket_lookup.ts`
- `.../.opencode/tools/context_snapshot.ts`
- `.../.opencode/tools/handoff_publish.ts`

Instructions:

1. Create one helper that returns, from one place:
   - whether process verification is pending
   - which done tickets are currently affected
   - whether the flag is legally clearable now
   - what restart surfaces should say about trust exposure
   - what the next legal move is
2. Make the following consume that same helper:
   - `ticket_lookup.process_verification`
   - `renderStartHere()`
   - context snapshot rendering
   - latest handoff rendering
   - handoff validation logic
   - audit expected-state calculations
3. Stop using raw `verification_state` as the primary driver of process-trust guidance.

Reasoning:

- `verification_state` and process-verification trust are not the same concept.
- Until every surface reads the same helper, restart-state contradictions will keep reappearing.

### Phase 4: make handoff publication fail closed

Files:

- `skills/repo-scaffold-factory/assets/project-template/.opencode/lib/workflow.ts`
- `skills/repo-scaffold-factory/assets/project-template/.opencode/tools/handoff_publish.ts`

Instructions:

1. Expand `validateHandoffNextAction()` so it rejects any explicit override that claims:
   - clean state
   - all work complete
   - all tickets verified
   - ready for normal operations
   - or any equivalent stronger readiness claim
   when canonical workflow state does not support that claim
2. Prefer structured next-action rendering from canonical state over freeform override text.
3. If freeform override remains allowed, limit it to explanatory detail that cannot weaken or strengthen the canonical state classification.

Reasoning:

- `handoff_publish` should be a publication tool, not a way for a model to narrate around blockers.

### Phase 5: upgrade audit from drift detection to contradiction-cycle detection

Files:

- `skills/scafforge-audit/scripts/audit_repo_process.py`
- `skills/scafforge-audit/SKILL.md`

Instructions:

1. Add an explicit finding for the session4 contradiction class:
   - `pending_process_verification == true`
   - `affected_done_tickets == []`
   - clear path unreachable or not exposed
2. Add a semantic publication finding for:
   - restart surfaces or handoff prose claiming clean or complete while canonical pending state remains
3. Change transcript-backed diagnosis flow so that, when supporting logs are supplied, chronology reconstruction happens before current-state-only reconciliation.
4. Make repeated same-process-version contradiction cycles escalate to package-first findings automatically.
5. Never allow a later raw `0 findings` pack to overrule a stronger transcript-backed contradiction basis unless the exact causal path has been replayed and eliminated.

Reasoning:

- The current script is too literal in the wrong direction.
- It sees fields, but not the contradiction created by the interaction of fields, tools, and published prose.

### Phase 6: make repair either convergent or explicitly partial

Files:

- `skills/scafforge-repair/scripts/run_managed_repair.py`
- `skills/scafforge-repair/scripts/apply_repo_process_repair.py`
- `skills/scafforge-repair/SKILL.md`
- `skills/scaffold-kickoff/SKILL.md`

Instructions:

1. Choose one of these two paths explicitly:
   - Preferred: make `scafforge-repair` actually orchestrate required follow-on stages in one public flow.
   - Fallback: split the deterministic managed-surface refresh into a differently named public action and stop calling it end-to-end repair.
2. If keeping the current public name, the runner should not exit with a "clean" or near-clean narrative after only deterministic refresh plus required-not-run follow-ons.
3. Deterministic refresh must not replace scaffold-managed `.opencode/skills/` and related project-specific surfaces unless the same public flow also restores or regenerates them.
4. Repair closeout must align exactly with:
   - `verification_passed`
   - `current_state_clean`
   - `causal_regression_verified`
   - remaining required stages

Reasoning:

- Right now repair emits truthful fragments, but the public story still invites operators to think the repo is largely repaired when it may only be refreshed.

### Phase 7: tighten the package's conceptual model, not just its mechanics

Files:

- `AGENTS.md`
- `skills/scafforge-audit/SKILL.md`
- `skills/scafforge-repair/SKILL.md`
- `skills/repo-scaffold-factory/assets/project-template/docs/process/workflow.md`

Instructions:

1. Clarify in package docs that these are distinct concepts:
   - historical verification label
   - current process trust
   - repair follow-on convergence
   - restart-surface publication
2. State explicitly that a weaker model being honestly unable to proceed counts as package failure, not just repo drift.
3. Document the precedence order:
   - canonical state
   - shared truth helper
   - derived restart surfaces
   - optional explanatory prose
4. Document the audit precedence order:
   - transcript-backed causal evidence
   - current-state reconciliation
   - raw script zero-finding outputs

Reasoning:

- The package is currently missing not just code-level fixes, but a stable conceptual contract for how these states relate.

### Phase 8: run one and only one revalidation on GPTTalker after package fixes

Instructions:

1. After package fixes land, run exactly one fresh `post_package_revalidation` audit on GPTTalker.
2. If that pack is clean on the package-first issues, run one repair from that fresh pack.
3. Then replay the weak-agent resume scenario.
4. Only after those steps should any remaining issue be classified as repo-local.

Reasoning:

- Repeated subject-repo audit/repair churn against a still-flawed package is what created this investigation in the first place.

## File clusters that should be treated as one unit

Do not patch these in isolation.

Treat this as a single repair cluster:

1. `skills/repo-scaffold-factory/assets/project-template/.opencode/lib/workflow.ts`
2. `skills/repo-scaffold-factory/assets/project-template/.opencode/tools/ticket_lookup.ts`
3. `skills/repo-scaffold-factory/assets/project-template/.opencode/tools/ticket_update.ts`
4. `skills/repo-scaffold-factory/assets/project-template/.opencode/tools/handoff_publish.ts`
5. `skills/repo-scaffold-factory/assets/project-template/.opencode/plugins/stage-gate-enforcer.ts`
6. `skills/scafforge-audit/scripts/audit_repo_process.py`
7. `skills/scafforge-repair/scripts/run_managed_repair.py`
8. `skills/scafforge-repair/scripts/apply_repo_process_repair.py`
9. `scripts/validate_scafforge_contract.py`
10. `scripts/smoke_test_scafforge.py`

If only one or two of these move, the contradiction is likely to reappear in a different surface.

## What not to do next

1. Do not run another ordinary `scafforge-repair` against GPTTalker before package work lands.
2. Do not add more restart-surface wording patches without first unifying the underlying truth helper.
3. Do not keep using raw `verification_state` as a proxy for current process trust.
4. Do not let a post-repair pack say `clean` while `current_state_clean` is false.
5. Do not treat transcript-backed weak-agent blockage as secondary evidence behind raw script output.
6. Do not continue layering heuristics onto `validateHandoffNextAction()` unless they are tied back to canonical-state comparison.

## Revalidation and acceptance criteria

Scafforge should not be considered fixed until all of these are true:

1. A closed repo with `affected_done_tickets == []` can clear `pending_process_verification` through one reachable legal path.
2. `ticket_lookup`, `START-HERE.md`, `.opencode/state/context-snapshot.md`, and `.opencode/state/latest-handoff.md` all derive trust exposure from the same helper.
3. `handoff_publish(next_action=\"All tickets complete and verified. System is in a clean state.\")` is rejected whenever canonical state does not support it.
4. The raw audit script reports the session4 contradiction without human override.
5. Post-repair verification cannot produce `result_state: clean` while `current_state_clean` is false.
6. The public repair flow either runs the required follow-on stages or exits with an explicitly partial/non-converged contract.
7. GPTTalker passes one fresh post-package revalidation audit and one repair cycle without reproducing the same contradiction.
8. A weak-model resume from generated restart surfaces reaches one legal next move without needing human reinterpretation.

## Final position

The failure here is not that Scafforge needs "more rules."

The failure is that Scafforge has been enforcing rules from different state models at the same time:

- one model for mutation rights
- one model for trust
- one model for restart summaries
- one model for audit detection
- one model for repair closeout

That is why the system keeps feeling like it is being "hardened" while still getting weaker in practice.

The next fix cycle should be judged by one question:

Does the package now make the truthful next move mechanically reachable and consistently visible across tools, restart surfaces, audit, and repair?

If the answer is not unambiguously yes, the package is not fixed.

# START HERE

<!-- SCAFFORGE:START_HERE_BLOCK START -->
## What This Repo Is

Glitch

## Current State

The repo is operating under the managed OpenCode workflow. Use the canonical state files below instead of memory or raw ticket prose.

## Read In This Order

1. README.md
2. AGENTS.md
3. docs/AGENT-DELEGATION.md
4. docs/spec/CANONICAL-BRIEF.md
5. docs/process/workflow.md
6. tickets/manifest.json
7. tickets/BOARD.md

## Current Or Next Ticket

- ID: ANDROID-001
- Title: Create Android export surfaces
- Wave: 21
- Lane: android-export
- Stage: planning
- Status: todo
- Resolution: open
- Verification: suspect

## Dependency Status

- current_ticket_done: no
- dependent_tickets_waiting_on_current: RELEASE-001
- split_child_tickets: RELEASE-001

## Generation Status

- handoff_status: repair follow-up required
- process_version: 7
- parallel_mode: sequential
- pending_process_verification: true
- repair_follow_on_outcome: managed_blocked
- repair_follow_on_required: true
- repair_follow_on_next_stage: none
- repair_follow_on_verification_passed: false
- repair_follow_on_updated_at: 2026-04-02T14:46:00Z
- pivot_in_progress: false
- pivot_class: none
- pivot_changed_surfaces: none
- pivot_pending_stages: none
- pivot_completed_stages: none
- pivot_pending_ticket_lineage_actions: none
- pivot_completed_ticket_lineage_actions: none
- post_pivot_verification_passed: false
- bootstrap_status: ready
- bootstrap_proof: .opencode/state/artifacts/history/setup-001/bootstrap/2026-04-01T19-46-00-274Z-environment-bootstrap.md
- bootstrap_blockers: none

## Post-Generation Audit Status

- audit_or_repair_follow_up: follow-up required
- reopened_tickets: none
- done_but_not_fully_trusted: SETUP-001, SYSTEM-001, CORE-001
- pending_reverification: none
- repair_follow_on_blockers: Post-repair verification still reports managed workflow or environment findings; handoff must remain blocked until they are resolved.
- pivot_pending_stages: none
- pivot_pending_ticket_lineage_actions: none

## Code Quality Status

- last_build_result: fail @ 2026-04-02T10:26:44.234Z
- last_test_run_result: unknown @ 2026-04-01T21:23:54.304Z
- open_remediation_tickets: 6
- known_reference_integrity_issues: 1

## Known Risks

- Repair follow-on remains incomplete: Post-repair verification still reports managed workflow or environment findings; handoff must remain blocked until they are resolved.
- Historical completion should not be treated as fully trusted until pending process verification or explicit reverification is cleared.
- Some done tickets are not fully trusted yet: SETUP-001, SYSTEM-001, CORE-001.
- ANDROID-001 is an open split parent; child ticket RELEASE-001 remain the active foreground work.
- Downstream tickets RELEASE-001 remain formally blocked until ANDROID-001 reaches done.

## Next Action

Post-repair verification still reports managed workflow or environment findings; handoff must remain blocked until they are resolved.
<!-- SCAFFORGE:START_HERE_BLOCK END -->

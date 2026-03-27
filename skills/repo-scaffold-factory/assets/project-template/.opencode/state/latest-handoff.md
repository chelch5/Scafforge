# START HERE

<!-- SCAFFORGE:START_HERE_BLOCK START -->
## What This Repo Is

__PROJECT_NAME__

## Current State

The repo is operating with a ticketed OpenCode workflow that separates historical completion from current trust and defaults to a single-lane-first execution posture.

## Read In This Order

1. README.md
2. AGENTS.md
3. docs/spec/CANONICAL-BRIEF.md
4. docs/process/workflow.md
5. tickets/manifest.json
6. tickets/BOARD.md

## Current Or Next Ticket

- ID: SETUP-001
- Title: Bootstrap environment and confirm scaffold readiness
- Wave: 0
- Lane: repo-foundation
- Stage: planning
- Status: todo
- Resolution state: open
- Verification state: suspect
- Parallel safe: no

## Generation Status

- handoff_status: bootstrap recovery required
- process_version: 5
- parallel_mode: sequential
- pending_process_verification: false
- bootstrap_status: missing
- bootstrap_proof: None
- process_changed_at: Not yet recorded.
- process_note: No recorded process change summary.
- process_state: No pending process-change verification.

## Post-Generation Audit Status

- audit_or_repair_follow_up: none recorded
- reopened_tickets: none
- done_but_not_fully_trusted: none
- pending_reverification: none

## Known Risks

- Validation can fail for environment reasons until bootstrap proof exists.
- Historical completion should not be treated as current trust once defects or process drift are discovered.

## Next Action

Replace the canonical brief placeholders, run `environment_bootstrap` through `/bootstrap-check` or the Wave 0 setup lane, then rerun `/resume` or `/kickoff` after bootstrap proof exists.
<!-- SCAFFORGE:START_HERE_BLOCK END -->

# ANDROID-001: Create Android export surfaces

## Summary

Create and validate the repo-local Android export surfaces for this Godot Android target. This includes an Android preset in `export_presets.cfg`, non-placeholder repo-local `android/` support surfaces, and a recorded canonical export command for downstream release work.

## Wave

21

## Lane

android-export

## Parallel Safety

- parallel_safe: false
- overlap_risk: medium

## Stage

planning

## Status

todo

## Trust

- resolution_state: open
- verification_state: suspect
- finding_source: WFLOW025
- source_ticket_id: REMED-002
- source_mode: split_scope

## Depends On

None

## Follow-up Tickets

- RELEASE-001

## Decision Blockers

- Split scope delegated to follow-up ticket RELEASE-001. Keep the parent open and non-foreground until the child work lands.

## Acceptance Criteria

- [ ] `export_presets.cfg` exists and defines an Android export preset.
- [ ] The repo-local `android/` support surfaces exist and are non-placeholder.
- [ ] The canonical Android export command is recorded in this ticket and the repo-local skill pack.

## Artifacts

- plan: .opencode/state/artifacts/history/android-001/planning/2026-04-02T15-00-22-444Z-plan.md (planning) - Planning artifact for ANDROID-001: Creates export_presets.cfg, repo-local android/ surfaces, and canonical export command. Raises explicit godot-lib.aar availability blocker before QA can complete.

## Notes

Generated from audit remediation recommendations.


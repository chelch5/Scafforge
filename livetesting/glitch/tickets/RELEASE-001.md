# RELEASE-001: Build Android debug APK

## Summary

Produce and validate the canonical debug APK for this Android target at `build/android/glitch-debug.apk` using the repo's resolved Godot binary and Android export pipeline.

## Wave

24

## Lane

release-readiness

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
- source_ticket_id: ANDROID-001
- source_mode: split_scope

## Depends On

ANDROID-001

## Follow-up Tickets

None

## Decision Blockers

None

## Acceptance Criteria

- [ ] `godot --headless --path . --export-debug Android build/android/glitch-debug.apk` succeeds or the exact resolved Godot binary equivalent is recorded with the same arguments.
- [ ] The APK exists at `build/android/glitch-debug.apk`.
- [ ] `unzip -l build/android/glitch-debug.apk` shows Android manifest and classes/resources content.

## Artifacts

- None yet

## Notes

Generated from audit remediation recommendations.


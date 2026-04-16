# Codex Plan 1604

## Goal

Close every Scafforge package issue that is still live after:

1. the fresh downstream investigations for `womanvshorseVA`, `womanvshorseVB`, `womanvshorseVC`, and `womanvshorseVD`
2. the independent PR review on PR #22
3. the current-head PR adjudication posted in `#issuecomment-4262705139`

Completion scope is still 100%: when this plan is done, no known valid package issue from those evidence sources remains open, and the downstream repos can be re-audited or repaired through Scafforge without manual source edits.

## Evidence Base

### Downstream evidence

- `womanvshorseVD`
  - `/home/rowan/womanvshorseVD/log3.md`
  - `/home/rowan/womanvshorseVD/javaandroidlog1.md`
  - `/home/rowan/womanvshorseVD/diagnosis/20260416-184215/manifest.json`
- `womanvshorseVA`
  - `/home/rowan/womanvshorseVA/wvhvalog1.md`
  - `/home/rowan/womanvshorseVA/.opencode/state/artifacts/history/finish-validate-001/smoke-test/2026-04-16T13-25-37-427Z-smoke-test.md`
  - `/home/rowan/womanvshorseVA/diagnosis/20260416-184348/manifest.json`
- `womanvshorseVC`
  - `/home/rowan/womanvshorseVC/wvhvclogblender1.md`
  - `/home/rowan/womanvshorseVC/blenderissue.md`
  - `/home/rowan/womanvshorseVC/diagnosis/20260416-184444/manifest.json`
- `womanvshorseVB`
  - direct product review findings from:
    - `scripts/wave_spawner.gd`
    - `scenes/player/player.gd`
    - `scripts/autoloads/game_manager.gd`
    - `scenes/enemies/horse_base.gd`
    - `scenes/ui/hud.gd`

### Package evidence

- PR adjudication:
  - `#issuecomment-4262644485`
  - `#issuecomment-4262705139`
- Audit routing / prevention:
  - `skills/scafforge-audit/scripts/disposition_bundle.py`
  - `skills/scafforge-audit/scripts/audit_reporting.py`
- Repair publish safety:
  - `skills/scafforge-repair/scripts/run_managed_repair.py`
- Godot completion-proof surfaces:
  - `skills/repo-scaffold-factory/assets/project-template/.opencode/tools/smoke_test.ts`
  - `skills/scafforge-audit/scripts/target_completion.py`
  - `skills/scafforge-audit/scripts/audit_execution_surfaces.py`
  - generated prompt/runtime guidance under `skills/repo-scaffold-factory/assets/project-template/.opencode/`
- Branch-only merge-surface issues:
  - `smoke-test`
  - `active-plans/possibleassethelp/`
  - `AGENTS.md:105-109`

## Resolved At Current Head - Do Not Reopen Without New Counter-Evidence

These issues were valid earlier in the PR but are already fixed on `autofixing` now:

- bootstrap freshness now fingerprints structured environment inputs in `workflow.ts:1071-1082,1477-1480`
- Godot exit-0 parse/load failures are now classified as fatal in `smoke_test.ts:581-599`
- remediation verdict regexes now accept decorated PASS/FAIL forms in:
  - `workflow.ts:336,1153-1186`
  - `audit_lifecycle_contracts.py:595-598`
- scaffold verifier `TEXT_SUFFIXES` now matches bootstrap in `verify_generated_scaffold.py:16`
- `references/authority-adr.md:15-20` now includes `scafforge-repair`
- `repair_follow_on_refresh.ts:52-74,92-113` now validates payload shape instead of using the old double assertion path
- `apply_repo_process_repair.py:676-701,1822-1826` now implements the ETC2 repair
- `.github/extensions/agentswarm/extension.mjs:120-163` no longer uses the old manual `cmd.exe /c` wrapper
- `.gitignore:34-38` now covers the earlier transient log / rollout / `.godot` artifact families

## Remaining Issue Register

### A. Managed-repair publish safety

- [x] A1. `run_managed_repair.py` now preserves the publish backup on double-failure and only cleans it up after a known-good publish or restore.
  - Smoke coverage now exercises successful publish cleanup, successful restore cleanup, and the backup-preservation failure path.

### B. Audit disposition and prevention mismatches

- [x] B1. `disposition_bundle.py` now classifies package-owned `EXEC-GODOT-006` and `EXEC-REMED-001` as `managed_blocker`, aligning the authoritative bundle with report routing.
- [x] B2. The Blender-route operating-surface finding now uses `SKILL003`, leaving `SKILL002` on its documented thin-`ticket-execution` meaning and aligning prevention guidance, repair docs, and smoke coverage.

### C. Product-completion proof gap for Godot game repos

- [x] C1. Scafforge now audits gameplay-shaped false-completion gaps beyond headless load/export proof.
  - Downstream proof from VB:
    - `start_wave()` has no caller
    - player death reloads the current scene instead of reaching game-over flow
    - score / wave state is not written back to `GameManager`
  - Package coverage now includes:
    - `EXEC-GODOT-010` for dead `start_wave()` progression entrypoints
    - `EXEC-GODOT-011` for unreachable repo-owned game-over flows
    - `EXEC-GODOT-012` for player-facing singleton state that UI reads but gameplay never updates

### D. Branch-only merge-surface noise

- [x] D1. `smoke-test` is removed from the branch.
- [x] D2. `active-plans/possibleassethelp/` is removed from the branch so `active-plans/` returns to plan documents only.
  - Current repo references point to it only as historical concept source inside archived plan material, not as a current canonical package surface.

## Execution Order

## 1. Clean the branch-only merge surface

- [x] Remove the empty `smoke-test` file unless implementation work proves it is actually needed.
- [x] Remove or relocate `active-plans/possibleassethelp/` so `active-plans/` contains planning documents only.
- [x] Re-check the branch diff after cleanup and make sure no sanctioned evidence surfaces were removed accidentally.

Validation

- [x] `git status --short`
- [x] `git diff --name-only main...HEAD | rg '^smoke-test$|^active-plans/possibleassethelp/'`
- [x] confirm `active-plans/*.md`, `archive/archived-audits/`, and sanctioned `livetesting/` source surfaces still remain when expected

## 2. Fix managed-repair publish safety

- [x] Rework `publish_candidate_root()` so backup cleanup happens only after a known-good publish or a known-good restore.
- [x] If restore fails, preserve the backup path and surface it in the thrown error so the operator still has a recovery handle.
- [x] Add regression coverage for:
  - publish failure followed by restore failure
  - successful publish cleanup
  - successful restore cleanup

Validation

- [x] targeted Python regression covering the publish/restore failure path
- [x] `npm run validate:smoke`

## 3. Fix audit routing and prevention guidance

- [x] Make the authoritative disposition bundle agree with report routing for package-owned execution findings.
- [x] Keep a clean separation between:
  - package-owned repairable defects
  - host/manual prerequisite blockers
  - subject-repo source follow-up
- [x] Update the Blender-route finding to `SKILL003` so Report 3 points at the actual Blender-route generation / repair surfaces while `SKILL002` stays on lifecycle explainer drift.
- [x] Add regression coverage proving:
  - package-owned `EXEC*` findings land in the same lane across the bundle and the report
  - `SKILL003` prevention text matches the actual managed-surface failure

Validation

- [x] `npm run validate:smoke`
- [x] `python3 scripts/integration_test_scafforge.py`
- [x] targeted audit fixture or diagnosis-pack assertion for `EXEC-GODOT-006` / `EXEC-REMED-001`

## 4. Strengthen gameplay-completion proof expectations

- [x] Inspect the current finish-validation, target-completion, audit, and prompt surfaces together before editing.
- [x] Add the minimum package-level proof requirement needed to stop "headless load only" from counting as product completion for Godot game repos.
- [x] Keep this package-side:
  - proof expectations
  - audit/report wording
  - generated guidance or required artifact expectations
  - no manual downstream source edits
- [x] Make the requirement concrete enough to catch VB-style false completion claims:
  - progression must start
  - a fail-state or end-state must be reachable when the game claims completion
  - state-reporting surfaces used by the product must actually update

Validation

- [x] `npm run validate:contract`
- [x] `npm run validate:smoke`
- [x] direct review of the resulting completion contract against the VB findings

## 5. Run the full package validation stack

- [x] `npm run validate:contract`
- [x] `npm run validate:smoke`
- [x] `python3 scripts/integration_test_scafforge.py`
- [x] `python3 scripts/validate_gpttalker_migration.py`

## 6. Revalidate downstream repos with the repaired package

- [ ] Run fresh `post_package_revalidation` audits for VA, VC, and VD using the latest root markdown evidence files.
- [ ] Decide from those new packs whether `scafforge-repair` is now appropriate for each repo.
- [ ] Run only Scafforge-managed repairs where the pack says package work is no longer first.
- [ ] Re-review VB from the Scafforge lens after the package proof changes.

Validation

- [ ] store the new diagnosis packs under each downstream repo
- [ ] compare them against the earlier packs cited above
- [ ] confirm blockers now route truthfully to package work, repair, host action, or source follow-up

## 7. Final publish and skill refresh

- [ ] Stage only the intended Scafforge package changes.
- [ ] Commit with a message aligned to the finished scope.
- [ ] Push `autofixing`.
- [ ] If PR 22 has no remaining valid issues, merge into `main`.
- [ ] Refresh the global `.codex` and `.copilot` skill copies from the final package state, including `asset-pipeline`.

## Completion Checklist

- [ ] All still-valid PR review findings from `#issuecomment-4262705139` are fixed or proven no longer applicable.
- [x] The package validation stack passes.
- [x] The branch no longer carries the empty `smoke-test` file or the stray `active-plans/possibleassethelp/` subtree.
- [ ] Fresh downstream audits for VA, VC, and VD were produced after the package fixes landed.
- [ ] Any safe downstream repairs were run through Scafforge only.
- [ ] No manual source edits were made in `womanvshorseVA`, `womanvshorseVB`, `womanvshorseVC`, or `womanvshorseVD`.
- [ ] Global `.codex` and `.copilot` skills were refreshed from the final package state.

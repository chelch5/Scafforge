# Codex Plan 1604

## Goal

Close every currently valid Scafforge issue identified from:

- downstream audits and blocker evidence in `womanvshorseVA`, `womanvshorseVB`, `womanvshorseVC`, and `womanvshorseVD`
- the independent PR review posted on PR 22
- the full adjudication of all existing PR comments on PR 22

Completion scope is 100%: when this plan is done, no known valid package issue from those sources remains unaddressed.

## Evidence Base

### Downstream evidence

- `womanvshorseVD`
  - `/home/rowan/womanvshorseVD/log3.md`
  - `/home/rowan/womanvshorseVD/javaandroidlog1.md`
  - `/home/rowan/womanvshorseVD/diagnosis/20260416-144226/manifest.json`
- `womanvshorseVA`
  - `/home/rowan/womanvshorseVA/wvhvalog1.md`
  - `/home/rowan/womanvshorseVA/.opencode/state/artifacts/history/finish-validate-001/smoke-test/2026-04-16T13-25-37-427Z-smoke-test.md`
  - `/home/rowan/womanvshorseVA/diagnosis/20260416-144506/manifest.json`
- `womanvshorseVC`
  - `/home/rowan/womanvshorseVC/wvhvclogblender1.md`
  - `/home/rowan/womanvshorseVC/blenderissue.md`
  - `/home/rowan/womanvshorseVC/diagnosis/20260416-144646/manifest.json`
- `womanvshorseVB`
  - direct code review findings from:
    - `scripts/wave_spawner.gd`
    - `scenes/player/player.gd`
    - `scripts/autoloads/game_manager.gd`

### Package evidence

- Bootstrap fingerprinting and routing:
  - `skills/repo-scaffold-factory/assets/project-template/.opencode/lib/workflow.ts`
  - `skills/repo-scaffold-factory/assets/project-template/.opencode/tools/environment_bootstrap.ts`
  - `skills/scafforge-audit/scripts/audit_reporting.py`
  - `skills/scafforge-audit/scripts/disposition_bundle.py`
- Godot smoke-test behavior:
  - `skills/repo-scaffold-factory/assets/project-template/.opencode/tools/smoke_test.ts`
  - `scripts/smoke_test_scafforge.py`
- Repair behavior:
  - `skills/scafforge-repair/scripts/apply_repo_process_repair.py`
  - `skills/scafforge-repair/scripts/run_managed_repair.py`
- Audit robustness:
  - `skills/scafforge-audit/scripts/audit_config_surfaces.py`
  - `skills/scafforge-audit/scripts/audit_repo_process.py`
  - `skills/scafforge-audit/scripts/audit_lifecycle_contracts.py`
- Generator/verifier drift:
  - `skills/repo-scaffold-factory/scripts/bootstrap_repo_scaffold.py`
  - `skills/repo-scaffold-factory/scripts/verify_generated_scaffold.py`
- Contract/docs drift:
  - `references/authority-adr.md`
  - `skills/skill-flow-manifest.json`
- Windows command invocation risk:
  - `.github/extensions/agentswarm/extension.mjs`
- PR hygiene:
  - `.gitignore`
  - `active-logs/`
  - `active-plans/agent-logs/`
  - `livetesting/*/.godot/`

## Valid Issue Register

### A. Greenfield and runtime contract defects

- [ ] A1. Bootstrap freshness is file-only and misses host drift.
  - Evidence: `workflow.ts` uses `BOOTSTRAP_INPUT_FILES` plus `computeBootstrapFingerprint()` without host/tool inputs.
  - Downstream proof: VA, VC, and VD all persist `bootstrap.environment_fingerprint = e3b0c442...`; VD stayed blocked after host setup was fixed.
- [ ] A2. Smoke-test PASS can still coexist with Godot parse/load failures.
  - Evidence: `smoke_test.ts` exit-0 classification is too narrow.
  - Downstream proof: VA smoke artifact records `Overall Result: PASS` with `Parse Error` and `Failed to load script`.
- [ ] A3. Greenfield/restart guidance can overclaim clean state or wrong next steps when smoke proof is contradictory.
  - Evidence: audit and runtime surfaces route around contradictory smoke artifacts instead of preventing release claims.
- [ ] A4. Greenfield and downstream operating surfaces still do not fully protect Blender-route repos from missing mandatory agent/skill surfaces.
  - Evidence: VC diagnosis still reports `SKILL002`; route generation is now improved, but repair/audit disposition still needs convergence.
- [ ] A5. Greenfield and finish validation do not enforce product-level gameplay proof strongly enough for Godot projects.
  - Downstream proof: VB headless load and APK existed, but first-wave/game-over/score integration defects remained undetected.

### B. Audit robustness and routing defects

- [ ] B1. Audit can crash on package-side helper load failure instead of emitting a package-owned finding.
- [ ] B2. Transcript JSON decode errors are dropped silently.
- [ ] B3. Audit routing misclassifies package-owned workflow defects as subject-repo source follow-up.
  - Downstream proof: VD diagnosis recommends `subject_repo_source_follow_up` even though the blocker is package bootstrap freshness.
- [ ] B4. SKILL/MODEL/BOOT/CYCLE/SESSION disposition classes are too coarse and route safe managed refresh work incorrectly.
  - Downstream proof: VC `SKILL002` is treated as a manual blocker instead of a repairable managed surface defect.
- [ ] B5. Remediation review verdict parsing misses decorated explicit PASS/FAIL forms and causes false `EXEC-REMED-001`.
  - Downstream proof: recent VA/VC/VD audits still emitted duplicate `EXEC-REMED-001` churn.

### C. Repair safety and package-managed mutation defects

- [ ] C1. Repair cleanup hides backup deletion failures.
- [ ] C2. Candidate promotion into the live repo is non-atomic.
- [ ] C3. `repair_follow_on_refresh.ts` merges unvalidated runtime object shape into typed workflow state.
- [ ] C4. Godot Android ETC2 audit finding has no repair implementation.

### D. Generator/verifier and contract drift

- [ ] D1. `TEXT_SUFFIXES` drift between scaffold bootstrap and scaffold verifier leaves `.cfg`/`.mjs`/`.cjs` placeholder coverage inconsistent.
- [ ] D2. Authority ADR omits `scafforge-repair` from the ownership map even though skill metadata assigns it runtime mutation ownership.

### E. Tooling and PR hygiene defects

- [ ] E1. `.github/extensions/agentswarm/extension.mjs` uses manual `cmd.exe /c` wrapping on Windows.
- [ ] E2. Mergeable branch state currently includes transient runtime artifacts:
  - `.running-pids`
  - raw agent logs under `active-plans/agent-logs/`
  - rollout logs under `active-logs/`
  - Godot cache content under `livetesting/*/.godot/`
- [ ] E3. `.gitignore` does not prevent those transient artifacts from recurring.

## Execution Order

## 1. Fix branch hygiene first

- [ ] Remove transient runtime artifacts from the branch tip while preserving sanctioned package truth.
- [ ] Add ignore rules for `.running-pids`, agent logs, rollout logs, and `livetesting/*/.godot/`.
- [ ] Re-check `git diff main...HEAD --name-only` to confirm the PR shape is materially smaller and no sanctioned evidence surfaces were removed accidentally.

Validation

- [ ] `git status --short`
- [ ] `git diff --name-only main...HEAD | wc -l`
- [ ] verify `active-plans/*.md`, `active-audits/`, `archive/archived-audits/`, and sanctioned `livetesting/` source surfaces still remain when expected

## 2. Repair the bootstrap freshness model

- [ ] Expand generated bootstrap freshness from file-only hashing to a structured environment signature.
  - include stack-sensitive repo inputs such as `project.godot`, `export_presets.cfg`, `opencode.jsonc`, and managed Android/Blender surfaces when present
  - include stack-sensitive host observations that determine bootstrap truth, such as executable paths, SDK/JDK roots, export templates, debug keystore, and Blender MCP availability
- [ ] Update `environment_bootstrap.ts` so the persisted bootstrap proof carries the resolved environment signature and enough evidence to detect host drift after machine moves.
- [ ] Update `workflow.ts` evaluation so a changed environment signature marks bootstrap `stale`.
- [ ] Add scaffold smoke/integration coverage reproducing the VD moved-host scenario.
- [ ] Add audit detection for stale bootstrap truth caused by host drift so audits can call package work first when the freshness model is wrong.

Validation

- [ ] `python3 scripts/integration_test_scafforge.py`
- [ ] `python3 scripts/smoke_test_scafforge.py`
- [ ] targeted reproducible harness case proves changed host signature flips bootstrap to `stale`

## 3. Repair Godot smoke proof integrity

- [ ] Broaden `smoke_test.ts` fatal Godot diagnostic detection to cover parse/class-resolution failures seen in VA, not just the current narrow patterns.
- [ ] Prevent `persistArtifact()` from marking smoke verified when any command records runtime parse/load contradictions, even if exit code is zero.
- [ ] Add package smoke coverage for the exact VA-style diagnostics:
  - `Could not parse global class`
  - `Could not resolve class`
  - `Failed to load script`
- [ ] Strengthen audit wording/routing so contradictory smoke artifacts are treated as package-managed proof failures first, not only source follow-up.
- [ ] Review finish-validation wording and generated prompts so Godot completion requires user-meaningful runtime proof, not only headless load or APK existence.

Validation

- [ ] `python3 scripts/smoke_test_scafforge.py`
- [ ] direct seed case demonstrates FAIL artifact on exit-0 Godot parse diagnostics
- [ ] rerun VA audit after package changes and confirm the diagnosis makes the smoke proof defect explicit and routes it correctly

## 4. Repair audit routing, robustness, and remediation-evidence parsing

- [ ] Wrap audit helper module loading so package-side loader failures become explicit findings rather than unhandled crashes.
- [ ] Track transcript JSON decode failures and surface them in the audit output or diagnosis metadata.
- [ ] Redesign disposition and next-step routing to distinguish:
  - package defect requiring package work first
  - safe managed repo repair
  - host/manual prerequisite
  - subject repo source follow-up
- [ ] Reclassify `SKILL002` and similar generated-surface gaps so safe managed surface refresh is routed to `scafforge-repair` when appropriate.
- [ ] Extend remediation verdict regexes in both:
  - `workflow.ts`
  - `audit_lifecycle_contracts.py`
  to accept decorated verdict forms like `Result: ✅ PASS`.
- [ ] Add package smoke/integration tests that prove decorated verdict acceptance and eliminate false `EXEC-REMED-001`.
- [ ] Ensure diagnosis manifest/report 4 consistency: if package work is required first, `recommended_next_step` and `package_work_required_first` must agree.

Validation

- [ ] `python3 scripts/smoke_test_scafforge.py`
- [ ] `python3 scripts/integration_test_scafforge.py`
- [ ] targeted audit fixture proves:
  - decorated verdict no longer emits `EXEC-REMED-001`
  - stale bootstrap freshness routes to package work first
  - safe managed skill-surface gap routes to repair instead of manual blocker

## 5. Repair managed-repair safety and coverage

- [ ] Add visible warning or hard-fail handling for backup cleanup problems instead of silent `ignore_errors=True`.
- [ ] Make candidate promotion safer:
  - validate candidate immediately before publish
  - add rollback-safe promotion behavior or explicit restore on failed publish
- [ ] Replace unsafe `unknown as Record<string, unknown>` merge in `repair_follow_on_refresh.ts` with validated shape normalization.
- [ ] Implement `GODOT-ANDROID-001` repair support:
  - section-aware `project.godot` editing
  - preserve user content outside the managed setting
  - add causal regression tests

Validation

- [ ] `python3 -m py_compile skills/scafforge-repair/scripts/*.py`
- [ ] `python3 scripts/smoke_test_scafforge.py`
- [ ] targeted repair case proves ETC2 finding is auto-repaired
- [ ] targeted failure case proves publish rollback or safe failure preserves repo integrity

## 6. Fix generator/verifier and contract drift

- [ ] Synchronize or centralize `TEXT_SUFFIXES` between scaffold bootstrap and scaffold verifier.
- [ ] Add `scafforge-repair` to `references/authority-adr.md` ownership map with wording aligned to the current runtime mutation contract.
- [ ] Re-run contract validation to ensure docs and manifests agree after the authority update.

Validation

- [ ] `npm run validate:contract`
- [ ] `python3 scripts/validate_gpttalker_migration.py`

## 7. Fix Windows command invocation safety

- [ ] Remove the manual `cmd.exe /c` wrapper from `agentswarm` and replace it with a safer Windows invocation path.
- [ ] Validate behavior on non-Windows platforms remains unchanged.

Validation

- [ ] targeted Node-level sanity check for the extension module
- [ ] if no Windows runtime is available, add deterministic unit-level coverage for the invocation builder path and document the platform limitation in the commit notes

## 8. Strengthen greenfield and finish-validation proof for gameplay-level completion

- [ ] Extend generated finish-contract wording and/or audit heuristics so “product complete” for Godot game repos requires more than headless load plus artifact existence.
- [ ] Encode a minimal gameplay proof concept that Scafforge can demand from the generated workflow when a repo claims completion:
  - game loop starts
  - core progression path advances
  - critical end-state or fail-state is reachable
  - core state reporting surfaces are updated if the UI depends on them
- [ ] Keep this as package guidance/audit/proof work only. Do not patch downstream source repos manually.

Validation

- [ ] contract validation and smoke tests remain green
- [ ] VB review findings are reflected in strengthened package audit/proof expectations

## 9. Revalidate downstream repos using the repaired package

- [ ] Refresh Scafforge package state in the working tree after all fixes.
- [ ] Run fresh post-package audits for VA, VC, and VD using the newest root markdown evidence files.
- [ ] Decide whether managed repair is now appropriate for each repo.
- [ ] If safe and package-owned, run Scafforge-managed repair only. No manual source edits in downstream repos.
- [ ] Re-review VB from the Scafforge lens after package proof changes; no source edits there either.

Validation

- [ ] store new diagnosis packs under each downstream repo
- [ ] compare new packs against the earlier evidence cited above
- [ ] confirm whether blockers now route to repair, host action, or subject-repo source work truthfully

## 10. Final package validation, publish, and sync

- [ ] Run the canonical package validation commands:
  - `npm run validate:contract`
  - `npm run validate:smoke`
  - `python3 scripts/integration_test_scafforge.py`
  - `python3 scripts/validate_gpttalker_migration.py`
- [ ] Stage only intended Scafforge package changes.
- [ ] Commit with a message that matches the completed scope.
- [ ] Push `autofixing`.
- [ ] If PR 22 has no remaining valid issues, merge into `main`.
- [ ] Refresh the global `.codex` skill copies from the updated Scafforge package, including `asset-pipeline` if needed.

## Completion Checklist

- [ ] All valid PR review findings are fixed or explicitly proven no longer applicable at head.
- [ ] All package validation commands pass.
- [ ] PR 22 branch state is free of transient runtime artifacts.
- [ ] Downstream audits for VA, VC, and VD have been rerun against the repaired package.
- [ ] Any safe downstream repairs have been run through Scafforge only.
- [ ] No manual source edits were made in `womanvshorseVA`, `womanvshorseVB`, `womanvshorseVC`, or `womanvshorseVD`.
- [ ] Global `.codex` skills are refreshed from the final package state.

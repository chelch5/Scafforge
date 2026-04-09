# Defect Register

This register includes only defects that are both currently evidenced and package-actionable.

## Summary Table

| Code | Priority | Short name | Primary package seams |
|---|---|---|---|
| `WFLOW-LOOP-001` | P0 | Split-scope sequencing | generated workflow runtime, ticket creation, ticket routing |
| `WFLOW-STAGE-001` | P1 | Stale-stage recovery | artifact registration, workflow recovery, repair reconciliation |
| `ANDROID-SURFACE-001` | P1 | Android export surfaces | scaffold template, bootstrap, repair, target verifier |
| `TARGET-PROOF-001` | P1 | Runnable vs deliverable proof | adapter contract, audit, follow-up ticketing, harnesses |
| `PRODUCT-FINISH-001` | P1 | Finished-product contract | intake schema, backlog generation, audit, repair routing |
| `REF-SCAN-001` | P2 | Dependency-tree false positives | reference-integrity scan |
| `EXEC-ENV-001` | P2 | Broken repo env classification | Python detection, execution audit, repair verification |
| `ARTIFACT-OWNERSHIP-001` | P2 | Coordinator artifact ownership | team-leader prompt, transcript enforcement |
| `EXEC-REMED-001` | P2 | Remediation review evidence | reviewer prompt, audit enforcement |
| `PROJ-VER-001` | P2 | Godot 4 project-version guard | Godot execution audit |

## `WFLOW-LOOP-001` — Split-scope sequencing still auto-foregrounds dependent child tickets

Priority: P0

Verified current-state evidence:

- `ticket_lookup.ts` foregrounds the first open split-scope child whenever one exists and the parent ticket is not done.
- `ticket_create.ts` auto-activates a new split-scope child when the source ticket is the active ticket.
- `workflow.ts` exposes only `source_mode === "split_scope"`; there is no `split_kind` or equivalent field anywhere in the generated runtime.
- `split_kind` does not appear anywhere under the generated runtime surfaces today.
- The live Glitch evidence still matches the same failure pattern: an Android parent ticket remains open while the release child is pushed foreground before the parent-owned work is complete.

Why it stays in the plan:

- This is still the clearest current package defect that can deadlock normal lifecycle routing without any source-code problem in the subject repo.

Required package outcome:

- split-scope children must distinguish `parallel_independent` from `sequential_dependent`
- sequential dependent children must not auto-activate while the parent is still open
- `ticket_lookup` must keep the parent foreground until the child is legally runnable

## `WFLOW-STAGE-001` — No deterministic stale-stage recovery path when artifacts are current but canonical stage/state is stale

Priority: P1

Verified current-state evidence:

- `artifact_register.ts` only snapshots and registers artifacts; it never reconciles ticket stage, ticket status, or workflow selection.
- `ticket_lookup.ts` routes strictly from manifest/workflow stage and status.
- No current package helper deterministically reconciles "current artifact exists" with stale manifest stage/state after interrupted or out-of-order lifecycle work.
- The repair runner does not contain an artifact-backed stale-stage recovery path for this case.

Why it stays in the plan:

- Without a deterministic recovery path, a repo can preserve correct artifact evidence and still resume into the wrong stage guidance, which is exactly the kind of package-level continuity failure this plan suite is meant to eliminate.

Required package outcome:

- the generated workflow layer must expose one canonical recovery path when artifact evidence and stage/state disagree
- managed repair must be able to use that same reconciliation logic instead of leaving the repo in a stale lifecycle position

## `ANDROID-SURFACE-001` — Godot Android export surfaces are detected but not scaffolded and repaired as owned repo-managed surfaces

Priority: P1

Verified current-state evidence:

- There is no `export_presets.cfg` template anywhere under `skills/repo-scaffold-factory/assets/project-template/`.
- `references/stack-adapter-contract.md` already defines `export_presets.cfg` and non-placeholder repo-local `android/` support surfaces as Godot Android repo prerequisites.
- `environment_bootstrap.ts` already warns when those repo prerequisites are missing.
- `run_managed_repair.py` has no Android-specific repo-surface generation path.
- Spinner and Glitch both still lack `export_presets.cfg`; Glitch also lacks meaningful Android support surfaces.

Why it stays in the plan:

- The earlier draft overstated repair behavior. The correct current package fact is narrower and more actionable: audit already detects the missing repo-managed Android surfaces, but the package still does not scaffold or repair them.

Required package outcome:

- greenfield scaffold must emit the owned repo-managed Android surfaces when the brief declares a Godot Android target
- managed repair must be able to regenerate those owned repo-managed surfaces later
- audit must remain the detector, not be misdescribed as the fixer

## `TARGET-PROOF-001` — Godot Android completion still collapses runnable proof and deliverable proof into one debug APK bar

Priority: P1

Verified current-state evidence:

- `references/stack-adapter-contract.md` still defines Godot Android release proof as `build/android/<project-slug>-debug.apk`.
- `target_completion.py` only models the expected debug APK path for Godot Android completion.
- `audit_execution_surfaces.py` blocks Android-targeted repos on export surfaces plus debug APK proof, with no separate deliverable-proof concept.
- `apply_remediation_follow_up.py` still creates the Android release follow-up ticket as `Build Android debug APK`.
- current smoke fixtures and Android-targeted verification only model Android lanes and debug proof; they do not model a distinct packaged deliverable proof path.

Why it stays in the plan:

- The user explicitly rejected debug-only closure. The package must be able to represent "first runnable Android build" separately from "finished packaged Android product".

Required package outcome:

- keep debug APK proof as runnable proof
- add a separate deliverable proof for signed release output when the brief requires a packaged Android product
- add explicit signing ownership and blocked release semantics rather than silently treating debug proof as final release proof

## `PRODUCT-FINISH-001` — Intake, backlog, audit, and repair have no explicit finished-product contract for art, audio, style, and placeholder policy

Priority: P1

Verified current-state evidence:

- `brief-schema.md` has no section for product finish, placeholder policy, art direction, audio expectations, or content-source ownership.
- `ticket-pack-builder/SKILL.md` has no product-finish lane, no asset/audio ownership rules, and no finish-contract acceptance logic.
- the core package skills and references contain no active finish contract for consumer-facing output beyond generic acceptance language.
- Spinner proves why this gap matters: the repo is playable with procedural visuals and empty asset directories, but the package currently has no way to say whether that is an acceptable final product or only a temporary placeholder state.

Why it stays in the plan:

- This is the package-level answer to the user's asset-quality objection. Scafforge does not need to promise aesthetic magic, but it does need to force the finish bar, placeholder policy, and content-source ownership into canonical truth instead of leaving them implicit.

Required package outcome:

- consumer-facing repos must be able to declare a finished-product contract in canonical truth
- backlog generation must create explicit ownership for finish work when placeholders are not acceptable as final output
- audit and repair must compare repo claims against that contract instead of assuming runnable equals finished

## `REF-SCAN-001` — Reference-integrity scan still walks dependency and build trees

Priority: P2

Verified current-state evidence:

- `audit_execution_surfaces.py` currently walks every `*.py`, `*.ts`, `*.tsx`, `*.js`, and `*.jsx` file via repo-wide recursion for relative-import checks.
- That scan path has no shared exclusion list for `node_modules`, `.venv`, `dist`, `build`, `target`, `vendor`, and similar third-party or build-output trees.
- Node-specific audit logic currently checks whether `node_modules` exists, but that does not stop the generic reference scan from walking dependency code when present.

Why it stays in the plan:

- This is still the package's simplest current false-positive vector in reference-integrity reporting.

Required package outcome:

- reference-integrity scanning must be limited to repo-owned source/config surfaces, not third-party or build-output trees

## `EXEC-ENV-001` — Broken repo-local Python environments can still fall through to system Python import failures

Priority: P2

Verified current-state evidence:

- `_detect_python` in `audit_repo_process.py` prefers repo-local `.venv` executables if they exist, then falls back to `python3` or `python`.
- `_detect_pytest_command` follows the same pattern for pytest.
- `audit_python_execution()` runs import checks with whatever interpreter was selected.
- A broken repo-local environment with a missing interpreter can therefore fall through to system Python and surface dependency import errors as code failures instead of repo-environment failures.
- GPTTalker currently demonstrates that exact evidence shape: its `.venv/bin/python*` entries are missing, system Python exists, and import failure reflects missing project dependencies in the fallback interpreter.

Why it stays in the plan:

- The package already improved generic Python prerequisite detection. This remaining gap is narrower and should be fixed narrowly: broken repo-local envs need first-class classification before import-based code findings run.

Required package outcome:

- once a repo-local Python environment is present but broken, audit and repair verification must classify that state explicitly and stop treating fallback system-import failures as source defects

## `ARTIFACT-OWNERSHIP-001` — Coordinator artifact ownership is still under-specified in the visible team-leader contract

Priority: P2

Verified current-state evidence:

- the visible team-leader prompt says the coordinator does not implement code directly and says coordinator-authored artifacts are suspect
- the same prompt does not explicitly forbid the team leader from calling `artifact_write` or `artifact_register` for planning, implementation, review, or QA bodies
- specialist prompts already own stage artifact authoring on their lanes

Why it stays in the plan:

- The remaining gap is not planner capability. It is coordinator-side prohibition and enforcement. The visible agent contract should make the forbidden action explicit rather than relying on indirect wording.

Required package outcome:

- the team-leader prompt must state that the coordinator must not author planning, implementation, review, or QA artifacts directly
- transcript or audit enforcement must treat violations as workflow defects, not advisory smells

## `EXEC-REMED-001` — Remediation review still lacks mandatory command-output proof

Priority: P2

Verified current-state evidence:

- `__AGENT_PREFIX__-reviewer-code.md` requires compile/import evidence in general, but it does not require remediation review to rerun the original failing command or embed the exact command output.
- `audit_repo_process.py` currently checks lifecycle structure and artifact presence, but there is no remediation-specific review-artifact parser that requires command-output evidence.

Why it stays in the plan:

- Remediation review can still collapse into generic prose unless the package requires evidence that the original failure was rerun and captured.

Required package outcome:

- remediation review must carry the original failing command or acceptance command, its raw output, and the post-fix outcome in the artifact body
- audit must reject remediation review artifacts that lack that evidence

## `PROJ-VER-001` — Godot 4.x config-version and renderer compatibility are still not audited explicitly

Priority: P2

Verified current-state evidence:

- the current audit scripts contain no explicit check for `config_version`, `GLES2`, or `GL Compatibility`.
- Glitch still contains `config_version=2` and `GLES2` references.
- Spinner currently uses the expected Godot 4-era values, so this is a missing audit rule, not a blanket claim that every Godot repo is broken.

Why it stays in the plan:

- This is still a real package blind spot for Godot 4.x repos. The package can already detect missing scenes, scripts, and autoloads; it should also detect stale Godot-project version and renderer settings.

Required package outcome:

- Godot 4.x repos must be audited for obviously stale project-version and renderer settings before Scafforge treats them as clean
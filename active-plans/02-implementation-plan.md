# Implementation Plan

This is the package worklist. Each section below names the exact behavior change that must land, the primary package surfaces that must move together, and the guardrails that keep the change from regressing into the same failure class.

No item in this document is satisfied by documentation-only edits.

## Phase 1 — Lifecycle correctness

### `WFLOW-LOOP-001` — Split-scope sequencing

Primary package surfaces:

- `skills/repo-scaffold-factory/assets/project-template/.opencode/lib/workflow.ts`
- `skills/repo-scaffold-factory/assets/project-template/.opencode/tools/ticket_create.ts`
- `skills/repo-scaffold-factory/assets/project-template/.opencode/tools/ticket_lookup.ts`
- `skills/repo-scaffold-factory/assets/project-template/.opencode/plugins/stage-gate-enforcer.ts`
- `skills/ticket-pack-builder/SKILL.md`
- `scripts/smoke_test_scafforge.py`
- `scripts/integration_test_scafforge.py`

Required changes:

1. Add an explicit split-scope sequencing field to the generated ticket contract.
   Minimum supported values:
   - `parallel_independent`
   - `sequential_dependent`

2. Keep split-scope lineage and dependency semantics separate.
   - Preserve the existing rule that a ticket cannot name the same source ticket in both `source_ticket_id` and `depends_on`.
   - Use `split_kind` to encode parent/child sequencing instead of reintroducing invalid duplicate parentage.

3. Change `ticket_create.ts` so a `sequential_dependent` child never auto-activates while the parent remains open.

4. Change `ticket_lookup.ts` so an open parent with `sequential_dependent` children stays foreground until the child is actually legal to run.

5. Extend `stage-gate-enforcer.ts` so split-scope creation without an explicit sequencing rule is rejected for any generated path that depends on ordered parent-child execution.

6. Update `ticket-pack-builder` guidance so open-parent decomposition defaults to `sequential_dependent` unless the child is truly independent.

7. Add smoke and integration fixtures that reproduce the Glitch-style parent-child Android deadlock and prove the new runtime keeps the parent foreground until the parent-owned work is complete.

Completion bar:

- A split child can still preserve source lineage without being foregrounded prematurely.
- The runtime never routes an agent into a child that is blocked on unfinished parent-owned work.

### `WFLOW-STAGE-001` — Artifact-backed stale-stage recovery

Primary package surfaces:

- `skills/repo-scaffold-factory/assets/project-template/.opencode/lib/workflow.ts`
- `skills/repo-scaffold-factory/assets/project-template/.opencode/tools/artifact_register.ts`
- `skills/repo-scaffold-factory/assets/project-template/.opencode/tools/ticket_lookup.ts`
- `skills/scafforge-repair/scripts/run_managed_repair.py`
- `scripts/smoke_test_scafforge.py`
- `scripts/integration_test_scafforge.py`

Required changes:

1. Add one canonical reconciliation helper in `workflow.ts` that can compare the active ticket's current artifacts against canonical stage/state and determine whether the repo is in a stale-stage condition.

2. Keep explicit stage advancement under team-leader control.
   - Do not make `artifact_register.ts` silently advance tickets through the lifecycle.
   - Do make `artifact_register.ts` preserve enough canonical metadata that `ticket_lookup` and repair can detect stale-stage drift deterministically.

3. Teach `ticket_lookup.ts` to return a recovery path when artifact evidence proves the repo is stale rather than simply routing from the stale manifest state.

4. Teach `run_managed_repair.py` to use the same reconciliation helper so managed repair can heal stale-stage drift after refresh instead of leaving the repo in a contradictory lifecycle position.

5. Add regression fixtures with:
   - current artifact present
   - stale manifest/workflow stage
   - expected recovery guidance instead of ordinary stage routing

Completion bar:

- A repo with current stage artifacts but stale canonical stage/state has one deterministic recovery path.
- Repair can use that path without inventing repo-local manual steps.

## Phase 2 — Android package contract

### `ANDROID-SURFACE-001` — Scaffold and repair owned Android export surfaces

Primary package surfaces:

- `skills/repo-scaffold-factory/assets/project-template/export_presets.cfg` (new template)
- `skills/repo-scaffold-factory/SKILL.md`
- `references/stack-adapter-contract.md`
- `skills/repo-scaffold-factory/assets/project-template/.opencode/tools/environment_bootstrap.ts`
- `skills/scafforge-repair/scripts/run_managed_repair.py`
- `skills/repo-scaffold-factory/scripts/verify_generated_scaffold.py`
- `scripts/smoke_test_scafforge.py`
- `scripts/integration_test_scafforge.py`

Required changes:

1. Add a canonical `export_presets.cfg` template to the project template.
   - It must be renderable from brief/provenance data.
   - It must model repo-managed Android export configuration rather than host-only prerequisites.

2. Update the stack adapter contract so Godot Android clearly separates:
   - repo-managed Android surfaces Scafforge owns
   - host prerequisites Scafforge can only detect
   - signing inputs Scafforge must model but not fabricate

3. Update greenfield scaffold logic so a repo that declares a Godot Android target actually receives the owned export surface instead of only later warnings about its absence.

4. Update `environment_bootstrap.ts` so warnings are explicitly partitioned into:
   - missing repo-managed Android surfaces
   - missing host toolchain or export templates
   - missing signing inputs when deliverable proof is required

5. Update managed repair so it can regenerate owned repo-managed Android surfaces when those surfaces are missing or stale.
   - Do not extend repair into keystore generation, secret creation, or subject-repo gameplay code changes.

6. Update the greenfield verifier and harnesses so a declared Godot Android target fails verification when the repo-managed Android export surface is absent.

Completion bar:

- Scafforge no longer stops at "warning only" for repo-managed Android export surfaces that the package itself should own.

### `TARGET-PROOF-001` — Separate runnable proof from deliverable proof

Primary package surfaces:

- `references/stack-adapter-contract.md`
- `skills/repo-scaffold-factory/assets/project-template/.opencode/tools/environment_bootstrap.ts`
- `skills/scafforge-audit/scripts/target_completion.py`
- `skills/scafforge-audit/scripts/audit_execution_surfaces.py`
- `skills/ticket-pack-builder/SKILL.md`
- `skills/ticket-pack-builder/scripts/apply_remediation_follow_up.py`
- `scripts/smoke_test_scafforge.py`
- `scripts/integration_test_scafforge.py`

Required changes:

1. Replace the single Godot Android `release proof` concept with two explicit proof layers:
   - runnable proof
   - deliverable proof

2. Keep debug APK proof as runnable proof.

3. Add deliverable-proof semantics for packaged Android output.
   - The deliverable artifact must be a signed release APK or AAB when the canonical brief requires a packaged Android product.

4. Add explicit signing ownership.
   - When packaged Android delivery is required, generate a separate signing-ownership lane or blocked signing ticket before `RELEASE-001` can close.
   - `RELEASE-001` must not close on debug proof alone in packaged-product mode.

5. Update `ticket-pack-builder` bootstrap and remediation-follow-up paths so the canonical Android backlog shape matches the contract:
   - `ANDROID-001` owns repo-managed export surfaces
   - `SIGNING-001` owns signing prerequisites when packaged delivery is required
   - `RELEASE-001` owns runnable and deliverable proof only after the prerequisites are owned

6. Update audit and target-completion helpers to emit distinct findings for:
   - missing repo-managed Android surfaces
   - missing runnable proof
   - missing deliverable proof or signing inputs once the repo claims packaged-product completion

7. Update smoke and integration coverage so the package fails if a future change collapses deliverable proof back into debug APK proof.

Completion bar:

- The package can truthfully represent "first runnable Android build" and "finished packaged Android product" as two different bars.

## Phase 3 — Finished-product contract

### `PRODUCT-FINISH-001` — Add a first-class finished-product contract

Primary package surfaces:

- `skills/spec-pack-normalizer/references/brief-schema.md`
- `skills/spec-pack-normalizer/SKILL.md`
- `skills/scaffold-kickoff/SKILL.md`
- `skills/ticket-pack-builder/SKILL.md`
- `skills/project-skill-bootstrap/SKILL.md`
- `skills/scafforge-audit/scripts/audit_contract_surfaces.py` or a dedicated finish-contract audit helper
- `skills/scafforge-repair/SKILL.md`
- `scripts/smoke_test_scafforge.py`
- `scripts/integration_test_scafforge.py`

Required changes:

1. Add a `Product Finish Contract` section to the canonical brief schema for consumer-facing repos.
   Minimum fields:
   - target deliverable kind
   - placeholder policy
   - visual finish target
   - audio finish target
   - content-source and licensing plan
   - finish acceptance signals

2. Teach `spec-pack-normalizer` and `scaffold-kickoff` how to treat the finish contract.
   - For consumer-facing repos, unresolved finish requirements must become explicit blocking decisions rather than implicit assumptions.
   - For internal tools and services, the finish contract can remain intentionally minimal.

3. Teach `ticket-pack-builder` to create explicit finish ownership when placeholders are not acceptable final output.
   - Do not bury art/audio/content completion under generic polish tickets.
   - Do not let runnable software be treated as finished product when the finish contract requires more.

4. Teach `project-skill-bootstrap` to synthesize stack-aware local guidance for the finish pipeline when the brief includes that contract.

5. Teach audit to compare repo claims against the finish contract.
   - Audit should not judge aesthetics subjectively.
   - Audit should flag missing owned finish work when the repo claims finished-product completion but the canonical contract still requires non-placeholder visuals, audio, or content proof.

6. Teach repair to route finish gaps into canonical follow-up tickets rather than silently leaving restart surfaces in a false-ready state.

7. Add fixtures that distinguish:
   - a repo where procedural or placeholder output is explicitly acceptable final output
   - a repo where the same output is only an unfinished interim state

Completion bar:

- Scafforge can encode and enforce the difference between a functional prototype and a finished product without pretending to auto-create art assets.

## Phase 4 — Audit and prompt hardening

### `REF-SCAN-001` — Exclude dependency and build trees from reference-integrity scanning

Primary package surfaces:

- `skills/scafforge-audit/scripts/audit_execution_surfaces.py`
- a new shared scan helper if needed under `skills/scafforge-audit/scripts/`
- `scripts/smoke_test_scafforge.py`

Required changes:

1. Move repo-wide source iteration behind one shared exclusion-aware helper.

2. Exclude at minimum:
   - `.git/`
   - `node_modules/`
   - `.venv/`
   - `venv/`
   - `dist/`
   - `build/`
   - `target/`
   - `vendor/`
   - other obvious generated dependency or build-output trees used by supported stacks

3. Keep config-managed repo-owned source files in scope.

4. Add regression fixtures that contain:
   - a real broken relative import in repo-owned source
   - an intentionally broken relative import under an excluded dependency tree

Completion bar:

- `REF-003` style findings come from repo-owned code only.

### `EXEC-ENV-001` — Distinguish broken repo-local Python environments from source import failures

Primary package surfaces:

- `skills/scafforge-audit/scripts/audit_repo_process.py`
- `skills/scafforge-audit/scripts/audit_execution_surfaces.py`
- `skills/scafforge-repair/scripts/run_managed_repair.py`
- `scripts/smoke_test_scafforge.py`

Required changes:

1. Add a repo-local Python environment health check before import and test execution.

2. Once `.venv` exists but is broken, stop falling through to system Python for import-based source validation.

3. Emit a dedicated environment finding for broken repo-local Python env state.

4. Carry the same classification into repair verification so repair does not misstate source failures when the repo-local env is broken.

5. Add regression coverage for:
   - missing repo-local interpreter with system Python present
   - healthy repo-local interpreter
   - no repo-local env plus no system Python

Completion bar:

- Broken repo-local env state is a first-class finding, not a misclassified source import failure.

### `ARTIFACT-OWNERSHIP-001` — Make coordinator artifact prohibition explicit and enforceable

Primary package surfaces:

- `skills/repo-scaffold-factory/assets/project-template/.opencode/agents/__AGENT_PREFIX__-team-leader.md`
- `skills/scafforge-audit/scripts/audit_session_transcripts.py`
- `scripts/smoke_test_scafforge.py`

Required changes:

1. Add explicit coordinator-side prohibition language.
   - The team leader must not call `artifact_write` or `artifact_register` for planning, implementation, review, or QA artifact bodies.

2. Keep the specialist and tool ownership boundaries intact.

3. Extend transcript-based enforcement so coordinator-authored stage artifacts are reported as workflow defects rather than vague suspicion.

Completion bar:

- The visible coordinator contract states the forbidden action directly, and transcript audit treats violations as real package defects.

### `EXEC-REMED-001` — Require command-output proof in remediation review

Primary package surfaces:

- `skills/repo-scaffold-factory/assets/project-template/.opencode/agents/__AGENT_PREFIX__-reviewer-code.md`
- `skills/scafforge-audit/scripts/audit_repo_process.py`
- `skills/scafforge-repair/SKILL.md`
- `scripts/smoke_test_scafforge.py`

Required changes:

1. Update the reviewer prompt so remediation review must rerun the original failing command or the canonical acceptance command for the repaired surface.

2. Require the review artifact to embed:
   - the command that was run
   - the raw command output
   - the post-fix pass/fail result

3. Extend audit so a remediation review artifact without that evidence does not count as trustworthy review closure.

4. Reflect the same evidence rule in `scafforge-repair/SKILL.md` so the skill contract and generated prompt stay aligned.

Completion bar:

- remediation review cannot pass on prose alone

### `PROJ-VER-001` — Add Godot 4 project-version and renderer checks

Primary package surfaces:

- `skills/scafforge-audit/scripts/audit_execution_surfaces.py`
- `scripts/smoke_test_scafforge.py`

Required changes:

1. Add explicit Godot 4-era checks for obviously stale project configuration.

2. At minimum, reject known stale values such as:
   - `config_version=2` for current Godot 4.x repos
   - `GLES2` renderer references in Godot 4.x repos

3. Add positive coverage using a current-good fixture and negative coverage using a Glitch-like stale config fixture.

Completion bar:

- Scafforge can catch this class of stale Godot 4 config drift before claiming a repo is clean.

## Phase 5 — Harness closure

Package-wide rule:

- Every behavior change above must land with matching smoke, integration, or generated-verifier coverage.
- None of the defects in this document are complete if the package still relies on a doc-only promise rather than an executable regression guard.
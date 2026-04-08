# Verification Suite

This is the package-side proof bar for the plan bundle in this directory.

## 1. Core validation entrypoints

Run these after implementation work lands:

```bash
npm run validate:contract
npm run validate:smoke
python3 scripts/integration_test_scafforge.py
python3 scripts/validate_gpttalker_migration.py
```

Use `python3`, not `python`.

## 2. Defect-specific proof requirements

### `WFLOW-LOOP-001`

Required proof:

- generated runtime contains explicit split-scope sequencing support
- smoke coverage proves a `sequential_dependent` child does not auto-activate while the parent is open
- integration coverage proves the Glitch-style parent/child deadlock no longer occurs

Minimum static presence checks:

```bash
rg -n "split_kind|sequential_dependent|parallel_independent" \
  skills/repo-scaffold-factory/assets/project-template/.opencode
```

Expected result after the fix:

- sequencing metadata exists in the runtime contract
- `ticket_create.ts` and `ticket_lookup.ts` both reference it

### `WFLOW-STAGE-001`

Required proof:

- there is one artifact-backed stale-stage reconciliation path in the runtime
- smoke coverage proves a repo with current artifacts and stale manifest stage receives recovery guidance instead of ordinary routing
- managed repair can exercise the same recovery path

Minimum static presence checks:

```bash
rg -n "recovery_action|stale stage|artifact-backed|reconcile" \
  skills/repo-scaffold-factory/assets/project-template/.opencode \
  skills/scafforge-repair/scripts/run_managed_repair.py
```

### `ANDROID-SURFACE-001`

Required proof:

- a Godot Android scaffold now emits owned Android export surfaces
- managed repair can regenerate those surfaces when they are missing
- the greenfield verifier fails when a declared Android target lacks those surfaces

Minimum static presence checks:

```bash
rg -n "export_presets.cfg|android support surfaces|ANDROID-001" \
  references/stack-adapter-contract.md \
  skills/repo-scaffold-factory \
  skills/scafforge-repair/scripts/run_managed_repair.py \
  skills/repo-scaffold-factory/scripts/verify_generated_scaffold.py
```

### `TARGET-PROOF-001`

Required proof:

- the package models runnable proof and deliverable proof as separate concepts
- packaged Android repos cannot close on debug APK proof alone
- ticket generation and remediation-follow-up reflect signing ownership when packaged delivery is required

Minimum static presence checks:

```bash
rg -n "runnable_proof|deliverable_proof|SIGNING-001|signed release|debug APK" \
  references/stack-adapter-contract.md \
  skills/repo-scaffold-factory/assets/project-template/.opencode/tools/environment_bootstrap.ts \
  skills/scafforge-audit/scripts/target_completion.py \
  skills/scafforge-audit/scripts/audit_execution_surfaces.py \
  skills/ticket-pack-builder/SKILL.md \
  skills/ticket-pack-builder/scripts/apply_remediation_follow_up.py
```

### `PRODUCT-FINISH-001`

Required proof:

- the canonical brief schema has a first-class finish contract for consumer-facing repos
- bootstrap backlog generation creates finish ownership when placeholders are not final output
- audit compares repo completion claims against the finish contract
- repair routes finish gaps into canonical follow-up instead of false-ready restart surfaces

Minimum static presence checks:

```bash
rg -n "Product Finish Contract|placeholder policy|visual finish|audio finish|content-source|finish acceptance" \
  skills/spec-pack-normalizer \
  skills/scaffold-kickoff \
  skills/ticket-pack-builder \
  skills/project-skill-bootstrap \
  skills/scafforge-audit \
  skills/scafforge-repair
```

### `REF-SCAN-001`

Required proof:

- reference scan uses shared exclusions for dependency and build trees
- smoke coverage proves third-party broken imports do not surface as repo-local findings
- repo-owned broken imports still surface correctly

Minimum static presence checks:

```bash
rg -n "node_modules|\.venv|vendor|target|dist|build" \
  skills/scafforge-audit/scripts
```

### `EXEC-ENV-001`

Required proof:

- broken repo-local Python env state is surfaced as an environment finding before source import checks run
- smoke coverage proves missing repo-local interpreter plus system fallback no longer produces a misclassified code failure

Minimum static presence checks:

```bash
rg -n "broken venv|repo-local Python environment|system Python|EXEC-ENV|environment finding" \
  skills/scafforge-audit/scripts \
  skills/scafforge-repair/scripts/run_managed_repair.py
```

### `ARTIFACT-OWNERSHIP-001`

Required proof:

- the team-leader prompt explicitly forbids coordinator-authored planning, implementation, review, and QA artifacts
- transcript audit treats coordinator-authored stage artifacts as workflow defects

Minimum static presence checks:

```bash
rg -n "must not call `artifact_write`|must not call `artifact_register`|coordinator-authored" \
  skills/repo-scaffold-factory/assets/project-template/.opencode/agents/__AGENT_PREFIX__-team-leader.md \
  skills/scafforge-audit/scripts/audit_session_transcripts.py
```

### `EXEC-REMED-001`

Required proof:

- remediation review prompts require the original failing or acceptance command to be rerun
- review artifacts must embed raw command output
- audit rejects remediation review artifacts that lack this evidence

Minimum static presence checks:

```bash
rg -n "raw command output|original failing command|acceptance command|remediation review" \
  skills/repo-scaffold-factory/assets/project-template/.opencode/agents/__AGENT_PREFIX__-reviewer-code.md \
  skills/scafforge-audit/scripts/audit_repo_process.py \
  skills/scafforge-repair/SKILL.md
```

### `PROJ-VER-001`

Required proof:

- Godot 4 audit detects stale project-version and renderer settings
- smoke coverage proves a Glitch-like stale config fails while a Spinner-like current config passes

Minimum static presence checks:

```bash
rg -n "config_version|GLES2|GL Compatibility" \
  skills/scafforge-audit/scripts/audit_execution_surfaces.py \
  scripts/smoke_test_scafforge.py
```

## 3. Harness additions required by this bundle

### `scripts/smoke_test_scafforge.py`

Must gain fixtures for:

- sequential split child versus independent split child
- artifact-backed stale-stage recovery
- missing Android export surfaces on greenfield scaffold
- runnable-proof-only Android repo versus packaged-deliverable Android repo
- finished-product contract required versus procedural-final allowed
- broken repo-local Python env with system fallback present
- remediation review with and without raw command proof
- Godot 4 current config versus stale config

### `scripts/integration_test_scafforge.py`

Must gain at least these end-to-end cases:

- greenfield packaged Android repo with explicit signing and deliverable-proof ownership
- managed repair of missing Android export surfaces without direct source edits
- consumer-facing repo whose finish contract forces explicit finish tickets
- broken repo-local Python env classified as environment failure rather than source failure

### `skills/repo-scaffold-factory/scripts/verify_generated_scaffold.py`

Must fail when a generated repo declares:

- a Godot Android target but lacks owned Android export surfaces
- a packaged Android product goal but lacks deliverable-proof ownership
- a consumer-facing finished-product goal but lacks the required finish-contract ownership surfaces

## 4. Final sign-off

This plan bundle is not verified until all of the following are true:

1. The four standard validation entrypoints pass.
2. Every defect-specific static presence check above returns the new contract terms in the expected package surfaces.
3. Smoke coverage contains both pass and fail fixtures for each newly encoded contract.
4. Integration coverage proves greenfield and repair behavior, not only static file presence.
5. The new acceptance gates in `09-acceptance-gates.md` are satisfied for GPTTalker, spinner, and glitch through package behavior, not direct repo-local edits.
# Completion Validation Matrix Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Status:** DONE
**Goal:** Build a cross-platform completion validation system so Scafforge can prove “done” across web apps, games, scripts, services, desktop apps, and Android repos without relying on agent self-report.

**Architecture:** Define a validation ladder per repo family and connect it to audit, repair, and handoff publication. The system should prefer the cheapest truthful check first, escalate to runtime, screenshot, network, emulator, or device proof only when required, and store concise structured proof artifacts that other package skills can consume.

**Tech Stack / Surfaces:** package validators, `skills/scafforge-audit/`, generated template stage-gates and handoff tooling, stack adapter references, test fixtures, platform-specific tooling recommendations.
**Depends On:** `02-downstream-reliability-hardening` for failure families; should run alongside `11-repository-documentation-sweep`.
**Unblocks:** every autonomy and review-oriented plan, especially `07-autonomous-downstream-orchestration` and `08-meta-improvement-loop`.
**Primary Sources:** `active-plans/_source-material/validation/completionqualityvalidation/toolstoimplement.md`, current package validation commands, `references/stack-adapter-contract.md`, audit verifier scripts, and the existing multi-stack proof harness in `scripts/integration_test_scafforge.py`.

---

## Problem statement

Scafforge currently has fragmented validation hints, with too much emphasis on smoke-level checks and Android-only tooling. The system needs one coherent answer to:

- what counts as “done” for each repo family
- which proof artifacts are mandatory
- when screenshot, video, network, process, or emulator evidence is required
- how family-level proof interacts with stack-adapter proof
- how validators feed audit and restart/handoff surfaces

Without that, weak models will keep equating “agent says it works” with actual completion.

## Repo families this plan must cover

- web apps and browser-heavy interactive projects
- Godot and game repos
- CLI and script repos
- backend and service repos
- desktop apps on Windows and Linux
- Android repos

Apple/iOS/macOS validation is explicitly out of scope for this cycle.

## Required deliverables

- a validation ladder per repo family
- a tool matrix covering static, runtime, visual, network, and device or emulator proof
- a proof-artifact convention that other package skills can consume
- a machine-readable validation matrix in one named location
- generated-repo guidance that blocks handoff when required proof is missing
- a family-to-stack mapping rule so family proof and stack proof do not contradict each other

## Package surfaces likely to change during implementation

- `references/stack-adapter-contract.md`
- `references/validation-proof-matrix.json`
- `scripts/validate_scafforge_contract.py`
- `scripts/smoke_test_scafforge.py`
- `scripts/integration_test_scafforge.py`
- `skills/scafforge-audit/scripts/shared_verifier.py`
- `skills/scafforge-audit/scripts/target_completion.py`
- new sibling proof-matrix modules under `skills/scafforge-audit/scripts/`
- `skills/scafforge-audit/scripts/audit_execution_surfaces.py`
- `skills/scafforge-audit/scripts/audit_reporting.py`
- `skills/repo-scaffold-factory/assets/project-template/.opencode/plugins/stage-gate-enforcer.ts`
- `skills/repo-scaffold-factory/assets/project-template/.opencode/tools/handoff_publish.ts`
- generated process and handoff docs in the project template
- `tests/fixtures/` with representative stack-family cases

## Family-to-stack mapping rule

This plan must not let repo family replace stack truth.

- Tier 1 stack-adapter proof remains the baseline proof host contract.
- Repo-family proof layers on top of that baseline when behavior or UX needs extra evidence.
- Example: a Node web app still uses the Node adapter proof host, then adds family-level HTTP, browser, or screenshot checks if the repo type requires them.
- Example: a Godot game still uses the Godot adapter proof host, then adds family-level scene, input, or screenshot checks if the repo type requires them.
- Multi-stack repos must satisfy the relevant Tier 1 proof for each owned runtime surface, plus the family-level behavioral proof for the top-level product experience.

## Machine-readable matrix decision

The machine-readable mapping should live in:

- `references/validation-proof-matrix.json`

That file should be the single package-owned mapping between:

- repo family
- stack adapter or adapters
- proof tiers
- required artifact kinds
- allowed degradation rules

Generated repos, validators, audit scripts, and handoff surfaces should consume the same matrix instead of each embedding their own copy.

## Proof artifact schema decision

Proof artifacts should be structured JSON and stored predictably.

Recommended shape:

- storage path: `.opencode/state/artifacts/proof-<family>.json`
- format: JSON

Required top-level fields:

- `family`: string
- `stack_label`: string
- `proof_tier`: string
- `passed`: boolean
- `checked_at`: string
- `artifact_path`: string or `null`
- `artifact_kind`: string
- `summary`: string

Optional fields:

- `command`: string
- `exit_code`: integer
- `url`: string
- `screenshot_path`: string
- `log_excerpt`: array of strings
- `degraded_reason`: string
- `not_applicable_reason`: string

The first implementation pass should keep this schema compact and auditable instead of turning proof artifacts into uncontrolled log dumps.

## target_completion architecture decision

`target_completion.py` should not grow into one giant `if/elif` tree.

Implementation target:

- keep `target_completion.py` as the dispatcher and shared helpers surface
- add sibling family modules or a registry-backed dispatch structure for web, game, CLI/script, service, desktop, and Android proof evaluation
- expose one consistent interface per family so audit, handoff, and stage-gate code can consume the same shape

This is explicitly meant to prevent Android-specific logic from becoming the template for every other family.

## Proposed validation ladder

Each supported repo family should progress through some subset of:

1. static contract and config checks
2. build, install, or bootstrap checks
3. runtime or process health checks
4. stack-specific behavioral checks
5. visual or artifact review checks
6. proof publication into handoff and audit surfaces

The exact ladder differs by family. The key rule is that completion cannot skip directly from code existence to success.

## Tool bundle categories this plan should evaluate

- Web: Playwright or browser automation, HTTP probes, performance or accessibility spot checks where relevant
- Godot or game: engine boot checks, scene or import checks, screenshot capture, input smoke coverage where feasible
- CLI or script: command exit status, structured output comparison, log capture, environment or bootstrap checks
- Backend or service: process startup, health endpoints, contract probes, dependency or bootstrap verification
- Desktop Windows or Linux: launch verification, window or process truth, screenshot capture when UI exists
- Android: `adb`, `logcat`, emulator workflows, Gradle, Android SDK CLI
- Shared support tools: `ffmpeg`, `ImageMagick`, `CMake`, Vulkan or toolchain checks, language servers only where they materially improve validation

## Headless-capable validation rule

Implementation and validation should prefer automation-friendly, headless-capable routes when they provide truthful proof. The proof ladder must acknowledge that:

- cheapest-first order should be explicit: process health -> HTTP or runtime truth -> Xvfb or virtual-display screenshot -> full browser automation or emulator/device interaction
- screenshot-based proof must degrade gracefully when no display server exists
- browser automation and screenshot capture should never be the first required check when cheaper truth already proves failure

## External-source caveat

The Android external skill sources in the research notes are research inputs only.

- public discovery is allowed
- direct import of external skills into package or generated output is not allowed by default
- any useful technique must be distilled into Scafforge-owned guidance and validators

## Phase plan

### Phase 1: Define the validation matrix

- [x] Write the supported repo families and the minimum validation ladder each one must satisfy.
- [x] Identify which proof steps are mandatory, optional, or stack-conditional.
- [x] Create `references/validation-proof-matrix.json` as the machine-readable source of truth for family-to-stack proof expectations.
- [x] Make sure the matrix distinguishes between “no validator exists yet” and “proof not required.”
- [x] Encode the family-to-stack mapping rule so family-level proof supplements Tier 1 stack proof instead of replacing it.

### Phase 2: Specify tool bundles and artifact rules

- [x] For each repo family, choose the baseline tools Scafforge should recommend or require.
- [x] Make the first-pass tool matrix answer the current research list explicitly, including `ImageMagick`, `ffmpeg`, `CMake`, `adb`, `logcat`, Android emulator flows, `Gradle`, Vulkan or graphics-capability checks where relevant, and language-server assistance only when it materially improves validation truth.
- [x] Define the proof artifact outputs and align them to the JSON schema above.
- [x] Decide what should be committed into generated repos versus what remains ephemeral package evidence.
- [x] Ensure proof storage stays concise and reviewable instead of turning into uncontrolled log dumps.
- [x] Record the headless-degradation order for desktop and web proof explicitly in the matrix.

### Phase 3: Seed representative fixtures first, then wire audit

- [x] Extend the existing `multi_stack_targets()` proof infrastructure in `scripts/integration_test_scafforge.py` instead of building a second fixture system from scratch.
- [x] Add or extend fixture coverage so at least one example exists for each supported family.
- [x] Ensure a failing fixture demonstrates a real missing-proof or wrong-proof condition.
- [x] Ensure a healthy fixture can clear the expected validation ladder without needing human interpretation.
- [x] Use the fixtures to prove that Android tooling is no longer the only concrete validation story in the repo.

### Phase 4: Integrate validation with audit, stage gates, and handoff

- [x] Teach audit to consume the validation matrix and report missing proof as a named issue, not a vague smell.
- [x] Teach handoff publication to summarize which proof steps passed, failed, degraded, or were not applicable.
- [x] Update the generated stage-gate flow so required proof blocks completion claims.
- [x] Make sure repair flows can request the right proof rerun instead of forcing the whole pipeline to restart blindly.
- [x] Keep proof-family findings machine-searchable, ideally through a dedicated proof-related finding family if implementation supports it cleanly.

### Phase 5: Connect matrix language to contributor docs

- [x] Add a concise operator-facing explanation of the validation ladder and proof categories.
- [x] Update package docs so supported repo families and proof expectations are discoverable.
- [x] Ensure generated repos get a lightweight explanation of their own required proof bundle.
- [x] Cross-link the matrix into the documentation sweep plan so future contract changes keep docs aligned.

## Validation and proof requirements

- each supported repo family has an explicit proof ladder
- required proof artifacts are named, stored predictably, and consumable by audit and handoff
- generated repos cannot claim completion when mandatory proof is absent
- validation coverage is visibly broader than Android-only smoke checks
- the family matrix extends existing multi-stack proof infrastructure instead of fragmenting it

## Risks and guardrails

- Do not create one giant validator that pretends every stack is the same.
- Do not overfit to Android because the source note contained Android tools.
- Do not demand expensive browser, emulator, or device checks when cheaper truthful checks already prove failure.
- Do not hide unsupported stacks behind silent skips; surface the gap clearly.
- Do not let family-level proof contradict the Tier 1 stack adapter contract.

## Documentation updates required when this plan is implemented

- stack adapter and validation references
- package validation command docs
- generated process and handoff docs
- contributor or operator guidance for proof artifacts

## Completion criteria

- Scafforge has a documented validation ladder for every supported repo family
- proof artifacts are first-class completion requirements
- audit and handoff consume the same proof model
- package validation is no longer smoke-only or Android-biased
- `scripts/integration_test_scafforge.py` visibly proves broader-than-Android family coverage

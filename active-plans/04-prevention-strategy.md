# Prevention Strategy

This strategy is about preventing Scafforge from drifting back into the same package failures after the code changes land.

## 1. Prevent stale plan drift

Rules for future package planning work:

- corrections must be folded into the active defect register and implementation plan, not parked in a sidecar addendum
- repo-local remediation instructions do not belong in package planning documents
- if a finding is already fixed in package code, remove it from the active plan set instead of preserving it for narrative continuity
- if a claim about current package behavior changes, update the active plan files in the same change that updates the underlying code

This directly addresses the failure mode that produced the previous `active-plans/` corpus.

## 2. Bundle related contract changes together

Several of the remaining defects only stay fixed if multiple package seams move together.

### Lifecycle bundle

Any split-scope or stale-stage change must ship as one bundle:

- generated runtime contract (`workflow.ts`)
- ticket creation and lookup tools
- stage-gate enforcement
- ticket-pack-builder guidance
- smoke and integration coverage

Do not land a split-scope change in just one of those layers.

### Android bundle

Any Godot Android contract change must ship as one bundle:

- stack adapter contract
- project template
- environment bootstrap
- target completion and execution audit
- ticket generation and remediation follow-up
- greenfield verifier and smoke coverage

Do not land a new Android proof rule in audit without updating scaffold, repair, and ticket ownership.

### Finished-product bundle

Any product-finish change must ship as one bundle:

- canonical brief schema
- kickoff and normalization rules
- backlog generation
- local-skill generation when needed
- audit comparison logic
- repair follow-up routing
- harness fixtures

Do not add a finish contract to intake without giving backlog, audit, and repair a way to consume it.

### Evidence bundle

Any evidence-enforcement change must ship as one bundle:

- the generated prompt or tool contract that asks for the evidence
- the audit or transcript parser that rejects missing evidence
- the harness case that proves the package fails when the evidence is absent

## 3. Keep audit rules scoped to repo-owned truth

To prevent false positives:

- file-walk audits must use shared exclusion-aware iteration
- environment execution audits must classify repo-env failure before source failure
- finish-contract audits must compare repo claims against explicit canonical truth, not subjective quality guesses

The rule is simple: audit repo-owned truth, not dependency noise and not unrecorded assumptions.

## 4. Keep repair inside its real boundary

To prevent repair overreach:

- repair may regenerate managed workflow and repo-owned config surfaces
- repair may create or normalize tickets for missing source work
- repair may not fabricate secrets, signing material, or content assets
- repair may not present a repo as clean when only host or source follow-up remains

This boundary must stay explicit in the repair skill, runtime, and plan documents.

## 5. Encode consumer-finish requirements as contract, not aspiration

To prevent another Spinner-style ambiguity:

- consumer-facing repos need an explicit finish contract when the product bar is above runnable prototype
- backlog generation must create ownership for finish work when placeholders are not final output
- audit must compare completion claims to that contract

This prevents the package from silently treating "it runs" as equivalent to "it is finished".

## 6. Add fixture pairs for every ambiguous contract

For each defect class in this bundle, add both:

- one fixture that should pass under the new contract
- one fixture that should fail under the new contract

Required fixture pairs:

- split child may run now versus split child must stay behind its parent
- current artifact/state aligned versus artifact-backed stale-stage drift
- Android runnable proof only versus packaged Android deliverable proof required
- procedural visuals explicitly acceptable versus procedural-only state not acceptable as final product
- healthy repo-local Python env versus broken repo-local Python env with system fallback available
- remediation review with real command proof versus remediation review with prose only
- current Godot 4 config versus stale `config_version=2` and `GLES2`

## 7. Make the greenfield verifier stricter where the package is stricter

Today the greenfield verifier checks placeholders, JSON validity, cross-reference integrity, and some bootstrap/continuation rules. Once this bundle lands, it also needs to reject:

- declared Godot Android targets missing owned Android export surfaces
- declared packaged Android targets missing deliverable-proof ownership
- declared consumer-facing finished-product repos missing finish-contract ownership surfaces

If the verifier does not fail on those conditions, the package will drift back into warning-only behavior.

## 8. Keep the package-only boundary visible

To prevent future plan or repair drift:

- package plans must describe package changes and package-observed outcomes
- subject-repo edit instructions belong in subject-repo work, not in `Scafforge/active-plans/`
- evidence repos may be used to prove the package problem, but not as the implementation surface for the package fix

This boundary is especially important for Android export, signing, and product-finish work because those areas tempt package plans to collapse into repo-local playbooks.
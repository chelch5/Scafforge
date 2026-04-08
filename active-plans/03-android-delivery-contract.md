# Android Delivery Contract

This document replaces the earlier narrow `export_presets.cfg` discussion with the full package contract Scafforge needs for Godot Android repos.

## 1. Verified Current-State Problem

Current package reality is split across several seams:

- the stack adapter contract already says Godot Android repos need `export_presets.cfg` and non-placeholder repo-local `android/` support surfaces
- `environment_bootstrap.ts` already warns when those repo prerequisites are missing
- there is still no `export_presets.cfg` template in the project template
- repair still does not provision repo-managed Android export surfaces
- the target-completion contract still treats a debug APK as the final Android proof bar

That means the package can detect the gap, but it cannot yet own the full repo-managed Android delivery contract.

## 2. The Contract Must Split Three Different Kinds of Inputs

### Repo-managed Android surfaces

These are owned by Scafforge scaffold and managed repair.

- `export_presets.cfg`
- repo-local `android/` support surfaces when the generated workflow says the repo owns them
- package name, version, and related export metadata that come from canonical project truth

### Host prerequisites

These are detected by bootstrap and audit, but Scafforge must not pretend it can fabricate them.

- Godot executable
- Java and `javac`
- Android SDK path
- Godot export templates

### Signing inputs

These must be modeled explicitly, but they are not safe deterministic repair output.

- release keystore or CI secret reference
- alias and password ownership
- release artifact format (`apk` or `aab`)
- signing-mode decision when the brief requires packaged delivery

## 3. Runnable Proof and Deliverable Proof Are Not the Same Thing

Scafforge must treat these as separate proof layers.

### Runnable proof

This answers: can the repo produce and validate a first runnable Android build?

For Godot Android, runnable proof should include:

- `godot --headless --quit --path .` or the resolved equivalent
- debug export success for the canonical Android export command
- debug APK present at the canonical runnable-proof path

### Deliverable proof

This answers: can the repo produce the packaged Android artifact the brief actually asks for?

For packaged Android product goals, deliverable proof should include:

- a signed release APK or AAB
- explicit signing ownership already satisfied
- artifact path declared in canonical truth

Debug APK proof must remain valid runnable proof. It must stop being treated as the only release proof when the brief requires a packaged Android product.

## 4. Canonical Backlog Ownership

The Android backlog needs three ownership layers when the brief requires a packaged product.

### `ANDROID-001` — repo-managed export surfaces

Owns:

- `export_presets.cfg`
- repo-local `android/` surfaces
- canonical export command recording

### `SIGNING-001` — signing prerequisites

Owns:

- signing mode decision if unresolved
- release keystore or CI secret reference ownership
- release artifact format selection

This ticket is only required when the brief requires packaged Android delivery beyond runnable debug proof.

### `RELEASE-001` — runnable and deliverable proof

Owns:

- runnable debug proof
- deliverable release proof when required by the brief

Recommended relationship:

- `RELEASE-001` may remain a split-scope child of `ANDROID-001`
- if packaged release is required, `RELEASE-001` also depends on `SIGNING-001`
- `RELEASE-001` must not close on debug proof alone when packaged delivery is required

## 5. What the Scaffold Must Emit

For a Godot Android repo, greenfield scaffold must stop at the first truthful package-owned surface, not at later warnings about a missing surface the package could have emitted itself.

Minimum owned scaffold output:

- parameterized `export_presets.cfg`
- canonical Android export command recorded in repo-local truth
- backlog lanes/tickets that match the repo goal

If signing inputs are unresolved, scaffold must encode them as blocked ownership, not as silent omission.

## 6. What Audit Must Detect

Audit should emit distinct findings for distinct failure classes.

### Missing repo-managed Android surfaces

Examples:

- no `export_presets.cfg`
- placeholder-only `android/` surface when the repo contract says that surface is owned

### Missing runnable proof

Examples:

- no debug APK after runnable Android work has started
- runnable export command still failing

### Missing deliverable proof

Examples:

- brief requires packaged Android product
- repo claims release or completion
- signing inputs or deliverable artifact are still absent

Audit must not collapse those into one generic Android warning.

## 7. What Managed Repair May And May Not Do

Managed repair may:

- regenerate `export_presets.cfg`
- regenerate repo-managed Android surfaces the package owns
- create or normalize the Android export, signing, and release tickets

Managed repair may not:

- fabricate keystores or secrets
- silently choose signing policy for the operator
- mutate gameplay code to chase export failures

If signing inputs are missing, repair should leave a truthful blocked state and the right follow-up tickets.

## 8. What the Harnesses Must Prove

### Greenfield verifier

Must fail when a declared Godot Android target is missing repo-managed Android surfaces.

### Smoke suite

Must include:

- a Godot Android repo missing repo-managed export surfaces
- a Godot Android repo with runnable proof only
- a packaged Android repo that still lacks deliverable proof

### Integration suite

Must prove:

- greenfield scaffold emits the owned Android surfaces
- repair regenerates owned Android surfaces
- packaged-product repos do not close on debug APK alone

## 9. Practical Design Rule

The package must always answer these questions separately for Android repos:

- what can the repo run now?
- what packaged artifact does the brief require?
- which missing inputs are repo-managed?
- which missing inputs are host-managed?
- which missing inputs are operator signing decisions or secrets?

If the package cannot answer those separately, the contract is still incomplete.
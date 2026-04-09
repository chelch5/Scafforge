# Host Boundaries And Repair Contract

This document replaces the earlier repo-remediation playbook. It keeps the useful boundary facts and removes the subject-repo edit instructions that do not belong in package planning.

## 1. The boundary problem that needed correction

The discarded draft mixed together three very different classes of work:

- repo-managed surfaces that Scafforge should scaffold and repair
- host prerequisites that Scafforge should detect but not fabricate
- source-level repo work that Scafforge should route into canonical tickets instead of editing directly from package planning

The package plan must keep those classes separate.

## 2. Ownership matrix

| Concern | Bootstrap / audit responsibility | Repair responsibility | Not safe for deterministic repair |
|---|---|---|---|
| `export_presets.cfg` | detect if missing | regenerate if the package owns it | no |
| repo-local `android/` support surfaces | detect if missing or placeholder | regenerate if the package owns them | no |
| Android SDK, Java, `javac`, Godot export templates | detect and report host blockers | preserve blocker truth in restart surfaces | yes |
| release keystore and signing secrets | detect missing ownership when deliverable proof requires them | create blocked signing follow-up, not secrets | yes |
| broken repo-local Python env | classify environment failure before source failure | keep verification truthful; route follow-up as needed | yes, if repair would require rebuilding subject-repo env state without explicit operator action |
| gameplay code, service code, or other source bugs | audit and classify | create canonical source follow-up tickets | yes |
| product art, audio, or other content work | compare repo claims to finish contract | create canonical finish follow-up tickets | yes |

## 3. Bootstrap and audit rules

Bootstrap and audit must tell the truth about which class of gap they are seeing.

### Repo-managed missing surfaces

Examples:

- no `export_presets.cfg`
- missing package-owned Android support surface

Required behavior:

- report these as package-owned repo-surface gaps
- do not blur them into generic host problems

### Host blockers

Examples:

- no Android SDK path
- no Java or `javac`
- no Godot export templates

Required behavior:

- report explicit host blockers
- do not claim repair can solve them by itself

### Source follow-up

Examples:

- gameplay or service code bug
- finish work still required by the canonical finish contract

Required behavior:

- route into canonical tickets
- do not let workflow repair pretend the repo is clean if those tickets are still required

## 4. Repair rules

Managed repair should be deterministic where the package owns the surface, and deliberately non-magical where it does not.

Repair may:

- regenerate workflow surfaces
- regenerate package-owned repo config surfaces
- normalize tickets and restart surfaces

Repair may not:

- invent keystores or secrets
- silently choose release-signing policy
- edit subject-repo product code to hide a package planning gap
- fabricate art, audio, or other creative content

When the missing thing is not safe deterministic repair output, repair must leave the repo in a truthful blocked or follow-up-required state.

## 5. Evidence-repo expectations under this boundary

### GPTTalker

Package behavior should be:

- classify broken repo-local Python env state correctly
- avoid misreporting that state as a source annotation bug
- keep repair focused on workflow surfaces, not direct service-code edits

### Spinner

Package behavior should be:

- treat missing Android export surfaces as package-owned repo-surface gaps
- distinguish that from host signing blockers
- route any missing finish work through the product-finish contract rather than through ad hoc commentary

### Glitch

Package behavior should be:

- fix the workflow deadlock at package level
- detect stale Godot config and Android repo-surface gaps
- route remaining source-level and host-level work truthfully after repair

## 6. Restart-surface rule

After this bundle lands, restart surfaces must stop collapsing these states together:

- repair completed successfully
- host prerequisites are still missing
- source-level or finish follow-up still exists

Those are different truths. The package contract should publish them separately.

## 7. Planning rule for future package work

If a package plan starts telling the operator to edit GPTTalker, spinner, or glitch directly, the plan has already crossed the wrong boundary.

The package plan must instead answer:

- what Scafforge should own directly
- what Scafforge should detect and report
- what Scafforge should route into canonical source follow-up
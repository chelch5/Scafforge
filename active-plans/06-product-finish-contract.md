# Product Finish Contract

This document defines the package-level answer to the user's strongest remaining objection: Scafforge currently has no explicit way to encode the difference between a working prototype and a finished product.

## 1. What the package is missing today

Current package behavior is strong on workflow structure and improving on runnable proof, but it still lacks a first-class finish contract for consumer-facing repos.

Verified package gaps:

- the canonical brief schema does not ask for placeholder policy, visual finish bar, audio finish bar, or content-source ownership
- backlog generation has no explicit finish lane or finish acceptance model
- audit has no contract-backed way to compare repo completion claims to finish expectations
- repair has no canonical route for saying "workflow is repaired, but product-finish work is still source follow-up"

Spinner is the clearest evidence case:

- it is playable today
- its visuals are procedural
- its asset directories contain only `.gitkeep`
- there are no runtime `res://assets/` references

That means the repo is functionally valid, but the package currently has no canonical way to answer whether this is the intended final product or only an unfinished interim presentation state.

## 2. What Scafforge should and should not promise

Scafforge should promise:

- the finish bar is explicit in canonical truth
- ownership for finish work exists in the backlog when needed
- audit compares completion claims against that explicit contract
- repair routes remaining finish work truthfully instead of publishing false-ready restart narratives

Scafforge should not promise:

- automatic creation of high-quality art or audio by package magic
- subjective aesthetic judgment without a recorded contract
- silent assumption that procedural or placeholder output is acceptable final output

The package goal is not "auto-beautify the repo". The package goal is "make the finish bar explicit, owned, and auditable".

## 3. Required canonical truth fields

Consumer-facing repos need a first-class `Product Finish Contract` section in the canonical brief.

Minimum fields:

- `deliverable_kind`
  - what the user expects at the end: service, internal tool, playable prototype, packaged mobile product, store-ready build, and so on
- `placeholder_policy`
  - whether placeholder or procedural output is acceptable as final output
- `visual_finish_target`
  - what visual bar counts as done for this repo
- `audio_finish_target`
  - what audio bar counts as done for this repo
- `content_source_plan`
  - where visuals, audio, and other creative content come from: custom authored, licensed pack, procedural-only, mixed, or intentionally none
- `licensing_or_provenance_constraints`
  - any constraints on generated, licensed, or bundled assets
- `finish_acceptance_signals`
  - the explicit signals that let audit and closeout know the finish bar was met

For internal tools and services, this contract may be intentionally minimal. For consumer-facing repos, leaving it blank must become a blocking decision rather than an implicit assumption.

## 4. Backlog ownership model

When placeholders are not acceptable final output, `ticket-pack-builder` must create explicit ownership for finish work.

The exact ticket IDs can stay project-specific, but the backlog must cover these responsibilities explicitly:

- finish direction or style decision if unresolved
- visual content production or integration
- audio content production or integration when required
- final finish validation against the recorded contract

What must stop happening:

- burying this work inside a generic `polish` bucket
- treating runnable software as finished product when the brief says otherwise
- leaving finish work as unwritten commentary outside the canonical backlog

## 5. Audit semantics

Audit should not guess whether a repo "looks good enough".

Audit should do three narrower, stronger things:

1. Read the finish contract.
2. Read the repo's current claimed completion state.
3. Compare the claim to the contract.

Examples of valid audit findings under the new contract:

- repo claims finished packaged product, but placeholder output is explicitly disallowed and the finish-owning tickets are still open
- repo claims finished product, but the finish contract requires audio deliverables and no owned audio proof exists
- repo claims finished product, but the finish contract itself was never resolved and remains a blocking decision

Examples of findings audit should not invent:

- "looks ugly" with no finish contract basis
- "empty asset folder means failure" when the finish contract says procedural-only output is acceptable final output

## 6. Repair semantics

Managed repair should consume the finish contract in a narrow way.

Repair may:

- regenerate managed workflow surfaces that encode finish truth
- create or normalize finish follow-up tickets when the audit already proved they are missing
- update restart surfaces so they stop claiming ready-state when finish work is still required by contract

Repair may not:

- generate art assets or audio content as a deterministic package action
- silently mark missing content work as complete
- rewrite source content decisions that were never resolved in canonical truth

The repair-side success condition is truthful workflow state, not fabricated finished-product content.

## 7. Two fixture modes are required

The harnesses need both of these cases:

### Mode A — procedural final is acceptable

Use this when the brief explicitly says the final product can be procedural or placeholder-light.

Expected behavior:

- audit does not raise a finish defect merely because the asset folders are empty
- backlog does not invent art/audio work that the brief explicitly said is unnecessary

### Mode B — procedural-only output is not acceptable final output

Use this when the brief says the repo must ship as a consumer-facing finished product.

Expected behavior:

- backlog contains explicit finish ownership
- audit flags premature completion claims if only placeholder/procedural output exists
- repair routes finish follow-up truthfully

Spinner-like evidence is exactly why both modes are necessary.

## 8. Relationship to Android delivery

This contract is separate from the Android delivery contract.

- Android delivery answers: can the repo produce the required runnable and packaged artifacts?
- Product finish answers: does the repo's content and presentation state match the final product bar recorded in canonical truth?

Both contracts are required for a consumer-facing mobile game. One cannot stand in for the other.

## 9. Package design rule

Scafforge must stop letting these three states collapse into each other:

- the repo runs
- the repo packages
- the repo is finished

The first two are technical execution bars. The third is a contract bar. This document defines how the package should carry that third bar.
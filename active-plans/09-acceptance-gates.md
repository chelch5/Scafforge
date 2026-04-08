# Acceptance Gates

This document defines what must be true before the rewritten `active-plans/` suite can be considered complete and trustworthy.

## 1. Package-level acceptance gates

All of these must be true:

1. The active defect list in `01-defect-register.md` matches current package code rather than historical commentary.
2. There is no separate corrections/addenda document; corrections are folded into the active documents.
3. There are no repo-local remediation playbooks in this directory.
4. The implementation plan names code, prompt, contract, and harness changes together for each active defect.
5. The verification suite requires executable coverage, not only static wording changes.

## 2. Behavior gates for the package itself

After the code changes described in this plan bundle land, Scafforge must be able to do all of the following:

- keep a split-scope parent foreground when the child is `sequential_dependent`
- recover deterministically from artifact-backed stale-stage drift
- scaffold and repair package-owned Android export surfaces
- distinguish Android runnable proof from Android packaged deliverable proof
- encode a finished-product contract for consumer-facing repos
- classify broken repo-local Python env state before source import failures
- reject remediation review without raw command-output proof

If any one of those still fails, this plan bundle is not done.

## 3. Evidence-repo expectations

These are package-behavior expectations, not instructions to edit the subject repos directly.

| Evidence repo | Fresh package behavior required | Must not happen |
|---|---|---|
| GPTTalker | fresh audit should classify the broken repo-local Python env as an environment problem before source import findings; repair should stay on workflow surfaces | package planning or repair must not mutate GPTTalker service code directly to hide the environment issue |
| Spinner | fresh audit should treat missing Android export surfaces as package-owned repo-surface gaps; if the brief requires a finished packaged product, the finish contract must prevent debug-only closure | package must not treat runnable gameplay or a future debug APK as automatic proof that the repo is a finished product |
| Glitch | fresh audit should catch the split-scope deadlock, stale Godot config, and missing Android export surfaces; fresh repair should resolve workflow-surface drift and route the rest truthfully | package must not leave the child foreground deadlock in place or require manual manifest hacking from the package plan |

## 4. What must no longer appear in the plan suite

These failure modes were present in the discarded draft and must stay gone:

- a separate corrections document
- repo-local copy-paste repair instructions for GPTTalker, spinner, or glitch
- claims that repair already provisions Android export surfaces
- claims that debug APK proof is enough for a packaged Android product
- vague "future ideas" instead of active package implementation work

## 5. Final sign-off rule

This rewrite is acceptable only if a future implementer can pick up this directory and answer three questions unambiguously:

1. Which Scafforge package files need to change?
2. What new package behavior must exist when those changes land?
3. How will the package prove the change with smoke, integration, or generated-verifier coverage?

If the documents in this directory do not answer those three questions clearly, they are not ready.
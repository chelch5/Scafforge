# Cross-Stack Generalization

The current evidence bundle comes from one Python service repo and two Godot Android repos, but most of the remaining package work is not Godot-specific.

## 1. Universal versus stack-specific defects

| Defect | Universal? | Notes |
|---|---|---|
| `WFLOW-LOOP-001` | yes | split-scope sequencing is a workflow-runtime problem, not a Godot problem |
| `WFLOW-STAGE-001` | yes | stale-stage recovery is a workflow-state problem, not a Godot problem |
| `PRODUCT-FINISH-001` | yes | any consumer-facing repo can confuse runnable with finished |
| `REF-SCAN-001` | yes | every stack has dependency or build trees that should not be audited as repo-owned source |
| `EXEC-ENV-001` | mostly yes | the current evidence is Python-specific, but the class of bug is broader: broken repo-local environments should be classified before source failure |
| `ARTIFACT-OWNERSHIP-001` | yes | coordinator artifact ownership is a generated-agent contract issue |
| `EXEC-REMED-001` | yes | remediation review needs executable proof regardless of stack |
| `ANDROID-SURFACE-001` | no | this specific repo-surface contract is Godot Android-specific |
| `TARGET-PROOF-001` | mostly no | the specific proof terms are Android-specific, though the runnable-versus-deliverable pattern generalizes |
| `PROJ-VER-001` | no | this is a Godot 4.x-specific project-version guard |

## 2. The universal patterns Scafforge should carry forward

### Workflow sequencing pattern

If the package supports open-parent decomposition, it needs explicit sequencing semantics.

That is true for:

- Android follow-up
- post-audit remediation splits
- backlog decomposition in any stack

### Runnable versus deliverable pattern

The package should not assume that a first runnable artifact is also the final deliverable artifact.

That is true beyond Android:

- a service can import successfully but still lack deployable packaging
- a game can boot and export debug output but still lack store-ready output
- a desktop app can build debug binaries but still lack signed distribution packaging

### Finished-product contract pattern

Consumer-facing repos need an explicit finish bar even when the stack is not Godot.

Examples:

- a web product may need real content, production styling, and asset provenance
- a mobile app may need store-ready assets, copy, and packaging
- a game may need art, audio, and presentation polish beyond functional interaction

### Repo-owned scan pattern

Reference-integrity and static repo scans should audit repo-owned truth, not dependency trees or build outputs.

That is universal across Python, Node, Rust, Go, Java, .NET, C/C++, and Godot.

### Evidence-first remediation pattern

Review and closeout should require raw command evidence, not prose alone, no matter which stack produced the original failure.

## 3. Adapter checklist for future Tier 1 stacks

When Scafforge promotes or extends a Tier 1 stack, the adapter work should answer all of these questions explicitly:

- what repo-managed build or export surfaces does scaffold own?
- what host prerequisites can bootstrap and audit detect but not fabricate?
- what counts as runnable proof?
- what counts as deliverable proof?
- when does the finish contract matter for this kind of repo?
- what scan exclusions are needed so audit only inspects repo-owned source?
- what remediation-review command evidence should be expected for this stack?

If a new stack adapter cannot answer those, it is not ready to behave like a first-class package contract.

## 4. Why this matters for the current bundle

The goal of this plan suite is not to overfit to Spinner and Glitch. It is to use those repos to close package holes that will recur anywhere else unless the contract becomes explicit.

That is why this bundle keeps:

- the workflow-runtime defects
- the finish-contract defect
- the audit/prompt evidence defects

and keeps only the Android-specific pieces that really are Android-specific.

## 5. Non-goal

Cross-stack generalization does not mean adding vague universal prose everywhere.

The package should generalize the contract shape, not hide the actual defect behind generic language.
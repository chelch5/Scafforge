# Agent Caller Prompts

## planchecker
{{COMMON_PLANCHECKER}}

Plan-specific focus:
- verify the plan replaces vague route labels with a real capability model
- check that provenance, license policy, workflow metadata, and QA surfaces are concrete
- confirm all asset assumptions stay free/open-source by default

## planimplementer
{{COMMON_PLANIMPLEMENTER}}

Plan-specific focus:
- implement the capability taxonomy, canonical asset state surfaces, provenance/compliance rules, and import/optimization QA
- prefer deterministic and curated routes before AI generation
- keep generated-repo asset truth machine-checkable

## planprreviewer methodology
{{COMMON_PR_REVIEW_METHODOLOGY}}

Plan-specific review focus:
- look for missing provenance fields, license-policy loopholes, or manifest/QA contradictions
- check whether the implementation really supports mixed asset sources in one truthful model
- confirm free-only assumptions are preserved

## planprreviewer big-pickle
Review PR #{{PR_NUMBER}} in {{OWNER_REPO}}. Use gh CLI to inspect the PR and post one top-level comment yourself.
Model emphasis: systemic provenance/compliance gaps, hidden unsupported asset routes, and contract drift between state surfaces.

## planprreviewer minimax-m2.7
Review PR #{{PR_NUMBER}} in {{OWNER_REPO}}. Use gh CLI to inspect the PR and post one top-level comment yourself.
Model emphasis: route selection coherence, fallback ordering, and lifecycle/state consistency for asset workflows.

## planprreviewer devstral-2512
Review PR #{{PR_NUMBER}} in {{OWNER_REPO}}. Use gh CLI to inspect the PR and post one top-level comment yourself.
Model emphasis: validator coverage, manifest handling, script correctness, and missing fixture cases.

## planprreviewer mistral-large-latest
Review PR #{{PR_NUMBER}} in {{OWNER_REPO}}. Use gh CLI to inspect the PR and post one top-level comment yourself.
Model emphasis: architecture quality, documentability, and whether the asset model stays navigable to weaker agents.

## planprreviewer kimi-k2.5-turbo
Review PR #{{PR_NUMBER}} in {{OWNER_REPO}}. Use gh CLI to inspect the PR and post one top-level comment yourself.
Model emphasis: practical usability, operator clarity, and whether the resulting pipeline would feel understandable in daily use.

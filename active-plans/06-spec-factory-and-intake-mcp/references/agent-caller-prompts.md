# Agent Caller Prompts

## planchecker
{{COMMON_PLANCHECKER}}

Plan-specific focus:
- verify the factory stays adjacent to Scafforge rather than being fused into package core
- check the state model, approval boundary, and ChatGPT/MCP ingress rules
- confirm ambiguous ideas become decisions, not silent assumptions

## planimplementer
{{COMMON_PLANIMPLEMENTER}}

Plan-specific focus:
- implement the spec-factory contract, intake object model, approval flow, and handoff boundary
- keep ChatGPT/MCP ingress bounded to transport/review, not hidden authority
- preserve `spec-pack-normalizer` as the package-side canonical brief contract

## planprreviewer methodology
{{COMMON_PR_REVIEW_METHODOLOGY}}

Plan-specific review focus:
- look for boundary violations between the spec factory and Scafforge package logic
- verify approval and decision states cannot be bypassed
- check that ingress/UI convenience does not become the hidden source of truth

## planprreviewer big-pickle
Review PR #{{PR_NUMBER}} in {{OWNER_REPO}}. Use gh CLI to inspect the PR and post one top-level comment yourself.
Model emphasis: systemic boundary collapse, bypassed approval flows, and hidden state/authority duplication.

## planprreviewer minimax-m2.7
Review PR #{{PR_NUMBER}} in {{OWNER_REPO}}. Use gh CLI to inspect the PR and post one top-level comment yourself.
Model emphasis: state-machine coherence, handoff lifecycle integrity, and ambiguous-input handling.

## planprreviewer devstral-2512
Review PR #{{PR_NUMBER}} in {{OWNER_REPO}}. Use gh CLI to inspect the PR and post one top-level comment yourself.
Model emphasis: concrete implementation gaps in schema handling, MCP/app wiring, and artifact flow.

## planprreviewer mistral-large-latest
Review PR #{{PR_NUMBER}} in {{OWNER_REPO}}. Use gh CLI to inspect the PR and post one top-level comment yourself.
Model emphasis: architecture clarity, documentation quality, and whether the new system remains maintainable.

## planprreviewer kimi-k2.5-turbo
Review PR #{{PR_NUMBER}} in {{OWNER_REPO}}. Use gh CLI to inspect the PR and post one top-level comment yourself.
Model emphasis: practical operability, approval UX clarity, and whether a user could trust the idea-to-spec flow.

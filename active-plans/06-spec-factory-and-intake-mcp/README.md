# Spec Factory And Intake MCP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Status:** TODO
**Goal:** Create a separate idea-to-spec system that can accept rough concepts, attachments, and prompts, turn them into Scafforge-ready brief material, and hand off approved outputs without weakening package boundaries.

**Architecture:** Build the spec factory as an adjacent workspace or service, not as hidden package logic. It owns intake, enrichment, drafting, decision packets, review, and approval state. Scafforge still owns normalization against its canonical brief contract and the actual greenfield scaffold. ChatGPT and MCP ingress should feed the factory through a reviewed workflow, not bypass it.

**Tech Stack / Surfaces:** adjacent spec-factory workspace or repo, MCP server, ChatGPT-facing app surface, package contract references, `spec-pack-normalizer`, `scaffold-kickoff`.
**Depends On:** `09-sdk-model-router-and-provider-strategy` should land before implementation. Contract design can begin now, but MCP and ChatGPT topology decisions are blocked until `09` is complete.
**Unblocks:** `07-autonomous-downstream-orchestration`, parts of the WinUI control plane, and user-facing idea intake.
**Primary Sources:** `_source-material/autonomy/hugeupgrade/ScafforgeAutonomousOrchestrationDRAFTPLAN.md`, `_source-material/autonomy/hugeupgrade/scafforgeautonomousnotes.md`, `skills/spec-pack-normalizer/references/brief-schema.md`, and current OpenAI Apps SDK / MCP patterns captured from live docs at implementation time.

---

## Problem statement

The “Spec Maker Workspace” currently exists as a concept, not an implementation contract. Without a defined state model and ownership boundary, idea intake will drift into one of two bad outcomes:

- raw ideas bypass review and become pseudo-specs
- the spec factory silently duplicates or mutates Scafforge’s canonical normalization logic

This plan exists to prevent both.

## Required deliverables

- a state machine for the spec factory
- an input object model for rough ideas, attachments, and references
- a clearly defined approved-output contract aligned to Scafforge’s canonical brief expectations
- a storage model for inbox, drafts, approvals, attachments, and decision packets
- a retrieval and indexing strategy for accumulated specs, attachments, and references that does not replace file truth
- a ChatGPT/MCP ingress design that still routes through review states
- package docs that explain where the factory ends and Scafforge begins

## Proposed factory state model

The factory should converge on an explicit workflow such as:

`inbox -> triage -> drafting -> decision-needed -> review -> approved -> handed-off`

Optional side states:

- `rejected`
- `needs-more-input`
- `superseded`

The critical rule is that `approved` is the only state allowed to make a handoff artifact eligible for generation.

## Approval authority rule

This plan should not allow autonomous self-approval by default.

- `approved` is human-gated by default in this cycle.
- Agents may draft, enrich, and recommend approval.
- Agents may not auto-transition an item into `approved` unless a future plan explicitly introduces and justifies an alternate approval policy.
- In-memory chat state is never sufficient for approval. The approved artifact must be persisted first.

## Package and adjacent surfaces likely to change during implementation

### Scafforge package surfaces

- `skills/spec-pack-normalizer/SKILL.md`
- `skills/spec-pack-normalizer/references/brief-schema.md`
- `skills/scaffold-kickoff/SKILL.md`
- `architecture.md`
- `AGENTS.md`
- new package reference docs describing spec-factory handoff contracts

### Adjacent workspace or service surfaces

- spec-factory workspace or repo layout
- MCP server for intake and artifact exposure
- ChatGPT-facing app or widget surface for idea submission and approval review
- storage model for inbox, drafts, approvals, attachments, and decision packets

## Ownership boundaries this plan must preserve

- The spec factory owns idea intake, research, creative expansion, drafting, and approval workflow.
- `spec-pack-normalizer` owns the package-side canonical brief normalization contract.
- Scafforge owns generation, ticketing, downstream repo scaffolding, and repair or audit loops.
- ChatGPT or MCP ingress is a transport and UI surface, not the authority for spec approval.
- The trigger that actually launches Scafforge generation belongs to the later orchestration layer from plan `07`, not to the spec factory itself.

## Storage model decision

The first implementation pass should use a file-backed workspace with machine-readable metadata, not a database-first design.

- canonical truth should live in durable, addressable files under the adjacent spec-factory workspace
- each item should have persisted draft, decision-packet, approval, and attachment-index artifacts
- machine-readable indices may summarize inbox state, but the approved artifact must remain an inspectable file that can be reviewed and versioned
- a retrieval layer such as embeddings or a vector index may be added later for search, reuse, and RAG-style drafting help, but it must remain a derived cache built from the file-backed artifacts rather than a new source of truth

This keeps the state easy to expose through MCP, easy to audit, and easy for agents to reason about.

## Approved-output contract rule

The approved output must be a committed, addressable artifact before any generation trigger is legal.

At minimum, the handoff bundle should persist:

- approved brief file
- approval metadata with timestamp and approver identity
- unresolved or deferred decision residue
- attachment index and attachment references
- provenance linking the approved brief back to the draft and source inputs

Transient chat approval or in-memory UI state is not sufficient.

## spec-pack-normalizer rule for approved factory briefs

When Scafforge receives an already-approved factory brief:

- `spec-pack-normalizer` should act as a validator-alignment pass, not as a second creative normalization pass
- it may validate schema alignment, detect malformed or missing required fields, and reject the handoff cleanly
- it must not regenerate a fresh decision packet for already-resolved blocking decisions unless the approved brief is malformed or inconsistent

This rule must be reflected in `spec-pack-normalizer` and `scaffold-kickoff` documentation when the plan is implemented.

## Invocation boundary decision

This plan defines the handoff artifact and the conditions under which it is eligible for generation.

- The actual external invocation mechanism that launches `scaffold-kickoff` should be owned by the orchestration layer in plan `07`.
- If a wrapper is needed, it belongs to that adjacent orchestration service, not to the spec factory contract itself.
- Plan `06` should therefore stop at “approved and addressable handoff bundle exists.”

## Phase plan

### Phase 1: Freeze the input, output, and storage contracts

- [ ] Define the intake object model for raw ideas, text notes, links, files, and reference assets.
- [ ] Define the minimum approved output schema and map it to `skills/spec-pack-normalizer/references/brief-schema.md`.
- [ ] Decide which fields may remain unresolved and must become explicit decision packets instead of silent guesses.
- [ ] Define the file-backed storage model for inbox, drafts, approvals, attachments, and decision packets.
- [ ] Define whether the factory also maintains a derived retrieval index over approved specs, attachments, and references, and if so keep it explicitly non-authoritative relative to the file-backed artifacts.
- [ ] Document exactly what metadata accompanies a handoff into Scafforge.
- [ ] Decide and document the validator-only behavior for `spec-pack-normalizer` when the input is an already-approved factory brief.

### Phase 2: Define internal factory roles and state transitions

- [ ] Split responsibilities between research, creative expansion, technical architecture drafting, and editorial normalization.
- [ ] Define who is allowed to transition an item into `decision-needed`, `review`, or `approved`.
- [ ] Keep `approved` human-gated by default and document the enforcement mechanism for that gate.
- [ ] Specify how conflicting agent outputs are reconciled and recorded.
- [ ] Define what evidence must be attached to an approved brief before handoff.

### Phase 3: Design the MCP and ChatGPT ingress surface

- [ ] This phase is blocked until plan `09` is complete enough to freeze Apps SDK, MCP, and ingress topology decisions.
- [ ] Define the MCP-facing intake operations: submit idea, attach files, inspect draft status, request approval view.
- [ ] Design the ChatGPT-facing app as an ingress and review surface rather than as the hidden source of truth.
- [ ] Follow current Apps SDK patterns for MCP server plus widget separation and keep the app bounded to intake and review flows.
- [ ] Ensure the ingress surface cannot bypass the state model and directly trigger generation without an approved persisted artifact.

### Phase 4: Define handoff semantics into Scafforge

- [ ] Specify the handoff artifact that the later orchestration layer receives once a brief is approved.
- [ ] Define the exact persisted bundle: brief, provenance, approval timestamp, decision-packet residue, and attachments.
- [ ] Ensure Scafforge can reject malformed or incomplete approved briefs cleanly.
- [ ] Define how rejected handoffs route back to the factory without corrupting state.
- [ ] Explicitly document that the runtime trigger to call `scaffold-kickoff` belongs to plan `07`, not to the spec factory itself.

### Phase 5: Validate the contract with short-idea scenarios

- [ ] Test a very short idea and ensure the factory produces a proper decision-rich brief instead of improvising too much.
- [ ] Test an ambiguous idea and ensure the factory emits a batched decision packet rather than guessing.
- [ ] Test an attachment-heavy idea and ensure references remain linked through approval and handoff.
- [ ] Confirm the approved artifact is sufficient for `scaffold-kickoff` and the validator-aligned `spec-pack-normalizer` path to consume.

## Validation and proof requirements

- the factory has an explicit state model and cannot skip straight from raw idea to scaffold
- approved outputs align to Scafforge’s canonical brief expectations
- ambiguous inputs produce visible decisions instead of silent assumptions
- ChatGPT/MCP ingress works as a bounded transport/review surface, not a workflow bypass
- every approved handoff is backed by a persistent, inspectable artifact bundle

## Risks and guardrails

- Do not embed the spec factory inside the Scafforge package repo.
- Do not duplicate `spec-pack-normalizer` logic; the factory should enrich inputs, not redefine package truth.
- Do not let chat-based convenience bypass approval and persistent artifact storage.
- Do not let agents auto-transition items into `approved` unless a later plan explicitly authorizes that behavior.
- Keep the factory’s role narrow enough that it can be tested independently from downstream generation.

## Documentation updates required when this plan is implemented

- a package reference explaining the spec-factory handoff contract
- `architecture.md` and `AGENTS.md` updates for the boundary
- operator docs for ChatGPT/MCP intake and approval flow
- downstream orchestration docs that describe how approved briefs arrive

## Completion criteria

- the spec factory has a real state model and handoff contract
- ChatGPT/MCP idea ingress is possible without boundary confusion
- approved outputs are acceptable to Scafforge
- ambiguous ideas remain visible as decisions instead of becoming pseudo-specs

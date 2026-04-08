# Scafforge Prevention Actions

## Package Changes Required

### ACTION-001

- source_finding: EXEC001
- change_target: generated repo implementation and validation surfaces
- why_it_prevents_recurrence: Tighten generated review and QA guidance so runtime validation and test collection proof exist before closure.
- change_class: safe package-managed workflow change unless a later human decision overrides scope or product intent.
- validation: rerun the generated-tool execution smoke coverage plus the relevant GPTTalker fixture family

### ACTION-002

- source_finding: REF-003
- change_target: generated repo reference integrity and configuration surfaces
- why_it_prevents_recurrence: Add reference-integrity checks and keep engine, config, and local-import paths aligned with real repo files before diagnosis or handoff treats the project as runnable.
- change_class: safe package-managed workflow change unless a later human decision overrides scope or product intent.
- validation: rerun contract validation, smoke, and integration coverage for the affected managed surfaces

### ACTION-003

- source_finding: WFLOW010
- change_target: repo-scaffold-factory generated workflow, handoff, and tool contract surfaces
- why_it_prevents_recurrence: Regenerate derived restart surfaces from canonical manifest and workflow state after every workflow mutation so resume guidance never contradicts active bootstrap, ticket, or lease facts.
- change_class: safe package-managed workflow change unless a later human decision overrides scope or product intent.
- validation: rerun contract validation, smoke, and integration coverage for the affected managed surfaces

### ACTION-004

- source_finding: WFLOW008
- change_target: repo-scaffold-factory generated workflow, handoff, and tool contract surfaces
- why_it_prevents_recurrence: Teach audit and repair to treat pending backlog process verification as a first-class verification state so repaired repos are not declared clean while historical done tickets remain untrusted.
- change_class: safe package-managed workflow change unless a later human decision overrides scope or product intent.
- validation: rerun contract validation, smoke, and integration coverage for the affected managed surfaces

## Validation and Test Updates

- EXEC001: rerun the generated-tool execution smoke coverage plus the relevant GPTTalker fixture family.

- REF-003: rerun contract validation, smoke, and integration coverage for the affected managed surfaces.

- WFLOW010: rerun contract validation, smoke, and integration coverage for the affected managed surfaces.

- WFLOW008: rerun contract validation, smoke, and integration coverage for the affected managed surfaces.

## Documentation or Prompt Updates

- WFLOW010: keep the docs, prompts, and generated workflow surfaces aligned with the repaired state machine.

- WFLOW008: keep the docs, prompts, and generated workflow surfaces aligned with the repaired state machine.

## Open Decisions

- None recorded.


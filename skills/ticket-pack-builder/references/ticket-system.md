# Ticket System Contract

Required files:

- `tickets/README.md`
- `tickets/BOARD.md`
- `tickets/manifest.json`
- `tickets/templates/TICKET.template.md`

Required ticket fields:

- `id`
- `title`
- `wave`
- `lane`
- `parallel_safe`
- `overlap_risk`
- `stage`
- `status`
- `resolution_state`
- `verification_state`
- `depends_on`
- `source_ticket_id`
- `follow_up_ticket_ids`
- `summary`
- `acceptance`
- `artifacts`
- `decision_blockers`

Optional ticket fields with controlled meaning:

- `source_mode` — one of `process_verification`, `post_completion_issue`, `net_new_scope`, or `split_scope`

Manifest contract:

- `tickets/manifest.json` uses `version: 3`
- `active_ticket` must reference a ticket that exists in the `tickets` array
- ticket objects must stay aligned with the runtime `Ticket` type in `.opencode/lib/workflow.ts`

Workflow-state seed contract for fresh scaffolds:

- `.opencode/state/workflow-state.json` seeds `bootstrap.status: "missing"`
- the foreground `active_ticket` in workflow-state matches `tickets/manifest.json`
- `ticket_state.<active_ticket>` exists with `approved_plan: false`, `reopen_count: 0`, and `needs_reverification: false`

Artifact registry contract:

- `.opencode/state/artifacts/registry.json` starts at `version: 2`
- artifact metadata is owned by the ticket entry in `tickets/manifest.json` and mirrored into `.opencode/state/artifacts/registry.json`

Recommended statuses:

- `todo`
- `ready`
- `plan_review`
- `in_progress`
- `blocked`
- `review`
- `qa`
- `smoke_test`
- `done`

Required initial values for new tickets:

- `stage: planning`
- `status: todo` or `blocked`
- `resolution_state: open`
- `verification_state: suspect`
- `artifacts: []`
- `follow_up_ticket_ids: []`

Lifecycle notes:

- `stage` is the lifecycle driver; `status` is the queue label derived and enforced by the workflow tools
- new tickets normally start at `stage: planning` with `status: todo` or `blocked`
- agents should not guess alternate stage/status pairs; `ticket_lookup` and `ticket_update` own that contract

Rules:

- keep queue status coarse and queue-oriented
- do not use ticket status for transient plan approval
- keep plan approval in workflow state or registered stage artifacts
- use `wave`, `lane`, `parallel_safe`, and `overlap_risk` to make cross-ticket concurrency explicit instead of implied
- keep `tickets/BOARD.md` human-readable only; do not turn it into a second state machine
- treat the manifest as the machine routing source and keep ticket files synchronized as detailed human-readable views
- keep artifact metadata on the owning ticket entry so the manifest acts as the primary artifact-routing record, while `.opencode/state/artifacts/registry.json` mirrors it for deterministic tooling
- during bootstrap, detail the first execution wave only where blocking decisions are resolved
- convert unresolved major choices into explicit blocked, decision, or discovery tickets instead of fabricating implementation detail
- keep acceptance commands scope-isolated; if a literal closeout command depends on later-ticket work, split the ticket or encode the dependency explicitly instead of shipping contradictory acceptance
- when canonical truth declares a Tier 1 release target, keep export and release-proof ownership explicit in the backlog instead of folding it into generic polish or validation tickets

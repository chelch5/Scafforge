# Scafforge Process Failures

## Scope

- Maps each validated finding back to the Scafforge-owned workflow surface that allowed it through.

## Failure Map

### EXEC001

- linked_report_1_finding: EXEC001
- implicated_surface: generated repo implementation and validation surfaces
- ownership_class: generated repo execution surface
- workflow_failure: One or more Python packages fail to import — the service cannot start.

### REF-003

- linked_report_1_finding: REF-003
- implicated_surface: generated repo reference integrity and configuration surfaces
- ownership_class: generated repo source and configuration surfaces
- workflow_failure: Source imports reference missing local modules.

### WFLOW010

- linked_report_1_finding: WFLOW010
- implicated_surface: repo-scaffold-factory generated workflow, handoff, and tool contract surfaces
- ownership_class: managed workflow contract surface
- workflow_failure: Derived restart surfaces disagree with canonical workflow state, so resume guidance can route work from stale or contradictory facts.

### WFLOW008

- linked_report_1_finding: WFLOW008
- implicated_surface: repo-scaffold-factory generated workflow, handoff, and tool contract surfaces
- ownership_class: managed workflow contract surface
- workflow_failure: Post-repair process verification is still pending, but the restart surfaces or legal next move contradict the canonical workflow state.

## Ownership Classification

### EXEC001

- ownership_class: generated repo execution surface
- affected_surface: generated repo implementation and validation surfaces

### REF-003

- ownership_class: generated repo source and configuration surfaces
- affected_surface: generated repo reference integrity and configuration surfaces

### WFLOW008

- ownership_class: managed workflow contract surface
- affected_surface: repo-scaffold-factory generated workflow, handoff, and tool contract surfaces

### WFLOW010

- ownership_class: managed workflow contract surface
- affected_surface: repo-scaffold-factory generated workflow, handoff, and tool contract surfaces

## Root Cause Analysis

### EXEC001

- root_cause: Runtime errors (NameError, FastAPIError, missing dependency, broken DI pattern, etc.) that are invisible to static analysis prevent module load. Common causes: TYPE_CHECKING-guarded names used in runtime annotations, FastAPI dependency functions with non-Pydantic parameter types, circular imports.
- safer_target_pattern: Verify every import succeeds: `python -c 'from src.<pkg>.main import app'`. Use string annotations (`-> "TypeName"`) for TYPE_CHECKING-only imports. Use `request: Request` (not `app: FastAPI`) in FastAPI dependency functions.
- how_the_workflow_allowed_it: One or more Python packages fail to import — the service cannot start.

### REF-003

- root_cause: At least one local import or require path no longer resolves to a file in the repo, so the runtime graph is internally inconsistent.
- safer_target_pattern: Audit local relative import paths and fail when the referenced module file is missing.
- how_the_workflow_allowed_it: Source imports reference missing local modules.

### WFLOW010

- root_cause: `START-HERE.md`, `.opencode/state/context-snapshot.md`, and `.opencode/state/latest-handoff.md` are not being regenerated from `tickets/manifest.json`, `.opencode/state/workflow-state.json`, and `.opencode/meta/pivot-state.json` after workflow mutations or managed repair, leaving bootstrap, repair-follow-on, pivot, verification, lane-lease, or active-ticket state stale.
- safer_target_pattern: Regenerate `START-HERE.md`, `.opencode/state/context-snapshot.md`, and `.opencode/state/latest-handoff.md` from canonical manifest, workflow state, and pivot state after every workflow save, compute handoff readiness from bootstrap plus repair-follow-on plus verification state in one shared contract, and fail repair verification if any derived restart surface drifts.
- how_the_workflow_allowed_it: Derived restart surfaces disagree with canonical workflow state, so resume guidance can route work from stale or contradictory facts.

### WFLOW008

- root_cause: The workflow contract changed, but the repo is still hiding, overstating, or deadlocking the pending backlog-verification state. That lets restart surfaces imply readiness before historical trust is restored, or leaves the workflow flag stranded after the affected done-ticket set is already empty.
- safer_target_pattern: Keep `pending_process_verification` visible, route the backlog verifier across the affected done-ticket set, expose `ticket_reverify` as the legal trust-restoration path, and when that affected set is empty leave a direct legal clear path for `pending_process_verification = false` instead of implying the repo is already clean or leaving the flag stranded.
- how_the_workflow_allowed_it: Post-repair process verification is still pending, but the restart surfaces or legal next move contradict the canonical workflow state.


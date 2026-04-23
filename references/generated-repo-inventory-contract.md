# Generated Repo Inventory Contract

This document freezes the minimum contract for orchestration-owned tracking of generated repos.

## Boundary

- Scafforge generates and repairs repos, but it does not own the cross-repo inventory for where those repos live or which host currently owns execution.
- The adjacent orchestration service owns tracked generated-repo inventory.
- The control plane consumes that inventory through backend APIs.
- Generated repo canonical truth remains inside each generated repo and must not be replaced by the inventory.

## Root policy

Generated repos are outside the ecosystem workspace by default.

- `Scafforge/` is for the ecosystem repos.
- A separate sibling root such as `ScafforgeProjects/` is the default host-local home for generated repos.
- Existing durable repos may be adopted from older locations without moving immediately, but the inventory still becomes their canonical tracking surface.

## Minimum record types

### `RepoRecord`

Required fields:

- `repo_id`
- `human_name`
- `git_remote`
- `repo_class` with `ephemeral` or `durable`
- `product_family`
- `lifecycle_state`
- `current_assigned_host`

### `HostRecord`

Required fields:

- `host_id`
- `host_kind` with `windows`, `wsl`, or `ssh-linux`
- `display_name`
- `connectivity_state`
- `worker_capabilities`

### `PathBinding`

Required fields:

- `repo_id`
- `host_id`
- `absolute_path`
- `path_role` with `primary`, `mirror`, `archived`, or `detached`

## Lifecycle states

The minimum lifecycle vocabulary is:

- `scaffolded`
- `active`
- `blocked`
- `archived`
- `ephemeral`
- `durable`

`ephemeral` and `durable` are class-like lifecycle markers that determine default operator views and cleanup posture. Systems may carry finer-grained runtime state, but they must not weaken these minimum distinctions.

## Registration rules

- Every scaffolded repo should enter the inventory.
- A repo may begin as `ephemeral` and later be promoted to `durable`.
- Existing repos such as `spinner`, `glitch`, `deephat`, or `womanvshorse*` may be adopted without being moved into `Scafforge/`.
- Path bindings may differ per host, and multiple bindings may exist for the same repo.
- Local folder scanning is not the canonical registration mechanism.

## Control-plane read model rule

The control plane may render inventory state, but it must not:

- invent the tracked repo set from local files
- rewrite lifecycle class by itself
- treat path presence on the Windows machine as proof that a repo is the active canonical target

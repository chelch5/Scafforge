# Example Inventory Records

These examples are illustrative scaffolding for plan `15`. They are supporting material, not the canonical contract.

## `RepoRecord`

```json
{
  "repo_id": "spinner",
  "human_name": "Spinner",
  "git_remote": "https://github.com/merceralex397-collab/spinner.git",
  "repo_class": "durable",
  "product_family": "game",
  "lifecycle_state": "active",
  "current_assigned_host": "wsl-main"
}
```

## `HostRecord`

```json
{
  "host_id": "wsl-main",
  "host_kind": "wsl",
  "display_name": "Local WSL Ubuntu",
  "connectivity_state": "healthy",
  "worker_capabilities": ["node", "python", "git", "godot"]
}
```

## `PathBinding`

```json
{
  "repo_id": "spinner",
  "host_id": "wsl-main",
  "absolute_path": "/home/pc/code/ScafforgeProjects/spinner",
  "path_role": "primary"
}
```

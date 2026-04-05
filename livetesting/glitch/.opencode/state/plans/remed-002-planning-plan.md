# REMED-002 Planning Artifact

## Finding Source
EXEC-GODOT-004 (headless validation failure caused by broken runtime initialization chain)

## Actual QA Blockers (from CORE-002 QA artifact)

### Blocker 1 — CRITICAL: GlitchEventManager never enters scene tree
- `GlitchSystemInitializer.gd` exists at `scripts/glitch/GlitchSystemInitializer.gd` but is **never invoked**:
  - Not registered as autoload in `project.godot`
  - Not added to `Main.tscn`
  - No code calls its `_ready()` method
- Impact: `GlitchEventManager.tscn` is never instantiated; its child modifier nodes (`PhysicsModifier`, `HazardModifier`, `RoomModifier`) do not exist at runtime

### Blocker 2 — CRITICAL: No path to GlitchPhysicsModifier at runtime
- `PlayerController.gd` lines 55–66 try two access paths, both fail:
  1. `get_node_or_null("/root/GlitchPhysicsModifier")` → fails (not an autoload)
  2. `event_manager.get_physics_modifier()` → fails (`event_manager` local var resolves to null because `GlitchEventManager` is not in tree)
- Impact: All 25 `physics_modifier` references in `PlayerController.gd` resolve to `null`; headless emits `WARNING: [PlayerController] GlitchPhysicsModifier not found`

### Blocker 3 — MODERATE: TelegraphEffect not wired to glitch_warning signal
- `TelegraphEffect.tscn` exists at `scenes/glitch/TelegraphEffect.tscn` but:
  - Never added to scene tree
  - No code connects `GlitchState.glitch_warning` signal to any handler
  - No `_process_glitch_warning()` handler exists in any scene
- Impact: Players receive no telegraph UI before glitch events

---

## Fix Approach

### Design Decision: Autoload registration (not scene composition in Main.tscn)

**Option A — Autoload registration for GlitchSystemInitializer** (chosen):
- Add `GlitchSystemInitializer` as an autoload in `project.godot`
- `GlitchSystemInitializer._ready()` self-initializes: finds or creates `GlitchEventManager`, adds it to tree, registers events
- Lowest risk: no Main.tscn structural changes, no introduction of new coupling

**Option B — Add GlitchSystemInitializer as a node in Main.tscn**:
- Requires editing Main.tscn
- Higher touch surface; more likely to conflict with future scene composition
- Rejected

**Option C — Register GlitchEventManager directly as autoload**:
- Would work for modifier access, but GlitchEventManager uses `@onready var physics_modifier: GlitchPhysicsModifier = $PhysicsModifier` which requires the node to be in the tree at `_ready()` time
- Instantiation order becomes fragile when mixed with autoload initialization sequence
- Rejected

**Option D — Register GlitchEventManager.tscn as autoload (singleton pattern)**:
- Add `GlitchEventManager="*res://scenes/glitch/GlitchEventManager.tscn"` as autoload
- Works: autoloads are added to `/root` as direct children
- Chosen for simplicity: no separate initializer node needed

**Chosen path**: Option D for GlitchEventManager autoload. GlitchSystemInitializer becomes unnecessary for initialization and can be removed or left as a no-op since it won't be called.

Wait — reconsidering. Option D (registering the scene directly) works cleanly in Godot: the scene's root node becomes the autoload singleton, and its `@onready` child references resolve correctly because all nodes enter the tree together during scene instantiation. This is the cleanest path.

**Revised choice**: Register `GlitchEventManager="*res://scenes/glitch/GlitchEventManager.tscn"` as autoload in `project.godot`. Remove GlitchSystemInitializer from consideration (it was a scaffolding attempt that never got wired up). This fixes:
- `PlayerController` fallback path `get_node_or_null("/root/GlitchEventManager")` succeeds
- `get_physics_modifier()` returns the real `PhysicsModifier` node
- All 25 physics_modifier references become functional

For TelegraphEffect wiring:
- Add a `_ready()` connection in `HUD.tscn`: `GlitchState.connect("glitch_warning", ...)`
- Create a handler in HUD that instances `TelegraphEffect.tscn` as a child and shows it

---

## Implementation Steps

### Step 1 — Register GlitchEventManager as autoload
Edit `project.godot`, add to `[autoload]` section:
```
GlitchEventManager="*res://scenes/glitch/GlitchEventManager.tscn"
```
This makes `GlitchEventManager` available at `/root/GlitchEventManager` from any script.

### Step 2 — Verify modifier access path in PlayerController
The fallback path in `PlayerController.gd` lines 55–66 already has the right structure:
```gdscript
physics_modifier = get_node_or_null("/root/GlitchPhysicsModifier")
if not physics_modifier:
    var event_manager = get_node_or_null("/root/GlitchEventManager")
    if event_manager:
        physics_modifier = event_manager.get_physics_modifier()
```
With `GlitchEventManager` as autoload, `get_node_or_null("/root/GlitchEventManager")` succeeds and `get_physics_modifier()` returns the real `PhysicsModifier` node. **No PlayerController code change required.**

### Step 3 — Wire GlitchState.glitch_warning to TelegraphEffect in HUD
Edit `scenes/ui/HUD.tscn` or its attached script:
- In `_ready()`: connect `GlitchState.connect("glitch_warning", self, "_on_glitch_warning")`
- Add `_on_glitch_warning(event_id: String)` handler that:
  1. Instances `TelegraphEffect.tscn` as a child of HUD
  2. Shows the warning label with event_id context
  3. Removes the telegraph node after ~2 seconds

### Step 4 — Clean up GlitchSystemInitializer (optional/safe)
- The file at `scripts/glitch/GlitchSystemInitializer.gd` is now dead code
- It is not registered as autoload and not in any scene — it has no effect
- Mark as deprecated in comment header, or delete; no functional impact either way

---

## Acceptance Criteria

1. **GlitchEventManager is an autoload**: `project.godot` contains `GlitchEventManager="*res://scenes/glitch/GlitchEventManager.tscn"` in `[autoload]` section

2. **Godot headless startup produces no GlitchPhysicsModifier warning**: `godot --headless --path . --quit` exits cleanly; log does not contain `WARNING: [PlayerController] GlitchPhysicsModifier not found`

3. **PlayerController accesses GlitchPhysicsModifier successfully**: At runtime, `PlayerController.physics_modifier` is non-null and is an instance of `GlitchPhysicsModifier`

4. **GlitchState signals are wired**: `GlitchState.emit_warning("test")` causes a `TelegraphEffect` node to appear in the scene tree under HUD

5. **All modifier children initialize**: `GlitchEventManager.physics_modifier`, `.hazard_modifier`, and `.room_modifier` are all non-null at runtime

6. **No crashes on startup**: Headless run completes with exit code 0

---

## Godot Headless Validation Plan

### Pre-fix baseline (current broken state)
```bash
godot --headless --log-file /tmp/glitch-before.log --path . --quit 2>&1 | grep -i "GlitchPhysicsModifier"
# Expected: WARNING: [PlayerController] GlitchPhysicsModifier not found
```

### Post-fix verification
```bash
godot --headless --log-file /tmp/glitch-after.log --path . --quit 2>&1 | grep -i "GlitchPhysicsModifier"
# Expected: (no match — warning gone)
grep "GlitchPhysicsModifier" /tmp/glitch-after.log
# Expected: [GlitchPhysicsModifier] Initialized  (or similar startup print)
```

### Broader headless checks
```bash
godot --headless --log-file /tmp/glitch-import.log --path . --import 2>&1
# Confirms scene import succeeds
godot --headless --path . --quit 2>&1
# Confirms clean startup
```

---

## Risks and Assumptions

| Risk | Assessment |
|------|------------|
| Autoload initialization order: GlitchState must exist before GlitchEventManager tries to use `emit_signal("glitch_warning")` | Safe: GlitchState is registered before GlitchEventManager in the [autoload] list |
| `@onready` in GlitchEventManager.tscn: $PhysicsModifier resolves correctly when scene is autoloaded | Safe: Godot resolves @onready relative to the scene root node at scene instantiation time |
| TelegraphEffect instancing: adding Node2D as child of HUD (CanvasLayer) | Safe: HUD is a CanvasLayer; adding a Node2D child is legal |
| PlayerController fallback path never tested with real GlitchEventManager | Low risk: code path is straightforward — get_node + method call |
| Removing GlitchSystemInitializer: it was never functional, no regression possible | Safe |

---

## Blockers / Required Decisions

None. The fix is fully scoped and low-risk:
- No architectural decisions required (autoload is canonical Godot pattern)
- No scene composition changes to Main.tscn
- No signal contract changes to GlitchState
- TelegraphEffect wiring uses existing HUD node and existing GlitchState signal
- All validation commands are executable immediately after changes

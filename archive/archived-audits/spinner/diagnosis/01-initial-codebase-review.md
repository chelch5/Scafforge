# 01 — Initial Codebase Review
**Spinner | Scafforge Audit | 2026-04-08**

---

## 1. Project Overview

Spinner is a Godot 4.x Android 2D touch-toy app for toddlers. The repo was scaffolded with
Scafforge using a full greenfield one-session path with MiniMax-M2.7. Six waves of ticket
work ran from environment bootstrap to release-readiness. As of this audit all gameplay
tickets are marked done; RELEASE-001 (Build Android debug APK) is the sole open ticket,
currently in `review` stage with verification_state: suspect.

---

## 2. Project Structure

```
spinner/
├── project.godot              ✓ Valid Godot 4.2 config
├── icon.svg                   ✓ Present
├── scripts/
│   ├── main.gd                ⚠ Stub only (extends Node2D, _ready passes)
│   ├── toy_box.gd             ✓ Working toy grid shell
│   ├── toy_button.gd          ✓ Working toy selection button
│   ├── toy_fan.gd             ✓ Desk fan toy
│   ├── toy_gear_board.gd      ✓ Gear board toy
│   ├── toy_helicopter.gd      ✓ Helicopter toy
│   ├── toy_pinwheel.gd        ✓ Pinwheel toy
│   ├── toy_washing_machine.gd ✓ Washing machine toy
│   ├── data/toy_registry.gd   ✓ Autoloaded ToyRegistry
│   ├── spinner/
│   │   ├── spinner_system.gd  ✓ Core physics system
│   │   └── input_detector.gd  ✓ Float-emitting signals
│   ├── audio/                 ⚠ Placeholder (.gitkeep only)
│   └── particles/             ⚠ Placeholder (.gitkeep only)
├── scenes/
│   ├── toy_box.tscn           ✓ Main scene (confirmed in project.godot)
│   ├── spinner_test.tscn      ✓ Dev validation scene
│   ├── toy_*.tscn (×5)        ✓ All five toy scenes present
│   └── main.tscn              ⚠ Stub / placeholder
├── android/
│   └── .gitkeep               ✗ EMPTY — no Gradle scaffold
├── build/android/             ✗ EMPTY — no APK artifact
├── assets/visuals/            ✗ Empty — no production assets
├── assets/audio/              ✗ Empty — no production audio
└── .opencode/                 ✓ Full Scafforge workflow layer present
```

---

## 3. GDScript Codebase Review

### 3.1 SpinnerSystem (scripts/spinner/spinner_system.gd)

**Status: GOOD.**

```gdscript
extends Node2D
class_name SpinnerSystem

signal spin_started()
signal spin_changed(angular_velocity: float)
signal spin_stopped()

@export var angular_velocity: float = 0.0
@export var angular_acceleration: float = 200.0
@export var max_angular_velocity: float = 1500.0
@export var friction: float = 0.97
@export var hit_radius: float = 150.0
```

- Typed signals (`float`) match the signal-type fix made in CORE-001 review
- `_was_spinning` boolean flag correctly replaces the `is_connected` anti-pattern fixed mid-CORE-001
- Physics model: `_current_velocity *= friction` per frame, clamped to `max_angular_velocity`
- `apply_impulse()` adds to velocity, emits `spin_started` when first activated
- 9 `@export` tuning variables as required by CORE-001 acceptance

**Minor observation:** `angular_velocity` is both `@export` and written by the physics process.
The `@export` makes it editor-configurable but it will be overwritten at runtime. Acceptable
for a toy but slightly confusing in the inspector.

### 3.2 ToyPinwheel (scripts/toy_pinwheel.gd)

**Status: GOOD.**

Signal wiring is complete:
- `InputDetector.tap_impulse → SpinnerSystem.apply_impulse(strength)`
- `InputDetector.drag_velocity → SpinnerSystem.apply_impulse(speed * 0.05)`
- `InputDetector.flick_release → SpinnerSystem.apply_impulse(impulse * 0.8)`
- `SpinnerSystem.spin_changed → SpinnerParticles._on_spin_changed`
- `SpinnerSystem.spin_started/changed/stopped → SpinnerAudio.*`

Procedural `_draw()` renders 8 sectors via `draw_polygon` with speed-scaled colour.

**Technical note:** Rotation approximation uses `spinner.angular_velocity * 0.01` as an
instantaneous visual offset rather than integrating position over time (`angle += vel * delta`).
The result is a colour-speed effect rather than true angular rotation, but it is visually
responsive and acceptable for a toddler toy.

Hit radius: 250px — large and forgiving. ✓

### 3.3 ToyGearBoard (scripts/toy_gear_board.gd)

**Status: GOOD.**

Gear configuration:
- Gear A (master): radius=80, red, 12 teeth
- Gear B: radius=50, blue — ratio = `R_A/R_B = 80/50 = 1.6×`, opposite direction
- Gear C: radius=40, green — ratio = `R_B/R_C` from B (double inversion = same direction as A)

Gear math is correct:
```gdscript
var angle_B: float = -master_angle * (GEAR_A_RADIUS / GEAR_B_RADIUS)  # 1.6× contra-rotating
var angle_C: float = -angle_B * (GEAR_B_RADIUS / GEAR_C_RADIUS)       # same direction as A
```

Speed-brightening via `body_color.v` adjustment. 250px hit radius. ✓

### 3.4 ToyBox (scripts/toy_box.gd)

**Status: ACCEPTABLE.**

```gdscript
func _on_toy_selected(toy: ToyEntry) -> void:
    if toy.scene_path.is_empty():
        return
    get_tree().change_scene_to_file(toy.scene_path)
```

This handler is defined but never wired to any signal — **dead code**. Scene navigation works
because `toy_button.gd` calls `get_tree().change_scene_to_file()` directly via
`get_parent().get_parent()` (the CORE-002 code smell flagged in review). Functional but the
`_on_toy_selected` method is unreachable. Does not affect runtime behaviour.

Mute and home buttons wired correctly.

### 3.5 main.gd

**Status: STUB.** Body is `_ready: pass`. The file was never developed. Main scene is
`toy_box.tscn` (confirmed in project.godot), so `main.tscn`/`main.gd` are unused scaffolding.

---

## 4. Godot Project Configuration

```ini
[application]
name="Spinner"
run/main_scene="res://scenes/toy_box.tscn"   ✓
config/features=PackedStringArray("4.2", "GL Compatibility")  ✓
config/icon="res://icon.svg"                  ✓

[autoload]
ToyRegistry="*res://scripts/data/toy_registry.gd"  ✓

[display]
window/size/viewport_width=1280               ⚠ Landscape default; portrait 720×1280 more
window/size/viewport_height=720                   typical for phone toddler apps
window/size/stretch_mode="canvas_items"       ✓

[rendering]
compatibility/compatibility/force_low_quality_mode=true  ✓ Target low-end Android
```

- `GL Compatibility` renderer: appropriate for broad Android device support ✓
- Viewport orientation: 1280×720 (landscape). Not a blocker but portrait orientation is more
  natural for most phone toddler apps. Note from CANONICAL-BRIEF that target is phones and tablets.

---

## 5. Android Build Surface — EXEC-GODOT-005: CRITICAL

### Finding: export_presets.cfg is ABSENT

**Confirmed:** File search across the entire repo found no `export_presets.cfg` at any path.

`export_presets.cfg` is mandatory for Godot Android export:
- Godot reads the named preset (e.g., `[preset.0]` with `name="Android"`) before any
  `--export-debug` invocation
- Contains: platform type, package name, keystore path, SDK paths, template selection
- Without it, `godot4 --export-debug "Android" output.apk` returns exit code 256 immediately

**Evidence from ticket history:**
- ANDROID-001 implementation (2026-04-01): "godot4 v4.6.1 confirmed on PATH, APK export
  attempted (exit code 256, export_presets.cfg absent — documented host gap)"
- ANDROID-001 QA: "2 FAIL (both documented host gaps — export_presets.cfg absent and resulting
  APK not produced)"
- RELEASE-001 review (2026-04-08): "Host gap (export_presets.cfg absent) correctly classified
  as external configuration gap, not code defect."

This finding has persisted from Wave 4 (ANDROID-001) through Wave 6 (RELEASE-001) without
resolution. Two complete ticket cycles reached the same wall.

### android/ directory state

```
android/
└── .gitkeep
```

The `android/` folder contains only `.gitkeep`. There is no:
- Gradle project (`build.gradle`, `settings.gradle`, `gradlew`)
- `AndroidManifest.xml`
- Keystore file (`.jks` or `.keystore`)
- Custom launcher activity modifications

In a Godot 4 Android export flow, the `android/` folder would normally be populated by
Godot's "Export Android Project" feature which extracts the Godot Android templates. Without
`export_presets.cfg`, that step was never triggered.

### APK artifact

`build/android/spinner-debug.apk`: **Does not exist.**

No APK has ever been successfully produced.

---

## 6. Reference Integrity (REF-003) — False Positive Assessment

REF-003 flags `.opencode/node_modules/zod/src/index.ts` importing `./v4/classic/external.js`.

**Classification: FALSE POSITIVE in Scafforge audit context.**

The `zod` npm package contains TypeScript source files that import compiled `.js` output
paths. These `.js` files are generated from TypeScript at build time and are not committed to
source trees. This is standard TypeScript package structure.

Impact on Spinner GDScript codebase: **Zero.**

The OpenCode tooling runs from pre-compiled node_modules. No Spinner product code has
missing imports. All five toy scripts resolve their `@onready` targets via scene node paths,
not import statements.

**Scafforge package note**: The REF-003 checker should exclude `**/node_modules/**` from its
import resolution scan.

---

## 7. Completeness Summary

| Component | Status | Notes |
|---|---|---|
| SpinnerSystem | ✓ Complete | Clean, typed, physics-correct |
| InputDetector | ✓ Complete | Float-typed signals throughout |
| ToyBox shell | ✓ Functional | Dead-code smell on `_on_toy_selected` |
| ToyRegistry | ✓ Functional | Data-driven registration pattern |
| Pinwheel | ✓ Complete | Good visual approach |
| Desk Fan | ✓ Complete | |
| Helicopter | ✓ Complete | Body wobble, rotor blur |
| Gear Board | ✓ Complete | Gear math correct |
| Washing Machine | ✓ Present | |
| SpinnerParticles | ⚠ Stub | audio/ and particles/ are .gitkeep only |
| SpinnerAudio | ⚠ Stub | No real audio assets |
| Production visuals | ✗ None | assets/visuals empty |
| Production audio | ✗ None | assets/audio empty |
| export_presets.cfg | ✗ ABSENT | Hard blocks all APK export |
| android/ Gradle | ✗ Empty | Scaffold placeholder only |
| build/android/spinner-debug.apk | ✗ None | Never produced |

---

## 8. Overall Health: GAMEPLAY GOOD, ANDROID BLOCKED

The GDScript gameplay foundation is in solid shape. Architecture is consistent, signal
types are correct, the toy pattern is reusable, and the five implemented toys are complete.
The scaffold infrastructure works.

The Android delivery surface is completely absent. The repo cannot produce an APK in its
current state. This is not a code quality failure — the GDScript source is exportable
in principle — but the Godot Android export configuration has never been established.

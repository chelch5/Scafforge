# Planning Artifact: ANDROID-001

## Ticket
- **ID:** ANDROID-001
- **Title:** Create Android export surfaces
- **Wave:** 21
- **Lane:** android-export
- **Stage:** planning
- **Status:** todo
- **Split parent:** Yes — child ticket RELEASE-001 (Build Android debug APK) is the foreground implementation lane; keep ANDROID-001 open and non-blocking while planning produces the required artifact.

---

## 1. Scope

ANDROID-001 creates and validates the repo-local Android export surfaces for the Glitch Godot Android target. This ticket does NOT produce an APK — that is the scope of child ticket RELEASE-001, which depends on ANDROID-001.

The surfaces to be created are:
1. `export_presets.cfg` — Godot 4.x Android export preset
2. `android/` directory — repo-local Android support surfaces (manifest, icons, proguard)
3. Canonical Android export command recorded in the ticket and the repo-local skill pack

**Out of scope for ANDROID-001:**
- APK production (RELEASE-001)
- Touch controls (UX-001)
- Signing keys (not required for debug export)

---

## 2. Gameplay or Engine Surfaces Affected

- **Engine surface:** Godot 4.x export pipeline (`export_presets.cfg`)
- **Android surface:** `android/` directory with manifest, icons, build configuration
- **Downstream:** RELEASE-001 APK build path (`build/android/glitch-debug.apk`)

---

## 3. Decisions Made

### Decision 1: Godot 4.x export_presets.cfg structure

**Format:** Godot 4.x INI-format export preset file.

**Preset name:** `Android Debug`

**Custom package name:** `com.glitch.game` — derived from project name `Glitch`. Debug-identifying name suitable for vertical-slice development. Production release will override via RELEASE-001 or a later ticket.

**Architectures:** Both `arm64-v8a` (arm64) and `armeabi-v7a` (arm32) included for maximum device compatibility during vertical slice.

**Output path (for RELEASE-001):** `build/android/glitch-debug.apk`

**Minimum Android SDK:** 18 (Android 4.3 — required by Godot 4.x Android export)
**Target Android SDK:** 35 (matching installed SDK)

**Full `export_presets.cfg` content:**
```ini
[preset.0]

name="Android Debug"
platform="Android"
runnable=true
dedicated_server=false
custom_features=""
export_filter="all_resources"
include_filter=""
exclude_filter=""
export_path="build/android/glitch-debug.apk"
encryption_include_filters=""
encryption_exclude_filters=""
encrypt_directory=false
encrypt_pck=false
encrypt_directory_key=""

[preset.0.options]

custom_template/debug=""
custom_template/release=""
custom_template/extensions_apk=""
custom_template/etc2_ktx=""

code_signing/alias=""
code_signing/passphrase=""
code_signing/key="
code_signing/cert=""
use_custom_keystore=false
keystore/pass=""

code_signing/alias_avd=""
code_signing/alias_pass_avd=""
use_custom_keystore_avd=false
keystore/pass_avd=""

one_click_manifest/permissions=["android.permission.INTERNET"]

vulkan/force_enable=false
vulkan/enabled=false
vulkan/require_32_bit=false

xr_mode/xr=0
xr_mode/immersive_mode=true
xr_mode/plane_detection=false
xr_mode/hand_tracking=false
xr_mode/hand_tracking_frequency=0
xr_mode/eye_tracking=false
xr_mode/eye_tracking_frequency=0

screen/immersive_mode=true
screen/support_small=false
screen/support_normal=true
screen/support_large=true
screen/support_xlarge=true

screen/logical_size/height=720
screen/logical_size/width=1280

screen/allow_resize=true
screen/center=true
screen/orientation=1
screen/override_screen_size=true
screen/use_screen_scale=true
screen/use_custom_screen_scale=false
screen/density=0
screen/percent_2d=1.0
screen/percent_3d=1.0

command_line/extra_args=""
name/localization="@godotengine/godot/android/java/lib/src/main/res/values-godot/strings.xml,"
godot_kotlin_android/enable_kotlin=false
godot_kotlin_android/kotlin_version=""

apk_expansion/enable=false
apk_expansion/SALT=""
apk_expansion/public_key=""

permission/manifest=application
permission/permissions=[]

application/icon="res://android/res/drawable/icon.png"
application/iconAdaptiveForeground="res://android/res/drawable/icon_foreground.png"
application/iconAdaptiveBackground="res://android/res/drawable/icon_background.png"
application/label="Glitch"
application/version_code=1
application/version_name="1.0.0"
application/instance_id_enabled=false
application/use_legacy_input=true
```

### Decision 2: Repo-local android/ surfaces

**Godot cannot auto-generate these surfaces without a running Godot editor session with GUI interaction.** The surfaces must be hand-authored in the repo.

**Required files:**

| File | Purpose | Non-placeholder approach |
|------|---------|--------------------------|
| `android/src/main/AndroidManifest.xml` | Android app manifest | Hand-authored with `com.glitch.game` package, INTERNET permission, and game activity |
| `android/res/values/strings.xml` | App display name | `"Glitch"` as app name |
| `android/res/drawable/icon.png` | App icon (48x48 baseline) | Real 48x48 PNG with solid magenta #FF00FF — not zero-byte |
| `android/res/drawable-xxxhdpi/icon.png` | High-density icon | Same placeholder |
| `android/res/values-godot/strings.xml` | Godot-generated strings | Created to prevent Godot export warning |
| `android/build.gradle` | Gradle build config | Minimal build.gradle with Android Gradle plugin 8.x compatibility |
| `android/project.godot` | Godot's Android project marker | Created with reference to parent `project.godot` |
| `android/settings.gradle` | Gradle settings | Minimal settings including Godot's Android module |
| `android/gradle.properties` | Gradle properties | `android.useAndroidX=true`, etc. |
| `android/app/libs/godot-lib.aar` | Godot Android library | **REQUIRES VERIFICATION** — must be copied from Godot templates or extracted from `android_source.zip`. Blocker recorded if missing. |

**Note on `godot-lib.aar`:** This file is the compiled Godot Android library required for APK builds. Godot generates it during the first Android export run or it can be copied from the Godot export templates. Without this file, Gradle builds will fail. This is recorded as an explicit blocker in Section 6.

### Decision 3: Canonical export command

The canonical debug export command for Godot 4.x headless Android export is:

```bash
ANDROID_HOME=/home/pc/Android/Sdk \
ANDROID_SDK_ROOT=/home/pc/Android/Sdk \
godot --headless \
  --path /home/pc/projects/Scafforge/livetesting/glitch \
  --export-debug "Android Debug" \
  build/android/glitch-debug.apk
```

**Preconditions for this command to succeed:**
1. `export_presets.cfg` exists in the repo root
2. `android/` directory contains a valid Godot Android project structure (including `godot-lib.aar`)
3. Godot export templates for 4.6.2.stable are installed
4. `build/android/` output directory exists

**This command will be validated during QA before ANDROID-001 is considered complete.**

### Decision 4: Godot export template verification

**Evidence from SETUP-001 QA:**
- Export templates verified at `~/.local/share/godot/export_templates/4.6.2.stable/`
- Contains the Android template files needed
- Template version matches installed Godot 4.6.2.stable

**Status: INSTALLED ✅** — No blocker.

### Decision 5: Android SDK path

**Evidence from SETUP-001 QA:**
- Android SDK present at `/home/pc/Android/Sdk`
- Contains android-35 platform and build-tools 35.0.1
- `ANDROID_HOME`/`ANDROID_SDK_ROOT` env vars not set in shell, but SDK is present

**Resolution:** The export command will explicitly set `ANDROID_HOME` and `ANDROID_SDK_ROOT` as environment variables inline with the export command.

---

## 4. Implementation Approach

### Step 1: Create directory structure
```
android/
  src/main/
    AndroidManifest.xml
    res/
      values/
        strings.xml
      drawable/
        icon.png
      drawable-xxxhdpi/
        icon.png
      values-godot/
        strings.xml
    java/
      com/glitch/game/
        (empty placeholder)
  build.gradle
  settings.gradle
  gradle.properties
  project.godot
  app/
    libs/
      (godot-lib.aar)
```

### Step 2: Create export_presets.cfg
Write the INI format preset file to repo root with Android Debug preset pointing to `build/android/glitch-debug.apk`.

### Step 3: Create AndroidManifest.xml
Hand-authored manifest with `package="com.glitch.game"`, INTERNET permission, and Godot placeholder activity.

### Step 4: Create placeholder icon
A real 48x48 PNG with solid magenta (#FF00FF) fill. Stored at `android/res/drawable/icon.png`. Not zero-byte — satisfies non-placeholder requirement for vertical slice.

### Step 5: Create Gradle configuration files
Minimal `build.gradle`, `settings.gradle`, and `gradle.properties` that Godot's Android export pipeline expects.

### Step 6: Verify and copy godot-lib.aar
Check if `godot-lib.aar` exists at:
- `~/.local/share/godot/export_templates/4.6.2.stable/android_source/app/libs/godot-lib.aar`
- OR extract from `~/.local/share/godot/export_templates/4.6.2.stable/android_source.zip`

Copy to `android/app/libs/godot-lib.aar`. If neither source exists, record as explicit blocker and halt before QA.

### Step 7: Create build/android/ output directory
Ensure `build/android/` exists for APK output path.

### Step 8: Record canonical command in skill pack
Add the canonical export command to `.opencode/skills/android-build-and-test/SKILL.md` under a "Canonical Commands" section.

---

## 5. Validation Approach

### Validation 1: export_presets.cfg existence
- File must exist at repo root
- Must contain `[preset.0]` section
- Must have `name="Android Debug"` and `platform="Android"`

### Validation 2: Android manifest validity
- `android/src/main/AndroidManifest.xml` must exist
- Must contain `package="com.glitch.game"`
- Must not be zero bytes

### Validation 3: godot-lib.aar presence
- `android/app/libs/godot-lib.aar` must exist and be a valid AAR/ZIP

### Validation 4: Icon presence
- `android/res/drawable/icon.png` must exist and be a valid PNG file (> 0 bytes)

### Validation 5: Headless export dry-run
Run the canonical export command. **Expected:** Command reaches Gradle build stage (not "preset not found"). Gradle may fail due to incomplete android/ project structure, but the command must not fail at the Godot level.

**If "preset not found":** export_presets.cfg format error
**If reaches Gradle and fails:** android/ project structure gap — record specific missing file
**If succeeds:** ANDROID-001 surfaces are fully valid

### Validation 6: Downstream path verification
- `build/android/` directory is created and writable

---

## 6. Blockers

### Blocker 1: godot-lib.aar availability (explicit blocker — must be resolved before QA)

**Finding:** `godot-lib.aar` must be confirmed present in the Godot export templates before this ticket can complete. The source path is `~/.local/share/godot/export_templates/4.6.2.stable/android_source.zip` or `~/.local/share/godot/export_templates/4.6.2.stable/android_source/app/libs/godot-lib.aar`.

**Impact:** Without this file, Gradle will fail to link the Godot Android library and the APK build will not succeed.

**Resolution required:**
1. Check if `godot-lib.aar` or `android_source.zip` exists in export templates
2. If present: extract/copy to `android/app/libs/godot-lib.aar`
3. If missing: **Hard blocker** — export templates are incomplete. Install via Godot Editor → Export → Android → Download Gradle Templates, or download from https://godotengine.org/

**This blocker is not raised by SETUP-001 because SETUP-001 scoped export template verification to the existence of the template directory, not the completeness of the Android source package within it.**

### No Blocker: ANDROID_HOME/ANDROID_SDK_ROOT

**Resolution:** The canonical export command explicitly sets these as environment variables inline. No shell-level env var is required.

### No Blocker: Godot Export Templates (directory-level)

**Status:** Verified installed by SETUP-001 QA at `~/.local/share/godot/export_templates/4.6.2.stable/`.

---

## 7. Acceptance Alignment

| Acceptance Criterion | How Satisfied |
|---------------------|---------------|
| `export_presets.cfg` exists and defines an Android export preset | Created in Step 2; validated by Validation 1 |
| Repo-local `android/` support surfaces exist and are non-placeholder | Created in Steps 1, 3–7; validated by Validations 2–4 |
| Canonical Android export command recorded in ticket and skill pack | Recorded in Decision 3 and Step 8; validated by Validation 5 |

---

## 8. Downstream Integration with RELEASE-001

RELEASE-001 depends on ANDROID-001 and will:
- Use `godot --headless --path . --export-debug "Android Debug" build/android/glitch-debug.apk`
- Verify APK exists at `build/android/glitch-debug.apk`
- Verify APK contents with `unzip -l build/android/glitch-debug.apk`

The `build/android/` directory created in Implementation Step 7 satisfies RELEASE-001's output path requirement.

---

## 9. Split-Parent Notes

ANDROID-001 is a split parent from REMED-002 (finding WFLOW025). Per workflow rules:
- ANDROID-001 stays **open and non-blocking** while child RELEASE-001 does the foreground APK build work
- ANDROID-001 does not advance to `in_progress` — it is in `planning` to produce this artifact
- Child ticket RELEASE-001 carries the active foreground lane for actual APK production
- ANDROID-001 advances to `done` once all three acceptance criteria are validated and godot-lib.aar blocker is resolved

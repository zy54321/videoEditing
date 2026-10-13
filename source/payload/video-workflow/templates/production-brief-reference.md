# Production Brief Reference (L4)

**Layer:** L4 — Production Brief  
**Template file:** `production-brief.yaml`  
**Version:** 1

---

## Purpose

The Production Brief answers:

> **What video does the Owner want to make?**

It expresses business intent and production requirements. It does **not** decide Runtime implementation routes, MCP actions, DRT vs live API, FFmpeg fallbacks, or DaVinci-internal parameters.

---

## Top-Level Sections

| Section | Role |
|---------|------|
| `version` | Brief schema version |
| `production` | Identity and intent |
| `editing` | L2 editing strategy selection |
| `media` | Input / output paths |
| `format` | Deliverable geometry and timing |
| `runtime` | NLE / backend preferences |
| `assets` | Voice, script, music with frozen semantics |
| `features` | Which finishing areas are in scope |
| `content` | Language and factuality constraints |
| `output` | Deliverable file policy |
| `notes` | Optional Owner notes |

---

## Field Semantics

### `production.id`

Stable production identifier.

Examples: `NEWS-2026-001`, `N03-austria-shopping`

**FIRST_RUN resolution** (governed by `production-entry-intake.mdc` §16):

1. Default candidate = Cursor Workspace **leaf directory name** (trimmed)
2. If unsuitable (`video`, `test`, `temp`, empty, etc.) → ask Owner for a short ID/name
3. **Do not** append date, GUID, or derive from media paths
4. **Do not** invent a business ID

Workspace name is a candidate only. Owner may override.

Once Brief is created, `production.id` is fixed. Repeat entry must not regenerate.

### `production.title`

Human-readable title. May be empty.

### `production.description`

Natural language: what video to make.

May express direction, narrative goal, tone, emphasis, special requests. **Not** for tool parameters.

### `editing.skill`

Must match an existing L2 Skill ID (e.g. `observational-info-short`).

L3 loads:

```
.cursor/skills/video-editing/<skill>/SKILL.md
```

If missing: `EDITING_SKILL_NOT_FOUND` — no fallback.

**Canonical display name** comes from the Skill frontmatter `display_name` (e.g. `生活观察 / 轻知识短视频`). Intake must not invent alternate names.

### `editing.creative_direction`

Optional array of Owner refinements to the **selected Style** — not a new Style.

Examples: `字幕更活泼`, `整体稍暖`, `少用夸张转场`.

- May be empty `[]` — do not force Owner to fill
- Style remains primary strategy
- Must not violate Safety Rules, Style identity, or Capability truth

### `content.authority`

Establishes **content semantics** authority (distinct from subtitle presentation).

| Field | Meaning |
|-------|---------|
| `content.authority.type` | `voice` \| `script` \| `subtitle` \| `owner` |
| `content.authority.path` | Primary file when type is voice/script/subtitle |

Resolved during Intake per `production-entry-intake.mdc` §12. Frozen semantics must not be altered; subtitle timing/layout may still adapt for presentation.

### `content.author_intent`

**Optional. Sole Owner Author Intent authority.**

Only for **Owner-explicit** expression intent — distinct from Style, `creative_direction`, and from L3-derived editorial / beat intent.

| Field | Meaning |
|-------|---------|
| `content.author_intent.global` | Whole-piece Owner intent string, or `null` when Owner did not provide |
| `content.author_intent.local` | Array of `{ beat_id, intent }` — Owner local intent; affects named beats only |

When Owner did not provide intent — **Owner Author Intent remains absent**:

- `global` remains `null`
- `local` remains `[]`
- **Do not** infer Owner Author Intent from Style, content authority, assets, or Agent reasoning

L3 may derive **editorial / beat-level intent** (`visual_intent`, `audience_effect`, etc.) from Style + content authority + assets. That derivation is **not** Owner Author Intent and must not be written into `content.author_intent`.

Edit Blueprint `author_intent` fields are a traceable snapshot / applied view of Brief — not a second authority. **Brief wins** on conflict.

Local Owner intent must **not** silently override entire Style identity.

### `production_options.review_before_edit`

When `true`: L3 pauses after Edit Blueprint summary for Owner review before Edit.

Default `false` — Blueprint summary is visible but **non-blocking**.

### `media.input`

Root directory for input media. Absolute path or workspace-relative.

L3 must resolve to a real path in Preflight.

### `media.output`

Deliverable output directory. **Not** assumed equal to `media.input`. Brief location does not imply media root.

### `format.orientation`

Allowed: `vertical` | `horizontal` | `square` | `custom`

Human intent. Authoritative dimensions are `format.width` and `format.height`.

If orientation conflicts with width/height: `BLOCK_BRIEF_CONFLICT` — do not guess.

### `format.width` / `format.height`

Target deliverable resolution (e.g. 1080 × 1920). Runtime must honor or report unsupported — no silent substitution.

### `format.fps`

Target frame rate. Not hardcoded to 24 in workflow logic.

### `format.target_duration_seconds`

Optional `min` and `max` (seconds). Both may be empty (no hard duration band).

If `min` > `max`: `BRIEF_INVALID`

### `runtime.type`

Runtime family. V0.1: `nle`. Future: `ffmpeg-only`, `other-nle`.

### `runtime.preferred_backend`

Owner/workspace backend preference. V0.1 default: `davinci-resolve`.

This is **backend identity**, not MCP package name, DRT, or live API route.

### `runtime.project_name` / `runtime.timeline_name`

Optional. Name existing NLE project/timeline, or leave empty for L3 to propose under policy. Must not overwrite existing projects without authorization.

### `assets.voice`

Voice Master or primary narration. `path` may be empty unless `frozen: true`.

When `frozen: true`: no regeneration, speed change, content edit, or replacement without new Owner authorization.

### `assets.script`

Frozen script source (markdown, txt, srt source, etc.).

When `frozen: true`: subtitle / transcription alignment uses Frozen Script as semantic authority.

**R1 runtime:** `content.authority.type = script` with `content.authority.path`, or `assets.script.frozen: true` with `assets.script.path`, feeds `build-canonical-subtitle-cues.py`. ASR JSON supplies timing evidence only; final cue text comes from Frozen Script, not ASR recognized text.

### `assets.music`

Optional music source. Two resolution modes (prefer library id for reusable tracks):

| Field | Meaning |
|-------|---------|
| `asset_id` | Shared Asset Library music id — resolved at runtime via `shared-asset-resolve` (machine-local root in `shared-asset-library-config.yaml`) |
| `path` | Direct file path (legacy / one-off Owner file, often under `media.input`) |

If both empty and `features.background_music: true`, L3 may query the Shared Asset Library catalog.  
If no READY asset matches → `MUSIC_ASSET_NOT_AVAILABLE` (asset supply gap).  
Do not download unknown-copyright music from the internet.

### `features`

Boolean scope flags — **what** is needed, not **how** to implement.

| Field | Meaning |
|-------|---------|
| `subtitles` | Run subtitle strategy per L2 |
| `background_music` | Run music/audio strategy per L2 |
| `transitions` | Apply L2 transition strategy (not “every cut must transition”) |
| `motion_normalization` | Check and correct abnormal motion |
| `framing` | Handle target frame / aspect |
| `color` | Basic color consistency |
| `graphics` | Extra titles / lower thirds / charts |
| `effects` | Extra visual effects |

**Priority:** Brief explicit `features.*` overrides L2 defaults. Safety Rules cannot be overridden by Brief.

If `features.background_music: false`, `assets.music.path` may still be set but workflow must not auto-use it.

If `features.subtitles: false`, L2 default “subtitles on” must not override Brief.

### `content.language`

Primary language (e.g. `zh-CN`, `en-US`) for subtitles, ASR, text handling.

### `content.factuality_sensitive`

When `true`: visuals and graphics must not mislead on facts. Typically `true` for news, observational, cultural, educational content.

### `output.filename`

Final deliverable filename (Required).

**Resolution** (governed by `production-entry-intake.mdc` §17):

- If Owner did not specify: default `<production.id>_V1.mp4`
- If `media.output` already has that file: try `_V2`, `_V3`, … (first unused)
- Set `output.overwrite_existing = false`
- Do not ask “文件名叫什么？” unless `production.id` is unresolved, Owner requests custom name, or safe auto-resolution fails

Render must re-verify target file does not exist.

### `output.overwrite_existing`

Default `false`. If target exists: version or `BLOCK` per Rules — no silent overwrite.

---

## Explicit vs Inferred

| Class | Examples | Policy |
|-------|----------|--------|
| **A. Owner authority** | `production.id`, `editing.skill`, frozen flags, width/height/fps, `features.*`, `overwrite_existing` | Agent must not change |
| **B. Inspectable** | File existence, current Resolve project/timeline, media metadata | May be filled from environment checks |
| **C. Derivable** | Consistency of `orientation` vs width/height | May validate; must not invent width/height from orientation alone when empty |

Template defaults (1080×1920, 24 fps) are **starting placeholders**, not silent inference when Owner leaves fields empty at validation time.

---

## Brief Validation Rules

### Required fields

- `production.id`
- `editing.skill`
- `media.input`
- `media.output`
- `format.width`
- `format.height`
- `format.fps`
- `output.filename`

### Conditional

| Condition | Rule |
|-----------|------|
| `runtime.type` = `nle` | `runtime.preferred_backend` should be present |
| `assets.voice.frozen` = `true` | `assets.voice.path` must be non-empty |
| `assets.script.frozen` = `true` | `assets.script.path` must be non-empty |
| `features.background_music` = `false` | `assets.music.path` may exist but must not be auto-used |
| `features.subtitles` = `false` | Subtitle pass must be skipped regardless of L2 default |

### Conflict checks

- `format.orientation` vs `format.width` / `format.height` → `BLOCK_BRIEF_CONFLICT`
- `format.target_duration_seconds.min` > `max` → `BRIEF_INVALID`

**Safety Rules** (crash boundaries, project isolation, frozen assets, overwrite policy) **cannot** be overridden by Brief.

---

## L4 → L3 Contract

L3 (`video-production` Skill) reads this Brief and maps dot-path fields directly:

| L4 path | L3 use |
|---------|--------|
| `production.id` | Identity, closeout |
| `editing.skill` | Load L2 Skill |
| `media.input` / `media.output` | Preflight paths |
| `format.*` | Deliverable spec |
| `runtime.*` | NLE target selection |
| `assets.*` | Frozen asset handling |
| `features.*` | Finish pass gating |
| `output.*` | Render target |

L3 does **not** read implementation routes from Brief.

---

## Example (minimal)

```yaml
version: 1

production:
  id: EXAMPLE-001
  title: Example observational short
  description: >
    A short observational information video about
    an everyday cultural habit.

editing:
  skill: observational-info-short

media:
  input: D:\Media\Example\input
  output: D:\Media\Example\output

format:
  orientation: vertical
  width: 1080
  height: 1920
  fps: 24
  target_duration_seconds:
    min: 60
    max: 90

runtime:
  type: nle
  preferred_backend: davinci-resolve
  project_name: Example-Project
  timeline_name: Example-V1

features:
  subtitles: true
  background_music: true
  transitions: true
  motion_normalization: true
  framing: true
  color: true
  graphics: false
  effects: false

content:
  language: zh-CN
  factuality_sensitive: true

output:
  filename: example-v1.mp4
  overwrite_existing: false
```

---

## Governed Intake & Brief Lifecycle

| Principle | Policy |
|-----------|--------|
| Creation | Brief is created **only** after governed Intake completes (`production-entry-intake.mdc`) |
| Location | `video-workflow/production/brief.yaml` |
| Paths | `media.input` / `media.output` come from **Owner-provided** paths, resolved to absolute at creation |
| Binding | After creation, paths are **stable** for this Production — not recomputed from date or workspace |
| Date | Workflow does **not** derive or manage date-based media directories |
| Instance | **One workspace → one Production**; another video requires a new workspace |
| Path change | Owner changes input/output → re-run Path Validation, Asset Audit, Preparation Gate |

Installer may create `video-workflow/production/` but **must not** pre-fill `brief.yaml`.

---

## What Brief Must Not Contain

Brief and this reference must **not** name:

- MCP tools or actions
- L1 implementation routes (`native_drt_*`, `live_api_*`, `ffmpeg_pre_attenuation`, etc.)
- Resolve scripting identifiers

Those belong to L1 / Runtime only.

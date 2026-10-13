---
name: video-production
description: Orchestrates an end-to-end video production from a Production Brief by loading the selected editing strategy skill, inspecting available runtime capabilities, planning the edit, executing production, verifying results, repairing ordinary defects, rendering, and closing out.
disable-model-invocation: true
---

# Video Production

This is the **L3 Production Workflow** of Video Editing Workflow.

## Governance

**Production Entry / Intake authority** is defined by:

```
.cursor/rules/production-entry-intake.mdc
```

L3 **MUST** obey that Rule. L3 must **not** bypass, weaken, or contradict it on:

- Standard entry (`【制作视频】`)
- Single-Production instance binding
- What must be asked vs inferred
- Path binding and date ownership
- Preparation Gate and auto-continue after READY
- Repeat entry behavior

This Skill implements execution steps **under** that Rule.

---

## Responsibilities

- Receive a Production Brief
- Confirm production context
- Load the corresponding L2 Editing Strategy Skill
- Confirm available Runtime / Capability
- Generate an Editing Plan
- Execute production
- QA
- Auto-repair ordinary defects
- Render
- Closeout

## Scope Boundaries

**This skill does not define genre-specific editing aesthetics.**

Genre-specific decisions belong to the selected **L2 Editing Strategy Skill**.

Tool-specific implementation knowledge belongs to **L1 capability knowledge** and the **active external runtime**.

L3 answers: *"What general production process should this task follow?"*

L3 does **not** answer:

- How to cut news, documentary, or vlog content
- Which DaVinci tool or MCP action to call
- Effect parameter libraries or preset aesthetics

---

## Invocation Contract

### Standard Product Entry (governed)

Per `production-entry-intake.mdc`, the standard Owner entry is:

```
【制作视频】
```

The Agent **must not** require `/video-production`, Skill names, or Brief paths for normal use.

### Advanced / Developer Invocation

```
/video-production
```

May be used when explicitly invoking this Skill directly. Still subject to `production-entry-intake.mdc` when the task is governed production.

### Brief Location (Single Production)

```
video-workflow/production/brief.yaml
```

One workspace → one Production. See `production-entry-intake.mdc` for FIRST_RUN vs CONTINUE_EXISTING.

### Startup Parsing

After governed Intake or on CONTINUE, parse from Brief:

- `production.id`
- `editing.skill`
- `editing.creative_direction` (optional refinements — not a new Style)
- `content.authority.*`
- `media.input` / `media.output`
- `format.*`, `runtime.*`, `assets.*`, `features.*`, `output.*`

**Do not** ask for Brief YAML fields that Intake already resolved.

---

## Preparation (execution under Rule)

Governed order is defined in `production-entry-intake.mdc`. L3 execution notes:

| Step | L3 action |
|------|-----------|
| TYPE_SELECTION | Enumerate `.cursor/skills/video-editing/*/SKILL.md`; map choice to `editing.skill` |
| PATH_COLLECTION | Parse natural language → `media.input`, `media.output` |
| PATH_VALIDATION | Verify input dir exists/readable; output parent writable; create empty output if authorized |
| ASSET_AUDIT | Read-only scan; classify assets; collect metadata |
| REQUIREMENT_CLASSIFICATION | Apply L2 + `features.*` + audit → REQUIRED_NOW / OPTIONAL / RESOLVABLE_DURING_PRODUCTION |
| NECESSARY_OWNER_CONFIRMATION | Frozen voice/script; content authority; music choice if needed |
| BRIEF_BUILD | Resolve `production.id` (§16) and `output.filename` (§17); fill `production-brief.yaml`; write absolute paths |
| PREPARATION_GATE | Verify all Required Brief fields; emit summary; on READY save Brief and enter Stage 0 automatically |

L3 **must not** enter Stage 0 before `PREPARATION_GATE = READY`.

---

## L4 → L3 Brief Contract

Full schema: `video-workflow/templates/production-brief.yaml`  
Reference: `video-workflow/templates/production-brief-reference.md`

L3 reads Brief fields by **dot path** (YAML nesting). Do not maintain a parallel flat field naming scheme.

### Required Brief Fields

| Field | Purpose |
|-------|---------|
| `production.id` | Stable production identity |
| `editing.skill` | L2 Skill to load |
| `editing.creative_direction` | Optional Owner refinements to selected Style (array; may be empty) |
| `content.authority.type` / `content.authority.path` | Content semantics authority when resolved |
| `media.input` | Input media root (resolved in Preflight) |
| `media.output` | Deliverable output directory |
| `format.width` | Target deliverable width |
| `format.height` | Target deliverable height |
| `format.fps` | Target frame rate |
| `output.filename` | Final deliverable filename |

### Conditional / Preflight Fields

| Field | When |
|-------|------|
| `runtime.type` / `runtime.preferred_backend` | Required when task depends on NLE |
| `runtime.project_name` / `runtime.timeline_name` | When targeting or creating NLE state |
| `assets.*.frozen` + `assets.*.path` | Frozen assets must have paths |
| `features.*` | Gates finishing passes; **overrides L2 defaults** when explicit |
| `format.orientation` | Must agree with width/height or `BLOCK_BRIEF_CONFLICT` |
| `format.target_duration_seconds` | Optional; `min` > `max` → `BRIEF_INVALID` |

Brief expresses **what** is needed. L3 selects **how** via L1 / Runtime — never from Brief.

### Missing Information Policy

If required information is missing: **do not invent values**.

| Class | Handling |
|-------|----------|
| **Owner authority** | `production.id`, `editing.skill`, frozen flags, format numbers, `features.*`, `output.overwrite_existing` — do not change |
| **Inspectable** | File existence, current project/timeline — may resolve in Preflight |
| **Derivable** | Orientation vs width/height consistency — validate only; do not infer empty width/height from orientation |

Safety Rules cannot be overridden by Brief.

---

## L3 → L2 Skill Loading Contract

This is the primary contract between L3 and L2.

### Brief Field

```yaml
editing:
  skill: <skill-id>
```

Example:

```yaml
editing:
  skill: observational-info-short
```

### Resolution Path

L3 resolves `editing.skill` to:

```
.cursor/skills/video-editing/<skill-id>/SKILL.md
```

In the installed target workspace. **Do not** hardcode developer-machine `source/` paths.

In the source payload, the equivalent path is:

```
source/payload/.cursor/skills/video-editing/<skill-id>/SKILL.md
```

### Loading Rules

1. Read the specified L2 `SKILL.md`.
2. Verify Skill identity matches the requested `editing.skill`.
3. Read that Skill's `references/` in the order specified by the L2 Skill (when provided).
4. Consult `video-workflow/knowledge/editing-craft/` for shared professional principles — Craft does not override Style.
5. Use the L2 Skill as strategy authority for:
   - pacing
   - shot grammar
   - motion strategy
   - transition strategy
   - subtitle strategy
   - music strategy
   - color strategy
   - graphics strategy
   - QA rules

### Missing L2 Skill

If the specified L2 Skill does not exist: **BLOCK**.

**Do not:**

- Automatically substitute another Skill
- Pretend a Skill was loaded using generic knowledge
- Silently fallback to "just cut something"

Report:

```
EDITING_SKILL_NOT_FOUND
```

---

## L3 → L1 / Runtime Contract

L3 does **not** assume any specific MCP tool name exists.

Before executing an action, prefer:

1. Tools exposed by the current runtime environment
2. L1 capability reference (when present)
3. Current Runtime's own tool / skill documentation

### Example Separation

| Layer | Responsibility |
|-------|----------------|
| L2 | Decides: "need short dissolve" |
| L3 | Puts that decision into the Editing Plan, asks Runtime for an available implementation, executes, verifies |
| L1 / Runtime | Knows how to implement it with current tools |

L3 must **not** hardcode specific MCP action names.

### Capability Unavailable

If Runtime cannot implement a required action:

1. Record: `CAPABILITY_UNAVAILABLE`
2. Decide impact:
   - Safe fallback allowed by Skill and does not change core production goal → use fallback
   - No safe fallback → **BLOCK**
3. **Do not** automatically install a second MCP.

---

## Aesthetic Decision Priority

When two legitimate editorial options conflict (after safety and factual integrity):

1. Author Intent (when provided in Brief)
2. Emotion / Audience Effect
3. Story / Information Progression
4. Rhythm
5. Visual Attention
6. Style Consistency
7. Technical Continuity

See also: `video-workflow/knowledge/editing-craft/aesthetic-qa.md` (four-level hierarchy).

---

## Production Pipeline

Unified workflow:

```
Preflight
  → Analyze
  → Understand Content / Intent
  → Build Beat Map
  → Apply L2 Style Decisions
  → Generate Edit Blueprint
  → Expose Blueprint Summary (default: non-blocking)
  → Capability Resolution
  → Plan Execution
  → Edit
  → Finish
  → QA
  → Repair
  → Render
  → Closeout
```

Different productions may:

- Skip inapplicable stages
- Enable additional internal actions
- Adjust order within allowed boundaries

But they still use this **same L3 workflow**.

---

## Stage 0 — Preflight

Preflight must complete before formal production begins.

**Prerequisite:** `production-entry-intake.mdc` Preparation Gate = **READY** and `video-workflow/production/brief.yaml` exists.

### Production

- Production Brief read
- `production.id` confirmed
- `editing.skill` confirmed

### Paths

- Input exists
- Output is usable
- Cursor workspace is not confused with media root

### Runtime

V0.1 Release is a **Workflow Installer** — not a full environment installer. It consumes **existing** external Runtime.

When the task depends on DaVinci / NLE backend:

- DaVinci Resolve is accessible
- Configured external DaVinci MCP is accessible
- Current Project identity can be confirmed

If unavailable: `BLOCK` → **`RUNTIME_NOT_READY`**

**MUST NOT:**

- Auto-download or install MCP
- Auto-modify `mcp.json`
- Auto-install DaVinci

Inform Owner: this Workflow Release only consumes an already-configured Runtime.

**FFmpeg / ffprobe:** check availability only when a capability route actually needs them (e.g. `ffmpeg_pre_attenuation`, render verify). If required and missing → `BLOCK` at that step only.

**Kokoro TTS:** check only when Production explicitly requires TTS. Missing Kokoro must **not** block all Productions.

### Assets

- Input media exists
- Frozen assets are locatable
- Frozen asset state is explicit

### Existing State

Inspect:

- Existing timeline
- Existing render
- Existing versions
- Output collision risk

### L2

- Editing Skill exists
- Editing Skill can be loaded

### Preflight Output

```
PASS
```

or

```
BLOCKED
```

If `BLOCKED`, do **not** enter Analyze.

---

## Stage 1 — Analyze

Goal: establish facts required for the Editing Plan.

Style decisions do **not** belong in Analyze.

### Media Analysis

As needed:

- duration
- resolution
- fps
- orientation
- audio presence
- source format
- representative visual inspection
- obvious slow motion
- content category
- quality problems

### Source FPS Distribution (mixed-source productions)

When multiple video sources exist, **MUST** record:

- per-clip or aggregate source fps distribution
- target timeline fps (from Brief)
- cadence / mismatch risk
- motion-heavy clip list

**MUST NOT** defer cadence assessment to post-render CFR metadata alone.

**Do not** make semantic judgments from filename alone.

### Voice / Dialogue

When present:

- Voice Master
- interview
- narration
- dialogue

As needed:

- transcription
- script alignment
- timestamp extraction

### Existing Timeline

For Repair / Continue tasks:

- Read current timeline state

### Capability Analysis

Confirm which capabilities may be needed and which are currently available:

- speed
- transform
- transition
- subtitle
- title
- audio
- color
- render

Analyze produces **evidence**, not aesthetic decisions.

---

## Stage 2 — Edit Blueprint

**Prerequisite:** Analyze complete.

### Flow

```
Understand Content
  → Load Owner Author Intent from Brief (if any)
  → Derive editorial / beat-level intent from Style + content authority + assets
  → Build Beat Map (beat-first, not default shot storyboard)
  → Write video-workflow/production/edit-blueprint.yaml
  → Emit concise Blueprint summary for Owner visibility
  → Continue unless blocked
```

### Blueprint Contract

- Template: `video-workflow/templates/edit-blueprint.yaml`
- Reference: `video-workflow/templates/edit-blueprint-reference.md`
- **Beat-first, shot-on-demand** — expand `shot_plan` only when beat complexity requires it
- **Must not** contain MCP method names or exact API calls
- **Not** a Runtime action plan

### Owner Visibility

Default: **NON_BLOCKING** — show summary, then proceed to Plan Execution.

**Block** only when:

- `production_options.review_before_edit: true`
- unresolved author intent
- high-impact ambiguity
- content authority conflict

### Owner Author Intent (Brief authority)

**Single authority:** `Production Brief.content.author_intent` — only for **Owner-explicit** expression intent.

| Brief state | L3 behavior |
|-------------|-------------|
| `global: null`, `local: []` | **Owner Author Intent remains absent** — do not populate Brief fields from inference |
| Owner provides `global` | Whole-piece Owner intent (within Style bounds) |
| Owner provides `local[]` | Per-beat `{ beat_id, intent }` — named beats only |

When Owner Author Intent is absent, L3 **derives editorial / beat-level intent** (`visual_intent`, `audience_effect`, `narrative_function`, etc.) from Style + content authority + assets. These derived fields are **not** Owner Author Intent and must not be written back to Brief as `author_intent`.

### Blueprint Author Intent fields (traceable snapshot)

Edit Blueprint `author_intent` fields are a **traceable applied view** of Brief (plus beat materialization). They are not a second Owner authority.

- **Brief wins** on conflict → regenerate or correct Blueprint
- Beat-level `author_intent` in Blueprint = materialized application to that beat, not new Owner authority

---

## Stage 3 — Capability Resolution

**Prerequisite:** Edit Blueprint complete (including `capability_requirements` where applicable).

### Inputs

- Edit Blueprint (`video-workflow/production/edit-blueprint.yaml`)
- L2 `capability-policy.yaml`
- L1 `video-workflow/capabilities/logical-capability-vocabulary.yaml`
- Analyze evidence

### Process

1. Collect logical capability IDs from Blueprint (global + per-beat)
2. Merge with L2 `capability-policy.yaml` for this Style
3. Query L1 canonical status per ID (see state matrix in `capability-resolution-reference.md`)
4. Resolve each requirement:
   - **VERIFIED** → may `SELECTED`
   - **AVAILABLE_UNVERIFIED** → **must not** direct `SELECTED`; use `CAPABILITY_VALIDATION_REQUIRED` or Style `FALLBACK` with recorded degradation
   - **UNKNOWN / FAILED / DEFERRED** → unavailable
   - **UNSAFE** → prohibited
   - **REQUIRED** + non-VERIFIED without safe path → `BLOCKED`
   - **PREFERRED** + non-VERIFIED → Style `fallback` with semantic metadata → `FALLBACK`; no fallback → unresolved / omit per policy
   - **OPTIONAL** + non-VERIFIED → `OMITTED`
5. Write `video-workflow/production/capability-resolution.yaml` including per-entry `effect_preservation`, `degradation_level`, `style_impact`, `reason` when fallback used
6. Emit Capability Coverage (mechanical derive from policy + vocabulary — not aesthetic score)

Template: `video-workflow/templates/capability-resolution-result.yaml`

**Must not** modify Owner Author Intent, silently change Style identity, or contain MCP / API names.

### Route truth (execution record)

Resolution and Plan must be able to distinguish:

| Field | Meaning |
|-------|---------|
| requested capability | Logical ID from Blueprint / policy |
| resolved capability | After Capability Resolution |
| planned route | Intended L1 / Runtime implementation path |
| actual executed route | What Runtime actually ran |
| route evidence | Read-back / artifact proof |

**Silent drift is a defect.** Example: planned `native_drt_subtitles` but executed `timeline_ai.create_subtitles` must be recorded and must not silent PASS.

---

## Stage 4 — Plan (Execution Planning)

Plan is the synthesis of:

```
Production Brief
+ Edit Blueprint
+ Capability Resolution
+ Analyze Evidence
+ L2 Editing Strategy Skill
+ Runtime Capability
```

### Required Plan Sections

#### Timeline

- target project
- target timeline / version
- resolution
- fps
- expected duration

#### Audio Structure

- narration / dialogue
- source audio
- music
- other required audio

#### Visual Assembly

Define by semantic segment:

- semantic purpose
- source
- source range or selection rule
- target range
- framing
- speed
- expected transition

#### Finishing

Per L2 Skill and Brief:

- motion normalization
- transitions
- subtitles
- titles
- music
- audio mix
- color
- graphics
- effects

#### QA Plan

Define what must be verified in this production.

### Plan Integrity

The plan must come from actual assets and the loaded L2 Skill.

**Do not** generate a polished but fictional plan unrelated to real media.

---

## Stage 5 — Edit

Edit establishes content structure and base assembly.

Typical actions:

- Project / Timeline preparation
- media ingest
- narration / dialogue placement
- B-roll / A-roll assembly
- source range selection
- clip timing
- framing
- basic speed decisions

### Edit Principle

First ensure:

```
content correctness
+ semantic correctness
+ pacing structure
```

Do **not** pile on finishing effects before structure is sound.

All write operations must follow existing Rules: **Write → Verify**.

---

## Stage 6 — Finish

Finish executes finishing passes according to:

```
Production Brief features
+ L2 Skill
```

### Possible Passes

#### Motion Pass

- motion normalization
- speed adjustment

#### Transition Pass

- hard cut
- dissolve
- strategy-selected transitions

#### Subtitle Pass

- **R1 authority chain (renderer-neutral):** Frozen Script = text authority; ASR = timing + alignment evidence only — `video-workflow/tools/build-canonical-subtitle-cues.py` → **Canonical Subtitle Cue list** (`canonical-subtitle-cue-list.schema.json`). Renderers (Native DRT / external ASS) **must consume** this list; they do not own subtitle text.
- **Mandatory gate (Frozen Script Production):** When `content.authority.type = script` **or** `assets.script.frozen = true` (and `features.subtitles` is enabled), subtitle production **MUST NOT** bypass Canonical Subtitle Cue. See **Frozen Script Subtitle Authority Gate** below.
- transcript / script alignment (monotonic global align — not line-count or whole-video proportional timing)
- subtitle segmentation (`subtitle.segment.semantic`) via existing `subtitle-layout-engine.ps1` / `subtitle-layout-preflight.ps1`
- Blueprint `subtitle_typography_intent` → styled runs (semantic emphasis targets only)
- L1 **subtitle layout preflight** (`video-workflow/tools/subtitle-layout-preflight.ps1`) when pixel-width discipline applies
- keyword emphasis (logical `subtitle.style.keyword_emphasis` **AVAILABLE_UNVERIFIED** for production): isolated StyledTextCLS SIZE route verified; production overlay not final — **first Production degradation** = native DRT subtitles + semantic segmentation (no keyword emphasis, no pixel-width parity guarantee)
- **readability profile** (`video-workflow/runtime/native-drt-subtitle-readability-profile.yaml`): production-safe default = white text + dark outer stroke on native DRT track; logical `subtitle.render.readability_stroke` is **VERIFIED** via Route A Subtitle Track `FieldsBlob` capture/inject + burn-in deliver QA; Inspector outer stroke remains fallback for one-off manual fixes
- do **not** use `fusion_comp.set_input(CharacterLevelStyling)` — **KNOWN_NON_WORKING_ROUTE**

**Layer split:** L2 / Blueprint decide *which words* deserve emphasis. L1 resolves font metrics, size multipliers, and layout. Runtime backend serializes materialized runs — not L2 Style details. Preflight PASS ≠ pixel-width renderer parity (`subtitle.layout.pixel_width` still AVAILABLE_UNVERIFIED).

##### Frozen Script Subtitle Authority Gate (R1 — MUST)

**Applies when:** `features.subtitles` is enabled **and** (`content.authority.type = script` **or** `assets.script.frozen = true`).

**Canonical Subtitle Cue is the only legal renderer input.** Fail closed — no fallback to ASR transcript text, Agent-generated subtitle copy, Frozen TXT line-number timing, or renderer-side re-segmentation of authority text.

**Ordered production route (MUST):**

1. Obtain ASR **timing evidence** (Resolve transcription route, MCP, or other authorized capture) and write `video-workflow/production/asr-timing-evidence.json` (ASR timing evidence contract).
2. Run `video-workflow/tools/invoke-frozen-script-subtitle-route.ps1` with `-WorkspaceRoot <cursor workspace>` **or** execute the same steps explicitly:
   - `build-canonical-subtitle-cues.py --brief video-workflow/production/brief.yaml --asr video-workflow/production/asr-timing-evidence.json --out video-workflow/production/canonical-subtitle-cues.json`
   - `validate-canonical-subtitle-authority-gate.py` → `video-workflow/production/subtitle-canonical-gate-result.json`
3. Require `SUBTITLE_CANONICAL_AUTHORITY_GATE = PASS` (`verdict: PASS` in gate result JSON).
4. **Before** Native DRT or external ASS materialization: run `assert-subtitle-renderer-canonical-input.ps1` — **BLOCK** on non-zero exit (bypass blocked).
5. Renderers consume **only** `canonical-subtitle-cues.json` (via `to_drt_subtitles()` / `to_ass_dialogue_lines()` adapters). **MUST NOT** feed ASR `recognized_text` or ad-hoc cue text into renderers.

**BLOCK (subtitle renderer MUST NOT run) when any of:**

- Frozen Script path missing or unreadable
- `asr-timing-evidence.json` missing
- `canonical-subtitle-cues.json` missing or stale vs current script/ASR
- Alignment `blocked` or `meta.status != OK`
- Gate `verdict != PASS`

Reference: `video-workflow/templates/subtitle-canonical-authority-gate-reference.md`

#### Graphics Pass

- titles
- lower thirds
- labels
- charts

#### Music Pass

- background music
- **Shared Asset Library** (Step 3A foundation + Step 3B-2 real assets): logical layer holds **`asset_id` only** — never absolute paths in Style, Brief, or Blueprint
- config: `video-workflow/runtime/shared-asset-library-config.yaml`
- catalog authority: `<shared_asset_root>/catalog/music.yaml` (machine-local; not bundled in release)
- **Execution chain (library boundary → runtime handoff):**

```
Production Brief / Style
        ↓
Music Requirement (mood / style / usage / energy / duration)
        ↓
music.library.search   → shared-asset-music-select.py
        ↓
music.library.select   → ranked READY candidates; top `asset_id` written to Brief `assets.music.asset_id`
        ↓
music.library.resolve  → shared-asset-resolve.py → absolute path (runtime only)
        ↓
audio.music.place      → VERIFIED (Resolve placement)
        ↓
audio.music.level_under_voice
```

- CLI: `shared-asset-music-select.py` (`--moods`, `--styles`, `--usage`, `--energy`) or `--requirement-json`
- if BGM required and no READY catalog match → `MUSIC_ASSET_NOT_AVAILABLE` (asset supply gap — **not** `audio.music.place` failure)
- **Forbidden:** random internet download; use REJECTED / UNVERIFIED assets; silent mismatch; silent BGM drop
- placement / level / fade still via **VERIFIED** `audio.music.place`, `audio.music.level_under_voice`, existing fade routes — do not reimplement placement
- looping / trimming
- section changes

#### Visual / Pacing QA Pass (Step 4B)

- pacing profile: `runtime/informational-short-pacing-v1-profile.yaml`
- black-bar profile: `runtime/black-bar-reframe-qa-profile.yaml`
- Blueprint `assembly_plan.shots[]` must carry `beat_id`, `shot_id`, `source_asset`, `source_range`, `timeline_duration_sec`, `reframe`
- pacing: `pacing-qa.py` — `>6s` warning, `>10s` unchanged cross-beat span → `PACING_REPAIR_CANDIDATE`
- repair priority: `clip.source_range` + `clip.assemble` — **not** push-in / pan / ResolveFX first
- black-bar loop: assemble → `visual.reframe.static` → `black-bar-qa.py` → `REPAIR_REQUIRED` → adjust scale/position → **re-QA** (max 3 attempts)
- post-render: `final-artifact-qa.ps1` embeds `black-bar-qa.py` — `REPAIR_REQUIRED` / `REFRAME_OWNER_REVIEW_REQUIRED` = fail-closed
- do **not** treat detector VERIFIED as Production closure without repair loop

#### Audio Mix Pass

- profile: `video-workflow/runtime/narration-short-v1-audio-mix-profile.yaml` (`narration_short_v1`)
- narration priority — voice primary, music supporting
- music: continuous BGM across narration pauses (low bed) — **not** dynamic ducking
- `audio.music.level_under_voice` via `ffmpeg_pre_attenuation` — measure voice/music LUFS when possible; fallback factor `0.15` (verified spike)
- `audio.music.duck` remains **UNKNOWN** — do not claim VERIFIED
- post-render loudness QA: `audio-loudness-qa.py` / `final-artifact-qa.ps1` audio section
- post-render loudness repair: `final-audio-loudness-repair.py` + `final-artifact-audio-qa-repair.ps1` (measure/repair separate)
- `FINAL_AUDIO_AUTO_REPAIR` = **VERIFIED** — ffmpeg loudnorm two-pass; max **1** attempt; `NO_REPAIR_REQUIRED` when already PASS; `FINAL_AUDIO_REPAIR_FAILED` fail-closed

#### Color Pass

- correction
- matching
- genre-appropriate look

#### Effects Pass

Only when Brief / L2 Skill requires it.

### Pass Skipping

Not every production runs every pass.

Examples:

- `subtitles: false` → skip Subtitle Pass
- `music: false` → skip Music Pass

---

## Stage 7 — QA (Pre-Render)

**Pre-Render QA only.** Final Artifact QA runs **after** Render (see below).

QA has **three** subtitle-relevant layers when captions are enabled:

1. **Pre-render Layout Preflight** — L1 measured width, line count, safe width, content preservation, emphasis width impact, `CUE_SPLIT_REQUIRED`, font resolution (see `subtitle-layout-reference.md`)
2. **Timeline / Route QA** — timeline state + planned vs actual route identity
3. **Post-render Artifact QA** — actual pixels in deliverable (`final-artifact-qa.ps1` + vision where applicable)

**Preflight PASS ≠ Final Artifact PASS.** Timeline subtitle population alone is **not** deliverable subtitle PASS.

Pre-render also has **two** general layers. **Timeline State QA ≠ Final Artifact QA.**

### 5A — Timeline State QA

Inspect current NLE timeline / project state:

- Frozen asset integrity
- no unintended timeline gaps
- clip counts / ranges
- transform read-back (supplementary only)
- subtitle track population (not sufficient alone)

### 5B — Universal QA

From Cross-cutting Rules:

- output identity
- no unintended overwrite
- no unexplained black frames on timeline
- target resolution / fps settings
- expected duration
- audio presence
- no destructive source mutation

### 5C — Genre / Style QA

From the loaded L2 Editing Skill (`references/08-qa.md` — Style Fidelity; technical QA separate).

Examples:

- pacing, motion normalization (**MUST** when L2 requires)
- mixed-fps cadence assessment
- subtitle layout + intentional gaps
- music behavior (`OWNER_DISABLED` when Owner chose no music)
- factual visual alignment
- Style-level extensions (OBS-QA-FINAL-RENDER, etc.)

### Final Artifact QA — NOT in Stage 7

Do **not** run Final Artifact QA before Render. See **Post-Render Final Artifact QA** (after Stage 9 Render).

QA must be based on **actual results**.

Passing execution steps without error is **not** sufficient for QA PASS.

---

## Stage 8 — Repair

When QA finds an ordinary defect:

```
Classify → Repair → Re-run affected QA
```

Ordinary repair does **not** wait for Owner.

Examples:

- 1-frame gap
- black frame
- bad crop
- incorrect source range
- too-slow clip
- subtitle timing
- typo
- missing transition
- music too loud
- render retry

### Repair Retry Policy

Repair loops must have a limit.

**V0.1 default:**

Each defect class may be auto-repaired at most **3 times**.

If still failing after 3 attempts:

```
BLOCK
```

and output evidence.

**No infinite repair loops.**

---

## Stage 9 — Render

Render only after **Pre-Render QA** (Stage 7 Universal + Genre) reaches render-ready state.

### Pre-Render Confirmation

- project
- timeline
- duration
- resolution
- fps
- output path
- filename
- collision policy

### Post-Render Verification

- file exists
- duration
- resolution
- fps
- video stream
- audio stream
- codec / format when relevant

If render output is invalid: enter Repair.

---

## Post-Render Final Artifact QA — MUST

**Order (mandatory):**

```
Pre-Render QA → Render → Post-Render Final Artifact QA → Repair (if needed) → Re-render → Post-Render QA
```

After a valid render file exists, verify the **actual MP4** — not timeline-only state.

Use `video-workflow/tools/final-artifact-qa.ps1` when FFmpeg/ffprobe available. Outputs go to `video-workflow/.qa/` only.

**Technical:** exists, duration, width/height, fps, codec, audio stream.

**Visual:** black bars (`black-bar-qa.py` / `qa.visual.black_bar_detect` — verdicts `PASS` | `REPAIR_REQUIRED` | `REFRAME_OWNER_REVIEW_REQUIRED`), framing, subtitle visibility/overflow (`final_render.subtitle_visual_qa`), gross crop, unintended blank frames. Findings must cite `beat_id` / `shot_id` / `source_asset`.

**Motion:** abnormal slow motion, judder — `MOTION_VISUAL_REVIEW_REQUIRED` when needed.

**Audio:** `final-artifact-qa.ps1` now includes `audio_loudness_qa` via `audio-loudness-qa.py` against `narration_short_v1` profile.

Verdicts: `PASS`, `LOUDNESS_TOO_LOW`, `LOUDNESS_TOO_HIGH`, `TRUE_PEAK_EXCEEDED`, `NO_AUDIO`.

Target: **-16 LUFS** (±1 LU), true peak **≤ -1 dBTP**. N02 V4 reference ≈ -24.8 LUFS (too low) — do not silently pass.

`FINAL_AUDIO_AUTO_REPAIR` = **VERIFIED** — use `final-artifact-audio-qa-repair.ps1` after render when loudness QA fails; do not mutate artifact inside QA-only tools.

`render.verify_output` PASS alone **does not** equal Production PASS.

If Agent cannot perform visual review: `FINAL_VISUAL_QA_REQUIRES_OWNER_REVIEW` — **no fake PASS**.

---

## Stage 10 — Closeout

Closeout is more than "video generated successfully."

### Required Structured Output

#### Identity

- production.id
- editing.skill
- runtime
- project
- timeline

#### Inputs

- input media count
- frozen assets

#### Execution

- stages executed
- stages skipped
- reasons for skip

#### Editing

- used media count
- clip count
- major semantic mapping

#### Finishing

For each area, state one of:

`EXECUTED` | `SKIPPED` | `PARTIAL` | `BLOCKED`

Areas:

- motion
- transitions
- subtitles
- music
- audio
- color
- effects

#### QA

- checks
- defects
- repairs
- remaining issues

#### Output

- render path
- render verification

#### Final State

Use only:

- `READY_FOR_OWNER_REVIEW`
- `BLOCKED`
- `FAILED`

**Do not** use vague conclusions such as "should be fine" or "looks successful."

---

## Continuous Execution Contract — MUST

**Truth label:** `PRODUCTION_CONTINUOUS_EXECUTION` — contract defined here; runtime Agent behavior is verified by Production evidence, not by this document alone.

Governance authority also in `video-workflow-core.mdc` §12.

### Authorization model

Once Owner completes governed Intake and `PREPARATION_GATE = READY` (or on `CONTINUE_EXISTING` with valid Brief), **Production Authority inherits** to all steps in the authorized Production Plan for **this** Production / Brief scope.

**Inherited without re-asking `继续`:**

| Domain | Examples |
|--------|----------|
| Workspace / files | production workspace reads/writes under bound paths |
| Inspection | media audit, runtime inspect, read-back |
| Planning | blueprint, capability resolution, execution plan |
| Editorial | source-range decisions, assemble, trim-by-range, cuts |
| Runtime | Resolve project/timeline, clips, subtitles, audio, visual treatment |
| Delivery | render, verify, final-artifact QA, closeout |
| Repair | ordinary defect repair per Repair Policy |

Intake-only Owner gates (type, paths, frozen assets, music choice when required) **do not** repeat after Brief exists.

### Authorized pipeline (single continuous run)

```
Preflight
  → Analyze
  → Understand Content / Intent
  → Build Beat Map
  → Apply L2 Style Decisions
  → Generate Edit Blueprint
  → Expose Blueprint Summary (default: non-blocking)
  → Capability Resolution
  → Plan Execution
  → Edit
  → Finish
  → QA
  → Repair
  → Render
  → Post-Render Final Artifact QA
  → Closeout
```

**Analyze must not bypass Edit Blueprint or Capability Resolution** to reach Plan or Edit.

### Execution mode — default

```
CONTINUE_AUTONOMOUSLY
```

While authorized work remains and no pause condition applies, L3 **MUST**:

1. Execute the next legal step
2. Verify when the step requires write → verify
3. Proceed to the following step **in the same Agent turn when platform allows**

**MUST NOT** end the turn with:

```
WAIT_FOR_OWNER_CONTINUE
```

### Forbidden turn endings

If a legal next step exists, **do not** use a final user-facing message as a substitute for executing it.

**Forbidden as turn terminators:**

- “下一步我会继续……” / “I will continue next…”
- “我会继续做完” / “No need to send 继续”
- “接下来进行字幕 / 导出 / Render…”
- “还剩 X 项” / progress-only checklist with no tool call
- “当前进度如下……” as the closing action

Progress may be logged inline or in production state notes. **Progress ≠ pause.**

### Only allowed pause outcomes

| Outcome | When | Required payload |
|---------|------|------------------|
| `BLOCKED` | Required file missing; Runtime crash/unavailable; failed call with no legal fallback; corrupt artifact; permission genuinely blocks execution | blocker id, attempted actions, why auto-continue impossible, minimal Owner input |
| `OWNER_DECISION_REQUIRED` | Frozen Voice change; topic/立意 change; new third-party asset needing authorization; materially different creative fork | decision needed, options, default if Owner defers |
| `AUTHORIZATION_REQUIRED` | Action outside current Brief / Production scope | what is out of scope, what authorization is needed |

**Completion** (`READY_FOR_OWNER_REVIEW` / closeout) is allowed only when the pipeline above is actually finished or explicitly skipped with recorded reason.

### Blueprint summary — non-blocking

Default: emit concise Blueprint summary, then **immediately** continue to Capability Resolution → Plan → Edit.

Pause only if `production_options.review_before_edit: true` or true ambiguity/blocker per Stage 2 rules.

### Platform limit risk (registered)

If Agent platform turn/tool/duration limits still terminate execution despite this contract, escalate to **checkpointed production runner** (future) — auto checkpoint, auto resume, no Owner `继续`. **Not implemented in V0.1.1.**

### Regression contract (mechanical)

See `source/tests/production-continuous-execution.ps1`:

| Case | Expected |
|------|----------|
| A — normal multi-step Production | `CONTINUE_AUTONOMOUSLY` |
| B — missing required media | `BLOCKED` |
| C — Frozen Voice change | `OWNER_DECISION_REQUIRED` |
| D — out-of-scope action | `AUTHORIZATION_REQUIRED` |
| E — step complete, more work remains | progress allowed; execution **continues** |

---

## Idempotency / Resume

L3 must support:

- new production
- continuing an existing production

On start, inspect existing state.

If present:

- Project
- Timeline
- partial render
- previous output

Do **not** blindly recreate.

Choose based on facts:

| Mode | When |
|------|------|
| `CREATE` | No usable existing state |
| `CONTINUE` | Partial progress exists and can resume |
| `REPAIR` | Existing output needs correction |
| `RENDER_ONLY` | Timeline is ready, only render remains |

If state is unclear: **inspect first**.

Do **not** guess from conversation history.

---

## No Hidden Strategy

L3 must **not** secretly invent L2 strategy.

If the loaded L2 Skill does not define a specific stylistic decision, priority is:

1. Production Brief explicit requirement
2. L2 Skill references
3. L2 Skill allowed fallback
4. Minimal-intrusion generic handling

If a choice would materially change video style: **ask Owner**.

L3 must not decide alone.

---

## No Runtime Ownership

L3 is **not** responsible for:

- installing Runtime
- modifying MCP
- managing Resolve
- auto-downloading plugins
- switching NLE software

It only consumes the currently available Runtime.

---

## V0.1 Limitations

V0.1 is designed first to validate:

```
DaVinci Resolve + existing external DaVinci MCP
```

But L3 itself must **not** bind to specific MCP action names.

Future backends may include:

- other Resolve MCP implementations
- FFmpeg-only backend
- other NLE runtimes

L3 remains backend-agnostic at the orchestration layer.

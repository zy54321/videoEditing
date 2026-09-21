---
name: video-production
description: Orchestrates an end-to-end video production from a Production Brief by loading the selected editing strategy skill, inspecting available runtime capabilities, planning the edit, executing production, verifying results, repairing ordinary defects, rendering, and closing out.
disable-model-invocation: true
---

# Video Production

This is the **L3 Production Workflow** of Video Editing Workflow.

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

### Recommended Invocation

```
/video-production
使用 <brief-path> 开始生产
```

Example:

```
/video-production
使用 video-workflow/productions/N02/brief.yaml 开始生产
```

This skill uses **explicit invocation** (`disable-model-invocation: true`).

### Startup Parsing

On start, the skill must parse:

- `brief path`
- `production.id`
- `editing.skill`

### Brief Path Resolution

If the user does not provide a Brief path:

1. Check whether the current context contains exactly one unambiguous Production Brief.
2. If multiple candidates exist, or uniqueness cannot be determined: **ask the user**.
3. **Do not** infer Production from filename alone.

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
3. Read that Skill's `references/` as needed.
4. Use the L2 Skill as strategy authority for:
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

## Production Pipeline

Unified workflow:

```
Preflight
  → Analyze
  → Plan
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

### Production

- Production Brief read
- `production.id` confirmed
- `editing.skill` confirmed

### Paths

- Input exists
- Output is usable
- Cursor workspace is not confused with media root

### Runtime

When the task depends on DaVinci:

- DaVinci is accessible
- Current Project identity can be confirmed
- Current Runtime / MCP is accessible

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

## Stage 2 — Plan

Plan is the synthesis of:

```
Production Brief
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

## Stage 3 — Edit

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

## Stage 4 — Finish

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

- transcript / script alignment
- subtitle segmentation
- keyword emphasis

#### Graphics Pass

- titles
- lower thirds
- labels
- charts

#### Music Pass

- background music
- placement
- looping / trimming
- section changes

#### Audio Mix Pass

- narration priority
- ducking
- level balance
- clipping check

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

## Stage 5 — QA

QA has two layers.

### Universal QA

From Cross-cutting Rules:

- Frozen asset integrity
- output identity
- no unintended overwrite
- no unintended gaps
- no unexplained black frames
- target resolution
- target fps
- expected duration
- render validity
- audio presence
- no destructive source mutation

### Genre QA

From the loaded L2 Editing Skill.

Examples:

- pacing
- allowed shot duration
- transition grammar
- subtitle density
- music behavior
- motion naturalness
- factual visual alignment

QA must be based on **actual results**.

Passing execution steps without error is **not** sufficient for QA PASS.

---

## Stage 6 — Repair

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

## Stage 7 — Render

Render only after:

- Universal QA
- Required Genre QA

reach render-ready state.

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

## Stage 8 — Closeout

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

## Execution Continuity

Once Owner explicitly starts:

```
/video-production <brief>
```

this authorizes completion within that Brief scope through:

```
Preflight → Analyze → Plan → Edit → Finish → QA → Repair → Render → Closeout
```

Do **not** pause between normal stages to ask "should I continue?"

Stop only for blockers, scope changes, or Owner decisions defined by existing Rules.

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

# Edit Blueprint Reference

## Purpose

The Edit Blueprint is a **beat-first** editorial plan.

It is **not**:

- a Runtime action list
- an MCP call script
- a mandatory shot-by-shot storyboard for every beat

Runtime path: `video-workflow/production/edit-blueprint.yaml`

---

## Beat-first, Shot-on-demand

Default planning unit: **Beat**.

**Shot Plan** is optional per beat.

### When to expand Shot Plan

Expand when a beat involves:

- key contrast or reveal
- complex motion continuity
- interview or dialogue segment
- original-sound section
- montage
- multi-shot evidence sequence
- special transition, graphics, or sound design
- local author intent with visual criticality

Ordinary beats: **do not** force full shot lists.

---

## Beat Fields

| Field | Required | Notes |
|-------|----------|-------|
| `beat_id` | yes | Stable ID (B01, B02, …) |
| `narrative_function` | yes | e.g. CONTRAST, EVIDENCE, REVEAL |
| `source_content_range` | recommended | Script / narration segment |
| `author_intent` | optional | Traceable snapshot of Brief Owner intent applied to this beat — not new authority |
| `audience_effect` | recommended | Intended viewer change |
| `visual_intent` | recommended | What picture should accomplish |
| `attention_target` | recommended | Primary visual focus |
| `preferred_shot_functions` | recommended | Ordered hints, not rigid shots |
| `pacing` | recommended | slow / medium / medium-fast / fast |
| `sound_music_intent` | optional | e.g. narration dominant, duck music |
| `subtitle_graphics_intent` | optional | standard caption, keyword emphasis, title |
| `color_effect_intent` | optional | natural, slightly warm, etc. |
| `asset_selection_guidance` | optional | Semantic search hints |
| `shot_plan` | optional | Detailed shots when needed |

---

## Shot Plan Entry (when present)

```yaml
shot_plan:
  - shot_id: B03-S01
    function: ESTABLISH
    visual_intent: closed street on Sunday morning
    asset_requirement: urban exterior, empty shops
    transition_in: hard cut
    transition_out: dissolve short
```

**Must not** include MCP method names or exact API calls.

---

## Author Intent Provenance

| Source | Role |
|--------|------|
| `Brief.content.author_intent` | **Sole Owner Author Intent authority** |
| Blueprint `author_intent` per beat | Materialized / traceable view for planning — not new Owner authority |
| `visual_intent`, `audience_effect`, etc. | L3-derived editorial intent — distinct from Owner Author Intent |

If Blueprint `author_intent` conflicts with Brief → **Brief wins**; regenerate or correct Blueprint.

---

## Owner Visibility

Default flow:

```
Analyze → Blueprint → concise summary → continue automatically
```

Blueprint summary is **NON_BLOCKING** unless:

- `review_before_edit: true`
- unresolved author intent
- high-impact ambiguity
- content authority conflict

---

## Example Beat

```yaml
- beat_id: B01
  narrative_function: CONTRAST
  source_content_range: "Sunday shopping expectation"
  audience_effect: surprise
  visual_intent: normal-life expectation → unexpected closure
  attention_target: closed sign / empty street
  preferred_shot_functions:
    - ESTABLISH
    - EVIDENCE
    - REVEAL
  pacing: medium-fast
  sound_music_intent: narration dominant
  subtitle_graphics_intent: standard caption
  color_effect_intent: natural
  asset_selection_guidance: prefer real European street; avoid ad-like slow motion
  shot_plan: null
```

---

## Relationship to Editing Plan

| Artifact | Layer | Contains |
|----------|-------|----------|
| Edit Blueprint | Beat / intent | WHY each section exists |
| L3 Editing Plan | Execution planning | WHAT to assemble (still no MCP names) |

Blueprint precedes detailed segment timing in Plan.

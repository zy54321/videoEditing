---
name: observational-info-short
display_name: 生活观察 / 轻知识短视频
description: Editing strategy for short observational and informational videos built around narration, everyday B-roll, cultural or social observations, conversational pacing, readable captions, restrained transitions, natural motion, and light background music.
---

# Observational Info Short — L2 Style

**Skill ID:** `observational-info-short`  
**Canonical name:** 生活观察 / 轻知识短视频  
**Type:** Complete Style (directing + editing + finishing)

See: `docs/06-style-first-editing.md`, `docs/07-editing-craft-architecture.md`

---

## Style Identity

**Core feeling:** A friend telling you something interesting they just noticed.

**Audience experience:**

- natural, informationally clear, lightly paced
- not news-anchor formal, not travel-ado glossy, not ad-like

**Typical form:** Narration + B-roll + captions + light music

**Primary duration:** ~60–90s (45–120s only when Brief allows)

**Not suitable for:** breaking news, interview-doc dominant, tutorial screencast, music video, trailer

---

## Applicability & Exclusions

| Suitable | Not suitable |
|----------|----------------|
| narration-driven observation | breaking news |
| 3–7 information points | talking-head opinion dominant |
| cultural / social / light knowledge | product demo, music video |

---

## Authority Model

| Layer | Role |
|-------|------|
| **This Style** | Primary creative system — WHAT / WHEN / WHY |
| **Common Craft** | `video-workflow/knowledge/editing-craft/` — professional defaults |
| **Author Intent** | Optional (`content.author_intent`) — global or per-beat |
| **Creative Direction** | Optional (`editing.creative_direction`) — presentation refinements |
| **L1 / Runtime** | HOW — capability truth and execution |

**Owner Author Intent handling:**

- Brief `content.author_intent` is the sole Owner authority (optional)
- If Owner did not provide → `global: null`, `local: []` — Owner Author Intent **remains absent**
- L3 derives editorial / beat intent from Style + content authority + assets — **not** written back as Owner Author Intent
- **Global** Owner intent shapes whole piece within Style bounds
- **Local** Owner intent affects named beat only — must not retarget entire Style

---

## Aesthetic Decision Priority

When options conflict (after safety / factual integrity):

1. Author Intent (if provided)
2. Emotion / Audience Effect
3. Story / Information Progression
4. Rhythm
5. Visual Attention
6. Style Consistency
7. Technical Continuity

---

## Blueprint Requirement

L3 **MUST** produce an **Edit Blueprint** (beat-first) before detailed Edit execution.

- Template: `video-workflow/templates/edit-blueprint.yaml`
- Runtime: `video-workflow/production/edit-blueprint.yaml`
- Default: expose concise summary → **continue automatically**
- Block only if `review_before_edit: true` or unresolved intent / authority conflict

Blueprint is **not** a Runtime action plan.

---

## Reference Loading Order

Load in order when executing this Style:

1. `references/directing.md` — beats, shot function, narrative
2. `references/visual-language.md` — composition, 9:16 framing
3. `references/editing.md` — pacing, motion, transitions, ending
4. `references/typography-graphics.md` — captions, graphics
5. `references/sound-music.md` — voice, music, sound design
6. `references/color-effects.md` — color, effects restraint
7. `references/qa.md` — Style acceptance checklist

Common Craft (`video-workflow/knowledge/editing-craft/`) may be consulted; **Craft does not override Style**.

`references/style.md` is **deprecated** — compatibility pointer only.

---

## Style Dimensions (17)

| # | Dimension | Reference |
|---|-----------|-----------|
| 1 | Style Identity | this file |
| 2–4 | Narrative / Pacing / Shot grammar | `directing.md`, `editing.md` |
| 5 | Source selection | `directing.md`, `editing.md` |
| 6–7 | Motion / Framing | `editing.md`, `visual-language.md` |
| 8 | Transitions | `editing.md` |
| 9–10 | Subtitles / Voice | `typography-graphics.md`, `sound-music.md` |
| 11–12 | Music / Sound design | `sound-music.md` |
| 13 | Graphics | `typography-graphics.md` |
| 14–15 | Color / Effects | `color-effects.md` |
| 16 | Ending | `editing.md` |
| 17 | Style QA | `qa.md` |

---

## Brief Override Policy

Brief may override non-safety stylistic parameters when explicit (subtitles, music, transitions, look, graphics density).

Safety, factual integrity, and Frozen assets are **not** overridable by Brief alone.

---

## Runtime Independence

Expressed in editorial terms — not bound to DaVinci, MCP, or specific tool names.

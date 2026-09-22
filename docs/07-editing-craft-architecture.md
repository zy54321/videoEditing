# Editing Craft Architecture (V0.1.1)

## Layer Model

```
Common Craft Knowledge (shared principles)
        ↓ informs
L2 Style Skill (aesthetic choices for a genre)
        ↓ drives
Edit Blueprint (beat-first plan)
        ↓ executed via
L1 Capability (implementation truth)
        ↓ runs on
Runtime (DaVinci / tools)
```

---

## Common Craft Knowledge

**Location:** `video-workflow/knowledge/editing-craft/`

Answers: *“What do professional film/video editors generally know?”*

- Not a Skill
- Not copied into each Style
- Does **not** override Style

---

## L2 Style Skill

**Primary unit:** `STYLE` (e.g. `observational-info-short`)

A Style is a **complete** directing / editing / finishing strategy.

**Not** first-class L2 units: subtitle, music, voice, color, transition, effect (these are Style dimensions).

---

## Edit Blueprint

**Beat-first, shot-on-demand.**

- Default unit: **Beat** (narrative function + intent)
- **Shot Plan** optional — expand only when warranted
- **Not** a Runtime action plan (no MCP names, no API calls)
- **Default:** non-blocking summary → continue automatically
- **Blocking** only when: `review_before_edit`, unresolved intent, authority conflict

**Template:** `video-workflow/templates/edit-blueprint.yaml`  
**Runtime:** `video-workflow/production/edit-blueprint.yaml`

---

## Author Intent vs Creative Direction

| Field | Role |
|-------|------|
| **Style** | Primary creative system |
| **Author Intent** | What Owner wants to express / emphasize (optional) |
| **Creative Direction** | How Owner wants it to feel / look (optional refinements) |

Brief fields:

```yaml
editing:
  skill: observational-info-short
  creative_direction: []

content:
  author_intent:
    global: null
    local: []
```

- `content.author_intent` is the **sole Owner Author Intent authority** (optional)
- If Owner did not provide: `global: null`, `local: []` — do not infer Owner Author Intent from Style or assets
- L3 derives editorial / beat-level intent separately (`visual_intent`, `audience_effect`, etc.)
- Blueprint `author_intent` = traceable snapshot / applied view — **Brief wins** on conflict
- **Global** Owner intent affects whole piece
- **Local** Owner intent affects named beat(s) only — must not silently retarget entire Style

---

## Aesthetic Decision Priority

When legitimate options conflict (after safety / factual integrity):

1. Author Intent (when provided)
2. Emotion / Audience Effect
3. Story / Information Progression
4. Rhythm
5. Visual Attention
6. Style Consistency
7. Technical Continuity

Safety and content authority always win over aesthetic preference.

---

## Aesthetic Rule Hierarchy

Four levels (see `editing-craft/aesthetic-qa.md`):

| Level | Name | Example |
|-------|------|---------|
| 1 | STRUCTURAL_INVARIANT | No subtitle overflow; no unintended black frames |
| 2 | REVIEWED_INVARIANT | Shots must serve narrative; intelligible audio hierarchy |
| 3 | CRAFT_DEFAULT | Avoid meaningless slow motion; motivated cuts |
| 4 | TASTE_OPTION | Warm vs cool; restrained vs energetic |

Do not promote Taste Options to fake objective rules.

---

## Build vs Production

See `docs/build-stage-no-production.md`.

Construction work must not trigger Production or Acceptance runs.

---

## External Research

`research/editing-craft-sources.md` — **research only**, not Runtime dependency.

Do not install external skills into payload without explicit Owner decision.

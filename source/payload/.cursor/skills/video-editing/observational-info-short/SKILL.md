---
name: observational-info-short
display_name: 生活观察 / 轻知识短视频
description: Editing strategy for short observational and informational videos built around narration, everyday B-roll, cultural or social observations, conversational pacing, readable captions, restrained transitions, natural motion, and light background music.
---

# Observational Info Short — L2 Style

**Skill ID:** `observational-info-short`  
**Canonical name:** 生活观察 / 轻知识短视频  
**Type:** Complete Style (directing + editing + finishing)

Architecture: `docs/08-l2-style-contract-aesthetic-intelligence.md`

---

## Style Identity

**Core feeling:** A friend telling you something interesting they just noticed.

**Audience experience:** natural, clear, lightly paced — not news-anchor, travel-ad, or promo.

**Typical form:** Narration + B-roll + captions + optional light music.

**Format / duration:** Defined by **Production Brief** (`format.*`, `format.target_duration_seconds`). This Style adapts composition and rhythm to Brief — it is not permanently bound to 9:16 or 60–90s.

See `style-profile.yaml` for structured taste coordinates.

---

## Applicability & Exclusions

| Suitable | Not suitable |
|----------|----------------|
| narration-driven observation | breaking news |
| 3–7 information points | talking-head opinion dominant |
| cultural / social / light knowledge | product demo, music video, trailer |

---

## Authority Model

| Layer | Role |
|-------|------|
| **This Style** | WHAT / WHEN / WHY |
| **style-profile.yaml** | Taste coordinates |
| **capability-policy.yaml** | L2 → L1 logical capability policy |
| **Common Craft** | `video-workflow/knowledge/editing-craft/` |
| **Owner Author Intent** | `Brief.content.author_intent` (optional, sole Owner authority) |
| **Creative Direction** | `editing.creative_direction` (optional refinements) |
| **L1 / Runtime** | HOW |

Owner Author Intent absent → `global: null`, `local: []`. L3 derives editorial / beat intent separately — not written back as Owner Author Intent.

---

## Aesthetic Decision Priority

1. Author Intent (when provided in Brief)
2. Emotion / Audience Effect
3. Story / Information Progression
4. Rhythm
5. Visual Attention
6. Style Consistency
7. Technical Continuity

(Safety and factual integrity always above aesthetic choices.)

---

## Blueprint Requirement

L3 **MUST** produce **Edit Blueprint** (beat-first) before Edit.

- Template: `video-workflow/templates/edit-blueprint.yaml`
- Runtime: `video-workflow/production/edit-blueprint.yaml`
- Default: concise summary → **non-blocking** continue
- Blueprint may include `capability_requirements` — semantic only, not Runtime actions

---

## Capability Policy Relationship

Load `capability-policy.yaml` during Plan / Capability Resolution.

- REQUIRED missing → BLOCK / review
- PREFERRED missing → Style-defined fallback
- OPTIONAL missing → omit

L1 vocabulary: `video-workflow/capabilities/logical-capability-vocabulary.yaml`

---

## Reference Loading Order

1. `style-profile.yaml`
2. `capability-policy.yaml`
3. `references/01-directing.md`
4. `references/02-visual-language.md`
5. `references/03-editing-rhythm.md`
6. `references/04-typography-graphics.md`
7. `references/05-sound-music.md`
8. `references/06-color-look-effects.md`
9. `references/07-taste.md`
10. `references/08-qa.md`

Common Craft may be consulted; **Craft does not override Style**.

Deprecated pointers (`directing.md`, `editing.md`, `style.md`, etc.) are **not** authority.

---

## Brief Override Policy

Brief may override non-safety stylistic parameters when explicit (`features.*`, creative direction).

Frozen assets and factual integrity are not overridable by Brief alone.

---

## QA Relationship

| Layer | Source |
|-------|--------|
| Universal Technical QA | L3 + Common Craft structural rules |
| Common Aesthetic QA | `editing-craft/aesthetic-qa.md` |
| **Style Fidelity QA** | `references/08-qa.md` |

---

## Runtime Independence

Expressed in editorial and logical capability terms only — no MCP, Resolve API, or implementation route names in this Skill.

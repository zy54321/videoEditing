---
name: <style-id>
display_name: <Human Readable Style Name>
description: <One-line Style summary for skill discovery>
---

# <Style Name> — L2 Style

**Skill ID:** `<style-id>`  
**Type:** Complete Style (directing + editing + finishing)

Contract: `docs/08-l2-style-contract-aesthetic-intelligence.md`

---

## Style Identity

See `style-profile.yaml` — identity and taste_profile coordinates.

**Format note:** Aspect ratio, duration, and platform come from **Production Brief**. This Style defines how to adapt when Brief specifies format (e.g. vertical 9:16).

---

## Applicability & Exclusions

<!-- Instance-specific lists -->

---

## Authority Model

| Layer | Role |
|-------|------|
| **This Style** | WHAT / WHEN / WHY |
| **Common Craft** | `video-workflow/knowledge/editing-craft/` |
| **Owner Author Intent** | `Brief.content.author_intent` (optional) |
| **Creative Direction** | `editing.creative_direction` (optional) |
| **Capability Policy** | `capability-policy.yaml` → L1 vocabulary |
| **L1 / Runtime** | HOW |

---

## Blueprint Requirement

L3 **MUST** produce Edit Blueprint before Edit. See `video-workflow/templates/edit-blueprint.yaml`.

---

## Reference Loading Order

1. `references/01-directing.md`
2. `references/02-visual-language.md`
3. `references/03-editing-rhythm.md`
4. `references/04-typography-graphics.md`
5. `references/05-sound-music.md`
6. `references/06-color-look-effects.md`
7. `references/07-taste.md`
8. `references/08-qa.md`

Load `style-profile.yaml` and `capability-policy.yaml` before references.

---

## Override Policy

Brief may override non-safety stylistic parameters when explicit. Frozen assets and factual integrity are not overridable.

---

## Runtime Independence

No MCP methods, Resolve API names, or implementation routes in this Skill.

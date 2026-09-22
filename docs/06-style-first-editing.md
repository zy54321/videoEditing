# Style-first Editing Model (V0.1.1+)

## Principle

L2 Editing Skill 的一级组织单位必须是**完整剪辑风格（Style）**，而不是单一技术维度。

以下不得单独作为一级 L2 Skill：

- subtitle
- voice
- music
- sound effect
- color
- filter
- visual effect
- transition

它们是完整 Style 的内部组成维度。

一个 Style Skill 可以同时定义：

- 多种字幕表现
- 多段音乐
- 多种音效
- 多种 Voice Treatment
- 多种 Graphics / Titles
- 多种调色处理
- 多种视觉特效

具体采用哪种处理，由以下共同决定：

```
Style
+ Narrative Section
+ Content
+ Creative Direction
+ Available Capability
```

## Authority Split

| Layer | Decides |
|-------|---------|
| **Style** | WHAT / WHEN / WHY |
| **L1** | HOW (capability truth) |
| **Runtime** | executes |

## Creative Direction

`editing.creative_direction` 是对已选 Style 的补充要求，**不是**新 Style。

Style 始终是 primary strategy。Creative Direction 只能在 Safety Rules、Style identity、Capability truth 范围内修饰执行。

## Content vs Presentation

**Content semantics**（事实、数字、专有名词、核心观点）与 **subtitle presentation**（分句、换行、timing、cue 拆分）是不同层面。

Frozen Script / Frozen Voice 作为内容权威时：不得改语义，但允许为剪辑表现调整字幕呈现。

## Final Artifact QA

Timeline State QA ≠ Final Artifact QA。

Render 技术 verify 通过，不等于成片视觉/运动/字幕布局 PASS。

---

## Architecture Freeze (Stage 08C)

**Frozen:** L2 primary unit = **STYLE** (complete directing / editing / finishing strategy).

Examples: `observational-info-short`, `lifestyle-vlog`, `news-explainer`, `documentary-short`

**Not** first-class L2: subtitle, music, voice, color, transition, effect, sound-design, typography.

### Layer Stack

```
Common Craft Knowledge  →  video-workflow/knowledge/editing-craft/
L2 Style Skill          →  .cursor/skills/video-editing/<style>/
Edit Blueprint          →  beat-first plan (templates/edit-blueprint.yaml)
L1 Capability           →  video-workflow/capabilities/
Runtime                 →  external NLE / MCP
```

See: `docs/07-editing-craft-architecture.md`

### Author Intent vs Creative Direction

| Field | Role |
|-------|------|
| `content.author_intent` | What Owner wants to express (optional) |
| `editing.creative_direction` | How Owner wants it to look/feel (optional) |
| `editing.skill` | Primary Style system |

Author Intent may be global or local (per beat). Local intent must not silently retarget entire Style.

### Beat-first Blueprint

Planning default = **Beat**, not shot-by-shot storyboard.

Shot Plan expands only when beat complexity requires it.

Blueprint is **non-blocking** unless `production_options.review_before_edit: true` or unresolved ambiguity.

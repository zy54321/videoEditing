# Editing Craft — External Research Sources

**Status:** Research Only — **not** Runtime dependencies.

Do not download or install these into `source/payload` without explicit Owner decision.

---

## Classification Key

| Class | Meaning |
|-------|---------|
| **Idea** | Concept absorbed into craft docs |
| **Algorithm** | Process pattern adapted |
| **Tool** | External tool reference only |
| **QA** | Review method adapted |
| **Reference** | Terminology / vocabulary source |

---

## AI Storyboard / Drama Workflow

| Source type | Class | Notes |
|-------------|-------|-------|
| AI 漫剧 / storyboard-first pipelines | Idea, Algorithm | Beat → shot intent; **not** generate-by-default for us |
| Text-to-image shot generation | Tool | Out of scope for editing workflow |
| Shot list from script parsers | Algorithm | Adapted to beat-first + existing assets |

**Our adaptation:** Intent → Beat / Shot Function → Visual Intent → select existing media.

---

## Video Editing Skills (external)

| Source type | Class | Notes |
|-------------|-------|-------|
| Generic “video editor” agent skills | Reference | Terminology for cuts, pacing |
| Template-based editing prompts | Idea | Rejected as L2 — too effect-first |

---

## DaVinci / NLE Skills

| Source type | Class | Notes |
|-------------|-------|-------|
| DaVinci Resolve MCP / API docs | Tool, Reference | L1 capability truth only |
| Color page workflows | QA, Reference | color-look-effects.md |

**Not copied:** full MCP action lists into Blueprint.

---

## Documentary Workflow

| Source type | Class | Notes |
|-------------|-------|-------|
| Observational documentary pacing | Idea | Informs observational-info-short |
| B-roll + narration structure | Algorithm | Beat map patterns |

---

## Visual Design / UI Aesthetic Skills

| Source type | Class | Notes |
|-------------|-------|-------|
| Typography safe zones | QA | typography-graphics.md width contract |
| Contrast / hierarchy principles | Reference | graphics restraint |

---

## Traditional Film Editing

| Source type | Class | Notes |
|-------------|-------|-------|
| Cut motivation, J/L cuts | Idea | editing-rhythm.md |
| 180° rule, match on action | Reference | visual-language.md |
| Kuleshov / contrast editing | Idea | directing-story.md |

---

## Position

External projects inform **Common Craft Knowledge** and **Style references**.

They do **not** become our L2 Skills or Runtime dependencies.

Final architecture:

```
Style-first → Beat-first → Capability-aware
```

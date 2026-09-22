# Directing & Story — Common Craft

## Core Concepts

- **Author Intent** — what the creator wants the audience to feel or understand (optional in Brief)
- **Theme** — underlying idea tying beats together
- **Narrative Function** — what a beat *does* for the story
- **Narrative Beat** — a unit of narrative progression (not necessarily one shot)
- **Audience Change** — how the viewer’s understanding or feeling shifts
- **Reveal** — new information or perspective lands
- **Contrast** — expectation vs reality, before vs after
- **Evidence** — concrete visual proof supporting a claim
- **Reaction** — human or situational response to an event
- **Escalation** — stakes or curiosity increase
- **Breath** — pause, reset, ambient moment
- **Resolution** — tension releases or question answers
- **Ending** — final audience state

Also: **Visual Intent** (what the image should accomplish) and **Attention Target** (where the eye should land).

---

## Shot Function Vocabulary

Vocabulary — not a rigid enum. Styles may extend.

| Function | Typical role |
|----------|----------------|
| **ESTABLISH** | Place, time, context |
| **CONTEXT** | Situational background |
| **EVIDENCE** | Prove or show a specific fact |
| **REVEAL** | Unveil contrast or surprise |
| **CONTRAST** | Juxtapose ideas or states |
| **REACTION** | Show response to prior beat |
| **EMPHASIS** | Stress one detail or idea |
| **TRANSITION** | Bridge beats or locations |
| **BREATH** | Rest, ambience, original sound |
| **ORIGINAL_SOUND** | Authentic diegetic moment |
| **RESOLUTION** | Close a narrative thread |
| **ENDING** | Final image / feeling |

Every shot should answer: **why does this image exist?**

---

## AI Storyboard Adaptation

**AI generation pipeline:**

```
Intent → Storyboard → Generate Shot
```

**Video editing pipeline (ours):**

```
Intent → Beat / Shot Function → Visual Intent
      → Search Existing Assets → Select Best Available → Edit
```

**Do not** treat “generate a new shot” as the default action.

The goal is for the agent to understand **why a moment exists**, not **what image to synthesize**.

---

## Beat-first Planning

Default planning unit: **Beat**.

Shots are expanded **on demand** when a beat requires detailed continuity or special treatment.

See: `templates/edit-blueprint.yaml`

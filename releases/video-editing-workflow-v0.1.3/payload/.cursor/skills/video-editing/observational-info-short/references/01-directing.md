# Directing

## Style Goal

Shape narration-driven observation into a beat-first story that feels like a friend sharing something they just noticed — clear, credible, lightly engaging, and never performative. Every beat must earn its place through information, contrast, or human context.

## Inherit from Common Craft

Consult `video-workflow/knowledge/editing-craft/directing-story.md` for:

- Owner Author Intent vs L3-derived editorial intent
- Narrative beat vocabulary (Reveal, Contrast, Evidence, Breath, Resolution)
- Shot function taxonomy and beat-first planning model
- Visual Intent and Attention Target concepts

Common Craft explains professional defaults. This Style selects which functions dominate and how aggressively beats escalate.

## Style Defaults

**Default narrative arc:**

```
Hook → Establish → Observation 1..N → Reframe / Insight → Natural Close
```

**Typical beat count:** 3–7 information points within Brief duration (usually ~60–90s soft guidance).

**Default shot-function palette:**

| Function | Role in this Style |
|----------|-------------------|
| **ESTABLISH** | Place, time, social context — "where we are" |
| **CONTEXT** | Background that supports understanding without stealing focus |
| **EVIDENCE** | Visual proof of the narrated fact |
| **REVEAL / CONTRAST** | Expectation vs reality, before vs after |
| **REACTION** | Human or situational response — social nuance |
| **EMPHASIS** | Stress one detail when narration demands it |
| **TRANSITION** | Bridge beats or locations without spectacle |
| **BREATH / ORIGINAL_SOUND** | Authentic ambient pause; credibility reset |
| **RESOLUTION / ENDING** | Thread closes; life continues |

**Source selection priority:**

1. Real B-roll directly related to narration facts
2. Semantically relevant generic lifestyle B-roll
3. Atmosphere B-roll
4. AI supplement — last resort; never fake specific real events

Filename is a hint only. Inspect actual media content before assignment.

## Prefer When

- A beat introduces a new place, habit, or social rule → **ESTABLISH** or **CONTEXT**
- Narration states a verifiable fact → **EVIDENCE** with readable action
- Narration contrasts expectation and reality → **REVEAL** or **CONTRAST**
- Audience needs to feel social texture → **REACTION** or **ORIGINAL_SOUND**
- Information density peaks → shorter beats with clear **EMPHASIS** targets
- Closing beat → **RESOLUTION** plus a natural life image, not a slogan card

## Allow When

- **TRANSITION** shots bridge location or time when narration explicitly shifts topic
- Generic lifestyle B-roll carries atmosphere when no direct evidence exists — label semantically adjacent, not falsely specific
- **BREATH** beats run 3–6s without new information when ambience supports credibility
- Local Owner Author Intent (`author_intent.local`) adjusts warmth, contrast, or emphasis within one named beat
- Global Owner Author Intent shapes whole-piece tone (e.g., "more skeptical," "warmer") without changing Style identity

## Avoid When

- A shot exists only because it "looks cinematic" with no narrative job
- Stock footage with obvious ad posing stands in for specific evidence
- The same source range repeats at short interval without changed framing or narrative role
- Hook opens with logo, filler, or information-free slow montage
- Beat map inflates to one-shot-per-sentence granularity without visual need

## Prohibit

- Treating AI generation as the default substitute for searching existing assets
- Using generic B-roll to imply specific real-world events, locations, or identifiable people as direct proof
- Local Owner Intent retargeting the entire piece into trailer, news broadcast, or corporate promo without explicit Style change
- Writing L3-derived editorial intent back into `Brief.content.author_intent` as if Owner provided it
- Empty beats whose only purpose is visual decoration

## Exceptions

- Brief explicitly requests a different opening structure (e.g., cold open on strongest contrast) — honor Brief within factual integrity bounds
- Asset scarcity: semantically adjacent B-roll may substitute for ideal evidence when labeled honestly in Blueprint notes
- Owner local intent on a named beat may request heightened contrast or reveal — apply only to that beat, not globally
- Single-beat **EMPHASIS** close-up is allowed when evidence or emotion truly requires it (see `02-visual-language.md`)

## Trade-offs

| Choice | Gain | Cost |
|--------|------|------|
| Evidence-first sourcing | Credibility, semantic alignment | Less "beautiful" montage flow |
| Generic lifestyle fallback | Coverage when direct footage missing | Weaker specificity; requires careful implication QA |
| Fewer, clearer beats | Faster comprehension | Less atmospheric texture |
| More **BREATH** beats | Authenticity, original sound | Slightly slower information delivery |
| Strict shot-function discipline | Coherent observation voice | Rejects flashy stock that other genres would embrace |

## Capability Intent

| Editorial need | Logical capability |
|----------------|-------------------|
| Select best available source for beat function | `visual.select_asset` |
| Reframe for subject / evidence readability | `visual.reframe.static` |
| Trim to beat content range | `visual.trim` |
| Place voice on timeline aligned to beats | `audio.voice.place` |
| Preserve diegetic ambience in **ORIGINAL_SOUND** beats | `audio.original_sound.preserve` |

Capability IDs express intent only. Runtime route selection belongs to L1.

## Blueprint Mapping

Each beat in `edit-blueprint.yaml` should declare at minimum:

| Field | Directing use |
|-------|---------------|
| `beat_id` | Stable reference for local intent and QA |
| `narrative_function` | Primary shot-function vocabulary (e.g., `EVIDENCE`, `CONTRAST`) |
| `source_content_range` | Narration segment or script section this beat serves |
| `author_intent` | Optional local Owner override |
| `audience_effect` | Intended shift (clarity, surprise, empathy, etc.) |
| `visual_intent` | What the image must accomplish |
| `attention_target` | Face, hands, object, environment relation |
| `preferred_shot_functions` | Ordered list for asset search |
| `asset_selection_guidance` | Constraints, red flags, fallback notes |

`shot_plan` is optional — expand only when a beat requires detailed continuity or special treatment.

Populate `capability_requirements` from `capability-policy.yaml` when beat-level execution needs explicit L1 binding (e.g., `visual.select_asset`, `visual.reframe.static`).

## QA Signals

Style fidelity signals for directing (not technical checks):

- Piece reads as observation, not advertisement or news bulletin
- Each major narration claim has a supporting or honestly adjacent visual role
- Hook establishes place, question, contrast, or strongest point within opening beats
- No beat exists purely for stock montage filler
- Repetition of sources changes range, framing, or semantic role
- Ending resolves information without forced CTA or engagement bait
- Owner Author Intent respected where provided; absent intent not invented

## Reference Cases

**RC-VIS-001** (`video-workflow/knowledge/editing-craft/reference-cards/RC-VIS-001.yaml`): Payment counter as **EVIDENCE** — prefer medium stable shot with readable action over aggressive push-in. Push-in reads as promotional emphasis; observational style treats payment as everyday proof, not spectacle.

**Hook contrast beat:** Sunday shop closure narrated → **REVEAL** with closed-door evidence beats expectation of open commerce. Prefer factual framing over dramatic angle.

**Breath beat before insight:** Short **ORIGINAL_SOUND** street ambience before reframing beat lets audience feel place before abstract conclusion lands.

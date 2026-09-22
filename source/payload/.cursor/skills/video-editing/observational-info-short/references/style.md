# Observational Info Short — Style Parameters

Decision ranges for L3 Editing Plan. These are **guidance ranges**, not fixed presets. Production Brief may override non-safety parameters when explicit.

---

## Duration

| Range | Seconds |
|-------|---------|
| Target | 60–90 |
| Extended (Brief required) | 45–120 |

---

## Shot Timing

| Segment | Visual unit duration |
|---------|---------------------|
| Hook | 1.5–3.5 sec between visual changes |
| Ordinary semantic unit | 2.5–4.5 sec |
| Establish | 4–6 sec |
| Dense information | 1.5–3 sec |

Cut on semantic turn, not sentence boundaries alone.

---

## Motion Normalization

| Condition | Speed range |
|-----------|-------------|
| Natural | 1.0× |
| Slight normalization | 1.15–1.35× |
| Obvious slow motion | 1.4–2.0× |
| Severe slow motion | 2.0×+ (verify naturalness) |

Evaluate by **visual action**, not frame rate metadata alone.

Establishing / environment shots may retain slightly slower rhythm as intentional style.

---

## Transition

| Type | Default |
|------|---------|
| Natural / Hard Cut | default (~70–85% of cuts) |
| Short Dissolve | 4–8 frames (fps-dependent) |
| Strong effect transitions | disabled by default |

Every transition: handles sufficient, no gap, no black frame.

---

## Subtitle

| Parameter | Range |
|-----------|-------|
| Lines per cue | 1–2 max |
| Horizontal safe width (9:16) | ~80–86% of frame |
| CN characters per cue | ~8–18 (secondary heuristic) |
| Keyword emphasis | 1–3 key elements per semantic section |
| Intentional gap | 3–6 sec during original-sound sections OK |

**Layout:** semantic line breaks (punctuation, phrases); avoid edge hugging; minimum readable font size.

**Visual types:** Standard Caption (default) | Keyword Emphasis (sparse) | Title/Section (hierarchy).

Default: ON unless Brief disables.

---

## Voice Treatment

| Treatment | Default |
|-----------|---------|
| Natural Voice | yes — clear, intelligible, dominant |
| Light EQ / compression / warmth | optional |
| Special FX (radio/phone) | narrative-only |

Frozen Voice Master: non-destructive or derived audio only.

---

## Sound Design

| Element | Guidance |
|---------|----------|
| Environment / original sound | preferred over decorative SFX |
| Transition SFX | sparingly |
| Silence | intentional sections OK |

---

## Music

| Section | Role |
|---------|------|
| Hook | light entry |
| Main | low-presence bed |
| Original-sound moment | duck / drop |
| Narrative turn | second track allowed |
| Ending | natural fade |

| Parameter | Guidance |
|-----------|----------|
| Track count | 1–2 typical for 60–90s |
| Presence | low — supportive |
| Narration | dominant |

Default: ON unless Owner disables (`OWNER_DISABLED`).

---

## Mixed FPS / Cadence

Record in Analyze before Plan:

| Field | Example |
|-------|---------|
| Source FPS distribution | 23.976, 25, 29.97, 30 |
| Timeline FPS | 24 (default) |
| Mismatch risk | low / medium / high |
| Motion-heavy clips | list |

Do not infer cadence PASS from CFR render metadata alone.

---

## Graphics

| Parameter | Guidance |
|-----------|----------|
| Density | minimal |
| Title / lower third | clean, simple, brief |

Use only when understanding benefits.

---

## Color

| Parameter | Guidance |
|-----------|----------|
| Look | natural, clean, coherent |
| Heavy cinematic LUT / teal-orange | off by default |
| Priority | believable realism > cinematic feel |

---

## Visual Effect Density

**Low.**

A typical 60–90 second piece should **not** have "one effect per shot."

Dynamic zoom: sparingly, for static low-variation shots only.

---

## Audio Mix

| Parameter | Guidance |
|-----------|----------|
| Narration priority | always highest |
| Music level | below narration (verify by ear) |
| Ducking | allowed |
| Fades | preferred for music in/out |

No fixed dB values — verify intelligibility and clipping.

---

## Ending

| Parameter | Guidance |
|-----------|----------|
| Visual tail | ~0.4–0.8 sec after final narration beat |
| Forced CTA / slogan | off by default |

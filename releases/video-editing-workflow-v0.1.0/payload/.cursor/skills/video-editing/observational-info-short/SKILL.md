---
name: observational-info-short
description: Editing strategy for short observational and informational videos built around narration, everyday B-roll, cultural or social observations, conversational pacing, readable captions, restrained transitions, natural motion, and light background music.
---

# Observational Info Short

**Skill type:** L2 Editing Strategy  
**Genre ID:** `OBSERVATIONAL_INFO_SHORT`

## Purpose

Turn "life observation + information explanation + light perspective" content into short videos that feel:

- natural
- informationally clear
- lightly paced
- not news-anchor formal
- not travel-promo glossy
- not ad-like
- not over-entertained

**Core feeling:**

> Like a friend telling you about something interesting they just noticed.

**Not:**

- news anchor delivery
- corporate promo
- movie trailer
- travel advertisement
- pure-emotion vlog
- high-frequency meme cut

## Scope Boundaries

This Skill answers: **"How should this type of video be edited?"**

It does **not** handle:

- Production lifecycle orchestration (L3)
- Runtime management
- MCP call details
- NLE API methods
- File installation
- Render implementation

L3 loads this Skill automatically. Owner does not invoke it directly each time.

## Typical Content

- overseas life differences
- everyday cultural observations
- social habits
- light knowledge / cold facts
- "this is how people live here"
- non-breaking-news informational observation
- light opinion + factual information

## Typical Production Form

```
Narration / Voice
+ B-roll
+ Captions
+ Light Music
```

---

## Applicability

### Suitable For

- ~60–90 seconds (primary target)
- narration-driven
- B-roll-heavy
- 3–7 information points
- real-life scenes
- cultural / social / experiential observation

### Extended Range

May extend to **45–120 seconds**, but only when L3 / Brief explicitly allows. Do not assume the same pacing rules apply beyond range without confirmation.

### Not Suitable For

- breaking news
- interview documentary
- talking-head opinion dominant
- tutorial screencast
- product demo
- music video
- trailer
- long documentary

Other genres should use future L2 Skills.

---

## Strategy Output Contract

When L3 loads this Skill, it must receive strategy guidance for:

1. Narrative Rhythm
2. Shot Grammar
3. Source Selection
4. Motion Strategy
5. Framing Strategy
6. Transition Strategy
7. Subtitle Strategy
8. Graphics Strategy
9. Music Strategy
10. Audio Mix Strategy
11. Color Strategy
12. Effects Strategy
13. Genre QA

These feed directly into the L3 Editing Plan.

For parameter ranges and QA checklist, see:

- `references/style.md`
- `references/qa.md`

---

## 1. Narrative Rhythm

Default pacing: **naturally brisk** — not urgent news, not slow cinematic prose.

### Suggested Structure

```
Hook
  → Establish
  → Observation 1
  → Observation 2
  → Observation 3 ...
  → Reframe / Insight
  → Natural Close
```

### Hook (first 3–5 seconds)

Establish at least one of:

- place
- question
- contrast
- most interesting information point

Avoid:

- long logo
- long establishing shot with no information
- meaningless slow opener

### Shot Timing Guidance

| Segment type | Typical duration |
|--------------|------------------|
| Ordinary semantic unit | 2.5–4.5 sec |
| Establishing shot | 4–6 sec |
| Strong information point | 1.5–3 sec |

Do **not** mechanically apply "one sentence = one cut."

Cut points should follow:

- semantic turn
- action change
- contrast
- emphasis
- subject change

---

## 2. Shot Grammar

Every shot must serve at least one function:

- establish
- explain
- demonstrate
- contrast
- reinforce
- reset attention
- close

Reject shots that occupy timeline only because they "look nice."

### Source Priority

1. Real B-roll directly related to narration facts
2. Semantically relevant generic lifestyle B-roll
3. Atmosphere B-roll
4. AI supplement (last resort)

AI B-roll only when no suitable real footage exists for a key action or scene.

**Never** use AI imagery to fake:

- news scenes
- real-event evidence
- specific factual behavior of identifiable people

---

## 3. Source Selection

Prioritize:

- semantic relevance
- natural movement
- composition
- authenticity
- sufficient source duration
- crop safety
- visual diversity

Filename is a hint only — not evidence of content.

### Stock Footage Red Flags

Lower priority or require treatment when footage shows:

- obvious slow motion
- over-staged posing
- ad-like camera language
- overly cinematic look
- mismatch with narration realism

Same source may be reused with different source ranges.

**Prohibit:** obvious identical visuals repeating in short succession.

See also: **Repetition Strategy**.

---

## 4. Motion Strategy

**MUST for this genre.** Real-life action speed takes priority.

Stock footage must **not** retain obvious slow-motion just because the source plays that way.

Evaluate whether these actions appear slower than natural:

- walking
- hand movement
- payment
- talking gesture
- vehicle movement
- pouring
- opening door
- shopping

If clearly slow-motion: apply **Motion Normalization**.

Goal is not "speed everything up." Goal is **restore believable real-world motion speed**.

### Decision Ranges

| Condition | Typical speed range |
|-----------|---------------------|
| Natural | 1.0× |
| Slightly slow stock | ~1.15–1.35× |
| Obvious slow-motion | ~1.4–2.0× |
| Severe slow-motion | Higher allowed; must verify naturalness |

Do **not** decide from frame rate alone. Combine visual action with source timing behavior.

Establishing / environment shots may intentionally retain slightly slower rhythm as a conscious style choice.

Parameter tables: `references/style.md`

---

## 5. Framing Strategy

Short-form default: **subject first.**

### 9:16 Vertical

For horizontal source:

- fill target frame
- preserve aspect ratio
- reposition for subject

**Prohibit:**

- stretch
- unintended letterbox
- unintended pillarbox

### Subject Priority

| Subject | Preserve |
|---------|----------|
| People | face / upper body / action |
| Object action | hands, payment, tools, key objects |
| City | landmark / vehicle / pedestrian relation |

If horizontal source cannot crop reasonably to vertical:

1. alternate source range
2. alternate source
3. intentional layout only when Skill / Brief allows

Do **not** default to black bars.

---

## 6. Transition Strategy

Core principle: **transitions serve semantic relationship, not decoration.**

### Default Distribution

- ~70–85%: Hard / Natural Cut
- remainder: short restrained transitions

### By Semantic Relationship

| Relationship | Preferred transition |
|--------------|---------------------|
| Same semantic continuity | Hard Cut / Action Cut |
| Light scene change | Short Dissolve (~4–8 frames; fps-dependent) |
| Clear time / place change | Short Dissolve or other low-intrusion transition |
| Contrast (e.g. digital pay → cash) | Direct Cut for visual contrast |
| Ending | Slightly softer transition allowed |

### Prohibited by Default

- spin
- whip
- flash
- heavy zoom transition
- glitch
- exaggerated light effects

Unless Production Brief explicitly requests them.

### Integrity Requirements

Every transition must ensure:

- enough handles
- no gap
- no black frames
- no accidental duration change

---

## 7. Subtitle Strategy

**Default: subtitles ON** unless Brief disables.

Goals: clear information, mobile-readable, not blocking subject.

### Principles

- short phrases
- 1–2 lines per cue
- do not dump full paragraphs at once
- follow semantics, not mechanical word-by-word timing
- maintain natural reading rhythm

### Cue Length

~8–18 Chinese characters per cue (adjust for language rhythm).

Keywords may be emphasized: place names, numbers, core concepts, contrast words, memory hooks.

Emphasis methods (prefer in order):

- font weight
- size
- simple highlight
- subtle pop / fade

**Avoid by default:** bouncing text, karaoke-style per-character coloring, flashy animation — unless Brief requests strong social-media motion style.

### Source Priority

1. Frozen Script
2. Script-aligned transcription
3. transcription

Proper nouns must align with frozen text when available.

---

## 8. Graphics Strategy

Graphics only when they improve understanding.

**Suitable for:** place names, time, numbers, keywords, simple explanations, small callouts.

**Not suitable for:** filling empty space with decorative UI.

Default: **minimal graphics.**

Titles / lower thirds: clean, simple, brief.

---

## 9. Music Strategy

**Default: music ON** unless Brief disables.

Music role: **supportive, not dominant.**

### Suitable Directions

- light lo-fi
- coffee jazz
- understated ambient
- light acoustic
- subtle modern lifestyle

### Avoid

- epic trailer
- horror tension
- dramatic cinematic rise
- sentimental piano overload
- corporate presentation music
- aggressive EDM

Music tempo should match overall narration pace.

For 60–90 seconds: usually **one main track**. Section change only when needed.

---

## 10. Audio Mix Strategy

**Narration always wins.**

Music must sit below narration. Verify by listening and loudness — no fixed dB preset is absolute.

Ducking is allowed.

Must check:

- narration intelligibility
- music masking
- clipping
- unexpected silence
- abrupt music start / end

Music in/out: short fades preferred over hard cuts.

---

## 11. Color Strategy

Target: **natural, clean, coherent.**

Prioritize:

- exposure consistency
- white balance consistency
- reasonable contrast
- skin tone
- source matching

Light unified look is allowed.

**Default prohibit:** heavy teal-orange, high-concentration cinematic LUT, heavy grain, exaggerated halation, crushed blacks, oversaturation — unless Brief requests.

For this genre: **believable realism** beats **cinematic look**.

---

## 12. Effects Strategy

Default: **minimal.**

### Allowed

- subtle dynamic zoom
- gentle push-in
- light vignette when justified
- small emphasis animation
- restrained blur for privacy / background
- simple motion graphics

### Dynamic Zoom

Only when a static or low-variation shot needs slight visual life.

**Never** zoom every shot.

### Motion Blur

Only when speed change or motion effect genuinely requires it.

Third-party OFX: only when current Runtime already has them and L1 confirms availability. **Do not auto-install.**

---

## 13. Repetition Strategy

This genre is highly sensitive to stock repetition.

Check for:

- same source
- same action
- same composition
- same source range

When reusing source:

- change source range, or
- change crop / framing, or
- change narrative purpose

**Not acceptable:** only moving the same clip to a different timeline position.

---

## 14. Ending Strategy

Do **not** force by default:

- slogan
- CTA
- dramatic uplift
- "what do you think?"
- dramatic fade

Unless Brief requests.

Preferred ending:

```
summary / reframe
+ natural life visual
+ ~0.4–0.8 sec visual tail
```

Music may continue briefly then end naturally.

---

## 15. Fallback Policy

When ideal footage is missing, priority:

1. semantic-adjacent real B-roll
2. alternate framing / source range
3. minimal graphic
4. AI supplement

Never use clearly factually wrong visuals because footage is missing.

When choosing between:

- visually beautiful but semantically wrong
- plain but semantically correct

→ **prefer semantically correct.**

---

## 16. Genre QA

L3 must run Genre QA from `references/qa.md` after Universal QA.

Minimum checklist: **OBS-QA-01 through OBS-QA-20.**

Key gates:

- motion naturalness (OBS-QA-01)
- no stock-slideshow feel (OBS-QA-19)
- genre fit (OBS-QA-20)

---

## Brief Override Policy

Production Brief may override non-safety stylistic parameters when explicit:

- subtitles on/off
- music on/off
- transition style requests
- color look requests
- graphics density
- duration extension beyond default range

Safety and factual-integrity rules are **not** overridable by Brief alone.

---

## Runtime Independence

This Skill is **not** bound to DaVinci Resolve, any MCP, or specific tool names.

Strategy is expressed in editorial terms so future Premiere, FFmpeg, or other runtimes can interpret and implement via their own L1 / capability layers.

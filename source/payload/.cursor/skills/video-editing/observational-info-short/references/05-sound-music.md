# Sound & Music

## Style Goal

Keep narration intelligible and credible while supporting observation with ambience, original sound, and light music beds — never a wall-to-wall track that performs emotion over the voice. Sound grammar reinforces human presence, not production showcase.

## Inherit from Common Craft

Consult `video-workflow/knowledge/editing-craft/sound-music.md` for:

- Audio hierarchy defaults (dialogue / narration priority)
- Music arc and section role concepts
- Ambience vs sound design distinction
- Mix verification principles

This Style defines Voice / Original / Ambience / Music / SFX / Silence roles and low-to-medium music presence.

## Style Defaults

### Sound Layer Grammar

| Layer | Role in this Style | Default level |
|-------|-------------------|---------------|
| **Voice** | Primary information carrier; Frozen Voice Master authoritative | Dominant |
| **Original** | Diegetic moments — street, shop, transaction, crowd | High value; preserve authenticity |
| **Ambience** | Continuous environmental bed supporting place feeling | Subtle; under voice |
| **Music** | Sectional emotional scaffolding — not decoration | **low_to_medium** presence |
| **SFX** | Transition or emphasis accent | Sparse; prefer original over synthetic |
| **Silence** | Intentional reset before insight or after contrast | Allowed; valuable |

**Music default:** ON unless Owner disables → record `OWNER_DISABLED`, not defect skip.

**Music structure:** multi-segment allowed — hook entry bed, main low bed, duck or drop for original sound, second track at narrative turn, natural fade at ending. **Not** one track wall-to-wall at uniform level.

**Mix rule:** narration always wins; music below voice; verify by listening.

## Prefer When

- Natural voice with light polish only — clarity, mild warmth, de-ess if needed
- **Original sound** preserved in **BREATH** and **EVIDENCE** beats where diegetic audio adds credibility
- Music enters lightly at hook; maintains low bed under main observation body
- Music ducks or drops during original-sound passages and dense narration clauses
- Second music segment or crossfade at narrative turn (contrast landing, reframe)
- Short fades on music in/out — avoid hard jumps
- Ambience fills spatial feeling without masking consonants
- Intentional silence before key insight line lands

## Allow When

- Light EQ / compression on voice when intelligibility improves and Frozen Voice preserved via non-destructive chain
- Radio or phone timbre on brief quoted segment when narratively motivated
- Transition SFX on rare motivated cuts — not every edit
- Music tail continues briefly under ending visual then fades naturally
- Owner adds music to input folder — treat as production asset, not auto-fetched unknown copyright

## Avoid When

- Music level competes with narration consonants or proper nouns
- Continuous energetic track from 0:00 to end without ducking or segmentation
- Decorative whoosh on every cut
- Replacing real ambient texture with generic SFX library filler
- Crushing dynamics until voice feels broadcast-hard unless Brief requests
- Music swells that perform emotion narration has not earned yet

## Prohibit

- Masking or overpowering narration with music
- Modifying or overwriting Frozen Voice Master destructively
- Fetching unknown-copyright music from internet without Owner-provided asset and legal path
- Fabricating music presence when Brief enabled music but no legal source exists
- SFX density that reads as promo or trailer sound design
- Hard music stops without narrative motivation

## Exceptions

- Brief disables background music → `OWNER_DISABLED`; do not fail Style QA for absence
- Brief requests stronger music presence for specific platform — honor explicit override within voice intelligibility floor
- Automatic ducking (`audio.music.duck`) is not VERIFIED; resolution uses `audio.music.level_under_voice` per capability-policy — static / pre-attenuated music under voice, not equivalent to dynamic ducking envelope
- Single continuous track when only one legal asset provided — still vary effective presence via ducking and sectional gain automation intent

## Trade-offs

| Choice | Gain | Cost |
|--------|------|------|
| low_to_medium music | Credibility, voice clarity | Less emotional propulsion |
| Multi-segment music | Narrative shaping | More edit complexity |
| Original sound priority | Authenticity | May expose noisy locations |
| Sparse SFX | Observational honesty | Less "produced" transition polish |
| Duck under voice | Intelligibility | Music may feel thinner in dense narration |

## Capability Intent

| Sound decision | Logical capability |
|----------------|-------------------|
| Place voice master | `audio.voice.place` |
| Preserve diegetic original | `audio.original_sound.preserve` |
| Place music bed | `audio.music.place` |
| Crossfade between music segments | `audio.music.crossfade` |
| Duck music under voice or original | `audio.music.duck` → fallback `audio.music.level_under_voice` (pre-attenuated level; not dynamic auto-duck) |
| Ambience bed | `audio.ambience.place` |

## Blueprint Mapping

| Blueprint field | Sound use |
|-----------------|------------|
| `sound_music_intent` | e.g., `narration dominant`, `duck for original sound`, `music drop at contrast`, `low bed main` |
| `narrative_function` | **ORIGINAL_SOUND** / **BREATH** → duck or drop music |
| `pacing` | Faster beats may need tighter duck response |
| `capability_requirements` | e.g., `audio.voice.place`, `audio.music.duck`, `audio.original_sound.preserve` |

Section-level music map may live in Blueprint notes when multiple segments planned.

## QA Signals

- Voice clearly intelligible throughout; music never masks key words
- Music presence feels low_to_medium — not constant foreground
- Original sound and ambience contribute authenticity; not sterile voice-over-only bed
- Breath and ambient beats retain environmental texture
- Music segments transition without jarring jumps
- No promo-trailer SFX density
- When music disabled by Owner, absence recorded as intentional — not skipped error

## Reference Cases

**Market breath beat:** Music ducks; original crowd and footsteps rise — 3–6s credibility reset before narration resumes.

**Contrast turn:** First bed fades; second lighter skeptical bed enters at reframe beat — not same loop louder.

**Payment evidence (RC-VIS-001):** Optional faint register or ambient shop sound under narration; music low; never swells over amount or place name spoken.

**Ending tail:** Narration completes; natural life visual continues ~0.4–0.8s with music fade — not abrupt cut to silence.

# Editing Rhythm

## Style Goal

Deliver naturally brisk, conversationally paced observation — informationally clear without news urgency or cinematic lethargy. Rhythm serves narration cadence and beat function, not arbitrary cutting templates.

## Inherit from Common Craft

Consult `video-workflow/knowledge/editing-craft/editing-rhythm.md` for:

- Cut motivation vocabulary (action, reaction, contrast, montage, J/L-cut)
- Pacing factors: information density, emotional temperature, narration cadence, hold and breath
- Motion cadence and fps mismatch risks
- Transition motivation — relationship between shots, not decoration

This Style applies a three-tier rhythm model and soft pacing guidance rather than fixed timers.

## Style Defaults

### Micro / Beat / Macro Rhythm Model

| Tier | Scope | Governs |
|------|-------|---------|
| **Micro** | Within a shot or cue | Motion energy, hold length before cut, subtitle cue timing |
| **Beat** | One narrative unit | Visual change rate, evidence clarity, breath insertion |
| **Macro** | Whole piece | Hook → body → reframe → ending arc; music segment shifts; cumulative density |

**Default cut motivation:** semantic turn, action change, contrast landing, emphasis — not sentence boundaries alone.

**Transition default:** ~70–85% hard / natural cuts; short dissolve only for light scene change.

**Motion default:** real-life action speed; normalize obvious stock slow motion.

**Ending default:** summary or reframe + natural life visual + brief visual tail (~0.4–0.8s soft guidance).

### Soft Pacing Guidance (not fixed timers)

Historical range hints — adapt to narration cadence, asset motion, and beat function:

| Segment | Soft guidance |
|---------|---------------|
| Hook visual change | ~1.5–3.5s between changes |
| Ordinary semantic unit | ~2.5–4.5s |
| Establish hold | ~4–6s when orienting place |
| Dense information | ~1.5–3s |
| Breath / original sound | ~3–6s intentional hold |

These are **SOFT_GUIDANCE** only. A beat may run shorter or longer when narration, motion, or **BREATH** function demands it. Never enforce timers over semantic completeness.

The ranges suggest how often the picture may change. They do not require one Clip per Beat or per narration sentence. When the same action is still playing and no cut has a purpose, keep that passage as one continuous Clip across the beat change.

## Prefer When

- Cut on narration semantic turn or new evidence requirement
- **Action cut** when movement continues across edit and preserves motion continuity
- **Contrast cut** when beat function is REVEAL or CONTRAST
- **Hold** lets evidence or ambient moment land before next claim
- **J-cut / L-cut** when audio lead or trail smooths beat entry without hiding information
- Hard cut between related continuity shots
- Short cross-dissolve (~4–8 frames at timeline fps) for soft location or time shift
- Speed normalization (typically 1.15×–2.0×+) on obvious stock slow motion in walking, hands, payment, vehicles, gestures
- Original-sound breath sections without ordinary captions when beat function is **BREATH**

## Allow When

- Slightly longer establish when place unfamiliarity requires orientation
- Montage compression when narration lists parallel examples — still cut on semantic units, not music bars
- Ending dissolve or softer transition when natural tail benefits from gentle release
- Faster hook pacing when Brief duration is short and hook point is strong
- Mixed-fps sources when cadence risk assessed and motion QA planned

## Avoid When

- Cutting every N seconds regardless of narration or beat function
- Dissolve on every scene change "for polish"
- Retaining obvious slow-motion walking, hands, or payment without normalization evaluation
- Sentence-boundary-only cutting that ignores visual evidence timing
- Stock slideshow: unrelated beautiful clips timed to voice without semantic motivation
- Anxious cutting — rapid unmotivated changes that feel TikTok-adjacent or news-urgent

## Prohibit

- Spin, whip, flash, heavy zoom, glitch transitions as default grammar
- Transitions applied without handles verification — gaps and black frames are defects (technical layer), but Style prohibits gratuitous transition density regardless
- `motion = SKIPPED` when abnormal slow motion is present in action footage
- Forced ending CTA, slogan card, or "what do you think?" unless Brief requests
- Pacing that makes observational narration feel like breaking news ticker

## Exceptions

- Owner local intent requests faster contrast beat or longer contemplative hold on named beat
- Brief disables transitions feature — hard cuts only
- No verified speed-change route: prefer alternate source or alternate range before accepting unnatural motion
- Single dissolve at ending when emotional release benefits and Brief allows

## Trade-offs

| Choice | Gain | Cost |
|--------|------|------|
| Semantic cutting | Alignment, credibility | Requires more editorial judgment |
| Hard-cut dominance | Observational honesty | Less "produced" smoothness |
| Motion normalization | Believable everyday speed | May shorten usable clip length |
| Breath holds | Authenticity, original sound | Slows information throughput |
| Soft dissolve transitions | Gentle scene shift | Risk of ad-like softness if overused |

## Capability Intent

| Rhythm decision | Logical capability |
|-----------------|-------------------|
| Primary edit join | `edit.cut` |
| Light scene-change dissolve | `edit.transition.cross_dissolve` → fallback `edit.transition.basic` |
| Clip in/out to beat range | `visual.trim` |
| Slow motion normalization | `visual.motion.speed_change` |
| Static reframe instead of kinetic transition | `visual.reframe.static` |
| Preserve diegetic audio in breath beats | `audio.original_sound.preserve` |
| Duck music under original sound | `audio.music.duck` |

## Blueprint Mapping

| Blueprint field | Rhythm use |
|-----------------|------------|
| `pacing` | Beat-level hint: `slow` \| `medium` \| `medium-fast` \| `fast` |
| `narrative_function` | Informs hold vs cut density (**BREATH** longer, dense info shorter) |
| `source_content_range` | Anchors cut points to narration segment |
| `sound_music_intent` | e.g., "narration dominant," "duck for original sound" |
| `subtitle_graphics_intent` | Coordinates caption-free breath moments |
| `capability_requirements` | e.g., `edit.cut`, `visual.motion.speed_change`, `edit.transition.cross_dissolve` |

Macro rhythm emerges from ordered beats — no separate Macro field required if beat sequence is coherent.

## QA Signals

- Cuts feel motivated by story or information, not template timer
- No anxious unmotivated cutting; no stock slideshow stall
- Motion in action footage looks naturally paced
- Transitions restrained; majority hard cuts
- Original-sound / breath moments present where Style expects authenticity
- Ending has natural visual and audio tail; not abrupt
- Piece pacing matches conversational observation — not news urgency or cinematic drift

## Reference Cases

**Sunday closure contrast beat:** Hard **contrast cut** from open-market expectation footage to closed-door **EVIDENCE** — cut lands on narration pivot, not mid-word filler.

**Payment slow-motion stock:** Evaluate **NORMALIZE** via `visual.motion.speed_change` before accept; if still unnatural, **REPLACE** source (RC-VIS-001 action readability principle extends to motion cadence).

**Breath before reframe:** 3–6s **ORIGINAL_SOUND** hold — captions intentionally absent; distinguish from defect in Style QA (`08-qa.md`).

**Hook efficiency:** First beats deliver place, question, or contrast — soft 1.5–3.5s visual change guidance as starting point, not law.

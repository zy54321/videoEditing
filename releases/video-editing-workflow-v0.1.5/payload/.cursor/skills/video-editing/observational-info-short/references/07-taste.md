# Taste

## Style Goal

Provide the aesthetic coordinate system for `observational-info-short` — how this Style resolves conflicts between professional craft options, what tensions it cultivates on purpose, and how to detect taste failure before technical QA runs.

## Inherit from Common Craft

Consult:

- `video-workflow/knowledge/editing-craft/aesthetic-qa.md` — four-level rule hierarchy (safety, factual integrity, Style, Owner review)
- `video-workflow/knowledge/editing-craft/reference-cards/` — structured preference cases
- Dimension references `01`–`06` — operationalized taste choices

Common Craft explains what options exist. Taste explains which options belong to this genre.

See also `style-profile.yaml` for machine-readable coordinates.

## Style Defaults

### Taste Identity Axes

Primary poles (strong preference toward left term):

| Axis | Position |
|------|----------|
| **Natural > Designed** | Strong |
| **Authentic > Spectacular** | Strong |
| **Clear > Clever** | Strong |
| **Restrained > Showy** | Strong |
| **Human > Corporate** | Strong |
| **Observation > Performance** | Strong |

### Taste Profile Coordinates (from style-profile.yaml)

High: naturalism, camera stability, breathing room, ambience value, silence value, realism priority

Low: polish, visual energy, camera assertiveness, graphic expressiveness, subtitle expressiveness, music assertiveness, color stylization, effects visibility

Medium: psychological distance, shot variety, cut density

**Format note:** 9:16, duration, and platform come from Production Brief — they are format adaptation, not taste identity.

### Desired Tensions

Productive tensions this Style intentionally maintains:

| Tension | Balance |
|---------|---------|
| Clear information vs atmospheric texture | Lean clear; texture via breath and original sound, not fog |
| Engaging pace vs observational calm | Naturally brisk without news anxiety |
| Polish vs credibility | Light polish; reject glossy ad finish |
| Visual variety vs shot-function discipline | Variety serves beats — not montage for montage sake |
| Music support vs voice authority | Music felt but not heard over words |
| Readable captions vs clean frame | Captions present; keyword emphasis sparse |

### Perceptual Effects Model

When choosing between craft-valid options, predict audience perception:

| Perceptual effect | Typical trigger in this Style | Desired? |
|-------------------|------------------------------|----------|
| **Credibility** | Medium stable evidence, natural motion, original sound | Yes — default |
| **Peer intimacy** | Conversational voice, eye-level framing, restrained captions | Yes |
| **Clarity** | Semantic cutting, readable captions, evidence alignment | Yes |
| **Spectacle** | Aggressive push-in, heavy grade, whip transitions | No — unless local intent |
| **Promo gloss** | Ad posing stock, constant music wall, keyword 花字 | No |
| **News urgency** | Anxious cutting, ticker graphics, hard broadcast mix | No |
| **Faux cinema** | Teal-orange, shallow-DoF beauty inserts, trailer SFX | No |
| **Corporate neutrality** | Sterile VO bed, template lower thirds, brand-safe emptiness | No |

### Taste Failure Modes

| Failure mode | Symptoms | Likely cause |
|--------------|----------|--------------|
| **Over-designed** | Every shot pushed, graded, vignetted, keyword-highlighted | Craft tools applied without Style filter |
| **Fake cinematic** | Shallow focus beauty, dramatic angles on mundane evidence | Imported trailer grammar |
| **Ad-like** | Ad posing stock, music wall, promo transitions, aggressive zoom | Stock montage + spectacle defaults |
| **News-like** | Rapid cuts, urgent graphics, broadcast hard voice | Misapplied short-form urgency |
| **Corporate** | Sterile bed, template graphics, risk-averse emptiness | Brand-safe over human |
| **Stock slideshow** | Beautiful unrelated clips, slow motion uncorrected, weak semantic fit | Filename guessing, no beat function |
| **Subtitle performance** | All-line decoration, captions overpower subject | Typography expressiveness creep |
| **Music over voice** | Consonants masked, emotional swells over unearned lines | Music assertiveness drift |
| **Authenticity loss** | No original sound, no breath, sterile VO-only world | Skipped ambience and silence value |

### Preference Logic

Decision procedure when multiple craft-valid options remain:

```
Context → Options → Preferred
```

1. **Context:** beat `narrative_function`, `attention_target`, `audience_effect`, Owner Author Intent (if any), asset reality
2. **Options:** enumerate craft-valid choices (see reference-cards pattern)
3. **Preferred:** select option that maximizes Taste Identity axes and Desired Tensions

Document `because` and `tradeoff` in Blueprint notes or reference-card pattern when choice is non-obvious.

## Prefer When

- Preference logic favors credibility and clarity over spectacle
- Reference card or analogous case exists for beat context
- `style-profile.yaml` coordinates break tie toward naturalism and restraint
- Global Owner intent aligns with observational identity (warmer, clearer, more skeptical) — shape within bounds
- Perceptual effect target is peer intimacy or clarity

## Allow When

- Local Owner intent explicitly requests heightened contrast, reveal, or energy on named beat
- Creative Direction adjusts presentation refinement (playful captions, warmer look) without axis inversion
- Brief overrides non-safety stylistic parameter with explicit value
- Tradeoff consciously accepted and noted (e.g., sacrifice cinematic punch for credibility — RC-VIS-001)

## Avoid When

- Option increases spectacle without narrative job
- "Looks more professional" is the only justification
- Default craft close-up / push-in / dissolve applied generically
- Taste drift accumulates across beats until genre unrecognizable
- Automation bias toward highest-energy asset in search results

## Prohibit

- Inverting core axes (Designed > Natural as default) without Style change
- Using taste logic to override factual integrity or Frozen assets
- Inventing Owner Author Intent to justify spectacle
- Declaring taste PASS when piece reads primarily as ad, news, trailer, or corporate promo

## Exceptions

- Brief explicitly authorizes different genre signals (e.g., campaign variant) — document override
- Reference card `avoid_when` clause: local Owner intent requests heightened contrast — prefer B over A for that beat only
- Single beat exception does not migrate to global Style rewrite

## Trade-offs

| Taste choice | Wins | Loses |
|--------------|------|-------|
| Natural > Designed | Trust, shareability in observation niche | Thumbnail punch vs glossy competitors |
| Clear > Clever | Comprehension, replay value | Meme-style share clips |
| Restrained music | Voice authority | Emotional propulsion |
| Observation > Performance | Authenticity | Charisma-forward presenter energy |
| Sparse effects | Content focus | Platform "premium" signaling |

## Capability Intent

Taste does not introduce new capabilities — it prioritizes among those in `capability-policy.yaml`:

- Prefer `visual.reframe.static` over `visual.motion.push_in` when credibility tie-break needed
- Prefer `edit.cut` over `edit.transition.cross_dissolve` when showiness tie-break needed
- Prefer `audio.original_sound.preserve` and `audio.music.duck` when authenticity vs bed conflict
- Forbid default path to `visual.motion.aggressive_zoom`
- Prefer `color.primary_balance` + `color.shot_match` over `color.look.apply`

## Blueprint Mapping

| Blueprint element | Taste use |
|-------------------|-----------|
| `author_intent.global` | Shapes whole-piece warmth or skepticism within axes |
| `author_intent.local` / beat `author_intent` | Beat-scoped exception documented |
| Beat `audience_effect` | Selects perceptual effect target |
| Beat notes `because` / `tradeoff` | Records preference logic outcome |
| `capability_requirements` | Must not contradict taste forbidden list |

Load `style-profile.yaml` before beat planning to anchor coordinates.

## QA Signals

- Overall genre feel: friend sharing observation — not presenter, brand, or trailer
- No accumulated taste failure modes detected
- Axis violations absent unless documented Brief / local intent exception
- Preference logic traceable for non-obvious visual or sound choices
- Desired tensions present: clear yet textured, brisk yet calm, polished yet credible
- 9:16 treated as format adaptation — taste identity stable across aspect ratios

## Reference Cases

**RC-VIS-001** (`reference-cards/RC-VIS-001.yaml`):

- Context: **EVIDENCE**, payment hands, curiosity → recognition
- Options: A medium stable neutral vs B aggressive push-in shallow depth
- Preferred: **A** — because observational treats payment as everyday proof
- Tradeoff: sacrifices cinematic punch for credibility
- avoid_when: local Owner intent requests heightened contrast or reveal

**Slow stock walking:** Preference logic → normalize or replace before accept; authenticity axis beats spectacle.

**Keyword caption creep:** Context main body beat → Options plain caption vs all-line emphasis → Preferred plain primary — keyword axis low expressiveness.

**Music wall detection:** Context dense narration body → Options continuous loud bed vs ducked low bed → Preferred duck — voice authority axis.

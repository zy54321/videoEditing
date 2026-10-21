# Color, Look & Effects

## Style Goal

Deliver natural, clean, coherent imagery with light polish — believable light, consistent shot-to-shot continuity, and effects only when narratively or rhythmically motivated. Processing serves credibility, not genre cosplay.

## Inherit from Common Craft

Consult `video-workflow/knowledge/editing-craft/color-look-effects.md` for:

- Correction vs match vs look vs effect ordering
- White balance, exposure, and skin tone principles
- Effect motivation — relationship to story, not feature demo

This Style stays near correction + light polish; stylization is exception.

## Style Defaults

**Processing order (mandatory intent):**

```
Correction → Match → Look → Effect
```

| Stage | This Style target |
|-------|-------------------|
| **Correction** | Reasonable exposure, neutral white balance, recover clipping only when credible |
| **Match** | Adjacent and related shots feel like same time and place |
| **Look** | Subtle warmth or mild contrast acceptable; no heavy grade identity |
| **Effect** | Minimal — motivated push-in, light vignette, privacy blur, simple motion graphic |

**Look identity:** Natural, Clean, Coherent, Slightly polished.

**Effects density:** very low — never "every shot has an effect."

## Prefer When

- Primary balance and shot-to-shot match before any creative LUT
- Mild saturation control; believable skin tone when people present
- Subtle warmth when narration tone is conversational-friendly
- Gentle push-in on static evidence plate when attention needs soft guide (see `02-visual-language.md`)
- Light vignette only when it helps subject isolation without mood melodrama
- Privacy blur or background softening when ethics or Brief require
- Simple motion graphics for place name or number when footage alone is abstract

## Allow When

- Brief requests specific warm or cool bias for platform consistency
- Single beat receives slightly stronger contrast when Owner local intent requests heightened reveal — beat-scoped only
- Grain or texture only if source already carries it and removal would feel over-designed
- Verified light look route when correction and match complete

## Avoid When

- Heavy teal-orange blockbuster grade on everyday street footage
- Crushed blacks and clipped highlights for "cinematic" contrast
- Extreme LUT as first move before match
- Vignette on every shot
- Push-in zoom on every static plate
- OFX stacking to prove tool availability
- Color breaks between adjacent shots with no narrative motivation

## Prohibit

- Stylization that makes observational footage read as travel ad or trailer
- Effect chains that dominate subject or narration readability
- `visual.motion.aggressive_zoom` as color-adjacent attention hack
- Auto-install third-party plugins or effects not already in verified runtime
- Declaring color PASS without verified route when automation cannot inspect output

## Exceptions

- Brief explicitly requests stylized look (e.g., documentary bleach bypass) — honor as Brief override within safety
- Mixed source footage with irreconcilable white balance — prefer alternate source; honest match notes in Blueprint
- No verified look route: stop at correction + match; do not fake graded deliverable
- Beat-level Owner intent for stronger contrast on one reveal — apply locally, revert for body beats

## Trade-offs

| Choice | Gain | Cost |
|--------|------|------|
| Correction-first | Credibility, consistency | Less instant "premium" feel |
| Light look vs heavy grade | Observational honesty | Less platform-thumbnail punch |
| Motivated effects only | Focus on content | Fewer dynamic visuals |
| Shot match discipline | Coherent piece | Time on secondary clips |
| Minimal vignette / push | Subtle guidance | Easy to overuse if unchecked |

## Capability Intent

| Color / effect decision | Logical capability |
|-------------------------|-------------------|
| Primary balance / exposure | `color.primary_balance` |
| Shot-to-shot match | `color.shot_match` |
| Light creative look (optional) | `color.look.apply` |
| Motivated gentle push-in | `visual.motion.push_in` → fallback `visual.reframe.static` |
| Speed change for motion credibility | `visual.motion.speed_change` |

Effects without verified capability remain editorial intent only — do not claim execution.

## Blueprint Mapping

| Blueprint field | Color / effect use |
|-----------------|-------------------|
| `color_effect_intent` | Default `natural`; beat exceptions noted |
| `narrative_function` | **REVEAL** may allow local contrast; **EVIDENCE** prefers neutral |
| `visual_intent` | Drives whether push-in or graphic is motivated |
| `capability_requirements` | e.g., `color.primary_balance`, `color.shot_match`, optional `color.look.apply` |

Whole-piece look defaults in Blueprint notes; beat-level overrides in beat entries only.

## QA Signals

- Shot-to-shot color feels coherent — no unexplained breaks
- Exposure and white balance believable for everyday locations
- No default heavy stylization or trailer grade
- Effects sparse and motivated — not per-shot showcase
- Skin tones natural when people present
- Push-in / vignette / blur used with restraint
- Piece still reads observational after finishing — not ad glossy or faux cinematic

## Reference Cases

**RC-VIS-001 payment counter:** Neutral match across adjacent shop clips; no dramatic grade pushing orange/teal; evidence readability priority over mood.

**Mixed lighting market:** Match to dominant ambient; avoid one clip heavily cooled while neighbors warm — breaks observational continuity.

**Static sign evidence:** Optional gentle push-in only if reframing insufficient; no simultaneous vignette + grade + zoom stack.

**Ending natural tail:** Look stable through fade — no last-second saturation bump for "pop."

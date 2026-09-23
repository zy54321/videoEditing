# Typography & Graphics

## Style Goal

Make narration readable on mobile without turning captions into performance. Typography supports comprehension first — restrained personality, clear hierarchy, semantic line breaks, and intentional caption-free moments when ambience or breath beats demand silence on screen.

## Inherit from Common Craft

Consult `video-workflow/knowledge/editing-craft/typography-graphics.md` for:

- Subtitle readability physics (line length, duration, contrast)
- Caption vs title vs graphic hierarchy
- Safe zones and vertical layout constraints
- Semantic segmentation principles

This Style sets pixel-width targets, expressiveness ceiling, and caption-type roles.

## Style Defaults

**Subtitles:** ON by default unless Brief disables.

**Layout contract:**

- Target width **76–78%** of frame width; hard ceiling **80%**
- Maximum **2 lines** per cue
- **Semantic wrap** — break at phrase or clause boundaries, not character-count chop alone
- Minimum readable size — do not shrink text to fit bad segmentation

**Caption types:**

| Type | Role | Default density |
|------|------|-----------------|
| **Primary caption** | Full narration coverage | Dominant |
| **Keyword emphasis** | 1–3 key terms per section (place, number, contrast word) | Sparse |
| **Title / section** | Hook label or mini-chapter only | Minimal |

**Graphics:** minimal — place names, time, numbers, simple callouts when understanding improves. No decorative UI filler.

**Personality:** restrained, readable, conversational — not meme 花字, not news ticker flash.

## Prefer When

- Standard primary caption tracks main narration with semantic cue breaks
- Keyword emphasis highlights proper noun, number, or contrast term already in Frozen Script / content authority — emphasis changes layout and must stay within the same width discipline (76–80% band)
- Emphasis remains **sparse** — emphasized number or proper noun must stay semantically intact (no splitting `40%` across lines)
- Cue split follows narration breath or semantic unit — one idea per cue where possible
- Caption-free moments during intentional **BREATH** or **ORIGINAL_SOUND** beats (3–6s soft guidance)
- Lower-third simple title at hook or section pivot only
- Overflow handled by semantic wrap first, then cue split — never illegible shrink

## Allow When

- Creative Direction requests slightly more playful keyword color or weight within readability bounds
- Brief disables keyword emphasis — primary caption only
- Single section title card at hook when it accelerates comprehension
- Intentional short gap before hook caption when opening visual establishes place silently (< few seconds)

## Avoid When

- Every line receives keyword styling — hierarchy collapses
- Captions block core subject (face, hands, payment action) persistently
- Character-count wrapping breaks proper nouns or numbers across lines awkwardly
- Long single cues exceed two lines instead of splitting semantically
- Decorative stickers, arrows, and frames on every beat
- Captions continue through intentional ambient breath designed for caption-free relief

## Prohibit

- All-lines decorative 花字 treatment
- News-style lower-third breaking banners with urgent motion
- Captions that alter Frozen Script facts, numbers, or proper nouns
- Shrinking below readable mobile size to avoid splitting cues
- Graphics that imply specific evidence the footage does not support
- Treating timeline subtitle presence as deliverable PASS without rendered artifact check

## Exceptions

- Brief explicitly requests higher graphics density or branded template — honor within Style readability floor
- Accessibility need for larger type or higher contrast when Brief specifies
- Frozen Script language mismatch requires presentation-only re-segmentation without semantic change
- No pixel-width layout route verified: fall back to semantic segmentation only (`subtitle.segment.semantic`) and flag layout QA gap

## Trade-offs

| Choice | Gain | Cost |
|--------|------|------|
| 76–78% width | Comfortable mobile reading | Less edge-to-edge graphic impact |
| Semantic wrap | Natural phrasing | More editorial segmentation effort |
| Sparse keyword emphasis | Clear hierarchy | Less visual "pop" |
| Caption-free breath moments | Authenticity, visual rest | Momentary comprehension reliance on audio only |
| Minimal graphics | Clean observational feel | Fewer on-screen anchors for abstract facts |

## Capability Intent

| Typography decision | Logical capability |
|---------------------|-------------------|
| Semantic cue segmentation | `subtitle.segment.semantic` |
| Basic caption render | `subtitle.render.basic` |
| Pixel-width layout targeting 76–78% | `subtitle.layout.pixel_width` → fallback `subtitle.segment.semantic` |
| Keyword emphasis styling | `subtitle.style.keyword_emphasis` (optional) |
| Deliverable subtitle layout verification | `qa.subtitle.layout` |

Functional captions must not block on unknown decorative style tokens.

## Blueprint Mapping

| Blueprint field | Typography use |
|-----------------|----------------|
| `subtitle_graphics_intent` | e.g., `standard caption`, `keyword on place names`, `caption-free breath` |
| `narrative_function` | **BREATH** / **ORIGINAL_SOUND** → caption-free allowance |
| `source_content_range` | Maps cues to narration segments |
| `author_intent` | Local request for quieter captions or emphasis in one beat |
| `capability_requirements` | e.g., `subtitle.segment.semantic`, `subtitle.layout.pixel_width` |

Coordinate with `sound_music_intent` when caption-free moments align with ducked music or original sound.

## QA Signals

- Subtitles readable at mobile scale; max two lines; width within 76–80% band
- Semantic breaks feel natural — not arbitrary chops
- Primary caption dominates; keyword emphasis sparse and accurate to content authority
- Intentional caption-free moments distinguishable from coverage defects
- Subtitles do not overpower frame or obscure evidence subjects persistently
- Proper nouns match Frozen Script when frozen text exists
- Personality stays conversational — not ad promo, not meme chaos, not news urgency

## Reference Cases

**Place name keyword:** Narration introduces "Vienna Sunday trade rule" — keyword emphasis on **Vienna** and **Sunday** only; remainder primary caption plain.

**Breath beat caption-free:** Market ambience **ORIGINAL_SOUND** — no captions for ~4s; narration absent or ambient; not a defect.

**Contrast number:** "90% of shops closed" — number receives keyword emphasis; semantic wrap keeps percentage intact on one line if possible.

**RC-VIS-001 alignment:** Payment evidence beat — captions sit in lower safe zone; medium shot keeps hands visible above subtitle band.

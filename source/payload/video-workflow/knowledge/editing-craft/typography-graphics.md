# Typography & Graphics — Common Craft

## Typography Principles

- **Font hierarchy** — title > section > body caption
- **Size, weight, tracking, line spacing** — affect readability
- **Contrast** — text vs background (outline, shadow, plate)
- **Safe zone** — keep text inside readable margins
- **Actual pixel width** — not character count alone
- **Semantic wrapping** — break at phrases, not arbitrary mid-word
- **Max line count** — typically 2 for short-form captions

---

## Subtitle Width Contract (Craft)

**Character count is NOT layout authority.**

Layout authority:

```
font + font size + tracking + actual rendered text width + canvas width
```

### Target width (9:16 short-form default)

- **Target:** ~76–78% of frame width
- **Hard ceiling:** 80%
- **Max lines:** 2

### Overflow policy

```
semantic wrap → cue split
```

**Not:** shrink font indefinitely to fit.

---

## Graphics Types

- title / section title
- lower third
- keyword emphasis
- data callout
- icon / simple motion graphic

Graphics must improve understanding — not decorate empty space.

---

## Validation Note

This document defines **craft contract only**.

Real subtitle render verification belongs to Production / Acceptance (`CAPABILITY_VALIDATION_REQUIRED` when route unverified).

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

## Styled Runs & Composite Bounds (08E-A)

Subtitles are **not** `text + one font size`.

- A cue may contain multiple **styled runs** (normal phrase, enlarged keyword, key number).
- Each run resolves to concrete typography metrics at **L1** (size, weight, tracking).
- **Composite line width** = measure(run₁) + measure(run₂) + … — never character-count heuristics on the whole cue at base size.
- After emphasis changes size, **re-layout is mandatory** before width judgment.
- Line breaks occur only at **semantic run boundaries** (`prefer` / `allow` / `forbid`).
- **Preflight ≠ final renderer truth** — System.Drawing (or equivalent) preflight does not prove Resolve/Fusion/Text+ pixel parity until Runtime Validation (08E-B).

---

## Validation Note

This document defines **craft contract only**.

Real subtitle render verification belongs to Production / Acceptance (`CAPABILITY_VALIDATION_REQUIRED` when route unverified).

Pre-render layout preflight (`subtitle-layout-preflight.ps1`) is **L1 inventory / planning QA** — not a substitute for post-render artifact visual QA.

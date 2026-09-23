# Subtitle Layout Contract (L1)

## Layer ownership

| Layer | Responsibility |
|-------|----------------|
| L2 Style | WHAT emphasis matters — semantic roles, sparse keyword rules, width discipline |
| L3 Blueprint | `subtitle_typography_intent` — caption mode, emphasis targets (no Runtime params) |
| L1 | Styled runs, typography resolution, measurement, line layout, preflight QA |
| L0 Runtime | Actual renderer (Resolve / Fusion / Text+) — **parity not assumed in 08E-A** |

**L2 decides emphasis semantics. L1 resolves concrete typography and layout. L0 renderer parity requires Runtime Validation (08E-B).**

---

## Artifacts

| File | Role |
|------|------|
| `subtitle-layout-request.json` | Layout request schema example |
| `subtitle-layout-result.json` | Layout result schema example |
| `tools/subtitle-layout-preflight.ps1` | Deterministic preflight (Windows / System.Drawing) |

---

## Request contract

- `canvas.width_px` / `height_px` — layout coordinate space
- `layout.target_width_ratio` — preferred band (e.g. 0.76–0.78)
- `layout.hard_ceiling_ratio` — absolute width ceiling (e.g. 0.80)
- `layout.max_lines` — maximum lines per cue
- `layout.safe_margins` — safe area inset (independent of Style width ratios)
- `typography` — L1 concrete metrics (font, base size, `emphasis_style_mapping` only — no duplicate `font_style` field)
- `cues[].runs[]` — atomic styled runs with `break_after`: `prefer` | `allow` | `forbid`

**Runs are measured individually.** Composite line width = sum(run widths) + tracking/stroke allowances.

---

## Typography resolution

`emphasis_level` on each run resolves to concrete metrics via `typography.emphasis_style_mapping`:

- size multiplier
- font style (Regular / Bold)
- tracking adjustment

These values are **L1 execution input**, not L2 Style authority.

---

## Frame width vs safe area (Style authority)

Style width ratios apply to **frame width**, not safe-area width:

```
style_target_width_px   = frame_width_px × target_width_ratio
style_hard_ceiling_px   = frame_width_px × hard_ceiling_ratio
safe_area_width_px      = frame_width_px - left_margin - right_margin
effective_ceiling_px    = min(style_hard_ceiling_px, safe_area_width_px)
```

Canonical width ratio denominator: **frame width** (`max_line_width_ratio_frame`).

`max_line_width_ratio_safe_area` is informational only — must not impersonate Style ratio.

## Width bands

| Condition | Band |
|-----------|------|
| max line width ≤ style target (frame-based) | `WITHIN_TARGET` |
| style target < width ≤ effective ceiling | `ABOVE_TARGET_WITHIN_CEILING` |
| width > effective ceiling | `ABOVE_CEILING` / overflow |

---

## Line layout resolver (`Resolve-SubtitleLineLayout`)

Deterministic search over legal break subsets — **not** greedy prev-boundary-only wrap.

Selection order when multiple layouts are legal:

1. All lines ≤ `effective_ceiling_px`
2. `line_count` ≤ `max_lines`
3. More `prefer` boundaries used at line ends
4. Width balance near frame-based style target (without exceeding hard ceiling)
5. Fixed tie-break on break indices

Synthetic width tests may call the resolver directly (no font required).

## Fail-closed validation

| Input | Policy |
|-------|--------|
| missing / empty `emphasis_level` | → `normal` |
| unknown `emphasis_level` | → `EMPHASIS_LEVEL_UNSUPPORTED` |
| unknown `break_after` | → `BREAK_POLICY_UNSUPPORTED` |
| unknown mapping `font_style` | → `FONT_STYLE_UNSUPPORTED` |
| unavailable font style on resolved family | → `FONT_STYLE_UNAVAILABLE` |
| invalid canvas / margins / ratios / empty runs | → fail closed |

Base style authority: `emphasis_style_mapping.normal.font_style` only (no `typography.font_style`).

## Wrap policy

1. Break only at **run boundaries**
2. Honor `break_after`: `forbid` blocks; `prefer` / `allow` are legal split points
3. No indefinite font shrinking
4. No Frozen Script content modification
5. If cannot satisfy `max_lines` within `effective_ceiling_px` → `CUE_SPLIT_REQUIRED`

**Split evidence:** `split_candidates[]` lists only `prefer` / `allow` boundaries. Atomic run wider than ceiling with no internal break → `NO_LEGAL_INTERNAL_BREAK`.

**L1 detects + evidences split. L3 re-segments cues / timing.**

## Measurement honesty

- Backend: System.Drawing per-run measurement
- Per-run `stroke_px` / `visual_padding_px` may **conservatively over-estimate** composite bounds
- Preflight PASS does **not** prove Resolve / Fusion / Text+ renderer parity (08E-B)

---

## QA layers

1. **Pre-render Layout Preflight** — measured width, lines, content preservation, split detection
2. **Timeline / Route QA** — route identity, planned vs executed path
3. **Post-render Artifact QA** — actual pixels in deliverable

**Preflight PASS ≠ Final Artifact PASS** (renderer parity unvalidated in 08E-A).

---

## Capability truth (08E-A)

| Logical ID | Status | Notes |
|------------|--------|-------|
| `subtitle.layout.pixel_width` | AVAILABLE_UNVERIFIED | Deterministic preflight foundation exists; Resolve renderer parity not validated |
| `subtitle.style.keyword_emphasis` | AVAILABLE_UNVERIFIED | Isolated StyledTextCLS SIZE verified; production overlay route partial; first Production uses native DRT fallback |
| `subtitle.segment.semantic` | VERIFIED | Does NOT guarantee pixel width |

---

## Route truth (documentation hook)

Execution records should distinguish:

- requested capability
- resolved capability
- planned route
- actual executed route
- route evidence

Silent drift (e.g. planned `native_drt_subtitles` vs executed `timeline_ai.create_subtitles`) must be detectable in L3 — not silent PASS.

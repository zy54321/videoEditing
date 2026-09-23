# Deterministic Subtitle & Typography Pipeline (Stage 08E)

## Problem

Short-form captions need **pixel-width discipline** (target band + hard ceiling) while supporting **inline keyword emphasis** that changes measured width per run. Character-count heuristics and single-font-size assumptions cause silent overflow and false QA PASS.

N02 history: `subtitle.layout.pixel_width` → `subtitle.segment.semantic` with **high** degradation — semantic segmentation does not guarantee pixel width.

---

## Layer ownership

| Layer | Owns |
|-------|------|
| **L2 Style** | Width band (e.g. 76–78% target, 80% ceiling), max lines, semantic wrap rules, sparse emphasis policy |
| **L3 Blueprint** | `subtitle_typography_intent` — caption mode, emphasis targets (`text`, `semantic_role`, `intensity`) |
| **L1** | Styled runs, typography resolution, System.Drawing measurement, line layout, preflight QA |
| **L0 Runtime** | Resolve / Fusion / Text+ render — **parity requires 08E-B validation** |

**Frozen principle:** L2 decides emphasis semantics. L1 resolves concrete typography and layout. L0 renderer parity requires Runtime Validation.

---

## Artifacts (08E-A)

| Path | Role |
|------|------|
| `templates/subtitle-layout-request.json` | Request schema example |
| `templates/subtitle-layout-result.json` | Result schema example |
| `templates/subtitle-layout-reference.md` | L1 contract |
| `tools/subtitle-layout-preflight.ps1` | Deterministic preflight CLI |
| `tools/lib/subtitle-layout-engine.ps1` | Layout engine (dot-sourced) |

Blueprint additions: optional `subtitle_typography_intent` (backward compatible with `subtitle_graphics_intent` string).

---

## Styled runs

A cue = ordered `runs[]` with:

- `text`, `semantic_role`, `emphasis_level`, `break_after` (`prefer` | `allow` | `forbid`)

Typography resolution maps `emphasis_level` → size multiplier / weight / tracking at **L1 only**.

Composite line width = sum of per-run measurements (+ stroke / tracking allowances).

---

## Frame width vs safe area (R1 authority)

Style width ratios use **frame width** as denominator — not safe-area width:

```
style_target_width_px   = frame_width_px × target_width_ratio
style_hard_ceiling_px   = frame_width_px × hard_ceiling_ratio
safe_area_width_px      = frame_width_px - left_margin - right_margin
effective_ceiling_px    = min(style_hard_ceiling_px, safe_area_width_px)
```

Result fields expose `max_line_width_ratio_frame` (canonical) and optional `max_line_width_ratio_safe_area` (informational).

## Wrap & split

1. `Resolve-SubtitleLineLayout` searches legal break subsets (not greedy prev-boundary only)
2. Break only at run boundaries honoring `break_after` (`prefer` | `allow` | `forbid`)
3. Unknown `emphasis_level` / `break_after` / unsupported `font_style` → **fail closed**
4. No indefinite font shrinking; no Frozen Script content mutation
5. `> effective_ceiling_px` → overflow / wrap path
6. Cannot fit in `max_lines` → `CUE_SPLIT_REQUIRED` with `split_candidates[]` (prefer/allow only); atomic oversized run → `NO_LEGAL_INTERNAL_BREAK`

### Layout selection semantics (R2)

- **Hard ceiling** = legality boundary (must not exceed)
- **Target band** = preferred layout objective (76–78% frame width for observational Style)
- **`prefer`** = semantic preference at a boundary — **not** a mandatory break
- **`line_count ≤ max_lines`** is a constraint, not “fewer lines is always better”
- A single line already **WITHIN_TARGET** should normally remain a single line
- When a legal `prefer` split yields all lines within target while a one-line layout is only `ABOVE_TARGET_WITHIN_CEILING`, the split is preferred

Candidate ranking tiers (deterministic):

1. All lines within target band
2. Some lines above target but all ≤ effective ceiling
3. Within tier: target fit → `prefer` boundary satisfaction → line count (tie-break) → fixed break-index order

Width bands:

- `WITHIN_TARGET` (vs frame-based style target)
- `ABOVE_TARGET_WITHIN_CEILING` (warning — e.g. 79% frame when target 76–78%)
- `ABOVE_CEILING` (overflow vs effective ceiling)

**Typography authority:** `emphasis_style_mapping.normal.font_style` is the base style — no duplicate `typography.font_style` field.

**Measurement honesty:** System.Drawing per-run measurement; stroke/padding may conservatively over-estimate. `subtitle.layout.pixel_width` remains `AVAILABLE_UNVERIFIED` until 08E-B.

---

## QA boundary

| Layer | Checks |
|-------|--------|
| Pre-render Layout Preflight | Measured width, lines, content preservation, split detection, font resolution |
| Timeline / Route QA | Planned vs actual route, timeline population |
| Post-render Artifact QA | Actual pixels in MP4 |

**Preflight PASS ≠ Final Artifact PASS**

---

## Capability truth (08E-A — unchanged status)

| Logical ID | Status |
|------------|--------|
| `subtitle.layout.pixel_width` | AVAILABLE_UNVERIFIED |
| `subtitle.style.keyword_emphasis` | UNKNOWN |
| `subtitle.segment.semantic` | VERIFIED (no pixel-width guarantee) |

Contract support ≠ Runtime VERIFIED.

---

## 08E-A vs 08E-B

| Stage | Scope |
|-------|-------|
| **08E-A** (this) | Contract, deterministic preflight tool, tests, documentation — **BUILD only** |
| **08E-B** (future) | Runtime Capability Validation — Resolve burn-in parity, styled render route, possible status upgrades |

---

## Route truth

Execution must record: requested capability → resolved → planned route → actual executed route → evidence. Silent drift (e.g. planned DRT subtitles vs executed `timeline_ai.create_subtitles`) is a defect.

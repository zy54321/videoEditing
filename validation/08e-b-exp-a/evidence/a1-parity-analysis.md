# A1 Parity Analysis — 2026-09-23

## Calibration

| Field | Value |
|-------|-------|
| Anchor | `HELLO TEST` / Arial / Style Regular |
| L1 `base_font_size_px` | 48 |
| L1 predicted width | 297.41 px |
| Selected Text+ `Size` | **0.064** |
| Calibrated actual (A00) | 297 px (Δ 0.41 px) |

## Matrix execution

| Metric | Value |
|--------|-------|
| Cases run | A01–A10 |
| Measurable renders | **10/10** |
| Authority | `gallery_stills.grab_and_export` on `A1-EXP-A` @ `01:00:02:12` |
| Font | Microsoft YaHei UI (L1 alias from `Microsoft YaHei`) |
| Tolerance gate | ±8 px or ±3% |

## Parity result

```
PARITY_PASS = 0 / 10
A1_GEOMETRY_PARITY = FAIL
```

| Case | L1 px | Actual px | Δ px | Notes |
|------|-------|-----------|------|-------|
| A01 | 196 | 172 | −24 | ~12% narrow |
| A02 | 676 | 608 | −68 | ~10% narrow |
| A03 | 843 | 754 | −89 | ~11% narrow |
| A04 | 674 | 601 | −73 | ~11% narrow |
| A05 | 357 | 317 | −40 | ~11% narrow |
| A06 | 820 | 738 | −82 | ~10% narrow |
| A07 | 0 (overflow) | 1079 | — | L1 `CUE_SPLIT_REQUIRED`; Text+ single line full bleed |
| A08 | 0 (overflow) | 1080 | — | same |
| A09 | 0 (overflow) | 1080 | — | same |
| A10 | 680 (1 L1 line) | 303 (max line bbox) | −377 | Text+ honored `\n`; L1 laid out as one line |

## Interpretation

1. **Pipeline validated:** Text+ → rendered frame → PNG → `measure_subtitle_width.py` is repeatable.
2. **Arial-only calibration does not transfer** to Microsoft YaHei UI at the same Text+ `Size` (~10% systematic under-width in Resolve).
3. **Overflow semantics diverge:** L1 refuses / requests split (A07–A09); Text+ renders unsplit ultra-wide lines.
4. **Multi-line:** L1 preflight single-line layout vs explicit newline in Text+ (A10) — not comparable without layout sync.

## YaHei re-calibration rerun (A01–A06)

| Field | Value |
|-------|-------|
| Anchor | A01 `你好世界` |
| Text+ Size | **0.073** |
| Result | **6/6 PASS** |

| Case | L1 px | Actual px | Δ px | Status |
|------|-------|-----------|------|--------|
| A01 | 196 | 196 | 0 | PASS |
| A02 | 676 | 694 | +18 | PASS |
| A03 | 843 | 860 | +17 | PASS |
| A04 | 674 | 686 | +12 | PASS |
| A05 | 357 | 362 | +5 | PASS |
| A06 | 820 | 841 | +21 | PASS |

Artifact: `evidence/a1-parity-matrix-yahei-a01-a06.json`

**Implication:** Per-font Text+ `Size` mapping is required; a single global Size does not span Arial ↔ YaHei.

## YaHei overflow rerun (A07–A09) @ Size 0.073

| Case | L1 status | L1 ceiling | Actual px | Result |
|------|-----------|------------|-----------|--------|
| A07 | `CUE_SPLIT_REQUIRED` | 864 | **1080** (100% frame) | FAIL_OVERFLOW |
| A08 | `CUE_SPLIT_REQUIRED` | 864 | **1080** | FAIL_OVERFLOW |
| A09 | `CUE_SPLIT_REQUIRED` | 864 | **1080** | FAIL_OVERFLOW |

**3/3 measurable**, **0/3 width parity** — not a font-size issue. L1 refuses unsplit layout (`max_line_width_px=0`); Text+ still renders one ultra-wide line edge-to-edge (+216 px vs hard ceiling).

Artifact: `evidence/a1-parity-matrix-yahei-a07-a09.json`

## YaHei A10 multi-line @ Size 0.073

| Variant | L1 ref | Actual | Δ | Status |
|---------|--------|--------|---|--------|
| Two-line (`\n`), line 1 | 340 px/run | 345 px | +5 | PASS |
| Two-line (`\n`), line 2 | 340 px/run | 343 px | +3 | PASS |
| Single-line concat | 680 px | 691 px | +11 (1.6%) | PASS |

**Layout note:** L1 `line_count=1` (both runs on one line); Text+ with `\n` renders 2 lines — semantic mismatch, but **per-line geometry parity holds**.

Artifact: `evidence/a1-parity-matrix-yahei-a10.json`

## Capability

`subtitle.layout.pixel_width` remains **AVAILABLE_UNVERIFIED** for production — YaHei Text+ parity on A01–A06 + A10 geometry; A07–A09 overflow + Deliver (A2) still open.

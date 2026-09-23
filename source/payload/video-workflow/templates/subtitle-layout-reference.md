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
- `layout.safe_margins` — reduce usable width inside canvas
- `typography` — L1 concrete metrics (font, base size, emphasis mapping)
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

## Width bands

| Condition | Band |
|-----------|------|
| max line width ≤ target | `WITHIN_TARGET` |
| target < width ≤ ceiling | `ABOVE_TARGET_WITHIN_CEILING` (warning, not overflow) |
| width > ceiling | overflow → wrap / split path |

---

## Wrap policy

1. Break only at **run boundaries**
2. Honor `break_after`: `forbid` > `prefer` > `allow`
3. No indefinite font shrinking
4. No Frozen Script content modification
5. If cannot satisfy `max_lines` within ceiling → `CUE_SPLIT_REQUIRED`

**L1 detects + evidences split. L3 re-segments cues / timing.**

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
| `subtitle.style.keyword_emphasis` | UNKNOWN | Styled-run contract exists; actual styled render route not validated |
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

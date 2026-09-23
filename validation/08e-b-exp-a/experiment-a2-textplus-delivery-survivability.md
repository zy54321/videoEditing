# Stage 08E-B A2 — Text+ Delivery Survivability

| Field | Value |
|-------|-------|
| Stage | **08E-B — Runtime Typography Capability Validation** |
| Sub-stage | **A2 — Text+ Delivery Survivability** |
| Date | 2026-09-23 |
| Starting HEAD | `29f4c9b84ab3d458597993a5ab5970e86b0999c1` |
| Ending HEAD | `29f4c9b84ab3d458597993a5ab5970e86b0999c1` (no commit in this window) |
| Parent | A1.1 `LAYOUT_MATERIALIZATION_PASS`; BR1 historical Deliver failure preserved |

```
A2_OUTCOME = TEXTPLUS_DELIVERY_PASS
EXPERIMENT_08E_B_A2 = PASS
TEXTPLUS_DELIVERY_SURVIVABILITY = PASS
```

Validated route: `timeline.insert_fusion_title` → standalone Text+ → Deliver (MP4/H.264 or PNG/RGB8) **when MarkIn/MarkOut intersect Text+ active clip span**.

---

## Environment

| Item | Value |
|------|-------|
| Resolve | DaVinci Resolve Studio **21.1.0.14** |
| MCP | Samuel **4.8.13** (4.8.15 available, not upgraded) |
| Disposable project | `Astra-08E-B-Subtitle-Validation` |
| Timeline | `A20-TEXTPLUS-DELIVER-SMOKE` |
| Timeline ID | `17d46e6e-6957-45d7-9640-bcd4486cdc54` |
| Resolution / FPS | 1080×1920 @ 24 |
| Timeline start | frame `86400`, TC `01:00:00:00` |
| N02 | **not touched** |
| Experiment B | **not executed** |

---

## A20 Minimal Repro

### Intended

- V1: solid background (≥3 s)
- V2: standalone Text+ `HELLO A20`, Arial Regular, Size `0.064`, ≥3 s
- No transitions, grade, motion, compound clip

### Actual (MCP layout deviation)

| Track | Item | Frames | Duration |
|-------|------|--------|----------|
| V1 | `纯色` (solid color) | 86400–86520 | 5 s |
| V1 | `Text+` | 86520–86640 | 5 s |
| V2 | *(empty)* | — | — |

`add_track` succeeded but `insert_fusion_title` landed on V1 after the solid clip (sequential, not overlapping). **Does not block Deliver** when render range targets the Text+ span.

---

## Route Identity (R1)

| Field | Value |
|-------|-------|
| Route ID | `R1_insert_fusion_title` |
| MCP operation | `timeline.insert_fusion_title` → `"Text+"` |
| Timeline item type | **generator** (standalone Fusion Title) |
| Clip ID | `eb9d144f-01af-4535-8b8a-8d6c4711cefd` |
| Fusion comp count | 1 |
| Tools | `Template` (TextPlus) → `MediaOut1` (MediaOut) |
| Connection | Template output → MediaOut1 input (**verified**) |
| StyledText | `HELLO A20` |
| Font / Style / Size | Arial / Regular / `0.064` |

**Not:** media-clip-attached Fusion comp, offline DRT placeholder, native subtitle burn-in, preview-only object.

Reference: `evidence/a1-route-probe.json` (same R1 class as A1).

---

## Fusion Graph

```
Template (TextPlus)
    └──► MediaOut1 (MediaOut)   [enabled, 1 input connected]
```

`probe_fusion_comp` + `get_text_plus` readback consistent after create and after save/reload.

---

## Track / Timeline Authority

| Check | Result |
|-------|--------|
| Text+ track enabled | ✓ V1 enabled |
| Text+ not muted/disabled | ✓ |
| Deliver job timeline | `A20-TEXTPLUS-DELIVER-SMOKE` (matches current) |
| Timeline resolution | 1080×1920 |
| Frame rate | 24 |

---

## Deliver Settings Audit

Common settings across successful runs:

| Setting | Value |
|---------|-------|
| Resolution | 1080×1920 |
| Frame rate | 24 |
| Render mode | Single clip |
| MarkIn / MarkOut (success path) | **86580** / **86580** (1 frame inside Text+ clip) |
| Target dir | `C:\Users\the_z\AppData\Local\Temp\08e-b-exp-a2` |

### MP4 / H.264 (primary)

| Run | Job output | Size | Measurement |
|-----|------------|------|-------------|
| A20-MCP-run1 | `A20-MCP-run1.mp4` | ~10 KB | `actual_width_px=255` |
| A20-MCP-run2 | `A20-MCP-run2.mp4` | ~10 KB | `actual_width_px=255` |
| A20-MCP-run3-post-reload | `A20-MCP-run3-post-reload.mp4` | ~10 KB | `actual_width_px=255` |

### PNG / RGB8 (control — not sole test)

| Run | Output | Measurement |
|-----|--------|-------------|
| A20-MCP-png-control | `A20-MCP-png-control00086580.png` | `actual_width_px=255` |

PNG Deliver **can** carry Text+ when range is correct (contrasts with BR1 failure at wrong frame).

### Negative control (BR1 reproduction)

| Run | MarkIn | Result |
|-----|--------|--------|
| A20-negative-mark86400 | **86400** (solid-color segment only) | **`NO_VISIBLE_TEXT`** |

At frame 86400 the timeline shows only the solid-color generator; Text+ starts at 86520. Deliver faithfully renders that frame — without text.

---

## Control Matrix

| Route | timeline_frame @ 86580 | Deliver (correct range) | Deliver (wrong range 86400) |
|-------|------------------------|-------------------------|------------------------------|
| **MCP Text+ (R1)** | **VISIBLE** | **TEXTPLUS_PRESENT** (255 px) | **TEXTPLUS_MISSING** |
| **GUI Text+ (R3)** | — | **SKIPPED** (Owner GUI not in scope) | — |

R2 (`timeline.insert_title`) not tested — R1 already satisfies A2 success criteria; no mature alternate route required.

---

## Save / Reload

| Step | Result |
|------|--------|
| `project_manager.save` → `close` → `load` | ✓ |
| StyledText readback after reload | `HELLO A20` ✓ |
| Fusion graph intact | ✓ |
| timeline_frame @ 86580 | VISIBLE ✓ |
| Deliver run3 | `actual_width_px=255` ✓ |

**PERSISTENCE_DEFECT:** not observed.

---

## Root Cause Classification

**A. RESOLVE_DELIVER_CONFIGURATION**

Historical BR1 `NO_VISIBLE_TEXT` on Deliver PNG is explained by **render range / MarkIn targeting frames where Text+ is not active**, not by:

- MCP Text+ creation route failure (B)
- Fusion graph persistence defect (C)
- Resolve API inability to composite Text+ in Deliver (D)
- Environment-only defect (E)

Evidence:

1. Same R1 route + same clip → Deliver **passes** at MarkIn=86580 (MP4 and PNG).
2. Same clip → Deliver **fails** measurement at MarkIn=86400 (negative control).
3. BR1 used MarkIn=86400 on Text+-only timelines where API/jobs could collapse range to timeline start.

**Important:** `timeline_frame.capture` and Deliver are different authorities; both must be validated. Property readback alone is not render truth.

---

## A2 Success Criteria

| # | Criterion | Result |
|---|-----------|--------|
| 1 | Text+ visible on timeline rendered frame | ✓ @ 86580 |
| 2 | Text+ visible in Deliver artifact | ✓ MP4 + PNG |
| 3 | Same route repeatable ≥2 | ✓ run1, run2 |
| 4 | Save/reload后仍成立 | ✓ run3 |
| 5 | Route identity明确 | ✓ R1 documented |
| 6 | `measure_subtitle_width.py` width > 0 | ✓ 255 px |
| 7 | 不依赖人工修复 timeline | ✓ MCP-only |

---

## Stable Resolve-Native Route

**Confirmed:** `timeline.insert_fusion_title` → Text+ → Deliver (MP4/H.264 or PNG/RGB8) **when MarkIn/MarkOut cover active Text+ frames**.

**Operational requirement for production:** Deliver range must include subtitle clip record span (or export full timeline with subtitles on active frames). Do not assume `MarkIn=timeline.start_frame` is safe when Text+ starts later.

---

## Historical BR1 (preserved, not rewritten)

BR1 recorded: `timeline_frame` visible, Deliver PNG `NO_VISIBLE_TEXT` at `MarkIn=86400`. **That historical evidence stands** — it was not erased or rewritten.

**New root-cause truth (A2 addendum):**

```
BR1 failure = WRONG_DELIVER_RANGE / MARKIN_OUTSIDE_TEXTPLUS_ACTIVE_SPAN
```

A2 negative control (`A20-negative-mark86400`) reproduces BR1 on a known-good Text+ clip when Deliver samples the solid-color segment only. This is **not** proof that Text+ / MCP / Fusion cannot Deliver.

Native subtitle burn-in (R3) remains valid **control/fallback evidence**, not the A2 fix.

See: `blocker-resolution.md`, `evidence/common-test-font.json`.

---

## Capability Truth (unchanged)

| ID | Status |
|----|--------|
| `subtitle.layout.pixel_width` | **AVAILABLE_UNVERIFIED** |
| `subtitle.style.keyword_emphasis` | **UNKNOWN** |
| `subtitle.segment.semantic` | **VERIFIED** |

### Recommendation (not applied)

A2 closes **Text+ Deliver survivability** for R1 under correct deliver-range policy. Do **not** auto-upgrade `subtitle.layout.pixel_width` until paired predicted/actual width parity is demonstrated end-to-end in a future stage. Document deliver-range alignment as a separate production gate.

---

## Artifacts

**In Git (minimal audit set):**

```
validation/08e-b-exp-a/
├── experiment-a2-textplus-delivery-survivability.md
├── evidence/a2-outcome.json
└── deliver-a2/
    ├── A20-MCP-run1.measurement.json
    ├── A20-MCP-run2-frame.measurement.json
    ├── A20-MCP-run3-post-reload-frame.measurement.json
    ├── A20-MCP-png-control-frame.measurement.json
    └── A20-negative-mark86400-frame.measurement.json
```

**Excluded from Git (local only):** PNG frame extractions under `deliver-a2/*.png` — measurement JSON + job metadata in this record are sufficient for audit; PNGs remain on disk for re-measurement.

Temp deliver outputs: `C:\Users\the_z\AppData\Local\Temp\08e-b-exp-a2\`

---

## Flags

```
TEXTPLUS_DELIVERY = PASS
N02_TOUCHED = NO
EXPERIMENT_B_EXECUTED = NO
```

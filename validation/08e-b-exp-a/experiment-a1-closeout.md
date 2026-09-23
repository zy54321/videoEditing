# Stage 08E-B Experiment A1 — Text+ Rendered-Frame Geometry Parity Closeout

| Field | Value |
|-------|-------|
| Stage | **08E-B — Runtime Typography Capability Validation** |
| Experiment | **A1 — Text+ Geometry Parity** |
| Starting HEAD | `73d0f53` |
| Ending HEAD | *(uncommitted closeout)* |
| Parent | Experiment A (first run INCONCLUSIVE); BR1 COMPLETE |
| Disposable Project | `Astra-08E-B-Subtitle-Validation` |
| Primary Timeline | `A1-EXP-A` (created this run) |
| N02 touched | **NO** |
| Experiment B | **NOT STARTED** |
| A2 work | **NOT STARTED** (evidence only) |

---

## A1 Outcome

```
A1_OUTCOME = PARTIAL (YaHei A01–A06 PASS; full matrix 0/10 @ Arial Size)
A1_GATE = CLOSED (matrix executed 2026-09-23)
A1_PIPELINE = PASS (capture → measure repeatable)
```

**Summary:** A00 smoke passed. Arial anchor `Size=0.064` → first matrix **0/10** parity. **YaHei `Size=0.073`** → **A01–A06 6/6 PASS**; **A07–A09 overflow mismatch**; **A10 per-line / single-line geometry PASS** (layout line-count semantics differ).

Evidence: `evidence/a00-smoke-result.json`, `evidence/a1-size-calibration.json`, `evidence/a1-parity-matrix.json`, `evidence/a1-parity-analysis.md`.

**Prior session (INCONCLUSIVE):** Black captures + `Style=Semibold` font-not-found before Owner GUI verify.

---

## Authority model (accepted)

Per Owner authorization and Samuel MCP documentation:

| Authority | Role in A1 |
|-----------|------------|
| `timeline_frame(capture, quality=frame)` | **ACTUAL_RENDERED_FRAME** for geometry parity |
| Deliver queue PNG/MOV | **Out of scope** for A1 (A2 survivability) |

---

## Text+ Route Identity — **R1 live standalone Fusion Title**

| Field | Value |
|-------|-------|
| Creation | `timeline.insert_fusion_title` → `"Text+"` |
| Item type | `generator` on video track 1 |
| Fusion comp | `Template` (TextPlus) → `MediaOut1` |
| Route ID | `R1_insert_fusion_title` |
| **Not** | DRT `place_fusion_title`, `AddFusionComp` on media clip, native burn-in |

Full probe: `validation/08e-b-exp-a/evidence/a1-route-probe.json`

---

## A00 Measurement Smoke — **PASSED** (2026-09-23)

| Step | Result |
|------|--------|
| Owner GUI verify `HELLO TEST` on `A1-EXP-A` | ✓ |
| Fix `Style=Semibold` → `Regular` (font-not-found) | ✓ |
| `gallery_stills` run1 + run2 PNG 1080×1920 | ✓ measurable |
| `measure_subtitle_width.py` ×3 | ✓ `actual_width_px=232` (repeatable) |
| `timeline_frame` authority check | ✓ `HELLO TEST` visible |
| L1 parity at smoke gate | N/A (calibration next) |

Artifacts: `renders/a1-staging/A00-smoke-run1_1.1.1.png`, `renders/A00-smoke.png`

---

## A00 Measurement Smoke — **FAILED** (prior session)

### Intended case

- Timeline: `A1-EXP-A`
- Text: `HELLO TEST`
- Font: `Arial`, Size `0.05`
- Canvas: 1080×1920 @ 24fps
- Capture: `timeline_frame quality=frame` + `gallery_stills grab_and_export`

### Results

| Step | Result |
|------|--------|
| Fusion API set/readback (`StyledText`, `Font`, `Size`) | ✓ readback `HELLO TEST` / `Arial` / `0.05` |
| `timeline_frame` visible (early session) | Partial — MCP returned images; vision described default **"Custom Title"** not `HELLO TEST` (**readback vs rendered-frame divergence suspected**) |
| `timeline_frame` after `fusion_comp.render()` | ✗ `RENDER_FORMAT_REFUSED: png + RGB16` |
| `timeline_frame` thereafter | ✗ All captures fail (project render format/codec poisoned) |
| `gallery_stills grab_and_export` | Files written 1080×1920 PNG, but **pixel analysis = uniform black**, `NO_VISIBLE_TEXT` |
| Repeatable saved measurable frame | ✗ **Not achieved** |

### Frame persistence method attempted

1. **Primary:** `gallery_stills(action=grab_and_export, cleanup=false)` → `validation/08e-b-exp-a/renders/a1-staging/*.png`
   - Requires Color page + correct playhead (`timeline_markers.set_current_timecode` on Edit page first)
2. **Secondary:** `timeline_frame` inline MCP image — **no durable file path** from MCP client; session later blocked by render settings

Evidence files (black, unmeasurable):

- `renders/a1-staging/A1-A00-smoke_1.1.1.png`
- `renders/a1-staging/v2-tc0512_1.2.1.png`

---

## Blockers

### B-A1-01 — Render settings poisoned (`timeline_frame` unusable)

After `fusion_comp(action=render)` and repeated `timeline_frame` captures, Resolve project render state stuck on **PNG + RGB16**, which `timeline_frame` refuses:

```
RENDER_FORMAT_REFUSED: png / RGB16
```

MCP server log:

```
frame capture could not restore the render format/codec to png/RGB8: SetCurrentRenderFormatAndCodec returned False
```

`get_format_and_codec` reports `png/RGB8` but capture path still attempts RGB16.

**Remediation (Owner / next session):** Restart Resolve or manually reset Deliver page format to PNG RGB 8-bit before A1 retry. Do **not** call `fusion_comp.render()` during geometry capture sessions.

### B-A1-02 — Gallery still route exports black field on Text+

Even with playhead at `01:00:02:12` on `A1-EXP-A` (inside Text+ clip), `gallery_stills` produced full-resolution PNG with **zero bright pixels**.

Possible causes: Color-page still grab not compositing Fusion generator titles on this host/build, or comp state not reflected in still pipeline.

### B-A1-03 — Fusion readback vs rendered frame (suspected)

When `timeline_frame` still worked, captures reportedly showed default **"Custom Title"** while `fusion_comp` / `get_input(StyledText)` readback returned configured strings (`HELLO TEST`, `你好世界`). If confirmed on recovery, geometry parity cannot trust API readback alone.

---

## Font-size calibration — **DONE** (Arial anchor)

| Field | Value |
|-------|-------|
| Anchor text | `HELLO TEST` |
| Font | Arial Regular |
| L1 predicted | 297.41 px |
| Text+ `Size` | **0.064** |
| Actual | 297 px (Δ 0.41 px) |

Artifact: `evidence/a1-size-calibration.json`

**Note:** Single Size from Arial anchor did **not** achieve YaHei parity on A01–A06 (~10% systematic gap).

### YaHei re-calibration (2026-09-23)

| Field | Value |
|-------|-------|
| Anchor | A01 `你好世界` / Microsoft YaHei UI Regular |
| L1 predicted | 196 px |
| Text+ `Size` | **0.073** |
| Actual @ anchor | 196 px (Δ 0 px) |

Artifact: `evidence/a1-size-calibration-yahei.json`

**A01–A06 rerun @ Size 0.073:** **6/6 PASS** (±8px / ±3%). Artifact: `evidence/a1-parity-matrix-yahei-a01-a06.json`

**A07–A09 rerun @ Size 0.073:** **3/3 measurable**, **0/3 parity** — `OVERFLOW_BEHAVIOR_MISMATCH` (actual 1080 px full bleed vs L1 ceiling 864 px / split-required). Artifact: `evidence/a1-parity-matrix-yahei-a07-a09.json`

**A10 @ Size 0.073:** Two-line `\n` → per-line **2/2 PASS** (345/343 vs L1 340); single-line concat **691 vs 680 PASS**. Layout semantics differ (L1 `line_count=1`). Artifact: `evidence/a1-parity-matrix-yahei-a10.json`

---

## A01–A10 — **EXECUTED**

| Metric | Result |
|--------|--------|
| Measurable | 10/10 |
| Parity pass (±8px / ±3%) | **0/10** |
| Renders | `renders/A01.png` … `renders/A10.png` |
| Measurements | `measurements/A01.measurement.json` … |
| Summary JSON | `evidence/a1-parity-matrix.json` |

See `evidence/a1-parity-analysis.md` for per-case table and interpretation.

---

## A2 evidence (record only)

| Route | Status |
|-------|--------|
| `timeline_frame quality=frame` | Was visible earlier in Stage 08E-B / BR1; **broken this session** after render-state poison |
| Deliver PNG/MOV Text+ | **BLOCKED** (BR1: `NO_VISIBLE_TEXT`) |
| Native subtitle burn-in Deliver | Measurable (BR1 R3); **not Text+ route** |

A2 remains open: **Text+ Delivery Survivability**.

---

## Capability truth (unchanged)

| ID | Status | Note |
|----|--------|------|
| `subtitle.layout.pixel_width` | **AVAILABLE_UNVERIFIED** | No A1 paired evidence |
| `subtitle.style.keyword_emphasis` | **UNKNOWN** | Experiment B not run |
| `subtitle.segment.semantic` | **VERIFIED** | Unchanged |

**Recommendation (not applied):** Even if A1 later shows geometry parity on `timeline_frame`, do **not** upgrade `subtitle.layout.pixel_width` until A2 confirms production Deliver survivability (if capability definition includes final-output guarantee).

---

## Architecture note — Subtitle Runtime backends

Subtitle layout must not bind to a single renderer. Current candidates:

| Backend | Role | Status |
|---------|------|--------|
| **Native Subtitle** (`drt.assemble` + burn-in) | Deliver-measurable on host | BR1 R3 verified |
| **Resolve Text+** (`insert_fusion_title`) | Planned typography route | A1 geometry partial; **A2 Deliver PASS** (R1, correct MarkIn) |
| **External Rich-text** | Research / future | **NOT IMPLEMENTED** |

---

## Artifacts

```
validation/08e-b-exp-a/
├── experiment-a1-closeout.md
├── evidence/a1-route-probe.json
├── cases/A00-smoke.request.json
└── renders/a1-staging/          (gallery exports — black, unmeasurable)
```

---

## Retry after Resolve restart (2026-09-23)

| Step | Result |
|------|--------|
| Load `Astra-08E-B-Subtitle-Validation` | ✓ |
| `render get_format_and_codec` on load | **png / RGB16** (persisted in project DB) |
| `render set_format_and_codec png RGB8` | ✓ success |
| `timeline_frame` on `A1-EXP-A` / `08E-B-EXP-A-v2` Text+ | Returns image but **pixel analysis = uniform black** |
| `gallery_stills grab_and_export` @ Text+ playhead | 1080×1920 PNG, **max_lum = 0** |
| `measure_subtitle_width.py` on BR1 `A00-drt-burnin.png` | ✓ still **969px** (tool OK) |
| A00 smoke | **STILL BLOCKED** |

**Conclusion:** Restart clears process state but **not** project Deliver format (RGB16). RGB8 can be reset via MCP, yet **Text+ rendered-frame capture still produces empty/black frames** on this host — separate from codec poison.

Owner GUI check needed: on `A1-EXP-A` @ `01:00:02:12`, is white `HELLO TEST` visible in the Resolve viewer?

---

## Recommended next entry

1. **Owner GUI verify** Text+ visible on `A1-EXP-A` at playhead (if not, Fusion comp / clip issue).
2. On each A1 session: `render set_format_and_codec png RGB8` (see `a1-resolve-preflight.ps1`).
3. Re-run A00 smoke only:
   - `A1-EXP-A` + `insert_fusion_title`
   - `timeline_markers.set_current_timecode` → `gallery_stills` **or** recovered `timeline_frame`
   - Verify **pixel** content matches `StyledText` (not just API readback).
3. If A00 passes → font-size calibration → A01–A10 matrix.
4. A2 remains separate authorization.

---

## Experiment A1.1 — Layout Materialization (2026-09-23)

**Full report:** `experiment-a1-1-layout-materialization.md`

```
A1.1_OUTCOME = LAYOUT_MATERIALIZATION_PASS
```

| Item | Result |
|------|--------|
| Materializer helper | `source/payload/video-workflow/tools/lib/textplus-layout-materializer.ps1` |
| Font profiles | `source/payload/video-workflow/runtime/textplus-font-profiles.yaml` |
| A11 smoke | **PASS** (2-line L1 → `\n` → 2 rendered lines, parity within tolerance) |
| A07–A09 original | **POLICY_BLOCKED** (`BLOCKED_NO_LEGAL_INTERNAL_BREAK`; classified `PRE_MATERIALIZATION_FAILURE`) |
| A07–A09 splittable | **PASS** (split → per-part L1 → Text+; representative captures) |
| A10 | **PASS** (`line_count=1`, no `\n`, 680→691 px) |
| 08E-A regression | 66/66 contract tests PASS |

**Consolidated A1 (post A1.1):**

- **A** Same-layout geometry: A01–A06, A10, A11
- **B** Materialized wrap/split: A07–A09 splittable
- **C** Invalid historical: A07–A09 pre-A1.1 atomic overflow renders

```
TEXTPLUS_GEOMETRY_PARITY = SUPPORTED_FOR_VALIDATED_PROFILE
```

Original A1 `PARTIAL` history preserved; A07–A09 overflow no longer counted as geometry parity failure.

---

## Flags

```
STAGE_08E_B = IN_PROGRESS
EXPERIMENT_A1 = PARTIAL (historical; superseded classification in A1.1)
EXPERIMENT_A1_1 = LAYOUT_MATERIALIZATION_PASS
EXPERIMENT_A1_A00_SMOKE = PASSED
EXPERIMENT_A1_MATRIX = EXECUTED
EXPERIMENT_A2 = TEXTPLUS_DELIVERY_PASS (see experiment-a2-textplus-delivery-survivability.md)
```

---

## Experiment A2 — Text+ Delivery Survivability (2026-09-23)

**Full report:** `experiment-a2-textplus-delivery-survivability.md`

```
A2_OUTCOME = TEXTPLUS_DELIVERY_PASS
```

| Item | Result |
|------|--------|
| Timeline | `A20-TEXTPLUS-DELIVER-SMOKE` |
| Route | R1 `insert_fusion_title` → Text+ |
| Deliver MP4/H.264 @ MarkIn=86580 | **TEXTPLUS_PRESENT** (255 px) ×3 + post-reload |
| Deliver PNG/RGB8 @ MarkIn=86580 | **TEXTPLUS_PRESENT** (255 px) |
| Negative @ MarkIn=86400 | **NO_VISIBLE_TEXT** (BR1 reproduction) |
| Root cause | **A. RESOLVE_DELIVER_CONFIGURATION** (render range) |
| GUI control (R3) | SKIPPED |
```

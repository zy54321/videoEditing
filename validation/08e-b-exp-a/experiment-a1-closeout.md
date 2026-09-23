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
A1_OUTCOME = INCONCLUSIVE
A1_GATE = BLOCKED (A00 smoke failed)
```

**Reason:** Could not establish a repeatable **saved PNG/JPG evidence file** with measurable subtitle geometry from `timeline_frame` or `gallery_stills`, after route probe and partial runtime work.

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

## A00 Measurement Smoke — **FAILED**

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

## Font-size calibration — **NOT STARTED**

Blocked at A00 smoke. Planned method:

1. Fix L1 `base_font_size_px` (48) + font family
2. Binary-search Text+ `Size` to minimize `|predicted_width_px - actual_width_px|` on calibration string
3. Record mapping table in `evidence/a1-size-calibration.json`
4. Apply single calibrated `Size` across A01–A10

---

## A01–A10 — **NOT RUN**

Gate: A00 smoke must pass first. No paired statistics.

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
| **Resolve Text+** (`insert_fusion_title`) | Planned typography route | A1 blocked; A2 Deliver blocked |
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

## Recommended next entry

1. **Restart Resolve** (or reset Deliver format) to clear RGB16 poison.
2. Re-run A00 smoke only:
   - `A1-EXP-A` + `insert_fusion_title`
   - `timeline_markers.set_current_timecode` → `gallery_stills` **or** recovered `timeline_frame`
   - Verify **pixel** content matches `StyledText` (not just API readback).
3. If A00 passes → font-size calibration → A01–A10 matrix.
4. A2 remains separate authorization.

---

## Flags

```
STAGE_08E_B = IN_PROGRESS
EXPERIMENT_A1 = INCONCLUSIVE
EXPERIMENT_A1_A00_SMOKE = BLOCKED
EXPERIMENT_A2 = OPEN
```

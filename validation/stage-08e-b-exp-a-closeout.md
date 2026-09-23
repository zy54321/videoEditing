# Stage 08E-B Experiment A — Pixel Width Renderer Parity Closeout

| Field | Value |
|-------|-------|
| Stage | **08E-B — Runtime Typography Capability Validation** |
| Experiment | **A — Pixel Width Renderer Parity** |
| Parent | Stage 08E (08E-A ACCEPTED; 08E-B not accepted) |
| Starting HEAD | `313104a` |
| VERSION | `0.1.1-dev` |
| Disposable Project | `Astra-08E-B-Subtitle-Validation` |
| N02 / Production | **NONE** |
| Experiment B | **NOT STARTED** |
| Capability upgrades | **NONE** |

---

## Authorization compliance

| Allowed | Executed |
|---------|----------|
| Resolve baseline + disposable project | Yes |
| MCP 4.8.13 | Yes |
| Test subtitles (Text+) | Yes (partial) |
| Validation renders | Yes (artifacts collected) |
| FFmpeg / Python measurement | Yes (tooling added) |
| L1 preflight | **Blocked** (font) |

| Forbidden | Violations |
|-----------|------------|
| N02 modification | None |
| Experiment B | None |
| live_api_srt_append | None |
| Capability state upgrade | None |
| v0.1.1 release | None |

---

## Experiment conclusion

```
EXPERIMENT_A_CONCLUSION = INCONCLUSIVE
```

### Why not PARITY_SUPPORTED / CALIBRATION_REQUIRED / PARITY_NOT_SUPPORTED

A definitive parity verdict requires **paired** `(L1 predicted_width_px, Resolve rendered measurable actual_width_px)` per case. This run failed before that pairing was possible at scale.

| Blocker | Effect |
|---------|--------|
| **B1 — L1 font unavailable** | `subtitle-layout-preflight.ps1` throws `FONT_NOT_FOUND: Microsoft YaHei` on validation host; SimSun fallback also missing. Cases A01–A10 cannot produce machine-readable predictions here. |
| **B2 — Render measurement route unreliable** | Deliver-page PNG/MOV render of Text+ timeline yields a **uniform gray frame** (RGB 135) with **no text signal** (`NO_VISIBLE_TEXT`). Same timeline shows correct subtitle via `timeline_frame.capture` (visual PASS). Automated width extraction from render artifacts is therefore **not reliable** on the attempted route. |
| **B3 — Fusion size unit mapping unvalidated** | Text+ `Size` is a Fusion normalized scalar (e.g. `0.05`), not L1 `base_font_size_px` (48). No calibration run completed. |

---

## Case matrix status (A01–A10)

| Case | L1 preflight | Resolve render measure | Notes |
|------|--------------|------------------------|-------|
| A01 | **BLOCKED** (font) | **PARTIAL** (visual only) | Text+ `你好世界` visible in frame capture; render artifact unmeasurable |
| A02–A05 | **NOT RUN** | **NOT RUN** | Blocked by B1 |
| A06–A09 (width bands) | **NOT RUN** | **NOT RUN** | Width probe script not completed (depends on B1) |
| A10 (two-line) | **NOT RUN** | **NOT RUN** | Blocked by B1 |

**Decision-boundary cases (WITHIN_TARGET / ABOVE_TARGET_WITHIN_CEILING / OVER_CEILING):** no paired data — **not evaluated**.

---

## Partial evidence (A01 probe)

### Typography setup (Resolve)

- Route: `insert_fusion_title` → `Text+` / Fusion tool `Template`
- `Font = Microsoft YaHei` (readback OK)
- `Size = 0.05` (Fusion units)
- `StyledText = 你好世界`

### Visual verification

- `timeline_frame.capture` @ `08E-B-EXP-A-v2`, TC `01:00:05:12` → **subtitle visible** (white text, black field)

### Render artifact

- `v2-A01-measure.mov` (H.264, 1080×1920, 1 frame)
- Extracted frame: **uniform RGB(135,135,135)** — `measure_subtitle_width.py` → `NO_VISIBLE_TEXT`

### L1 prediction

- **Not produced** on this host (`FONT_NOT_FOUND`)

---

## Capability truth (unchanged)

| ID | Before | After | Notes |
|----|--------|-------|-------|
| `subtitle.layout.pixel_width` | AVAILABLE_UNVERIFIED | **AVAILABLE_UNVERIFIED** | No paired parity evidence |
| `subtitle.style.keyword_emphasis` | UNKNOWN | **UNKNOWN** | Experiment B not run |
| `subtitle.segment.semantic` | VERIFIED | **VERIFIED** | Unchanged |

---

## Evidence-based recommendations (not capability patches)

1. **Font parity gate:** Run Experiment A on a host where L1 `Microsoft YaHei` (or an Owner-approved matched family) is installed for System.Drawing, *and* Resolve Text+ uses the same family.
2. **Measurement route:** Do not use Deliver PNG/MOV alone for Text+ width QA on disposable generator timelines until a render path is proven to match `timeline_frame` output. Candidate next steps: overlay Text+ on imported still (V2), export via `timeline_frame` to file, or validate a burn-in route separately.
3. **Size calibration:** Establish an explicit mapping table `base_font_size_px` ↔ Fusion `Size` before interpreting pixel deltas.
4. **Case generator:** Complete `generate_cases.py` width-band probing once B1 is cleared.

---

## Artifacts

```
validation/08e-b-exp-a/
├── baseline-audit.md
├── cases/A01.request.json
├── measure_subtitle_width.py
├── generate_cases.py
├── run-preflight-batch.ps1
├── renders/A01-frame.jpg          (from Deliver — gray, unmeasurable)
└── measurements/A01.measurement.json
```

Temp render outputs: `C:\Users\the_z\AppData\Local\Temp\08e-b-exp-a\`

---

## Flags

```
STAGE_08E_B = INCONCLUSIVE
STAGE_08E_B_EXP_A = INCONCLUSIVE
STAGE_08E_B_EXP_A_CLOSEOUT = COMPLETE
```

**Not declared:** `STAGE_08E = ACCEPTED`, `subtitle.layout.pixel_width = VERIFIED`

---

## BR1 rerun (blocker resolution)

| Field | Value |
|-------|-------|
| Sub-stage | **BR1 — Runtime Measurement Blocker Resolution** |
| Starting HEAD | `ed04506` |
| Document | `validation/08e-b-exp-a/blocker-resolution.md` |

**first_run = INCONCLUSIVE** (preserved above)

**rerun_result = NOT_EXECUTED (A01–A10)**

| Blocker | BR1 status |
|---------|------------|
| B1 Font Authority | **CLOSED** — GDI+ family alias fix; BR1-01 regression pass |
| B2 Render / Measurement | **CLOSED (R3 burn-in Deliver)**; **Text+ Deliver still BLOCKED** |

A01 L1 preflight now produces `max_line_width_px=196` (alias → `Microsoft YaHei UI`), but Text+ Deliver PNG remains `NO_VISIBLE_TEXT` — no paired parity data.

`EXPERIMENT_A_CONCLUSION` remains **INCONCLUSIVE**.

---

## Experiment A1 (Text+ rendered-frame geometry) — 2026-09-23

| Field | Value |
|-------|-------|
| Starting HEAD | `73d0f53` |
| Document | `validation/08e-b-exp-a/experiment-a1-closeout.md` |
| Outcome | **INCONCLUSIVE** — A00 smoke **BLOCKED** |

Authority shift: `timeline_frame quality=frame` is the A1 actual-width source (not Deliver). A00 could not produce a saved measurable PNG; `timeline_frame` later failed with poisoned PNG/RGB16 render state after `fusion_comp.render()`.

**A01–A10 not run.** A2 (Deliver survivability) remains open.

---

## Next entry (Owner)

1. **Restart Resolve** or reset Deliver format, then retry A1 A00 smoke (`experiment-a1-closeout.md`).
2. Resolve **Text+ Deliver graph** (A2) separately from A1 geometry.
3. Re-run A01–A10 only after A00 smoke + font-size calibration pass.
4. Only after full paired matrix: choose among `PARITY_SUPPORTED`, `CALIBRATION_REQUIRED`, or `PARITY_NOT_SUPPORTED`.

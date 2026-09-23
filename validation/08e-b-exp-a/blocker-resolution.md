# Stage 08E-B Experiment A-BR1 — Blocker Resolution

| Field | Value |
|-------|-------|
| Stage | **08E-B — Runtime Typography Capability Validation** |
| Sub-stage | **BR1 — Runtime Measurement Blocker Resolution** |
| Starting HEAD | `ed04506` |
| Parent experiment | **A — Pixel Width Renderer Parity** (first run = INCONCLUSIVE) |
| Disposable Project | `Astra-08E-B-Subtitle-Validation` |
| Resolve | Studio **21.1.0.14** |
| MCP | Samuel **4.8.13** |
| N02 touched | **NO** |
| Experiment B | **NOT STARTED** |

---

## Executive summary

| Blocker | Status | Outcome |
|---------|--------|---------|
| **B1 — Font Authority** | **CLOSED** | Root cause = GDI+ family-name mismatch, not missing fonts. L1 alias resolver fixed + regression test added. |
| **B2 — Render / Measurement Authority** | **CLOSED (partial)** | Measurable **Deliver** route found: **R3** native subtitle burn-in. **Text+ Deliver route remains BLOCKED.** |
| **A01–A10 resume** | **NO** | Gate for measurable route passed, but Experiment A target route (`insert_fusion_title` / Text+) still cannot produce paired `actual_width_px` from final render. |
| **EXPERIMENT_A_CONCLUSION** | **INCONCLUSIVE** (unchanged) | No paired L1↔Resolve Text+ width matrix. |

```
B1_FONT_AUTHORITY = CLOSED
B2_RENDER_MEASUREMENT_ROUTE = CLOSED   # R3 native subtitle burn-in Deliver
B2_TEXTPLUS_DELIVER_ROUTE = BLOCKED    # Experiment A intended route
BLOCKER_RESOLUTION = COMPLETE
EXPERIMENT_A_CONCLUSION = INCONCLUSIVE
first_run = INCONCLUSIVE
rerun_result = NOT_EXECUTED (A01–A10 not resumed on Text+ route)
```

---

## B1 — Font Authority Audit

### Root cause

**Not** “font missing on Windows.” The validation host has `msyh.ttc`, `simsun.ttc`, `arial.ttf`, etc. under `C:\Windows\Fonts`.

**Actual defect:** **Family name identity mismatch** between contract strings and `System.Drawing.FontFamily` enumeration.

| Contract / Registry display | Windows file | System.Drawing `Families` | Resolve Text+ |
|----------------------------|--------------|---------------------------|---------------|
| `Microsoft YaHei` | `msyh.ttc` | **not enumerated** | accepts string; prior readback `Microsoft YaHei` |
| `Microsoft YaHei UI` | `msyh.ttc` (same family) | **enumerated** | set/readback `Microsoft YaHei UI` ✓ |
| `SimSun` | `simsun.ttc` | **not enumerated** | not fully probed this round |
| `NSimSun` | (subset) | **not enumerated** | — |
| `Arial` | `arial.ttf` | **enumerated** | set/readback `Arial` ✓ |

Registry display names (e.g. `Microsoft YaHei & Microsoft YaHei UI`) are **not** identical to GDI+ family names.

### Classification

- **L1 FONT RESOLUTION DEFECT** — preflight threw `FONT_NOT_FOUND` despite fonts being installed, because resolver required exact enumeration match.
- **Not** a System.Drawing backend limitation for YaHei — `Microsoft YaHei UI` is measurable.

### Fix (authorized in BR1)

File: `source/payload/video-workflow/tools/lib/subtitle-layout-engine.ps1`

- Added `Get-SubtitleFontAliases` + alias-aware `Resolve-SubtitleFont`
- `Microsoft YaHei` → `Microsoft YaHei UI` (when UI enumerated)
- `SimSun` → `NSimSun` / variants (when enumerated)
- Regression: **BR1-01** in `source/tests/subtitle-layout-contract.ps1` (66/66 pass)

### A01 preflight after fix

```
requested_family: Microsoft YaHei
resolved_family:  Microsoft YaHei UI
resolved_from:    alias
max_line_width_px: 196
width_band: WITHIN_TARGET
```

Artifact: `validation/08e-b-exp-a/predictions/A01.prediction.json`

---

## Common test font evidence

Full table: `validation/08e-b-exp-a/evidence/common-test-font.json`

### Primary: Arial (Latin probe on A00-TextOnly)

| Check | Result |
|-------|--------|
| Windows file | `C:\Windows\Fonts\arial.ttf` ✓ |
| System.Drawing enumerate | ✓ |
| L1 instantiate / preflight | ✓ |
| Resolve Text+ set/readback | `Arial` ✓ |
| `timeline_frame.capture` @ `frame=60` | text **visible** (`A00 RENDER TRUTH`) |
| Deliver PNG @ job `MarkIn=86400` | **NO_VISIBLE_TEXT** |

### Chinese: Microsoft YaHei UI (via alias)

| Check | Result |
|-------|--------|
| Windows file | `msyh.ttc` ✓ |
| System.Drawing | `Microsoft YaHei UI` enumerated ✓ |
| L1 alias from `Microsoft YaHei` | ✓ |
| Resolve Text+ set/readback | `Microsoft YaHei UI` ✓ |
| Deliver Text+ | not measurable (same graph issue as Arial) |

**Conclusion:** Common font parity exists for **L1 measurement ↔ Resolve Text+ property authority**. It does **not** imply Deliver renderer parity for Fusion Text+ generators.

---

## B2 — Render Graph / Route Audit

### A00 minimal case

Timeline: `A00-TextOnly` — single `Text+` generator, 120 frames @ timeline start `86400`.

| Field | Value |
|-------|-------|
| Clip type | generator (`insert_fusion_title`) |
| Fusion tool | `Template` |
| StyledText | `A00 RENDER TRUTH` |
| Video tracks | 1 (enabled) |
| Transitions / effects | none |

### `timeline_frame.capture` authority

Per MCP `timeline_frame` documentation:

- `quality=frame` (default): **single-frame precise render** (~1s), processed output including Fusion/titles — **not** clip thumbnail.
- Uses a **temporary render path** inside Resolve; restores most render settings afterward.
- **Not the same authority** as Deliver queue final encoder output.

Observed: `frame=60` → subtitle **visible** (white on black).  
Observed: absolute `frame=86460` → **black** (parameter semantics differ; `frame` behaves as offset/elapsed, not always absolute timeline index).

### Deliver authority

Deliver queue PNG (`prepare_render_job` + `start`):

- Resolves `MarkIn`/`MarkOut`; on this host jobs collapse to timeline item start (`86400`) when range is rewritten.
- Output files ~6562 bytes uniform field → `measure_subtitle_width.py` → **`NO_VISIBLE_TEXT`**
- Re-verified BR1: `A00-textonly-deliver-f60_00086400.png`, `A00-abs-86460_00086460.png` — both unmeasurable.

**Deliver does not composite Fusion Text+ generators into final PNG on the tested route**, while `timeline_frame` preview render does.

### Route matrix

| Route | ID | Timeline visible | Deliver artifact visible | Repeatable | Notes |
|-------|----|------------------|--------------------------|------------|-------|
| Live Fusion Text+ | **R1** | ✓ (`timeline_frame`) | ✗ (`NO_VISIBLE_TEXT`) | yes | Experiment A planned route |
| DRT `type:title` | **R2** | ✗ (empty Fusion comp) | ✗ | — | `tool_count=0` after import |
| DRT `subtitles[]` + `ExportSubtitle: BurnIn` | **R3** | not re-tested this round | ✓ | ✓ | **Measurable Deliver route** |

### R3 — measurable final-render route

| Field | Value |
|-------|-------|
| Timeline | `A00-DRT-Subtitle` |
| Authoring | `drt.assemble` + `ExportSubtitle: BurnIn` |
| Deliver | PNG RGB8 1080×1920, `MarkIn=86460` |
| Artifact | `validation/08e-b-exp-a/renders/A00-drt-burnin.png` |
| Smoke measurement | `actual_width_px=969`, `ratio=0.897222` |
| Repeatability | 2/2 identical (`evidence/b2-smoke-measurement.json`) |

**B2 closed** for “exists a measurable Deliver route.”  
**Experiment A cannot use R3** without changing the renderer under test (native burn-in ≠ Text+ typography).

---

## A01–A10 gate decision

Per BR1 authorization:

```
B1_FONT_AUTHORITY = CLOSED
B2_RENDER_MEASUREMENT_ROUTE = CLOSED (R3)
```

However, Experiment A scope is **L1 pixel width vs Resolve Text+ renderer**. R3 is a different render graph.

| Step | A01 status |
|------|------------|
| L1 preflight | ✓ `predicted max_line_width_px = 196` |
| Resolve Text+ visual | ✓ `timeline_frame` (prior run + A00) |
| Deliver `actual_width_px` | ✗ blocked on Text+ |
| Paired parity | ✗ impossible |

**Decision:** Do **not** resume full A01–A10 matrix — would add predictions without `actual_width_px`, cannot change INCONCLUSIVE conclusion.

---

## Capability truth (unchanged)

| ID | Status |
|----|--------|
| `subtitle.layout.pixel_width` | **AVAILABLE_UNVERIFIED** |
| `subtitle.style.keyword_emphasis` | **UNKNOWN** |
| `subtitle.segment.semantic` | **VERIFIED** |

No capability state upgrades in BR1.

---

## Remaining limitations

1. **Text+ Deliver graph** — Fusion generator titles visible in `timeline_frame` but absent in Deliver PNG/MOV on disposable timelines (Resolve 21.1.0.14).
2. **MarkIn rewrite** — Deliver jobs collapse mark range to timeline/item start; complicates frame-targeted exports.
3. **Fusion Size ↔ `base_font_size_px`** — not calibrated (deferred per BR1 §12).
4. **SimSun / NSimSun** — still not enumerated on host; alias table ready but no common Chinese serif route verified end-to-end.

---

## Artifacts

```
validation/08e-b-exp-a/
├── blocker-resolution.md          (this file)
├── evidence/
│   ├── b1-font-audit.json
│   ├── system-drawing-families.txt
│   ├── common-test-font.json
│   └── b2-smoke-measurement.json
├── predictions/A01.prediction.json
└── renders/A00-drt-burnin.png
```

Code:
- `source/payload/video-workflow/tools/lib/subtitle-layout-engine.ps1` (alias resolver)
- `source/tests/subtitle-layout-contract.ps1` (BR1-01)

---

## Recommended next entry (Owner)

1. **Text+ Deliver investigation** — overlay on video still, compound clip, or Owner-approved alternate Text+ export path that matches Experiment A route identity.
2. **Or** explicitly re-scope Experiment A to a renderer with proven Deliver parity (not done in BR1).
3. Re-run A01–A10 only when **same route** supports L1 prediction + Deliver `actual_width_px` pairing.

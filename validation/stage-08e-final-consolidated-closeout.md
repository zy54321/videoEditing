# Stage 08E — Final Consolidated Closeout

**Date:** 2026-09-23  
**Baseline HEAD:** `7062e67`  
**Outcome:** **PASS_WITH_DEGRADATION** (OUTCOME B)

---

## Static truth fixes (COMPLETE)

| Area | Resolution |
|------|------------|
| SIZE-only emphasis | Production mapping: Regular + tracking 0 for all levels; size multipliers 1.0 / 1.1 / 1.25 |
| Bold / tracking | `CLS_FONT_STYLE_NOT_VERIFIED`, `CLS_TRACKING_NOT_VERIFIED` fail-closed |
| Stroke | Production `stroke_px = 0`; `TEXTPLUS_STROKE_NOT_VERIFIED` if non-zero |
| Timing | `start_frame` + `duration_frames` required; no production default `global_out=119` |
| Materializer | `TimingAuthority=production` blocks equal-split timing; `TIMING_ROUTE_NOT_VERIFIED` on split |
| Plain vs emphasized | Same Text+ base profile; plain = no CLS node; emphasized = StyledTextCLS |
| Placement | Lower safe zone `VerticalJustificationNew=2` in production profile (pending visual final) |

Artifacts: `textplus-production-profile.yaml`, updated `textplus_cls_setting.py`, `subtitle-layout-request.json`.

---

## Overlay route probe (08E-FINAL-SUBTITLE-PROBE)

### Route tested

`textplus_nested_timeline_overlay` (PARTIAL)

1. `08E-FINAL-SUBTITLE-LAYER-PROBE` — V1 Text+ title
2. `08E-FINAL-SUBTITLE-MASTER-PROBE` — V1 Solid Color + V2 nested subtitle timeline (`media_pool.append_to_timeline`, `track_index=2`)

### Visual evidence

`timeline_frame` at master frame 86460: V1 background + V2 nested Text+ composite visible (text partially rendered; default font missing CJK glyphs).

### Not validated in integrated probe

- P1/P2/P3 cue timing gates (before/inside/after)
- Lower-safe-zone placement visual confirmation
- CLS emphasis on overlay route
- L1 width vs rendered width parity
- Deliver + save/reload integrated probe

### A2 scope clarification (preserved)

A2 **PASS** = standalone Text+ Deliver survivability.  
A2 **did NOT** validate real V1+V2 overlay composition.  
08E-FINAL adds partial nested-overlay structure evidence only.

---

## Capability final truth

| Capability | Before | After |
|------------|--------|-------|
| `subtitle.style.keyword_emphasis` | VERIFIED | **AVAILABLE_UNVERIFIED** |
| `subtitle.layout.pixel_width` | AVAILABLE_UNVERIFIED | **AVAILABLE_UNVERIFIED** (unchanged) |
| `subtitle.segment.semantic` | VERIFIED | **VERIFIED** |
| `subtitle.render.basic` | VERIFIED | **VERIFIED** |

Isolated route evidence retained: `textplus_styledtextcls_import_comp` = VERIFIED (isolated).

---

## Production fallback (first Production)

```
native_drt_subtitles + semantic segmentation
+ no keyword emphasis
+ no guaranteed pixel-width parity
```

`REMAINING_PRODUCTION_BLOCKERS = []` for Stage 08E Owner acceptance path with degradation.

---

## Stage readiness

| Gate | Status |
|------|--------|
| `STAGE_08E_B_FINAL_REVIEW` | **PASS_WITH_DEGRADATION** |
| `STAGE_08E_B` | **ELIGIBLE** |
| `STAGE_08E` | **READY_FOR_OWNER_ACCEPTANCE** |

Not declared: `STAGE_08E_B = ACCEPTED`, `STAGE_08E = ACCEPTED`.

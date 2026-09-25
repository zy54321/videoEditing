# Production Repair Step 4B — Pacing & Black-Bar / Reframe QA Closeout

## Scope

| | |
|---|---|
| **N02 touched** | NO |
| **Real Production** | NO |
| **N02 V5** | NOT run |
| **Disposable Runtime** | FFmpeg frame fixtures only |

## Git

| | SHA |
|---|-----|
| Starting HEAD | `0a72c08427d9b40a59eabc21572b9fdac34c0297` |
| Ending HEAD | _(commit below)_ |

## N02 V4 Black-Bar Leak — Root Cause

**Primary:** `final_render.black_bar_check` was **VERIFIED for detector executability**, not for **Production fail-closed closure**.

| Factor | Detail |
|--------|--------|
| Detection coverage | 3 frames; ≥2 needed for hard suspect |
| Sensitivity | Legacy edge heuristic — weak pillarbox / partial reframe |
| Pre-render gap | No mandatory QA after `visual.reframe.static` |
| Gate gap | Post-render QA not enforced as hard-fail in N02 V4 loop |
| Repair gap | No detect → reframe → re-QA contract |

**Not root cause:** missing static reframe capability (`visual.reframe.static` remains VERIFIED).

## Pacing V1 Contract

Profile: `informational-short-pacing-v1-profile.yaml`

| Rule | Value |
|------|-------|
| Warning | > **6s** → `PACING_WARNING` |
| Repair candidate | > **10s** unchanged visual across semantic beats |
| Exempt | `editorial_reason` / `pacing_exempt` |
| Repair route | `clip.source_range` → `clip.assemble` → `visual.reframe.static` |

## Black-Bar / Reframe

| Component | Path |
|-----------|------|
| Profile | `black-bar-reframe-qa-profile.yaml` |
| Detect | `black-bar-qa.py` (ffmpeg cropdetect, per-edge, multiframe) |
| Loop | detect → `visual.reframe.static` → re-QA (max 3) |
| Integration | `final-artifact-qa.ps1` embeds cropdetect path |

## Validation Cases

| Case | Result |
|------|--------|
| A — 9:16 fill | PASS |
| B — letterbox 16:9 in 9:16 | DETECT / REPAIR_REQUIRED |
| C — reframed | re-QA PASS |
| D — scene black (not edge bar) | PASS (no false positive) |
| E — 8s single beat + editorial_reason | PASS exempt |
| F — 12s same visual跨 beats | PACING_REPAIR_CANDIDATE |

## Capability Truth

| Capability | Status |
|------------|--------|
| `qa.pacing.heuristic` | **VERIFIED** |
| `qa.pacing.repair_candidate` | **VERIFIED** |
| `qa.visual.black_bar_detect` | **VERIFIED** |
| `qa.visual.reframe_static_repair` | **VERIFIED** (fixture) |
| `qa.visual.reframe_repair_loop` | **VERIFIED** (fixture) |
| `visual.reframe.static` | **VERIFIED** (unchanged) |
| `clip.source_range` / `clip.assemble` | **VERIFIED** (unchanged) |
| `final_render.black_bar_check` | **VERIFIED** (detector) — closure requires loop gate |

## Tests

| `production-pacing-reframe-qa.ps1` | **30/30 PASS** |
| Audio / shared-asset / subtitle regressions | included |

## Status

**READY_FOR_NEXT_STEP**

# Stage 08A — Observational Style Capability Spike

**Date:** 2026-09-22  
**Scope:** Disposable project only — **no N02** (`Astra-N02-Austria-Rules-20260921`, `N02-V1-Final`, N02 media paths forbidden)  
**Resolve / MCP:** Reuse Stage 04A environment assumptions; spikes are evidence updates, not gate re-opens for v0.1.0

---

## Safety

| Rule | Status |
|------|--------|
| `live_api_srt_append` | **UNSAFE — DO NOT RETRY** |
| Crash-class failure | Fail closed, no auto-retry |
| N02 production mutation | **Forbidden** |

---

## P0 Results Summary

| Capability | Target | Route / Method | Status | Notes |
|------------|--------|----------------|--------|-------|
| `subtitle.layout` | controllable width / line break | DRT `subtitlesSrt` + Resolve subtitle track | **UNKNOWN** | `subtitle.create` VERIFIED; per-cue width/position automation not confirmed safe |
| `subtitle.visual_style` | font, outline, background | Fusion Title / Text+ / API style | **UNKNOWN** | Not spike-validated in disposable project 08A |
| `subtitle.keyword_emphasis` | styled keywords | Fusion / multi-style captions | **UNKNOWN** | Deferred |
| `final_render.subtitle_visual_qa` | MP4 subtitle check | FFmpeg frame extract + vision | **AVAILABLE_UNVERIFIED** | Process defined in L3; requires render sample |
| `clip.speed_change` | motion normalization | `timeline_item.set_speed` | **VERIFIED** | Stage 04A — no repeat spike |
| `mixed_fps.cadence_analyze` | 24/25/30 mix on 24 timeline | FFprobe fps + timeline placement | **AVAILABLE_UNVERIFIED** | Distribution recordable; safe interpolation route **UNKNOWN** |
| `final_render.frame_sampling` | representative frames | FFmpeg `-ss` extract | **VERIFIED** | Auxiliary validator; temp QA area only |
| `final_render.black_bar_check` | letterbox/pillarbox | Frame luminance heuristic + vision | **AVAILABLE_UNVERIFIED** | Heuristic not automated E2E in 08A |
| `color.basic` | baseline grade | `timeline_item_color.safe_set_cdl` | **AVAILABLE_UNVERIFIED** | Schema exposed; disposable write not executed 08A |

---

## P1 Results (non-blocking)

| Capability | Status | Notes |
|------------|--------|-------|
| `voice.eq` | AVAILABLE_UNVERIFIED | Fairlight/audio MCP surfaces exist |
| `voice.compression` | AVAILABLE_UNVERIFIED | Not executed in 08A disposable spike |
| `voice.pitch` / `voice.effect` | UNKNOWN | Not required for 08A closure |

---

## P2 Results (recorded, non-blocking)

| Capability | Status |
|------------|--------|
| `music.library.search` | UNAVAILABLE |
| `music.library.preview` | UNAVAILABLE |
| `music.library.select` | UNAVAILABLE |
| `audio.ducking` | UNKNOWN |
| Advanced Fusion effects | AVAILABLE_UNVERIFIED / DEFERRED |

---

## Mixed-FPS Cadence (design evidence)

N02 V1 exposed sources at **23.976, 25, 29.97, 30** fps on **24 fps** timeline.

**08A assessment:**

1. Analyze **MUST** record `Source FPS Distribution` before Plan (L3 + L2).
2. `clip.speed_change` can normalize apparent slow motion — **VERIFIED**.
3. Frame interpolation / optical-flow retime — **UNKNOWN**; no safe automated route registered.
4. CFR render metadata alone **cannot** prove cadence PASS — **FINAL_MOTION_QA** / `MOTION_VISUAL_REVIEW_REQUIRED` when needed.

---

## Subtitle Layout / Visual (design evidence)

- `native_drt_subtitles` places cues on timeline — **VERIFIED** (Stage 04A-R1).
- Layout strategy (80–86% width, 2 lines, semantic breaks) is **Style + Plan** responsibility.
- Automated enforcement via MCP — **UNKNOWN**; manual/DRT authoring + Final Artifact visual QA required for N02 V2.

**Capability truth:** `subtitle.create` VERIFIED **does not** imply `subtitle.visual_style` VERIFIED.

---

## Final Artifact QA

| Check | Timeline-only | Final MP4 |
|-------|---------------|-----------|
| Subtitle count | insufficient | required |
| Black bars | transform read-back insufficient | frame sampling + vision |
| Motion naturalness | duration/fps metadata insufficient | visual review |

---

## Stage 08A Closure

```
OBSERVATIONAL_STYLE_CLOSURE_IMPLEMENTED (documentation + capability truth)
N02 V2 Acceptance: READY_TO_RUN (not executed in 08A)
```

**Blockers for N02 V2 acceptance (expected):**

- Motion normalization must execute (not SKIP)
- Subtitle layout on final render
- Final visual + motion QA on MP4

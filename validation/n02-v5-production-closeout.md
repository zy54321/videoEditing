# N02 V5 Production Closeout

| Field | Value |
|-------|-------|
| Starting HEAD | `f4417e13522f1507a22fc47fb0a32a4dfa2c7d7c` |
| VERSION | `0.1.3-dev` |
| Timeline | `N02-V5-Captioned-Final` (duplicate of V4) |
| Final artifact | `E:\03_Media\02_Video\Davinci\Astra\2026-09-21\output\N02_V5.mp4` |
| SHA256 (post loudnorm promote) | `ef3411b2cca7c37d6616c32363d2eb91297821e08eb971e85e9467546ecbc985` |

## Root cause — landscape / portrait

V4 对横屏素材使用 **Fit + 轻微 Zoom（~1.01）**，在 9:16 画布上产生 **大面积上下黑区**（非薄边 letterbox）。根因是 **fill mode 错误**，不是 cropdetect 薄边误报 alone。

## Portrait reframe (static)

- Route: `visual.reframe.static` — **center cover** via Resolve `ZoomX/Y`（横屏 ~3.16，open sign ~1.067，V1-11 ~3.37）。
- Evidence: `validation/n02-v5-portrait-reframe.json`
- Runtime readback: opening clip Zoom **3.1605** verified.

## Candidate portrait-safety

Plan 层为每镜补充 `source_aspect_ratio`, `portrait_fill_required`, `portrait_crop_feasible`, `reframe_status`（见 portrait-reframe JSON）。V1-11 cover zoom > 3.5 heuristic 仍执行 STATIC_FILL（授权填满画布；未换源）。

## QA gates (FINAL ARTIFACT)

| Gate | Result |
|------|--------|
| ASSEMBLY_PLAN_CONVERGED | YES (V4 plan reused) |
| PLAN_RUNTIME_FRAME_PARITY | PASS (1821 / 1821 / Δ0) |
| RESOLVE_MATERIALIZATION | PASS (V5 duplicate + in-place transform + music swap) |
| PORTRAIT_FILL_QA | **PASS** |
| LAYOUT_STATE_QA | **PASS** |
| BLACK_BAR_QA | **PASS** |
| MUSIC_PRESENT | **PASS** |
| MUSIC_MIX_BALANCE | **PASS** |
| FINAL_AUDIO_QA | **PASS** (−16.1 LUFS, −1.3 dBTP, 48 kHz stereo) |
| SUBTITLE_FONT_WEIGHT | **PARTIAL** |
| SUBTITLE_GEOMETRY_QA | **PASS** (Bold preflight max width 788px, safe margins 72px) |
| SUBTITLE_READABILITY_QA | **PASS** (layout + burn-in present) |
| FINAL_ARTIFACT_QA | **PASS** (visual/audio samples) |

## Music

- Legacy attenuation: **0.15** on Glass Horizon.
- V5 strategy: `recommended_base_factor` **0.08** + **section static gain envelope** (`music_glass_horizon_v5_envelope.wav`) — no ducking.
- Balance measured on **pre-loudnorm** render mix: `MUSIC_MIX_BALANCE=PASS`, relative gap max ~−8.1 dB (voice-primary, music audible).

## Subtitle

- Requested: **Open Sans Bold**; host preflight **fallback → Microsoft YaHei UI Bold** (Open Sans not resolved on layout host).
- **Timeline / burn-in not re-styled** this round (Project.db path unavailable on MCP host); artifact inherits V4 DRT stroke + prior weight.
- `VISUAL_CONFIRM_REQUIRED`: 12s, 35s — confirm stroke + weight on encoded frames.

## Continuous execution

`CONTINUOUS_EXECUTION_PRODUCTION_EVIDENCE`: **PASS_THREE_TIMES** (intake → V5 materialize → render → loudnorm → QA without Owner `继续`).

## READY_FOR_OWNER_REVIEW

**NO** — blocker: **SUBTITLE_FONT_WEIGHT** not closed on **final artifact** (needs Open Sans Bold or verified Semibold on burn-in + optional re-render).

## Evidence files

- `validation/n02-v5-portrait-reframe.json`
- `validation/n02-v5-music-mix-analysis.json`
- `validation/n02-v5-subtitle-final-qa.json`
- `validation/n02-v5-final-artifact-qa.json`
- `validation/n02-v5-production-closeout.md`

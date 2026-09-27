# N02 V4 Production Closeout (Repair R1)

**Starting HEAD:** `536d50f`  
**Ending HEAD:** _(见本次 commit)_  
**VERSION:** `0.1.3-dev`  
**Final artifact:** `E:\03_Media\02_Video\Davinci\Astra\2026-09-21\output\N02_V4.mp4`  
**SHA-256 (post loudnorm promote, reframe rerender):** `07E1E4B13AB41D1B48A79410333B7ABE1569A8E1BB9DCC665327D7204F3C6CC4`

---

## Frame delta root cause (V3 → V4)

| Factor | V3 行为 | 修复 |
|--------|---------|------|
| 时长公式 | 计划按 `timeline_duration_sec` 取整，未对齐 Resolve | `floor(source_span × timeline_fps / source_fps)` |
| `source_out` | `floor(out_sec × fps)` 未反算目标镜长 | `source_span_for_timeline_duration()` 反求 span |
| `record_frame` | 非连续 + 单镜时长偏差 → 间隙/漂移 **+25** | `build_contiguous_clip_infos()` 从 0 连续累加 |
| `source_fps` | 计划默认 25（如欧元 29.97） | `SOURCE_FPS_BY_ASSET` 实测覆盖 |
| Voice 对齐 | 视频 1839 vs 旁白 1821 | 末镜 **+7f** tail pad → **1821** |

模块：`source/payload/video-workflow/tools/lib/resolve_materialization_frames.py`

---

## Plan → Runtime parity (V4 delivery)

| Metric | Value |
|--------|--------|
| Planned sum `timeline_duration_frames` | **1821** |
| Materialized sum (19 shots) | **1821** |
| Per-shot delta | **0** (all shots) |
| Timeline `end − start` | **1821** |
| `PLAN_RUNTIME_FRAME_PARITY` | **PASS** |
| `RESOLVE_MATERIALIZATION` | **PASS** |

证据：`validation/n02-v4-frame-parity-trace.json`，Resolve `N02-V4-Captioned-Final` readback（`N02-V4-Assembly-Parity v03` 一致）。

V3 对照：plan **1814** / runtime **1839** / **+25**。

---

## Candidate safety

| 项 | 结果 |
|----|------|
| `CANDIDATE_SAFETY` | **PASS** |
| Open sign | OPEN 段 ~14s；CLOSE 2.5–5s 已排除 |
| Business hall | **REJECTED** — `RUTA DE EVACUACIÓN` @ 5.5s |
| V1-10 替换 | 超市 `bb019a05` 5.42–9.35s 源段（非西班牙标识） |
| Coffee / clinic | 帧证据：`validation/n02-v4-candidate-frames/` |

`validation/n02-v4-candidate-safety-audit.json`

---

## Black-bar repair

- 路线：`visual.reframe.static`（V1-00）
- 应用：`ZoomX/Y 1.0127`，`Pan −0.0063`，`Tilt −0.0063`
- 时间线：`N02-V4-Captioned-Final` → 二次渲染 `N02_V4_render2` → loudnorm 提升为 `N02_V4.mp4`

### Expanded black-bar QA（成片）

| 采样 (s) | cropdetect (1s+ending) | edge heuristic |
|----------|--------------------------|----------------|
| 1 | suspect letterbox ~12px | suspect |
| 15, 30, 60 | — | high edge ratio（忙场景，非确认黑边） |
| 45, 73 | pass | pass |

`black-bar-qa` 开场 1s：**SUSPECT_BLACK_BARS**（薄 letterbox 仍检出）  
`final-artifact-qa` multiframe（1s + 73s）：**SUSPECT_BLACK_BARS**（1/2 帧）  
**`BLACK_BAR_QA`：未达 PASS**（Owner 门控要求无确认黑边）

---

## Subtitle QA (V4 materialization)

| 检查 | 结果 |
|------|------|
| BurnIn | Render 含字幕 data stream + `SubtitleFormat: BurnIn` |
| Cue 完整 | Timeline transcript **35** cues（与 V2 链一致） |
| Stroke | 继承 V2 `N02-V2-Captioned-wrap` 字幕轨（未改 Text+ 实现） |
| 可读性抽帧 | `final-artifact-qa` 已抽 6 时点；视觉 stroke/边距需 Owner 目视或下轮 Agent 帧审 |
| **`SUBTITLE_QA`** | **PARTIAL** — 结构/烧录 PASS；全量浅/忙背景可读性未在本轮逐条 vision 签字 |

---

## Audio / music

| 项 | 值 |
|----|-----|
| Music | `music_glass_horizon_attenuated.wav`（V2 duplicate） |
| Pre-repair render | −24.5 LUFS |
| Post `final-audio-loudness-repair.py` | **−16.1 LUFS**, **−1.4 dBTP**, **48 kHz stereo** |
| **`FINAL_AUDIO_QA`** | **PASS** |

---

## Runtime

| Item | Value |
|------|--------|
| Project | `N02-20260927` |
| Assembly | `N02-V4-Assembly-Parity v03` |
| Delivery | `N02-V4-Captioned-Final` |
| Render jobs | `248b7032…`（初渲），`ff96623f…`（reframe 重渲） |

---

## Continuous execution

`CONTINUOUS_EXECUTION_PRODUCTION_EVIDENCE` = **PASS_TWICE**（V3 链一次 + 本 Repair R1 一次，全程未要求 Owner「继续」）

---

## Final gates

| Gate | Status |
|------|--------|
| `ASSEMBLY_PLAN_CONVERGED` | **YES** |
| `PLAN_RUNTIME_FRAME_PARITY` | **PASS** |
| `CANDIDATE_SAFETY` | **PASS** |
| `RESOLVE_MATERIALIZATION` | **PASS** |
| `BLACK_BAR_QA` | **FAIL** (opening thin letterbox suspect) |
| `SUBTITLE_QA` | **PARTIAL** |
| `FINAL_AUDIO_QA` | **PASS** |
| `FINAL_ARTIFACT_QA` | **PARTIAL** (audio pass; black-bar suspect) |

## **`READY_FOR_OWNER_REVIEW`：NO**

**Remaining blocker:** 开场 1s 薄 letterbox 在 `black-bar-qa` 下仍为 **SUSPECT**；需略增 static zoom 或 Owner 接受 detector 阈值/目视豁免。

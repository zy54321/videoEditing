# N02 Validation Case

## 概述

**N02** 是 `observational-info-short` 剪辑策略的**第一条真实验证样本**。

| 属性 | 值 |
|------|-----|
| Editing Skill | `observational-info-short` |
| Canonical name | 生活观察 / 轻知识短视频 |
| 类型 | 观察式信息短视频 |
| V1 状态 | **VALIDATION EVIDENCE + PARTIAL STYLE ACCEPTANCE** |
| V2 状态 | **READY_TO_RUN** (Stage 08B) |

## 资产边界

已存在真实生产资产与 Resolve Project，但：

- **媒体文件不复制**进本项目
- **Resolve 工程不复制**进本项目

Validation 目录**只记录**输入条件、Skill 行为、问题、修复与 Acceptance 结果。

---

## N02 V1 — First Real Production (2026-09-21)

### Summary

| Dimension | Result |
|-----------|--------|
| Workflow | **PASS** |
| Editing Quality | **IMPROVED** |
| Final Acceptance | **NOT ACCEPTED** |

V1 不是失败——它是真实环境下的**验证证据**与**部分风格验收**。

### 正向结果

- Source switching 明显更自然
- Narrative flow 改善
- Transitions 改善
- Zero timeline gaps
- Frozen voice preserved
- Valid vertical render produced (1080×1920)

### 未接受原因（V0.1.1 输入）

| # | Issue | Category |
|---|-------|----------|
| 1 | Motion normalization **skipped** | Motion |
| 2 | User: walking appears too slow | Motion |
| 3 | User: some motion appears jerky | Cadence |
| 4 | Subtitle layout overflow | Subtitle |
| 5 | Final subtitle visibility needs stronger artifact QA | Final QA |
| 6 | Framing / black bar artifact risk on final MP4 | Framing |
| 7 | Color only partial | Color |
| 8 | Music disabled by Owner — **not a defect** | Music (`OWNER_DISABLED`) |

### Mixed FPS (V1 evidence)

Source distribution included **23.976, 25, 29.97, 30** fps → timeline **24 fps**. Cadence risk documented for V2.

---

## L1 Capability Gate (unchanged baseline)

**N02_V1_CAPABILITY_GATE (v0.1.0):** `PASS` — Stage 04A baseline only.

**N02_V2_READINESS_GATE (v0.1.1):** `PASS` — see `validation/capability-spike/STAGE-08A1-n02-v2-execution-readiness.md`. Ready for Stage 08B real V2 acceptance.

Stage 08A adds **capability truth** for layout, visual subtitle, final artifact QA, mixed-fps analyze — see `validation/capability-spike/STAGE-08A-observational-style.md`.

**Non-blocking:** `live_api_srt_append` UNSAFE; use `native_drt_subtitles`; `subtitle.timing` → PRODUCTION_QA.

---

## N02 V2 Acceptance Targets (Stage 08B)

| Check | Required |
|-------|----------|
| Narrative | PASS |
| Shot Selection | PASS |
| Pacing | PASS |
| Motion Normalization | PASS |
| Framing | PASS |
| Subtitle Functional | PASS |
| Subtitle Layout | PASS |
| Voice | PASS |
| Color / Look | PASS |
| Final Visual QA | PASS |
| Final Motion QA | PASS |
| Render | PASS |
| Music | OWNER_DISABLED if Owner chose B |

---

## Requirements → L2 Coverage (V0.1.1)

| N02 问题 | L2 / QA |
|----------|---------|
| Stock slow motion | Motion Strategy MUST + OBS-QA-MOTION |
| Jerky cadence | Mixed FPS + OBS-QA-CADENCE |
| Subtitle overflow | Subtitle Layout + OBS-QA-SUBTITLE-LAYOUT |
| Final subtitle QA | Final Artifact QA + OBS-QA-FINAL-RENDER |
| Black bars | Framing + final_render.black_bar_check |
| Color partial | Color / Look Strategy |
| Music off | Music Strategy — OWNER_DISABLED |

---

## 记录规范

后续每次验证迭代，在本目录追加：输入摘要、观察、修复、Acceptance 判定。

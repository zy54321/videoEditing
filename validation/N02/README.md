# N02 Validation Case

## 概述

**N02** 是 `observational-info-short` 剪辑策略的**第一条真实验证样本**。

| 属性 | 值 |
|------|-----|
| Editing Skill | `observational-info-short` |
| 类型 | 观察式信息短视频 |
| 状态 | 进行中 — Bootstrap 阶段记录基线 |

## 资产边界

已存在真实生产资产与 Resolve Project，但：

- **媒体文件不复制**进本项目
- **Resolve 工程不复制**进本项目

Validation 目录**只记录**：

- 输入条件
- Skill 行为
- 发现的问题
- 修复结果
- Acceptance 结果

## 当前已验证

| 步骤 | 状态 |
|------|------|
| Voice Master | ✅ |
| 素材搜集 | ✅ |
| Resolve Project Bootstrap | ✅ |
| Semantic rough cut | ✅ |
| Render | ✅ |

## 当前暴露的问题

以下问题将成为 `observational-info-short` Skill V0 的**真实需求来源**：

| 问题 | 描述 |
|------|------|
| Stock slow motion | Stock footage 存在明显慢动作，需 Motion Normalization |
| Timeline gap / black frame | 时间线空隙与黑帧 |
| 9:16 framing | 竖屏画幅统一策略缺失 |
| Transition | 仅 Hard Cut，转换生硬 |
| Subtitle | 字幕未纳入标准流程 |
| Music | 背景音乐集成未标准化 |
| Repetition / pacing | 重复镜头与节奏问题 |

## Acceptance 目标

在 V0.1 Release 初始化后，针对 N02：

> 仅提供 Production Brief + 调用 `video-production` Skill，  
> 系统自动完成完整生产流程，  
> **不再需要 Owner 手写数百行逐镜头执行 Prompt。**

## L1 Capability Gate

| N02 Requirement | Required Capability | Status | Evidence / Note |
|-----------------|---------------------|--------|-----------------|
| Motion normalization | `clip.speed` | **VERIFIED** | Stage 04A spike: 150% read-back; duration 144→96 |
| 9:16 framing | `clip.scale` + `clip.position` | **VERIFIED** (API) | Transform read-back verified; visual QA still recommended |
| Transitions | `transition.apply` | **VERIFIED** | R2: `native_drt_transition` — DRT assemble → import → render |
| Subtitles | `subtitle.create` via DRT | **VERIFIED** | R1: `native_drt_subtitles`; SRT live-append **UNSAFE** (crash) |
| Background music | `audio.import` + `audio.place` + `background_music_level_control` + `audio.fade` | **VERIFIED** | Level via `ffmpeg_pre_attenuation` (R2); native volume **FAILED** |
| Voice preservation | `audio.place` + timeline control | VERIFIED | Voice Master in N02 rough cut |
| Render | `render.configure` + `render.start` | **VERIFIED** | R2 ffprobe: H.264 **1080×1920** 24fps AAC |
| Post-render verification | `render.verify` + FFprobe | VERIFIED | `verify_output` + external probe |

**N02_CAPABILITY_GATE:** `PASS`

**Post Stage 04A-R2:** All N02 MUST logical capabilities have a VERIFIED safe route. Native live transition and DaVinci-native volume remain FAILED but are not gate blockers.

**Non-blocking:** ducking UNKNOWN; visual 9:16 subject QA; `subtitle.timing` full automation → **PRODUCTION_QA** (not Capability Gate); `live_api_srt_append` UNSAFE (use DRT subtitles).

See `validation/capability-spike/`.

## Requirements → L2 Coverage

N02 已暴露问题与 `observational-info-short` Skill 的映射关系（验证记录 only；N02 专属规则不得反向写入通用 Skill）：

| N02 问题 | L2 覆盖 |
|----------|---------|
| Stock slow motion | Motion Strategy / OBS-QA-01 |
| Timeline gap / black frame | Transition Integrity + Universal QA |
| 9:16 framing | Framing Strategy / OBS-QA-08 |
| Hard-cut stiffness | Transition Strategy |
| Missing subtitles | Subtitle Strategy / OBS-QA-09 |
| Missing background music | Music Strategy + Audio Mix Strategy / OBS-QA-12 |
| Repetition / pacing | Repetition Strategy + Narrative Rhythm / OBS-QA-02, OBS-QA-05 |

## 记录规范

后续每次验证迭代，在本目录追加：

- 输入条件摘要
- Skill 行为观察
- 问题与修复记录
- Acceptance 判定

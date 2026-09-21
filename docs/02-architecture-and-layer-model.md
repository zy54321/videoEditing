# 架构与层级模型

本文档冻结 Video Editing Workflow 的五层模型与横切规则。

---

## L4 — Production Brief

> **「我要做什么视频？」**

**Owner / 用户决定。**

包括：

- 内容
- 目标
- 平台
- 时长
- 画幅
- 已有素材
- Voice
- Editing Skill 类型
- 特殊要求

Brief 是每次生产的输入契约，不包含剪辑策略本身。

---

## L3 — Production Workflow

> **「整条视频生产按照什么通用过程完成？」**

这是**通用流水线**，不是为每种视频类型各复制一套完整流程。

### 基础流程

```
Preflight
  → Analyze
  → Plan
  → Edit
  → Finish
  → QA
  → Repair
  → Render
  → Closeout
```

不同任务可以：

- 跳过某些步骤
- 开启某些步骤
- 改变部分顺序

但**不为** News / Documentary / Vlog 各复制一套完整 Workflow。

---

## L2 — Editing Strategy Skill

> **「这种类型的视频应该怎么剪？」**

这是项目**长期核心价值层**。

### 原则

**一个主要剪辑范式 / Genre 对应一个 Editing Skill。**

### 未来候选

| Skill ID | 说明 |
|----------|------|
| `observational-info-short` | 观察式信息短视频（V0.1 首个实现） |
| `news-explainer` | 新闻解读 |
| `documentary-short` | 纪录短片 |
| `lifestyle-vlog` | 生活方式 Vlog |
| `opinion-talking-head` | 观点口播 |
| `tech-explainer` | 科技讲解 |

### Skill 决定

- shot grammar
- pacing
- average shot duration
- motion strategy
- transition strategy
- subtitle strategy
- title / lower-third strategy
- music strategy
- audio mix strategy
- color tendency
- visual effects
- QA rules

---

## L1 — Capability / Operator Knowledge

> **「L2 决定的剪辑动作如何使用当前工具实现？」**

### 示例

| 层级 | 职责 |
|------|------|
| L2 决定 | short dissolve，6 frames |
| L1 负责 | 当前 DaVinci MCP / Resolve 中应调用什么能力、需要什么参数、调用约束、如何验证结果 |

### V0.1 策略

V0.1 **不建设**复杂 L1 Skill 系统。

先使用：

- 当前 MCP 自带知识
- 一个轻量 **capability reference**（`source/payload/video-workflow/capabilities/`）

---

## L0 — Runtime / Tools

> **「真正执行操作。」**

### 当前栈

```
Cursor
  → samuelgursky/davinci-resolve-mcp
  → DaVinci Resolve
```

### 旁路能力

- FFmpeg
- Resolve transcription
- Kokoro
- 后续本地模型

**L0 不进入本项目 Release 管理。** 本项目只消费 Runtime。

---

## Cross-cutting Rules

Rules 横跨全部层级，用于规定长期不变的执行边界：

| 规则 | 说明 |
|------|------|
| Frozen asset 不得偷偷修改 | 已冻结资产不可静默变更 |
| Original media immutable | 原始素材不可改写 |
| Inspect before destructive/write action | 破坏性 / 写入操作前必须先检查 |
| Write 后必须 verify | 每次写入后验证结果 |
| 普通 repair 自动完成 | 常规修复由系统自动处理 |
| blocker / scope change / Owner decision 才停 | 仅在阻塞、范围变更或 Owner 决策时暂停 |
| 不修改其他 Resolve Project | 操作范围限定于当前 Brief 关联工程 |
| 不把工具成功返回等价为最终结果成功 | 工具返回成功 ≠ 剪辑质量达标 |

---

## 层级依赖关系

```
L4 Production Brief
        ↓
L3 Production Workflow  ←── Cross-cutting Rules（横切）
        ↓
L2 Editing Strategy Skill
        ↓
L1 Capability Knowledge
        ↓
L0 Runtime / Tools
```

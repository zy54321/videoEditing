# Video Editing Workflow

一个独立于 Astra、独立于具体视频项目的 **AI-assisted video editing workflow / skill package**。

## 定位

本项目将「每次重新给 AI 写一大段如何剪视频的 Prompt」转化为可复用的生产体系：

| 输入 | 输出 |
|------|------|
| 一次性 Prompt 堆砌 | **Production Brief** — 声明要做什么视频 |
|  | **Reusable Production Workflow** — 通用生产流水线 |
|  | **Reusable Editing Strategy Skills** — 按视频类型的剪辑策略 |
|  | **Tool Capability Knowledge** — 工具如何实现剪辑动作 |
|  | **Runtime Execution** — 在编辑器中真正执行 |

## 当前运行环境

- **Cursor** — AI 编排与执行环境
- **DaVinci Resolve** — 当前第一个 Runtime / Execution Backend
- **samuelgursky/davinci-resolve-mcp** — 已跑通的 Resolve 自动化桥接

> DaVinci 是当前第一个 Runtime，**不是**整个项目的产品身份。  
> 未来允许扩展：Premiere、FFmpeg、其他视频编辑器 / Runtime。

## 项目解决什么问题

把：

> 「每次重新给 AI 写一大段如何剪视频的 Prompt」

转化为：

> **Production Brief** + **Reusable Production Workflow** + **Reusable Editing Strategy Skills** + **Tool Capability Knowledge** + **Runtime Execution**

让 AI 不再依赖临场发挥的 Prompt，而是按层级加载 Brief、Workflow、Skill 与 Capability 知识，在 Runtime 中完成剪辑。

## 项目当前不负责什么

V0.1 是 **Workflow Installer**，不是 **Full Environment Installer**。

### What this installer installs (PACKAGED)

- Cursor Rules
- Cursor Skills
- L1 Capability Reference
- Production Brief Template
- Workspace Installer

### What it does NOT install

- DaVinci Resolve
- DaVinci MCP
- FFmpeg / ffprobe
- Kokoro TTS
- Node / Python runtime
- 研究用 MCP / Skill 仓库（Plotline、ChaiWithJai、CiprianSpiridon 等）

### Runtime dependency model

| Class | Examples |
|-------|----------|
| **PACKAGED** | Rules, Skills, templates, installer |
| **REQUIRED EXTERNAL** | Cursor, DaVinci Resolve Studio, compatible external DaVinci MCP |
| **AUXILIARY / CONDITIONAL** | FFmpeg/ffprobe (fallback/verify), Kokoro (TTS only when needed) |
| **RESEARCH ONLY** | 其他 MCP/Skill 研究项目 — 不进入 Release，不自动下载 |

当前**已验证**（validated ≠ vendor lock）环境：DaVinci Resolve Studio **21.1.0.14** + `samuelgursky/davinci-resolve-mcp` **v4.8.13**。

首次生产输入 **【制作视频】** 后，Agent 在 Preparation / Preflight 检查必要 Runtime 是否就绪；不会自动安装或修改 MCP / Resolve。

本项目**不包含**、**不管理**、**不分发**：

- 视频素材
- 具体 Resolve Project
- Astra

## 目录结构

```
011-video-editing-workflow\          ← 项目级根目录（本 README 所在位置）
│
├─ README.md
├─ docs\                             ← 项目背景、架构、范围
├─ research\                         ← 研究资料与参考
├─ validation\                       ← 验证案例记录
├─ releases\                         ← Release 产物
└─ source\                           ← 产品源码（干净区域）
    ├─ payload\                      ← 安装到 Cursor 工作区的内容
    ├─ installer\
    ├─ build\
    ├─ tests\
    ├─ VERSION
    └─ manifest.template.json
```

**边界原则：** 项目背景、架构、研究、验证、Release 与 `source` 平级；真正的产品实现只进入 `source/`。

## 当前阶段

### V0.1.1（已发布 — First Real Production Baseline）

从此版本起，系统允许进入**真实 Production**，并以真实成片反馈驱动后续能力演进。

- `PRODUCTION_MINIMUM_BUNDLE = READY`
- `REMAINING_PRODUCTION_BLOCKERS = []`
- 字幕基线：**Native DRT subtitles + semantic segmentation**（08E accepted degradation）
- Text+ overlay / keyword emphasis / pixel width 等为 enhancement backlog，**不阻塞**首条 Production

详见 [V0.1 范围](docs/03-v0.1-scope.md)、[Stage 08F closeout](validation/stage-08f-closeout.md)。

### V0.1.0（已发布 — immutable）

以 **N02** 真实生产作为第一条 validation case。

目标：在一个新的 Cursor 工作区中初始化 Release 后，仅提供 Production Brief 并调用 `video-production` Skill，系统能够自动完成从分析、剪辑、后期到 QA / Render / Closeout 的完整流程。

详见：

- [项目背景](docs/01-project-background.md)
- [架构与层级模型](docs/02-architecture-and-layer-model.md)
- [V0.1 范围](docs/03-v0.1-scope.md)
- [N02 验证案例](validation/N02/README.md)

## Quick Start（最终使用方式）

1. 解压 **Release Package**
2. 双击 `init-video-workflow.bat`
3. 选择存放本次 Production Workspace 的**父目录**，然后输入 **Workspace 名称**
4. 用 Cursor 打开安装器创建的 Workspace 子目录（例如 `E:\Productions\N02-Production-01`）
5. 在对话中输入：

```
【制作视频】
```

Agent 会主动询问视频类型、input、output，无需编写复杂 Prompt。

**注意：** Release 可以反复用于初始化**不同** Workspace；但**每一个**已初始化的 Workspace 只对应**一条** Production。制作新视频请重新运行 Release，在父目录下创建新的 Workspace 名称。

开发阶段 Installer 位于 `source/installer/`；Smoke 测试位于 `source/tests/installer-smoke.ps1`。

## License

待定。

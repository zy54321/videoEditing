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

本项目**不包含**、**不管理**、**不分发**：

- DaVinci Resolve 本体
- DaVinci MCP Server（使用外部已安装的 samuelgursky/davinci-resolve-mcp）
- FFmpeg Runtime
- Kokoro
- ASR Model
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

### V0.1

以 **N02** 真实生产作为第一条 validation case。

目标：在一个新的 Cursor 工作区中初始化 Release 后，仅提供 Production Brief 并调用 `video-production` Skill，系统能够自动完成从分析、剪辑、后期到 QA / Render / Closeout 的完整流程。

详见：

- [项目背景](docs/01-project-background.md)
- [架构与层级模型](docs/02-architecture-and-layer-model.md)
- [V0.1 范围](docs/03-v0.1-scope.md)
- [N02 验证案例](validation/N02/README.md)

## License

待定。

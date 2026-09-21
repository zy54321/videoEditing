# 项目背景

## 产生原因

在尝试用 AI 辅助完成真实短视频生产的过程中，我们发现：**单纯「能调用 Resolve」不等于「知道怎么剪」**。

## 当前已完成

1. **DaVinci Resolve Studio 21.1** 自动化连接已跑通。
2. 当前稳定使用：**samuelgursky/davinci-resolve-mcp**
3. 已验证以下能力：
   - Project 操作
   - Timeline 操作
   - Media Import
   - Audio / Video 编排
   - Resolve transcription
   - Render
   - QA / Repair
4. 已完成多轮 **AutoCut** 测试。
5. 已进入 **N02** 第一次真实短视频生产。

## N02 暴露出的关键问题

| 问题域 | 描述 |
|--------|------|
| 剪辑策略缺失 | 单纯「能调用 Resolve」不等于「知道怎么剪」 |
| Motion | Stock footage 存在明显慢动作，需要 **Motion Normalization** |
| Transition | 只有 Hard Cut 时镜头转换可能生硬 |
| Subtitle | 字幕需要成为标准生产步骤 |
| Audio Mix | 背景音乐 / Audio Mix 需要标准化 |
| Framing | 9:16 framing 需要统一策略 |
| Genre | 不同视频类型需要不同剪辑语言 |
| 能力层级 | 现有能力需要从「工具能力」上升到「剪辑策略知识」 |

## 项目因此建立

**核心目标：** 建立可复用的视频剪辑 Skill / Workflow 系统。

将分散在 Prompt 中的剪辑知识、生产流程与工具调用方式，沉淀为可安装、可版本化、可验证的产品包。

## 与外部系统的关系

- **Astra** — 独立项目，当前不集成
- **DaVinci Resolve MCP** — 消费外部已安装实例，不修改、不替换
- **具体 Resolve Project** — 不纳入本项目管理；Validation 仅记录行为与结果

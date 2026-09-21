# Video Editing Workflow v0.1.0

基于 Cursor Rules + Skills + 外部 DaVinci Resolve Runtime 执行 AI-assisted video production。

## Install

1. 解压 Release
2. 双击 `init-video-workflow.bat`
3. 选择本次视频的 Cursor Workspace
4. 用 Cursor 打开该 Workspace

## Start

只输入：

```
【制作视频】
```

Agent 会主动：

- 让用户选择视频类型
- 索要 input/output
- 检查素材
- 生成 Production Brief
- 进入正式制作
- QA / Repair / Render

## Instance Model

Release 可以反复使用。

但是：一个初始化 Workspace 只服务一个 Production。

新视频：重新运行 Installer，选择新的 Workspace。

## Runtime Requirement

当前 V0.1 已验证运行环境：

- Cursor
- DaVinci Resolve Studio
- 已配置的外部 DaVinci Resolve MCP

Release 本身不安装、不修改、不管理 MCP / Resolve。

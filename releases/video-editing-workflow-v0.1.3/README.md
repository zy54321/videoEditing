# Video Editing Workflow v0.1.3

基于 Cursor Rules + Skills + 外部 DaVinci Resolve Runtime 执行 AI-assisted video production。

## Install

1. 解压 Release
2. 双击 `init-video-workflow.bat`
3. 选择存放本次 Production Workspace 的**父目录**，然后输入 **Workspace 名称**
4. 用 Cursor 打开安装器创建的 Workspace 子目录（例如 `E:\Productions\N02-Production-01`）

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

新视频：重新运行 Installer，在父目录下创建新的 Workspace 名称。

## Runtime Requirement

当前 V0.1 已验证运行环境：

- Cursor
- DaVinci Resolve Studio
- 已配置的外部 DaVinci Resolve MCP

Release 本身不安装、不修改、不管理 MCP / Resolve。

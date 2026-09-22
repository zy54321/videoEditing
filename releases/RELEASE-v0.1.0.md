# Release v0.1.0

| Field | Value |
|-------|-------|
| Version | 0.1.0 |
| Source Commit | 21b92a4a0a93a9e9f9d01878512415f3600e689b |
| Build Timestamp | 2026-09-22T08:05:06+08:00 |
| Release Directory | `releases/video-editing-workflow-v0.1.0` |
| ZIP | `releases/video-editing-workflow-v0.1.0.zip` |
| ZIP size (bytes) | 51402 |
| ZIP SHA256 | de9f7f65e39b855d49a1b2bec075338d92affbed640479e6cb5dc24806480803 |
| Installer Smoke | PASS |
| Pre-release Consistency | PASS |
| Release Smoke | PASS |
| ZIP Independent Install | PASS |
| N02 Capability Gate | PASS |
| Runtime Model | external-runtime |
| Remote status | REMOTE_NOT_CONFIGURED |

## Known Limitations

1. 当前仅包含 `observational-info-short` 一种 L2 剪辑策略。
2. 当前主要验证 backend 为 DaVinci Resolve。
3. `live_api_srt_append`：UNSAFE / DO NOT RETRY。
4. 字幕安全路径：`native_drt_subtitles`。
5. live transition route：FAILED。
6. transition 安全路径：`native_drt_transition`。
7. Resolve-native item audio volume：FAILED。
8. 背景音乐电平 fallback：`ffmpeg_pre_attenuation`。
9. audio ducking：UNKNOWN / OPTIONAL。
10. subtitle timing：Production QA 责任，非 Capability Gate blocker。
11. Runtime：Release 不安装、不修改 Resolve / MCP。

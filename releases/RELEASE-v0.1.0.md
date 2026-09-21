# Release v0.1.0

| Field | Value |
|-------|-------|
| Version | 0.1.0 |
| Build commit | 9ff30e73cf60f22ffed4f4d2da0e67bc3f3843d3 |
| Build date/time | 2026-09-21T21:38:26+08:00 |
| Source HEAD | 9ff30e73cf60f22ffed4f4d2da0e67bc3f3843d3 |
| Release file count | 16 |
| ZIP size (bytes) | 49167 |
| ZIP SHA256 | 8d928a50d490dc38b623e5d6f1a8c679c426cf1bd9afb513761bdcab5e80620d |
| Installer smoke | PASS |
| Release smoke | PASS |
| N02 capability gate | PASS |
| Remote status | REMOTE_NOT_CONFIGURED |

## Known Limitations

1. 当前只有 observational-info-short 一种 L2 剪辑策略。
2. 当前主要验证 Runtime 为 DaVinci Resolve。
3. live_api_srt_append route 为 UNSAFE；当前使用安全 DRT route。
4. live transition route FAILED；当前使用 native_drt_transition route。
5. DaVinci-native item audio volume FAILED；当前允许 FFmpeg pre-attenuation fallback。
6. ducking 未实现，非阻塞项。
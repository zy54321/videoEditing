# Release v0.1.1

| Field | Value |
|-------|-------|
| Version | 0.1.1 |
| Source Commit | e0076cc87a2ace317d64cce50070bdf83e0661fc |
| Build date/time | 2026-09-24T08:10:32+08:00 |
| Release file count | 74 |
| ZIP size (bytes) | 161282 |
| ZIP SHA256 | 026c14f25df781a2e8f71440c74a7d4adbd17f48ea20ad5f7a840524422919ce |
| Installer smoke | PASS |
| Release smoke | PASS |
| N02 capability gate | PASS |
| Remote status | REMOTE_NOT_CONFIGURED |

## Release Position

**First Real Production Baseline** — capability-complete for first Production; not feature-complete.

| Gate | Status |
|------|--------|
| PRODUCTION_MINIMUM_BUNDLE | READY |
| REMAINING_PRODUCTION_BLOCKERS | [] |
| Subtitle baseline | Native DRT + semantic segmentation |

## Known Limitations

1. 当前只有 observational-info-short 一种 L2 剪辑策略。
2. 当前主要验证 Runtime 为 DaVinci Resolve。
3. live_api_srt_append route 为 UNSAFE；当前使用安全 DRT route。
4. live transition route FAILED；当前使用 native_drt_transition route。
5. DaVinci-native item audio volume FAILED；当前允许 FFmpeg pre-attenuation fallback。
6. ducking 未实现，非阻塞项。
7. subtitle.layout.pixel_width / subtitle.style.keyword_emphasis = AVAILABLE_UNVERIFIED（accepted degradation）。
8. Text+ production overlay = PARTIAL；不得升级为 production VERIFIED。
9. motion / LUT / OFX / Fusion effects = enhancement backlog，非 P0 blocker。
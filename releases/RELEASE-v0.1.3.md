# Release v0.1.3

| Field | Value |
|-------|-------|
| Version | 0.1.3 |
| Source Commit | 58e646cdd15bc49f959448e99aad537a6db9423e |
| Build date/time | 2026-09-27T21:08:57+08:00 |
| Release file count | 117 |
| ZIP size (bytes) | 228352 |
| ZIP SHA256 | d2b0e0a591ca8e2b70f8e7b2c2abd87b0f1f52247c69bdb4befcdd8f433facfb |
| Installer smoke | PASS |
| Release smoke | PASS |
| N02 capability gate | PASS |
| Remote status | CONFIGURED |

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
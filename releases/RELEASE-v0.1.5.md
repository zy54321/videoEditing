# Release v0.1.5

| Field | Value |
|-------|-------|
| Version | 0.1.5 |
| Source Commit | c527f704dd18b768ff9da2c8075c74c94aa1ca22 |
| Build date/time | 2026-10-21T09:49:18+08:00 |
| Release file count | 166 |
| ZIP size (bytes) | 310224 |
| ZIP SHA256 | 53c5ebd9e690bed7e3ddde5ee9b59a814d4a77df14113102de813cafc63caeef |
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
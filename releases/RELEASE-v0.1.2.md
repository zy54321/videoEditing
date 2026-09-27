# Release v0.1.2

| Field | Value |
|-------|-------|
| Version | 0.1.2 |
| Source Commit | 25233fd0ad938336c3e66d3b31110e84a6feedbc |
| Build date/time | 2026-09-27T15:09:35+08:00 |
| Release file count | 112 |
| ZIP size (bytes) | 258239 |
| ZIP SHA256 | 751413bb16548fea2b1280acb086a7fbed3a8f105a5520484f27dd26aaf7db5d |
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
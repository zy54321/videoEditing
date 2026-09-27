# N02 V6 Production Closeout — External ASS Final

| Field | Value |
|-------|--------|
| **Starting HEAD (route review)** | `5b10557` |
| **VERSION** | `0.1.3-dev` |
| **Timeline** | `N02-V6-Audio-Repair` |
| **Subtitle runtime** | `subtitle.runtime.external_ass` |
| **Final artifact** | `E:\03_Media\02_Video\Davinci\Astra\2026-09-21\output\N02_V6.mp4` |
| **FINAL_ARTIFACT_SHA256** | `0a4028a65b546e06cc1bfabb0b84ed3c948da0c42e3d3350a11c6624ccea3462` |

## Pipeline

```
N02-V6-Audio-Repair (Resolve, no subtitle burn-in)
  → N02_V6_clean_master.mp4 (H.264 mezzanine, INTERMEDIATE_LIMITATION)
  → layout engine (Microsoft YaHei UI Bold) → ASS
  → ffmpeg libass burn-in (audio copy)
  → loudnorm two-pass (video preserved)
  → N02_V6.mp4
```

**Second lossy video generation:** Yes — Resolve H.264 clean master + one libx264 CRF18 burn-in pass. Mezzanine ProRes/DNxHR/FFV1 rejected by Resolve on this host.

## Gates

| Gate | Result |
|------|--------|
| FONT_DEPENDENCY | **PASS** (`msyhbd.ttc`) |
| FRAME_PARITY | **PASS** (1821 / 1821 / 1821) |
| PORTRAIT_FILL / BLACK_BAR / LAYOUT | **PASS** |
| FINAL_AUDIO | **PASS** (−16.1 LUFS, −1.4 dBTP, 48 kHz stereo) |
| MUSIC_MIX_BALANCE | **PASS** (V6 music stem vs V4 reference) |
| SUBTITLE_* (35 cues, timing, geometry, burn-in) | **PASS** |
| FINAL_ARTIFACT | **PASS** |
| **READY_FOR_OWNER_REVIEW** | **YES** |

## Capability promotion

| Capability | Status |
|------------|--------|
| `subtitle.runtime.external_ass` | **VERIFIED** |
| `subtitle.render.readable_static` | **VERIFIED** |
| Native DRT | Retained for preview / stroke / fallback — not N02 final renderer |

## Evidence

- `validation/n02-v6-subtitle-production-plan.json`
- `validation/n02-v6-subtitle-timing-trace.json`
- `validation/n02-v6-subtitle-final-qa.json`
- `validation/n02-v6-final-artifact-qa.json`
- `validation/scripts/n02-v6-external-ass-production.py`

## Intermediate artifacts (not in git)

| Path | Purpose |
|------|---------|
| `N02_V6_clean_master.mp4` | Clean picture+audio |
| `_N02_V6_INTERMEDIATE_subtitles.ass` | ASS renderer input |
| `_N02_V6_INTERMEDIATE_subtitle_burnin.mp4` | Pre-loudnorm burn-in |

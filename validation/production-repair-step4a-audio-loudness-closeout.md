# Production Repair Step 4A — Final Audio Loudness Closeout

## Scope

Final Audio Loudness / Voice–BGM Mix / Audio QA only.

| | |
|---|---|
| **Runtime executed** | NO (disposable FFmpeg fixtures only) |
| **Production executed** | NO |
| **N02 touched** | NO |
| **N02 V5** | NOT run |

## Git

| | SHA |
|---|-----|
| Starting HEAD | `da5e39ae7f9d00d72b40a3185f0bc093faecd4f0` |
| Ending HEAD | _(commit below)_ |

## Audio Runtime Capability Inventory

### Resolve software vs Runtime automation

| Layer | Voice place | Music place | Clip gain | Ducking | Fades | Loudness norm |
|-------|-------------|-------------|-----------|---------|-------|---------------|
| Resolve/Fairlight | Yes | Yes | Yes | Yes (UI) | Yes | Yes |
| Current MCP evidence | **VERIFIED** | **VERIFIED** | **FAILED** | **UNKNOWN** | **VERIFIED** | **AVAILABLE_UNVERIFIED** |

### Production routes (evidence-based)

| Capability | Status | Evidence |
|------------|--------|----------|
| `audio.music.place` | VERIFIED | 04A-R2 |
| `audio.music.level_under_voice` | VERIFIED | `ffmpeg_pre_attenuation` 0.15 |
| `audio.voice_music_mix` | VERIFIED | continuous pre-attenuated BGM |
| `audio.music.duck` | UNKNOWN | unchanged |
| `audio.final.measure_loudness` | **VERIFIED** | Step 4A fixtures |
| `audio.final.true_peak_qa` | **VERIFIED** | Step 4A fixtures |
| `audio.final.normalize_or_adjust` | **BLOCKED** | no verified auto route |
| `qa.audio` | **VERIFIED** | loudness verdicts |
| `FINAL_AUDIO_AUTO_REPAIR` | **BLOCKED** | fail closed |

## narration_short_v1 Profile

File: `video-workflow/runtime/narration-short-v1-audio-mix-profile.yaml`

| Field | Value |
|-------|-------|
| Integrated target | **-16 LUFS** ±1 LU |
| Accept range | -17 … -15 LUFS |
| True peak ceiling | **-1 dBTP** |
| Voice | primary |
| Music | supporting, continuous (not gated on pause) |

## N02 V4 Offline Reference

| Metric | Value |
|--------|-------|
| Integrated Loudness | ≈ **-24.8 LUFS** |
| True Peak | ≈ **-5.84 dBTP** |
| Gap to profile | ≈ **8.8 LU** |

## Implementation Routes

| Component | Path |
|-----------|------|
| Profile | `runtime/narration-short-v1-audio-mix-profile.yaml` |
| Reference / audit | `templates/narration-short-v1-audio-mix-reference.md` |
| Loudness QA | `tools/audio-loudness-qa.py` |
| Library | `tools/lib/audio_loudness_qa.py` |
| Final artifact integration | `tools/final-artifact-qa.ps1` → `audio_loudness_qa` section |

## BGM Level Strategy

1. Probe voice integrated LUFS (narration master).
2. Probe music integrated LUFS (READY asset).
3. Compute attenuation so music ≈ **14 LU** below voice; clamp **0.08–0.35**.
4. Fallback: verified spike **`0.15`** when probes unavailable.
5. BGM spans full timeline — does **not** drop during ~0.6–0.8s narration pauses (not ducking).

## Validation (Disposable FFmpeg — no Resolve)

| Case | Fixture | Result |
|------|---------|--------|
| A — Voice only | `voice_only.wav` @ -16 LUFS | **PASS** |
| B — Voice + BGM | amix + loudnorm | **PASS** + attenuation recommendation |
| C — Too low | -30 LUFS | **LOUDNESS_TOO_LOW** |
| C — Too high | -10 LUFS | **LOUDNESS_TOO_HIGH** |
| C — True peak | limiter abuse | **TRUE_PEAK_EXCEEDED** |
| C — No audio | silent MP4 | **NO_AUDIO** |

## Tests

| Suite | Result |
|-------|--------|
| `production-audio-mix-profile.ps1` | **37/37 PASS** |
| `shared-asset-library.ps1` regression | included |
| `capability-resolution-consistency.ps1` | included |
| `production-subtitle-readability.ps1` | included |

## Status

**READY_FOR_STEP_4B**

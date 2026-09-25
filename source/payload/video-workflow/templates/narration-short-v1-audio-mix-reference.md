# narration_short_v1 — Final Audio Mix Reference (Step 4A)

## Profile authority

`video-workflow/runtime/narration-short-v1-audio-mix-profile.yaml`

## Consolidated Audio Runtime Audit

### Resolve / Fairlight (software capability)

| Area | Resolve supports | Automation via current MCP |
|------|------------------|----------------------------|
| Voice placement | Yes | **VERIFIED** (`audio.place_on_track`) |
| Music placement | Yes | **VERIFIED** (`audio.import`, `audio.place_on_track`) |
| Clip / track gain | Yes (Fairlight) | **FAILED** — `audio.volume` write+readback false on WAV |
| Auto ducking | Yes (manual/automation UI) | **UNKNOWN** (`audio.ducking`) |
| Fades | Yes | **VERIFIED** (`audio.fade` / `set_fades`) |
| Loudness normalization | Yes (Fairlight meters / deliverable loudness) | **AVAILABLE_UNVERIFIED** — no evidenced MCP route |
| Master output gain | Yes | **AVAILABLE_UNVERIFIED** — not in verified production chain |

### Current Runtime evidence (what we may claim VERIFIED)

| Route | Status | Evidence |
|-------|--------|----------|
| `audio.music.place` | **VERIFIED** | 04A-R2 integrated render |
| `audio.music.level_under_voice` / `ffmpeg_pre_attenuation` | **VERIFIED** | `volume=0.15` derived WAV → A3 |
| `audio.music.crossfade` | **VERIFIED** | FadeIn 12 / FadeOut 24 frames |
| `audio.music.duck` | **UNKNOWN** | No reliable API — **do not upgrade** |
| `audio.final.measure_loudness` | **VERIFIED** (Step 4A) | `audio-loudness-qa.py` + ebur128 on fixtures |
| `audio.final.true_peak_qa` | **VERIFIED** (Step 4A) | same tool |
| `audio.final.normalize_or_adjust` | **BLOCKED** | No verified auto-adjust route |
| `audio.voice_music_mix` | **VERIFIED** | Pre-attenuated continuous BGM under voice |
| `FINAL_AUDIO_AUTO_REPAIR` | **BLOCKED** | QA fail-closed; no auto re-render loop |

### N02 V4 reference (offline — artifact not modified)

| Metric | Value |
|--------|-------|
| Integrated Loudness | ≈ **-24.8 LUFS** |
| True Peak | ≈ **-5.84 dBTP** |
| Gap to profile target (-16 LUFS) | ≈ **8.8 LU** |

Qualitative: voice intelligible; music present; overall deliverable too quiet for `narration_short_v1`.

## Voice-first mix rules

1. Narration is primary — never masked by BGM.
2. BGM is continuous across narration pauses (~0.6–0.8s gaps in N02 V4) at low level — **not** gated ducking.
3. Use `ffmpeg_pre_attenuation` on immutable music source → derived WAV → Resolve import.
4. Attenuation factor is **measured**, not a magic constant — `0.15` remains verified fallback from spike.

## QA verdicts

| Verdict | Condition |
|---------|-----------|
| `PASS` | -17 ≤ I ≤ -15 LUFS and Peak ≤ -1 dBTP and audio stream exists |
| `LOUDNESS_TOO_LOW` | I < -17 LUFS |
| `LOUDNESS_TOO_HIGH` | I > -15 LUFS |
| `TRUE_PEAK_EXCEEDED` | Peak > -1 dBTP |
| `NO_AUDIO` | No audio stream |

Repair: **fail closed** — `FINAL_AUDIO_AUTO_REPAIR = BLOCKED`.

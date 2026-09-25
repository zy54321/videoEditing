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
| `audio.final.normalize_or_adjust` | **VERIFIED** (Step 4A-Repair) | `final-audio-loudness-repair.py` — ffmpeg loudnorm two-pass |
| `audio.voice_music_mix` | **VERIFIED** | Pre-attenuated continuous BGM under voice |
| `FINAL_AUDIO_AUTO_REPAIR` | **VERIFIED** (Step 4A-Repair) | `final-artifact-audio-qa-repair.ps1` — measure/repair separate; max 1 retry |

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

## Post-render loudness repair (Step 4A-Repair)

| Parameter | Value |
|-----------|-------|
| Route | `ffmpeg_loudnorm_two_pass` |
| Target I | **-16 LUFS** (±1 LU) |
| True peak ceiling | **-1 dBTP** |
| LRA (V1 engineering) | **7** — not claimed as universal platform standard |
| Max repair attempts | **1** |

**Pass 1:** `loudnorm` with `print_format=json` — capture `input_i`, `input_tp`, `input_lra`, `input_thresh`, `target_offset`.

**Pass 2:** explicit measured values + `linear=true` — not two independent one-pass runs.

**MP4:** `-c:v copy`; audio loudnorm + AAC. Original artifact preserved until QA PASS promotes repaired copy.

**Repairable:** `LOUDNESS_TOO_LOW`, `LOUDNESS_TOO_HIGH`, `TRUE_PEAK_EXCEEDED`.  
**No-op:** input already `PASS` → `NO_REPAIR_REQUIRED`.  
**Blocked:** `NO_AUDIO`, corrupt/unreadable streams.  
**Fail closed:** post-repair QA still fails → `FINAL_AUDIO_REPAIR_FAILED`.

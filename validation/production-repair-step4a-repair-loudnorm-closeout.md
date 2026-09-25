# Production Repair Step 4A-Repair — Final Audio Loudnorm Two-Pass Closeout

## Scope

Post-render final audio loudness auto-repair only. No mix redesign, no Resolve runtime, no N02.

| | |
|---|---|
| **Runtime executed** | NO (FFmpeg disposable fixtures only) |
| **Production executed** | NO |
| **N02 touched** | NO |
| **Starting HEAD** | `fd96d108d69a287eee8031e14fd1c42370b9070c` |

## Implementation

| Component | Path |
|-----------|------|
| Repair library | `tools/lib/audio_loudness_repair.py` |
| Repair CLI | `tools/final-audio-loudness-repair.py` |
| QA + repair orchestrator | `tools/final-artifact-audio-qa-repair.ps1` |
| Profile | `runtime/narration-short-v1-audio-mix-profile.yaml` |

### Two-pass contract

**Pass 1:** `loudnorm=I=-16:TP=-1:LRA=7:print_format=json` → parse `input_i`, `input_tp`, `input_lra`, `input_thresh`, `target_offset`.

**Pass 2:** explicit `measured_*` + `offset` + `linear=true` — not two independent one-pass runs.

### MP4 strategy

- Video: `-c:v copy`
- Audio: loudnorm two-pass → AAC 192k
- Verify codec / resolution / fps / duration tolerance

### Artifact policy

`original` → `.work/*.loudnorm-repaired.*` → QA PASS → optional `--promote-on-pass`. Failure leaves original intact.

### Retry policy

Max **1** loudnorm repair + re-QA. Still failing → `FINAL_AUDIO_REPAIR_FAILED`.

## Cases A–G (disposable validation)

| Case | Input | Result |
|------|-------|--------|
| A Too Low | ~-25 LUFS WAV | before **-25.0 LUFS** / **-21.0 dBTP** → after **-16.0 LUFS** / **-12.0 dBTP** → PASS |
| B Too High | ~-10 LUFS WAV | PASS after repair |
| C Peak | limiter spike | TRUE_PEAK detected; repair outcome explicit (PASS or fail-closed) |
| D Already PASS | -16 LUFS WAV | `NO_REPAIR_REQUIRED`, 0 attempts |
| E MP4 | H.264 + quiet audio | video stream preserved; audio PASS |
| F No Audio | silent MP4 | `BLOCKED` / `NO_AUDIO` |
| G Simulated fail | `LOUDNORM_REPAIR_SIMULATE_FAIL=1` | `FINAL_AUDIO_REPAIR_FAILED`; original hash unchanged |

## Capability truth (after evidence)

| Capability | Status |
|------------|--------|
| `audio.final.measure_loudness` | VERIFIED (unchanged) |
| `audio.final.true_peak_qa` | VERIFIED (unchanged) |
| `audio.final.normalize_or_adjust` | **VERIFIED** |
| `FINAL_AUDIO_AUTO_REPAIR` | **VERIFIED** |
| `audio.music.level_under_voice` | VERIFIED (unchanged) |
| `audio.music.duck` | UNKNOWN (unchanged) |

## Tests

`source/tests/production-audio-loudness-repair.ps1` — Cases A–G + orchestrator + regressions (4A, 4B, shared asset, subtitle, capability policy).

## Ending HEAD

`9e5e3887672bb03afc10499f9f521dbcf291c81a`

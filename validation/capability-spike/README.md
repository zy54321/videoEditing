# DaVinci Capability Spike — V0.1

## Stage Status

| Stage | Status | Date |
|-------|--------|------|
| 04A | **BLOCKED_RUNTIME_CRASH** | 2026-09-21 |
| 04A-R1 Safe Route Recovery | **COMPLETE** (no second crash) | 2026-09-21 |
| 04A-R2 N02 Blocker Closure | **COMPLETE** (no crash) | 2026-09-21 |

## Disposable Projects (do not use for production)

| Project | Purpose |
|---------|---------|
| `VEW-Capability-Spike-V01` | Original spike (terminated at CAP-05) |
| `VEW-R1-Transition` | CAP-04 transition + subtitle DRT import |
| `VEW-R1-Audio` | CAP-06~08 audio isolation |
| `VEW-Capability-Spike-R2` | R2 vertical / transition / music / integrated |

## Crash Record

See [`CRASH-20260921.md`](./CRASH-20260921.md).

**CRASH_BOUNDARY:** SRT MediaPool item → `AppendToTimeline` (subtitle) → Resolve abort.

**Rule:** Do **not** retry `live_api_srt_append` in automated production.

---

## Stage 04A-R1 Results

| CAP | Capability | Result | Evidence |
|-----|------------|--------|----------|
| — | Crash evidence | **RECORDED** | `CRASH-20260921.md` |
| CAP-01 | `clip.scale` | **VERIFIED** | Stage 04A: ZoomX/Y=1.35 read-back (promoted, no re-write) |
| CAP-02 | `clip.position` | **VERIFIED** | Stage 04A: Pan=0.15, Tilt=-0.1 read-back (promoted) |
| CAP-03 | `clip.speed` | **VERIFIED** | Stage 04A: 150%, duration 144→96, gap clean after reposition |
| CAP-04 | `transition.apply` | **FAILED** | R1 single attempt: `options must be a non-empty dictionary` |
| CAP-05 | Subtitle safe route | **VERIFIED** | `native_drt_subtitles`: assemble → import → 3 cues transcript |
| CAP-05 | `live_api_srt_append` | **UNSAFE** | Crash boundary (04A) — not retried |
| CAP-06 | Music placement | **VERIFIED** | `music.wav` on A2; append read-back verified |
| CAP-07 | Volume | **FAILED** | `Volume` write/readback `false` on WAV audio item |
| CAP-08 | Fade | **VERIFIED** | FadeIn=12, FadeOut=24 read-back |
| CAP-09 | Ducking | **UNKNOWN** | `audio_mix_capability_report` — no auto-duck API |
| CAP-10 | Render | **VERIFIED** (partial) | H.264+AAC 24fps 12s; **1920×1080** (not 1080×1920) |

## Stage 04A-R2 Results

| CAP | Capability | Result | Evidence |
|-----|------------|--------|----------|
| CAP-R2-01 | Vertical timeline identity | **VERIFIED** | Project+timeline read-back: 1080×1920, 24fps |
| CAP-R2-02 | Vertical render | **VERIFIED** | `vertical-test.mp4` ffprobe: 1080×1920, 24fps, H.264+AAC |
| CAP-R2-03 | DRT transition | **VERIFIED** | Cross Dissolve 6f read-back; `transition-test.mp4` 1080×1920 |
| CAP-R2-04 | Resolve-native volume | **FAILED** | `set_property` ITEM_INDEX_OUT_OF_RANGE on probe timeline |
| CAP-R2-05 | FFmpeg music level | **VERIFIED** | `music_attenuated.wav` −16.5 dB mean; placed A3 + integrated render |
| CAP-R2-10 | Integrated render | **VERIFIED** | `integrated-test.mp4` 1080×1920, 6s, video+audio, DRT transition+voice+music |

**Render contract (R2):** explicit `FormatWidth: 1080`, `FormatHeight: 1920` in `prepare_render_job` settings.

**Live transition:** not retested in R2 (remains **FAILED** from R1; not N02 blocker).

---

## N02_V1_CAPABILITY_GATE

```
PASS
```

Stage 04A-R2 baseline only. **Not** N02 V2 execution readiness.

See `STAGE-08A1-n02-v2-execution-readiness.md` for `N02_V2_READINESS_GATE`.

**Non-blocking unknowns:** DaVinci-native volume; live transition API; ducking; visual 9:16 QA.

---

## Artifacts

| Path | Notes |
|------|-------|
| `temp-media/` | Synthetic FFmpeg test clips (regenerated in R1) |
| `output/VEW-R1-subtitle.drt` | DRT subtitle test archive |
| `output/VEW-R1-render.mp4` | R1 render sample (local only) |
| `r2-output/vertical-test.mp4` | R2 vertical render (local only) |
| `r2-output/transition-test.mp4` | R2 DRT transition render (local only) |
| `r2-output/integrated-test.mp4` | R2 integrated render (local only) |
| `r2-output/VEW-R2-transition.drt` | DRT transition test archive |
| `temp-media/music_attenuated.wav` | FFmpeg-derived music (gitignored) |

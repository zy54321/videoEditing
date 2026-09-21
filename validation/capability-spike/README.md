# DaVinci Capability Spike — V0.1

## Stage Status

| Stage | Status | Date |
|-------|--------|------|
| 04A | **BLOCKED_RUNTIME_CRASH** | 2026-09-21 |
| 04A-R1 Safe Route Recovery | **COMPLETE** (no second crash) | 2026-09-21 |

## Disposable Projects (do not use for production)

| Project | Purpose |
|---------|---------|
| `VEW-Capability-Spike-V01` | Original spike (terminated at CAP-05) |
| `VEW-R1-Transition` | CAP-04 transition + subtitle DRT import |
| `VEW-R1-Audio` | CAP-06~08 audio isolation |

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

## N02_CAPABILITY_GATE

```
BLOCKED
```

**Blockers:** `transition.apply` FAILED · `audio.volume` FAILED · vertical 1080×1920 render not verified.

**Resolved in R1:** safe subtitle route via DRT.

---

## Artifacts

| Path | Notes |
|------|-------|
| `temp-media/` | Synthetic FFmpeg test clips (regenerated in R1) |
| `output/VEW-R1-subtitle.drt` | DRT subtitle test archive |
| `output/VEW-R1-render.mp4` | CAP-10 render sample (local only, not committed) |

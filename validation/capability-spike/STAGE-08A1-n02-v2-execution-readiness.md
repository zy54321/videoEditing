# Stage 08A.1 — N02 V2 Execution Readiness

**Date:** 2026-09-22  
**Disposable project:** `VEW-08A1-N02V2-Readiness`  
**Forbidden:** N02 (`Astra-N02-Austria-Rules-20260921`), N02 media paths, `live_api_srt_append`

---

## Summary

```
N02_V2_READINESS_GATE = PASS
State: N02_V2_RUNTIME_READY
Next: Stage 08B — N02 V2 Real Production Acceptance
```

---

## Subtitle Functional Layout Spike

**Route:** `drt.assemble` with `spec.subtitles[]` (`startFrame`, `durationFrames`, `text` with `\n`)

| Test cue | Result |
|----------|--------|
| 单行短字幕 | Transcript + burn-in MP4 visible |
| 两行 + explicit `\n` | Two lines readable in MP4 |
| Semantic split (2 cues) | 4 cues on timeline |

**Evidence:**

- Timeline: `08a1-subtitle-events` — 4 subtitle items + video
- Transcript: 4 cues; cue 2 contains line break
- Render: `08a1-output/08a1-subtitle-render.mp4` (1080×1920, verified)
- Frames: `08a1-output/frames/sub-cue1-2s.png`, `sub-cue2-5s.png` — Agent vision PASS

| Capability | Status |
|------------|--------|
| `subtitle.line_break_control` | **VERIFIED** |
| `subtitle.safe_text_width` | **AVAILABLE_UNVERIFIED** (heuristic fallback) |
| `subtitle.position` | **UNKNOWN** |
| `subtitle.visual_style` | **UNKNOWN** (non-blocker) |

**Note:** `subtitlesSrt` path alone did not populate `SubtitleTrackVec` in DRT parse; use `spec.subtitles[]` for line-break control.

---

## Final Subtitle Artifact QA

**Pipeline:** `video-workflow/tools/final-artifact-qa.ps1` + Agent vision on extracted frames.

| Step | Status |
|------|--------|
| FFmpeg frame extract at cue midpoints | PASS |
| Subtitle visible in MP4 | PASS (vision) |
| Pipeline executable end-to-end | **VERIFIED** |

---

## Black-Bar QA

**Pipeline:** `final-artifact-qa.ps1` edge-band luminance heuristic.

| Sample | Verdict |
|--------|---------|
| `08a1-subtitle-render.mp4` (pillarbox from timeline aspect) | `SUSPECT_BLACK_BARS` |
| `08a1-letterbox.mp4` (intentional letterbox) | `SUSPECT_BLACK_BARS` |

Heuristic may flag both; use `AUTOMATED_SCREEN + VISUAL_CONFIRM` for borderline cases.

| Capability | Status |
|------------|--------|
| `final_render.black_bar_check` | **VERIFIED** (pipeline) |

---

## Mixed-FPS / Cadence

**Clips (FFprobe):**

| File | FPS | Duration |
|------|-----|----------|
| 08a1-fill-24fps.mp4 | 24 | 8.08s |
| 08a1-clip-25fps.mp4 | 25 | 4.0s |
| 08a1-clip-30fps.mp4 | 30 | 4.0s |

**Policy:** Safe Cadence Degradation documented in L1 §8 — no VERIFIED interpolation.

| Capability | Status |
|------------|--------|
| `mixed_fps.cadence_analyze` | **VERIFIED** |
| `mixed_fps.interpolation` | **UNKNOWN** (non-blocker) |

---

## Color Basic Spike

**Route:** Color page + `timeline_item_color.set_cdl` (array CDL format)

| Step | Result |
|------|--------|
| `safe_set_cdl` dry_run | PASS |
| `safe_set_cdl` live | **FAILED** (`set_cdl_returned_false`) |
| `set_cdl` live | **SUCCESS** |
| Node graph read-back | Tools present on node 1 |

| Capability | Status |
|------------|--------|
| `color.basic` | **VERIFIED** via `set_cdl` |

---

## Motion

| Capability | Status |
|------------|--------|
| `clip.speed_change` | **VERIFIED** (Stage 04A, unchanged) |

L2 requires per-clip **KEEP | NORMALIZE | REPLACE** — no `motion = SKIPPED` when slow motion detected.

---

## Artifacts (local, gitignored paths under validation/)

- `08a1-output/08a1-subtitle-render.mp4`
- `08a1-output/qa-test/*/final-artifact-qa.json`
- `08a1-output/frames/*.png`
- `temp-media/08a1-*.mp4`, `08a1-subtitle-layout.srt`

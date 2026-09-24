# Production Repair Step 2 — Native Subtitle Readability / Stroke Closeout

**Date:** 2026-09-24  
**Starting HEAD:** `e40df370b969f3e15016ececbfeaf30baa738a99`  
**Scope:** Native DRT subtitle readability profile only — no N02, no real Production, no Text+ pivot

---

## Preflight

| Check | Result |
|-------|--------|
| `releases/` rebuild residue | Restored — working tree clean before implementation |
| N02 touched | **NO** |
| Real Production executed | **NO** |
| Stage 08E reopened | **NO** |

---

## Native subtitle route (current)

```
Frozen Script / semantic segmentation
→ drt.assemble spec.subtitles[]
→ timeline.import_timeline_checked
→ ExportSubtitle: BurnIn deliver
```

**VERIFIED today:** placement, transcript, burn-in survivability (08A.1 + Step 2 disposable probe)  
**NOT VERIFIED today:** track-level stroke / outline automation

---

## FACT vs RUNTIME COVERAGE

| Item | Resolve UI (FACT) | Automation coverage |
|------|-------------------|---------------------|
| Subtitle cues on timeline | Yes | **VERIFIED** — `native_drt_subtitles` |
| Line breaks / semantic splits | Yes | **VERIFIED** — `spec.subtitles[]` + `\n` |
| Outer stroke (white on light bg) | Yes (18.6+ Inspector) | **BLOCKED** — no API; MCP has no stroke fields |
| Track font / position | Yes | **PARTIAL** — `project_db.set_subtitle_style` (font + position only); host lacks `better-sqlite3`; unstyled DRT tracks have no style blob to patch |
| `drt.assemble` style fields | N/A | **NOT_SUPPORTED** — `subtitleStyle` / `subtitleTrackStyle` ignored; `TRACK_FIELDS_BLOB` unstyled stub |
| Burn-in deliver | Yes | **VERIFIED** — disposable `stroke-probe-burnin.mp4` 1080×1920 |

---

## Implementation outcome

**Profile established:** `video-workflow/runtime/native-drt-subtitle-readability-profile.yaml`  
**Reference:** `video-workflow/templates/native-drt-subtitle-readability-reference.md`

**Automation result:** `NATIVE_SUBTITLE_STROKE_AUTOMATION = BLOCKED`

**Manual fallback:** Resolve Inspector outer stroke = `AVAILABLE_MANUAL`

---

## Disposable runtime validation

**Project:** `_mcp_VEW-Subtitle-Stroke-Probe` (disposable)  
**Evidence (local, gitignored):** `validation/subtitle-stroke-probe/stroke-probe-burnin.mp4`, `evidence/deliver-frame.png`

| Case | Background | Result |
|------|------------|--------|
| A — Dark | Black solid | White text visible; **no dark stroke** (not required on dark) |
| B — Light / white | Light generator segment | **Not isolated in this probe** (timeline generator read as black in vertical deliver) |
| C — Mixed / busy | — | **Not run** (stroke automation blocked; probe scoped to route truth) |
| D — Deliver | Burn-in MP4 | Subtitle text **survives** deliver; **no stroke** visible on dark frame |

Visual: deliver frame shows white glyphs `白字黑描边测试` without outline — confirms unstyled native DRT default.

---

## Capability truth (final)

| ID | Status |
|----|--------|
| `subtitle.render.readability_stroke` | **BLOCKED** |
| `subtitle.render.basic` | **VERIFIED** (unchanged) |
| `subtitle.segment.semantic` | **VERIFIED** (unchanged) |
| `subtitle.layout.pixel_width` | **AVAILABLE_UNVERIFIED** (unchanged) |
| `subtitle.style.keyword_emphasis` | **AVAILABLE_UNVERIFIED** (unchanged) |
| `native_drt_subtitles` | **VERIFIED** (unchanged) |
| Text+ overlay | **PARTIAL / isolated** (unchanged) |

---

## Tests

- `source/tests/production-subtitle-readability.ps1` — profile + truth regression
- Targeted PASS required before commit

---

## Blockers for next step

1. Harvest or author a styled `EffectFiltersBA` blob with outer-stroke params (opaque param IDs 19/34/142 not decoded in MCP codec), **or**
2. Extend advanced MCP `set_subtitle_style` with stroke fields + ensure `better-sqlite3` on host, **or**
3. Owner one-time UI style seed + `project_db` patch workflow (font/position only until stroke params mapped)

---

## READY_FOR_NEXT_STEP

Profile + truth registered. Stroke automation remains **BLOCKED** pending a verified automation route with light-background visual evidence.

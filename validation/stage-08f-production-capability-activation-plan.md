# Stage 08F — Production Capability Activation & Existing Resolve Inventory

**Date:** 2026-09-23  
**Baseline HEAD:** `225c4ea`  
**Mode:** Planning / Inventory / Gap Analysis only — **no Runtime writes, no Production execution**

**Upstream acceptance (closed):**

| Stage | Status |
|-------|--------|
| `STAGE_08E_A` | ACCEPTED |
| `STAGE_08E_B` | ACCEPTED_WITH_DEGRADATION |
| `STAGE_08E` | ACCEPTED |

**Frozen first Production subtitle baseline:** Native DRT subtitles + semantic segmentation

---

## 1. Consolidated inventory (13 domains)

Runtime = Samuel MCP 4.8.13 + Resolve Studio 21.1.0.14 evidence in-repo.  
Status labels = project logical truth — **not** “DaVinci software supports it.”

| # | Domain | Primary logical IDs | Status | Runtime evidence |
|---|--------|---------------------|--------|------------------|
| 1 | Clip assembly / source range / trim | `edit.cut`, `clip.assemble`, `clip.source_range`, `visual.trim` | **VERIFIED** / **VERIFIED** / **VERIFIED** / **AVAILABLE_UNVERIFIED** | 04A assemble + source read-back; trim timeline extent limited evidence |
| 2 | Static reframe | `visual.reframe.static` | **VERIFIED** | 04A scale/position read-back |
| 3 | Speed normalization | `visual.motion.speed_change` | **VERIFIED** | 04A 150% speed + duration |
| 4 | Hard cut / cross dissolve | `edit.transition.basic`, `edit.transition.cross_dissolve` | **VERIFIED** / **VERIFIED** | Hard cut via assemble; dissolve via `native_drt_transition` (04A-R2) |
| 5 | Basic color correction | `color.primary_balance` | **VERIFIED** | 08A.1 `set_cdl` array CDL read-back |
| 6 | LUT / Look | `color.look.apply`, `color.lut` (L1) | **VERIFIED** (CDL look) / **AVAILABLE_UNVERIFIED** (LUT file) | CDL route verified; LUT node path not E2E validated |
| 7 | Basic title / overlay | `graphics.title.basic` | **AVAILABLE_UNVERIFIED** | Fusion title path not production-shaped E2E |
| 8 | ResolveFX / OpenFX | `effects.resolvefx`, `effects.ofx` | **UNKNOWN** / **UNKNOWN** | DEFERRED; no MCP validation |
| 9 | Fusion effects / preset | `effects.fusion` | **AVAILABLE_UNVERIFIED** | DEFERRED; isolated Text+ ≠ production overlay |
| 10 | Audio placement / music level / fade | `audio.voice.place`, `audio.music.place`, `audio.music.level_under_voice`, `audio.music.crossfade` | **VERIFIED** | 04A-R2 music level + fades; voice assemble |
| 11 | Subtitle baseline | `subtitle.segment.semantic`, `subtitle.render.basic` | **VERIFIED** | 08A.1 `native_drt_subtitles`; 08E accepted degradation |
| 12 | Render | `render.configure`, `render.start`, `render.verify` | **VERIFIED** | 04A-R2 1080×1920 H.264 + FFprobe |
| 13 | Final artifact QA | `qa.final_artifact`, `qa.visual.frame`, `qa.subtitle.layout` | **VERIFIED** | 08A.1 `final-artifact-qa.ps1` pipelines |

**Explicitly NOT production baseline (08E closed):**

| Item | Status |
|------|--------|
| `subtitle.layout.pixel_width` | AVAILABLE_UNVERIFIED |
| `subtitle.style.keyword_emphasis` | AVAILABLE_UNVERIFIED |
| `textplus_styledtextcls_import_comp` | VERIFIED (isolated only) |
| `textplus_nested_timeline_overlay` | PARTIAL |

---

## 2. Production Minimum Capability Matrix (observational-info-short)

### REQUIRED (P0) — all VERIFIED

| Policy bucket | Logical capability | Status | Production route |
|---------------|-------------------|--------|----------------|
| Asset selection | `visual.select_asset` | VERIFIED | pool import + inspect |
| Static framing | `visual.reframe.static` | VERIFIED | clip scale/position |
| Hard cut | `edit.cut` | VERIFIED | assemble / DRT |
| Subtitle semantic | `subtitle.segment.semantic` | VERIFIED | native DRT + segmentation |
| Subtitle render | `subtitle.render.basic` | VERIFIED | native DRT burn-in path |
| Voice | `audio.voice.place` | VERIFIED | timeline assemble |
| Final QA | `qa.final_artifact`, `qa.visual.frame` | VERIFIED | render verify + frame QA |

### PREFERRED — degradation acceptable for first Production

| Policy bucket | Preferred | Status | VERIFIED fallback |
|---------------|-----------|--------|-------------------|
| Motivated motion | push_in, pan | AVAILABLE_UNVERIFIED | `visual.reframe.static` |
| Speed normalization | speed_change | **VERIFIED** | — (no fallback needed) |
| Trim | `visual.trim` | AVAILABLE_UNVERIFIED | **`clip.source_range` + assemble** (see §4) |
| Dissolve | cross_dissolve | **VERIFIED** | `edit.transition.basic` (hard cut) |
| Pixel layout | pixel_width | AVAILABLE_UNVERIFIED | `subtitle.segment.semantic` |
| Music under voice | duck | UNKNOWN | `audio.music.level_under_voice` |
| Color shot match | shot_match | AVAILABLE_UNVERIFIED | `color.primary_balance` |
| Subtitle visual QA | qa.subtitle.layout | **VERIFIED** | — |

### OPTIONAL — not P0

keyword emphasis, color look (optional policy), music bed optional, SFX, titles, ResolveFX, Fusion, LUT file, advanced styling.

---

## 3. VERIFIED capability bundle (first Production)

```
media import / inspect
→ clip.source_range + clip.assemble + edit.cut
→ visual.reframe.static
→ visual.motion.speed_change (when needed)
→ transition.apply (dissolve) OR hard cut fallback
→ audio.voice.place + audio.music.level_under_voice + audio.music.crossfade
→ color.primary_balance (CDL)
→ subtitle.segment.semantic + native_drt_subtitles
→ render.configure + render.start + render.verify
→ final-artifact-qa (frame / subtitle / black-bar)
```

---

## 4. `visual.trim` — not a P0 blocker

| Question | Answer |
|----------|--------|
| First Production needs timeline post-placement trim API? | **No** — editorial in/out is expressed via **`clip.source_range` (VERIFIED)** before/at assembly |
| `clip.assemble` + `edit.cut` sufficient for V1 rhythm? | **Yes** for observational B-roll + narration assembly |
| `visual.trim` (timeline extent) blocks Production? | **No** — PREFERRED only; unresolved in coverage but **not REQUIRED** |
| When would trim matter later? | Repair pass adjusting clip head/tail on timeline without re-import — enhancement, not first-run blocker |

**Conclusion:** Do **not** elevate `visual.trim` to Stage 08F validation candidate.

---

## 5. P0 blocker analysis (AVAILABLE_UNVERIFIED / UNKNOWN scan)

For each non-VERIFIED item in inventory — “Does first real Production **require** it with no fallback?”

| Item | Required? | Fallback? | Blocker? |
|------|-----------|-----------|----------|
| `visual.trim` | No | source_range assembly | **No** |
| `visual.motion.push_in/pan` | No | static reframe | **No** |
| `subtitle.layout.pixel_width` | No (accepted) | semantic segmentation | **No** |
| `subtitle.style.keyword_emphasis` | No (accepted) | plain DRT text | **No** |
| `color.lut` | No | CDL look | **No** |
| `graphics.title.basic` | No | none needed V1 | **No** |
| `effects.resolvefx/ofx/fusion` | No | DEFERRED | **No** |
| `audio.music.duck` | No | level_under_voice | **No** |
| `audio.sfx.place` | No | skip SFX | **No** |
| `qa.audio` | No | render.verify streams | **No** |
| `subtitle.style.basic` | No | DRT functional style | **No** |

---

## 6. REMAINING_PRODUCTION_BLOCKERS

```
REMAINING_PRODUCTION_BLOCKERS = []
```

No logical capability gap blocks first Production **given**:

- Accepted 08E subtitle degradation
- observational policy REQUIRED set fully VERIFIED
- PREFERRED gaps have documented VERIFIED fallbacks

**Caveat (process, not capability):** First Production still needs Owner authorization for **Runtime write operations** on a real project — that is governance, not a missing capability.

---

## 7. Runtime validation candidates (Stage 08F)

**None required for P0.**

Optional future enhancements (backlog only — do not open 08F validation without new Owner scope):

| ID | Trigger | Minimal probe shape |
|----|---------|---------------------|
| E1 | Owner requests timeline trim repair | Disposable clip extent adjust + read-back |
| E2 | Owner requests LUT-first look | Single LUT apply + frame verify |
| E3 | Owner re-opens Text+ overlay | 08E enhancement backlog items |

**This planning round does not authorize any Runtime write.**

---

## 8. Enhancement list (non-blocker)

1. Text+ production overlay final validation (08E backlog)
2. Keyword SIZE emphasis on overlay
3. Pixel-width production parity
4. Animated push-in / pan
5. `visual.trim` timeline API
6. ResolveFX / OpenFX / Fusion production effects
7. Advanced titles / rich typography
8. Auto music ducking envelope
9. LUT file workflow
10. Color shot-to-shot match automation

---

## 9. Stage 08F conclusion

| Gate | Status |
|------|--------|
| `STAGE_08F` | **CLOSED** — see `validation/stage-08f-closeout.md` |
| `PRODUCTION_MINIMUM_BUNDLE` | **READY** |
| `REMAINING_PRODUCTION_BLOCKERS` | **`[]`** |
| `STAGE_08F_RUNTIME_VALIDATION` | **NOT_REQUIRED** (no P0 candidates) |

**Closeout:** Stage 08F closed without new capability construction or Runtime validation.

**Next legal direction:**

> **Release baseline → First Real Production Intake** — Owner authorizes a specific Production with Runtime write scope; execute under existing VERIFIED bundle + accepted degradations.

---

## 10. Audit

| Item | Value |
|------|-------|
| Stage 08E reopened | **NO** |
| Implementation modified | **NO** (this planning doc only) |
| N02 touched | **NO** |
| Real Production executed | **NO** |
| Resolve project modified | **NO** |

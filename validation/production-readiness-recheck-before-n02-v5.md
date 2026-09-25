# Production Readiness Recheck — Before N02 V5

**Date:** 2026-09-25  
**Review type:** Consolidated evidence review — no implementation, no Runtime, no Production execution

---

## Git bookkeeping

| Label | SHA | Meaning |
|-------|-----|---------|
| **Starting HEAD** | `55404a1037249f1e3ff0addf9c8a578fc6c7afd9` | Repository HEAD at review start |
| **Step 4A-Repair IMPLEMENTATION_HEAD** | `d86e513b8e9ddb647025f58534e81ddb9a8bcd05` | Feature implementation commit |
| **Step 4A-Repair CLOSEOUT_RECORD_HEAD** | `55404a1037249f1e3ff0addf9c8a578fc6c7afd9` | Closeout docs-only commit on top |

Do not use a single `Ending HEAD` to mean both implementation and closeout record.

---

## Executive question

**以当前真实证据，是否已经可以启动 N02 V5？**

**Answer: NO — `NOT_READY_FOR_N02_V5`**

N02 V4 proved E2E chain works but deliverable quality is below publish-review standard. Since Repair Steps 3A–4B, all registered gaps except **native subtitle readability on light backgrounds** have fixture-level or catalog-level closure. The remaining gap is a **real Production–proven P0** with **no VERIFIED automation fallback**.

---

## Readiness Matrix

| Gate | Current Truth | Evidence Level | V5 Blocker? | Production Validation Pending? |
|------|---------------|----------------|-------------|--------------------------------|
| **A. Continuous Execution** | Contract **VERIFIED** (Rules + L3 §12 + Cases A–E regression PASS). N02 V4 runtime behavior **FAILED** | Contract: static regression. Real: N02 V4 retrospective only | **NO** — V5 is the validation run; do not pre-build checkpointed runner | **YES** — real Cursor Production turn-chaining not re-tested since contract repair |
| **B. Music Asset Supply** | 4× Adobe Firefly WAV **READY**; catalog valid; license/provenance recorded | Catalog + ffprobe (Step 3B-2) | **NO** | **NO** |
| **C. Music Selection / Placement Chain** | `music.library.search` / `select` / `resolve` **VERIFIED**; `audio.music.place` **VERIFIED**; L3 Music Pass accepts `asset_id` | Fixture + catalog ranking (3B-2); placement from 04A-R2 | **NO** | **YES** — `asset_id` → Resolve import+place not re-run on N02 since catalog registration |
| **D. Voice–Music Mix** | `audio.voice_music_mix` / `audio.music.level_under_voice` **VERIFIED** (`ffmpeg_pre_attenuation`, continuous BGM, not ducking) | 04A-R2 spike + profile | **NO** | **YES** — full N02 mix pass with registered Firefly asset |
| **E. Final Loudness QA** | `audio.final.measure_loudness` / `audio.final.true_peak_qa` / `qa.audio` **VERIFIED**; `narration_short_v1` (-16 ±1 LUFS, TP ≤ -1 dBTP) | Disposable ebur128 fixtures (Step 4A) | **NO** | **YES** — N02 deliverable loudness gate not exercised on real render since profile |
| **F. Final Loudness Auto Repair** | `audio.final.normalize_or_adjust` / `FINAL_AUDIO_AUTO_REPAIR` **VERIFIED**; loudnorm two-pass; max 1 retry; fail-closed | Disposable QA→repair→re-QA loop (Step 4A-Repair, 40/40) | **NO** | **YES** — not yet run on real N02 artifact |
| **G. Pacing** | `qa.pacing.heuristic` / `qa.pacing.repair_candidate` **VERIFIED**; >6s warn, >10s cross-beat → repair candidate; `clip.source_range` + `clip.assemble` route | Fixture assembly plans (Step 4B) | **NO** — animated push-in/pan/ResolveFX explicitly **not** blockers | **YES** — N02 editorial loop not re-run with pacing gate |
| **H. Black-Bar Detection** | `qa.visual.black_bar_detect` / `final_render.black_bar_check` **VERIFIED** (cropdetect multiframe) | Disposable frames (Step 4B) | **NO** | **YES** — detector on N02 V5 render |
| **I. Reframe Repair Loop** | `qa.visual.reframe_static_repair` / `qa.visual.reframe_repair_loop` **VERIFIED** on fixtures; max 3 attempts; Owner-review path defined | Fixture loop only — **not** real Production loop | **NO** | **YES** — N02 V4 gap was gate/loop enforcement, not missing static reframe |
| **J. Subtitle Basic Rendering** | `native_drt_subtitles` / `subtitle.render.basic` / `subtitle.segment.semantic` **VERIFIED** | 08A.1 + R1 burn-in | **NO** | **NO** — placement works; issue is style not placement |
| **K. Subtitle Readability** | `subtitle.render.readability_stroke` **BLOCKED**; profile contract exists; UI outer stroke `AVAILABLE_MANUAL` only | **Real N02 V4 deliverable** + Step 2 disposable probe (white text, **no stroke** on burn-in) | **YES — P0** | **N/A** — blocker is missing capability, not pending validation |
| **L. Render** | `render.configure` / `render.start` / `render.status` / `render.verify` **VERIFIED** | 04A-R2 integrated render | **NO** | **NO** |
| **M. Final Artifact QA** | `qa.final_artifact` **VERIFIED**; `final-artifact-qa.ps1` embeds audio + black-bar sections | Fixture + integration tests | **NO** | **YES** — full gate stack on N02 V5 artifact |

---

## Gate summaries

### Gate A — Continuous Production Execution

| Layer | Status |
|-------|--------|
| Contract repair | **VERIFIED** — `video-workflow-core.mdc` §12, `production-entry-intake.mdc`, L3 Continuous Execution Contract, `production-continuous-execution.ps1` Cases A–E |
| N02 V4 real behavior | **FAILED** — Owner had to send `继续` multiple times |
| Re-validation | **VALIDATION_PENDING** — only achievable via next real Production |

**Judgment:** Do not implement checkpointed runner preemptively. N02 V5 is the correct validation vehicle. If V5 fails again for platform turn limits → escalate runner.

### Gate B — Shared Music Assets

- Root: `E:\03_Media\02_Video\Davinci\Astra\assets`
- 4 Firefly tracks READY with commercial provenance (Step 3B-2)
- Logical route complete: requirement → search → select → `asset_id` → absolute path

**Judgment:** `PRODUCTION_INTEGRATION_VALIDATION_PENDING` for Resolve placement only — **not a pre-V5 blocker**.

### Gate C — Final Audio

- Profile `narration_short_v1` established
- QA + loudnorm two-pass auto-repair closed on disposable artifacts (Step 4A / 4A-Repair)
- N02 V4 reference ≈ -24.8 LUFS (too low) — repair route now exists but unproven on N02 artifact

**Judgment:** Fixture closure sufficient; **do not build more Audio**. N02 V5 confirms production chain.

### Gate D — Pacing

- Heuristic + repair-candidate tooling VERIFIED on fixtures
- Repair route = source-range / assemble / static reframe — sufficient to address N02 V4 long-shot issue without animated camera moves

**Judgment:** Gate PASS for readiness; real effect validated in V5.

### Gate E — Black-bar / Reframe

- Fixture detect → static reframe → re-QA loop VERIFIED
- Truth preserved: fixture VERIFIED ≠ real Production loop VERIFIED

**Judgment:** Gate PASS for readiness; N02 V5 is production confirmation.

### Gate F — Subtitle Readability (重点)

**Real Production facts (N02 V4):**

- E2E PASS with native DRT white subtitles
- Deliverable **not** publish-review ready
- White native DRT text on **light backgrounds** has demonstrated readability risk
- Step 2 disposable burn-in probe: white glyphs **without** dark outer stroke

**Current automation truth:**

| Route | Status |
|-------|--------|
| `native_drt_subtitles` placement | **VERIFIED** |
| `subtitle.render.readability_stroke` | **BLOCKED** |
| DRT `subtitleStyle` / `subtitleTrackStyle` | ignored |
| Scripting API subtitle style R/W | none |
| Advanced MCP style | font + position only; stroke fields absent; host route incomplete |
| Resolve UI outer stroke | `AVAILABLE_MANUAL` |
| Text+ overlay | **not** upgraded — explicitly out of scope |

**Classification:** `P0_BLOCKER` for goal *自动产生达到发布审查条件的成片*.

There is **no VERIFIED fallback**. Manual UI stroke does not satisfy automated Production. Must not silently treat as optional enhancement.

**Owner decision exists:** accept known subtitle degradation **or** authorize Step 5 repair before V5.

---

## Prohibited scope (confirmed non-blockers)

Not V5 blockers per Owner directive:

- keyword emphasis, pixel-width parity, Text+ overlay, color/bold/italic emphasis
- kinetic typography, advanced transitions, ResolveFX/OFX
- animated pan / push-in, dynamic ducking, LUT workflow, shot matching

---

## `REMAINING_PRODUCTION_BLOCKERS`

```yaml
REMAINING_PRODUCTION_BLOCKERS:
  - id: P0_SUBTITLE_READABILITY_STROKE
    capability: subtitle.render.readability_stroke
    truth: BLOCKED
    evidence:
      - N02 V4 real deliverable — readability risk on light backgrounds with white unstyled native DRT
      - Step 2 disposable probe — burn-in survives but no outer stroke
      - No scripting/MCP/DRT automation route VERIFIED
    impact: Publish-review quality — subtitles may be unreadable on light/busy frames
    owner_decision_required: true
    accepted_degradation_alternative: Owner may explicitly accept V5 without stroke automation
    recommended_repair: Production Repair Step 5 — Minimal Native Subtitle Readability Unblock
```

**Count: 1 true blocker.**

All other gates marked `PRODUCTION_INTEGRATION_VALIDATION_PENDING` are **intentionally deferred to N02 V5** — not listed as blockers.

---

## Final Readiness Verdict

### `NOT_READY_FOR_N02_V5`

**Reason:** One real-Production-proven, publish-quality blocker remains — automated native subtitle outer stroke for light-background readability.

**Not** `READY_FOR_N02_V5_WITH_OWNER_ACCEPTED_DEGRADATION` unless Owner **first** explicitly accepts: *V5 may proceed knowing light-background subtitles can fail publish review with no automated fix.*

---

## Owner decision

| Decision | Required? |
|----------|-----------|
| Accept subtitle readability degradation for V5 | **YES** — only path to start V5 without Step 5 |
| Authorize Step 5 repair | **Recommended** — resolves P0 without accepting degradation |

Agent must **not** substitute Owner acceptance.

---

## Next唯一合法动作

**Production Repair Step 5 — Minimal Native Subtitle Readability Unblock**

Priority order (frozen):

1. Resolve UI: create standard outer-stroke style → export/harvest native `EffectFiltersBA` blob → map to existing track-style route
2. If (1) infeasible: minimal Advanced MCP style extension (stroke fields only)
3. If (1)(2) infeasible: return to Owner for degradation decision

**Do not:** jump to Text+ refactor, implement checkpointed runner, or add new Audio/Pacing/QA systems.

---

## Execution record (this round)

| Item | Value |
|------|-------|
| Runtime executed | **NO** |
| Production executed | **NO** |
| Implementation modified | **NO** |
| N02 V5 executed | **NO** |
| N02 touched | **NO** |

---

## Closeout record

| Label | SHA |
|-------|-----|
| **CLOSEOUT_RECORD_HEAD** | `5f0d6183c49e662942a4d7956e30439847680904` |

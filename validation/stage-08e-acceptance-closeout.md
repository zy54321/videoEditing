# Stage 08E — Owner Acceptance Closeout

**Date:** 2026-09-23  
**Baseline HEAD:** `30a6807`  
**Owner Acceptance reference:** 【确认验收】Stage 08E@2026-09-23  
**Prior evidence:** `validation/stage-08e-final-consolidated-closeout.md`

---

## Acceptance status

| Stage | Status |
|-------|--------|
| `STAGE_08E_A` | **ACCEPTED** |
| `STAGE_08E_B_FINAL_REVIEW` | **PASS_WITH_DEGRADATION** |
| `STAGE_08E_B` | **ACCEPTED_WITH_DEGRADATION** |
| `STAGE_08E` | **ACCEPTED** |

---

## Accepted scope

### Stage 08E-A — ACCEPTED

Deterministic subtitle layout contract, L1 preflight, styled runs, materializer semantics, font profile calibration (A1 / A1.1).

### Stage 08E-B — ACCEPTED_WITH_DEGRADATION

Text+ StyledTextCLS isolated route verified; production overlay partial; first Production uses native DRT fallback.

### Stage 08E — ACCEPTED

**Deterministic Subtitle & Typography Pipeline** accepted for first Production with explicit degradation (see below).

---

## Accepted production degradation

Owner explicitly accepts:

| Capability | Status |
|------------|--------|
| `subtitle.layout.pixel_width` | **AVAILABLE_UNVERIFIED** |
| `subtitle.style.keyword_emphasis` | **AVAILABLE_UNVERIFIED** |

**VERIFIED fallback for first Production:**

| Capability / Route | Status |
|--------------------|--------|
| `subtitle.segment.semantic` | **VERIFIED** |
| `subtitle.render.basic` | **VERIFIED** |
| `native_drt_subtitles` | **VERIFIED** |

---

## First Production subtitle baseline (FROZEN)

```
Native DRT subtitles
+ semantic segmentation
```

**Not required in first Production:**

- keyword emphasis
- pixel-width parity guarantee
- Text+ production overlay
- advanced subtitle styling
- color emphasis
- weight / italic
- kinetic typography
- animation

These items are **enhancement backlog only** — they must not block first Production.

---

## Text+ route truth (unchanged — no upgrade in this acceptance)

| Route / Capability | Truth |
|--------------------|-------|
| `textplus_styledtextcls_import_comp` | **VERIFIED (isolated)** |
| `textplus_nested_timeline_overlay` | **PARTIAL** |
| `subtitle.style.keyword_emphasis` | **AVAILABLE_UNVERIFIED** (production) |
| `subtitle.layout.pixel_width` | **AVAILABLE_UNVERIFIED** |

This acceptance record does **not** upgrade any of the above.

---

## Accepted product truth

- SIZE-only Text+ v1 contract (Regular, tracking = 0, stroke = 0)
- Exact validated font / px profiles only
- Production timing must be supplied by L3 / Production (`start_frame`, `duration_frames`)
- No production default `GlobalOut = 119`
- Plain / emphasized Text+ generator routes (product code; not first Production path)
- `fusion_comp.set_input(CharacterLevelStyling)` = **KNOWN_NON_WORKING_ROUTE**
- Generated `.setting` + `import_comp` = isolated route evidence (B-R1)
- Native DRT = first Production subtitle path

---

## Enhancement backlog (registered — not in scope)

1. Text+ production overlay final validation
2. Lower-safe-zone visual verification
3. Text+ integrated Deliver / reload
4. Keyword SIZE emphasis on production overlay
5. Pixel-width production parity
6. Color / weight / italic emphasis
7. Kinetic typography / animation

**Stage 08E is closed.** These items must not reopen Stage 08E.

---

## Post-acceptance boundary

After Stage 08E acceptance:

- **Stop** subtitle pipeline construction
- **Next direction:** Visual / Motion / existing Resolve capabilities

Principles for next stage:

- Prefer mature DaVinci-native capabilities: transitions, Resolve FX / OpenFX, LUT / Looks, presets, Fusion existing effects, basic motion / reframe / trim
- Do **not** prioritize re-implementing capabilities Resolve already provides
- Goal: minimal capability bundle for real Production, then real video production validation

---

## Audit

| Item | Value |
|------|-------|
| N02 touched | **NO** |
| Real Production executed | **NO** |
| Implementation modified in this acceptance | **NO** (documentation only) |

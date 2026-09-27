# Subtitle Rendering Capability Decision

## SELECTED_ROUTE

```yaml
SELECTED_ROUTE: external_ass_burnin
RUNTIME_ID: subtitle.runtime.external_ass
CAPABILITY: subtitle.render.readable_static
STATUS: CAPABILITY_VERIFIED_ON_FIXTURE
```

## WHY

1. **Production target met on fixture:** Bold **Microsoft YaHei UI**, white, black outline, semantic two-line wrap, margins **PASS** on final encoded slice (`validation/subtitle-route-fixture-results.json`).
2. **Chinese reliability:** Open Sans is **not** a valid primary font for this content; ASS names a real CJK font.
3. **Decoupling:** Semantic wrap stays in `subtitle-layout-engine` → ASS generator (next implementation); renderer swappable.
4. **Fail-closed:** No Project.db, no blob guessing; FFmpeg path reproducible on Astra Windows host.
5. **Preserves N02 gates:** Resolve → **clean master** (video+audio, subtitles not burned) → ASS burn-in → existing final QA + loudness chain.

## WHY NOT alternatives

| Route | Verdict | Reason |
|-------|---------|--------|
| A Native DRT direct | **REJECTED** for weight | No verified weight automation; stroke-only insufficient. |
| B DRT template replay | **PARTIAL backup** | Workable if Owner re-captures gold **YaHei Bold** blob; opaque, Resolve-coupled; keep for stroke parity experiments. |
| C Static Text+ | **REJECTED for N02** | Higher integration cost vs D for static-only; overlay route incomplete. |
| Project.db | **REJECTED** | Policy + missing verified Windows path + no stroke. |

## Production flow (next authorized round — not this commit)

```
subtitle cues (35) + layout intent
  → PRECHECK (subtitle-layout-preflight)
  → ASS build (timing from plan frames)
Resolve: N02 master render (ExportSubtitle: off / no burn-in)
  → external_ass_burnin
  → FINAL_ARTIFACT subtitle + geometry QA
  → loudness repair if needed
```

## Capability truth

| Field | Value |
|-------|-------|
| `SUBTITLE_RENDERING_CAPABILITY` | **VERIFIED_ON_FIXTURE** (not full N02 yet) |
| `READY_TO_APPLY_N02` | **NO** — awaits Owner review + next apply authorization |
| `CAPABILITY_GAP` | **FALSE** at product level; gap was **route selection**, not impossibility |

## Fixture evidence

| Item | Value |
|------|-------|
| Artifact | `validation/fixtures/subtitle-route/route_d_external_burnin.mp4` (~12.5s) |
| Font family | Microsoft YaHei UI |
| Font weight | Bold (ASS Bold=1) |
| Stroke | Outline 4px black |
| Geometry | PASS (wide_wrap @ 6s) |
| Timing | ASS dialogue times; aligned to slice offsets |

## Gap class (original blocker)

| Was | Now |
|-----|-----|
| CAPABILITY_GAP (Native weight only) | **WORKFLOW_GAP** — treated Native DRT as sole runtime for style |
| | **CAPABILITY_GAP** only for `resolve_native_font_weight` specifically |

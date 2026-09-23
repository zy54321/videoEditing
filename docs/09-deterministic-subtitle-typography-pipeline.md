# Deterministic Subtitle & Typography Pipeline (Stage 08E)

## Problem

Short-form captions need **pixel-width discipline** (target band + hard ceiling) while supporting **inline keyword emphasis** that changes measured width per run. Character-count heuristics and single-font-size assumptions cause silent overflow and false QA PASS.

N02 history: `subtitle.layout.pixel_width` → `subtitle.segment.semantic` with **high** degradation — semantic segmentation does not guarantee pixel width.

---

## Layer ownership

| Layer | Owns |
|-------|------|
| **L2 Style** | Width band (e.g. 76–78% target, 80% ceiling), max lines, semantic wrap rules, sparse emphasis policy |
| **L3 Blueprint** | `subtitle_typography_intent` — caption mode, emphasis targets (`text`, `semantic_role`, `intensity`) |
| **L1** | Styled runs, typography resolution, System.Drawing measurement, line layout, preflight QA |
| **L0 Runtime** | Resolve / Fusion / Text+ render — **parity requires 08E-B validation** |

**Frozen principle:** L2 decides emphasis semantics. L1 resolves concrete typography and layout. L0 renderer parity requires Runtime Validation.

---

## Artifacts (08E-A)

| Path | Role |
|------|------|
| `templates/subtitle-layout-request.json` | Request schema example |
| `templates/subtitle-layout-result.json` | Result schema example |
| `templates/subtitle-layout-reference.md` | L1 contract |
| `tools/subtitle-layout-preflight.ps1` | Deterministic preflight CLI |
| `tools/lib/subtitle-layout-engine.ps1` | Layout engine (dot-sourced) |

Blueprint additions: optional `subtitle_typography_intent` (backward compatible with `subtitle_graphics_intent` string).

---

## Styled runs

A cue = ordered `runs[]` with:

- `text`, `semantic_role`, `emphasis_level`, `break_after` (`prefer` | `allow` | `forbid`)

Typography resolution maps `emphasis_level` → size multiplier / weight / tracking at **L1 only**.

Composite line width = sum of per-run measurements (+ stroke / tracking allowances).

---

## Wrap & split

1. Break only at run boundaries honoring `break_after`
2. No indefinite font shrinking
3. No Frozen Script content mutation
4. `> hard ceiling` → overflow / wrap path
5. Cannot fit in `max_lines` → `CUE_SPLIT_REQUIRED` (L1 detect + evidence; L3 re-segments timing)

Width bands:

- `WITHIN_TARGET`
- `ABOVE_TARGET_WITHIN_CEILING` (warning — e.g. 79% when target 76–78%)
- `ABOVE_CEILING` (overflow)

---

## QA boundary

| Layer | Checks |
|-------|--------|
| Pre-render Layout Preflight | Measured width, lines, content preservation, split detection, font resolution |
| Timeline / Route QA | Planned vs actual route, timeline population |
| Post-render Artifact QA | Actual pixels in MP4 |

**Preflight PASS ≠ Final Artifact PASS**

---

## Capability truth (08E-A — unchanged status)

| Logical ID | Status |
|------------|--------|
| `subtitle.layout.pixel_width` | AVAILABLE_UNVERIFIED |
| `subtitle.style.keyword_emphasis` | UNKNOWN |
| `subtitle.segment.semantic` | VERIFIED (no pixel-width guarantee) |

Contract support ≠ Runtime VERIFIED.

---

## 08E-A vs 08E-B

| Stage | Scope |
|-------|-------|
| **08E-A** (this) | Contract, deterministic preflight tool, tests, documentation — **BUILD only** |
| **08E-B** (future) | Runtime Capability Validation — Resolve burn-in parity, styled render route, possible status upgrades |

---

## Route truth

Execution must record: requested capability → resolved → planned route → actual executed route → evidence. Silent drift (e.g. planned DRT subtitles vs executed `timeline_ai.create_subtitles`) is a defect.

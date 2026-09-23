# Stage 08E-A-R1 — Deterministic Layout Correctness Repair Closeout

| Field | Value |
|-------|-------|
| Stage | **08E-A-R1 — Owner Source Review Repair** |
| Parent | Stage 08E-A (NOT ACCEPTED at repair start) |
| Starting HEAD | `1c6a544` |
| VERSION | `0.1.1-dev` |
| Build policy | `BUILD_STAGE_NO_PRODUCTION` |
| Production actions executed | **NONE** |
| Resolve / MCP writes | **NONE** |
| Render | **NONE** |
| N02 Production | **NONE** |
| 08E-B | **NOT STARTED** |
| Stage 08D Acceptance | **PRESERVED** |

---

## Owner findings closed

| ID | Finding | Repair |
|----|---------|--------|
| R1-01 | Style ratios applied to safe area | Frame-width authority; `effective_ceiling_px = min(style_hard_ceiling_px, safe_area_width_px)`; result truth fields |
| R1-02 | Greedy prev-boundary wrap | `Resolve-SubtitleLineLayout` searches legal break subsets with deterministic scoring |
| R1-03 | Greedy counterexample regression | Synthetic width tests (A/B/C) + prefer-vs-allow priority test |
| R1-04 | Silent downgrade on invalid enums | Fail closed: `EMPHASIS_LEVEL_UNSUPPORTED`, `BREAK_POLICY_UNSUPPORTED`, `FONT_STYLE_UNSUPPORTED` |
| R1-05 | Dual `font_style` authority | Removed `typography.font_style`; `emphasis_style_mapping.normal.font_style` is base authority |
| R1-06 | Missing request validation | `Validate-SubtitleLayoutRequest` fail-closed for canvas, margins, ratios, cues, runs, font style availability |
| R1-07 | Inconsistent result example | `subtitle-layout-result.json` self-consistent (`line_count == lines.length`, frame/safe-area truth) |
| R1-08 | Weak split evidence | `split_candidates[]` (prefer/allow only); `NO_LEGAL_INTERNAL_BREAK` for atomic oversized runs |
| R1-09 | Measurement honesty | `measurement_limitations` + `MEASUREMENT_CONSERVATIVE_BOUND` warning; capability status unchanged |
| R1-10 | Regression tests | `subtitle-layout-contract.ps1` extended (49 assertions, 0 failures) |
| R1-11 | Full regression | All Stage 08D/08E gate scripts PASS (see below) |
| R1-12 | Closeout | This document |

---

## Capability states (unchanged)

| ID | Before R1 | After R1 |
|----|-----------|----------|
| `subtitle.layout.pixel_width` | AVAILABLE_UNVERIFIED | AVAILABLE_UNVERIFIED |
| `subtitle.style.keyword_emphasis` | UNKNOWN | UNKNOWN |
| `subtitle.segment.semantic` | VERIFIED | VERIFIED |

Observational Style frame-width authority (76–78% target / 80% ceiling) **not modified**.

---

## Test results

### Subtitle layout contract

```
subtitle-layout-contract.ps1 — 49 passed, 0 failed
```

Includes original T01–T20 plus R1-01–R1-10 coverage (frame authority, counterexample, fail-closed, split evidence, capability guard).

### Full regression (R1-11)

| Script | Result |
|--------|--------|
| `style-skill-contract.ps1` | PASS (90) |
| `capability-resolution-consistency.ps1` | PASS (17) |
| `verify-capability-coverage.ps1` | PASS |
| `validate-style-reference-capability-consistency.ps1` | PASS |
| `editing-craft-architecture.ps1` | PASS (35) |
| `observational-style-consistency.ps1` | PASS (37) |
| `pre-release-consistency.ps1` | PASS (25) |
| `installer-smoke.ps1` | PASS (32) |

**Note:** `validate-style-profile.ps1` and `validate-capability-fallbacks.ps1` are path-parameter helper CLIs invoked from `style-skill-contract.ps1` (S34/S34b/S34c) and `verify-capability-coverage.ps1` — not standalone entrypoints.

---

## Status flags

```
STAGE_08E_A_R1_IMPLEMENTATION = COMPLETE
STAGE_08E_A_R1_REGRESSION = PASS
STAGE_08E_A = READY_FOR_OWNER_REVIEW
```

**Not declared:** `STAGE_08E_A = ACCEPTED`, `STAGE_08E = ACCEPTED`, 08E-B entry, v0.1.1 Release.

---

## Remaining gaps (explicit)

- Resolve / Fusion / Text+ renderer parity (`subtitle.layout.pixel_width` → VERIFIED) — **08E-B**
- Styled keyword emphasis render route (`subtitle.style.keyword_emphasis`) — **08E-B**
- Per-run stroke/padding conservative bound vs composite visual bounds — documented limitation

# Stage 08E-A-R2 — Prefer Boundary / Target-Band Selection Repair Closeout

| Field | Value |
|-------|-------|
| Stage | **08E-A-R2 — Layout candidate ranking repair** |
| Parent | Stage 08E-A (Formal Acceptance = HOLD at R2 start) |
| Starting HEAD | `b443a65` |
| VERSION | `0.1.1-dev` |
| Build policy | `BUILD_STAGE_NO_PRODUCTION` |
| Production actions executed | **NONE** |
| Resolve / MCP writes | **NONE** |
| 08E-B | **NOT STARTED** |
| Stage 08D Acceptance | **PRESERVED** |

---

## Problem closed

Formal Review blocker: candidate ranking prioritized `line_count` before target-band fit and `prefer` boundary satisfaction, causing single-line layouts to win when a legal prefer split would place all lines within the Style target band.

---

## Ranking algorithm

### Before (R1)

```
line_count ↑
→ prefer_breaks ↓
→ allow_breaks ↑
→ imbalance ↑
→ break-index tie-break
```

### After (R2)

```
target_tier ↑          (0 = all lines ≤ style target; 1 = some above target, all ≤ ceiling)
→ lines_above_target ↑
→ imbalance ↑          (closer to target width intent)
→ prefer_breaks ↓
→ allow_breaks ↑
→ line_count ↑         (tie-break only — not “fewer is always better”)
→ break-index tie-break
```

`line_count ≤ max_lines` remains a **legality** constraint only.

New layout evidence fields: `selected_break_indices`, `selected_break_policies`.

---

## Regression cases added

| ID | Behavior |
|----|----------|
| R2-03 | 1-line above target (85) vs 2-line prefer split within target (45+40) → choose split |
| R2-04 | 1-line within target (70) with prefer boundary available → keep 1 line |
| R2-05 | prefer beats allow at equal tier |
| R2-06 | deterministic deep structural compare (preflight cue) |
| R2-07 | `FONT_STYLE_UNSUPPORTED` fail-closed |
| R2-07b | `FONT_STYLE_UNAVAILABLE` when host has Regular-only font (skip if none) |

All R1 tests retained.

---

## Capability states (unchanged)

| ID | Before R2 | After R2 |
|----|-----------|----------|
| `subtitle.layout.pixel_width` | AVAILABLE_UNVERIFIED | AVAILABLE_UNVERIFIED |
| `subtitle.style.keyword_emphasis` | UNKNOWN | UNKNOWN |
| `subtitle.segment.semantic` | VERIFIED | VERIFIED |

---

## Test results

```
subtitle-layout-contract.ps1 — 63 passed, 0 failed (1 host-conditional skip)
```

Full regression: style-skill, capability-resolution, verify-coverage, validate-style-reference-capability-consistency, editing-craft-architecture, observational-style-consistency, pre-release-consistency, installer-smoke — **ALL PASS**.

---

## Status flags

```
STAGE_08E_A_R2_IMPLEMENTATION = COMPLETE
STAGE_08E_A_R2_REGRESSION = PASS
STAGE_08E_A = READY_FOR_OWNER_REVIEW
```

**Not declared:** `STAGE_08E_A = ACCEPTED`, `STAGE_08E = ACCEPTED`, 08E-B entry.

---

## Remaining gaps

- Resolve renderer parity (08E-B)
- `subtitle.style.keyword_emphasis` render route validation (08E-B)

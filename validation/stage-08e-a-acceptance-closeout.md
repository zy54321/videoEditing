# Stage 08E-A — Acceptance & Closeout Receipt

## Receipt

| Field | Value |
|-------|-------|
| Stage | **08E-A — Subtitle Typography Contract + Deterministic Layout Foundation** |
| Parent | Stage 08E — Deterministic Subtitle & Typography Pipeline Closure |
| Owner decision | **ACCEPTED** |
| Acceptance date | **2026-09-23** |
| Acceptance baseline HEAD | `63b441f` |
| VERSION | `0.1.1-dev` |
| Production actions executed | **NONE** |
| N02 status | **UNCHANGED** |
| Stage 08D Acceptance | **PRESERVED** (`35bd046`) |

---

## Construction Chain

| Sub-stage | HEAD | Summary |
|-----------|------|---------|
| 08E-A (initial) | `1c6a544` | Contract, preflight tool, layout engine, docs/09 |
| 08E-A-R1 | `b443a65` | Frame-width authority, search-based line layout, fail-closed validation, split evidence |
| 08E-A-R2 | `63b441f` | Target-band / prefer-boundary candidate ranking repair |

---

## Established Artifacts

| Flag | Status |
|------|--------|
| `SUBTITLE_LAYOUT_REQUEST_CONTRACT` | **ESTABLISHED** |
| `SUBTITLE_LAYOUT_RESULT_CONTRACT` | **ESTABLISHED** |
| `SUBTITLE_LAYOUT_REFERENCE` | **ESTABLISHED** |
| `SUBTITLE_LAYOUT_PREFLIGHT_TOOL` | **ESTABLISHED** |
| `SUBTITLE_LAYOUT_ENGINE` | **ESTABLISHED** |
| `BLUEPRINT_SUBTITLE_TYPOGRAPHY_INTENT` | **ESTABLISHED** |
| `DOCS_09_SUBTITLE_PIPELINE` | **ESTABLISHED** |
| `SUBTITLE_LAYOUT_CONTRACT_TESTS` | **ESTABLISHED** (63 assertions at acceptance) |
| `BUILD_STAGE_NO_PRODUCTION` | **PRESERVED** |

---

## Owner-Confirmed Properties

- **Frame width authority:** Style target / hard ceiling ratios use **frame width** as denominator; `effective_ceiling_px = min(style_hard_ceiling_px, safe_area_width_px)`.
- **Line layout:** `Resolve-SubtitleLineLayout` searches legal break subsets (not greedy-only); deterministic scoring with target-band tiers.
- **Prefer semantics:** `prefer` is a semantic preference — not a mandatory break; single line within target is not forced to split.
- **Fail-closed validation:** Unknown `emphasis_level`, `break_after`, unsupported `font_style` → explicit errors; no silent downgrade.
- **Typography authority:** `emphasis_style_mapping.normal.font_style` is the sole base style authority (no duplicate `typography.font_style`).
- **Split evidence:** `split_candidates[]` (prefer/allow only); `NO_LEGAL_INTERNAL_BREAK` for atomic oversized runs.
- **Measurement honesty:** System.Drawing per-run measurement; conservative bound documented; preflight PASS ≠ Resolve renderer parity.
- **Observational Style frozen:** 76–78% target / 80% ceiling frame-width authority **unchanged**.
- **L2 / L3 / L1 ownership boundary** preserved per docs/09.

---

## Capability Truth at Acceptance (unchanged)

| Logical ID | Status | Note |
|------------|--------|------|
| `subtitle.layout.pixel_width` | AVAILABLE_UNVERIFIED | Contract + preflight exist; Resolve parity **not** validated |
| `subtitle.style.keyword_emphasis` | UNKNOWN | Styled-run contract exists; render route **not** validated |
| `subtitle.segment.semantic` | VERIFIED | No pixel-width guarantee |

Acceptance does **not** upgrade any capability state.

---

## Regression Snapshot (acceptance baseline `63b441f`)

| Script | Result |
|--------|--------|
| `subtitle-layout-contract.ps1` | 63 passed, 0 failed |
| `style-skill-contract.ps1` | 90 passed |
| `capability-resolution-consistency.ps1` | 17 passed |
| `verify-capability-coverage.ps1` | PASS |
| `validate-style-reference-capability-consistency.ps1` | PASS |
| `editing-craft-architecture.ps1` | 35 passed |
| `observational-style-consistency.ps1` | 37 passed |
| `pre-release-consistency.ps1` | 25 passed |
| `installer-smoke.ps1` | 32 passed |

---

## Explicit Non-Actions (Acceptance)

This acceptance does **not**:

- Enter Production or N02 execution
- Execute Resolve / MCP writes or Render
- Start **08E-B** Runtime Capability Validation
- Publish v0.1.1 Release
- Declare `STAGE_08E = ACCEPTED` (parent stage includes 08E-B)
- Upgrade `subtitle.layout.pixel_width` or `subtitle.style.keyword_emphasis` capability status

**08E-B remains Owner decision only.**

---

## Legal Next Actions (Owner Authority)

| Action | Gate / prerequisite |
|--------|---------------------|
| **08E-B Runtime Validation** | Owner authorizes spike for Resolve burn-in parity, styled render route |
| **N02 V2 Production run** | Owner authorizes `【制作视频】` in bound workspace |
| **v0.1.1 Release build** | Owner authorizes release stage |
| **No action** | Valid — Stage 08E-A closed at `63b441f` until Owner directs |

---

## Sign-Off

```
STAGE_08E_A = ACCEPTED
STAGE_08E_A_CLOSEOUT = COMPLETE
OWNER_ACCEPTANCE_08E_A = RECORDED
```

*This receipt records Owner acceptance of the **08E-A build foundation** (contract + deterministic preflight). It does not constitute Resolve renderer parity acceptance, N02 Final Acceptance, or `STAGE_08E` parent-stage acceptance.*

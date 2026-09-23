# Stage 08E-B B-R3 — Product Truth Closeout

**Date:** 2026-09-23  
**Baseline HEAD:** `f081724`

---

## Status

| Gate | Status |
|------|--------|
| `STAGE_08E_B_R3` | **COMPLETE** |
| `STAGE_08E_B` | **READY_FOR_FINAL_REVIEW** |

---

## R3-01 — Exact font profile truth

`resolve_font_profile()` now requires:

- `typography.font_family` (or fallback) matches profile
- `typography.base_font_size_px` **exactly equals** `profile.l1_base_font_size_px`

Validated pairs only:

| Font | L1 px | Text+ size |
|------|-------|------------|
| Microsoft YaHei | 48 | 0.073 |
| Arial | 48 | 0.064 |

Unvalidated size → `TEXTPLUS_FONT_SIZE_PROFILE_NOT_VALIDATED` (fail-closed). No scaling, interpolation, or silent defaults.

---

## R3-02 — Production request authority

Production CLI (`generate-textplus-cls-setting.py`) accepts **only**:

```
materialized_cue + typography
```

Missing `materialized_cue` → `MATERIALIZED_CUE_REQUIRED`.

`generate_from_legacy_test_request()` retained as **TEST_ONLY / VALIDATION_ONLY** for B10–B12 static replay. Production CLI does not call it.

---

## R3-03 — Graph authority

| Role | Authority |
|------|-----------|
| Executable graph | `textplus_cls_setting.generate_setting()` |
| Golden fixture | `textplus-cls-canonical.setting` — structural topology reference, **not** runtime dependency |

Consistency tests verify topology markers (StyledTextCLS → TextPlus → MediaOut1, SourceOp wiring, TEMPLATE_ID) without byte-equal comparison.

---

## VERIFIED scope (`subtitle.style.keyword_emphasis`)

**VERIFIED:**

- static inline SIZE
- validated Text+ font profiles
- validated L1 `base_font_size_px`
- Resolve Text+ / StyledTextCLS
- generated `.setting` + `import_comp`

**NOT VERIFIED:**

- arbitrary font size
- color, weight, animation, kinetic typography

---

## Unchanged

- Experiment B / B-R1 / B-R2 runtime evidence
- `fusion_comp.set_input(CharacterLevelStyling)` = KNOWN_NON_WORKING_ROUTE
- `subtitle.layout.pixel_width` = AVAILABLE_UNVERIFIED
- No N02 / Production / v0.1.1 release

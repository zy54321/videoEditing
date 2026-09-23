# Stage 08E-B — Keyword Emphasis Productization Closeout (B-R2)

**Date:** 2026-09-23  
**Baseline HEAD:** `c6cc3ab`  
**Scope:** Promote validated Text+ StyledTextCLS backend from validation tree to `source/payload/`

---

## Status summary

| Gate | Status |
|------|--------|
| `EXPERIMENT_B` | **PASS** (`INLINE_KEYWORD_EMPHASIS_PASS`, B10–B12) |
| `KEYWORD_EMPHASIS_RUNTIME_ROUTE` | **VERIFIED** |
| `KEYWORD_EMPHASIS_PRODUCT_INTEGRATION` | **COMPLETE** |
| `subtitle.style.keyword_emphasis` | **VERIFIED** (static inline SIZE only) |
| `subtitle.layout.pixel_width` | **AVAILABLE_UNVERIFIED** (unchanged this round) |
| `STAGE_08E_B` | **READY_FOR_FINAL_REVIEW** |

**Not declared:** `STAGE_08E_B = ACCEPTED`, `STAGE_08E = ACCEPTED`, N02 production, v0.1.1 release.

---

## Runtime route verification (Experiment B / B-R1)

Validated chain:

```
Resolve Text+
→ StyledTextCLS
→ dynamically generated .setting
→ timeline_item_fusion.import_comp
→ timeline_frame
→ Deliver
→ save/reload
```

Evidence: `validation/08e-b-exp-b/evidence/br1-outcome.json`, B10–B12 deliver-range checks, GUI gold standard `B00-gui-cls-working.setting`.

**Known non-working route (DO NOT USE IN PRODUCTION):**

```
fusion_comp.set_input(CharacterLevelStyling)
```

Environment: Resolve Studio 21.1.0.14, Samuel MCP 4.8.13.

---

## Product integration verification (B-R2)

Promoted artifacts (installed via `init-video-workflow.ps1`):

| Path | Role |
|------|------|
| `video-workflow/tools/generate-textplus-cls-setting.py` | CLI entry |
| `video-workflow/tools/lib/textplus_cls_setting.py` | CLS generator (v1 SIZE only) |
| `video-workflow/runtime/textplus-cls-canonical.setting` | Canonical Resolve-native graph template |

**Authority chain (production):**

```
L2 semantic emphasis
→ L1 styled runs
→ subtitle layout preflight
→ textplus-layout-materializer
→ materialized cue lines[].runs
→ CLS setting generator
→ import_comp
```

Validation helpers under `validation/08e-b-exp-b/` remain evidence only — not production dependencies.

---

## Verified scope (v1)

- Static inline **SIZE** emphasis via StyledTextCLS parameter 102
- Unicode index = Python codepoint semantics on final `styled_text`
- Font base size from `textplus-font-profiles.yaml` (no hardcoded YaHei/Arial constants in generator)

**Not verified / not in v1:**

- color (fail-closed: `CLS_COLOR_NOT_VERIFIED`)
- weight (fail-closed: `CLS_WEIGHT_NOT_VERIFIED`)
- animation / kinetic typography

---

## Test coverage

Static: `source/tests/textplus-cls-setting.ps1` (+ `textplus_cls_setting_tests.py`)

Runtime evidence: B10, B11, B12 (Experiment B-R1)

---

## Historical notes retained

- Experiment B PARTIAL history (early `set_input` failures)
- GUI gold standard export format
- B-R1 dynamic template PASS

# Stage 08E-B Experiment B — Inline Keyword Emphasis

| Field | Value |
|-------|-------|
| Date | 2026-09-23 |
| Starting HEAD | `f611548` |
| B-R1 HEAD | see `evidence/br1-outcome.json` |
| Project | `Astra-08E-B-Subtitle-Validation` |

```
EXPERIMENT_B_OUTCOME = INLINE_KEYWORD_EMPHASIS_PASS
```

---

## Canonical Truth

| Route | Status |
|-------|--------|
| Resolve GUI + StyledTextCLS | **PASS** |
| MCP `fusion_comp.set_input(CharacterLevelStyling)` | **KNOWN_NON_WORKING_ROUTE** — do not use |
| MCP dynamic `.setting` + `import_comp` | **PASS** — v1 production backend |

---

## v1 Production Backend

```
JSON request (cases/B10.request.json)
  → helpers/generate_cls_setting.py
  → generated/*.setting
  → timeline_item_fusion.import_comp
  → export_comp / timeline_frame / Deliver
```

Canonical template: `templates/textplus-cls-canonical.setting`

Graph:

```
CharacterLevelStyling1 (StyledTextCLS) → Template (TextPlus) → MediaOut1
```

---

## B-R1 Dynamic Validation (B10–B12) — PASS

| Case | Text | Spans | Export | Frame | Deliver | Width | 80% ceiling |
|------|------|-------|--------|-------|---------|-------|-------------|
| B10 | `价格上涨了 40%` | `40%` strong | PASS | PASS | PASS | 388px | ✓ |
| B11 | `AI 让效率提升了 35%` | `AI` medium, `35%` strong | PASS | PASS | PASS | 506px | ✓ |
| B12 | `今年增长 18%，成本下降 7%` | `18%`, `7%` strong | PASS | PASS | PASS | 692px | ✓ |

- **Unicode index:** Python codepoint (verified; not UTF-16)
- **Deterministic generation:** B10 byte-identical across 2 runs
- **Reload:** B10 CLS Array survives save/close/load
- **Color / weight:** NOT_RUN (out of scope for PASS)

Full evidence: `evidence/br1-outcome.json`

---

## Direct SetInput — Final

```
KNOWN_NON_WORKING_ROUTE
Samuel MCP 4.8.13 / Resolve 21.1.0.14
```

Research backlog: `research/backlog/mcp-cls-automation-research.md`

---

## Capability Recommendation

| ID | Status | Scope |
|----|--------|-------|
| `subtitle.style.keyword_emphasis` | **VERIFIED** | Static inline **size** emphasis via Text+ / StyledTextCLS template backend |
| color / weight / animation | **NOT VERIFIED** | — |

---

## Artifacts

```
validation/08e-b-exp-b/
├── experiment-b-inline-keyword-emphasis.md
├── templates/textplus-cls-canonical.setting
├── helpers/generate_cls_setting.py
├── helpers/parse_cls_export.py
├── helpers/deliver_range_check.py
├── cases/B10|B11|B12.request.json
├── generated/B10|B11|B12.generated.setting
├── evidence/br1-outcome.json
├── evidence/b-outcome.json
├── evidence/B10|B11|B12-export.setting
├── tests/test_generate_cls_setting.py
└── renders/.gitignore
```

---

## Flags

```
N02_TOUCHED = NO
PRODUCTION_EXECUTED = NO
```

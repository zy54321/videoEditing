# Stage 08E-B Experiment A1.1 — Text+ Layout Materialization

| Field | Value |
|-------|-------|
| Stage | **08E-B — Runtime Typography Capability Validation** |
| Experiment | **A1.1 — L1 Layout → Text+ Materialization** |
| Starting HEAD | `55797439e8f114efa20185c23e7e29200117a598` |
| Ending HEAD | *(uncommitted)* |
| Parent | Experiment A1 (`PARTIAL`) |
| Disposable Project | `Astra-08E-B-Subtitle-Validation` |
| Timeline | `A1-EXP-A` |
| Text+ clip | `ea145b87-f280-47ea-b959-5a9ec29e775e` |
| N02 touched | **NO** |
| Experiment B | **NOT EXECUTED** |
| A2 | **NOT EXECUTED** |

---

## A1.1 Outcome

```
A1.1_OUTCOME = LAYOUT_MATERIALIZATION_PASS
```

Authority chain closed:

```
L1 subtitle-layout result  →  materializer  →  Text+ StyledText  →  rendered frame
```

Text+ no longer self-wraps or self-splits. L1 `lines[]`, `split_candidates`, and newline boundaries are the layout authority.

---

## Implementation

| Component | Path |
|-----------|------|
| Materializer | `source/payload/video-workflow/tools/lib/textplus-layout-materializer.ps1` |
| Font profiles | `source/payload/video-workflow/runtime/textplus-font-profiles.yaml` |
| Plan runner | `validation/08e-b-exp-a/run-a1-1-materialization.ps1` |
| Focused tests | `source/tests/textplus-layout-materializer.ps1` |
| Outcome summary | `validation/08e-b-exp-a/evidence/a1-1-outcome.json` |

Runtime route (reused, no new renderer):

- `fusion_comp.safe_set_inputs` on Fusion `Template` (Text+)
- `gallery_stills.grab_and_export` for rendered-frame capture
- `measure_subtitle_width.py` / `measure_multiline_width.py`

### Font profiles (validated only)

| Profile | L1 base px | Text+ Size | Style |
|---------|------------|------------|-------|
| Microsoft YaHei UI | 48 | 0.073 | Regular |
| Arial | 48 | 0.064 | Regular |

---

## Case Results

### A11 — Materialization Smoke — **PASS**

| Check | Result |
|-------|--------|
| L1 `line_count` | 2 |
| `selected_break_indices` | `[0]` |
| Materialized `StyledText` newline @ 10 | ✓ |
| Text+ readback newline | ✓ |
| Rendered lines detected | 2 |
| Geometry parity | 484→493, 484→494 (±3%) |

### A07 / A08 / A09 — Original (atomic overflow)

| Case | L1 status | Materialization | Classification |
|------|-----------|-----------------|----------------|
| A07 | `CUE_SPLIT_REQUIRED` + `NO_LEGAL_INTERNAL_BREAK` | `BLOCKED_NO_LEGAL_INTERNAL_BREAK` | `PRE_MATERIALIZATION_FAILURE` |
| A08 | same | same | same |
| A09 | same | same | same |

Ultra-wide atomic Text+ **not rendered**. Prior A1 overflow parity comparisons invalidated.

### A07 / A08 / A09 — Splittable validation

Recursive split → per-part L1 preflight → materialized cues (5 parts each).

Representative rendered captures (first single-line part + final two-line part):

| Part | Predicted | Actual | Pass |
|------|-----------|--------|------|
| A07-A | 724 | 741 | ✓ (2.3%) |
| A07-B-B-B-B L1 | 724 / 244 | 741 / 244 | ✓ |
| A08-A | 724 | 742 | ✓ |
| A08-B-B-B-B | 724 / 244 | 742 / 246 | ✓ |
| A09-A | 724 | 742 | ✓ |
| A09-B-B-B-B | 724 / 244 | 742 / 246 | ✓ |

Middle parts share identical 15-char chunk geometry with first part.

Timing: `deterministic_equal_split_validation_only` — **not** production subtitle timing authority.

### A10 — Same semantic text, L1 line authority — **PASS**

| L1 | Materialization |
|----|-----------------|
| `line_count = 1` | No `\n` in StyledText |
| Concatenated runs | `第一行字幕内容第二行继续说明` |
| Predicted width | 680 px |
| Actual width | 691 px (1.6%) |

---

## Regression

| Suite | Result |
|-------|--------|
| `source/tests/textplus-layout-materializer.ps1` | 6/6 PASS |
| `source/tests/subtitle-layout-contract.ps1` | 66 passed, 0 failed |

08E-A layout algorithm unchanged.

---

## Consolidated A1 Conclusion (post A1.1)

| Category | Cases | Notes |
|----------|-------|-------|
| **A — Same-layout geometry** | A01–A06, A10, A11 | YaHei @ 0.073 |
| **B — Materialized wrap/split** | A07–A09 splittable | Split + newline materialization |
| **C — Invalid historical** | A07–A09 pre-A1.1 | Atomic overflow rendered as 1080px |

```
TEXTPLUS_GEOMETRY_PARITY = SUPPORTED_FOR_VALIDATED_PROFILE
```

Scoped to: validated font profiles, validated font size, Text+ R1 route, rendered-frame measurement authority.

---

## Capability Recommendation (unchanged)

| Capability | Status |
|------------|--------|
| `subtitle.layout.pixel_width` | **AVAILABLE_UNVERIFIED** |
| `subtitle.style.keyword_emphasis` | **UNKNOWN** |

A2 Deliver Survivability remains open — not executed this stage.

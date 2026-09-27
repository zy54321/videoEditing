# N02 Assembly QA — Repair R1 Re-evaluation

**Source:** `validation/n02-v1-timeline-assembly.json` (no new render)  
**Machine report:** `validation/n02-assembly-qa-r1-metrics.json`

## Micro-fragments (FACT)

| Shot ID | ~duration @ 24fps |
|---------|-------------------|
| V1-01, V1-07, V1-12, V1-15, V1-19, V1-22 | **6** items ≈ 0.042s (≤2 frames) |

## Logical spans

- **Raw shots:** 25  
- **Logical source spans (reuse QA):** **16** (adjacent same-source trims collapsed)

## Corrected reuse metrics (before repair)

| Metric | Count |
|--------|------:|
| Cooldown violations (logical spans) | **6** |
| 30s window violations | **1** (plaza `8caf2f07…`) |
| Ping-pong A-B-A | **3** |
| Ping-pong A-B-A-B | **1** |

Adjacent plaza micro-tail **no longer** false-trigger cooldown vs previous item.

## Repair plan (one pass, no unapproved alternates)

| Outcome | Value |
|---------|-------|
| Safe actions | **6** micro-fragment timeline absorbs |
| Blocked | **5** ping-pong (no `alternate_source_assets`) |
| Status | **`ASSEMBLY_REPAIR_NOT_CONVERGED`** |
| After reuse | still **STRONG_REPAIR_CANDIDATE** |
| After pacing | still not PASS (long office span + remaining issues) |

## Unresolved (expected)

- Ping-pong / cooldown / window: need **approved alternates** or upstream re-assembly — not arbitrary pool swaps.  
- Office ~11.7s span: **REPAIR_CANDIDATE** without approved alternate — no plaza substitution.

## Audio (unchanged this round)

`FINAL_AUDIO_REPAIR_PRODUCTION = PASS` (-16.1 LUFS, -1.4 dBTP, 48 kHz) — not modified in R1.

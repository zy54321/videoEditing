# N02 V1 Production Review

**Artifact:** `E:\03_Media\02_Video\Davinci\Astra\2026-09-21\output\N02_V1.mp4`  
**Resolve:** `N02-20260927` / timeline `N02-V1-Captioned-wrap2`  
**Status:** READY_FOR_OWNER_REVIEW — **not** Production PASS

---

## Audio failure (FACT)

| Metric | Measured (encoded MP4) | Target |
|--------|------------------------|--------|
| Integrated LUFS | **-24.5** | -16 ±1 (-17..-15) |
| True Peak | **-5.7 dBTP** | ≤ -1.0 dBTP |
| Sample rate | 48000 Hz | 48000 Hz |
| Channels | 2 | 2 |

**Root cause:** Deliverable left Resolve at narration bed level; post-render loudnorm repair either did not run on promote path or prior repair hit **-16.1 LUFS / -0.7 dBTP at 96000 Hz** and was correctly **not promoted** (authority must be encoded artifact; 96 kHz violated output contract).

---

## Repeated visual sequences

### FACT — same `source_asset` (media pool ID)

| Time (approx) | Pattern | Assets (pool ID → filename hint) |
|---------------|---------|----------------------------------|
| 0.0–18.8 | A→B→A→B | `8caf2f07…` plaza ↔ `bb019a05…` supermarket |
| 51.3–75.9 | A→B→A→B→A | `8caf2f07…` plaza ↔ `d4db87c8…` mountain village |

Trace: `validation/n02-v1-timeline-assembly.json` (25 V1 video items from Resolve probe).

### INFERENCE

Different filenames may still look like the “same scene” to a viewer; this review does **not** treat that as fact without visual CV. **`VISUAL_SCENE_REUSE_GAP`** not expanded in this bundle.

---

## Pacing issue (FACT)

| Window | Observation | Evidence |
|--------|-------------|----------|
| ~28.8–40.4 s | Office俯拍 ~**11.67 s** continuous | Items 8–10, same `source_asset` `78389944…` (`Open office space [open-office-space-914].mp4`), frames 87090–87370 |

**Why production did not repair:** `pacing-qa.py` only flagged **unchanged `source_range`** across semantic beats; office clips used **adjacent trims** (different `source_range`) and per-clip duration &lt; 10 s → no `PACING_REPAIR_CANDIDATE`. No `assembly-qa-repair-loop` in the N02 V1 render path.

---

## Shot reuse metrics (assembly QA on V1 export)

| Metric | Count |
|--------|------:|
| Ping-pong A-B-A | **3** |
| Ping-pong A-B-A-B | **1** |
| Ping-pong A-B-A-B-A | 0 |
| Same-source 12 s cooldown violations | multiple (plaza) |

---

## Repair decisions (this bundle)

1. **Audio:** `repair_target_dbtp = -1.5`, `encoder_safety_margin_dbtp = 0.5`, force AAC **48 kHz**; verdict on **encoded** MP4 only; max **1** repair.
2. **Pacing:** add `same_source_asset_span` rule + assembly repair (alternate middle shot / `source_range`).
3. **Reuse:** `shot-reuse-qa.py` + `assembly-qa-repair-loop.py` (plan-level); Resolve `overwrite_range` apply attempted — **blocked** on source trim resolution for one swap (timeline apply remains partial).

---

## `PRODUCTION_CONTINUOUS_EXECUTION`

**Not verified for N02 V1 → V1 render in this workspace.** Prior N02 V4 evidence remains **FAILED** (`validation/first-real-production-review-n02-v4.md`). This review does not upgrade without a full transcript audit of the N02 V1 production chat.

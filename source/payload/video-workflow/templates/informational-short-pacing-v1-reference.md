# informational_short_pacing_v1 — Pacing & Black-Bar QA Reference (Step 4B)

## N02 V4 — Why black bars leaked despite VERIFIED capability

| Layer | What happened |
|-------|----------------|
| **Detector** | `final-artifact-qa.ps1` edge heuristic was **executable** — capability marked VERIFIED for pipeline existence |
| **Coverage gap** | Only **3** sampled frames; **≥2** suspects needed for `SUSPECT_BLACK_BARS`; single-frame hits → `AUTOMATED_SCREEN + VISUAL_CONFIRM` only |
| **Per-edge gap** | Legacy heuristic merged all edges — weak on **pillarbox** and partial reframes |
| **Loop gap** | No mandatory **pre-render** frame QA after `visual.reframe.static` |
| **Gate gap** | Post-render QA **not enforced** as Production hard-fail in N02 V4 continuous execution |
| **Repair gap** | No **detect → reframe → re-QA** contract; reframe could run once without recheck |
| **Pacing gap (N02 V1)** | Per-shot duration &lt; 10s while **same `source_asset` span** ~11.7s; legacy rule required identical `source_range` + semantic beats → no `PACING_REPAIR_CANDIDATE` on timeline export |

**Root cause (primary):** QA **detector VERIFIED ≠ Production closure VERIFIED**. Detection existed but was neither sufficiently sensitive nor wired into a fail-closed repair loop.

**N02 V1 pacing root cause:** `pacing-qa.py` did not treat consecutive **same `source_asset`** trims as one visual span; assembly export used per-clip `beat_id` so cross-beat unchanged-span rule never fired. **Closure (V2 bundle):** `same_source_asset_span` + `assembly-qa-repair-loop.py`.

**Not the root cause:** missing `visual.reframe.static` (that route remains VERIFIED).

---

## Pacing V1 contract

Profile: `runtime/informational-short-pacing-v1-profile.yaml`

| Threshold | Meaning |
|-----------|---------|
| **> 6s** | `PACING_WARNING` — review |
| **> 10s** + unchanged visual across semantic beats | `PACING_REPAIR_CANDIDATE` |
| `editorial_reason` / `pacing_exempt` | `PACING_EXEMPT` |

Repair priority: `clip.merge_continuous_source` only when the finished timeline abuts and Resolve `clip_info` source frames match before and after the join → `replan_continuous_source_range` is a suggestion when a source-frame gap must not be filled, and it does not rewrite in/out by itself → `clip.source_range` → `clip.assemble` → `visual.reframe.static`  
A continuous long take is a non-blocking hold when nothing else fails. It is not an automatic asset swap.  
**Forbidden first:** push-in, pan, ResolveFX, Fusion motion. Filling skipped source frames to hide a gap.  
Production closure for a legal join is `assembly-qa-repair-loop.py --apply-repair`. Without that flag the loop is a preview and must not report normalization as complete.

---

## Black-bar / Reframe loop

Profile: `runtime/black-bar-reframe-qa-profile.yaml`

```
source selection → assemble → static reframe → frame QA → black-bar detect
  → PASS | REPAIR_REQUIRED → visual.reframe.static repair → re-QA
```

Tool: `black-bar-qa.py` (ffmpeg `cropdetect`, per-edge bars, multi-frame).

Verdicts: `PASS` | `SUSPECT_BLACK_BARS` | `REPAIR_REQUIRED` | `REFRAME_OWNER_REVIEW_REQUIRED`

---

## Blueprint traceability

`assembly_plan.shots[]` must carry:

- `shot_id`, `beat_id`, `source_asset`, `source_range`, `timeline_duration_sec`
- `reframe.required`, `reframe.applied`, `reframe.scale`, `reframe.position`

QA findings reference **Beat / Shot / asset** — not generic “发现黑边”.

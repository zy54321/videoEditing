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

**Root cause (primary):** QA **detector VERIFIED ≠ Production closure VERIFIED**. Detection existed but was neither sufficiently sensitive nor wired into a fail-closed repair loop.

**Not the root cause:** missing `visual.reframe.static` (that route remains VERIFIED).

---

## Pacing V1 contract

Profile: `runtime/informational-short-pacing-v1-profile.yaml`

| Threshold | Meaning |
|-----------|---------|
| **> 6s** | `PACING_WARNING` — review |
| **> 10s** + unchanged visual across semantic beats | `PACING_REPAIR_CANDIDATE` |
| `editorial_reason` / `pacing_exempt` | `PACING_EXEMPT` |

Repair priority: `clip.source_range` → `clip.assemble` → `visual.reframe.static`  
**Forbidden first:** push-in, pan, ResolveFX, Fusion motion.

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

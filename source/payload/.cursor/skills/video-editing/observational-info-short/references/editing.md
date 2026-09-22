# Observational Info Short — Editing

Common craft baseline: `video-workflow/knowledge/editing-craft/editing-rhythm.md`

---

## Pacing & Cuts

| Segment | Typical visual unit |
|---------|---------------------|
| Hook | 1.5–3.5s between visual changes |
| Ordinary semantic unit | 2.5–4.5s |
| Establish | 4–6s |
| Dense information | 1.5–3s |

Cut on: semantic turn, action change, contrast, emphasis — **not** sentence boundaries alone.

---

## Motion Strategy — MUST

Real-life action speed takes priority. `motion = SKIPPED` unacceptable when abnormal slow motion present.

### Evaluate for slow motion

walking, hands, payment, gestures, vehicles, pouring, doors, shopping

| Condition | Typical speed |
|-----------|---------------|
| Natural | 1.0× |
| Slight stock slow | 1.15–1.35× |
| Obvious slow motion | 1.4–2.0× |
| Severe | 2.0×+ (verify; replace if still unnatural) |

Each motion-risk clip: **KEEP** | **NORMALIZE** | **REPLACE**

### Mixed FPS / Cadence

Analyze **before** Plan:

- source fps distribution
- timeline fps (Brief default 24)
- motion-heavy clip list
- cadence risk

Safe degradation (no VERIFIED interpolation):

1. prefer matching fps sources
2. low-motion mismatch → keep → motion QA
3. motion-heavy mismatch → alternate source
4. abnormal slow → normalize
5. still bad → replace

---

## Transition Strategy

~70–85% hard / natural cuts.

| Relationship | Transition |
|--------------|------------|
| Same continuity | Hard / action cut |
| Light scene change | Short dissolve (~4–8 frames @ timeline fps) |
| Contrast beat | Hard cut often stronger |
| Ending | Slightly softer allowed |

**Prohibited by default:** spin, whip, flash, heavy zoom, glitch.

Every transition: handles, no gap, no black frame.

---

## Original Sound

Allowed breath sections (3–6s): ambience without ordinary captions when intentional.

Distinguish intentional no-caption vs defect in QA.

---

## Ending Strategy

No forced slogan / CTA / “what do you think?” unless Brief requests.

Preferred:

```
summary or reframe + natural life visual + ~0.4–0.8s visual tail
```

Music may tail briefly then end naturally.

---

## Fallback Policy

Missing ideal footage:

1. semantic-adjacent real B-roll
2. alternate framing / range
3. minimal graphic
4. AI supplement (last)

Prefer semantically correct over merely beautiful.

# Observational Info Short — Genre QA

Checklist for L3 QA Stage (Genre layer). Run after Universal QA.

Each item: **PASS** | **FAIL** | **N/A** (with reason).

---

## OBS-QA-01 — Motion Naturalness

No unintentional obvious slow-motion in action footage (walking, hands, payment, gestures, vehicles, etc.).

Stock footage must not retain clearly unnatural slow speed without Motion Normalization or conscious style justification.

---

## OBS-QA-02 — Shot Duration

No unjustified long stock B-roll holds that stall information flow.

Establishing shots may be longer; ordinary semantic units should stay within style ranges unless Brief allows.

---

## OBS-QA-03 — Semantic Alignment

Picture and narration must not be obviously misaligned.

Visual should support, illustrate, or contrast the spoken information — not contradict or drift from it.

---

## OBS-QA-04 — Factual Implication

Generic B-roll must not imply specific real-world events, locations, or identifiable people as if they were direct evidence.

AI or stock must not fake news scenes or factual proof.

---

## OBS-QA-05 — Repetition

No short-interval repeat of same source range or same composition without narrative purpose.

Reuse must change range, framing, or semantic role.

---

## OBS-QA-06 — Transition Restraint

Not every cut should have a transition effect.

Majority should be natural / hard cuts per Transition Strategy.

---

## OBS-QA-07 — Transition Integrity

No black frames, timeline gaps, or insufficient handles caused by transitions.

Duration must match plan.

---

## OBS-QA-08 — Vertical Framing

No unintended black bars (letterbox / pillarbox).

Subject must remain visible and reasonably composed in 9:16 when that is the target format.

---

## OBS-QA-09 — Subtitle Coverage

When Brief `subtitles: true`, main narration segments must have subtitle coverage.

Gaps only where intentionally silent or Brief excludes.

---

## OBS-QA-10 — Subtitle Readability

Subtitles must not be excessively long per cue or block core subject.

1–2 lines; mobile-readable.

---

## OBS-QA-11 — Keyword Accuracy

Proper nouns (names, places, terms) must match Frozen Script when frozen text exists.

ASR alone is not authority over frozen text.

---

## OBS-QA-12 — Music Presence

When Brief `music: true`, background music must be present at appropriate level.

---

## OBS-QA-13 — Narration Dominance

Music must not mask or overpower narration.

Voice must remain clearly intelligible.

---

## OBS-QA-14 — Music Continuity

No jarring music start, stop, or level jump without justification.

Fades preferred over hard cuts.

---

## OBS-QA-15 — Color Coherence

No unexplained exposure or white-balance breaks between adjacent or related shots.

Sources should feel like one coherent piece.

---

## OBS-QA-16 — Effect Restraint

Effects must not dominate content.

No "every shot has an effect" density for this genre.

---

## OBS-QA-17 — Opening Efficiency

Opening must not linger without information.

First 3–5 seconds should establish place, question, contrast, or hook point.

---

## OBS-QA-18 — Ending Quality

Ending must not cut off abruptly.

Natural visual and audio tail (~0.4–0.8 sec visual tail when applicable).

---

## OBS-QA-19 — Overall Stock Feel

If the whole piece reads as obvious "slow stock montage + voiceover" fakery, **FAIL** even when individual technical checks pass.

Believable real-life motion and semantic fit override checkbox QA.

---

## OBS-QA-20 — Genre Fit

Final piece must still feel like **observational / informational short video**.

Must **not** read primarily as:

- news broadcast
- travel advertisement
- movie trailer
- corporate promo

---

## QA Summary Template

```
Genre QA: observational-info-short
Production: <production_id>

OBS-QA-01: PASS | FAIL | N/A
...
OBS-QA-20: PASS | FAIL | N/A

Overall Genre QA: PASS | FAIL
Blocking items: [...]
```

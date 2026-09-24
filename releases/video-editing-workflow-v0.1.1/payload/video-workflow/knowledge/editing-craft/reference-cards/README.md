# Reference Card Contract

Shared schema for pairwise aesthetic preference examples. **Research / teaching artifacts** — not Runtime dependencies.

## Purpose

Answer: *Given context C, why does Style S prefer option A over B?*

Cards are loaded by L2 references via ID — **do not** duplicate large case libraries inside each Style.

## Card Schema

```yaml
id: RC-VIS-001
dimension: visual-language

context:
  narrative_function: EVIDENCE
  emotion_before: curiosity
  emotion_after: recognition
  attention_target: hands paying at counter

options:
  - id: A
    description: medium shot, stable, subject-centered
  - id: B
    description: aggressive push-in on hands with shallow depth

preferred: A

because: >
  Observational style favors readable evidence over cinematic emphasis;
  push-in would signal ad-like intentionality.

tradeoff: A may feel less "dynamic" but preserves authenticity.

avoid_when: contrast beat explicitly needs visual surprise (local Owner intent)

applicable_styles:
  - observational-info-short
```

## Loading Policy

1. L2 `07-taste.md` or dimension references may cite `reference-cards/<id>.yaml`
2. L3 Blueprint may reference card ID in `asset_selection_guidance` — not required
3. Cards **do not** override Style authority or Brief
4. Missing card → use Style Decision Policy; do not invent card authority

## Pairwise Preference

Cards support `GOOD / BAD` or `A / B` comparisons only — not absolute beauty scores.

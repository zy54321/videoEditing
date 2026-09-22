# L2 Style Contract & Aesthetic Intelligence (V0.1.1 — Stage 08D)

## Architecture Stack

```text
Author Intent (Brief — optional)
      ↓
Common Editing Craft (knowledge/editing-craft/)
      ↓
L2 Style Identity / Taste / Decision Policy
      ↓
L2 Capability Policy (capability-policy.yaml)
      ↓
Beat-first Edit Blueprint (+ capability_requirements)
      ↓
L3 Capability Resolution
      ↓
L1 Capability Vocabulary / Registry
      ↓
Execution Plan
      ↓
L0 Runtime
      ↓
Technical QA → Aesthetic QA → Style Fidelity QA
```

**Principle:** WHY → WHAT → CAPABILITY → HOW → VERIFY

| Layer | Responsibility |
|-------|----------------|
| L2 | WHAT / WHEN / WHY |
| L1 | HOW (capability truth) |
| L0 | EXECUTE |

L2 files **must not** bind MCP methods, Resolve APIs, or runtime functions.

---

## Canonical L2 Directory

```text
.cursor/skills/video-editing/<style-id>/
├─ SKILL.md
├─ style-profile.yaml
├─ capability-policy.yaml
├─ capability-coverage.yaml   # static inventory snapshot (optional)
└─ references/
   ├─ 01-directing.md
   ├─ 02-visual-language.md
   ├─ 03-editing-rhythm.md
   ├─ 04-typography-graphics.md
   ├─ 05-sound-music.md
   ├─ 06-color-look-effects.md
   ├─ 07-taste.md
   └─ 08-qa.md
```

Template: `video-workflow/templates/style-skill/`

**Reference implementation:** `observational-info-short`

---

## Style Profile

`style-profile.yaml` — structured taste coordinates (not quality scores).

---

## Decision Policy References

Dimensions `01`–`06` use unified sections: Style Goal, Inherit from Common Craft, Style Defaults, Prefer/Allow/Avoid/Prohibit, Capability Intent, Blueprint Mapping, QA Signals.

`07-taste.md` — taste identity, tensions, failure modes, preference logic.

`08-qa.md` — **Style Fidelity QA only** (not technical QA).

---

## Capability Policy

`capability-policy.yaml` bridges L2 → L1 using **Logical Capability IDs** only.

Criticality: `REQUIRED` | `PREFERRED` | `OPTIONAL`

Vocabulary: `video-workflow/capabilities/logical-capability-vocabulary.yaml`

---

## Blueprint & Resolution

- Blueprint `capability_requirements` — semantic requirements, not runtime actions
- Resolution output: `video-workflow/production/capability-resolution.yaml`
- Template: `capability-resolution-result.yaml`
- Status: `SELECTED` | `FALLBACK` | `OMITTED` | `BLOCKED`
- **UNKNOWN ≠ VERIFIED**

Capability Coverage = inventory only — **not** aesthetic score.

---

## Reference Cards

`knowledge/editing-craft/reference-cards/` — pairwise preference schema (research / teaching). Not runtime dependency.

---

## Format vs Style

**Format** (aspect, duration, platform) → **Production Brief**

**Style** → how to adapt when Brief specifies format (e.g. vertical 9:16 framing rules in `02-visual-language.md`).

---

## Style Extension Process

```text
Canonical Style Template
  → Define Identity + Taste Profile
  → Decision Policies (01–07)
  → Bind Capability Policy
  → Style Fidelity QA (08)
  → Generic Style Contract Test
  → Capability Coverage snapshot
  → Only then Runtime Validation / Production
```

Stage 08D does **not** create additional Styles or run Production.

---

## Build vs Production

Construction stages (including 08D) follow `BUILD_STAGE_NO_PRODUCTION`.

`CAPABILITY_VALIDATION_REQUIRED` marks designs needing future runtime proof — not validated in 08D.

---

## Acceptance (Owner — 2026-09-23)

| Field | Value |
|-------|-------|
| Status | **ACCEPTED** |
| Baseline HEAD | `81035a7` |
| Receipt | `validation/stage-08d-acceptance-closeout.md` |

Stage 08D construction foundation is closed. N02 Final Acceptance and v0.1.1 Release remain separate Owner decisions.

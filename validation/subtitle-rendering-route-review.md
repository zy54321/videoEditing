# Subtitle Rendering Route Review (A–D)

**Starting HEAD:** `732dc4d31014b88c9ee17523e300f087d29ec3a9`  
**Production objective (restated):** Stable `SUBTITLE_RENDERING_PRODUCTION_CAPABILITY` — CJK readable **Bold/Semibold**, white fill, black stroke, semantic wrap, safe-area, 35 cues timing-stable, automated, final-artifact verifiable, repeatable — **without** per-video Owner hand work.

**Not the goal:** “Make Native DRT expose Bold API.”

---

## Route A — Native DRT direct automation

| Criterion | Verdict | Facts |
|-----------|---------|-------|
| Automation coverage | **PARTIAL** | `drt.assemble` + timing/text/**\\n** **VERIFIED** (08A.1). |
| Font family / weight | **BLOCKED** | No scripting API; `project_db` font fields **PARTIAL** and stroke not writable. |
| Stroke | **SUPPORTED** | FieldsBlob inject **VERIFIED** (Step 5). |
| Geometry / wrap | **PARTIAL** | Wrap upstream (`subtitle-layout-engine`); position not API-stable. |
| Timing fidelity | **SUPPORTED** | Frame-accurate cues on timeline. |
| Final-artifact determinism | **PARTIAL** | Burn-in OK; weight/font not deterministic without blob map. |
| Readback | **BLOCKED** for style | No stroke/font readback via API. |
| Resolve coupling | High | |
| Fragility | Medium (blob opaque) | |
| Production complexity | Low for stroke-only | |
| **Overall** | **PARTIAL** (content+stroke) / **BLOCKED** (Bold production target) | Guessing blob offsets = **REJECTED**. |

---

## Route B — Gold-standard DRT template replay

| Criterion | Verdict | Facts |
|-----------|---------|-------|
| Automation coverage | **PARTIAL** | Stroke template **VERIFIED**; full-style template **not yet captured** for YaHei Bold. |
| Font family / weight | **SUPPORTED** *if* gold capture includes desired style | One-time Owner styled track → capture `FieldsBlob` → inject style-only (Step 5 pattern). |
| Stroke | **SUPPORTED** | Proven. |
| Geometry / wrap | **PARTIAL** | Still cue text + **\\n**; no auto margin API. |
| Timing fidelity | **SUPPORTED** | Same as A. |
| Final-artifact determinism | **SUPPORTED** after capture | Replay is deterministic for **style**; text/timing parameterized. |
| Readback | **BLOCKED** | Binary blob diff only. |
| **Overall** | **PARTIAL** | **Viable backup** to external burn-in if Owner accepts one-time gold capture with **Microsoft YaHei UI Bold**. |

---

## Route C — Static Text+ / Fusion template

| Criterion | Verdict | Facts |
|-----------|---------|-------|
| Automation coverage | **PARTIAL** | `textplus_styledtextcls_import_comp` **VERIFIED (isolated)**; nested overlay **PARTIAL** (08E-FINAL). |
| Font / weight / stroke | **PARTIAL** | Generator route can set font; production 35-cue timeline overlay **not** final-validated. |
| Geometry | **AVAILABLE_UNVERIFIED** | Pixel width L1 exists; Deliver parity incomplete. |
| Timing fidelity | **PARTIAL** | Per-title placement vs 35 cues = high complexity. |
| **Overall** | **PARTIAL** | Not rejected for rich animation — rejected for **N02 cost**: higher than B/D for static-only need. |

---

## Route D — External deterministic burn-in (ASS / FFmpeg)

| Criterion | Verdict | Facts |
|-----------|---------|-------|
| Automation coverage | **SUPPORTED** (fixture) | `subtitle-route-fixture-experiment.py` → burn-in **PASS**. |
| Font family / weight | **SUPPORTED** | ASS `Microsoft YaHei UI` **Bold**, outline 4px, white on fixture. |
| Stroke | **SUPPORTED** | ASS outline. |
| Geometry | **SUPPORTED** (fixture) | Final-artifact QA **PASS** (margins 134/127 px on two-line sample). |
| semantic wrap | **SUPPORTED** upstream | Layout intent → ASS `\\N` (decoupled). |
| Timing fidelity | **SUPPORTED** | ASS dialogue times; must align to plan frames (generator TBD). |
| Final-artifact determinism | **SUPPORTED** | FFmpeg + libass repeatable on CI/host. |
| Resolve coupling | **Low** | Resolve delivers **clean master** (no burn-in) → external pass. |
| Gates preserved | **SUPPORTED** | Duration, A/V streams, loudness, geometry QA apply to final MP4. |
| **Overall** | **SUPPORTED_ON_FIXTURE** | Ready for `CAPABILITY_VERIFIED_ON_FIXTURE`; not yet N02 apply. |

---

## Project.db

| Verdict | **REJECTED_FOR_PRODUCTION** |
|---------|-------------------------------|
| Reasons | No Windows `Project.db` path; closed-project + relaunch; stroke not in API; violates fail-closed policy unless schema+backup+determinism proven. |

---

## Chinese font / Open Sans

| Finding | Detail |
|---------|--------|
| **Open Sans Bold** | **Not suitable** as primary for N02 Chinese — no CJK glyphs on host (`cannot open resource` / fallback). |
| **Actual glyph font** | Must be **CJK-capable** family; recommended **Microsoft YaHei UI Bold** (`msyhbd.ttc`). |
| Distinction | *requested* Open Sans ≠ *rendered* glyphs for 中文. |

---

## Architecture

Logical capability: **`subtitle.render.readable_static`** (new runtime binding in decision doc).  
Upstream: **`subtitle.layout.*`** (semantic wrap, PRECHECK only).  
Runtime implementations: `resolve_native_drt` | `resolve_textplus_static` | **`external_ass_burnin`** (selected).

---

## Is Native DRT assumption wrong?

**Partially.** Native DRT remains **correct** for **cue authoring + stroke template + Resolve-native preview**. It is **not** the best **sole** runtime for **Bold CJK + safe geometry** without gold capture or DB surgery. Issue class: **WORKFLOW** (wrong default route) + **CAPABILITY** (no safe weight API), **not** “Astra cannot do bold subtitles.”

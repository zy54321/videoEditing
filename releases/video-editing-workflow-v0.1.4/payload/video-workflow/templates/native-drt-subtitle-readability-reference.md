# Native DRT Subtitle Readability Reference (L1)

## Purpose

Production-safe default for **Native DRT subtitles** on light / busy backgrounds:

- **White** foreground
- **Black / dark outer stroke**
- No background box by default
- No Text+ overlay
- No adaptive per-cue color logic

Profile artifact: `video-workflow/runtime/native-drt-subtitle-readability-profile.yaml`

---

## Layer split

| Layer | Owns |
|-------|------|
| **This profile (L1 runtime)** | Readability baseline — white + dark stroke semantics |
| **L2 Style** | Creative accent (e.g. orange stroke) — must not remove readability requirement |
| **L3 Finish / Subtitle Pass** | Apply profile after `native_drt_subtitles` placement when automation route is VERIFIED |

---

## Resolve UI vs automation

| Capability | Resolve UI | Current automation |
|------------|------------|-------------------|
| Subtitle placement | Yes | **VERIFIED** — `drt.assemble` `spec.subtitles[]` |
| Outer stroke | Yes (18.6+) | **BLOCKED** — no scripting API; MCP `set_subtitle_style` has no outline fields |
| Font / position (track) | Yes | **PARTIAL** — `project_db.set_subtitle_style` (font + normalized position only); requires pre-styled track blob |
| Burn-in deliver | Yes | **VERIFIED** — `ExportSubtitle: BurnIn` on Resolve 21.x disposable probe |

**Do not conflate:** GUI can set stroke manually (`AVAILABLE_MANUAL`) ≠ production automation (`VERIFIED`).

---

## Automation priority (fixed)

1. Samuel MCP native subtitle style → **UNAVAILABLE**
2. Resolve scripting API → **UNAVAILABLE** (api_truth: subtitle track styling)
3. `project_db.set_subtitle_style` → **PARTIAL** (no stroke)
4. DRT / native artifact style injection → **NOT_SUPPORTED** (`place-subtitles` authors unstyled `TRACK_FIELDS_BLOB`)

If stroke automation is required and all above fail: register `NATIVE_SUBTITLE_STROKE_AUTOMATION = BLOCKED`.

---

## Step 5 — Route A template (checkpoint)

| Step | Tool |
|------|------|
| Owner UI gold standard | white + black outer stroke on native subtitle track |
| Capture diff | `native-drt-subtitle-stroke-capture.py` |
| Inject into production DRT | `native-drt-subtitle-stroke-inject.py` |
| Disposable orchestrator | `native-drt-subtitle-readability-probe.ps1` |

`subtitle.render.readability_stroke` is **VERIFIED** after Step 5 Route A FieldsBlob inject + burn-in deliver (see `validation/native-subtitle-readability-unblock/step5-visual-qa.json`).

---

## Verification rule

`subtitle.render.readability_stroke` may reach **VERIFIED** only with:

```
Automation or controlled manual seed
→ Timeline native subtitles
→ Rendered frame / burn-in deliver
→ Visible dark outline on light background
```

API success or DB readback alone is **insufficient**.

---

## Stage 08E non-regression

Unchanged by this profile:

- `subtitle.layout.pixel_width` = AVAILABLE_UNVERIFIED
- `subtitle.style.keyword_emphasis` = AVAILABLE_UNVERIFIED
- Text+ overlay = PARTIAL / isolated only
- Native DRT + semantic segmentation = first Production baseline

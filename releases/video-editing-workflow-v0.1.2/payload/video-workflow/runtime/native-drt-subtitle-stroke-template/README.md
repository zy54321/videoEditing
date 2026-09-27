# Native DRT Subtitle Stroke Template (Route A)

Style-only `EffectFiltersBA` blob harvested from a **UI-styled** Native Subtitle track.

## Gold standard (Owner manual once)

In disposable project `_mcp_VEW-Native-Subtitle-Readability-Unblock`:

1. Place native DRT subtitles (unstyled) → export baseline `.drt`
2. Inspector → subtitle track → **white text + black outer stroke** → save → export styled `.drt`
3. Run:

```text
python video-workflow/tools/native-drt-subtitle-stroke-capture.py baseline.drt styled.drt
```

`template-manifest.json` must reach `status: READY` before injection.

## Injection

```text
python video-workflow/tools/native-drt-subtitle-stroke-inject.py input.drt output.drt
```

Cue text and timing remain from `spec.subtitles[]` — only track style blob is copied.

## Verification authority

Rendered pixels on **light background** + deliver MP4 — not API/DB success alone.

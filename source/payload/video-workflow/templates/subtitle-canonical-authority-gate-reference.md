# Subtitle Canonical Authority Gate (R1 Closeout)

## When mandatory

`features.subtitles` enabled **and**:

- `content.authority.type = script`, or
- `assets.script.frozen = true`

## Production artifacts (workspace)

| Artifact | Path |
|----------|------|
| ASR timing evidence | `video-workflow/production/asr-timing-evidence.json` |
| Canonical cues | `video-workflow/production/canonical-subtitle-cues.json` |
| Gate result | `video-workflow/production/subtitle-canonical-gate-result.json` |

## Orchestration

```powershell
video-workflow/tools/invoke-frozen-script-subtitle-route.ps1 -WorkspaceRoot <workspace>
```

## Renderer fail-closed

```powershell
video-workflow/tools/assert-subtitle-renderer-canonical-input.ps1 -WorkspaceRoot <workspace>
```

Exit `0` = renderer may proceed. Non-zero = **RENDERER_SUBTITLE_AUTHORITY_BYPASS_BLOCKED**.

## Gate checks

- `pipeline_id` = `subtitle.authority_alignment_v1`
- `meta.text_authority` = `frozen_script`
- `meta.status` = `OK`, alignment not blocked
- Concatenated cue text = Frozen Script normalized text
- Cue timings monotonic
- Final text must not equal ASR-only text when Frozen Script differs (homophone / misrecognition guard)

# Voice Subtitle Text Review (U1)

**Content authority** remains `content.authority.type=voice`. **Subtitle text authority** for Canonical cues comes from reviewed text after U1 review + **Owner intent artifact**.

## Artifacts

| File | Role |
|------|------|
| `voice-subtitle-review-result.json` | Detector output + `status` + provenance assessment |
| `reviewed-subtitle-text.txt` | Draft text for `--script` canonical build |
| `voice-subtitle-owner-approval-intent.json` | **Owner-written** confirmation bound to `production.id` + text SHA256 |
| `voice-subtitle-approval.json` | Recorded approval (only after intent validation); not final U3 gate |
| `asr-timing-evidence.json` | Primary ASR (required) |
| `asr-timing-evidence-alt.json` | Secondary ASR (optional; provenance required for independence checks) |

ASR JSON may include optional `provenance`: `asr_run_id`, `provider_id`, `source_audio_sha256`, `captured_at`.

## Status

`OWNER_ACCEPTED` | `NEEDS_OWNER_REVIEW` | `BLOCKED` | `NOT_APPLICABLE`

`AUTO_ACCEPTED` is **not emitted** in this repository (`AUTO_REVIEW_RUNTIME_NOT_AVAILABLE`).

## Commands

```
video-workflow/tools/invoke-voice-subtitle-review-route.ps1 -WorkspaceRoot <ws>
# Owner creates intent JSON on disk, then:
video-workflow/tools/record-voice-subtitle-owner-approval.py --workspace <ws> [--intent-file <path>]
```

`--owner-actor` alone is **not** sufficient. Cursor does not provide cryptographic Owner identity (`identity_authentication: NOT_PROVIDED_CURSOR_WORKFLOW_BOUNDARY`).

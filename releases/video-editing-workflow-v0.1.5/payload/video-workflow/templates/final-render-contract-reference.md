# Final Render Contract (R2)

**Deliver authority:** burned final MP4 only. Timeline / DRT / ASS / TTML are not Production PASS evidence.

## Artifact path

`video-workflow/production/final-render-contract.json`

## Required fields (schema_version 1)

| Field | Meaning |
|-------|---------|
| `renderer_route` | `native_drt` or `external_ass` |
| `render_source_timeline` | Resolve timeline name / id |
| `final_artifact_path` | **Owner deliverable** MP4 (subtitles burned in when enabled) |
| `clean_master_path` | Optional Resolve export **without** burn-in (external ASS route only) |
| `subtitle_materialization` | `native_drt_burnin` \| `external_ass_burnin` \| `na` |
| `burnin_method` | `resolve_export_burn_in` \| `ffmpeg_libass` |
| `resolve_subtitle_export_mode` | `burn_into_video` \| `separate_subtitle_file` (Native DRT) |
| `canonical_subtitle_cues_path` | R1 `canonical-subtitle-cues.json` |
| `external_ass_style_baseline_id` | When `external_ass` — verified baseline id (e.g. `astra-external-ass-n02prod-v1`) |
| `subtitle_series_style_ref` | Optional Brief registry key echoed for traceability |
| `sidecar_subtitle_paths` | TTML/SRT paths if any (N03 regression guard) |

## Native DRT

- `subtitle_materialization` = `native_drt_burnin`
- `resolve_subtitle_export_mode` **must** be `burn_into_video` (Resolve `ExportSubtitle: BurnIn`)
- Separate subtitle file + playable MP4 without pixels = **FAIL** (`FINAL_RENDER_SUBTITLE_BURNIN`)

## external ASS

- `clean_master_path` = Resolve export (no burn-in)
- `final_artifact_path` = libass-burned MP4
- PASS only on `final_artifact_path`, never on clean master alone

## Post-render gate

```powershell
video-workflow/tools/run-final-artifact-gate.ps1 -WorkspaceRoot <workspace>
```

Writes `video-workflow/production/final-artifact-gate-result.json` with `FINAL_ARTIFACT_GATE` verdict.

On **PASS**, records `evidence_bindings` (SHA256): `contract_sha256`, `final_artifact_sha256`, `canonical_subtitle_cues_sha256`, optional `qa_report_sha256`. Stage 10 `assert-production-final-deliver.ps1` recomputes hashes — any drift → `PRODUCTION_COMPLETE_BLOCKED`.

Subtitle burn-in uses **differential evidence** (`subtitle_burnin_evidence.py`): external ASS compares clean master vs final; Native DRT uses temporal negative control. Bright pixels alone are **not** sufficient for `FINAL_RENDER_SUBTITLE_BURNIN = PASS`.

# External ASS Style Baseline (v1)

Versioned machine-readable style for **optional** `subtitle.runtime.external_ass` materialization.

| Field | Value |
|-------|--------|
| Baseline file | `subtitle-external-ass-style-baseline.v1.json` |
| `baseline_id` | `astra-external-ass-n02prod-v1` |
| Style name | `N02Prod` |

**Not** a global production default. Owners opt in via `final-render-contract.json` (`renderer_route: external_ass`).

## Authority

Style values are copied from Owner-verified N02_V6 ASS (`source_ass_sha256` in baseline JSON). Do not re-estimate font size from pixels.

## Tooling

| Step | CLI |
|------|-----|
| Canonical → ASS | `canonical-to-external-ass.py` |
| libass burn-in | `external-ass-burnin.py` |
| Production orchestration (opt-in) | `invoke-external-ass-deliver-route.ps1` → `invoke-production-deliver-closeout.ps1` (with R2 gate) |
| R2 gate | `run-final-artifact-gate.py` (unchanged) |

R1 remains `canonical-subtitle-cues.json` + `SUBTITLE_CANONICAL_AUTHORITY_GATE`.

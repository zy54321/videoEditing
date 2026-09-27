# N02 V6 Gap Classification

## Music mix balance

| Item | Value |
|------|-------|
| **FACT** | V5 timeline music stem RMS ≈ **−41.3 dB** vs V4 attenuated stem **−35.9 dB** (**−5.4 dB**). Owner reports V5 music subjectively weaker than V4. |
| **Root cause (QA)** | `n02-v5-music-mix-final-measure.py` used `voice_rms − mix_rms` on full mix; weak music ⇒ mix ≈ voice ⇒ never exceeded weak threshold. Pre-loudnorm file mislabeled as mix truth. |
| **Root cause (mix)** | `recommended_base_factor` **0.08** vs V4 legacy **0.15** (~**5.6 dB** attenuation delta). |
| **gap_class** | **WORKFLOW_GAP** (QA authority/semantics) + **PARAMETER_GAP** (base factor) |
| **why_not_capability** | FFmpeg measurement works; failure was verdict logic and production parameter choice. |
| **repair authority** | `music_mix_balance_qa.py` + `music-mix-balance-profile.yaml` + V6 stem anchored to **0.15** envelope. |

## Subtitle font weight

| Item | Value |
|------|-------|
| **FACT** | V5 burn-in inherits V4 DRT stroke template; Open Sans Bold never applied on timeline. |
| **Root cause** | Verified route is stroke **FieldsBlob** template only; font/weight change needs new styled capture or **project_db** with closed project — not verified on this Windows host. |
| **gap_class** | **CAPABILITY_GAP** (`SUBTITLE_FONT_WEIGHT`) |
| **why_not_parameter** | No safe parameter to turn without verified font write + re-burn-in. |
| **why_not_workflow_only** | Preflight PASS was incorrectly treated as final PASS (WORKFLOW_GAP for geometry authority — separate fix). |
| **repair authority** | Fail closed; no unverified Project.db patch. |

## Subtitle geometry (final artifact)

| Item | Value |
|------|-------|
| **FACT** | Wide cues (e.g. clinic line) near horizontal safe area on encoded frames. |
| **Root cause** | Layout preflight marked **PASS** without final burn-in pixel extent. |
| **gap_class** | **WORKFLOW_GAP** |
| **repair authority** | `subtitle_final_artifact_qa.py` on encoded MP4 samples. |

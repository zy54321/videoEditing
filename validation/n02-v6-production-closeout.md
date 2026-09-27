# N02 V6 Production Closeout

| Field | Value |
|-------|-------|
| Starting HEAD | `921863e8f603581983ef3d7cd2b8ab4ba7a73852` |
| VERSION | `0.1.3-dev` |
| Timeline (music repair) | `N02-V6-Audio-Repair` |
| Music preview artifact | `E:\03_Media\02_Video\Davinci\Astra\2026-09-21\output\N02_V6_audio_repaired_preview.mp4` |
| SHA256 (preview) | `00466c5d77ac88e2b6cb77e9ed37bc4aba2fc9ea7668edc92e8c02be8c4e42fe` |
| Full `N02_V6.mp4` | **Not produced** (subtitle weight CAPABILITY_GAP) |

## Music

- **V5 false PASS:** WORKFLOW_GAP — wrong metric (`voice−mix`), pre-loudnorm mislabeled; see `validation/n02-v6-gap-classification.md`.
- **V5 truth:** production stem **−5.4 dB** vs V4 (`music_mix_balance_qa.py` stem regression).
- **QA fix:** `music_mix_balance_qa.py` + fixtures + stem regression authority.
- **Repair:** V6 envelope `base_factor=0.15` → stem RMS **−35.9 dB** (matches V4).
- **Preview:** encode 1821f → loudnorm **−16.1 LUFS**, **−1.4 dBTP**.

## Subtitle

- **CAPABILITY_GAP:** no verified Bold apply + burn-in route (`validation/n02-v6-subtitle-capability-audit.md`).
- **Geometry:** final artifact QA **FAIL** on encoded V5 (`validation/n02-v6-subtitle-final-qa.json`) — precheck was not authority.

## Gates

| Gate | Status |
|------|--------|
| MUSIC_MIX_QA_AUTHORITY | **PASS** |
| MUSIC_MIX_BALANCE (V6 preview stem) | **PASS** |
| SUBTITLE_RUNTIME_WEIGHT_CAPABILITY | **FAIL** |
| SUBTITLE_FONT_WEIGHT | **CAPABILITY_GAP** |
| SUBTITLE_GEOMETRY_QA | **FAIL** (V5 artifact) |
| READY_FOR_OWNER_REVIEW | **NO** |
| BLOCKER_CLASS | **CAPABILITY_GAP** |

## Continuous execution

Fourth uninterrupted repair chain within authorization (audit → QA → music → render → evidence).

## Evidence

- `validation/n02-v6-gap-classification.md`
- `validation/n02-v6-music-mix-qa.json`
- `validation/n02-v6-subtitle-capability-audit.md`
- `validation/n02-v6-subtitle-final-qa.json`
- `validation/n02-v6-regression-matrix.md`

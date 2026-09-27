# N02 Regression Matrix (V1–V6)

| Issue | V1 | V2 | V3 | V4 | V5 | V6 | Truth source | Regression? |
|-------|----|----|----|----|----|-----|--------------|-------------|
| Loudness (−17…−15 LUFS) | repaired | repaired | repaired | **PASS** | **PASS** | **PASS** | `n02-v6-final-artifact-qa.json` | No |
| True peak ≤ −1 dBTP | — | — | — | **PASS** | **PASS** | **PASS** | same | No |
| Sample rate 48 kHz stereo | — | — | — | **PASS** | **PASS** | **PASS** | ffprobe | No |
| Frame parity 1821 | gap | gap | gap | **PASS** | **PASS** | **PASS** | clean + final | No |
| Portrait fill | — | — | — | letterbox | **PASS** | **PASS** | artifact QA | No |
| Black bars / layout | suspect | — | — | suspect | **PASS** | **PASS** | artifact QA | No |
| Candidate safety | — | — | **PASS** | **PASS** | **PASS** | **PASS** | plan | No |
| Music balance | weak | weak | weak | baseline | **FAIL** stem | **PASS** | stem regression | **Fixed** |
| Music QA authority | — | — | — | — | false PASS | **PASS** | `music_mix_balance_qa.py` | No |
| Subtitle geometry | — | — | — | partial | **FAIL** | **PASS** | external ASS + artifact QA | **Fixed** |
| Subtitle weight (CJK Bold) | — | — | — | regular | gap | **PASS** | YaHei UI + ASS | **Fixed** |
| Encode regression (burn-in) | — | — | — | — | — | **PASS** | PSNR vs clean master | No |

**Deliverable:** `N02_V6.mp4` — full production with external ASS subtitles and V6 music mix.

**Owner:** `OWNER_ACCEPTANCE = CONFIRMED`, `N02_V6_PRODUCTION = ACCEPTED` (2026-09-27).

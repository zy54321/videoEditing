# N02 Regression Matrix (V1–V6)

| Issue | V1 | V2 | V3 | V4 | V5 | V6 current | Current truth | Regression? |
|-------|----|----|----|----|----|------------|---------------|-------------|
| Loudness (−17…−15 LUFS) | repaired | repaired | repaired | **PASS** | **PASS** | preview **PASS** | Final promote | No |
| True peak ≤ −1 dBTP | — | — | — | **PASS** | **PASS** | preview **PASS** | Final promote | No |
| Sample rate 48 kHz stereo | — | — | — | **PASS** | **PASS** | **PASS** | ffprobe | No |
| Frame parity 1821 | gap | gap | gap | **PASS** | **PASS** | **PASS** | Resolve verify | No |
| Portrait fill | — | — | — | letterbox | **PASS** | **PASS** (same video) | artifact QA | No |
| Black bars / layout | suspect | — | — | suspect | **PASS** | **PASS** | artifact QA | No |
| Candidate safety | — | — | **PASS** | **PASS** | **PASS** | **PASS** | plan | No |
| Music balance | weak | weak | weak | baseline | **FAIL** (−5.4 dB stem) | **PASS** stem vs V4 | stem + encode QA | **Fixed in preview** |
| Music QA authority | — | — | — | — | **FALSE PASS** | **PASS** | `music_mix_balance_qa.py` | No |
| Subtitle geometry | — | — | — | partial | precheck only | **FAIL** artifact | pixel QA | **Truth surfaced** |
| Subtitle weight | — | — | — | regular | regular | **CAPABILITY_GAP** | audit | No change |
| Subtitle stroke | — | — | — | DRT | DRT | DRT | inherited | No |

**V6 deliverable:** `N02_V6_audio_repaired_preview.mp4` (music repair only). **Not** `N02_V6.mp4` — subtitle weight capability gap.

# N02 V2 Production Closeout

**Output:** `E:\03_Media\02_Video\Davinci\Astra\2026-09-21\output\N02_V2.mp4`  
**Timeline:** `N02-V2-Captioned-wrap` (duplicated from V1; render + post audio repair)  
**SHA-256:** `765FE38DACC35CA8BBC77EC6500F74DD0AA5993F18987CD88066CD451A1A4BD3`

---

## V1 vs V2

| Area | N02 V1 | N02 V2 |
|------|--------|--------|
| **Audio LUFS** | -24.5 | **-16.1** |
| **True Peak** | -5.7 dBTP | **-1.4 dBTP** |
| **Sample rate** | 48000 Hz | **48000 Hz** |
| **Audio verdict** | FAIL | **PASS** (encoded authority) |
| **Pacing QA (plan)** | missed 11.7 s office span | **detects** `same_source_asset_span`; repair plan includes item 9 alternate |
| **Reuse A-B-A (plan)** | 3 | **0** after assembly repair JSON |
| **Reuse A-B-A-B (plan)** | 1 | **0** after assembly repair JSON |
| **Timeline visual apply** | — | **partial** (duplicate + render; MCP `overwrite_range` trim error on one swap) |
| **Black bar / subtitle / music** | unchanged routes | same timeline generation path (Glass Horizon bed preserved) |

---

## Final artifact QA (N02_V2.mp4)

| Check | Result |
|-------|--------|
| Video | 1080×1920, H.264, 24 fps |
| Duration | 75.9 s |
| Audio PASS | -16.1 LUFS, -1.4 dBTP, AAC 48 kHz stereo |
| Longest same-source span (plan, post-repair) | office span broken in **plan** (item 9 → plaza pool id) |
| Ping-pong A-B-A / A-B-A-B (plan after repair) | **0 / 0** |
| Warm / lively subtitles | **DEFERRED** (Owner scope) |

---

## Remaining production blockers

1. **Resolve apply bridge:** assembly repair plan → `overwrite_range` / append needs reliable source-trim mapping (blocked one office→plaza swap).
2. **Reuse window:** `same_source_window_exceeded` may still flag plaza density after plan repair (acceptable warning vs hard fail — policy TBD).
3. **Continuous execution:** not re-verified for N02 V1 origin run.

---

## Status

**READY_FOR_OWNER_REVIEW** — audio deliverable gate **PASS** on N02_V2 encoded file; editorial reuse/pacing improvements **proven in QA loop**; full visual parity with repair plan pending Resolve apply hardening.

# Stage 08E-B Experiment A — Baseline Audit

| Field | Value |
|-------|-------|
| Stage | **08E-B — Runtime Typography Capability Validation** |
| Experiment | **A — Pixel Width Renderer Parity** |
| Date | 2026-09-23 |
| Starting HEAD | `313104a` |
| VERSION | `0.1.1-dev` |
| Disposable Project | `Astra-08E-B-Subtitle-Validation` |
| Primary Timeline | `08E-B-EXP-A-v2` (active measurement timeline) |
| Legacy Probe Timeline | `08E-B-EXP-A-Pixel-Width` |

---

## Runtime

| Item | Value | Evidence |
|------|-------|----------|
| Resolve product | DaVinci Resolve **Studio** | `resolve_control.get_version` |
| Resolve version | **21.1.0.14** | `version_string` |
| Resolve path | `D:\soft\davinci\app\Resolve.exe` | Public desktop shortcut target |
| MCP | Samuel DaVinci MCP **4.8.13** | `get_version.mcp.version` |
| MCP update available | v4.8.15 (not applied; authorized pin 4.8.13) | `mcp.update_decision` |
| Connection | **CONNECTED** (GUI, Local Database) | `runtime_mode` after manual launch |
| N02 isolation | **PASS** — no N02 project loaded | `project_manager.list` |

---

## Timeline format

| Item | Planned | Actual |
|------|---------|--------|
| Resolution | 1080×1920 | 1080×1920 (`project_manager.snapshot`) |
| FPS | 24 | 24 |
| Safe margins (L1 contract) | L54 / R54 | unchanged |
| Style target ratio | 0.77 | unchanged |
| Hard ceiling ratio | 0.80 | unchanged |

---

## Font

| Layer | Requested | Resolved / Available | Notes |
|-------|-----------|----------------------|-------|
| L1 preflight (System.Drawing) | Microsoft YaHei | **NOT FOUND** on validation host | `FONT_NOT_FOUND`; SimSun fallback also unavailable |
| Resolve Text+ (Fusion) | Microsoft YaHei | **Set + readback OK** on `Template` tool | `fusion_comp.safe_set_inputs` |
| Contract tests on host | — | Falls back to **Arial** | `subtitle-layout-contract.ps1` |

**Impact:** L1 predicted width cannot be produced on this host for the authorized Chinese typography contract without font installation or a matched fallback policy decision.

---

## Subtitle route

| Item | Value |
|------|-------|
| **Requested route (Experiment A)** | Typography renderer isolation — Fusion **Text+** with explicit `Font` / `Size` / `StyledText` |
| **Planned route recorded** | `timeline.insert_fusion_title` → `Text+` → `fusion_comp` on tool `Template` |
| **Actual executable route** | **PARTIAL** |
| Route evidence | Text visible via `timeline_frame.capture` on `08E-B-EXP-A-v2` @ `01:00:05:12` |
| Deliver render artifact | **Text NOT present** in PNG/MOV output (flat RGB 135 gray field); not measurable |
| `insert_title` (non-Fusion) | **FAILED** on v1 timeline |
| `live_api_srt_append` | **NOT USED** (UNSAFE) |
| Native subtitle burn-in | **NOT TESTED** (out of scope for Typography renderer isolation) |

---

## Project / timeline inventory (disposable)

| Name | Purpose | Status |
|------|---------|--------|
| `Astra-08E-B-Subtitle-Validation` | Isolated validation project | Created |
| `08E-B-EXP-A-Pixel-Width` | Initial generator probe | Superseded |
| `08E-B-EXP-A-v2` | Black still + Text+ sequential layout | **Active** |

---

## Measurement tooling

| Tool | Status |
|------|--------|
| FFmpeg / FFprobe | Available |
| Python 3.12 + Pillow | Available |
| `validation/08e-b-exp-a/measure_subtitle_width.py` | Added |
| numpy | Not installed (Pillow-only path used) |

---

## Baseline deltas vs expectation

| Delta | Breaks Experiment A? | Action |
|-------|----------------------|--------|
| Resolve not auto-launchable via MCP until manual start | No (recovered) | Document manual launch path |
| MCP 4.8.15 available vs authorized 4.8.13 | No | Record only |
| L1 font missing on host | **YES** | Stop parity matrix |
| Deliver render ≠ timeline_frame for Text+ | **YES** | Stop automated width matrix |

# Production Repair Step 5 — Native Subtitle Readability Unblock Closeout

## Git provenance

| Label | SHA |
|-------|-----|
| **Starting HEAD** | `48c9ce18a8649c8c5e6a3ee1b838b0197752e5b2` |
| **Prior review CLOSEOUT_RECORD_HEAD** | `5f0d6183c49e662942a4d7956e30439847680904` |
| **Prior review record fix HEAD** | `48c9ce18a8649c8c5e6a3ee1b838b0197752e5b2` |

Preflight: current HEAD matched `48c9ce…`; working tree clean at start.

## Scope

| | |
|---|---|
| **N02 touched** | NO |
| **Real Production** | NO |
| **N02 V5** | NOT run |
| **Stage 08E** | NOT reopened |
| **Text+ overlay** | NOT upgraded |

## Runtime outcome

| Check | Result |
|-------|--------|
| `resolve_control.launch` | **FAILED** — Resolve not running; could not be started from MCP host |
| Local `Resolve.exe` default path | **NOT FOUND** |
| Route A disposable project | **NOT CREATED** (blocked on Resolve) |

**Checkpoint:** `OWNER_MANUAL_GOLD_STANDARD_REQUIRED` + **Start DaVinci Resolve** on host.

## Route A — Native styled track blob capture

| Phase | Result |
|-------|--------|
| Gold standard UI stroke | **NOT CAPTURED** — requires Owner one-time Inspector outer stroke |
| Baseline vs styled diff | **INCONCLUSIVE** — Step 2 probe DRT pair both have empty `<EffectFiltersBA/>` under `SubtitleTrackVec` |
| FACT (offline inspect) | Subtitle track uses `<EffectFiltersBA/>` self-closing stub when unstyled |
| INFERENCE | Populated `EffectFiltersBA` inner payload likely carries stroke — **requires UI-styled export** |
| Minimal injection tooling | **IMPLEMENTED** (pending valid template) |

### Tools delivered

| Tool | Role |
|------|------|
| `tools/lib/native_subtitle_stroke_template.py` | diff / validate / inject |
| `tools/native-drt-subtitle-stroke-capture.py` | baseline vs styled DRT → template manifest |
| `tools/native-drt-subtitle-stroke-inject.py` | apply style-only blob to new DRT |
| `tools/native-drt-subtitle-readability-probe.ps1` | checkpoint orchestrator |
| `runtime/native-drt-subtitle-stroke-template/` | manifest `PENDING_GOLD_STANDARD` |

## Route B — Advanced MCP `project_db.set_subtitle_style`

**NOT ENTERED** — no styled `EffectFiltersBA` gold standard; Route A prerequisite unmet; no `Project.db` path available while Resolve offline.

## Visual validation Cases A–E

| Case | Result |
|------|--------|
| A Dark bg | **NOT RUN** |
| B Light bg | **NOT RUN** |
| C Busy bg | **NOT RUN** |
| D Deliver | **NOT RUN** |
| E Reload | **NOT RUN** |

No new pixel evidence this round.

## Capability truth (final)

| Capability | Status |
|------------|--------|
| `subtitle.render.readability_stroke` | **BLOCKED** (unchanged) |
| `native_drt_subtitles` | **VERIFIED** (unchanged) |
| `stroke_automation` (profile) | **BLOCKED** |
| Route A template | **PENDING_GOLD_STANDARD** |

## Production readiness impact

```yaml
SUBTITLE_READABILITY_AUTOMATION_REMAINS_BLOCKED: true
P0_SUBTITLE_READABILITY_STROKE: OPEN
REMAINING_PRODUCTION_BLOCKERS:
  - subtitle.render.readability_stroke
READY_FOR_N02_V5: NO
```

## Owner decision (minimum)

1. Start **DaVinci Resolve** on this machine (or provide path to styled/baseline DRT pair from disposable project `_mcp_VEW-Native-Subtitle-Readability-Unblock`).
2. Apply **white text + black outer stroke** on native subtitle track (Inspector).
3. Export/save **baseline** and **styled** DRT (or DRP extract) and re-run Agent from checkpoint:

```text
python source/payload/video-workflow/tools/native-drt-subtitle-stroke-capture.py <baseline.drt> <styled.drt>
```

Then continue: inject → import timeline → light-background render → deliver → re-QA.

## Tests

`source/tests/production-subtitle-stroke-unblock.ps1` — capture fail-closed on unstyled probe pair, inject unit contract, regressions.

## IMPLEMENTATION_HEAD / CLOSEOUT_RECORD_HEAD

| Label | SHA |
|-------|-----|
| **IMPLEMENTATION_HEAD** | _(commit below)_ |
| **CLOSEOUT_RECORD_HEAD** | _(if docs-only follow-up)_ |

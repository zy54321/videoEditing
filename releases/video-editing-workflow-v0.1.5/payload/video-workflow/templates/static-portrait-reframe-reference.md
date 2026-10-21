# Static Portrait Reframe Runtime (v1)

| Field | Value |
|-------|--------|
| Policy ID | `static-portrait-reframe.v1` |
| L1 route | `visual.reframe.static` |
| Fill | `cover_static_center_zoom_only` |

## Problem this fixes

Do **not** combine heavy symmetric `CropLeft`/`CropRight` with large `ZoomX`/`ZoomY` for 16:9→9:16 fill. That double-crops and over-magnifies.

## Algorithm

Uses `portrait_fill_qa.shot_portrait_contract`:

- `target_zoom_cover` from source vs 1080×1920 canvas
- Crop reset to **0** on all edges
- `ZoomX` = `ZoomY` = `target_zoom_cover` when `portrait_fill_required`

## Tools

| Step | CLI |
|------|-----|
| Plan from timeline probe JSON | `build-static-portrait-reframe-plan.py --probe <probe.json> --out <plan.json>` |
| Plan orchestration | `invoke-static-portrait-reframe.ps1 -WorkspaceRoot <ws>` (writes `production/static-portrait-reframe-plan.json`) |
| Apply in Resolve | `-Apply` on orchestrator, or `apply-static-portrait-reframe-bulk.py --plan …` (requires `DAVINCI_RESOLVE_MCP_ROOT`) |
| MCP alternative | `timeline.bulk_set_item_properties` with `plan.bulk_ops` |

**Deprecated (do not use in production):** media-local `build_reframe_bulk.py` (hard-coded crop 0.345 + zoom). Not part of the release package; use this policy instead.

## QA

- `black-bar-qa.py` on delivered MP4
- `portrait_fill_qa` contracts embedded in plan JSON

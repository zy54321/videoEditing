# Production Repair Step 3A — Shared Asset Library V1 Foundation Closeout

**Date:** 2026-09-24  
**Starting HEAD:** `e52c4555a64d2e618d4467bc38f60f51eb1d8f49`

---

## Shared Asset root

`E:\03_Media\02_Video\Davinci\Astra\assets`

Parallel to dated Production folders (`YYYY-MM-DD/input|output`). Not inside any date folder.

---

## Directory skeleton (machine-local)

```text
assets\
├─ music\          (V1 ACTIVE)
├─ sfx\            (reserved)
├─ video\          (reserved)
├─ images\         (reserved)
├─ overlays\       (reserved)
└─ catalog\
   ├─ music.yaml    (catalog authority — empty assets[] at init)
   └─ README.md
```

---

## Catalog authority

| Item | Location |
|------|----------|
| Runtime config | `video-workflow/runtime/shared-asset-library-config.yaml` |
| Schema | `video-workflow/templates/shared-asset-catalog.schema.yaml` |
| Metadata reference | `video-workflow/templates/shared-asset-music-metadata-reference.md` |
| Live catalog | `<shared_asset_root>/catalog/music.yaml` |

---

## Music metadata contract

Required: `asset_id`, `type=music`, `path` (relative), `title`, `duration`, `mood`, `energy`, `bpm`, `loopable`, `license.*`, `status`.

Status: `READY` | `UNVERIFIED` | `REJECTED` | `MISSING`

---

## License policy

- License fields are first-class; empty/missing → cannot be `READY`
- Production auto-select requires `license.commercial_use: true`
- No internet download → Production without catalog registration

---

## Music selection contract

Deterministic filter + rank: mood → energy → duration → loopable.  
Missing match → `MUSIC_ASSET_NOT_AVAILABLE` (asset supply gap, not `audio.music.place` failure).

---

## Tools

| Tool | Role |
|------|------|
| `tools/lib/shared_asset_library.py` | Core validate / filter / resolve |
| `tools/shared-asset-catalog-validate.py` | CLI validate |
| `tools/shared-asset-music-select.py` | CLI filter |
| `tools/shared-asset-resolve.py` | CLI `asset_id → path` |

Placement unchanged: `audio.music.place`, `audio.music.level_under_voice`.

---

## Runtime / Production

| Item | Value |
|------|-------|
| Resolve Runtime executed | **NO** |
| Production executed | **NO** |
| Music downloaded | **NO** |
| Release payload includes shared assets | **NO** |

---

## READY_FOR_STEP_3B

Register real licensed music into `catalog/music.yaml` + files under `music/`, then validate READY entries and integrate L3 Music Pass selection.

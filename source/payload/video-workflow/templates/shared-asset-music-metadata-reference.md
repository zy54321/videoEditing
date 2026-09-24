# Shared Asset Library — Music Metadata Contract (V1)

## Layer role

| Layer | Responsibility |
|-------|----------------|
| **Shared Asset Library** | `discover → filter → resolve path` by `asset_id` |
| **L3 Production** | Express mood/energy/duration needs; receive candidate or `MUSIC_ASSET_NOT_AVAILABLE` |
| **L1 Runtime** | `audio.music.place`, `audio.music.level_under_voice` — unchanged |

The library does **not** place audio on timeline.

---

## Catalog authority

Machine-local file:

```
<shared_asset_root>/catalog/music.yaml
```

Default root (runtime config): `video-workflow/runtime/shared-asset-library-config.yaml`

Schema: `video-workflow/templates/shared-asset-catalog.schema.yaml`

---

## Required fields (per music asset)

| Field | Requirement |
|-------|-------------|
| `asset_id` | Stable identifier; used in Production contract |
| `type` | Must be `music` |
| `path` | Relative to `shared_asset_root`; no `..` |
| `title` | Human-readable |
| `duration` | Seconds (number > 0) |
| `mood` | One of: `calm`, `curious`, `tense`, `warm`, `neutral` |
| `energy` | One of: `low`, `medium`, `high` |
| `bpm` | Number or null |
| `loopable` | Boolean |
| `license.type` | e.g. `royalty_free`, `original`, `licensed` |
| `license.source` | Provenance description |
| `license.commercial_use` | Boolean — required explicit value |
| `license.attribution_required` | Boolean — required explicit value |
| `source_url` | String or empty |
| `status` | `READY` \| `UNVERIFIED` \| `REJECTED` \| `MISSING` |

---

## License policy (first-class)

Before **READY**:

- `license.source` must be non-empty
- `license.commercial_use` must be explicit boolean
- `license.attribution_required` must be explicit boolean
- Production auto-selection requires `license.commercial_use: true`
- Missing license metadata → **cannot** be `READY`

**Forbidden:** internet download → immediate Production use without catalog registration.

---

## Status semantics

| Status | Meaning |
|--------|---------|
| `READY` | Metadata complete, license OK, file exists — selectable |
| `UNVERIFIED` | Registered but not cleared for Production |
| `REJECTED` | Do not use |
| `MISSING` | File absent or path invalid at validate time |

File existence alone does **not** imply `READY`.

---

## Selection contract (V1)

Filter parameters:

```
mood            optional exact match
energy          optional exact match
required_duration  optional minimum seconds coverage
commercial_use  default true for Production
loopable        optional require true
status          default READY only
```

Ranking (deterministic):

1. Status `READY` (filter gate)
2. Mood match (exact > none)
3. Energy match (exact > none)
4. Duration suitable (`duration >= required_duration` when set)
5. Loopable when required

No AI recommendation. No embedding search.

---

## Missing asset behavior

When BGM is required and no READY asset matches:

```
MUSIC_ASSET_NOT_AVAILABLE
```

This is an **asset supply gap**, not `audio.music.place` failure.

Workflow must not silently disable BGM or download unknown-copyright music.

---

## Production Brief binding

Prefer:

```yaml
assets:
  music:
    asset_id: music-calm-neutral-01
    path: ""   # resolved at runtime from library
```

Legacy direct `path` remains valid for Owner-supplied one-off files in `media.input`.

Do not hardcode Shared Asset absolute paths in L2 Style or L3 Skill.

# N02 V6 Subtitle Runtime Capability Audit

## Verified routes (in repo)

| Route | Status | Font family | Font weight | Stroke | Read-back |
|-------|--------|-------------|-------------|--------|-----------|
| `native_drt_subtitle_track_fields_blob_template` | **VERIFIED** | Unknown (captured blob) | Unknown | **VERIFIED** inject | Style-only blob, no per-field API |
| `project_db.set_subtitle_style` | **PARTIAL** | Writable in theory | Writable in theory | **Not writable** | Requires closed project + host `Project.db` path + `better-sqlite3` |
| Resolve scripting API | **UNAVAILABLE** | — | — | — | — |

## Open Sans Bold on host

| Check | Result |
|-------|--------|
| Layout preflight (`subtitle-layout-engine.ps1`) | **Open Sans not resolved** → fallback **Microsoft YaHei UI** |
| Timeline burn-in (V5 artifact) | Inherits V4 DRT stroke template; **no Bold apply step executed** |

## Stable capability verdict

| Gate | Result |
|------|--------|
| `SUBTITLE_RUNTIME_WEIGHT_CAPABILITY` | **FAIL / CAPABILITY_GAP** |
| Reason | No verified end-to-end route: **set weight → render burn-in → read back** without unverified Project.db surgery or new styled DRT capture with Open Sans Bold. |

## Allowed without Owner

- Final-artifact geometry QA (pixel extent on encoded MP4)
- Semantic wrap **PRECHECK** for future Bold application

## Blocked without Owner

- Automatic Project.db search/patch
- Claiming **SUBTITLE_FONT_WEIGHT = PASS** on current artifact

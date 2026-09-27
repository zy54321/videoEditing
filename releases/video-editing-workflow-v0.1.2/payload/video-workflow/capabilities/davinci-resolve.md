# DaVinci Resolve Capability Reference

**Layer:** L1 — lightweight capability / operator knowledge  
**Version:** V0.1  
**Discovery date:** 2026-09-21

---

## 1. Purpose

This document is the **L1 lightweight capability reference** for Video Editing Workflow V0.1.

It serves:

- L3 Production Workflow
- L2 Editing Strategy Skills

It does **not**:

- own the Runtime
- replace MCP documentation
- define genre editing aesthetics (L2)
- define production lifecycle (L3)

It records, per logical capability:

| Field | Meaning |
|-------|---------|
| Logical capability ID | Stable editorial concept |
| Current backend | How V0.1 implements it today |
| Capability status | Evidence-based status label |
| Preconditions | What must be true before write |
| Execution guidance | How L3 should request implementation |
| Verification requirements | Read-back / external checks after write |
| Fallback / blocker semantics | What to do when unavailable |

---

## 2. Capability Status Vocabulary

| Status | Definition |
|--------|------------|
| **VERIFIED** | Successfully executed in current Samuel MCP + Resolve environment with acceptable production outcome |
| **AVAILABLE_UNVERIFIED** | Current Runtime / tool schema / MCP docs expose the capability; this project has not fully validated end-to-end production effect |
| **UNKNOWN** | Insufficient evidence to confirm availability or effect |
| **UNAVAILABLE** | Current Runtime clearly cannot perform the action |
| **DEFERRED** | Out of V0.1 validation scope |

Forbidden wording: `probably`, `should work`, `likely supported`.

### Implementation Route Status (per-route, separate from logical capability)

| Route Status | Definition |
|--------------|------------|
| **VERIFIED** | This specific implementation path succeeded live with read-back and/or render verification |
| **AVAILABLE_UNVERIFIED** | Runtime exposes the path; not validated in this project |
| **FAILED** | Attempted in disposable validation; did not achieve acceptable outcome |
| **UNSAFE** | Known instability boundary; **do not retry** in automated production |
| **UNAVAILABLE** | Runtime does not expose this path |

A logical capability (e.g. `subtitle.create`) may be **VERIFIED** via one route while another route on the same capability is **UNSAFE** or **FAILED**.

**Stage 04A-R1 evidence date:** 2026-09-21 · Resolve Studio **21.1.0.14** · MCP **4.8.13**

---

## 3. Runtime Identity

| Field | Value |
|-------|-------|
| Runtime family | DaVinci Resolve |
| Current validated backend | `samuelgursky/davinci-resolve-mcp` |
| Reference Resolve build | DaVinci Resolve Studio **21.1** (per project background) |
| Discovery method (this stage) | Read-only MCP tool schema + MCP knowledge corpus + project validation records |
| Live Resolve probe | Stage 04A (terminated by crash) + Stage 04A-R1 (isolated recovery) — 2026-09-21 |

### Important

After Release install, **do not assume** every machine shares:

- Resolve version
- MCP version
- exposed tool set
- plugin / OFX set

Production **Preflight** must re-confirm Runtime on each session.

### Auxiliary validators (not DaVinci MCP capabilities)

| Tool | Role |
|------|------|
| FFmpeg / FFprobe | External file probe, frame extract, silence detect |
| Kokoro | External TTS (not in scope of this reference) |
| Agent vision / media_analysis | Semantic media understanding — **not** Resolve MCP native duty |

---

## 4. Exact Tool Names Policy

Logical capabilities are **portable**. MCP tool/action names are **implementation details**.

When this document records an exact MCP mapping, it is marked:

> **Implementation Detail — Not Portable Contract**

L2 and L3 must **not** depend on these names. Future adapters change L1 only.

Confirmed mappings below come from the **currently installed** `user-davinci-resolve` MCP tool schemas (read-only discovery, 2026-09-21).

---

## 5. Runtime Fallback Rules

When a capability is not available at execution time:

```
1. Another verified implementation on the same Runtime
2. Release-allowed auxiliary tool (e.g. FFprobe for render verify)
3. L2-defined legal degradation
4. BLOCK
```

**Forbidden:**

- Auto-install second MCP
- Auto-switch MCP implementation
- Auto-install plugins / OFX
- Unverified GUI automation reported as success

Report blockers as: `CAPABILITY_UNAVAILABLE`

---

## 6. Capability Categories

### A. Project

| Logical ID | Description | Status | N02 V0.1 | Verify Method |
|------------|-------------|--------|----------|---------------|
| `project.inspect` | Read current project identity and snapshot | **VERIFIED** | Required | `project_manager` `get_current`, `snapshot` |
| `project.create` | Create new project | **VERIFIED** | Required | Project exists, correct name/id |
| `project.open` | Load project by name | **VERIFIED** | Required | `get_current` matches Brief |
| `project.save` | Persist project | **VERIFIED** | Required | Save succeeds; re-open state consistent |

**Preconditions:** Resolve connected; correct database/folder context.

**Execution notes:** Use `project_manager.snapshot` before planning destructive work.

**Implementation Detail — Not Portable Contract:**

- `project_manager` `action=get_current|snapshot|create|load|save`

---

### B. Media

| Logical ID | Description | Status | N02 V0.1 | Verify Method |
|------------|-------------|--------|----------|---------------|
| `media.import` | Import files into Media Pool | **VERIFIED** | Required | Imported clip count; clip IDs returned |
| `media.inspect` | Read clip metadata / properties / duration | **VERIFIED** | Required | `media_pool_item` `get_clip_property`, `probe_clip_properties` |
| `media.duration` | Determine source duration | **VERIFIED** | Required | Property read-back vs FFprobe |
| `media.metadata` | Read/write clip metadata | **AVAILABLE_UNVERIFIED** | Optional | Metadata key read-back |

**Semantic media understanding** (content category, slow-motion appearance, subject relevance) is **not** a native Resolve MCP duty. It belongs to:

- `media_analysis` (FFprobe, vision, strata)
- Agent inspection of extracted frames

Filename alone is **not** semantic evidence.

**Implementation Detail — Not Portable Contract:**

- `media_pool` `safe_import_media` / `import_media`
- `media_pool_item` `get_clip_property`, `get_metadata`
- `media_analysis` `analyze_clip`, `extract_frames` (auxiliary)

---

### C. Timeline

| Logical ID | Description | Status | N02 V0.1 | Verify Method |
|------------|-------------|--------|----------|---------------|
| `timeline.inspect` | Read timeline identity, structure, items | **VERIFIED** | Required | `timeline` `get_current`, `probe_timeline_structure` |
| `timeline.create` | Create new timeline | **VERIFIED** | Required | Timeline name/id; set as current |
| `timeline.select` | Set current timeline | **VERIFIED** | Required | `get_current` read-back |
| `timeline.settings` | Read/write timeline settings (resolution, fps) | **AVAILABLE_UNVERIFIED** | Required | Settings read-back; fps used for frame math |
| `timeline.duration` | Read timeline start/end/duration | **VERIFIED** | Required | `get_start_frame`, `get_end_frame`, gap detection |
| `timeline.track_inspect` | List tracks and items | **VERIFIED** | Required | `get_items`, `detect_gaps_overlaps` |

**Preconditions (all timeline writes):** Correct project open; correct timeline selected; timeline id/name matches Brief.

**Implementation Detail — Not Portable Contract:**

- `media_pool` `create_timeline`, `create_timeline_from_clips`
- `timeline` `set_current`, `get_setting`, `set_setting`, `probe_timeline_structure`, `detect_gaps_overlaps`

---

### D. Clip Assembly

| Logical ID | Description | Status | N02 V0.1 | Verify Method |
|------------|-------------|--------|----------|---------------|
| `clip.assemble` | Append/insert clips on timeline | **VERIFIED** | Required | Item count; `timeline_item_id` read-back |
| `clip.trim` | Adjust clip timeline extent | **AVAILABLE_UNVERIFIED** | Required | `get_start`/`get_end` read-back |
| `clip.source_range` | Set/read source in/out | **VERIFIED** | Required | `get_source_start_frame`/`get_source_end_frame` |
| `clip.timeline_range` | Read timeline record range | **VERIFIED** | Required | Frame-accurate read-back at timeline fps |
| `clip.move` | Reposition clip on timeline | **AVAILABLE_UNVERIFIED** | Optional | Position read-back |
| `clip.delete_or_replace` | Remove or overwrite clips | **AVAILABLE_UNVERIFIED** | Repair | Gap/overlap inspection after delete |

**Frame alignment:** Always use timeline fps for record frames; source frames use source fps.

**Gap risk:** After assembly/trim/speed, run `detect_gaps_overlaps` and visual QA.

**Implementation Detail — Not Portable Contract:**

- `media_pool` `append_to_timeline` (clip_ids / clip_infos)
- `timeline` `duplicate_clips`, `ripple_insert`, `lift_range`
- `timeline_item` `get_start`, `get_end`, `get_source_*`

---

### E. Transform / Framing

**N02 MUST** — 9:16 framing was an exposed production gap.

| Logical ID | Description | Status | N02 V0.1 | Verify Method |
|------------|-------------|--------|----------|---------------|
| `clip.scale` | Adjust ZoomX/ZoomY (fill frame) | **VERIFIED** | **MUST** | `get_transform` read-back (ZoomX/Y=1.35, Stage 04A) |
| `clip.position` | Adjust Pan/Tilt for subject | **VERIFIED** | **MUST** | `get_transform` read-back (Pan=0.15, Tilt=-0.1, Stage 04A) |
| `clip.rotation` | Rotation if needed | **AVAILABLE_UNVERIFIED** | Optional | `get_transform` read-back |
| `clip.crop` | Crop left/right/top/bottom | **AVAILABLE_UNVERIFIED** | Optional | `get_crop` read-back + visual QA |

**Can current Runtime:**

1. Change Zoom / Scale — **yes** via `timeline_item` `set_transform` (schema exposes ZoomX/ZoomY)
2. Change Position X/Y — **yes** via Pan/Tilt
3. Read-back Inspector values — **yes** via `get_transform` / `get_crop`

**Caveat:** API read-back success ≠ subject-safe framing. Visual verification required (`timeline_frame` capture or render sample).

**Implementation Detail — Not Portable Contract:**

- `timeline_item` `action=set_transform|get_transform|set_crop|get_crop`

---

### F. Speed / Motion

**N02 MUST** — stock slow motion was an exposed production gap.

| Logical ID | Description | Status | N02 V0.1 | Verify Method |
|------------|-------------|--------|----------|---------------|
| `clip.speed_change` | Apply speed / retime to clip | **VERIFIED** | **MUST** | `get_speed` 150% read-back; duration 144→96; gap clean after reposition (Stage 04A) |
| `clip.retime_mode` | Nearest / optical flow / frame blend | **UNKNOWN** | Optional | `get_retime` read-back |
| `mixed_fps.cadence_analyze` | Assess mixed source fps vs timeline cadence risk | **VERIFIED** | **MUST** (N02 V2) | FFprobe per-clip fps/duration + motion-risk classification + Safe Cadence Policy (08A.1) |
| `mixed_fps.interpolation` | Optical flow / frame interpolation retime | **UNKNOWN** | Optional | **Not** N02 V2 blocker; use Safe Cadence Degradation instead |

**L1 responsibility:** implement a speed factor **decided by L2** — not preset 1.4× / 2×.

**After speed change verify:**

- clip timeline duration
- source range integrity
- timeline gaps
- audio behavior (if source clip carries audio)
- motion naturalness (visual QA — not API-only)

**Implementation Detail — Not Portable Contract:**

- `timeline_item` `action=set_speed|get_speed|set_retime|get_retime`

---

### G. Transition

**N02 MUST** — hard-cut stiffness was an exposed gap.

| Logical ID | Description | Status | N02 V0.1 | Verify Method |
|------------|-------------|--------|----------|---------------|
| `transition.available` | Discover transition types | **UNKNOWN** | Required | MCP/docs enumeration not confirmed this stage |
| `transition.apply` | Apply transition between adjacent clips | **VERIFIED** | **MUST** | Via `native_drt_transition` (Stage 04A-R2) |
| `transition.duration` | Set transition length in frames | **VERIFIED** | **MUST** | DRT `durationFrames: 6` authored + read-back on import |
| `transition.remove_or_replace` | Repair incorrect transition | **UNKNOWN** | Repair | Post-change integrity |

**Preconditions:** Adjacent clips; sufficient handles; known timeline fps.

**Verify:** No gap; no black frame; timeline duration integrity.

**Note:** Timeline edit kernel documents **no public transition clone API** — transitions are apply/remove surfaces, not fully introspectable in all builds.

**Implementation Detail — Not Portable Contract:**

- `timeline_item` `action=add_transition` (Resolve 21.1+ per schema; requires `options` dict wrapper)

**Implementation Routes — `transition.apply`:**

| Route | Status | Evidence / Rule |
|-------|--------|-----------------|
| `live_api_add_transition` | **FAILED** | R1: `options must be a non-empty dictionary`. Not retried in R2 (not N02 gate blocker). |
| `native_drt_transition` | **VERIFIED** | R2: `drt.assemble` → `media_pool.import_timeline` → Cross Dissolve read-back (6 frames, no gaps) → `transition-test.mp4` 1080×1920 render. |

---

### H. Transcription

| Logical ID | Description | Status | N02 V0.1 | Verify Method |
|------------|-------------|--------|----------|---------------|
| `transcription.generate` | Generate clip/folder transcription | **VERIFIED** | Required | Transcription job success; segments present |
| `transcription.read` | Read transcription with timestamps | **VERIFIED** | Required | `get_transcription` segments/words |

**Authority rule:** ASR/transcription is **not** Frozen Script authority. Align to frozen text for proper nouns.

**Implementation Detail — Not Portable Contract:**

- `folder` / `media_pool_item` `transcribe_audio`
- `media_pool_item` `get_transcription`
- `timeline` `get_transcript` (timeline subtitle track — separate from clip transcription)

---

### I. Subtitle

**N02 MUST** — subtitles were missing from standard production flow.

| Logical ID | Description | Status | N02 V0.1 | Verify Method |
|------------|-------------|--------|----------|---------------|
| `subtitle.generation` | Auto-generate captions from audio | **AVAILABLE_UNVERIFIED** | Optional | Subtitle track populated |
| `subtitle.import` | Import SRT / external subtitle media | **VERIFIED** | **MUST** | Pool import only; live timeline placement via SRT append is **UNSAFE** |
| `subtitle.create` | Place subtitles on timeline | **VERIFIED** | **MUST** | Via `native_drt_subtitles` route (R1); not via live SRT append |
| `subtitle.track` | Create/manage subtitle track | **VERIFIED** | **MUST** | Subtitle track populated after DRT import |
| `subtitle.line_break_control` | Explicit cue splits + `\n` line breaks in authored text | **VERIFIED** | **MUST** (N02 V2) | Stage 08A.1: `drt.assemble` `spec.subtitles[]` → 4-cue transcript with 2-line cue → burn-in render visual |
| `subtitle.safe_text_width` | Avoid horizontal overflow via semantic split + line heuristic | **AVAILABLE_UNVERIFIED** | **MUST** (N02 V2) | L1 deterministic preflight (`subtitle-layout-preflight.ps1`) exists (08E-A); Resolve burn-in parity not validated |
| `subtitle.position` | Per-cue position / safe-area API control | **UNKNOWN** | Optional | Not required for functional layout |
| `subtitle.render.readability_stroke` | Production-safe white text + dark outer stroke on native DRT track | **VERIFIED** | **MUST** (readability) | Repair Step 5 Route A: gold standard Subtitle Track `FieldsBlob` capture/inject + burn-in deliver (light + busy) visual QA |
| `subtitle.visual_style` | Font, outline, background, animation | **UNKNOWN** | Optional | **Not** N02 V2 blocker; `subtitle.create` VERIFIED ≠ visual style VERIFIED; prefer `subtitle.render.readability_stroke` for production-safe stroke scope |
| `subtitle.keyword_emphasis` | Per-cue keyword styling | **AVAILABLE_UNVERIFIED** | Optional | Isolated StyledTextCLS SIZE route verified (B-R1); production nested-timeline overlay partial only (08E-FINAL); native DRT fallback VERIFIED |
| `subtitle.style` | Legacy alias — prefer `subtitle.visual_style` | **UNKNOWN** | Optional | Style read-back not confirmed |
| `subtitle.timing` | Verify cue timing vs narration | **AVAILABLE_UNVERIFIED** | **PRODUCTION_QA** | `get_transcript` cues vs plan; checked in final QA, not a Capability Gate blocker |
| `subtitle.edit` | Adjust cue text/timing programmatically | **UNKNOWN** | Repair | No confirmed write surface this stage |

**Do not conflate:** "subtitles can be imported" ≠ "all subtitle styling is API-controllable".

**Implementation Routes — `subtitle.keyword_emphasis` (v1 — SIZE only):**

| Route | Status | Evidence / Rule |
|-------|--------|-----------------|
| `textplus_styledtextcls_import_comp` | **VERIFIED (isolated)** | Standalone Text+ title: materialized runs → generator → `.setting` → `import_comp` (B10–B12). **Not** production overlay subtitle route. |
| `textplus_nested_timeline_overlay` | **PARTIAL** | Nested subtitle timeline on V2 over V1 background composites in `timeline_frame` (08E-FINAL probe). Missing: timing gates, lower-safe-zone final, CLS on overlay, Deliver/reload integrated probe. |
| `native_drt_subtitle_fallback` | **VERIFIED** | First Production degradation when Text+ overlay not final: semantic segmentation + native DRT subtitles (08A.1). |
| `fusion_comp.set_input(CharacterLevelStyling)` | **KNOWN_NON_WORKING_ROUTE** | API success but empty read-back, no visual SIZE change (Resolve 21.1.0.14 / MCP 4.8.13). **DO NOT SELECT IN PRODUCTION.** |
| `cls_color` / `cls_weight` | **NOT_VERIFIED** | Generator fail-closed (`CLS_COLOR_NOT_VERIFIED`, `CLS_WEIGHT_NOT_VERIFIED`) |

**Authority:** L2 decides *which* words to emphasize. L1 resolves layout + concrete size multipliers. Runtime backend serializes materialized `lines[].runs` only — no parallel substring/start/end truth.

**Implementation Routes — `subtitle.create`:**

| Route | Status | Evidence / Rule |
|-------|--------|-----------------|
| `live_api_srt_append` | **UNSAFE** | Resolve Studio 21.1.0.14 runtime crash on `media_pool.append_to_timeline` with `media_type: 3` (SRT). See `validation/capability-spike/CRASH-20260921.md`. **DO NOT RETRY IN AUTOMATED PRODUCTION.** |
| `native_auto_caption` | **AVAILABLE_UNVERIFIED** | `timeline_ai` `create_subtitles` / transcription path. Not suitable as default for Frozen Script precise captions. |
| `native_drt_subtitles` | **VERIFIED** | `drt.assemble` with `spec.subtitles[]` (`startFrame`, `durationFrames`, `text` with `\n`) → import → transcript + burn-in render (08A.1). `subtitlesSrt` alone may not author cues — prefer `subtitles[]`. Track style = unstyled stub unless separately seeded. |
| `native_drt_subtitle_readability_profile` | **CONTRACT_ONLY** | `runtime/native-drt-subtitle-readability-profile.yaml` — white + black outer stroke semantics; stroke automation **BLOCKED** until visual route verified |
| `project_db_set_subtitle_style` | **PARTIAL** | Advanced MCP: font family/size/weight/italic + normalized position only; **no outline/stroke**; requires styled track blob + closed project + host `better-sqlite3` |
| `subtitle_functional_fallback` | **VERIFIED** | Content → semantic segmentation → explicit `\n` → max 2 lines → split cue → render → `final-artifact-qa.ps1` visual check |

**Implementation Detail — Not Portable Contract:**

- `timeline` `add_track` (track_type=subtitle)
- `media_pool` `import_media` (SRT to pool only — **not** append to timeline)
- Advanced MCP `drt` `assemble` (`spec.subtitles` / `spec.subtitlesSrt`)
- `timeline` `import_timeline_checked`
- `timeline_ai` `create_subtitles`
- `timeline` `get_transcript`

---

### J. Titles / Graphics

| Logical ID | Description | Status | N02 V0.1 | Verify Method |
|------------|-------------|--------|----------|---------------|
| `title.insert` | Insert basic title/generator | **AVAILABLE_UNVERIFIED** | Optional | Item exists on timeline |
| `title.text_edit` | Set title text content | **AVAILABLE_UNVERIFIED** | Optional | `set_title_text` read-back |
| `graphics.fusion` | Fusion comp text/graphics | **AVAILABLE_UNVERIFIED** | DEFERRED | Rendered frame proof required |
| `graphics.lower_third` | Lower third template | **DEFERRED** | Not N02 MUST | — |

V0.1 N02 does not require heavy graphics automation.

**Implementation Detail — Not Portable Contract:**

- `timeline` `insert_title`, `set_title_text`
- `fusion_comp`, `timeline_item_fusion`

---

### K. Audio / Music

**N02 MUST** — background music integration was an exposed gap.

| Logical ID | Description | Status | N02 V0.1 | Verify Method |
|------------|-------------|--------|----------|---------------|
| `audio.import` | Import music/audio to pool | **VERIFIED** | **MUST** | Clip in pool |
| `audio.place_on_track` | Place audio on timeline track | **VERIFIED** | **MUST** | Item on audio track; range correct |
| `audio.trim` | Trim music segment | **AVAILABLE_UNVERIFIED** | Required | Source/timeline range read-back |
| `audio.volume` | Set clip/track volume (DaVinci-native) | **FAILED** | — | `set_audio` / `set_property` / `safe_set_audio_properties` all failed on WAV items (R1–R2) |
| `background_music_level_control` | Control music level under voice | **VERIFIED** | **MUST** | Via `ffmpeg_pre_attenuation` auxiliary route (R2) — not DaVinci-native automation |
| `audio.fade` | Fade in/out | **VERIFIED** | **MUST** | `set_fades` with `options` dict; read-back FadeIn=12, FadeOut=24 (R1) |
| `audio.track_management` | Add/manage audio tracks | **VERIFIED** | Required | Track count/names |
| `audio.mix_readback` | Read levels / mapping | **AVAILABLE_UNVERIFIED** | Required | `probe_audio_item`, listen test |
| `audio.ducking` | Auto-duck music under voice | **UNKNOWN** | Desired | No reliable auto-duck API confirmed |
| `music.library.search` | Search licensed/internal music library | **VERIFIED** | No | Step 3B-2: 4 Firefly WAV registered; mood/style/usage filter + rank via `shared-asset-music-select.py` (`shared-asset-library-3b2.ps1`) |
| `music.library.preview` | Preview library track | **UNAVAILABLE** | No | — |
| `music.library.select` | Select library track for production | **VERIFIED** | No | Step 3B-2: N02-like ranking validated; missing → `MUSIC_ASSET_NOT_AVAILABLE` |
| `music.library.resolve` | Resolve `asset_id` → absolute path under Shared Asset root | **VERIFIED** | No | Step 3B-2: `shared-asset-resolve.py`; 4 asset_id paths validated; traversal guarded |
| `voice.eq` | EQ on voice track/item | **AVAILABLE_UNVERIFIED** | Optional | Fairlight/audio MCP surfaces exist; not spike-validated 08A |
| `voice.compression` | Dynamics on voice | **AVAILABLE_UNVERIFIED** | Optional | — |
| `voice.pitch` | Pitch/timbre adjustment | **UNKNOWN** | Optional | — |
| `voice.effect` | Special voice FX | **UNKNOWN** | Optional | Not N02 blocker |

**Voice Master preservation:** Place voice on dedicated track; music on separate track; verify narration intelligibility after mix.

**Ducking:** L2 may require ducking; L1 reports **UNKNOWN** for automatic ducking — manual volume automation may be required.

**Implementation Routes — `background_music_level_control`:**

| Route | Status | Evidence / Rule |
|-------|--------|-----------------|
| `resolve_item_volume` | **FAILED** | `set_audio` / `set_property` / `safe_set_audio_properties` — write+readback false on WAV (R1–R2) |
| `ffmpeg_pre_attenuation` | **VERIFIED** | FFmpeg `volume=0.15` → `music_attenuated.wav` (mean −21.1 → −37.6 dB); import + place on A3; `integrated-test.mp4` render with voice on A2 (R2) |

**Auxiliary note:** `ffmpeg_pre_attenuation` is an **Auxiliary Runtime Fallback** — original music file remains immutable; derived asset imported to Resolve.

**Step 4A — `narration_short_v1` profile:** target **-16 LUFS** (±1 LU), true peak **≤ -1 dBTP**, LRA **7** (V1 engineering). Music uses measure-then-attenuate (fallback `0.15`). BGM continuous across narration pauses — **not** ducking. `audio.final.measure_loudness` / `audio.final.true_peak_qa` **VERIFIED**; `audio.final.normalize_or_adjust` / `FINAL_AUDIO_AUTO_REPAIR` **VERIFIED** (Step 4A-Repair — ffmpeg loudnorm two-pass post-render; max 1 attempt).

**Implementation Detail — Not Portable Contract:**

- `project_settings` `insert_audio`
- `media_pool` `append_to_timeline` (audio clip_infos)
- `timeline_item` `set_audio`, `get_audio`, `set_fades`, `get_fades`
- `timeline` `probe_audio_item`, `audio_mix_capability_report`

---

### L. Color

| Logical ID | Description | Status | N02 V0.1 | Verify Method |
|------------|-------------|--------|----------|---------------|
| `color.basic` | Light correction / matching | **VERIFIED** | **MUST** (N02 V2) | Stage 08A.1: Color page + `timeline_item_color.set_cdl` (array CDL) → node graph read-back (`safe_set_cdl` may fail on same host) |
| `color.lut` | Apply LUT | **AVAILABLE_UNVERIFIED** | Optional | Node/LUT state |
| `color.match` | Shot matching | **DEFERRED** | Not N02 MUST | — |

Resolve Color Page features ≠ MCP automation features. Do not mark VERIFIED without MCP-path validation.

**Implementation Detail — Not Portable Contract:**

- `timeline_item_color` `safe_set_cdl`, `safe_copy_grade`

---

### M. Effects / ResolveFX / Fusion / OFX

| Logical ID | Description | Status | N02 V0.1 | Verify Method |
|------------|-------------|--------|----------|---------------|
| `effects.resolvefx` | ResolveFX via API | **UNKNOWN** | DEFERRED | — |
| `effects.fusion` | Fusion comp effects on items | **AVAILABLE_UNVERIFIED** | DEFERRED | Rendered frame proof |
| `effects.ofx` | Third-party OFX | **UNKNOWN** | DEFERRED | No plugin install in V0.1 |

**Boundary:** DaVinci software capability ≠ MCP-exposed capability.

V0.1 does not maintain a plugin registry. **Do not auto-install OFX.**

---

### N. Render

| Logical ID | Description | Status | N02 V0.1 | Verify Method |
|------------|-------------|--------|----------|---------------|
| `render.configure` | Set format/codec/resolution/fps/output | **VERIFIED** | **MUST** | Job settings read-back |
| `render.start` | Start render job | **VERIFIED** | **MUST** | Job completes |
| `render.status` | Poll render progress | **VERIFIED** | Required | Status transitions |
| `render.verify` | Verify output file | **VERIFIED** | **MUST** | `verify_output` + FFprobe |

**Verified production profile:** H.264, **1080×1920**, 24 fps, AAC — **VERIFIED** (Stage 04A-R2: explicit `FormatWidth`/`FormatHeight` in render job settings).

**Render resolution note:** Timeline 1080×1920 alone is insufficient if Deliver page preset differs — R2 proved **explicit** `FormatWidth: 1080`, `FormatHeight: 1920` required in `prepare_render_job` settings.

**Post-render verify must check:**

- file exists
- duration
- resolution
- fps
- video stream
- audio stream
- codec/format

**FFprobe** is an **auxiliary validator**, not a DaVinci MCP capability.

**Implementation Detail — Not Portable Contract:**

- `render` `prepare_render_job`, `safe_set_render_settings`, `start`, `get_job_status`, `verify_output`

---

### O. QA / Inspection

| Logical ID | Description | Status | N02 V0.1 | Verify Method |
|------------|-------------|--------|----------|---------------|
| `qa.clip_ranges` | Read clip timeline/source ranges | **VERIFIED** | Required | `timeline_item` getters |
| `qa.track_state` | Inspect tracks/items | **VERIFIED** | Required | `probe_timeline_structure` |
| `qa.transform_readback` | Read transform/crop values | **AVAILABLE_UNVERIFIED** | Required | `get_transform` / `get_crop` |
| `qa.transition_state` | Inspect transitions | **UNKNOWN** | Required | Limited API introspection |
| `qa.subtitle_state` | Read subtitle cues | **AVAILABLE_UNVERIFIED** | Required | `get_transcript` |
| `qa.audio_state` | Read audio properties | **AVAILABLE_UNVERIFIED** | Required | `get_audio`, `probe_audio_item` |
| `qa.gap_detection` | Detect gaps/overlaps | **VERIFIED** | Required | `detect_gaps_overlaps` |
| `qa.visual_frame` | Capture rendered frame | **AVAILABLE_UNVERIFIED** | Required | `timeline_frame` capture |
| `final_render.frame_sampling` | Extract representative frames from MP4 (FFmpeg) | **VERIFIED** | **MUST** | Auxiliary: `ffmpeg -ss` frame extract; workflow temp only |
| `final_render.black_bar_check` | Detect letterbox/pillarbox in rendered frames | **VERIFIED** (detector) | **MUST** (N02 V2) | Step 4B: `black-bar-qa.py` cropdetect multiframe via `final-artifact-qa.ps1`; **production closure** requires repair loop — N02 V4 gap was gate/loop not detector absence |
| `final_render.subtitle_visual_qa` | Verify subtitle visibility/overflow in MP4 | **VERIFIED** | **MUST** (N02 V2) | Frame extract at cue midpoints + Agent vision; pipeline in `final-artifact-qa.ps1` (08A.1) |
| `final_render.audio_loudness_check` | Integrated LUFS + true peak on rendered artifact | **VERIFIED** | **MUST** (Step 4A) | `audio-loudness-qa.py` + `narration-short-v1-audio-mix-profile.yaml`; merged into `final-artifact-qa.ps1` JSON |

**N02 V4 loudness reference (offline, artifact unchanged):** Integrated ≈ **-24.8 LUFS**, True Peak ≈ **-5.84 dBTP** — below `narration_short_v1` target (-16 ±1 LU).

**`FINAL_AUDIO_AUTO_REPAIR`:** **VERIFIED** (Step 4A-Repair) — `final-artifact-audio-qa-repair.ps1` orchestrates `audio-loudness-qa.py` → `final-audio-loudness-repair.py` (loudnorm two-pass, video copy for MP4) → re-QA; **max 1** repair attempt; original artifact preserved until promote. Resolve clip gain (`audio.volume`) remains **FAILED** — repair is offline post-render only.

**Visual QA not replaceable by Inspector numbers alone:**

- subject cropped out
- unnatural slow motion
- visual repetition
- black frames

Use `timeline_frame` capture and/or short render samples.

---

## 7. Capability Matrix (Summary)

Full matrix spans logical capabilities in the master table below (Stage 08A expanded).

### Status Counts (master matrix)

Counts are **derived from Master Matrix rows** — do not maintain separate manual totals.

### Master Matrix

| Capability ID | Description | Status | N02 V0.1 | Verify Method |
|---------------|-------------|--------|----------|---------------|
| project.inspect | Project identity snapshot | VERIFIED | Yes | project_manager snapshot |
| project.create | Create project | VERIFIED | Yes | get_current |
| project.open | Load project | VERIFIED | Yes | get_current |
| project.save | Save project | VERIFIED | Yes | save + reopen |
| media.import | Import to Media Pool | VERIFIED | Yes | clip IDs |
| media.inspect | Clip metadata/properties | VERIFIED | Yes | probe_clip_properties |
| media.duration | Source duration | VERIFIED | Yes | property vs FFprobe |
| media.metadata | Metadata read/write | AVAILABLE_UNVERIFIED | No | read-back |
| timeline.inspect | Timeline structure | VERIFIED | Yes | probe_timeline_structure |
| timeline.create | Create timeline | VERIFIED | Yes | id/name |
| timeline.select | Set current timeline | VERIFIED | Yes | get_current |
| timeline.settings | Resolution/fps settings | AVAILABLE_UNVERIFIED | Yes | get_setting |
| timeline.duration | Timeline extent | VERIFIED | Yes | start/end frames |
| timeline.track_inspect | Track/item listing | VERIFIED | Yes | get_items |
| clip.assemble | Append/insert clips | VERIFIED | Yes | item read-back |
| clip.trim | Trim timeline extent | AVAILABLE_UNVERIFIED | Yes | get_start/end |
| clip.source_range | Source in/out | VERIFIED | Yes | get_source_* |
| clip.scale | Zoom for fill frame | VERIFIED | **MUST** | get_transform ZoomX/Y (Stage 04A) |
| clip.position | Pan/Tilt reposition | VERIFIED | **MUST** | get_transform Pan/Tilt (Stage 04A) |
| clip.speed | Speed / retime | VERIFIED | **MUST** | get_speed 150%; duration 144→96 (Stage 04A) |
| transition.apply | Apply transition | VERIFIED | **MUST** | native_drt_transition (R2) |
| transcription.generate | Generate transcription | VERIFIED | Yes | job/segments |
| transcription.read | Read transcription | VERIFIED | Yes | get_transcription |
| subtitle.track | Subtitle track | VERIFIED | **MUST** | track + items |
| subtitle.create | Place subtitles on timeline | VERIFIED | **MUST** | native_drt_subtitles route (R1) |
| subtitle.import | Import SRT to pool | VERIFIED | **MUST** | pool import; live append UNSAFE |
| subtitle.line_break_control | Explicit line breaks in cues | VERIFIED | **MUST** (V2) | drt.assemble subtitles[] + render burn-in (08A.1) |
| subtitle.safe_text_width | Semantic width heuristic | AVAILABLE_UNVERIFIED | **MUST** (V2) | split cue fallback; no API box |
| subtitle.position | Position API | UNKNOWN | Optional | not V2 blocker |
| subtitle.visual_style | Font/outline/background | UNKNOWN | Optional | not V2 blocker |
| subtitle.keyword_emphasis | Keyword styling | AVAILABLE_UNVERIFIED | Optional | Isolated CLS verified; production overlay not final |
| subtitle.timing | Cue timing verify | AVAILABLE_UNVERIFIED | PRODUCTION_QA | get_transcript; QA check, not gate blocker |
| mixed_fps.cadence_analyze | Mixed fps cadence risk | VERIFIED | **MUST** (V2) | FFprobe + Safe Cadence Policy (08A.1) |
| mixed_fps.interpolation | Optical flow retime | UNKNOWN | Optional | not V2 blocker |
| music.library.search | Music library search | VERIFIED | No | Step 3B-2 — 4 Firefly WAV; filter/rank validated |
| music.library.preview | Music library preview | UNAVAILABLE | No | — |
| music.library.select | Music library select | VERIFIED | No | Step 3B-2 N02-like ranking; missing → MUSIC_ASSET_NOT_AVAILABLE |
| music.library.resolve | asset_id → path | VERIFIED | No | Step 3B-2 — 4 asset_id resolve paths validated |
| voice.eq | Voice EQ | AVAILABLE_UNVERIFIED | Optional | schema exposed |
| voice.compression | Voice compression | AVAILABLE_UNVERIFIED | Optional | — |
| voice.pitch | Voice pitch | UNKNOWN | Optional | — |
| voice.effect | Voice FX | UNKNOWN | Optional | — |
| final_render.frame_sampling | MP4 frame extract | VERIFIED | **MUST** | FFmpeg auxiliary |
| final_render.black_bar_check | Black bar detection | VERIFIED | **MUST** (V2) | final-artifact-qa.ps1 (08A.1) |
| final_render.subtitle_visual_qa | Subtitle in MP4 | VERIFIED | **MUST** (V2) | frame extract + vision (08A.1) |
| audio.import | Import music | VERIFIED | **MUST** | pool clip |
| audio.place | Place on track | VERIFIED | **MUST** | audio item |
| audio.volume | DaVinci-native volume | FAILED | — | item-level write/readback false (R1–R2) |
| background_music_level_control | Music level under voice | VERIFIED | **MUST** | ffmpeg_pre_attenuation (R2) |
| audio.fade | Fade in/out | VERIFIED | **MUST** | get_fades 12/24 frames (R1) |
| audio.ducking | Auto ducking | UNKNOWN | Desired | — |
| color.basic | Light correction | VERIFIED | **MUST** (V2) | set_cdl array CDL on Color page (08A.1) |
| effects.resolvefx | ResolveFX automation | UNKNOWN | No | — |
| effects.fusion | Fusion effects | AVAILABLE_UNVERIFIED | No | render frame |
| effects.ofx | OFX plugins | UNKNOWN | No | — |
| render.configure | Render settings | VERIFIED | **MUST** | job settings |
| render.start | Start render | VERIFIED | **MUST** | job complete |
| render.verify | Output verification | VERIFIED | **MUST** | verify_output + FFprobe |

---

## 8. N02 Capability Gates (L1 Assessment)

### N02_V1_CAPABILITY_GATE (Stage 04A / N02 V1 baseline)

Historical gate for **N02 V1** only. Does **not** imply N02 V2 execution readiness.

| N02 V1 Requirement | Required Capability | Status | Evidence / Note |
|--------------------|---------------------|--------|-----------------|
| Motion normalization | `clip.speed_change` | **VERIFIED** | Stage 04A: 150% read-back |
| 9:16 framing | `clip.scale` + `clip.position` | **VERIFIED** (API) | Transform read-back; visual QA separate |
| Transitions | `transition.apply` | **VERIFIED** | `native_drt_transition` (R2) |
| Subtitles | `subtitle.create` | **VERIFIED** | `native_drt_subtitles` (R1); `live_api_srt_append` **UNSAFE** |
| Background music | `audio.*` + `background_music_level_control` | **VERIFIED** | FFmpeg attenuation route (R2) |
| Render | `render.configure` + `render.start` | **VERIFIED** | 1080×1920 @ 24fps (R2) |

```
N02_V1_CAPABILITY_GATE = PASS
```

### N02_V2_READINESS_GATE (Stage 08A.1 — execution readiness)

Must pass **before** real N02 V2 production. Documentation alone is insufficient.

| # | V2 P0 Requirement | Capability | Status | Evidence |
|---|-------------------|------------|--------|----------|
| A | Subtitle placement | `subtitle.create` | **VERIFIED** | native_drt_subtitles (R1+) |
| B | Line breaks / cue split | `subtitle.line_break_control` | **VERIFIED** | 08A.1 DRT `subtitles[]` + MP4 burn-in |
| C | Functional layout route | `subtitle.safe_text_width` + fallback | **AVAILABLE_UNVERIFIED** + fallback **VERIFIED** | Semantic split; no API width |
| D | Advanced subtitle style | `subtitle.visual_style` | **UNKNOWN** | **Not** V2 blocker |
| E | Mixed FPS analysis | `mixed_fps.cadence_analyze` | **VERIFIED** | FFprobe + policy (08A.1) |
| F | Interpolation | `mixed_fps.interpolation` | **UNKNOWN** | Safe degradation policy; **not** V2 blocker |
| G | Frame sampling | `final_render.frame_sampling` | **VERIFIED** | FFmpeg + `final-artifact-qa.ps1` |
| H | Subtitle visual QA pipeline | `final_render.subtitle_visual_qa` | **VERIFIED** | 08A.1 disposable render + vision |
| I | Black-bar detect | `final_render.black_bar_check` | **VERIFIED** (detector) | 4B `black-bar-qa.py` |
| I2 | Black-bar repair loop | `qa.visual.reframe_repair_loop` | **VERIFIED** (fixture) | 4B detect→reframe→re-QA disposable validation |
| I3 | Pacing heuristic QA | `qa.pacing.heuristic` | **VERIFIED** | 4B `pacing-qa.py` |
| J | Baseline color | `color.basic` | **VERIFIED** | `timeline_item_color.set_cdl` (08A.1) |
| K | Motion normalize | `clip.speed_change` | **VERIFIED** | Stage 04A |

```
N02_V2_READINESS_GATE = PASS
```

**Safe Cadence Degradation (no VERIFIED interpolation):**

1. Prefer clips matching timeline FPS
2. mismatch + low-motion → keep + Final Motion QA
3. mismatch + motion-heavy → prefer alternate source
4. abnormal slow motion → `clip.speed_change`
5. retime still unnatural → replace clip
6. Do **not** call UNKNOWN interpolation routes

**Crash record:** `validation/capability-spike/CRASH-20260921.md`  
**08A.1 evidence:** `validation/capability-spike/STAGE-08A1-n02-v2-execution-readiness.md`

---

## 9. What This Document Does Not Cover

- Second MCP (`CiprianSpiridon/davinci-resolve-mcp`) — research only
- MCP installation / `mcp.json` changes
- Plugin / OFX installation
- Premiere / FFmpeg-only backends (future L1 adapters)
- L2 editing aesthetics
- L3 workflow orchestration

---

## 10. Discovery Log (Stage 04)

| Step | Action | Result |
|------|--------|--------|
| 1 | Enumerate `user-davinci-resolve` MCP tools | 40+ tools cataloged from schema |
| 2 | Read `knowledge` topics index | 22 topics (kernels, guides, reference) |
| 3 | Read `timeline-edit-kernel` | Transition clone unsupported; transform copy partial |
| 4 | Stage 04A live spike | CAP-01~03 pass; CAP-04 fail; CAP-05 SRT append → **crash** |
| 5 | Stage 04A-R1 recovery | DRT subtitle **VERIFIED**; live transition/volume **FAILED** |
| 6 | Stage 04A-R2 closure | Vertical 1080×1920 render; DRT transition; FFmpeg music level; integrated render |
| 7 | Crash evidence | `validation/capability-spike/CRASH-20260921.md` |
| 8 | Stage 08A observational spike | `validation/capability-spike/STAGE-08A-observational-style.md` |

Next recommended action: **N02 V2** real production acceptance (Stage 08B) with motion normalization enforced and Final Artifact QA.

"""Resolve AppendToTimeline frame parity — authority is planned timeline_duration_frames."""
from __future__ import annotations

import math
from typing import Any, Dict, List, Tuple

from assembly_plan_frames import sec_to_frame

# Measured on Resolve 21.x (N02 V4 assembly readback): timeline item duration =
# floor(source_span * timeline_fps / source_fps) for AppendToTimeline clip_infos.
RESOLVE_DURATION_ROUND = "floor"


def resolve_timeline_duration_frames(source_span: int, source_fps: float, timeline_fps: float) -> int:
    if source_span <= 0:
        return 0
    return int(math.floor(source_span * float(timeline_fps) / float(source_fps)))


def source_span_for_timeline_duration(
    timeline_duration_frames: int,
    source_fps: float,
    timeline_fps: float,
) -> int:
    """Smallest source span whose Resolve-rounded timeline duration equals target."""
    target = int(timeline_duration_frames)
    if target <= 0:
        return 1
    for span in range(1, 500_000):
        if resolve_timeline_duration_frames(span, source_fps, timeline_fps) == target:
            return span
    raise ValueError(f"cannot resolve source span for {target} timeline frames")


def source_out_exclusive(
    source_in_frame: int,
    timeline_duration_frames: int,
    source_fps: float,
    timeline_fps: float,
) -> int:
    span = source_span_for_timeline_duration(timeline_duration_frames, source_fps, timeline_fps)
    return int(source_in_frame) + span


def build_contiguous_clip_infos(
    shots: List[Dict[str, Any]],
    *,
    timeline_fps: float = 24.0,
    voice_authority_frames: int | None = None,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], int]:
    """
    Returns (clip_infos, parity_rows, total_timeline_frames).
    parity_rows document planned vs requested Resolve mapping.
    """
    cursor = 0
    clip_infos: List[Dict[str, Any]] = []
    parity: List[Dict[str, Any]] = []
    enriched = list(shots)

    if voice_authority_frames is not None and enriched:
        planned_total = sum(int(s.get("timeline_duration_frames") or 0) for s in enriched)
        delta = int(voice_authority_frames) - planned_total
        if delta > 0:
            last = dict(enriched[-1])
            last["timeline_duration_frames"] = int(last.get("timeline_duration_frames") or 0) + delta
            last["voice_tail_pad_frames"] = delta
            enriched[-1] = last

    for shot in enriched:
        T = int(shot.get("timeline_duration_frames") or 0)
        sf = float(shot.get("source_fps") or 25.0)
        src_in = int(shot.get("source_in_frame") or sec_to_frame(float((shot.get("source_range") or {}).get("in_sec", 0)), sf))
        src_out_req = source_out_exclusive(src_in, T, sf, timeline_fps)
        span = src_out_req - src_in
        clip_infos.append(
            {
                "media_pool_item_id": shot.get("source_asset"),
                "start_frame": src_in,
                "end_frame": src_out_req,
                "record_frame": cursor,
                "track_index": 1,
            }
        )
        parity.append(
            {
                "shot_id": shot.get("shot_id"),
                "source_fps": sf,
                "timeline_fps": timeline_fps,
                "planned_source_in": src_in,
                "planned_source_out_exclusive": src_out_req,
                "planned_timeline_duration_frames": T,
                "resolve_requested_source_in": src_in,
                "resolve_requested_source_out_exclusive": src_out_req,
                "resolve_expected_timeline_duration_frames": resolve_timeline_duration_frames(span, sf, timeline_fps),
                "record_frame": cursor,
                "duration_formula": RESOLVE_DURATION_ROUND,
            }
        )
        cursor += T

    return clip_infos, parity, cursor


def parity_delta_summary(parity_rows: List[Dict[str, Any]], materialized: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for i, row in enumerate(parity_rows):
        mat = materialized[i] if i < len(materialized) else {}
        planned_t = int(row["planned_timeline_duration_frames"])
        runtime_t = int(mat.get("duration_frames") or mat.get("duration") or 0)
        row = {**row}
        row["runtime_timeline_duration_frames"] = runtime_t
        row["runtime_source_in"] = mat.get("source_start")
        row["runtime_source_out_exclusive"] = mat.get("source_end")
        row["delta_frames"] = runtime_t - planned_t
        out.append(row)
    return out

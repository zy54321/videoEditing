"""Frame-accurate fields for assembly plans (deterministic rounding)."""
from __future__ import annotations

import math
from typing import Any, Dict, List

DEFAULT_SOURCE_FPS = 25.0


def sec_to_frame(sec: float, fps: float) -> int:
    return int(math.floor(float(sec) * float(fps) + 1e-9))


def frame_to_sec(frame: int, fps: float) -> float:
    return float(frame) / float(fps)


def enrich_plan_frames(
    assembly_plan: Dict[str, Any],
    *,
    timeline_fps: float = 24.0,
    default_source_fps: float = DEFAULT_SOURCE_FPS,
) -> Dict[str, Any]:
    shots: List[Dict[str, Any]] = list(assembly_plan.get("shots") or [])
    record = 0
    enriched: List[Dict[str, Any]] = []
    for shot in shots:
        s = dict(shot)
        src_fps = float(s.get("source_fps") or default_source_fps)
        dur_sec = float(s.get("timeline_duration_sec") or 0)
        dur_frames = sec_to_frame(dur_sec, timeline_fps)
        if dur_frames < 1 and dur_sec > 0:
            dur_frames = 1
        s["timeline_fps"] = timeline_fps
        s["source_fps"] = src_fps
        s["timeline_start_frame"] = record
        s["timeline_duration_frames"] = dur_frames
        s["timeline_end_frame"] = record + dur_frames
        sr = s.get("source_range") or {}
        if isinstance(sr, dict) and "in_sec" in sr and "out_sec" in sr:
            in_f = sec_to_frame(float(sr["in_sec"]), src_fps)
            out_f = sec_to_frame(float(sr["out_sec"]), src_fps)
            if out_f <= in_f:
                out_f = in_f + max(1, sec_to_frame(dur_sec, src_fps))
            s["source_in_frame"] = in_f
            s["source_out_frame"] = out_f
        enriched.append(s)
        record += dur_frames
    plan = dict(assembly_plan)
    plan["fps"] = timeline_fps
    plan["shots"] = enriched
    plan["timeline_duration_frames"] = record
    return plan

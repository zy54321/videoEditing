"""Shared assembly shot timing, exemption, and source-range helpers."""
from __future__ import annotations

import copy
from typing import Any, Dict, List, Optional, Tuple

from assembly_plan_frames import sec_to_frame
from resolve_materialization_frames import build_contiguous_clip_infos

CONTINUITY_GAP_SEC = 1.0 / 24.0  # one frame @ 24fps default continuity tolerance

EXEMPT_REASON_TOKENS = frozenset({
    "intentional_callback",
    "comparison",
    "narrative_reason",
    "intentional_flash",
})


def assembly_fps(assembly_plan: Dict[str, Any]) -> float:
    fps = assembly_plan.get("fps") or assembly_plan.get("timeline_fps")
    if fps:
        return float(fps)
    return 24.0


def shot_timeline_duration_sec(shot: Dict[str, Any]) -> float:
    if "timeline_duration_sec" in shot:
        return float(shot["timeline_duration_sec"])
    if "timeline_duration" in shot:
        return float(shot["timeline_duration"])
    src = shot.get("source_range") or {}
    if isinstance(src, dict) and "in_sec" in src and "out_sec" in src:
        return float(src["out_sec"]) - float(src["in_sec"])
    return float(shot.get("duration_sec") or 0)


def shot_timeline_duration_frames(shot: Dict[str, Any], fps: float) -> int:
    if shot.get("timeline_duration_frames") is not None:
        return int(shot["timeline_duration_frames"])
    return max(0, int(round(shot_timeline_duration_sec(shot) * fps)))


def build_timed_shots(
    shots: List[Dict[str, Any]],
) -> Tuple[List[Dict[str, Any]], float]:
    cursor = 0.0
    timed: List[Dict[str, Any]] = []
    for shot in shots:
        if "timeline_start_sec" in shot:
            start = float(shot["timeline_start_sec"])
            dur = shot_timeline_duration_sec(shot)
        else:
            start = cursor
            dur = shot_timeline_duration_sec(shot)
        end = start + dur
        timed.append({**shot, "_start": start, "_end": end, "_dur": dur})
        cursor = end
    return timed, cursor


def is_editorial_exempt(shot: Dict[str, Any]) -> bool:
    if shot.get("reuse_exempt") or shot.get("pacing_exempt") or shot.get("micro_fragment_exempt"):
        return True
    if shot.get("intentional_flash"):
        return True
    editorial = str(shot.get("editorial_reason") or "").strip()
    if editorial:
        return True
    reuse_reason = str(shot.get("reuse_exempt_reason") or "").strip()
    if reuse_reason:
        return True
    for key in ("intentional_callback", "comparison", "narrative_reason"):
        if shot.get(key):
            return True
    return False


def is_micro_fragment(shot: Dict[str, Any], fps: float, max_frames: int, max_sec_fallback: float) -> bool:
    if is_editorial_exempt(shot):
        return False
    frames = shot_timeline_duration_frames(shot, fps)
    if frames <= max_frames:
        return True
    return shot_timeline_duration_sec(shot) <= max_sec_fallback


def source_range_bounds(shot: Dict[str, Any]) -> Optional[Tuple[float, float]]:
    src = shot.get("source_range") or {}
    if not isinstance(src, dict) or "in_sec" not in src or "out_sec" not in src:
        return None
    return float(src["in_sec"]), float(src["out_sec"])


def source_duration_sec(shot: Dict[str, Any]) -> Optional[float]:
    if shot.get("source_duration_sec") is not None:
        return float(shot["source_duration_sec"])
    return None


def validate_source_range(
    shot: Dict[str, Any],
    in_sec: float,
    out_sec: float,
    *,
    min_duration_sec: float = 0.04,
) -> Tuple[bool, Optional[str]]:
    if not shot.get("source_asset"):
        return False, "missing_source_asset"
    dur_avail = source_duration_sec(shot)
    if dur_avail is None:
        return False, "missing_source_duration_evidence"
    if in_sec < 0 or out_sec > dur_avail + 1e-6:
        return False, "source_range_out_of_bounds"
    span = out_sec - in_sec
    if span < min_duration_sec:
        return False, "source_range_insufficient_duration"
    return True, None


def approved_alternate_candidates(shot: Dict[str, Any]) -> List[Dict[str, Any]]:
    raw = shot.get("alternate_source_assets") or []
    out: List[Dict[str, Any]] = []
    for item in raw:
        if isinstance(item, str):
            out.append({"source_asset": item})
        elif isinstance(item, dict) and item.get("source_asset"):
            out.append(dict(item))
    return out


def pick_valid_approved_alternate(
    shot: Dict[str, Any],
    avoid: set,
) -> Optional[Dict[str, Any]]:
    need = shot_timeline_duration_sec(shot)
    for cand in approved_alternate_candidates(shot):
        asset = str(cand.get("source_asset") or "")
        if not asset or asset in avoid:
            continue
        sd = cand.get("source_duration_sec")
        if sd is not None and float(sd) < need - 1e-6:
            continue
        default = cand.get("source_range") or {}
        if isinstance(default, dict) and "in_sec" in default and "out_sec" in default:
            ok, _ = validate_source_range(
                {"source_asset": asset, "source_duration_sec": sd},
                float(default["in_sec"]),
                float(default["out_sec"]),
                min_duration_sec=need * 0.9,
            )
            if not ok:
                continue
        elif sd is None:
            continue
        return cand
    return None


def build_logical_source_spans(
    timed: List[Dict[str, Any]],
    *,
    continuity_gap_sec: float = CONTINUITY_GAP_SEC,
) -> List[Dict[str, Any]]:
    spans: List[Dict[str, Any]] = []
    i = 0
    while i < len(timed):
        shot = timed[i]
        if is_editorial_exempt(shot):
            i += 1
            continue
        src = str(shot.get("source_asset") or "")
        if not src:
            i += 1
            continue
        j = i + 1
        shot_ids = [shot.get("shot_id")]
        while j < len(timed):
            nxt = timed[j]
            if is_editorial_exempt(nxt):
                break
            if str(nxt.get("source_asset") or "") != src:
                break
            gap = float(nxt["_start"]) - float(timed[j - 1]["_end"])
            if gap > continuity_gap_sec:
                break
            shot_ids.append(nxt.get("shot_id"))
            j += 1
        spans.append({
            "source_asset": src,
            "start_sec": timed[i]["_start"],
            "end_sec": timed[j - 1]["_end"],
            "shot_ids": shot_ids,
        })
        i = j
    return spans


def frame_join_tolerance_sec(fps: float) -> float:
    """Legacy one-frame second tolerance. Continuous joins do not use it."""
    rate = float(fps) if fps and fps > 0 else 24.0
    return (1.0 / rate) + 1e-6


def beat_ids_of(shot: Dict[str, Any]) -> List[str]:
    raw = shot.get("beat_ids")
    found: List[str] = []
    if isinstance(raw, list):
        found.extend(str(item) for item in raw if str(item).strip())
    single = str(shot.get("beat_id") or "").strip()
    if single and single not in found:
        found.insert(0, single)
    return found


def has_explicit_cut_intent(shot: Dict[str, Any]) -> bool:
    if shot.get("jump_cut") or shot.get("intentional_flash"):
        return True
    for key in ("jump_cut_reason", "cut_reason", "editorial_reason"):
        if str(shot.get(key) or "").strip():
            return True
    return False


_HARD_CUT_LABELS = frozenset({"", "none", "cut", "hard_cut", "hard cut"})
_EFFECT_KEYS = (
    "transition",
    "transition_in",
    "transition_out",
    "effect",
    "effects",
    "fusion_comp",
    "resolve_fx",
)


def has_special_transition_or_effect(shot: Dict[str, Any]) -> bool:
    for key in _EFFECT_KEYS:
        value = shot.get(key)
        if value in (None, False):
            continue
        if isinstance(value, str) and value.strip().lower() in _HARD_CUT_LABELS:
            continue
        if isinstance(value, (list, dict)) and len(value) == 0:
            continue
        return True
    return False


_TRANSFORM_KEYS = (
    "reframe",
    "resolve_crop",
    "resolve_transform",
    "crop",
    "transform",
    "zoom",
    "zoom_x",
    "zoom_y",
)


def treatment_signature(shot: Dict[str, Any]) -> Dict[str, Any]:
    return {key: shot.get(key) for key in _TRANSFORM_KEYS if shot.get(key) is not None}


def treatments_compatible(left: Dict[str, Any], right: Dict[str, Any]) -> bool:
    return treatment_signature(left) == treatment_signature(right)


def playback_speed(shot: Dict[str, Any]) -> Optional[float]:
    for key in ("playback_speed", "speed"):
        if shot.get(key) is not None:
            return float(shot[key])
    bounds = source_range_bounds(shot)
    duration = shot_timeline_duration_sec(shot)
    if bounds is None or duration <= 0:
        return None
    return (bounds[1] - bounds[0]) / duration


def speeds_compatible(left: Dict[str, Any], right: Dict[str, Any]) -> bool:
    left_speed = playback_speed(left)
    right_speed = playback_speed(right)
    if left_speed is None or right_speed is None:
        return left_speed is None and right_speed is None
    return abs(left_speed - right_speed) <= 0.02


def timeline_frame_bounds(shot: Dict[str, Any], fps: float) -> Optional[Tuple[int, int]]:
    """Explicit finished-timeline frame span, or None when the shot has no position.

    End is exclusive. Seconds are quantized with the same floor used by frame enrichment.
    """
    has_frame = shot.get("timeline_start_frame") is not None
    has_sec = "timeline_start_sec" in shot
    if not has_frame and not has_sec:
        return None
    if has_frame:
        start = int(shot["timeline_start_frame"])
    else:
        start = sec_to_frame(float(shot["timeline_start_sec"]), fps)
    if has_frame and shot.get("timeline_end_frame") is not None:
        end = int(shot["timeline_end_frame"])
    elif shot.get("timeline_duration_frames") is not None:
        end = start + int(shot["timeline_duration_frames"])
    elif has_sec:
        end = sec_to_frame(float(shot["timeline_start_sec"]) + shot_timeline_duration_sec(shot), fps)
    else:
        end = start + shot_timeline_duration_frames(shot, fps)
    return start, end


def joined_timing(prev: Dict[str, Any], nxt: Dict[str, Any]) -> Dict[str, Any]:
    """Timing fields of a candidate join. Does not by itself prove the join is legal."""
    merged = copy.deepcopy(prev)
    merged["timeline_duration_sec"] = shot_timeline_duration_sec(prev) + shot_timeline_duration_sec(nxt)
    if "timeline_start_sec" in prev:
        merged["timeline_start_sec"] = prev.get("timeline_start_sec")
    if prev.get("timeline_start_frame") is not None:
        merged["timeline_start_frame"] = int(prev["timeline_start_frame"])
    if prev.get("timeline_duration_frames") is not None or nxt.get("timeline_duration_frames") is not None:
        merged["timeline_duration_frames"] = int(prev.get("timeline_duration_frames") or 0) + int(
            nxt.get("timeline_duration_frames") or 0
        )
        if merged.get("timeline_start_frame") is not None:
            merged["timeline_end_frame"] = int(merged["timeline_start_frame"]) + int(merged["timeline_duration_frames"])
    prev_bounds = source_range_bounds(prev)
    next_bounds = source_range_bounds(nxt)
    if prev_bounds and next_bounds:
        merged["source_range"] = {"in_sec": prev_bounds[0], "out_sec": next_bounds[1]}
    if prev.get("source_in_frame") is not None:
        merged["source_in_frame"] = int(prev["source_in_frame"])
    return merged


def _frame_ready_shot(shot: Dict[str, Any], timeline_fps: float) -> Dict[str, Any]:
    ready = dict(shot)
    if ready.get("timeline_duration_frames") is None:
        duration = shot_timeline_duration_sec(ready)
        frames = sec_to_frame(duration, timeline_fps)
        if frames < 1 and duration > 0:
            frames = 1
        ready["timeline_duration_frames"] = frames
    return ready


def resolve_clip_frames(shot: Dict[str, Any], timeline_fps: float) -> Dict[str, int]:
    """Frames `build_contiguous_clip_infos` would hand to Resolve for one shot."""
    ready = _frame_ready_shot(shot, timeline_fps)
    infos, _parity, total = build_contiguous_clip_infos([ready], timeline_fps=timeline_fps)
    info = infos[0]
    return {
        "start_frame": int(info["start_frame"]),
        "end_frame": int(info["end_frame"]),
        "record_frame": int(info["record_frame"]),
        "timeline_frames": int(total),
    }


def _source_fps_value(shot: Dict[str, Any]) -> Optional[float]:
    if shot.get("source_fps") is None:
        return None
    return float(shot["source_fps"])


def source_join_decision(
    prev: Dict[str, Any],
    nxt: Dict[str, Any],
    fps: float,
) -> Dict[str, Any]:
    """Decide whether two neighboring shots may become one continuous clip.

    Timeline positions must abut in frames. Source frames are the frames
    Resolve clip_info would use, and the merged clip must request that same span.
    A one-frame hole or overlap is not absorbed.
    """
    base = {
        "prev_shot_id": prev.get("shot_id"),
        "next_shot_id": nxt.get("shot_id"),
        "source_asset": prev.get("source_asset"),
        "source_range_replanned": False,
    }
    if str(prev.get("source_asset") or "") != str(nxt.get("source_asset") or "") or not prev.get("source_asset"):
        return {**base, "decision": "different_source"}
    if has_explicit_cut_intent(prev) or has_explicit_cut_intent(nxt):
        return {**base, "decision": "cut_intent"}
    if has_special_transition_or_effect(prev) or has_special_transition_or_effect(nxt):
        return {**base, "decision": "effect_or_transition"}
    if is_editorial_exempt(prev) or is_editorial_exempt(nxt):
        return {**base, "decision": "editorial_exempt"}
    if not treatments_compatible(prev, nxt):
        return {**base, "decision": "transform_conflict"}
    if not speeds_compatible(prev, nxt):
        return {**base, "decision": "speed_conflict"}

    prev_timeline = timeline_frame_bounds(prev, fps)
    next_timeline = timeline_frame_bounds(nxt, fps)
    if (prev_timeline is None) != (next_timeline is None):
        return {**base, "decision": "timeline_position_unproven"}
    if prev_timeline is not None and next_timeline is not None:
        timeline_delta = next_timeline[0] - prev_timeline[1]
        base["timeline_delta_frames"] = timeline_delta
        base["prev_timeline_frames"] = {"start": prev_timeline[0], "end": prev_timeline[1]}
        base["next_timeline_frames"] = {"start": next_timeline[0], "end": next_timeline[1]}
        if timeline_delta > 0:
            return {**base, "decision": "timeline_gap"}
        if timeline_delta < 0:
            return {**base, "decision": "timeline_overlap"}

    prev_bounds = source_range_bounds(prev)
    next_bounds = source_range_bounds(nxt)
    if prev_bounds is None or next_bounds is None:
        return {**base, "decision": "source_range_unproven", "source_range_replanned": False}
    base["gap_sec"] = next_bounds[0] - prev_bounds[1]
    if _source_fps_value(prev) != _source_fps_value(nxt):
        return {**base, "decision": "source_fps_conflict"}

    ready = [_frame_ready_shot(prev, fps), _frame_ready_shot(nxt, fps)]
    pair, _parity, _total = build_contiguous_clip_infos(ready, timeline_fps=fps)
    left = pair[0]
    right = pair[1]
    left_timeline = int(ready[0]["timeline_duration_frames"])
    right_timeline = int(ready[1]["timeline_duration_frames"])
    source_delta = int(right["start_frame"]) - int(left["end_frame"])
    merged = joined_timing(prev, nxt)
    merged_clip = resolve_clip_frames(merged, fps)
    base.update({
        "source_delta_frames": source_delta,
        "prev_clip": {
            "start_frame": int(left["start_frame"]),
            "end_frame": int(left["end_frame"]),
            "record_frame": int(left["record_frame"]),
            "timeline_frames": left_timeline,
        },
        "next_clip": {
            "start_frame": int(right["start_frame"]),
            "end_frame": int(right["end_frame"]),
            "record_frame": int(right["record_frame"]),
            "timeline_frames": right_timeline,
        },
        "merged_clip": merged_clip,
        "source_range_replanned": False,
    })
    if source_delta > 0:
        return {**base, "decision": "source_gap"}
    if source_delta < 0:
        return {**base, "decision": "source_overlap"}
    same_frames = (
        merged_clip["start_frame"] == int(left["start_frame"])
        and merged_clip["end_frame"] == int(right["end_frame"])
        and merged_clip["timeline_frames"] == left_timeline + right_timeline
        and int(right["record_frame"]) == int(left["record_frame"]) + left_timeline
    )
    if not same_frames:
        return {**base, "decision": "frame_inconsistent"}
    return {**base, "decision": "merge"}

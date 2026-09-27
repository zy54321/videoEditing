"""Shared assembly shot timing, exemption, and source-range helpers."""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

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

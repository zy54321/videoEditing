"""Portrait fill QA — distinguish thin bars vs landscape letterbox on 9:16 canvas."""
from __future__ import annotations

import math
from typing import Any, Dict, Optional, Tuple

TARGET_W = 1080
TARGET_H = 1920
TARGET_AR = TARGET_W / TARGET_H


def zoom_fill_cover(source_w: int, source_h: int, target_w: int = TARGET_W, target_h: int = TARGET_H) -> float:
    if source_w <= 0 or source_h <= 0:
        return 1.0
    scale_fit = min(target_w / source_w, target_h / source_h)
    scale_cover = max(target_w / source_w, target_h / source_h)
    if scale_fit <= 0:
        return 1.0
    return scale_cover / scale_fit


def source_aspect_ratio(source_w: int, source_h: int) -> float:
    return float(source_w) / float(source_h) if source_h else 1.0


def portrait_fill_required(source_w: int, source_h: int, tolerance: float = 0.02) -> bool:
    ar = source_aspect_ratio(source_w, source_h)
    return ar > (TARGET_AR + tolerance)


def portrait_crop_feasible(zoom: float, max_zoom: float = 2.5) -> Tuple[bool, str]:
    if zoom <= 1.05:
        return True, "already_portrait_or_near"
    if zoom > max_zoom:
        return False, f"cover_zoom_{zoom:.2f}_exceeds_safe_{max_zoom}"
    return True, "static_center_crop_acceptable"


def classify_canvas_from_crop(
    frame_w: int,
    frame_h: int,
    crop_w: int,
    crop_h: int,
    crop_x: int,
    crop_y: int,
) -> Dict[str, Any]:
    bar_top = crop_y
    bar_bottom = frame_h - crop_y - crop_h
    bar_left = crop_x
    bar_right = frame_w - crop_x - crop_w
    occupancy = (crop_w * crop_h) / max(frame_w * frame_h, 1)
    v_bar = bar_top + bar_bottom
    h_bar = bar_left + bar_right
    v_frac = v_bar / max(frame_h, 1)
    max_edge = max(bar_top, bar_bottom, bar_left, bar_right)
    thin_px = 24
    large_frac = 0.12

    if occupancy >= 0.92 and max_edge <= thin_px:
        layout = "PORTRAIT_FILLED"
        bar_class = "NONE"
    elif v_frac >= large_frac and bar_left < thin_px and bar_right < thin_px:
        layout = "LETTERBOXED"
        bar_class = "LARGE_LETTERBOX" if v_frac >= 0.2 else "PARTIAL_CANVAS_FILL"
    elif h_frac := h_bar / max(frame_w, 1) >= large_frac:
        layout = "PILLARBOXED"
        bar_class = "LARGE_PILLARBOX"
    elif max_edge <= thin_px and v_bar > 0:
        layout = "PARTIAL_FILL"
        bar_class = "THIN_EDGE_BAR"
    elif occupancy < 0.85:
        layout = "PARTIAL_FILL"
        bar_class = "PARTIAL_CANVAS_FILL"
    else:
        layout = "PORTRAIT_FILLED"
        bar_class = "NONE"

    return {
        "layout_state": layout,
        "bar_classification": bar_class,
        "content_occupancy": round(occupancy, 4),
        "bars_px": {"top": bar_top, "bottom": bar_bottom, "left": bar_left, "right": bar_right},
        "vertical_bar_fraction": round(v_frac, 4),
    }


def shot_portrait_contract(
    shot_id: str,
    source_w: int,
    source_h: int,
    *,
    max_safe_zoom: float = 2.5,
) -> Dict[str, Any]:
    ar = source_aspect_ratio(source_w, source_h)
    z = zoom_fill_cover(source_w, source_h)
    req = portrait_fill_required(source_w, source_h)
    ok, reason = portrait_crop_feasible(z, max_safe_zoom)
    return {
        "shot_id": shot_id,
        "source_aspect_ratio": round(ar, 4),
        "portrait_fill_required": req,
        "portrait_crop_feasible": ok,
        "portrait_crop_reason": reason,
        "reframe_status": "STATIC_FILL" if req and ok else ("REFRAME_UNSAFE" if req and not ok else "NO_REFRAME"),
        "target_zoom_cover": round(z, 4),
        "fill_mode": "cover_static" if req else "native_fit",
    }

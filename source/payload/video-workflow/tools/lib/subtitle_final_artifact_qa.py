"""Subtitle geometry/readability on final encoded burn-in (heuristic pixel extent)."""
from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    from PIL import Image
except ImportError:
    Image = None  # type: ignore

SAFE_LEFT_PX = 72
SAFE_RIGHT_PX = 72
SUBTITLE_BAND_TOP_RATIO = 0.62


def extract_frame(video: Path, sec: float, out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-ss",
            f"{sec:.3f}",
            "-i",
            str(video),
            "-frames:v",
            "1",
            str(out),
        ],
        check=True,
        capture_output=True,
    )


def _luma(px: Tuple[int, int, int]) -> float:
    return 0.299 * px[0] + 0.587 * px[1] + 0.114 * px[2]


def measure_subtitle_extent(
    image_path: Path,
    bright_threshold: float = 200.0,
) -> Dict[str, Any]:
    if Image is None:
        return {"error": "PIL_UNAVAILABLE", "verdict": "VISUAL_CONFIRM_REQUIRED"}
    im = Image.open(image_path).convert("RGB")
    w, h = im.size
    y0 = int(h * SUBTITLE_BAND_TOP_RATIO)
    min_x, max_x = w, 0
    hits = 0
    for y in range(y0, h):
        for x in range(w):
            if _luma(im.getpixel((x, y))) >= bright_threshold:
                hits += 1
                min_x = min(min_x, x)
                max_x = max(max_x, x)
    if hits < 50:
        return {
            "verdict": "VISUAL_CONFIRM_REQUIRED",
            "reason": "insufficient_bright_pixels_in_subtitle_band",
            "frame_w": w,
            "frame_h": h,
        }
    extent_w = max_x - min_x + 1
    left_margin = min_x
    right_margin = w - max_x - 1
    geom_fail = left_margin < SAFE_LEFT_PX or right_margin < SAFE_RIGHT_PX
    return {
        "frame_w": w,
        "frame_h": h,
        "text_extent_px": extent_w,
        "left_margin_px": left_margin,
        "right_margin_px": right_margin,
        "verdict": "FAIL_GEOMETRY" if geom_fail else "PASS",
    }


def analyze_samples(video: Path, samples: List[Dict[str, Any]], work_dir: Path) -> Dict[str, Any]:
    rows = []
    fails = []
    visual = []
    for s in samples:
        png = work_dir / f"{s['id']}_{s['sec']:.2f}s.png"
        extract_frame(video, s["sec"], png)
        m = measure_subtitle_extent(png)
        row = {**s, "image": str(png), **m}
        rows.append(row)
        if m.get("verdict") == "FAIL_GEOMETRY":
            fails.append(s["id"])
        if m.get("verdict") == "VISUAL_CONFIRM_REQUIRED":
            visual.append(s["id"])

    geometry = "PASS" if not fails else "FAIL"
    readability = "PASS" if not visual else "VISUAL_CONFIRM_REQUIRED"
    if visual and fails:
        readability = "FAIL_READABILITY"
    return {
        "authority": "FINAL_ARTIFACT",
        "artifact": str(video),
        "samples": rows,
        "SUBTITLE_GEOMETRY_QA": geometry,
        "SUBTITLE_READABILITY_QA": readability,
        "failed_geometry_ids": fails,
        "visual_confirm_ids": visual,
    }

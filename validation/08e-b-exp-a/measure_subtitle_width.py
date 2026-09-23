#!/usr/bin/env python3
"""Measure subtitle text horizontal span from rendered frame (white text on dark bg)."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from PIL import Image


def measure(path: Path, frame_width: int = 1080, lum_threshold: int = 180) -> dict:
    img = Image.open(path).convert("RGB")
    w, h = img.size
    px = img.load()
    xs: list[int] = []
    ys: list[int] = []
    for y in range(h):
        for x in range(w):
            r, g, b = px[x, y]
            lum = int(0.299 * r + 0.587 * g + 0.114 * b)
            if lum >= lum_threshold:
                xs.append(x)
                ys.append(y)
    if not xs:
        return {
            "image": str(path),
            "image_width_px": w,
            "image_height_px": h,
            "measurable": False,
            "error": "NO_VISIBLE_TEXT",
        }
    left, right = min(xs), max(xs)
    top, bottom = min(ys), max(ys)
    width_px = right - left + 1
    return {
        "image": str(path),
        "image_width_px": w,
        "image_height_px": h,
        "measurable": True,
        "bbox_left_px": left,
        "bbox_right_px": right,
        "bbox_top_px": top,
        "bbox_bottom_px": bottom,
        "actual_width_px": width_px,
        "actual_height_px": bottom - top + 1,
        "actual_frame_ratio": round(width_px / frame_width, 6),
        "lum_threshold": lum_threshold,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("image")
    ap.add_argument("--frame-width", type=int, default=1080)
    ap.add_argument("--threshold", type=int, default=180)
    ap.add_argument("--out", help="Write JSON result path")
    args = ap.parse_args()
    result = measure(Path(args.image), args.frame_width, args.threshold)
    text = json.dumps(result, ensure_ascii=False, indent=2)
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
    print(text)
    return 0 if result.get("measurable") else 1


if __name__ == "__main__":
    sys.exit(main())

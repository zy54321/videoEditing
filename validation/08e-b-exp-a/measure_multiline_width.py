#!/usr/bin/env python3
"""Measure per-line horizontal spans for multi-line subtitle frames."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from PIL import Image


def measure_lines(path: Path, lum_threshold: int = 180, gap_rows: int = 8) -> dict:
    img = Image.open(path).convert("RGB")
    w, h = img.size
    px = img.load()
    row_has_bright: list[tuple[int, int, int]] = []
    for y in range(h):
        xs = []
        for x in range(w):
            r, g, b = px[x, y]
            lum = int(0.299 * r + 0.587 * g + 0.114 * b)
            if lum >= lum_threshold:
                xs.append(x)
        if xs:
            row_has_bright.append((y, min(xs), max(xs)))

    if not row_has_bright:
        return {"measurable": False, "error": "NO_VISIBLE_TEXT", "image": str(path)}

    lines: list[dict] = []
    group: list[tuple[int, int, int]] = []
    for row in row_has_bright:
        if not group:
            group = [row]
            continue
        if row[0] - group[-1][0] <= gap_rows:
            group.append(row)
        else:
            left = min(r[1] for r in group)
            right = max(r[2] for r in group)
            lines.append(
                {
                    "top_px": group[0][0],
                    "bottom_px": group[-1][0],
                    "left_px": left,
                    "right_px": right,
                    "width_px": right - left + 1,
                }
            )
            group = [row]
    if group:
        left = min(r[1] for r in group)
        right = max(r[2] for r in group)
        lines.append(
            {
                "top_px": group[0][0],
                "bottom_px": group[-1][0],
                "left_px": left,
                "right_px": right,
                "width_px": right - left + 1,
            }
        )

    max_line = max(lines, key=lambda ln: ln["width_px"])
    return {
        "image": str(path),
        "image_width_px": w,
        "image_height_px": h,
        "measurable": True,
        "line_count_detected": len(lines),
        "lines": lines,
        "max_line_width_px": max_line["width_px"],
        "lum_threshold": lum_threshold,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("image")
    ap.add_argument("--out")
    args = ap.parse_args()
    result = measure_lines(Path(args.image))
    text = json.dumps(result, ensure_ascii=False, indent=2)
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
    print(text)
    return 0 if result.get("measurable") else 1


if __name__ == "__main__":
    sys.exit(main())

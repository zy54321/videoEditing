#!/usr/bin/env python3
"""Fail-closed check: Deliver MarkIn/MarkOut must intersect Text+ clip active span."""
from __future__ import annotations

import argparse
import json
import sys


def check(clip_start: int, clip_end: int, mark_in: int, mark_out: int) -> dict:
    # clip_end is exclusive (Resolve timeline probe convention)
    active_start = clip_start
    active_end = clip_end - 1
    intersects = not (mark_out < active_start or mark_in > active_end)
    return {
        "clip_start": clip_start,
        "clip_end_exclusive": clip_end,
        "mark_in": mark_in,
        "mark_out": mark_out,
        "intersects_textplus_span": intersects,
        "ok": intersects,
        "error": None if intersects else "MARKIN_OUTSIDE_TEXTPLUS_ACTIVE_SPAN",
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--clip-start", type=int, required=True)
    ap.add_argument("--clip-end", type=int, required=True)
    ap.add_argument("--mark-in", type=int, required=True)
    ap.add_argument("--mark-out", type=int, required=True)
    ap.add_argument("--out")
    args = ap.parse_args()
    result = check(args.clip_start, args.clip_end, args.mark_in, args.mark_out)
    text = json.dumps(result, ensure_ascii=False, indent=2)
    if args.out:
        from pathlib import Path

        Path(args.out).write_text(text, encoding="utf-8")
    print(text)
    return 0 if result["ok"] else 2


if __name__ == "__main__":
    sys.exit(main())

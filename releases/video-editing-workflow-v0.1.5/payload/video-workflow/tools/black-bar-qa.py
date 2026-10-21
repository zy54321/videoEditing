#!/usr/bin/env python3
"""Multi-frame black-bar / pillarbox QA with static reframe suggestions."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

LIB = Path(__file__).resolve().parent / "lib"
sys.path.insert(0, str(LIB))

from black_bar_qa import (  # noqa: E402
    analyze_frame,
    analyze_frames,
    analyze_video,
    load_black_bar_profile,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Black-bar / reframe QA")
    parser.add_argument("target", type=Path, help="Video file or PNG frame")
    parser.add_argument("--profile", type=Path)
    parser.add_argument("--frames", nargs="*", type=Path, help="Additional frame paths for multi-frame QA")
    parser.add_argument("--work-dir", type=Path)
    args = parser.parse_args()

    payload = Path(__file__).resolve().parents[1]
    profile_path = args.profile or (payload / "runtime" / "black-bar-reframe-qa-profile.yaml")
    profile = load_black_bar_profile(profile_path.resolve())
    target = args.target.resolve()

    if args.frames:
        frame_paths = [target] + [p.resolve() for p in args.frames]
        result = analyze_frames(frame_paths, profile)
    elif target.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}:
        result = analyze_frames([target], profile)
    else:
        result = analyze_video(target, profile, args.work_dir)

    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result.get("ok") else 2


if __name__ == "__main__":
    raise SystemExit(main())

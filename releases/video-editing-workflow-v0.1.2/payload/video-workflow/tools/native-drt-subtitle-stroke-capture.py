#!/usr/bin/env python3
"""Capture styled Native Subtitle EffectFiltersBA template from baseline vs styled DRT pair."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

LIB = Path(__file__).resolve().parent / "lib"
sys.path.insert(0, str(LIB))

from native_subtitle_stroke_template import capture_from_pair, save_template_manifest  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Diff baseline vs UI-styled DRT subtitle track blob")
    parser.add_argument("baseline_drt", type=Path, help="Unstyled native subtitle DRT export")
    parser.add_argument("styled_drt", type=Path, help="UI outer-stroke styled DRT export (same structure)")
    parser.add_argument("--template-dir", type=Path)
    args = parser.parse_args()

    payload = Path(__file__).resolve().parents[1]
    template_dir = args.template_dir or (payload / "runtime" / "native-drt-subtitle-stroke-template")

    capture = capture_from_pair(args.baseline_drt.resolve(), args.styled_drt.resolve())
    manifest = save_template_manifest(template_dir.resolve(), capture)
    capture["manifest"] = str(manifest.resolve())
    print(json.dumps(capture, indent=2, ensure_ascii=False))
    return 0 if capture.get("template_valid") else 2


if __name__ == "__main__":
    raise SystemExit(main())

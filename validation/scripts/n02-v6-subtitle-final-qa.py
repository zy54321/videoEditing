#!/usr/bin/env python3
"""Final-artifact subtitle QA for N02 (geometry authority on encoded MP4)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LIB = ROOT / "source/payload/video-workflow/tools/lib"
sys.path.insert(0, str(LIB))

from subtitle_final_artifact_qa import analyze_samples  # noqa: E402

VIDEO = Path(r"E:\03_Media\02_Video\Davinci\Astra\2026-09-21\output\N02_V5.mp4")
OUT = ROOT / "validation/n02-v6-subtitle-final-qa.json"
FRAMES = ROOT / "validation/n02-v6-subtitle-final-frames"

SAMPLES = [
    {"id": "short_single", "sec": 8.5, "role": "short_single_line"},
    {"id": "wide_clinic", "sec": 29.0, "role": "wide_single_line"},
    {"id": "two_line_money", "sec": 48.0, "role": "two_line"},
    {"id": "light_bg", "sec": 12.0, "role": "light_background"},
    {"id": "busy_bg", "sec": 35.0, "role": "busy_background"},
    {"id": "dark_bg", "sec": 65.0, "role": "dark_background"},
    {"id": "near_edge", "sec": 29.0, "role": "near_safe_area"},
]


def main() -> int:
    result = analyze_samples(VIDEO, SAMPLES, FRAMES)
    result["SUBTITLE_FONT_WEIGHT"] = "CAPABILITY_GAP"
    result["SUBTITLE_RUNTIME_WEIGHT_CAPABILITY"] = "FAIL"
    result["font_requested"] = "Open Sans Bold"
    result["actual_final_applied_font"] = "unknown_inherited_v4_drt"
    result["actual_final_applied_weight"] = "unknown_regular_or_ui_default"
    result["precheck_note"] = "Layout preflight is PRECHECK_ONLY; not used as PASS authority."
    result["SUBTITLE_QA"] = (
        "FAIL"
        if result["SUBTITLE_GEOMETRY_QA"] == "FAIL"
        else "PARTIAL_CAPABILITY_GAP"
    )
    OUT.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({k: result[k] for k in result if "SUBTITLE" in k or k == "failed_geometry_ids"}, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

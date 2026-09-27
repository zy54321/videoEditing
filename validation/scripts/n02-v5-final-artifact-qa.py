#!/usr/bin/env python3
"""N02 V5 final encoded artifact QA — portrait fill, layout, black-bar, audio."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LIB = ROOT / "source/payload/video-workflow/tools/lib"
sys.path.insert(0, str(LIB))

from black_bar_qa import analyze_frame, load_black_bar_profile  # noqa: E402
from portrait_fill_qa import classify_canvas_from_crop  # noqa: E402
from audio_loudness_qa import measure_loudness  # noqa: E402

VIDEO = Path(r"E:\03_Media\02_Video\Davinci\Astra\2026-09-21\output\N02_V5.mp4")
FRAMES_DIR = ROOT / "validation/n02-v5-final-artifact-frames"
OUT_JSON = ROOT / "validation/n02-v5-final-artifact-qa.json"
PROFILE = ROOT / "source/payload/video-workflow/runtime/black-bar-reframe-qa-profile.yaml"

SAMPLES = [
    {"id": "opening", "sec": 1.0, "role": "opening"},
    {"id": "first_landscape", "sec": 2.5, "role": "first_landscape"},
    {"id": "office", "sec": 29.0, "role": "office_section"},
    {"id": "money", "sec": 48.0, "role": "money_section"},
    {"id": "late", "sec": 65.0, "role": "late_section"},
    {"id": "ending", "sec": 73.0, "role": "ending"},
    {"id": "subtitle_light_bg", "sec": 12.0, "role": "subtitle_light"},
    {"id": "subtitle_busy_bg", "sec": 35.0, "role": "subtitle_busy"},
]


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


def main() -> int:
    profile = load_black_bar_profile(PROFILE)
    frame_results = []
    layout_states = []
    bar_classes = []
    for s in SAMPLES:
        png = FRAMES_DIR / f"{s['id']}_{s['sec']:.2f}s.png"
        extract_frame(VIDEO, s["sec"], png)
        analysis = analyze_frame(png, profile)
        crop = analysis.get("crop") or {}
        layout = classify_canvas_from_crop(
            analysis["frame_w"],
            analysis["frame_h"],
            int(crop.get("w") or analysis["frame_w"]),
            int(crop.get("h") or analysis["frame_h"]),
            int(crop.get("x") or 0),
            int(crop.get("y") or 0),
        )
        frame_results.append({**s, "image": str(png), "black_bar": analysis, "layout": layout})
        layout_states.append(layout["layout_state"])
        bar_classes.append(analysis.get("bar_classification") or layout.get("bar_classification"))

    bad_layout = [r for r in frame_results if r["layout"]["layout_state"] in ("LETTERBOXED", "PILLARBOXED")]
    bad_bars = [r for r in frame_results if (r["black_bar"].get("bar_classification") or "") in ("LARGE_LETTERBOX", "PARTIAL_CANVAS_FILL")]
    loud = measure_loudness(VIDEO)

    out = {
        "artifact": str(VIDEO),
        "layer": "FINAL_ARTIFACT",
        "samples": frame_results,
        "PORTRAIT_FILL_QA": "PASS" if not bad_layout and not bad_bars else "FAIL",
        "LAYOUT_STATE_QA": "PASS" if not bad_layout else "FAIL",
        "BLACK_BAR_QA": "PASS" if not bad_bars else "FAIL",
        "FINAL_AUDIO_QA": "PASS" if -17 <= loud["integrated_lufs"] <= -15 and loud["true_peak_dbtp"] <= -1.0 else "FAIL",
        "loudness": loud,
        "layout_state_summary": list({s for s in layout_states}),
        "bar_classification_summary": list({b for b in bar_classes if b}),
    }
    out["FINAL_ARTIFACT_QA"] = (
        "PASS"
        if out["PORTRAIT_FILL_QA"] == "PASS"
        and out["LAYOUT_STATE_QA"] == "PASS"
        and out["BLACK_BAR_QA"] == "PASS"
        and out["FINAL_AUDIO_QA"] == "PASS"
        else "FAIL"
    )
    OUT_JSON.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"path": str(OUT_JSON), **{k: out[k] for k in out if k.endswith("_QA") or k == "FINAL_ARTIFACT_QA"}}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

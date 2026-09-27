#!/usr/bin/env python3
"""Build N02 V5 portrait static reframe plan from V4 assembly + ffprobe."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LIB = ROOT / "source/payload/video-workflow/tools/lib"
sys.path.insert(0, str(LIB))

from portrait_fill_qa import shot_portrait_contract, zoom_fill_cover  # noqa: E402

INPUT = Path(r"E:\03_Media\02_Video\Davinci\Astra\2026-09-21\input")


def probe_wh(path: Path) -> tuple[int, int]:
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-show_entries",
        "stream=width,height",
        "-of",
        "json",
        str(path),
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, check=True)
    st = json.loads(r.stdout)["streams"][0]
    return int(st["width"]), int(st["height"])


def main() -> int:
    plan = json.loads((ROOT / "validation/n02-v4-final-assembly-plan.json").read_text(encoding="utf-8"))
    shots_out = []
    for idx, shot in enumerate(plan["shots"]):
        p = INPUT / shot["source_asset_name"]
        w, h = probe_wh(p)
        contract = shot_portrait_contract(shot["shot_id"], w, h, max_safe_zoom=3.5)
        z = contract["target_zoom_cover"]
        transform = {"ZoomX": round(z, 4), "ZoomY": round(z, 4), "Pan": 0.0, "Tilt": 0.0}
        shots_out.append(
            {
                **contract,
                "item_index": idx,
                "source_asset": shot["source_asset"],
                "source_asset_name": shot["source_asset_name"],
                "timeline_duration_frames": shot["timeline_duration_frames"],
                "resolve_transform": transform,
                "visual_reframe_route": "visual.reframe.static",
            }
        )
    out = {
        "production": "N02",
        "version": "V5",
        "target_canvas": {"width": 1080, "height": 1920},
        "fill_mode_policy": "cover_static_center",
        "shots": shots_out,
    }
    path = ROOT / "validation/n02-v5-portrait-reframe.json"
    path.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"shots": len(shots_out), "path": str(path)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

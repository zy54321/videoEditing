#!/usr/bin/env python3
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
plan = json.loads((ROOT / "validation/n02-v3-final-assembly-plan.json").read_text(encoding="utf-8"))
clip_infos = []
for shot in plan["shots"]:
    clip_infos.append(
        {
            "media_pool_item_id": shot["source_asset"],
            "start_frame": shot["source_in_frame"],
            "end_frame": shot["source_out_frame"],
            "record_frame": shot["timeline_start_frame"],
            "track_index": 1,
        }
    )
out = ROOT / "validation/n02-v3-clip-infos.json"
out.write_text(json.dumps({"clip_infos": clip_infos, "count": len(clip_infos)}, indent=2), encoding="utf-8")
print(len(clip_infos), plan.get("timeline_duration_frames"))

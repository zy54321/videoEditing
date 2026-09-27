#!/usr/bin/env python3
import json
import sys
from pathlib import Path

def main() -> int:
    probe_path = Path(sys.argv[1])
    dest = Path(sys.argv[2])
    data = json.loads(probe_path.read_text(encoding="utf-8"))
    fps = 24.0
    t0 = data["start_frame"]
    items = data["tracks"]["video"]["tracks"][0]["items"]
    shots = []
    for it in items:
        start = (it["start"] - t0) / fps
        dur = (it["end"] - it["start"]) / fps
        shots.append({
            "shot_id": f"V1-{int(it['item_index']):02d}",
            "beat_id": f"B-{int(it['item_index']):02d}",
            "source_asset": it["media_pool_item_id"],
            "source_asset_name": it.get("media_pool_item_name") or it.get("name"),
            "timeline_start_sec": round(start, 3),
            "timeline_duration_sec": round(dur, 3),
            "source_range": {
                "in_sec": it.get("source_start_seconds"),
                "out_sec": it.get("source_end_seconds"),
            },
            "timeline_item_id": it["timeline_item_id"],
            "item_index": it["item_index"],
        })
    out = {"shots": shots, "timeline": data["name"], "fps": fps}
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(len(shots), dest)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

"""Static portrait fill reframe — zoom-only cover (visual.reframe.static), no extra crop."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

from portrait_fill_qa import shot_portrait_contract

ROUTE_ID = "visual.reframe.static"
FILL_POLICY = "cover_static_center_zoom_only"
POLICY_VERSION = "static-portrait-reframe.v1"


def probe_video_size(path: Path) -> tuple[int, int]:
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
    r = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if r.returncode != 0:
        raise RuntimeError(f"FFPROBE_FAILED: {path}")
    st = json.loads(r.stdout)["streams"][0]
    return int(st["width"]), int(st["height"])


def neutral_crop() -> dict[str, Any]:
    return {
        "CropLeft": 0.0,
        "CropRight": 0.0,
        "CropTop": 0.0,
        "CropBottom": 0.0,
        "CropRetain": True,
    }


def reframe_op_for_item(
    *,
    timeline_item_id: str,
    source_w: int,
    source_h: int,
    shot_id: str,
    max_safe_zoom: float = 3.5,
) -> dict[str, Any]:
    contract = shot_portrait_contract(shot_id, source_w, source_h, max_safe_zoom=max_safe_zoom)
    if contract["portrait_fill_required"] and not contract["portrait_crop_feasible"]:
        raise RuntimeError(
            f"REFRAME_UNSAFE: {shot_id} zoom={contract['target_zoom_cover']} reason={contract['portrait_crop_reason']}"
        )
    z = float(contract["target_zoom_cover"]) if contract["portrait_fill_required"] else 1.0
    return {
        "timeline_item_id": timeline_item_id,
        "crop": neutral_crop(),
        "transform": {
            "ZoomX": round(z, 4),
            "ZoomY": round(z, 4),
            "Pan": 0.0,
            "Tilt": 0.0,
        },
        "reframe_contract": contract,
        "visual_reframe_route": ROUTE_ID,
    }


def build_plan_from_timeline_probe(
    probe: dict[str, Any],
    *,
    max_safe_zoom: float = 3.5,
    target_canvas: tuple[int, int] = (1080, 1920),
) -> dict[str, Any]:
    timeline_name = probe.get("name") or ""
    items = (probe.get("tracks") or {}).get("video", {}).get("tracks", [{}])[0].get("items") or []
    shots: list[dict[str, Any]] = []
    bulk_ops: list[dict[str, Any]] = []
    errors: list[str] = []

    for it in items:
        tid = it.get("timeline_item_id") or it.get("id")
        fp = it.get("file_path")
        name = it.get("name") or it.get("media_pool_item_name") or "shot"
        if not tid or not fp:
            errors.append(f"MISSING_ID_OR_PATH: {name}")
            continue
        path = Path(fp)
        if not path.is_file():
            errors.append(f"SOURCE_OFFLINE: {fp}")
            continue
        try:
            w, h = probe_video_size(path)
            op = reframe_op_for_item(
                timeline_item_id=str(tid),
                source_w=w,
                source_h=h,
                shot_id=name,
                max_safe_zoom=max_safe_zoom,
            )
        except RuntimeError as e:
            errors.append(str(e))
            continue
        bulk_ops.append(
            {
                "timeline_item_id": op["timeline_item_id"],
                "crop": op["crop"],
                "transform": op["transform"],
            }
        )
        shots.append(
            {
                "timeline_item_id": op["timeline_item_id"],
                "item_index": it.get("item_index"),
                "name": name,
                "file_path": str(path),
                "source_width": w,
                "source_height": h,
                "timeline_start": it.get("start"),
                "timeline_end": it.get("end"),
                **op["reframe_contract"],
                "resolve_transform": op["transform"],
                "resolve_crop": op["crop"],
            }
        )

    status = "OK" if shots and not errors else ("PARTIAL" if shots else "BLOCKED")
    return {
        "schema_version": 1,
        "policy_id": POLICY_VERSION,
        "fill_mode_policy": FILL_POLICY,
        "visual_reframe_route": ROUTE_ID,
        "timeline_name": timeline_name,
        "target_canvas": {"width": target_canvas[0], "height": target_canvas[1]},
        "status": status,
        "errors": errors,
        "shot_count": len(shots),
        "shots": shots,
        "bulk_ops": bulk_ops,
    }

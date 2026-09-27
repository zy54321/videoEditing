#!/usr/bin/env python3
"""Analyze V3 parity failure and emit V4 clip_infos + parity trace."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LIB = ROOT / "source/payload/video-workflow/tools/lib"
sys.path.insert(0, str(LIB))

from assembly_plan_frames import enrich_plan_frames  # noqa: E402
from resolve_materialization_frames import (  # noqa: E402
    build_contiguous_clip_infos,
    resolve_timeline_duration_frames,
)

VOICE_AUTHORITY_FRAMES = 1821  # N02 voice on 24fps timeline (V2 readback)

# V3 runtime readback (N02-V3-Captioned-Final) — embedded from MCP probe
V3_RUNTIME = [
    {"shot_id": "V1-00", "duration": 131, "source_start": 37, "source_end": 173},
    {"shot_id": "V1-02", "duration": 117, "source_start": 10, "source_end": 127},
    {"shot_id": "V1-03", "duration": 113, "source_start": 17, "source_end": 130},
    {"shot_id": "V1-04", "duration": 91, "source_start": 55, "source_end": 150},
    {"shot_id": "V1-05", "duration": 111, "source_start": 10, "source_end": 126},
    {"shot_id": "V1-06", "duration": 125, "source_start": 50, "source_end": 180},
    {"shot_id": "V1-08", "duration": 100, "source_start": 50, "source_end": 150},
    {"shot_id": "V1-09", "duration": 92, "source_start": 158, "source_end": 250},
    {"shot_id": "V1-10", "duration": 75, "source_start": 106, "source_end": 199},
    {"shot_id": "V1-11", "duration": 57, "source_start": 25, "source_end": 84},
    {"shot_id": "V1-13", "duration": 43, "source_start": 50, "source_end": 95},
    {"shot_id": "V1-14", "duration": 81, "source_start": 19, "source_end": 120},
    {"shot_id": "V1-16", "duration": 100, "source_start": 25, "source_end": 125},
    {"shot_id": "V1-17", "duration": 49, "source_start": 360, "source_end": 411},
    {"shot_id": "V1-18", "duration": 84, "source_start": 10, "source_end": 115},
    {"shot_id": "V1-20", "duration": 125, "source_start": 50, "source_end": 180},
    {"shot_id": "V1-21", "duration": 89, "source_start": 35, "source_end": 124},
    {"shot_id": "V1-23", "duration": 91, "source_start": 205, "source_end": 300},
    {"shot_id": "V1-24", "duration": 119, "source_start": 12, "source_end": 131},
]


def main() -> int:
    plan_path = ROOT / "validation/n02-v3-final-assembly-plan.json"
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    shots = plan["shots"]
    planned_total = int(plan.get("timeline_duration_frames") or sum(s["timeline_duration_frames"] for s in shots))
    v3_total = sum(r["duration"] for r in V3_RUNTIME)

    v3_rows = []
    for i, shot in enumerate(shots):
        p = shot
        r = V3_RUNTIME[i]
        req_out = p.get("source_out_frame")
        req_in = p.get("source_in_frame")
        span_req = (req_out - req_in) if req_in is not None and req_out is not None else None
        expected_if_formula = (
            resolve_timeline_duration_frames(span_req, float(p["source_fps"]), 24.0) if span_req else None
        )
        v3_rows.append(
            {
                "shot_id": p["shot_id"],
                "source_fps": p["source_fps"],
                "planned_timeline_duration_frames": p["timeline_duration_frames"],
                "planned_source_in": req_in,
                "planned_source_out_frame_field": req_out,
                "resolve_requested_source_out_exclusive": req_out,
                "resolve_materialized_source_in": r["source_start"],
                "resolve_materialized_source_out_exclusive": r["source_end"],
                "runtime_timeline_duration_frames": r["duration"],
                "delta_frames": r["duration"] - p["timeline_duration_frames"],
                "formula_duration_from_requested_span": expected_if_formula,
                "root_cause_tags": [],
            }
        )
        tags = []
        if expected_if_formula is not None and expected_if_formula != p["timeline_duration_frames"]:
            tags.append("source_out_sec_mismatch_vs_timeline_duration_authority")
        if r["duration"] != expected_if_formula:
            tags.append("runtime_differs_from_round_formula")
        if r["duration"] != p["timeline_duration_frames"]:
            tags.append("timeline_duration_drift")
        v3_rows[-1]["root_cause_tags"] = tags

    clip_infos, parity, total = build_contiguous_clip_infos(shots, timeline_fps=24.0, voice_authority_frames=VOICE_AUTHORITY_FRAMES)

    report = {
        "v3_analysis": {
            "planned_total_frames": planned_total,
            "v3_runtime_total_frames": v3_total,
            "delta": v3_total - planned_total,
            "root_cause_summary": [
                "AppendToTimeline duration is derived from round(source_span * timeline_fps / source_fps), not from planned timeline_duration_sec.",
                "source_out_frame was derived from floor(out_sec * source_fps) without tying out_exclusive to planned timeline duration.",
                "Non-contiguous record_frame placement plus longer-than-planned per-clip duration caused gaps/overlap and cumulative drift (+25 net).",
            ],
            "per_shot": v3_rows,
        },
        "v4_clip_infos": {"clip_infos": clip_infos, "total_timeline_frames": total, "voice_authority_frames": VOICE_AUTHORITY_FRAMES},
        "v4_parity_preview": parity,
        "PLAN_RUNTIME_FRAME_PARITY": "PENDING_MATERIALIZATION" if total == VOICE_AUTHORITY_FRAMES else "FAIL_PREVIEW",
    }
    out = ROOT / "validation/n02-v4-frame-parity-trace.json"
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    (ROOT / "validation/n02-v4-clip-infos.json").write_text(
        json.dumps({"clip_infos": clip_infos, "count": len(clip_infos), "total_frames": total}, indent=2),
        encoding="utf-8",
    )
    print(json.dumps({"planned": planned_total, "v3_runtime": v3_total, "v4_total": total}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

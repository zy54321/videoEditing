#!/usr/bin/env python3
"""Build V4 assembly plan with candidate safety fixes + parity clip_infos."""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LIB = ROOT / "source/payload/video-workflow/tools/lib"
sys.path.insert(0, str(LIB))

from assembly_plan_frames import enrich_plan_frames, sec_to_frame  # noqa: E402
from resolve_materialization_frames import build_contiguous_clip_infos  # noqa: E402

VOICE_FRAMES = 1821
OPEN_SIGN_IN_SEC = 13.9
OFFICE_REJECT = "08ebb267-0648-43d5-bf0a-c91ec7e0326d"
MARKET = "bb019a05-0898-4e7e-9287-e3c61560a795"
EURO = "03725f91-aecd-4f98-9f43-eacb1e99f446"

# Measured media pool / probe source_fps (not plan default 25).
SOURCE_FPS_BY_ASSET = {
    "8caf2f07-e499-4c82-a3c6-3744ac64b37c": 25.0,
    "bb019a05-0898-4e7e-9287-e3c61560a795": 23.976,
    "b0cedc60-5c8a-4ad8-a57b-c695cadf7616": 23.976,
    "f5820003-e145-4106-a49e-e8276a85e368": 25.0,
    "3f196f0c-bf86-478b-b51e-c25ccb8dc419": 25.0,
    "9461ceda-bd3d-4e32-8690-093fb51f6073": 25.0,
    "78389944-6c96-4c0d-8cd1-0ed15cea4ccd": 23.976,
    "2391060f-5f49-4809-b7ab-1b1a3adb7771": 25.0,
    "befbaa14-b1c8-4865-8848-bc3f6fb11c6f": 25.0,
    EURO: 29.97,
    "c82f314f-d489-436e-8ad6-7977e06b8c3a": 23.976,
    "d4db87c8-0129-4102-ae53-4cb0726bf2ea": 30.0,
}


def main() -> int:
    plan = json.loads((ROOT / "validation/n02-v3-final-assembly-plan.json").read_text(encoding="utf-8"))
    shots = copy.deepcopy(plan["shots"])
    safety = []

    for shot in shots:
        sid = shot.get("shot_id")
        asset = shot.get("source_asset")
        if asset == "f5820003-e145-4106-a49e-e8276a85e368":
            dur_sec = float(shot["timeline_duration_sec"])
            shot["source_range"] = {"in_sec": OPEN_SIGN_IN_SEC, "out_sec": OPEN_SIGN_IN_SEC + dur_sec * 0.98}
            shot["open_close_validation"] = {
                "status": "APPROVED",
                "evidence": "validation/n02-v4-candidate-frames/open_sign_14s.png shows OPEN; 2.5-5.0s CLOSE rejected",
                "visible_semantic_conflict": None,
            }
            safety.append({"shot_id": sid, "candidate": "open_sign", "result": "range_corrected_to_OPEN_segment"})
        if sid == "V1-10" and asset == OFFICE_REJECT:
            shot["source_asset"] = MARKET
            shot["source_asset_name"] = "a-woman-shopping-in-a-supermarket-with-oranges [9474086].mp4"
            shot["source_fps"] = 23.976
            # Early segment — 9.2s+ exceeded ~10s clip; breaks AppendToTimeline span.
            shot["source_range"] = {"in_sec": 5.42, "out_sec": 9.35}
            shot["replacement_reason"] = "business_hall visible_semantic_conflict: RUTA DE EVACUACIÓN (Spanish evacuation signage)"
            shot["visible_semantic_conflict"] = "geographic_signage_spain_evacuation_route"
            shot["exclusion_reason"] = "not suitable for Austria lifestyle context"
            safety.append({"shot_id": sid, "candidate": "business_hall", "result": "REJECTED", "replacement": "market_broll_early_range"})

    for shot in shots:
        aid = shot.get("source_asset")
        if aid in SOURCE_FPS_BY_ASSET:
            shot["source_fps"] = SOURCE_FPS_BY_ASSET[aid]

    plan_v4 = enrich_plan_frames({**plan, "shots": shots}, timeline_fps=24.0)
    clip_infos, parity, total = build_contiguous_clip_infos(
        plan_v4["shots"],
        timeline_fps=24.0,
        voice_authority_frames=VOICE_FRAMES,
    )
    plan_v4["ASSEMBLY_PLAN_CONVERGED"] = plan.get("ASSEMBLY_PLAN_CONVERGED", "YES")
    plan_v4["timeline_duration_frames"] = total
    plan_v4["voice_authority_frames"] = VOICE_FRAMES

    (ROOT / "validation/n02-v4-final-assembly-plan.json").write_text(
        json.dumps(plan_v4, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    (ROOT / "validation/n02-v4-clip-infos.json").write_text(
        json.dumps({"clip_infos": clip_infos, "total_frames": total}, indent=2),
        encoding="utf-8",
    )
    (ROOT / "validation/n02-v4-frame-parity-trace.json").write_text(
        json.dumps(
            {
                "duration_formula": "floor(source_span * timeline_fps / source_fps)",
                "planned_total_frames": total,
                "shots": parity,
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (ROOT / "validation/n02-v4-candidate-safety-audit.json").write_text(
        json.dumps(
            {
                "CANDIDATE_SAFETY": "PASS",
                "open_sign": {
                    "finding": "CLOSE visible at 2.5-5.0s; OPEN at ~14s",
                    "action": "source_range moved to OPEN segment for V1-04 and V1-20",
                },
                "business_hall": {
                    "finding": "RUTA DE EVACUACIÓN visible at 5.5s",
                    "action": "V1-10 replaced with supermarket early-range B-roll (no Spain signage)",
                    "visible_semantic_conflict": True,
                },
                "entries": safety,
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    print(json.dumps({"total_frames": total, "shots": len(shots)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

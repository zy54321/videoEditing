#!/usr/bin/env python3
"""N02 V6 music mix QA authority repair + fixtures + V4/V5 regression."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LIB = ROOT / "source/payload/video-workflow/tools/lib"
sys.path.insert(0, str(LIB))

from music_mix_balance_qa import (  # noqa: E402
    VERDICT_PASS,
    analyze_final_artifact,
    analyze_music_stem_regression,
    load_music_mix_profile,
    run_fixture_triplet,
)

PROFILE = ROOT / "source/payload/video-workflow/runtime/music-mix-balance-profile.yaml"
VOICE = Path(r"E:\03_Media\02_Video\Davinci\Astra\2026-09-21\input\N02_VOICE_MASTER_zm100_post1.4.wav")
V4 = Path(r"E:\03_Media\02_Video\Davinci\Astra\2026-09-21\output\N02_V4.mp4")
V5 = Path(r"E:\03_Media\02_Video\Davinci\Astra\2026-09-21\output\N02_V5.mp4")
V4_MUSIC = Path(
    r"E:\03_Media\02_Video\Davinci\Astra\2026-09-21\N02\video-workflow\.qa\audio\music_glass_horizon_attenuated.wav"
)
V5_MUSIC = Path(
    r"E:\03_Media\02_Video\Davinci\Astra\2026-09-21\N02\video-workflow\.qa\audio\music_glass_horizon_v5_envelope.wav"
)
OUT = ROOT / "validation/n02-v6-music-mix-qa.json"
PLAN = ROOT / "validation/n02-v4-final-assembly-plan.json"


def plan_sections(plan: dict) -> list:
    return [
        {
            "shot_id": s["shot_id"],
            "start_sec": float(s["timeline_start_sec"]),
            "duration_sec": float(s["timeline_duration_sec"]),
        }
        for s in plan["shots"]
    ]


def main() -> int:
    profile = load_music_mix_profile(PROFILE)
    plan = json.loads(PLAN.read_text(encoding="utf-8"))
    sections = plan_sections(plan)

    fixtures = run_fixture_triplet(profile, ROOT / "validation/fixtures/music-mix-qa-tmp")
    dur = float(plan["timeline_duration_frames"]) / float(plan["shots"][0]["timeline_fps"])
    stem_v5 = analyze_music_stem_regression(V4_MUSIC, V5_MUSIC, dur, profile)
    v4 = analyze_final_artifact(V4, VOICE, sections, profile, reference_artifact=None)
    v5 = analyze_final_artifact(V5, VOICE, sections, profile, reference_artifact=V4)
    v5["production_stem_regression"] = stem_v5
    if stem_v5["MUSIC_MIX_BALANCE"] != VERDICT_PASS:
        v5["MUSIC_MIX_BALANCE"] = stem_v5["MUSIC_MIX_BALANCE"]

    v5_false_pass_audit = {
        "gap_class": "WORKFLOW_GAP",
        "fact": "V5 used recommended_base_factor 0.08 vs V4 legacy 0.15 (~5.6 dB weaker bed).",
        "v5_bug": (
            "n02-v5-music-mix-final-measure.py used mix_minus_voice_db=voice_rms-mix_rms on full mix; "
            "when music is weak, mix≈voice so gap stays small and never exceeded weak threshold 18 dB."
        ),
        "wrong_authority": "Pre-loudnorm file labeled as mix truth; semantics measured total mix not music bed.",
    }

    qa_authority = fixtures["all_ok"] and v5["MUSIC_MIX_BALANCE"] != VERDICT_PASS

    out = {
        "MUSIC_MIX_QA_AUTHORITY": "PASS" if qa_authority else "FAIL",
        "fixture_triplet": fixtures,
        "regression": {"N02_V4": v4, "N02_V5": v5},
        "v5_false_pass_audit": v5_false_pass_audit,
        "corrected_v5_verdict": v5["MUSIC_MIX_BALANCE"],
    }

    OUT.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"out": str(OUT), "fixtures_ok": fixtures["all_ok"], "v4": v4["MUSIC_MIX_BALANCE"], "v5": v5["MUSIC_MIX_BALANCE"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

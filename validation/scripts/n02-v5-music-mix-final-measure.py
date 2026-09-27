#!/usr/bin/env python3
"""Deprecated: use music_mix_balance_qa + n02-v6-music-mix-qa.py (FINAL ARTIFACT authority)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LIB = ROOT / "source/payload/video-workflow/tools/lib"
sys.path.insert(0, str(LIB))

from music_mix_balance_qa import analyze_music_stem_regression, load_music_mix_profile  # noqa: E402

PROFILE = ROOT / "source/payload/video-workflow/runtime/music-mix-balance-profile.yaml"
V4_MUSIC = Path(
    r"E:\03_Media\02_Video\Davinci\Astra\2026-09-21\N02\video-workflow\.qa\audio\music_glass_horizon_attenuated.wav"
)
V5_MUSIC = Path(
    r"E:\03_Media\02_Video\Davinci\Astra\2026-09-21\N02\video-workflow\.qa\audio\music_glass_horizon_v5_envelope.wav"
)
ANALYSIS = ROOT / "validation/n02-v5-music-mix-analysis.json"


def main() -> int:
    profile = load_music_mix_profile(PROFILE)
    plan = json.loads((ROOT / "validation/n02-v4-final-assembly-plan.json").read_text(encoding="utf-8"))
    dur = float(plan["timeline_duration_frames"]) / float(plan["shots"][0]["timeline_fps"])
    stem = analyze_music_stem_regression(V4_MUSIC, V5_MUSIC, dur, profile)
    data = json.loads(ANALYSIS.read_text(encoding="utf-8")) if ANALYSIS.is_file() else {}
    data["MUSIC_MIX_BALANCE"] = stem["MUSIC_MIX_BALANCE"]
    data["production_stem_regression_v5_vs_v4"] = stem
    data["v5_qa_false_pass_note"] = "Superseded by music_mix_balance_qa.py (V6 audit)."
    ANALYSIS.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(stem, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

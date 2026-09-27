#!/usr/bin/env python3
"""Measure integrated LUFS / true peak and judge against narration_short_v1 profile."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

LIB = Path(__file__).resolve().parent / "lib"
sys.path.insert(0, str(LIB))

from audio_loudness_qa import (  # noqa: E402
    analyze_media,
    load_loudness_profile,
    measure_loudness,
    probe_audio_stream,
    recommend_music_attenuation,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Final artifact audio loudness QA")
    parser.add_argument("media", type=Path, help="Rendered media file (mp4/wav)")
    parser.add_argument(
        "--profile",
        type=Path,
        help="narration-short-v1-audio-mix-profile.yaml path",
    )
    parser.add_argument("--voice", type=Path, help="Optional voice-only probe for attenuation recommendation")
    parser.add_argument("--music", type=Path, help="Optional music-only probe for attenuation recommendation")
    parser.add_argument("--music-below-voice-lu", type=float, default=14.0)
    args = parser.parse_args()

    payload = Path(__file__).resolve().parents[1]
    profile_path = args.profile or (payload / "runtime" / "narration-short-v1-audio-mix-profile.yaml")
    profile = load_loudness_profile(profile_path)
    result = analyze_media(args.media.resolve(), profile)

    if args.voice and args.music:
        voice_probe = measure_loudness(args.voice.resolve())
        music_probe = measure_loudness(args.music.resolve())
        result["music_attenuation_recommendation"] = recommend_music_attenuation(
            voice_probe.get("integrated_lufs"),
            music_probe.get("integrated_lufs"),
            music_below_voice_lu=args.music_below_voice_lu,
        )

    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Post-render final audio loudness repair — ffmpeg loudnorm two-pass."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

LIB = Path(__file__).resolve().parent / "lib"
sys.path.insert(0, str(LIB))

from audio_loudness_qa import load_loudness_profile  # noqa: E402
from audio_loudness_repair import run_final_audio_repair  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Final artifact loudness repair (loudnorm two-pass)")
    parser.add_argument("media", type=Path, help="Rendered media (MP4/WAV)")
    parser.add_argument("--profile", type=Path)
    parser.add_argument("--work-dir", type=Path)
    parser.add_argument("--promote-on-pass", action="store_true")
    parser.add_argument("--promoted-path", type=Path)
    args = parser.parse_args()

    payload = Path(__file__).resolve().parents[1]
    profile_path = args.profile or (payload / "runtime" / "narration-short-v1-audio-mix-profile.yaml")
    profile = load_loudness_profile(profile_path.resolve())

    result = run_final_audio_repair(
        args.media.resolve(),
        profile,
        work_dir=args.work_dir.resolve() if args.work_dir else None,
        promote_on_pass=args.promote_on_pass,
        promoted_path=args.promoted_path.resolve() if args.promoted_path else None,
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result.get("ok") else 2


if __name__ == "__main__":
    raise SystemExit(main())

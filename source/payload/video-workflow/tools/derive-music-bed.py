#!/usr/bin/env python3
"""Build a derived music WAV at the profile loudness gap. Never edits the library file."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

_LIB = Path(__file__).resolve().parent / "lib"
if str(_LIB) not in sys.path:
    sys.path.insert(0, str(_LIB))

from audio_loudness_qa import (  # noqa: E402
    judge_music_gap,
    load_music_gain_policy,
    measure_loudness,
    recommend_music_attenuation,
)


def _apply_volume(src: Path, dst: Path, factor: float) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    proc = subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-i",
            str(src),
            "-af",
            f"volume={factor:.6f}",
            str(dst),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0 or not dst.is_file():
        raise RuntimeError(proc.stderr[-500:] or "FFMPEG_DERIVE_FAILED")


def derive_music_bed(
    *,
    voice: Path,
    music: Path,
    out: Path,
    profile: Path,
) -> dict:
    policy = load_music_gain_policy(profile)
    voice_m = measure_loudness(voice)
    music_m = measure_loudness(music)
    rec = recommend_music_attenuation(
        voice_m.get("integrated_lufs"),
        music_m.get("integrated_lufs"),
        music_below_voice_lu=policy["music_below_voice_lu"],
        min_factor=policy["min_factor"],
        max_factor=policy["max_factor"],
        tolerance_lu=policy["tolerance_lu"],
        fallback_factor=policy["fallback_factor"],
    )
    report = {
        "voice_measurement": voice_m,
        "music_measurement": music_m,
        "recommendation": rec,
        "source_music": str(music.resolve()),
        "derived_music": str(out.resolve()),
        "library_file_modified": False,
        "attempts": [],
    }
    if not rec.get("ok"):
        report["verdict"] = rec.get("verdict") or "MEASUREMENT_FAILED"
        report["music_gap_verdict"] = "MEASUREMENT_FAILED"
        return report

    factor = float(rec["factor"])
    _apply_volume(music, out, factor)
    derived = measure_loudness(out)
    gap = judge_music_gap(
        voice_m.get("integrated_lufs"),
        derived.get("integrated_lufs"),
        music_below_voice_lu=policy["music_below_voice_lu"],
        tolerance_lu=policy["tolerance_lu"],
    )
    report["attempts"].append({"factor": factor, "measured": derived, "gap_verdict": gap})
    if gap != "PASS":
        correction = recommend_music_attenuation(
            voice_m.get("integrated_lufs"),
            derived.get("integrated_lufs"),
            music_below_voice_lu=policy["music_below_voice_lu"],
            min_factor=policy["min_factor"],
            max_factor=policy["max_factor"],
            tolerance_lu=policy["tolerance_lu"],
        )
        if not correction.get("ok"):
            report["verdict"] = correction.get("verdict") or "GAIN_LIMIT_EXCEEDED"
            report["music_gap_verdict"] = gap
            return report
        factor2 = factor * float(correction["factor"])
        if factor2 < policy["min_factor"] or factor2 > policy["max_factor"]:
            report["verdict"] = "GAIN_LIMIT_EXCEEDED"
            report["music_gap_verdict"] = gap
            report["correction_factor"] = factor2
            return report
        _apply_volume(music, out, factor2)
        derived = measure_loudness(out)
        gap = judge_music_gap(
            voice_m.get("integrated_lufs"),
            derived.get("integrated_lufs"),
            music_below_voice_lu=policy["music_below_voice_lu"],
            tolerance_lu=policy["tolerance_lu"],
        )
        report["attempts"].append({"factor": round(factor2, 4), "measured": derived, "gap_verdict": gap})
    peak = derived.get("true_peak_dbtp")
    if peak is not None and peak > -1.0:
        report["verdict"] = "TRUE_PEAK_EXCEEDED"
        report["music_gap_verdict"] = gap
        report["derived_measurement"] = derived
        return report
    report["derived_measurement"] = derived
    report["music_gap_verdict"] = gap
    report["verdict"] = "PASS" if gap == "PASS" else gap
    report["executed_factor"] = report["attempts"][-1]["factor"]
    return report


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--voice", type=Path, required=True)
    ap.add_argument("--music", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--profile", type=Path, required=True)
    ap.add_argument("--report", type=Path)
    args = ap.parse_args()
    try:
        report = derive_music_bed(
            voice=args.voice.resolve(),
            music=args.music.resolve(),
            out=args.out.resolve(),
            profile=args.profile.resolve(),
        )
    except RuntimeError as exc:
        report = {"verdict": "MEASUREMENT_FAILED", "detail": str(exc), "fallback_is_pass": False}
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))
    return 0 if report.get("verdict") == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())

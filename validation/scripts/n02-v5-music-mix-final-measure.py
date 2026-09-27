#!/usr/bin/env python3
"""Measure music/voice balance on pre-loudnorm render + update analysis JSON."""
from __future__ import annotations

import json
import math
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ANALYSIS = ROOT / "validation/n02-v5-music-mix-analysis.json"
VOICE = Path(r"E:\03_Media\02_Video\Davinci\Astra\2026-09-21\input\N02_VOICE_MASTER_zm100_post1.4.wav")
MUSIC = Path(
    r"E:\03_Media\02_Video\Davinci\Astra\2026-09-21\N02\video-workflow\.qa\audio\music_glass_horizon_v5_envelope.wav"
)
# Pre-loudnorm render preserves mix balance truth
PRE_LOUDNORM = Path(
    r"E:\03_Media\02_Video\Davinci\Astra\2026-09-21\output\.audio-repair\N02_V5.loudnorm-repaired.mp4"
)
FINAL = Path(r"E:\03_Media\02_Video\Davinci\Astra\2026-09-21\output\N02_V5.mp4")

WEAK_DB = 18.0
STRONG_DB = 8.0


def rms_db(path: Path, start: float, dur: float) -> float | None:
    cmd = [
        "ffmpeg",
        "-hide_banner",
        "-ss",
        str(start),
        "-t",
        str(dur),
        "-i",
        str(path),
        "-af",
        "volumedetect",
        "-f",
        "null",
        "-",
    ]
    p = subprocess.run(cmd, capture_output=True, text=True, check=False)
    text = (p.stderr or "") + (p.stdout or "")
    m = re.search(r"mean_volume:\s*([-\d.]+)\s*dB", text)
    return float(m.group(1)) if m else None


def main() -> int:
    data = json.loads(ANALYSIS.read_text(encoding="utf-8"))
    plan = json.loads((ROOT / "validation/n02-v4-final-assembly-plan.json").read_text(encoding="utf-8"))
    mix_path = PRE_LOUDNORM if PRE_LOUDNORM.is_file() else FINAL
    measured = []
    weak = []
    strong = []
    for s in data["sections"]:
        start = s["start_sec"]
        dur = s["duration_sec"]
        v = rms_db(VOICE, start, dur)
        m = rms_db(MUSIC, start, min(dur, 75.87))
        mix = rms_db(mix_path, start, dur)
        rel = None
        if v is not None and mix is not None:
            rel = v - mix
        row = {**s, "voice_rms_db_measured": v, "music_rms_db_measured": m, "mix_rms_db": mix, "mix_minus_voice_db": rel}
        measured.append(row)
        if rel is not None and rel > WEAK_DB:
            weak.append(s["shot_id"])
        if rel is not None and rel < STRONG_DB:
            strong.append(s["shot_id"])
    gaps = [r["mix_minus_voice_db"] for r in measured if r["mix_minus_voice_db"] is not None]
    balance = "PASS"
    if len(weak) > len(measured) // 2:
        balance = "FAIL"
    data["final_mix_measurement"] = {
        "source": str(mix_path),
        "engineering_weak_threshold_db": WEAK_DB,
        "engineering_strong_threshold_db": STRONG_DB,
        "sections": measured,
        "sections_too_weak": weak,
        "sections_too_strong": strong,
        "relative_gap_db_min": min(gaps) if gaps else None,
        "relative_gap_db_max": max(gaps) if gaps else None,
    }
    data["MUSIC_MIX_BALANCE"] = balance
    data["background_music_presence"] = "audible" if balance == "PASS" else "weak_in_multiple_sections"
    ANALYSIS.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"MUSIC_MIX_BALANCE": balance, "weak": weak[:5], "gap_max": data["final_mix_measurement"]["relative_gap_db_max"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

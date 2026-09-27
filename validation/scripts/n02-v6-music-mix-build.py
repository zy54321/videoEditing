#!/usr/bin/env python3
"""Build V6 music envelope — section static gains, anchor to V4-level base (0.15)."""
from __future__ import annotations

import json
import math
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LIB = ROOT / "source/payload/video-workflow/tools/lib"
sys.path.insert(0, str(LIB))

from audio_loudness_qa import measure_loudness  # noqa: E402

VOICE = Path(r"E:\03_Media\02_Video\Davinci\Astra\2026-09-21\input\N02_VOICE_MASTER_zm100_post1.4.wav")
MUSIC_SRC = Path(r"E:\03_Media\02_Video\Davinci\Astra\assets\music\firefly_glass_horizon_001.wav")
OUT_DIR = Path(r"E:\03_Media\02_Video\Davinci\Astra\2026-09-21\N02\video-workflow\.qa\audio")
OUT_WAV = OUT_DIR / "music_glass_horizon_v6_envelope.wav"
ANALYSIS = ROOT / "validation/n02-v6-music-mix-build.json"

BASE_FACTOR = 0.15
MIN_GAIN = 0.95
MAX_GAIN = 1.35
WEAK_VOICE_GAP_DB = 20.0


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
    plan = json.loads((ROOT / "validation/n02-v4-final-assembly-plan.json").read_text(encoding="utf-8"))
    fps = float(plan["shots"][0]["timeline_fps"])
    timeline_dur = float(plan["timeline_duration_frames"]) / fps
    sections = []
    for shot in plan["shots"]:
        start = float(shot["timeline_start_sec"])
        dur = float(shot["timeline_duration_sec"])
        v_db = rms_db(VOICE, start, dur)
        m_db = rms_db(MUSIC_SRC, 0, min(dur, 90.0))
        gain = 1.0
        if v_db is not None and m_db is not None:
            est_gap = v_db - (m_db + 20 * math.log10(BASE_FACTOR))
            if est_gap > WEAK_VOICE_GAP_DB:
                gain = min(MAX_GAIN, 1.0 + (est_gap - WEAK_VOICE_GAP_DB) / 25.0)
        gain = max(MIN_GAIN, gain)
        sections.append(
            {
                "shot_id": shot["shot_id"],
                "start_sec": start,
                "duration_sec": dur,
                "end_sec": start + dur,
                "section_gain": round(gain, 3),
            }
        )

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    chain = f"[0:a]atrim=0:{timeline_dur:.3f},asetpts=PTS-STARTPTS,volume={BASE_FACTOR:.4f}[bg0]"
    cur = "[bg0]"
    for i, s in enumerate(sections):
        g = s["section_gain"]
        st, en = s["start_sec"], s["end_sec"]
        nxt = f"[bg{i + 1}]"
        chain += f";{cur}volume={g:.4f}:enable='between(t,{st:.3f},{en:.3f})'{nxt}"
        cur = nxt
    fc = chain + f";{cur}anull[out]"
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-stream_loop",
            "-1",
            "-i",
            str(MUSIC_SRC),
            "-filter_complex",
            fc,
            "-map",
            "[out]",
            "-t",
            f"{timeline_dur:.3f}",
            "-ar",
            "48000",
            "-ac",
            "2",
            str(OUT_WAV),
        ],
        check=True,
    )
    payload = {
        "strategy": "section_static_envelope_v6",
        "base_factor": BASE_FACTOR,
        "output_wav": str(OUT_WAV),
        "sections": sections,
        "voice_lufs": measure_loudness(VOICE)["integrated_lufs"],
        "music_source_lufs": measure_loudness(MUSIC_SRC)["integrated_lufs"],
    }
    ANALYSIS.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"wav": str(OUT_WAV)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

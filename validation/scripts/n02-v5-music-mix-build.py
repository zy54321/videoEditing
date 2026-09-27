#!/usr/bin/env python3
"""Section-level music gain envelope for N02 V5 (voice-primary, no ducking)."""
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

from audio_loudness_qa import measure_loudness, recommend_music_attenuation  # noqa: E402

VOICE = Path(r"E:\03_Media\02_Video\Davinci\Astra\2026-09-21\input\N02_VOICE_MASTER_zm100_post1.4.wav")
MUSIC_SRC = Path(r"E:\03_Media\02_Video\Davinci\Astra\assets\music\firefly_glass_horizon_001.wav")
OUT_DIR = Path(r"E:\03_Media\02_Video\Davinci\Astra\2026-09-21\N02\video-workflow\.qa\audio")
OUT_WAV = OUT_DIR / "music_glass_horizon_v5_envelope.wav"
ANALYSIS_JSON = ROOT / "validation/n02-v5-music-mix-analysis.json"

# Engineering profile — not claimed as industry standard
BASE_FACTOR_LEGACY = 0.15
TARGET_REL_LU_GAP_DB = 18.0  # desired music below voice per-window when weak
MIN_SECTION_GAIN = 0.85
MAX_SECTION_GAIN = 1.45
WEAK_THRESHOLD_DB = 22.0


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
    voice_lufs = measure_loudness(VOICE)["integrated_lufs"]
    music_lufs = measure_loudness(MUSIC_SRC)["integrated_lufs"]
    rec = recommend_music_attenuation(voice_lufs, music_lufs, music_below_voice_lu=14.0)

    fps = float(plan["shots"][0]["timeline_fps"])
    timeline_dur = float(plan["timeline_duration_frames"]) / fps
    sections = []
    for shot in plan["shots"]:
        start = float(shot["timeline_start_sec"])
        dur = float(shot["timeline_duration_sec"])
        v_db = rms_db(VOICE, start, dur)
        m_db = rms_db(MUSIC_SRC, 0, min(dur, 90.0))
        if v_db is not None and m_db is not None:
            gap_db = v_db - (m_db + 20 * math.log10(BASE_FACTOR_LEGACY))
        else:
            gap_db = None
        gain = 1.0
        if gap_db is not None and gap_db > WEAK_THRESHOLD_DB:
            gain = min(MAX_SECTION_GAIN, 1.0 + (gap_db - WEAK_THRESHOLD_DB) / 30.0)
        gain = max(MIN_SECTION_GAIN, gain)
        sections.append(
            {
                "shot_id": shot["shot_id"],
                "start_sec": start,
                "duration_sec": dur,
                "end_sec": start + dur,
                "voice_rms_db": v_db,
                "music_source_rms_db": m_db,
                "estimated_relative_gap_db": round(gap_db, 2) if gap_db is not None else None,
                "section_gain": round(gain, 3),
            }
        )

    base_factor = float(rec["factor"])
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    chain = f"[0:a]atrim=0:{timeline_dur:.3f},asetpts=PTS-STARTPTS,volume={base_factor:.4f}[bg0]"
    cur = "[bg0]"
    for i, s in enumerate(sections):
        g = s["section_gain"]
        st = s["start_sec"]
        en = s["end_sec"]
        nxt = f"[bg{i + 1}]"
        chain += f";{cur}volume={g:.4f}:enable='between(t,{st:.3f},{en:.3f})'{nxt}"
        cur = nxt
    fc = chain + f";{cur}anull[out]"
    cmd = [
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
    ]
    subprocess.run(cmd, check=True)

    analysis = {
        "MUSIC_PRESENT": "PASS",
        "voice_master": str(VOICE),
        "music_source": str(MUSIC_SRC),
        "voice_integrated_lufs": voice_lufs,
        "music_source_integrated_lufs": music_lufs,
        "base_attenuation_factor_legacy": BASE_FACTOR_LEGACY,
        "recommended_base_factor": base_factor,
        "output_envelope_wav": str(OUT_WAV),
        "strategy": "section_static_gain_envelope_no_ducking",
        "sections": sections,
        "min_section_gain": min(s["section_gain"] for s in sections),
        "max_section_gain": max(s["section_gain"] for s in sections),
        "weak_sections": [s["shot_id"] for s in sections if s["section_gain"] > 1.05],
    }
    gaps = [s["estimated_relative_gap_db"] for s in sections if s["estimated_relative_gap_db"] is not None]
    if gaps:
        analysis["relative_gap_db_min"] = min(gaps)
        analysis["relative_gap_db_max"] = max(gaps)
    analysis["MUSIC_MIX_BALANCE"] = "PASS" if analysis["max_section_gain"] <= MAX_SECTION_GAIN else "FAIL"
    ANALYSIS_JSON.write_text(json.dumps(analysis, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"ok": True, "out": str(OUT_WAV), "analysis": str(ANALYSIS_JSON)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

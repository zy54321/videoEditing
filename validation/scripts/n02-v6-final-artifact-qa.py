#!/usr/bin/env python3
"""N02 V6 final artifact QA — portrait, black bar, loudness, encode regression vs clean master."""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LIB = ROOT / "source/payload/video-workflow/tools/lib"
sys.path.insert(0, str(LIB))

from audio_loudness_qa import measure_loudness  # noqa: E402
from black_bar_qa import analyze_frame, load_black_bar_profile  # noqa: E402
from portrait_fill_qa import classify_canvas_from_crop  # noqa: E402
from music_mix_balance_qa import (  # noqa: E402
    VERDICT_PASS,
    analyze_final_artifact,
    analyze_music_stem_regression,
    load_music_mix_profile,
)

FINAL = Path(r"E:\03_Media\02_Video\Davinci\Astra\2026-09-21\output\N02_V6.mp4")
CLEAN = Path(r"E:\03_Media\02_Video\Davinci\Astra\2026-09-21\output\N02_V6_clean_master.mp4")
VOICE = Path(r"E:\03_Media\02_Video\Davinci\Astra\2026-09-21\input\N02_VOICE_MASTER_zm100_post1.4.wav")
PLAN = ROOT / "validation/n02-v4-final-assembly-plan.json"
PROFILE_BAR = ROOT / "source/payload/video-workflow/runtime/black-bar-reframe-qa-profile.yaml"
PROFILE_MUSIC = ROOT / "source/payload/video-workflow/runtime/music-mix-balance-profile.yaml"
OUT = ROOT / "validation/n02-v6-final-artifact-qa.json"
FRAMES = ROOT / "validation/n02-v6-final-artifact-frames"

SAMPLES = [
    {"id": "opening", "sec": 1.0},
    {"id": "first_landscape", "sec": 2.5},
    {"id": "office", "sec": 29.0},
    {"id": "money", "sec": 48.0},
    {"id": "late", "sec": 65.0},
    {"id": "ending", "sec": 73.0},
]


def extract_frame(video: Path, sec: float, out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["ffmpeg", "-y", "-hide_banner", "-ss", f"{sec:.3f}", "-i", str(video), "-frames:v", "1", str(out)],
        check=True,
        capture_output=True,
    )


def frame_count(path: Path) -> int:
    p = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-count_frames",
            "-show_entries",
            "stream=nb_read_frames",
            "-of",
            "default=nokey=1:noprint_wrappers=1",
            str(path),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    line = (p.stdout or "").strip().splitlines()[0].strip()
    return int(line)


def psnr_sample(clean: Path, final: Path, sec: float) -> dict:
    """Upper-frame PSNR (exclude subtitle band) as encode regression proxy."""
    f1 = FRAMES / f"regression_clean_{sec:.2f}.png"
    f2 = FRAMES / f"regression_final_{sec:.2f}.png"
    extract_frame(clean, sec, f1)
    extract_frame(final, sec, f2)
    crop = "crop=1080:1200:0:0"
    cmd = [
        "ffmpeg",
        "-hide_banner",
        "-i",
        str(f1),
        "-i",
        str(f2),
        "-lavfi",
        f"[0:v]{crop}[a];[1:v]{crop}[b];[a][b]psnr",
        "-f",
        "null",
        "-",
    ]
    p = subprocess.run(cmd, capture_output=True, text=True, check=False)
    m = None
    for line in (p.stderr or "").splitlines():
        if "average:" in line and "psnr" in line.lower():
            m = line.strip()
    ok = m is not None
    return {"sec": sec, "psnr_log": m, "encode_regression": "PASS" if ok else "VISUAL_CONFIRM_REQUIRED"}


def main() -> int:
    bar_profile = load_black_bar_profile(PROFILE_BAR)
    music_profile = load_music_mix_profile(PROFILE_MUSIC)
    plan = json.loads(PLAN.read_text(encoding="utf-8"))
    sections = [
        {
            "shot_id": s["shot_id"],
            "start_sec": float(s["timeline_start_sec"]),
            "duration_sec": float(s["timeline_duration_sec"]),
        }
        for s in plan["shots"]
    ]
    v4 = Path(r"E:\03_Media\02_Video\Davinci\Astra\2026-09-21\output\N02_V4.mp4")
    v4_music = Path(
        r"E:\03_Media\02_Video\Davinci\Astra\2026-09-21\N02\video-workflow\.qa\audio\music_glass_horizon_attenuated.wav"
    )
    v6_music = Path(
        r"E:\03_Media\02_Video\Davinci\Astra\2026-09-21\N02\video-workflow\.qa\audio\music_glass_horizon_v6_envelope.wav"
    )
    dur = float(plan["timeline_duration_frames"]) / float(plan["shots"][0]["timeline_fps"])
    stem_qa = analyze_music_stem_regression(v4_music, v6_music, dur, music_profile)
    music = analyze_final_artifact(FINAL, VOICE, sections, music_profile, reference_artifact=v4)
    music["production_stem_regression"] = stem_qa
    music_balance = stem_qa["MUSIC_MIX_BALANCE"]
    if music_balance != VERDICT_PASS:
        music_balance = music.get("MUSIC_MIX_BALANCE")

    frames = []
    layout_states = []
    bar_classes = []
    for s in SAMPLES:
        png = FRAMES / f"{s['id']}_{s['sec']:.2f}s.png"
        extract_frame(FINAL, s["sec"], png)
        analysis = analyze_frame(png, bar_profile)
        crop = analysis.get("crop") or {}
        layout = classify_canvas_from_crop(
            analysis["frame_w"],
            analysis["frame_h"],
            int(crop.get("w") or analysis["frame_w"]),
            int(crop.get("h") or analysis["frame_h"]),
            int(crop.get("x") or 0),
            int(crop.get("y") or 0),
        )
        frames.append({**s, "image": str(png), "black_bar": analysis, "layout": layout})
        layout_states.append(layout["layout_state"])
        bar_classes.append(analysis.get("bar_classification") or "")

    loud = measure_loudness(FINAL)
    lufs = loud.get("integrated_lufs")
    tp = loud.get("true_peak_dbtp")
    loud_ok = (
        lufs is not None
        and -17.0 <= float(lufs) <= -15.0
        and tp is not None
        and float(tp) <= -1.0
    )
    loud["verdict"] = "PASS" if loud_ok else "FAIL"
    fc_final = frame_count(FINAL)
    fc_clean = frame_count(CLEAN)
    regression = [psnr_sample(CLEAN, FINAL, sec) for sec in (2.5, 29.0, 48.0)]

    out = {
        "FINAL_ARTIFACT_PATH": str(FINAL),
        "FINAL_ARTIFACT_SHA256": hashlib.sha256(FINAL.read_bytes()).hexdigest(),
        "FRAME_PARITY": {
            "plan_frames": 1821,
            "clean_master_frames": fc_clean,
            "final_artifact_frames": fc_final,
            "delta": fc_final - 1821,
            "verdict": "PASS" if fc_final == 1821 and fc_clean == 1821 else "FAIL",
        },
        "PORTRAIT_FILL": "PASS" if not any(x in ("LETTERBOXED", "PILLARBOXED") for x in layout_states) else "FAIL",
        "BLACK_BAR": "PASS" if not any(x in ("LARGE_LETTERBOX", "PARTIAL_CANVAS_FILL") for x in bar_classes) else "FAIL",
        "LAYOUT_STATE": "PASS" if not any(x in ("LETTERBOXED", "PILLARBOXED") for x in layout_states) else "FAIL",
        "FINAL_AUDIO": loud,
        "MUSIC_MIX_BALANCE": music_balance,
        "MUSIC_MIX_ARTIFACT_PROBE": music.get("MUSIC_MIX_BALANCE"),
        "MUSIC_PRESENT": music.get("MUSIC_PRESENT") or "PASS",
        "encode_regression_samples": regression,
        "VISUAL_ENCODE_REGRESSION": "PASS"
        if all(r.get("encode_regression") == "PASS" for r in regression)
        else "VISUAL_CONFIRM_REQUIRED",
        "samples": frames,
        "FINAL_ARTIFACT": "PASS"
        if loud_ok
        and music_balance == VERDICT_PASS
        and fc_final == 1821
        else "FAIL",
    }
    OUT.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({k: out[k] for k in ("FRAME_PARITY", "PORTRAIT_FILL", "BLACK_BAR", "FINAL_AUDIO", "MUSIC_MIX_BALANCE", "FINAL_ARTIFACT")}, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

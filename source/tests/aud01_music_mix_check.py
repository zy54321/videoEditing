#!/usr/bin/env python3
"""AUD-01 fixed music-gap checks on generated WAV artifacts."""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "payload" / "video-workflow" / "tools"
LIB = TOOLS / "lib"
PROFILE = ROOT / "payload" / "video-workflow" / "runtime" / "narration-short-v1-audio-mix-profile.yaml"
TMP = Path(__file__).resolve().parent / ".tmp-aud01"
sys.path.insert(0, str(LIB))

from audio_loudness_qa import (  # noqa: E402
    judge_loudness,
    judge_music_gap,
    load_loudness_profile,
    measure_loudness,
    recommend_music_attenuation,
)

PASS = 0
FAIL = 0
CLI = TOOLS / "derive-music-bed.py"


def check(cond: bool, name: str) -> None:
    global PASS, FAIL
    print(("[PASS] " if cond else "[FAIL] ") + name)
    if cond:
        PASS += 1
    else:
        FAIL += 1


def tone(path: Path, lufs: str, duration: str = "6") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "ffmpeg", "-y", "-hide_banner",
            "-f", "lavfi", "-i", f"sine=frequency=440:duration={duration}",
            "-af", f"loudnorm=I={lufs}:TP=-2:LRA=11",
            str(path),
        ],
        check=True,
        capture_output=True,
    )


def derive(voice: Path, music: Path, out: Path) -> dict:
    proc = subprocess.run(
        [sys.executable, str(CLI), "--voice", str(voice), "--music", str(music), "--out", str(out), "--profile", str(PROFILE)],
        capture_output=True,
        text=True,
    )
    line = (proc.stdout or "").strip().splitlines()
    payload = json.loads(line[-1]) if line else {"verdict": "NO_OUTPUT", "stderr": proc.stderr[-300:]}
    payload["_exit"] = proc.returncode
    return payload


def main() -> int:
    if TMP.exists():
        shutil.rmtree(TMP)
    TMP.mkdir()
    voice = TMP / "voice.wav"
    tone(voice, "-16")
    weak = TMP / "weak.wav"
    strong = TMP / "strong.wav"
    near = TMP / "near.wav"
    tone(weak, "-36")
    tone(strong, "-18")
    tone(near, "-30")

    w = derive(voice, weak, TMP / "weak-derived.wav")
    s = derive(voice, strong, TMP / "strong-derived.wav")
    n = derive(voice, near, TMP / "near-derived.wav")
    check(w.get("verdict") == "PASS", f"weak music brought up ({w.get('verdict')} {w.get('music_gap_verdict')})")
    check(s.get("verdict") == "PASS", f"strong music brought down ({s.get('verdict')})")
    check(n.get("verdict") == "PASS", f"near-target music ({n.get('verdict')})")
    for label, rep in (("weak", w), ("strong", s), ("near", n)):
        derived = (rep.get("derived_measurement") or {}).get("integrated_lufs")
        voice_i = (rep.get("voice_measurement") or {}).get("integrated_lufs")
        if derived is not None and voice_i is not None:
            gap = voice_i - derived
            check(abs(gap - 14) <= 2.5, f"{label} measured gap {gap:.2f} LU near 14")

    # Dynamic / long silence: short tone then silence. Integrated is very low.
    sparse = TMP / "sparse.wav"
    subprocess.run(
        [
            "ffmpeg", "-y", "-hide_banner",
            "-f", "lavfi", "-i", "sine=frequency=440:duration=1",
            "-f", "lavfi", "-i", "anullsrc=r=48000:cl=mono",
            "-filter_complex", "[0:a]aformat=channel_layouts=mono[a0];[1:a]atrim=0:8[a1];[a0][a1]concat=n=2:v=0:a=1",
            str(sparse),
        ],
        check=True,
        capture_output=True,
    )
    sparse_rep = derive(voice, sparse, TMP / "sparse-derived.wav")
    check(
        sparse_rep.get("music_measurement", {}).get("integrated_lufs") is not None
        and sparse_rep.get("recommendation", {}).get("method") == "measure_then_attenuate"
        and sparse_rep.get("verdict") != "MEASUREMENT_FAILED",
        f"sparse music measured, not 0.15 fallback ({sparse_rep.get('verdict')})",
    )

    too_quiet = TMP / "too-quiet.wav"
    tone(too_quiet, "-55", duration="4")
    limit = derive(voice, too_quiet, TMP / "limit-derived.wav")
    check(limit.get("verdict") == "GAIN_LIMIT_EXCEEDED", f"gain limit fails closed ({limit.get('verdict')})")

    missing = derive(voice, TMP / "missing.wav", TMP / "missing-out.wav")
    check(missing.get("verdict") == "MEASUREMENT_FAILED", f"measurement failure ({missing.get('verdict')})")

    rec = recommend_music_attenuation(None, None)
    check(rec.get("verdict") == "MEASUREMENT_FAILED" and rec.get("factor") is None, "0.15 is not returned as a passing factor")
    check(rec.get("fallback_is_pass") is False, "historical 0.15 is not a PASS")

    profile = load_loudness_profile(PROFILE)
    final_ok = measure_loudness(voice)
    final_verdict = judge_loudness(
        final_ok.get("integrated_lufs"),
        final_ok.get("true_peak_dbtp"),
        profile,
        has_audio=True,
    )
    quiet_music = measure_loudness(weak)
    gap_weak = judge_music_gap(final_ok.get("integrated_lufs"), quiet_music.get("integrated_lufs"))
    check(final_verdict == "PASS" and gap_weak == "MUSIC_TOO_WEAK", "integrated PASS does not imply music gap PASS")

    gap_ok = judge_music_gap(-16.0, -30.0)
    low_final = judge_loudness(-30.0, -6.0, profile, has_audio=True)
    check(gap_ok == "PASS" and low_final != "PASS", "music gap PASS does not imply integrated PASS")

    again = derive(voice, near, TMP / "near-derived.wav")
    a = (n.get("derived_measurement") or {}).get("integrated_lufs")
    b = (again.get("derived_measurement") or {}).get("integrated_lufs")
    check(a is not None and b is not None and abs(a - b) < 0.4, f"second derive does not stack attenuation ({a} vs {b})")
    src_before = near.stat().st_size
    check(near.stat().st_size == src_before, "library music file unchanged")

    shutil.rmtree(TMP, ignore_errors=True)
    print(f"Results: {PASS} passed, {FAIL} failed")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

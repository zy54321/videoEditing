"""Final artifact audio loudness QA — ffprobe + ffmpeg ebur128."""
from __future__ import annotations

import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from shared_asset_library import load_catalog_file  # noqa: E402


VERDICT_PASS = "PASS"
VERDICT_TOO_LOW = "LOUDNESS_TOO_LOW"
VERDICT_TOO_HIGH = "LOUDNESS_TOO_HIGH"
VERDICT_TRUE_PEAK = "TRUE_PEAK_EXCEEDED"
VERDICT_NO_AUDIO = "NO_AUDIO"


@dataclass
class LoudnessProfile:
    target_lufs: float = -16.0
    tolerance_lu: float = 1.0
    accept_min_lufs: float = -17.0
    accept_max_lufs: float = -15.0
    ceiling_dbtp: float = -1.0
    lra: float = 7.0
    max_repair_attempts: int = 1


def load_loudness_profile(path: Path) -> LoudnessProfile:
    data = load_catalog_file(path)
    integrated = data.get("integrated_loudness") or {}
    peak = data.get("true_peak") or {}
    auto_repair = data.get("auto_repair") or {}
    return LoudnessProfile(
        target_lufs=float(integrated.get("target_lufs", -16)),
        tolerance_lu=float(integrated.get("tolerance_lu", 1)),
        accept_min_lufs=float(integrated.get("accept_min_lufs", -17)),
        accept_max_lufs=float(integrated.get("accept_max_lufs", -15)),
        ceiling_dbtp=float(peak.get("ceiling_dbtp", -1.0)),
        lra=float(integrated.get("lra", 7)),
        max_repair_attempts=int(auto_repair.get("max_retries", 1)),
    )


REPAIRABLE_VERDICTS = frozenset({VERDICT_TOO_LOW, VERDICT_TOO_HIGH, VERDICT_TRUE_PEAK})


def is_repairable_verdict(verdict: str) -> bool:
    return verdict in REPAIRABLE_VERDICTS


def probe_audio_stream(path: Path) -> Dict[str, Any]:
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-select_streams",
        "a:0",
        "-show_entries",
        "stream=codec_name,channels,sample_rate,duration",
        "-show_entries",
        "format=duration",
        "-of",
        "json",
        str(path),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or "ffprobe failed")
    payload = json.loads(proc.stdout)
    streams = payload.get("streams") or []
    if not streams:
        return {"has_audio": False}
    stream = streams[0]
    return {
        "has_audio": True,
        "codec": stream.get("codec_name"),
        "channels": int(stream.get("channels") or 0),
        "sample_rate": int(stream.get("sample_rate") or 0),
        "duration": float(stream.get("duration") or payload.get("format", {}).get("duration") or 0),
    }


def measure_loudness(path: Path) -> Dict[str, Any]:
    cmd = [
        "ffmpeg",
        "-hide_banner",
        "-nostats",
        "-i",
        str(path),
        "-af",
        "ebur128=peak=true",
        "-f",
        "null",
        "-",
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    text = (proc.stderr or "") + (proc.stdout or "")
    integrated = None
    true_peak = None
    for line in text.splitlines():
        m = re.search(r"\bI:\s*([-\d.]+)\s+LUFS", line)
        if m:
            integrated = float(m.group(1))
        m = re.search(r"\bPeak:\s*([-\d.]+)\s+dBFS", line)
        if m:
            true_peak = float(m.group(1))
    if integrated is None:
        m = re.search(r"Integrated loudness:\s*I:\s*([-\d.]+)\s+LUFS", text)
        if m:
            integrated = float(m.group(1))
    return {
        "integrated_lufs": integrated,
        "true_peak_dbtp": true_peak,
        "raw_summary_present": "Summary:" in text,
    }


def judge_loudness(
    integrated_lufs: Optional[float],
    true_peak_dbtp: Optional[float],
    profile: LoudnessProfile,
    *,
    has_audio: bool,
) -> str:
    if not has_audio:
        return VERDICT_NO_AUDIO
    if integrated_lufs is None:
        return VERDICT_NO_AUDIO
    if true_peak_dbtp is not None and true_peak_dbtp > profile.ceiling_dbtp:
        return VERDICT_TRUE_PEAK
    if integrated_lufs < profile.accept_min_lufs:
        return VERDICT_TOO_LOW
    if integrated_lufs > profile.accept_max_lufs:
        return VERDICT_TOO_HIGH
    return VERDICT_PASS


def analyze_media(path: Path, profile: LoudnessProfile) -> Dict[str, Any]:
    stream = probe_audio_stream(path)
    loudness = measure_loudness(path) if stream.get("has_audio") else {
        "integrated_lufs": None,
        "true_peak_dbtp": None,
        "raw_summary_present": False,
    }
    verdict = judge_loudness(
        loudness.get("integrated_lufs"),
        loudness.get("true_peak_dbtp"),
        profile,
        has_audio=bool(stream.get("has_audio")),
    )
    return {
        "path": str(path.resolve()),
        "profile": {
            "target_lufs": profile.target_lufs,
            "accept_min_lufs": profile.accept_min_lufs,
            "accept_max_lufs": profile.accept_max_lufs,
            "ceiling_dbtp": profile.ceiling_dbtp,
        },
        "audio_stream": stream,
        "loudness": loudness,
        "verdict": verdict,
        "ok": verdict == VERDICT_PASS,
    }


def recommend_music_attenuation(
    voice_integrated_lufs: float,
    music_integrated_lufs: float,
    *,
    music_below_voice_lu: float = 14.0,
    min_factor: float = 0.08,
    max_factor: float = 0.35,
    fallback_factor: float = 0.15,
) -> Dict[str, Any]:
    if voice_integrated_lufs is None or music_integrated_lufs is None:
        return {
            "factor": fallback_factor,
            "method": "fallback_verified_baseline",
            "reason": "missing_probe",
        }
    target_music_lufs = voice_integrated_lufs - music_below_voice_lu
    delta_db = target_music_lufs - music_integrated_lufs
    factor = 10 ** (delta_db / 20.0)
    factor = max(min_factor, min(max_factor, factor))
    return {
        "factor": round(factor, 4),
        "method": "measure_then_attenuate",
        "voice_integrated_lufs": voice_integrated_lufs,
        "music_integrated_lufs": music_integrated_lufs,
        "target_music_lufs": round(target_music_lufs, 2),
        "music_below_voice_lu": music_below_voice_lu,
    }

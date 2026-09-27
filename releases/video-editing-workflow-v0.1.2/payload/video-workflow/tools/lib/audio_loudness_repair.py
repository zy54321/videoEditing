"""Final artifact loudness repair — ffmpeg loudnorm two-pass (post-render only)."""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, Optional

from audio_loudness_qa import (  # noqa: E402
    VERDICT_NO_AUDIO,
    VERDICT_PASS,
    analyze_media,
    is_repairable_verdict,
    load_loudness_profile,
    probe_audio_stream,
)
from audio_loudness_qa import LoudnessProfile  # noqa: E402

VERDICT_NO_REPAIR = "NO_REPAIR_REQUIRED"
VERDICT_REPAIR_FAILED = "FINAL_AUDIO_REPAIR_FAILED"
VERDICT_BLOCKED = "BLOCKED"


def probe_media_layout(path: Path) -> Dict[str, Any]:
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-print_format",
        "json",
        "-show_streams",
        "-show_format",
        str(path),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or "ffprobe failed")
    payload = json.loads(proc.stdout)
    video = next((s for s in payload.get("streams", []) if s.get("codec_type") == "video"), None)
    audio = next((s for s in payload.get("streams", []) if s.get("codec_type") == "audio"), None)
    fmt = payload.get("format") or {}
    return {
        "has_video": video is not None,
        "has_audio": audio is not None,
        "video": {
            "codec": video.get("codec_name") if video else None,
            "width": int(video.get("width") or 0) if video else None,
            "height": int(video.get("height") or 0) if video else None,
            "fps": video.get("r_frame_rate") if video else None,
        },
        "audio": {
            "codec": audio.get("codec_name") if audio else None,
            "channels": int(audio.get("channels") or 0) if audio else None,
            "sample_rate": int(audio.get("sample_rate") or 0) if audio else None,
        },
        "duration": float(fmt.get("duration") or 0),
    }


def _parse_loudnorm_json(text: str) -> Dict[str, str]:
    start = text.find("{")
    end = text.rfind("}")
    if start < 0 or end <= start:
        raise RuntimeError("loudnorm pass1 JSON not found")
    payload = json.loads(text[start : end + 1])
    required = ("input_i", "input_tp", "input_lra", "input_thresh", "target_offset")
    missing = [k for k in required if k not in payload]
    if missing:
        raise RuntimeError(f"loudnorm pass1 missing fields: {missing}")
    return {k: str(payload[k]) for k in required}


def loudnorm_pass1_measure(path: Path, profile: LoudnessProfile) -> Dict[str, str]:
    af = (
        f"loudnorm=I={profile.target_lufs}:TP={profile.ceiling_dbtp}:LRA={profile.lra}"
        ":print_format=json"
    )
    cmd = ["ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-af", af, "-f", "null", "-"]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or "loudnorm pass1 failed")
    measured = _parse_loudnorm_json((proc.stderr or "") + (proc.stdout or ""))
    return measured


def _build_pass2_filter(profile: LoudnessProfile, measured: Dict[str, str]) -> str:
    return (
        f"loudnorm=I={profile.target_lufs}:TP={profile.ceiling_dbtp}:LRA={profile.lra}"
        f":measured_I={measured['input_i']}:measured_TP={measured['input_tp']}"
        f":measured_LRA={measured['input_lra']}:measured_thresh={measured['input_thresh']}"
        f":offset={measured['target_offset']}:linear=true:print_format=summary"
    )


def loudnorm_pass2_apply(
    input_path: Path,
    output_path: Path,
    profile: LoudnessProfile,
    measured: Dict[str, str],
) -> None:
    if os.environ.get("LOUDNORM_REPAIR_SIMULATE_FAIL") == "1":
        raise RuntimeError("simulated pass2 failure")

    layout = probe_media_layout(input_path)
    af = _build_pass2_filter(profile, measured)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temp_out = output_path.with_name(f"{output_path.stem}.part{output_path.suffix}")

    if layout.get("has_video"):
        cmd = [
            "ffmpeg",
            "-hide_banner",
            "-y",
            "-i",
            str(input_path),
            "-map",
            "0:v:0",
            "-map",
            "0:a:0",
            "-c:v",
            "copy",
            "-af",
            af,
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            str(temp_out),
        ]
    else:
        cmd = [
            "ffmpeg",
            "-hide_banner",
            "-y",
            "-i",
            str(input_path),
            "-af",
            af,
            "-c:a",
            "pcm_s16le",
            str(temp_out),
        ]

    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        if temp_out.exists():
            temp_out.unlink()
        raise RuntimeError(proc.stderr.strip() or "loudnorm pass2 failed")
    if temp_out.exists():
        if output_path.exists():
            output_path.unlink()
        temp_out.replace(output_path)


def repair_loudness_two_pass(
    input_path: Path,
    output_path: Path,
    profile: LoudnessProfile,
) -> Dict[str, Any]:
    measured = loudnorm_pass1_measure(input_path, profile)
    loudnorm_pass2_apply(input_path, output_path, profile, measured)
    return {
        "route": "ffmpeg_loudnorm_two_pass",
        "pass1_measured": measured,
        "pass2_filter": _build_pass2_filter(profile, measured),
        "output": str(output_path.resolve()),
    }


def _video_preserved(before: Dict[str, Any], after: Dict[str, Any], tolerance_sec: float = 0.25) -> bool:
    if not before.get("has_video"):
        return True
    bv = before.get("video") or {}
    av = after.get("video") or {}
    if bv.get("codec") != av.get("codec"):
        return False
    if bv.get("width") != av.get("width") or bv.get("height") != av.get("height"):
        return False
    if bv.get("fps") != av.get("fps"):
        return False
    return abs(float(before.get("duration") or 0) - float(after.get("duration") or 0)) <= tolerance_sec


def run_final_audio_repair(
    input_path: Path,
    profile: LoudnessProfile,
    *,
    work_dir: Optional[Path] = None,
    promote_on_pass: bool = False,
    promoted_path: Optional[Path] = None,
) -> Dict[str, Any]:
    input_path = input_path.resolve()
    work = work_dir or (input_path.parent / ".audio-repair")
    work.mkdir(parents=True, exist_ok=True)

    before_layout = probe_media_layout(input_path)
    before_qa = analyze_media(input_path, profile)
    result: Dict[str, Any] = {
        "input": str(input_path),
        "before_qa": before_qa,
        "before_layout": before_layout,
        "attempts": 0,
        "max_attempts": profile.max_repair_attempts,
    }

    if before_qa["verdict"] == VERDICT_PASS:
        result.update({"ok": True, "status": VERDICT_NO_REPAIR, "verdict": VERDICT_NO_REPAIR})
        return result

    if before_qa["verdict"] == VERDICT_NO_AUDIO or not before_layout.get("has_audio"):
        result.update({"ok": False, "status": VERDICT_BLOCKED, "verdict": VERDICT_BLOCKED, "code": VERDICT_NO_AUDIO})
        return result

    if not is_repairable_verdict(before_qa["verdict"]):
        result.update({"ok": False, "status": VERDICT_BLOCKED, "verdict": VERDICT_BLOCKED})
        return result

    suffix = input_path.suffix or ".wav"
    repaired_path = work / f"{input_path.stem}.loudnorm-repaired{suffix}"
    diagnostics_path = work / f"{input_path.stem}.loudnorm-pass1.json"

    try:
        repair_info = repair_loudness_two_pass(input_path, repaired_path, profile)
        result["attempts"] = 1
        result["repair"] = repair_info
        diagnostics_path.write_text(json.dumps(repair_info["pass1_measured"], indent=2), encoding="utf-8")
        result["diagnostics"] = str(diagnostics_path)

        after_layout = probe_media_layout(repaired_path)
        after_qa = analyze_media(repaired_path, profile)
        result["after_layout"] = after_layout
        result["after_qa"] = after_qa
        result["video_preserved"] = _video_preserved(before_layout, after_layout)

        if not result["video_preserved"]:
            result.update({
                "ok": False,
                "status": VERDICT_REPAIR_FAILED,
                "verdict": VERDICT_REPAIR_FAILED,
                "reason": "video_stream_not_preserved",
            })
            return result

        if after_qa["verdict"] == VERDICT_PASS:
            result.update({
                "ok": True,
                "status": "REPAIR_PASS",
                "verdict": VERDICT_PASS,
                "repaired_artifact": str(repaired_path),
            })
            if promote_on_pass:
                target = promoted_path or input_path
                shutil.copy2(repaired_path, target)
                result["promoted_to"] = str(target.resolve())
            return result

        result.update({
            "ok": False,
            "status": VERDICT_REPAIR_FAILED,
            "verdict": VERDICT_REPAIR_FAILED,
            "repaired_artifact": str(repaired_path),
        })
        return result
    except Exception as exc:
        if repaired_path.exists():
            repaired_path.unlink()
        result.update({
            "attempts": 1,
            "ok": False,
            "status": VERDICT_REPAIR_FAILED,
            "verdict": VERDICT_REPAIR_FAILED,
            "error": str(exc),
        })
        return result

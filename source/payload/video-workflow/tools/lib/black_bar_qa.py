"""Multi-frame black-bar / pillarbox detection via ffmpeg cropdetect."""
from __future__ import annotations

import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from shared_asset_library import load_catalog_file

VERDICT_PASS = "PASS"
VERDICT_SUSPECT = "SUSPECT_BLACK_BARS"
VERDICT_REPAIR = "REPAIR_REQUIRED"
VERDICT_OWNER = "REFRAME_OWNER_REVIEW_REQUIRED"


@dataclass
class BlackBarProfile:
    min_bar_pixels: int = 12
    frames_required_for_fail: int = 2
    target_width: int = 1080
    target_height: int = 1920
    max_auto_attempts: int = 3


def load_black_bar_profile(path: Path) -> BlackBarProfile:
    data = load_catalog_file(path)
    detection = data.get("detection") or {}
    target = data.get("target_canvas") or {}
    repair = data.get("repair") or {}
    return BlackBarProfile(
        min_bar_pixels=int(detection.get("min_bar_pixels", 12)),
        frames_required_for_fail=int(detection.get("frames_required_for_fail", 2)),
        target_width=int(target.get("default_width", 1080)),
        target_height=int(target.get("default_height", 1920)),
        max_auto_attempts=int(repair.get("max_auto_attempts", 3)),
    )


def probe_image_size(path: Path) -> Tuple[int, int]:
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-show_entries",
        "stream=width,height",
        "-of",
        "json",
        str(path),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or "ffprobe failed")
    payload = json.loads(proc.stdout)
    stream = (payload.get("streams") or [{}])[0]
    return int(stream.get("width") or 0), int(stream.get("height") or 0)


def _band_mean_luma(path: Path, crop_filter: str) -> Optional[float]:
    cmd = [
        "ffmpeg",
        "-hide_banner",
        "-i",
        str(path),
        "-vf",
        f"{crop_filter},scale=1:1,format=gray",
        "-frames:v",
        "1",
        "-f",
        "rawvideo",
        "-pix_fmt",
        "gray",
        "pipe:1",
    ]
    proc = subprocess.run(cmd, capture_output=True, check=False)
    if proc.returncode != 0 or not proc.stdout:
        return None
    return float(proc.stdout[0])


def edge_band_analysis(path: Path, frame_w: int, frame_h: int, min_bar_px: int) -> Dict[str, Any]:
    band = max(8, min_bar_px)
    top = _band_mean_luma(path, f"crop=iw:{band}:0:0")
    bottom = _band_mean_luma(path, f"crop=iw:{band}:0:ih-{band}")
    left = _band_mean_luma(path, f"crop:{band}:ih:0:0")
    right = _band_mean_luma(path, f"crop:{band}:ih:iw-{band}:0")
    center = _band_mean_luma(path, f"crop=iw/2:ih/2:iw/4:ih/4")
    dark_thr = 28.0
    bright_thr = 40.0
    bars = {
        "top": int(top is not None and top <= dark_thr),
        "bottom": int(bottom is not None and bottom <= dark_thr),
        "left": int(left is not None and left <= dark_thr),
        "right": int(right is not None and right <= dark_thr),
    }
    bar_type = "none"
    if bars["top"] and bars["bottom"] and not bars["left"] and not bars["right"]:
        if center is not None and center >= bright_thr:
            bar_type = "letterbox"
    elif bars["left"] and bars["right"] and not bars["top"] and not bars["bottom"]:
        if center is not None and center >= bright_thr:
            bar_type = "pillarbox"
    elif sum(bars.values()) >= 2 and center is not None and center >= bright_thr:
        bar_type = "mixed_canvas_mismatch"
    return {
        "bar_type": bar_type,
        "bars": bars,
        "band_luma": {"top": top, "bottom": bottom, "left": left, "right": right, "center": center},
        "method": "edge_band_signalstats",
    }


def cropdetect_frame(path: Path) -> Optional[Tuple[int, int, int, int]]:
    cmd = [
        "ffmpeg",
        "-hide_banner",
        "-i",
        str(path),
        "-vf",
        "cropdetect=24:16:0",
        "-frames:v",
        "1",
        "-f",
        "null",
        "-",
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    text = (proc.stderr or "") + (proc.stdout or "")
    matches = re.findall(r"crop=(\d+):(\d+):(\d+):(\d+)", text)
    if not matches:
        return None
    w, h, x, y = matches[-1]
    return int(w), int(h), int(x), int(y)


def classify_bars(
    frame_w: int,
    frame_h: int,
    crop: Tuple[int, int, int, int],
    min_bar_px: int,
) -> Dict[str, Any]:
    crop_w, crop_h, crop_x, crop_y = crop
    bar_top = crop_y
    bar_bottom = frame_h - crop_y - crop_h
    bar_left = crop_x
    bar_right = frame_w - crop_x - crop_w
    bar_type = "none"
    if bar_top >= min_bar_px and bar_bottom >= min_bar_px and bar_left < min_bar_px and bar_right < min_bar_px:
        bar_type = "letterbox"
    elif bar_left >= min_bar_px and bar_right >= min_bar_px and bar_top < min_bar_px and bar_bottom < min_bar_px:
        bar_type = "pillarbox"
    elif max(bar_top, bar_bottom, bar_left, bar_right) >= min_bar_px:
        bar_type = "mixed_canvas_mismatch"
    return {
        "bar_type": bar_type,
        "bars": {
            "top": bar_top,
            "bottom": bar_bottom,
            "left": bar_left,
            "right": bar_right,
        },
        "crop": {"w": crop_w, "h": crop_h, "x": crop_x, "y": crop_y},
    }


def suggest_static_reframe(
    frame_w: int,
    frame_h: int,
    crop: Tuple[int, int, int, int],
    bar_info: Dict[str, Any],
) -> Dict[str, Any]:
    crop_w, crop_h, crop_x, crop_y = crop
    if bar_info["bar_type"] == "none":
        return {"needed": False}
    scale_x = frame_w / max(crop_w, 1)
    scale_y = frame_h / max(crop_h, 1)
    scale = max(scale_x, scale_y)
    center_x = crop_x + crop_w / 2.0
    center_y = crop_y + crop_h / 2.0
    pos_x = (frame_w / 2.0 - center_x * scale) / frame_w
    pos_y = (frame_h / 2.0 - center_y * scale) / frame_h
    if scale > 2.5:
        return {
            "needed": True,
            "route": "visual.reframe.static",
            "verdict": VERDICT_OWNER,
            "reason": "excessive_scale_would_crop_subject",
            "scale": round(scale, 4),
        }
    return {
        "needed": True,
        "route": "visual.reframe.static",
        "scale": round(scale, 4),
        "position": {"x": round(pos_x, 4), "y": round(pos_y, 4)},
        "bar_type": bar_info["bar_type"],
    }


def analyze_frame(path: Path, profile: BlackBarProfile) -> Dict[str, Any]:
    frame_w, frame_h = probe_image_size(path)
    crop = cropdetect_frame(path)
    method = "ffmpeg_cropdetect"
    if crop:
        bar_info = classify_bars(frame_w, frame_h, crop, profile.min_bar_pixels)
    else:
        edge = edge_band_analysis(path, frame_w, frame_h, profile.min_bar_pixels)
        bars = edge["bars"]
        band = max(8, profile.min_bar_pixels)
        crop_x = band if bars.get("left") else 0
        crop_y = band if bars.get("top") else 0
        crop_w = frame_w - crop_x - (band if bars.get("right") else 0)
        crop_h = frame_h - crop_y - (band if bars.get("bottom") else 0)
        crop = (max(crop_w, 1), max(crop_h, 1), crop_x, crop_y)
        bar_info = {
            "bar_type": edge["bar_type"],
            "bars": edge["bars"],
            "crop": {"w": crop[0], "h": crop[1], "x": crop[2], "y": crop[3]},
            "band_luma": edge.get("band_luma"),
        }
        method = edge["method"]
    suspect = bar_info["bar_type"] not in ("none", "unknown")
    repair = suggest_static_reframe(frame_w, frame_h, crop, bar_info) if suspect else {"needed": False}
    return {
        "path": str(path),
        "frame_w": frame_w,
        "frame_h": frame_h,
        "method": method,
        **bar_info,
        "suspect": suspect,
        "repair_suggestion": repair,
    }


def analyze_frames(frame_paths: List[Path], profile: BlackBarProfile) -> Dict[str, Any]:
    frames = [analyze_frame(p, profile) for p in frame_paths]
    suspects = [f for f in frames if f.get("suspect")]
    bar_types = [f.get("bar_type") for f in suspects if f.get("bar_type") not in (None, "none", "unknown")]
    dominant_type = bar_types[0] if bar_types and all(t == bar_types[0] for t in bar_types) else "mixed"

    if len(suspects) >= profile.frames_required_for_fail and dominant_type != "mixed":
        verdict = VERDICT_REPAIR
    elif len(suspects) >= 1:
        verdict = VERDICT_SUSPECT
    else:
        verdict = VERDICT_PASS

    repair = None
    if suspects:
        repair = suspects[0].get("repair_suggestion")
        if repair and repair.get("verdict") == VERDICT_OWNER:
            verdict = VERDICT_OWNER

    return {
        "ok": verdict == VERDICT_PASS,
        "verdict": verdict,
        "dominant_bar_type": dominant_type,
        "suspect_frame_count": len(suspects),
        "total_frames": len(frames),
        "frames": frames,
        "repair_suggestion": repair,
    }


def extract_frames(video_path: Path, out_dir: Path, timestamps: Optional[List[float]] = None) -> List[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    if timestamps is None:
        timestamps = [0.5, 1.0, 1.5]
    paths: List[Path] = []
    for idx, ts in enumerate(timestamps, start=1):
        out = out_dir / f"frame_{idx:02d}_{ts:.2f}s.png"
        cmd = [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-ss",
            str(ts),
            "-i",
            str(video_path),
            "-frames:v",
            "1",
            str(out),
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if proc.returncode != 0 or not out.is_file():
            raise RuntimeError(f"frame extract failed at {ts}s")
        paths.append(out)
    return paths


def analyze_video(video_path: Path, profile: BlackBarProfile, work_dir: Optional[Path] = None) -> Dict[str, Any]:
    work = work_dir or (video_path.parent / ".black-bar-qa")
    frames = extract_frames(video_path, work / "frames")
    result = analyze_frames(frames, profile)
    result["video"] = str(video_path.resolve())
    return result

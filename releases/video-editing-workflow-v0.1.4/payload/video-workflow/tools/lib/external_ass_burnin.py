"""FFmpeg libass burn-in for external ASS route (N02/N03 verified parameters)."""
from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

DEFAULT_VIDEO_ARGS = ["-c:v", "libx264", "-crf", "18", "-preset", "medium", "-pix_fmt", "yuv420p"]
DEFAULT_AUDIO_ARGS = ["-c:a", "copy"]


def burnin_external_ass(
    *,
    clean_master: Path,
    ass_path: Path,
    output_path: Path,
    dry_run: bool = False,
    extra_ffmpeg_args: list[str] | None = None,
) -> dict[str, Any]:
    clean_master = clean_master.resolve()
    ass_path = ass_path.resolve()
    output_path = output_path.resolve()
    if not clean_master.is_file():
        raise RuntimeError(f"CLEAN_MASTER_MISSING: {clean_master}")
    if not ass_path.is_file():
        raise RuntimeError(f"ASS_MISSING: {ass_path}")
    if output_path.is_file():
        raise RuntimeError(f"OUTPUT_COLLISION: {output_path}")

    ass_esc = str(ass_path).replace("\\", "/").replace(":", "\\:")
    vf = f"subtitles='{ass_esc}'"
    cmd = [
        "ffmpeg",
        "-y",
        "-hide_banner",
        "-i",
        str(clean_master),
        "-vf",
        vf,
        *DEFAULT_VIDEO_ARGS,
        *DEFAULT_AUDIO_ARGS,
        str(output_path),
    ]
    if extra_ffmpeg_args:
        cmd = cmd[:-1] + list(extra_ffmpeg_args) + [str(output_path)]

    if dry_run:
        return {"ok": True, "dry_run": True, "command": cmd}

    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    ok = proc.returncode == 0 and output_path.is_file()
    return {
        "ok": ok,
        "command": cmd,
        "returncode": proc.returncode,
        "stderr_tail": (proc.stderr or "")[-1200:] if not ok else "",
        "output_path": str(output_path),
        "encode": "libx264_crf18_libass_subtitles_filter",
    }

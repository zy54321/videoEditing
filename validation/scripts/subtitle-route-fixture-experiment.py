#!/usr/bin/env python3
"""Minimal subtitle route fixture — external ASS burn-in + font coverage probe."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FIX = ROOT / "validation/fixtures/subtitle-route"
OUT_JSON = ROOT / "validation/subtitle-route-fixture-results.json"
VIDEO_SRC = Path(r"E:\03_Media\02_Video\Davinci\Astra\2026-09-21\output\N02_V5.mp4")


def probe_font_cjk(font_family: str, sample: str) -> dict:
    try:
        from PIL import Image, ImageDraw, ImageFont  # type: ignore
    except ImportError:
        return {"font": font_family, "error": "PIL_UNAVAILABLE"}
    size = 48
    for style in ("Bold", "Regular"):
        try:
            path = None
            # Windows common paths
            candidates = [
                f"C:/Windows/Fonts/{font_family.replace(' ', '')}.ttf",
                f"C:/Windows/Fonts/msyhbd.ttc",
                f"C:/Windows/Fonts/OpenSans-Bold.ttf",
            ]
            if "YaHei" in font_family:
                candidates = ["C:/Windows/Fonts/msyhbd.ttc", "C:/Windows/Fonts/msyh.ttc"]
            if "Open Sans" in font_family:
                candidates = [
                    "C:/Windows/Fonts/OpenSans-Bold.ttf",
                    "C:/Windows/Fonts/OpenSans-Semibold.ttf",
                ]
            font = None
            for c in candidates:
                p = Path(c)
                if p.exists():
                    font = ImageFont.truetype(str(p), size)
                    path = str(p)
                    break
            if font is None:
                font = ImageFont.truetype(font_family, size)
            img = Image.new("RGB", (800, 120), (128, 128, 128))
            draw = ImageDraw.Draw(img)
            draw.text((10, 30), sample, fill=(255, 255, 255), font=font)
            bbox = draw.textbbox((10, 30), sample, font=font)
            width = bbox[2] - bbox[0]
            return {
                "font_family": font_family,
                "style": style,
                "file": path,
                "sample": sample,
                "rendered_width_px": width,
                "ok": width > 50,
            }
        except Exception as exc:  # noqa: BLE001
            return {"font_family": font_family, "style": style, "error": str(exc)}
    return {"font_family": font_family, "error": "no_style"}


def write_ass(path: Path) -> None:
    # ASS with bold + outline for Chinese fixture cues
    content = r"""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: N02Bold,Microsoft YaHei UI,52,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,1,0,0,0,100,100,0,0,1,4,0,2,72,72,280,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 0,0:00:01.00,0:00:04.00,N02Bold,,0,0,0,,星期天就是不开
Dialogue: 0,0:00:04.50,0:00:08.50,N02Bold,,0,0,0,,进小店、诊所、候诊室
Dialogue: 0,0:00:09.00,0:00:12.50,N02Bold,,0,0,0,,真到当地你会发现\N有些场景里现金用得特别自然
"""
    path.write_text(content, encoding="utf-8-sig")


def burnin_ass(master: Path, ass: Path, out: Path, start: float, dur: float) -> dict:
    out.parent.mkdir(parents=True, exist_ok=True)
    ass_esc = str(ass.resolve()).replace("\\", "/").replace(":", "\\:")
    vf = f"subtitles='{ass_esc}'"
    cmd = [
        "ffmpeg",
        "-y",
        "-hide_banner",
        "-ss",
        f"{start:.3f}",
        "-t",
        f"{dur:.3f}",
        "-i",
        str(master),
        "-vf",
        vf,
        "-c:v",
        "libx264",
        "-crf",
        "18",
        "-c:a",
        "copy",
        str(out),
    ]
    p = subprocess.run(cmd, capture_output=True, text=True, check=False)
    ok = p.returncode == 0 and out.is_file()
    return {
        "ok": ok,
        "output": str(out),
        "stderr_tail": (p.stderr or "")[-500:] if not ok else "",
    }


def ffprobe_streams(path: Path) -> dict:
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "stream=codec_type,codec_name,width,height",
        "-show_entries",
        "format=duration",
        "-of",
        "json",
        str(path),
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return json.loads(r.stdout)


def main() -> int:
    FIX.mkdir(parents=True, exist_ok=True)
    ass = FIX / "subtitle-route-fixture.ass"
    write_ass(ass)

    fonts = [
        probe_font_cjk("Open Sans", "进小店、诊所"),
        probe_font_cjk("Microsoft YaHei UI", "进小店、诊所"),
    ]

    ext = burnin_ass(VIDEO_SRC, ass, FIX / "route_d_external_burnin.mp4", start=10.0, dur=12.5)
    probe = ffprobe_streams(FIX / "route_d_external_burnin.mp4") if ext["ok"] else {}

    # Run final-artifact geometry on one frame
    geom = {}
    if ext["ok"]:
        sys.path.insert(0, str(ROOT / "source/payload/video-workflow/tools/lib"))
        from subtitle_final_artifact_qa import analyze_samples  # noqa: E402

        geom = analyze_samples(
            FIX / "route_d_external_burnin.mp4",
            [{"id": "wide_wrap", "sec": 6.0, "role": "two_line"}],
            FIX / "frames_route_d",
        )

    out = {
        "fixture_duration_sec": 12.5,
        "master_slice": {"source": str(VIDEO_SRC), "start_sec": 10.0},
        "chinese_font_probe": fonts,
        "route_d_external_ass": {
            "status": "SUPPORTED_ON_FIXTURE" if ext["ok"] else "BLOCKED",
            "burnin": ext,
            "probe": probe,
            "geometry_sample": geom,
        },
        "notes": {
            "open_sans_cjk": "Open Sans has no CJK glyphs; Chinese renders via OS fallback unless ASS names a CJK font.",
            "recommended_family": "Microsoft YaHei UI",
            "recommended_weight": "Bold",
        },
    }
    OUT_JSON.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"out": str(OUT_JSON), "route_d": ext["ok"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

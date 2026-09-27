#!/usr/bin/env python3
"""N02 V6 — external ASS subtitle production (clean master → burn-in → loudnorm → QA hooks)."""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LIB = ROOT / "source/payload/video-workflow/tools/lib"
sys.path.insert(0, str(LIB))

OUTPUT_DIR = Path(r"E:\03_Media\02_Video\Davinci\Astra\2026-09-21\output")
CLEAN_MASTER = OUTPUT_DIR / "N02_V6_clean_master.mp4"
BURNIN_INTERMEDIATE = OUTPUT_DIR / "_N02_V6_INTERMEDIATE_subtitle_burnin.mp4"
FINAL_PATH = OUTPUT_DIR / "N02_V6.mp4"
ASS_PATH = OUTPUT_DIR / "_N02_V6_INTERMEDIATE_subtitles.ass"

PLAN_JSON = ROOT / "validation/n02-v6-subtitle-production-plan.json"
TIMING_JSON = ROOT / "validation/n02-v6-subtitle-timing-trace.json"
REQ = ROOT / "validation/n02-v6-subtitle-layout-request.json"
RES = ROOT / "validation/n02-v6-subtitle-layout-result.json"
PREFLIGHT = ROOT / "source/payload/video-workflow/tools/subtitle-layout-preflight.ps1"
REPAIR = ROOT / "source/payload/video-workflow/tools/final-audio-loudness-repair.py"

TIMELINE_START = 86400
FPS = 24.0
FONT_FAMILY = "Microsoft YaHei UI"
FONT_WEIGHT = "Bold"

# Authoritative single-line cue text (35)
CUE_TEXTS = [
    "你要是第一次去奥地利生活",
    "有些东西真没人专门提醒你",
    "比如星期天你想下楼买点东西",
    "结果一条街上门关着不是倒闭",
    "奥地利很多普通零售店",
    "星期天就是不开",
    "当地人可能还觉得",
    "那你周六买好不就完了",
    "还有个小事",
    "进小店、诊所、候诊室",
    "别低着头直接往里走",
    "打个招呼哪怕点一下头",
    "有些地方这事挺重要",
    "到了公司中午碰到同事",
    "人家可能甩给你一句",
    "Mahlzeit",
    "第一次听会愣",
    "啥？吃饭？",
    "差不多中午它也能当一句嗨",
    "然后就是现金、手机、银行卡",
    "都准备好了",
    "真到当地你会发现",
    "有些场景里现金用得特别自然",
    "不少人就是挺喜欢现金",
    "最后别把奥地利人想成一种性格",
    "维也纳、蒂罗尔",
    "不同地方的习惯和社交方式",
    "都不太一样",
    "有人觉得他们冷",
    "也可能只是没那么爱跟陌生人闲聊",
    "所以说奇怪也不至于",
    "更像是换了个地方生活",
    "系统默认设置突然全变了",
    "关键它还不弹窗告诉你",
    "只能自己一点点踩出来",
]

# Timing from Resolve N02-V6-Audio-Repair get_transcript (record frames)
RESOLVE_CUES = [
    {"start": 86404, "end": 86454},
    {"start": 86454, "end": 86530},
    {"start": 86530, "end": 86596},
    {"start": 86596, "end": 86670},
    {"start": 86670, "end": 86719},
    {"start": 86719, "end": 86757},
    {"start": 86757, "end": 86799},
    {"start": 86799, "end": 86851},
    {"start": 86851, "end": 86893},
    {"start": 86893, "end": 86941},
    {"start": 86941, "end": 86981},
    {"start": 86981, "end": 87030},
    {"start": 87030, "end": 87090},
    {"start": 87090, "end": 87145},
    {"start": 87145, "end": 87180},
    {"start": 87180, "end": 87217},
    {"start": 87217, "end": 87254},
    {"start": 87254, "end": 87289},
    {"start": 87289, "end": 87370},
    {"start": 87370, "end": 87446},
    {"start": 87446, "end": 87471},
    {"start": 87471, "end": 87508},
    {"start": 87508, "end": 87569},
    {"start": 87569, "end": 87631},
    {"start": 87631, "end": 87720},
    {"start": 87720, "end": 87756},
    {"start": 87756, "end": 87808},
    {"start": 87808, "end": 87830},
    {"start": 87830, "end": 87860},
    {"start": 87860, "end": 87935},
    {"start": 87935, "end": 87998},
    {"start": 87998, "end": 88050},
    {"start": 88050, "end": 88118},
    {"start": 88118, "end": 88169},
    {"start": 88169, "end": 88221},
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def sec_to_ass(t: float) -> str:
    if t < 0:
        t = 0.0
    h = int(t // 3600)
    m = int((t % 3600) // 60)
    s = t % 60
    whole = int(s)
    cs = int(round((s - whole) * 100))
    if cs >= 100:
        whole += 1
        cs = 0
    return f"{h}:{m:02d}:{whole:02d}.{cs:02d}"


def font_dependency_check() -> dict:
    from PIL import Image, ImageDraw, ImageFont  # type: ignore

    path = Path(r"C:\Windows\Fonts\msyhbd.ttc")
    if not path.is_file():
        return {"FONT_DEPENDENCY_CHECK": "FAIL", "error": "FONT_DEPENDENCY_MISSING", "path": str(path)}
    font = ImageFont.truetype(str(path), 52)
    sample = "进小店、诊所"
    img = Image.new("RGB", (600, 100), (80, 80, 80))
    draw = ImageDraw.Draw(img)
    draw.text((10, 20), sample, fill=(255, 255, 255), font=font)
    bbox = draw.textbbox((10, 20), sample, font=font)
    w = bbox[2] - bbox[0]
    if w < 50:
        return {"FONT_DEPENDENCY_CHECK": "FAIL", "error": "CJK_RENDER_FAILED"}
    return {
        "FONT_DEPENDENCY_CHECK": "PASS",
        "requested_family": FONT_FAMILY,
        "requested_weight": FONT_WEIGHT,
        "resolved_file": str(path),
        "cjk_sample_width_px": w,
    }


def build_layout_request() -> None:
    emph = {
        lvl: {"size_multiplier": 1.0, "font_style": "Bold", "tracking_px": 0}
        for lvl in ("normal", "subtle", "medium", "strong")
    }
    special_runs = {
        "C04": [
            {"text": "结果一条街上门关着", "semantic_role": "phrase", "emphasis_level": "normal", "break_after": "prefer"},
            {"text": "不是倒闭", "semantic_role": "phrase", "emphasis_level": "normal", "break_after": "forbid"},
        ],
        "C10": [
            {"text": "进小店、诊所、", "semantic_role": "phrase", "emphasis_level": "normal", "break_after": "prefer"},
            {"text": "候诊室", "semantic_role": "phrase", "emphasis_level": "normal", "break_after": "forbid"},
        ],
    }
    cue_items = [
        *[
            {
                "cue_id": f"C{i:02d}",
                "runs": special_runs.get(f"C{i:02d}")
                or [
                    {
                        "text": t,
                        "semantic_role": "phrase",
                        "emphasis_level": "normal",
                        "break_after": "prefer",
                    }
                ],
            }
            for i, t in enumerate(CUE_TEXTS, 1)
            if f"C{i:02d}" not in special_runs
        ],
        *[{"cue_id": k, "runs": v} for k, v in special_runs.items()],
    ]
    cue_items.sort(key=lambda x: x["cue_id"])
    request = {
        "schema_version": 1,
        "canvas": {"width_px": 1080, "height_px": 1920},
        "layout": {
            "target_width_ratio": 0.77,
            "hard_ceiling_ratio": 0.8,
            "max_lines": 2,
            "safe_margins": {"left_px": 72, "right_px": 72},
        },
        "typography": {
            "font_family": FONT_FAMILY,
            "fallback_font_family": FONT_FAMILY,
            "base_font_size_px": 52,
            "tracking_px": 0,
            "stroke_px": 4,
            "visual_padding_px": 0,
            "emphasis_style_mapping": emph,
        },
        "cues": cue_items,
    }
    REQ.write_text(json.dumps(request, indent=2, ensure_ascii=False), encoding="utf-8")


def run_layout() -> dict:
    build_layout_request()
    subprocess.run(
        [
            "powershell",
            "-NoProfile",
            "-File",
            str(PREFLIGHT),
            "-RequestPath",
            str(REQ),
            "-OutputPath",
            str(RES),
            "-FontPolicy",
            "fail_closed",
        ],
        check=True,
    )
    return json.loads(RES.read_text(encoding="utf-8"))


def layout_display_text(layout: dict, cue_id: str) -> str:
    pool = layout.get("cue_results") or layout.get("cues") or []
    for c in pool:
        if c.get("cue_id") == cue_id:
            lines = c.get("lines") or []
            if lines:
                parts = []
                for ln in lines:
                    runs = ln.get("runs") or []
                    if runs:
                        parts.append("".join(r.get("text") or "" for r in runs))
                    else:
                        parts.append(ln.get("text") or "")
                return "\\N".join(p for p in parts if p)
            if c.get("display_text"):
                return str(c["display_text"]).replace("\n", "\\N")
    raise KeyError(cue_id)


def write_ass(layout: dict, timing_trace: list) -> None:
    header = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: N02Prod,Microsoft YaHei UI,52,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,1,0,0,0,100,100,0,0,1,4,0,2,72,72,280,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    events = []
    for i, (text_authority, tc) in enumerate(zip(CUE_TEXTS, RESOLVE_CUES, strict=True), 1):
        cid = f"C{i:02d}"
        disp = layout_display_text(layout, cid)
        sf = tc["start"] - TIMELINE_START
        ef = tc["end"] - TIMELINE_START
        st = sf / FPS
        en = ef / FPS
        events.append(f"Dialogue: 0,{sec_to_ass(st)},{sec_to_ass(en)},N02Prod,,0,0,0,,{disp}")
        timing_trace.append(
            {
                "cue_id": cid,
                "text_authority": text_authority,
                "display_ass": disp.replace("\\N", " | ") if disp else text_authority,
                "source_start_frame": tc["start"],
                "source_end_frame": tc["end"],
                "relative_start_frame": sf,
                "relative_end_frame": ef,
                "ass_start": sec_to_ass(st),
                "ass_end": sec_to_ass(en),
                "start_sec": round(st, 6),
                "end_sec": round(en, 6),
            }
        )
    ASS_PATH.write_text(header + "\n".join(events) + "\n", encoding="utf-8-sig")


def burnin_ass(master: Path, ass: Path, out: Path) -> dict:
    ass_esc = str(ass.resolve()).replace("\\", "/").replace(":", "\\:")
    vf = f"subtitles='{ass_esc}'"
    cmd = [
        "ffmpeg",
        "-y",
        "-hide_banner",
        "-i",
        str(master),
        "-vf",
        vf,
        "-c:v",
        "libx264",
        "-crf",
        "18",
        "-preset",
        "medium",
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "copy",
        str(out),
    ]
    p = subprocess.run(cmd, capture_output=True, text=True, check=False)
    ok = p.returncode == 0 and out.is_file()
    return {"ok": ok, "stderr_tail": (p.stderr or "")[-800:] if not ok else ""}


def probe_video(path: Path) -> dict:
    p = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-count_frames",
            "-show_entries",
            "stream=nb_read_frames,width,height,r_frame_rate",
            "-show_entries",
            "format=duration",
            "-of",
            "json",
            str(path),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(p.stdout)


def main() -> int:
    if not CLEAN_MASTER.is_file():
        print("BLOCKED: clean master missing", CLEAN_MASTER)
        return 2

    font = font_dependency_check()
    if font.get("FONT_DEPENDENCY_CHECK") != "PASS":
        PLAN_JSON.write_text(json.dumps({"font": font}, indent=2), encoding="utf-8")
        print(json.dumps(font, ensure_ascii=False))
        return 2

    layout = run_layout()
    timing_trace: list = []
    write_ass(layout, timing_trace)
    TIMING_JSON.write_text(json.dumps({"fps": FPS, "timeline_start_frame": TIMELINE_START, "cues": timing_trace}, indent=2, ensure_ascii=False), encoding="utf-8")

    bi = burnin_ass(CLEAN_MASTER, ASS_PATH, BURNIN_INTERMEDIATE)
    if not bi["ok"]:
        print("BLOCKED: burn-in failed", bi)
        return 2

    subprocess.run(
        [
            sys.executable,
            str(REPAIR),
            str(BURNIN_INTERMEDIATE),
            "--promote-on-pass",
            "--promoted-path",
            str(FINAL_PATH),
        ],
        check=True,
        cwd=str(ROOT),
    )

    plan = {
        "runtime_id": "subtitle.runtime.external_ass",
        "clean_master": {
            "path": str(CLEAN_MASTER),
            "codec": "h264",
            "container": "mp4",
            "INTERMEDIATE_LIMITATION": True,
            "reason": "ProRes/DNxHR/FFV1 render pairs rejected on host; H.264 mezzanine + single libx264 burn-in delivery encode",
            "sha256": sha256(CLEAN_MASTER),
            "frames": probe_video(CLEAN_MASTER),
        },
        "ass_path": str(ASS_PATH),
        "burnin_intermediate": str(BURNIN_INTERMEDIATE),
        "final_path": str(FINAL_PATH),
        "font": font,
        "font_family": FONT_FAMILY,
        "font_weight": FONT_WEIGHT,
        "cue_count": len(CUE_TEXTS),
        "layout_policy": "semantic_wrap_via_subtitle-layout-engine",
        "encode_graph": "Resolve H.264 clean master → ffmpeg subtitles (libx264 crf18) → loudnorm two-pass (audio only, video copy when possible)",
        "second_lossy_video_generation": True,
    }
    if FINAL_PATH.is_file():
        plan["FINAL_ARTIFACT_SHA256"] = sha256(FINAL_PATH)
        plan["final_probe"] = probe_video(FINAL_PATH)
    PLAN_JSON.write_text(json.dumps(plan, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"FINAL": str(FINAL_PATH), "sha256": plan.get("FINAL_ARTIFACT_SHA256")}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

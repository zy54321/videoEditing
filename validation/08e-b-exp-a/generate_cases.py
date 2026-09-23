#!/usr/bin/env python3
"""Generate Stage 08E-B Experiment A case request JSON files."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[1]
CASES = ROOT / "cases"
PREFLIGHT = REPO / "source/payload/video-workflow/tools/subtitle-layout-preflight.ps1"


def base_request(cues: list[dict]) -> dict:
    return {
        "schema_version": 1,
        "canvas": {"width_px": 1080, "height_px": 1920},
        "layout": {
            "target_width_ratio": 0.77,
            "hard_ceiling_ratio": 0.8,
            "max_lines": 2,
            "safe_margins": {"left_px": 54, "right_px": 54},
        },
        "typography": {
            "font_family": "Microsoft YaHei",
            "fallback_font_family": "SimSun",
            "base_font_size_px": 48,
            "tracking_px": 0,
            "stroke_px": 2,
            "visual_padding_px": 0,
            "emphasis_style_mapping": {
                "normal": {"size_multiplier": 1.0, "font_style": "Regular", "tracking_px": 0},
                "subtle": {"size_multiplier": 1.0, "font_style": "Regular", "tracking_px": 1},
                "medium": {"size_multiplier": 1.1, "font_style": "Bold", "tracking_px": 0},
                "strong": {"size_multiplier": 1.25, "font_style": "Bold", "tracking_px": 0},
            },
        },
        "cues": cues,
    }


def single_run(cue_id: str, text: str, break_after: str = "allow") -> dict:
    return {
        "cue_id": cue_id,
        "runs": [
            {
                "text": text,
                "semantic_role": "phrase",
                "emphasis_level": "normal",
                "break_after": break_after,
            }
        ],
    }


def preflight_width(text: str) -> float:
    req = base_request([single_run("PROBE", text)])
    probe = ROOT / "_probe.request.json"
    out = ROOT / "_probe.prediction.json"
    probe.write_text(json.dumps(req, ensure_ascii=False, indent=2), encoding="utf-8")
    subprocess.run(
        [
            "powershell.exe",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(PREFLIGHT),
            "-RequestPath",
            str(probe),
            "-OutputPath",
            str(out),
        ],
        check=True,
    )
    data = json.loads(out.read_text(encoding="utf-8"))
    return float(data["cue_results"][0]["max_line_width_px"])


def find_near_ratio(target_ratio: float, seed: str, tol_px: float = 8.0) -> str:
    target_px = 1080.0 * target_ratio
    text = seed
    width = preflight_width(text)
    while width < target_px - tol_px and len(text) < 80:
        text += seed
        width = preflight_width(text)
    while width > target_px + tol_px and len(text) > 1:
        text = text[:-1]
        width = preflight_width(text)
    return text


def main() -> int:
    CASES.mkdir(parents=True, exist_ok=True)
    specs = [
        ("A01", single_run("A01", "你好世界"), "简短中文"),
        ("A02", single_run("A02", "这件事真正离谱的地方在于价格"), "较长中文"),
        ("A03", single_run("A03", "Typography parity validation sample"), "英文"),
        ("A04", single_run("A04", "Hello 你好 mixed caption test"), "中英混排"),
        ("A05", single_run("A05", "价格上涨了 40%"), "数字/百分比"),
        ("A06", single_run("A06", find_near_ratio(0.76, "宽")), "~76%"),
        ("A07", single_run("A07", find_near_ratio(0.78, "幅")), "~78%"),
        ("A08", single_run("A08", find_near_ratio(0.80, "界")), "~80%"),
    ]
    a08_text = specs[-1][1]["runs"][0]["text"]
    specs.append(("A09", single_run("A09", a08_text + "超限"), ">80% repair"))
    specs.append(
        (
            "A10",
            {
                "cue_id": "A10",
                "runs": [
                    {
                        "text": "第一行字幕内容",
                        "semantic_role": "phrase",
                        "emphasis_level": "normal",
                        "break_after": "prefer",
                    },
                    {
                        "text": "第二行继续说明",
                        "semantic_role": "phrase",
                        "emphasis_level": "normal",
                        "break_after": "forbid",
                    },
                ],
            },
            "两行字幕",
        )
    )

    manifest = []
    for case_id, cue, note in specs:
        path = CASES / f"{case_id}.request.json"
        path.write_text(
            json.dumps(base_request([cue]), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        manifest.append({"case_id": case_id, "note": note, "path": str(path)})
        print(case_id, note, cue["runs"][0]["text"] if case_id != "A10" else "2-line")

    (ROOT / "cases-manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

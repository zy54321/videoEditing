#!/usr/bin/env python3
"""N03 V9 — restore N02_V6 external ASS style + libass burn-in (route correction)."""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from statistics import median

ROOT = Path(__file__).resolve().parents[2]
LIB = ROOT / "source/payload/video-workflow/tools/lib"
sys.path.insert(0, str(LIB))

from canonical_subtitle_cue import CanonicalSubtitleCue  # noqa: E402

N03_ROOT = Path(r"E:\03_Media\02_Video\Davinci\Astra\2026-10-12\N03")
PROD = N03_ROOT / "video-workflow/production"
EVIDENCE = N03_ROOT / "evidence/external-ass-v9"
OUTPUT_DIR = Path(r"E:\03_Media\02_Video\Davinci\Astra\2026-10-12\output")

N02_ASS = Path(r"E:\03_Media\02_Video\Davinci\Astra\2026-09-21\output\_N02_V6_INTERMEDIATE_subtitles.ass")
N02_REF = Path(r"E:\03_Media\02_Video\Davinci\Astra\2026-09-21\output\N02_V6.mp4")

CANONICAL_PATH = PROD / "canonical-subtitle-cues.json"
FROZEN_V5 = PROD / "frozen_subtitle_cues_v5.json"
ASS_OUT = OUTPUT_DIR / "N03_V9.ass"
BURNIN_INTER = OUTPUT_DIR / "_N03_V9_INTERMEDIATE_subtitle_burnin.mp4"
FINAL = OUTPUT_DIR / "N03_V9.mp4"
CLEAN_MASTER = OUTPUT_DIR / "N03_V9_clean_master.mp4"
STYLE_REF_JSON = EVIDENCE / "N02_V6_ASS_STYLE_REFERENCE.json"
REPORT_JSON = EVIDENCE / "n03-v9-external-ass-route-report.json"

TIMELINE_START = 86400
FPS = 24.0
STYLE_LINE_RE = re.compile(r"^Style:\s*([^,]+),(.+)$")


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


def parse_ass_style(ass_path: Path) -> dict:
    fields = [
        "Name",
        "Fontname",
        "Fontsize",
        "PrimaryColour",
        "SecondaryColour",
        "OutlineColour",
        "BackColour",
        "Bold",
        "Italic",
        "Underline",
        "StrikeOut",
        "ScaleX",
        "ScaleY",
        "Spacing",
        "Angle",
        "BorderStyle",
        "Outline",
        "Shadow",
        "Alignment",
        "MarginL",
        "MarginR",
        "MarginV",
        "Encoding",
    ]
    for line in ass_path.read_text(encoding="utf-8-sig").splitlines():
        m = STYLE_LINE_RE.match(line.strip())
        if not m:
            continue
        name = m.group(1).strip()
        parts = [p.strip() for p in m.group(2).split(",")]
        if len(parts) != len(fields) - 1:
            raise RuntimeError(f"ASS style field count mismatch: {len(parts)}")
        style = {"Name": name}
        for k, v in zip(fields[1:], parts, strict=True):
            style[k] = v
        return {
            "source_ass_path": str(ass_path.resolve()),
            "source_ass_sha256": sha256(ass_path),
            "visual_reference_mp4": str(N02_REF.resolve()),
            "style": style,
        }
    raise RuntimeError("ASS_STYLE_NOT_FOUND")


def normalize_text(s: str) -> str:
    return s.replace("\r", "").replace("\n", "").replace("\\N", "").strip()


def load_or_materialize_canonical() -> tuple[list[CanonicalSubtitleCue], dict]:
    if CANONICAL_PATH.is_file():
        doc = json.loads(CANONICAL_PATH.read_text(encoding="utf-8-sig"))
        cues = [
            CanonicalSubtitleCue(
                cue_id=c["cue_id"],
                start=float(c["start"]),
                end=float(c["end"]),
                text=c["text"],
                lines=tuple(c.get("lines") or [c["text"]]),
                confidence=float(c.get("confidence") or 1.0),
                source_span_ids=tuple(c.get("source_span_ids") or []),
            )
            for c in doc["cues"]
        ]
        return cues, {"source": str(CANONICAL_PATH), "materialized": False}

    frozen = json.loads(FROZEN_V5.read_text(encoding="utf-8-sig"))
    cues: list[CanonicalSubtitleCue] = []
    for i, row in enumerate(frozen, 1):
        text = str(row["text"])
        lines = tuple(text.split("\n")) if "\n" in text else (text,)
        start_sec = (int(row["start"]) - TIMELINE_START) / FPS
        end_sec = (int(row["end"]) - TIMELINE_START) / FPS
        cues.append(
            CanonicalSubtitleCue(
                cue_id=f"C{i:02d}",
                start=start_sec,
                end=end_sec,
                text=text.replace("\n", ""),
                lines=lines,
                confidence=float(row.get("alignment_confidence") or 1.0),
                source_span_ids=tuple(str(x) for x in row.get("source_asr_cue_ids") or []),
            )
        )
    meta = {
        "schema_version": 1,
        "pipeline_id": "subtitle.authority_alignment_v1",
        "status": "OK",
        "cue_count": len(cues),
        "text_authority": "frozen_script",
        "materialization_note": "Mechanical export from closed R1 frozen_subtitle_cues_v5 (no re-alignment)",
    }
    doc = {
        "schema_version": 1,
        "pipeline_id": "subtitle.authority_alignment_v1",
        "meta": meta,
        "cues": [
            {
                "cue_id": c.cue_id,
                "start": c.start,
                "end": c.end,
                "text": c.text,
                "lines": list(c.lines),
                "confidence": c.confidence,
                "source_span_ids": list(c.source_span_ids),
                "text_authority": "frozen_script",
            }
            for c in cues
        ],
    }
    CANONICAL_PATH.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return cues, {"source": str(CANONICAL_PATH), "materialized": True, "from": str(FROZEN_V5)}


def build_ass_header(style_ref: dict, style_name: str = "N02Prod") -> str:
    s = style_ref["style"]
    if s["Name"] != style_name:
        style_name = s["Name"]
    row = (
        f"Style: {style_name},{s['Fontname']},{s['Fontsize']},{s['PrimaryColour']},"
        f"{s['SecondaryColour']},{s['OutlineColour']},{s['BackColour']},{s['Bold']},"
        f"{s['Italic']},{s['Underline']},{s['StrikeOut']},{s['ScaleX']},{s['ScaleY']},"
        f"{s['Spacing']},{s['Angle']},{s['BorderStyle']},{s['Outline']},{s['Shadow']},"
        f"{s['Alignment']},{s['MarginL']},{s['MarginR']},{s['MarginV']},{s['Encoding']}"
    )
    return f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
{row}

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def write_ass(cues: list[CanonicalSubtitleCue], style_ref: dict) -> None:
    style_name = style_ref["style"]["Name"]
    lines = [build_ass_header(style_ref, style_name).rstrip()]
    for c in cues:
        disp = "\\N".join(c.lines) if len(c.lines) > 1 else c.text
        lines.append(
            f"Dialogue: 0,{sec_to_ass(c.start)},{sec_to_ass(c.end)},{style_name},,0,0,0,,{disp}"
        )
    ASS_OUT.write_text("\n".join(lines) + "\n", encoding="utf-8-sig")


def verify_canonical_ass_text(cues: list[CanonicalSubtitleCue], ass_path: Path) -> dict:
    ass_texts = []
    for line in ass_path.read_text(encoding="utf-8-sig").splitlines():
        if line.startswith("Dialogue:"):
            ass_texts.append(normalize_text(line.split(",", 9)[9]))
    canon = [normalize_text(c.text) for c in cues]
    ok = canon == ass_texts and len(canon) == len(ass_texts)
    return {
        "CANONICAL_ASS_TEXT_MATCH": "PASS" if ok else "FAIL",
        "canonical_cue_count": len(canon),
        "ass_dialogue_count": len(ass_texts),
    }


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
    return {"ok": ok, "command": cmd, "stderr_tail": (p.stderr or "")[-1200:] if not ok else ""}


def compare_n02_n03_v9(out_json: Path) -> dict:
    """Reuse compare logic with N03_V9 path."""
    compare_py = N03_ROOT / "evidence/size-root-cause-audit/visual_single_line_compare.py"
    code = compare_py.read_text(encoding="utf-8")
    code = code.replace(
        'N03 = Path(r"E:/03_Media/02_Video/Davinci/Astra/2026-10-12/output/N03_V7.mp4")',
        'N03 = Path(r"E:/03_Media/02_Video/Davinci/Astra/2026-10-12/output/N03_V9.mp4")',
    )
    code = code.replace(
        'OUT = Path(__file__).resolve().parent',
        f'OUT = Path(r"{EVIDENCE.as_posix()}")',
    )
    code = code.replace(
        'visual_single_line_n02_vs_n03.json',
        "visual_single_line_n02_vs_n03_v9.json",
    )
    tmp = EVIDENCE / "_compare_v9_runner.py"
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    tmp.write_text(code, encoding="utf-8")
    p = subprocess.run([sys.executable, str(tmp)], capture_output=True, text=True, check=False)
    if out_json.is_file():
        return json.loads(out_json.read_text(encoding="utf-8"))
    return {"ok": False, "stdout": p.stdout[-500:], "stderr": p.stderr[-500:]}


def write_final_contract(clean: Path, final: Path, ass: Path) -> Path:
    contract = {
        "schema_version": 1,
        "production_id": "N03",
        "deliver_authority": "final_mp4_burned",
        "renderer_route": "external_ass",
        "subtitle_materialization": "external_ass_burnin",
        "subtitle_export_mode": "burn_in",
        "final_artifact_path": str(final.resolve()),
        "clean_master_path": str(clean.resolve()),
        "canonical_subtitle_cues_path": str(CANONICAL_PATH.resolve()),
        "ass_path": str(ass.resolve()),
        "expected_width": 1080,
        "expected_height": 1920,
        "expected_fps": 24.0,
        "expected_duration_seconds_min": 90.0,
        "expected_duration_seconds_max": 100.0,
    }
    path = PROD / "final-render-contract-v9.json"
    path.write_text(json.dumps(contract, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def run_final_gate(contract_path: Path, work_dir: Path) -> dict:
    gate_cli = ROOT / "source/payload/video-workflow/tools/run-final-artifact-gate.py"
    out = work_dir / "final-artifact-gate-v9.json"
    p = subprocess.run(
        [sys.executable, str(gate_cli), "--contract", str(contract_path), "--work-dir", str(work_dir), "--out", str(out)],
        capture_output=True,
        text=True,
        check=False,
    )
    if out.is_file():
        return json.loads(out.read_text(encoding="utf-8"))
    return {"verdict": "FAIL", "stderr": p.stderr}


def main() -> int:
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    if not N02_ASS.is_file():
        print("BLOCKED: N02 ASS missing")
        return 2

    style_ref = parse_ass_style(N02_ASS)
    STYLE_REF_JSON.write_text(json.dumps(style_ref, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    cues, canon_meta = load_or_materialize_canonical()
    write_ass(cues, style_ref)
    text_match = verify_canonical_ass_text(cues, ASS_OUT)

    report: dict = {
        "native_drt_size_reverse_engineering": "ABANDONED_FOR_CURRENT_PRODUCTION",
        "n02_visual_reference": str(N02_REF),
        "n02_ass_source": style_ref["source_ass_path"],
        "n02_ass_style": style_ref["style"],
        "canonical_source": canon_meta,
        "n03_v9_ass": str(ASS_OUT),
        "ass_cue_count": text_match["ass_dialogue_count"],
        "style_name": style_ref["style"]["Name"],
        "fontname": style_ref["style"]["Fontname"],
        "fontsize": style_ref["style"]["Fontsize"],
        "outline": style_ref["style"]["Outline"],
        "margin_v": style_ref["style"]["MarginV"],
        "alignment": style_ref["style"]["Alignment"],
        "canonical_text_match": text_match,
        "clean_master_path": str(CLEAN_MASTER),
        "ffmpeg_burnin": None,
        "n03_v9_path": str(FINAL),
    }

    if not CLEAN_MASTER.is_file():
        report["phase"] = "BLOCKED_CLEAN_MASTER"
        REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 3

    bi = burnin_ass(CLEAN_MASTER, ASS_OUT, BURNIN_INTER)
    report["ffmpeg_burnin"] = bi
    if not bi["ok"]:
        REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return 2

    if FINAL.is_file():
        FINAL.unlink()
    BURNIN_INTER.replace(FINAL)

    visual = compare_n02_n03_v9(EVIDENCE / "visual_single_line_n02_vs_n03_v9.json")
    report["visual_compare"] = visual

    contract = write_final_contract(CLEAN_MASTER, FINAL, ASS_OUT)
    gate = run_final_gate(contract, EVIDENCE)
    report["final_render_contract"] = str(contract)
    report["FINAL_RENDER_SUBTITLE_BURNIN"] = (gate.get("checks") or {}).get("FINAL_RENDER_SUBTITLE_BURNIN")
    report["FINAL_ARTIFACT_GATE"] = gate.get("verdict")
    report["gate_detail"] = gate

    ratio = visual.get("glyph_height_ratio_median")
    in_band = ratio is not None and 0.85 <= float(ratio) <= 1.15
    gate_pass = report["FINAL_ARTIFACT_GATE"] == "PASS"
    burnin_pass = report["FINAL_RENDER_SUBTITLE_BURNIN"] == "PASS"
    text_pass = text_match["CANONICAL_ASS_TEXT_MATCH"] == "PASS"

    if gate_pass and burnin_pass and text_pass and in_band:
        report["final_verdict"] = "N03_EXTERNAL_ASS_STYLE_RESTORED"
    elif gate_pass and burnin_pass and text_pass:
        report["final_verdict"] = "N03_EXTERNAL_ASS_STYLE_RESTORED_VISUAL_BAND_WARN"
    else:
        report["final_verdict"] = "N03_ASS_STYLE_RESTORE_BLOCKED"

    report["continue_native_drt_size_probe"] = False
    REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["final_verdict"].startswith("N03_EXTERNAL_ASS") else 2


if __name__ == "__main__":
    raise SystemExit(main())

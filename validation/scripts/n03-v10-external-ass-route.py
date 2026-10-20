#!/usr/bin/env python3
"""N03 V10 — external ASS burn-in from V10 clean master (reframe R3)."""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LIB = ROOT / "source/payload/video-workflow/tools/lib"
sys.path.insert(0, str(LIB))

N03_ROOT = Path(r"E:\03_Media\02_Video\Davinci\Astra\2026-10-12\N03")
PROD = N03_ROOT / "video-workflow/production"
EVIDENCE = N03_ROOT / "evidence/r3-reframe-closure"
OUTPUT_DIR = Path(r"E:\03_Media\02_Video\Davinci\Astra\2026-10-12\output")

CLEAN_MASTER = OUTPUT_DIR / "N03_V10_clean_master.mp4"
ASS_V9 = OUTPUT_DIR / "N03_V9.ass"
ASS_OUT = OUTPUT_DIR / "N03_V10.ass"
BURNIN_INTER = OUTPUT_DIR / "_N03_V10_INTERMEDIATE_subtitle_burnin.mp4"
FINAL = OUTPUT_DIR / "N03_V10.mp4"
CANONICAL_PATH = PROD / "canonical-subtitle-cues.json"
REPORT_JSON = EVIDENCE / "n03-v10-external-ass-route-report.json"


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
    return {"ok": ok, "stderr_tail": (p.stderr or "")[-1200:] if not ok else ""}


def write_contract(clean: Path, final: Path, ass: Path) -> Path:
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
        "reframe_policy_id": "static-portrait-reframe.v1",
        "source_timeline": "N03_V10_Assembly-merged",
    }
    path = PROD / "final-render-contract-v10.json"
    path.write_text(json.dumps(contract, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def run_final_gate(contract_path: Path) -> dict:
    gate_cli = ROOT / "source/payload/video-workflow/tools/run-final-artifact-gate.py"
    out = EVIDENCE / "final-artifact-gate-v10.json"
    p = subprocess.run(
        [sys.executable, str(gate_cli), "--contract", str(contract_path), "--work-dir", str(EVIDENCE), "--out", str(out)],
        capture_output=True,
        text=True,
        check=False,
    )
    if out.is_file():
        return json.loads(out.read_text(encoding="utf-8"))
    return {"verdict": "FAIL", "stderr": p.stderr}


def main() -> int:
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    report: dict = {"clean_master": str(CLEAN_MASTER), "ass_source": str(ASS_V9)}

    if not CLEAN_MASTER.is_file():
        report["phase"] = "BLOCKED_CLEAN_MASTER"
        REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return 3
    if not ASS_V9.is_file():
        report["phase"] = "BLOCKED_ASS"
        REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return 3

    shutil.copy2(ASS_V9, ASS_OUT)
    report["ass_path"] = str(ASS_OUT)

    bi = burnin_ass(CLEAN_MASTER, ASS_OUT, BURNIN_INTER)
    report["ffmpeg_burnin"] = bi
    if not bi["ok"]:
        REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return 2

    if FINAL.is_file():
        FINAL.unlink()
    BURNIN_INTER.replace(FINAL)
    report["final_path"] = str(FINAL)

    contract = write_contract(CLEAN_MASTER, FINAL, ASS_OUT)
    gate = run_final_gate(contract)
    report["final_render_contract"] = str(contract)
    report["FINAL_ARTIFACT_GATE"] = gate.get("verdict")
    report["FINAL_RENDER_SUBTITLE_BURNIN"] = (gate.get("checks") or {}).get("FINAL_RENDER_SUBTITLE_BURNIN")
    report["gate_detail"] = gate

    gate_pass = report["FINAL_ARTIFACT_GATE"] == "PASS"
    burnin_pass = report["FINAL_RENDER_SUBTITLE_BURNIN"] == "PASS"
    report["final_verdict"] = "N03_V10_DELIVER_READY" if gate_pass and burnin_pass else "N03_V10_GATE_BLOCKED"

    REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["final_verdict"] == "N03_V10_DELIVER_READY" else 2


if __name__ == "__main__":
    raise SystemExit(main())

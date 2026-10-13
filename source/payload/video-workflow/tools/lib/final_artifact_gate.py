"""FINAL_ARTIFACT_GATE — unified post-render QA (R2)."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

from final_render_contract import (
    EXPORT_MODE_SEPARATE,
    MATERIALIZATION_EXTERNAL,
    MATERIALIZATION_NATIVE,
    MATERIALIZATION_NA,
    load_final_render_contract,
)
from artifact_fingerprint import build_evidence_bindings
from subtitle_burnin_evidence import evaluate_subtitle_burnin_gate

GATE_ID = "FINAL_ARTIFACT_GATE"
MIN_FILE_BYTES = 4096


def _ffprobe(path: Path) -> dict[str, Any]:
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-print_format",
        "json",
        "-show_format",
        "-show_streams",
        str(path),
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if r.returncode != 0:
        return {"error": r.stderr or "ffprobe_failed"}
    return json.loads(r.stdout)


def _parse_fps(rate: str) -> float:
    if not rate or rate == "0/0":
        return 0.0
    if "/" in rate:
        num, den = rate.split("/", 1)
        return float(num) / float(den) if float(den) else 0.0
    return float(rate)


def evaluate_final_artifact_gate(
    *,
    contract_path: Path,
    qa_report_path: Path | None = None,
    work_dir: Path,
) -> dict[str, Any]:
    contract_path = contract_path.resolve()
    contract = load_final_render_contract(contract_path)
    video = Path(contract.final_artifact_path)
    errors: list[str] = []
    checks: dict[str, str] = {}

    if contract.deliver_authority != "final_mp4_burned":
        errors.append("DELIVER_AUTHORITY_NOT_FINAL_MP4")

    if not video.is_file():
        errors.append("FINAL_MP4_MISSING")
        checks["VIDEO_STREAM_PASS"] = "FAIL"
        checks["FORMAT_PASS"] = "FAIL"
        return _result(checks, errors, contract, None, None)

    size = video.stat().st_size
    checks["ARTIFACT_EXISTENCE_PASS"] = "PASS" if size >= MIN_FILE_BYTES else "FAIL"
    if size < MIN_FILE_BYTES:
        errors.append("FINAL_MP4_TOO_SMALL")

    probe = _ffprobe(video)
    if probe.get("error"):
        errors.append("FFPROBE_FAILED")
        checks["VIDEO_STREAM_PASS"] = "FAIL"
        checks["AUDIO_STREAM_PASS"] = "FAIL"
        checks["FORMAT_PASS"] = "FAIL"
        return _result(checks, errors, contract, probe, None)

    streams = probe.get("streams") or []
    v = next((s for s in streams if s.get("codec_type") == "video"), None)
    a = next((s for s in streams if s.get("codec_type") == "audio"), None)
    checks["VIDEO_STREAM_PASS"] = "PASS" if v else "FAIL"
    checks["AUDIO_STREAM_PASS"] = "PASS" if a else "FAIL"
    if not v:
        errors.append("NO_VIDEO_STREAM")
    if not a:
        errors.append("NO_AUDIO_STREAM")

    fmt = probe.get("format") or {}
    duration = float(fmt.get("duration") or 0)
    width = int(v.get("width") or 0) if v else 0
    height = int(v.get("height") or 0) if v else 0
    fps = _parse_fps(str(v.get("r_frame_rate") or "")) if v else 0.0

    format_ok = (
        width == contract.expected_width
        and height == contract.expected_height
        and abs(fps - contract.expected_fps) < 0.06
    )
    if contract.expected_duration_seconds is not None and duration > 0:
        format_ok = format_ok and abs(duration - contract.expected_duration_seconds) < 1.5
    checks["FORMAT_PASS"] = "PASS" if format_ok else "FAIL"
    if not format_ok:
        errors.append("FORMAT_MISMATCH")

    checks["BLACK_BAR_QA"] = "N/A"
    checks["AUDIO_LOUDNESS_QA"] = "N/A"
    if qa_report_path and qa_report_path.is_file():
        qa = json.loads(qa_report_path.read_text(encoding="utf-8-sig"))
        bb = (qa.get("black_bar_check") or {}).get("verdict", "")
        if bb in ("PASS", "NO_EDGE_BLACK_PATTERN"):
            checks["BLACK_BAR_QA"] = "PASS"
        elif bb in ("AUTOMATED_SCREEN + VISUAL_CONFIRM", "SUSPECT_BLACK_BARS", "REPAIR_REQUIRED", "REFRAME_OWNER_REVIEW_REQUIRED"):
            checks["BLACK_BAR_QA"] = "VISUAL_CONFIRM_REQUIRED"
            errors.append(f"BLACK_BAR_{bb}")
        elif bb:
            checks["BLACK_BAR_QA"] = "FAIL"
            errors.append(f"BLACK_BAR_{bb}")
        al = qa.get("audio_loudness_qa") or {}
        if al.get("skipped"):
            checks["AUDIO_LOUDNESS_QA"] = "N/A"
        elif al.get("ok"):
            checks["AUDIO_LOUDNESS_QA"] = "PASS"
        elif al:
            checks["AUDIO_LOUDNESS_QA"] = "FAIL"
            errors.append(f"AUDIO_{al.get('verdict')}")

    mat = contract.subtitle_materialization
    subtitle_detail = None
    if mat == MATERIALIZATION_NA:
        checks["SUBTITLE_BURNIN_PASS"] = "N/A"
        checks["FINAL_RENDER_SUBTITLE_BURNIN"] = "N/A"
    elif mat in (MATERIALIZATION_NATIVE, MATERIALIZATION_EXTERNAL):
        burnin_errors: list[str] = []
        separate_export = contract.resolve_subtitle_export_mode == EXPORT_MODE_SEPARATE
        if separate_export:
            burnin_errors.append("N03_SEPARATE_SUBTITLE_EXPORT_MODE")
            checks["FINAL_RENDER_SUBTITLE_BURNIN"] = "FAIL"
            checks["SUBTITLE_BURNIN_PASS"] = "FAIL"
        for sc in contract.sidecar_subtitle_paths:
            if Path(sc).is_file() and separate_export:
                burnin_errors.append("SIDECAR_SUBTITLE_FILE_PRESENT")

        canonical = Path(contract.canonical_subtitle_cues_path or "")
        if not canonical.is_file():
            burnin_errors.append("CANONICAL_CUES_MISSING_FOR_QA")
        else:
            work_dir.mkdir(parents=True, exist_ok=True)
            subtitle_detail = evaluate_subtitle_burnin_gate(
                contract=contract,
                final_video=video,
                canonical_path=canonical,
                work_dir=work_dir,
                duration=duration,
            )
            burn = subtitle_detail.get("FINAL_RENDER_SUBTITLE_BURNIN", "FAIL")
            if burn == "VISUAL_CONFIRM_REQUIRED":
                burnin_errors.append("SUBTITLE_BURNIN_VISUAL_CONFIRM_REQUIRED")
            if not separate_export:
                checks["FINAL_RENDER_SUBTITLE_BURNIN"] = burn
                checks["SUBTITLE_BURNIN_PASS"] = burn
                if burn != "PASS":
                    burnin_errors.append("SUBTITLE_PIXELS_ABSENT_ON_FINAL_MP4")
            elif burn == "PASS":
                burnin_errors.append("SEPARATE_EXPORT_BUT_PIXELS_PRESENT_STILL_FAIL")
            if contract.sidecar_subtitle_paths and checks.get("FINAL_RENDER_SUBTITLE_BURNIN") == "FAIL":
                burnin_errors.append("SIDECAR_ONLY_DELIVERY_SUSPECTED")
        if burnin_errors:
            errors.extend(burnin_errors)
            if not separate_export and checks.get("FINAL_RENDER_SUBTITLE_BURNIN") != "PASS":
                checks["FINAL_RENDER_SUBTITLE_BURNIN"] = "FAIL"
                checks["SUBTITLE_BURNIN_PASS"] = "FAIL"
    else:
        checks["SUBTITLE_BURNIN_PASS"] = "FAIL"
        checks["FINAL_RENDER_SUBTITLE_BURNIN"] = "FAIL"
        errors.append("UNKNOWN_SUBTITLE_MATERIALIZATION")

    required = [k for k, v in checks.items() if v not in ("N/A", "PASS")]
    verdict = "PASS" if not errors and not required else "FAIL"

    evidence_bindings = None
    if verdict == "PASS":
        canonical_p = Path(contract.canonical_subtitle_cues_path or "") if contract.canonical_subtitle_cues_path else None
        evidence_bindings = build_evidence_bindings(
            contract_path=contract_path,
            final_artifact_path=video,
            canonical_cues_path=canonical_p if canonical_p and canonical_p.is_file() else None,
            qa_report_path=qa_report_path,
        )

    return _result(
        checks,
        errors,
        contract,
        probe,
        subtitle_detail,
        verdict,
        evidence_bindings=evidence_bindings,
        contract_path=str(contract_path),
        qa_report_path=str(qa_report_path) if qa_report_path else None,
    )


def _result(
    checks: dict[str, str],
    errors: list[str],
    contract: Any,
    probe: dict[str, Any] | None,
    subtitle_detail: dict[str, Any] | None,
    verdict: str | None = None,
    evidence_bindings: dict[str, Any] | None = None,
    contract_path: str | None = None,
    qa_report_path: str | None = None,
) -> dict[str, Any]:
    if verdict is None:
        verdict = "PASS" if not errors else "FAIL"
    return {
        "gate": GATE_ID,
        "verdict": verdict,
        "status": "COMPLETE" if verdict in ("PASS", "FAIL") else "INCOMPLETE",
        "checks": checks,
        "errors": errors,
        "contract_path": contract_path,
        "qa_report_path": qa_report_path,
        "final_artifact_path": contract.final_artifact_path,
        "subtitle_materialization": contract.subtitle_materialization,
        "evidence_bindings": evidence_bindings,
        "probe_summary": {
            "duration": (probe or {}).get("format", {}).get("duration"),
        }
        if probe
        else None,
        "subtitle_burnin_detail": subtitle_detail,
    }

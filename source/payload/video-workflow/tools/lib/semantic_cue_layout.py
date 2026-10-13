"""Bridge TimedScriptSpan → subtitle-layout-engine (PowerShell) → layout cues."""
from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from script_audio_monotonic_align import TimedScriptSpan

_PUNCT_PREFER = set("，。！？；、：")


def build_runs_from_text(text: str) -> list[dict[str, Any]]:
    runs: list[dict[str, Any]] = []
    buf = ""
    for ch in text:
        buf += ch
        if ch in _PUNCT_PREFER:
            runs.append(
                {
                    "text": buf,
                    "semantic_role": "phrase",
                    "emphasis_level": "normal",
                    "break_after": "prefer",
                }
            )
            buf = ""
    if buf:
        runs.append(
            {
                "text": buf,
                "semantic_role": "phrase",
                "emphasis_level": "normal",
                "break_after": "allow",
            }
        )
    if not runs:
        runs.append(
            {
                "text": text,
                "semantic_role": "phrase",
                "emphasis_level": "normal",
                "break_after": "allow",
            }
        )
    return runs


def _default_layout_request(cue_id: str, runs: list[dict[str, Any]]) -> dict[str, Any]:
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
            "stroke_px": 0,
            "visual_padding_px": 0,
            "emphasis_style_mapping": {
                "normal": {"size_multiplier": 1.0, "font_style": "Regular", "tracking_px": 0},
                "subtle": {"size_multiplier": 1.0, "font_style": "Regular", "tracking_px": 0},
                "medium": {"size_multiplier": 1.1, "font_style": "Regular", "tracking_px": 0},
                "strong": {"size_multiplier": 1.25, "font_style": "Regular", "tracking_px": 0},
            },
        },
        "cues": [{"cue_id": cue_id, "runs": runs}],
    }


def _invoke_preflight(tools_dir: Path, request: dict[str, Any]) -> dict[str, Any]:
    preflight = tools_dir / "subtitle-layout-preflight.ps1"
    if not preflight.is_file():
        raise FileNotFoundError(f"LAYOUT_PREFLIGHT_MISSING: {preflight}")

    with tempfile.TemporaryDirectory() as tmp:
        req_path = Path(tmp) / "request.json"
        out_path = Path(tmp) / "result.json"
        req_path.write_text(json.dumps(request, ensure_ascii=False), encoding="utf-8")
        cmd = [
            "powershell.exe",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(preflight),
            "-RequestPath",
            str(req_path),
            "-OutputPath",
            str(out_path),
            "-FontPolicy",
            "allow_fallback",
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
        if proc.returncode != 0:
            raise RuntimeError(f"LAYOUT_PREFLIGHT_FAILED: {proc.stderr or proc.stdout}")
        return json.loads(out_path.read_text(encoding="utf-8-sig"))


def _select_split_candidate(candidates: list[dict[str, Any]]) -> dict[str, Any] | None:
    for pol in ("prefer", "allow"):
        for c in candidates:
            if c.get("boundary_policy") == pol:
                return c
    return candidates[0] if candidates else None


def _split_runs_at_index(runs: list[dict[str, Any]], after_run_index: int) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    left = runs[: after_run_index + 1]
    right = runs[after_run_index + 1 :]
    if right:
        right[0] = dict(right[0])
        right[0]["break_after"] = right[0].get("break_after", "allow")
    return left, right


def _lines_to_text(line_results: list[dict[str, Any]]) -> tuple[str, list[str]]:
    lines: list[str] = []
    for ln in line_results:
        parts = [str(r.get("text", "")) for r in ln.get("runs", [])]
        lines.append("".join(parts))
    display = "\n".join(lines)
    flat = "".join(lines)
    return display, lines


def layout_span_to_cue_parts(
    span: TimedScriptSpan,
    span_id: str,
    tools_dir: Path,
    depth: int = 0,
) -> list[dict[str, Any]]:
    """Returns list of {text, lines, layout_status, source_span_id, char_len}."""
    if depth > 8:
        raise RuntimeError("CUE_SPLIT_DEPTH_EXCEEDED")

    runs = build_runs_from_text(span.text)
    request = _default_layout_request(span_id, runs)
    result = _invoke_preflight(tools_dir, request)
    cue = result["cue_results"][0]
    status = cue.get("status")

    if status == "CUE_SPLIT_REQUIRED":
        candidate = _select_split_candidate(list(cue.get("split_candidates") or []))
        if not candidate:
            raise RuntimeError(f"CUE_SPLIT_BLOCKED: {span_id}")
        idx = int(candidate["after_run_index"])
        left_runs, right_runs = _split_runs_at_index(runs, idx)
        left_text = "".join(r["text"] for r in left_runs)
        right_text = "".join(r["text"] for r in right_runs)
        total_len = max(len(left_text) + len(right_text), 1)
        mid = span.audio_start + (span.audio_end - span.audio_start) * (len(left_text) / total_len)
        left_span = TimedScriptSpan(
            script_start=span.script_start,
            script_end=span.script_end,
            text=left_text,
            audio_start=span.audio_start,
            audio_end=mid,
            confidence=span.confidence,
            source_asr_cue_ids=span.source_asr_cue_ids,
            alignment_method=span.alignment_method,
            low_confidence=span.low_confidence,
        )
        right_span = TimedScriptSpan(
            script_start=span.script_start,
            script_end=span.script_end,
            text=right_text,
            audio_start=mid,
            audio_end=span.audio_end,
            confidence=span.confidence,
            source_asr_cue_ids=span.source_asr_cue_ids,
            alignment_method=span.alignment_method,
            low_confidence=span.low_confidence,
        )
        out: list[dict[str, Any]] = []
        out.extend(layout_span_to_cue_parts(left_span, f"{span_id}-A", tools_dir, depth + 1))
        out.extend(layout_span_to_cue_parts(right_span, f"{span_id}-B", tools_dir, depth + 1))
        return out

    if status not in ("PASS", "PASS_WITH_WARNING"):
        raise RuntimeError(f"LAYOUT_STATUS_BLOCKED: {span_id} status={status}")

    display, lines = _lines_to_text(cue.get("lines") or [])
    flat = "".join(r["text"] for r in runs)
    if display.replace("\n", "") != flat.replace("\n", ""):
        # lines joined without newlines in content check
        if flat != display.replace("\n", ""):
            raise RuntimeError(f"CONTENT_PRESERVATION_FAILED: {span_id}")

    return [
        {
            "text": display,
            "lines": lines,
            "layout_status": status,
            "source_span_id": span_id,
            "char_len": len(flat),
            "span_text": span.text,
        }
    ]

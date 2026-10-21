"""Materialize external ASS from R1 canonical subtitle cues + versioned style baseline."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from canonical_subtitle_cue import CanonicalSubtitleCue
from external_ass_style_baseline import (
    ass_style_line,
    load_baseline,
    play_res,
    sha256_bytes,
    sha256_file,
)


def normalize_dialogue_text(s: str) -> str:
    return s.replace("\r", "").replace("\n", "").replace("\\N", "").strip()


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


def load_canonical_cues(path: Path) -> tuple[list[CanonicalSubtitleCue], dict[str, Any]]:
    path = path.resolve()
    if not path.is_file():
        raise RuntimeError(f"CANONICAL_CUES_MISSING: {path}")
    doc = json.loads(path.read_text(encoding="utf-8-sig"))
    meta = doc.get("meta") or {}
    status = meta.get("status")
    if status != "OK":
        raise RuntimeError(f"CANONICAL_CUES_NOT_OK: status={status!r}")
    raw = doc.get("cues") or []
    if not raw:
        raise RuntimeError("CANONICAL_CUES_EMPTY")
    cues: list[CanonicalSubtitleCue] = []
    for c in raw:
        lines_raw = c.get("lines") or [c.get("text", "")]
        lines = tuple(str(x) for x in lines_raw)
        text = str(c.get("text") or "".join(lines))
        cues.append(
            CanonicalSubtitleCue(
                cue_id=str(c["cue_id"]),
                start=float(c["start"]),
                end=float(c["end"]),
                text=text,
                lines=lines,
                confidence=float(c.get("confidence") or 1.0),
                source_span_ids=tuple(str(x) for x in (c.get("source_span_ids") or [])),
            )
        )
    cues.sort(key=lambda x: (x.start, x.end, x.cue_id))
    return cues, {"path": str(path), "sha256": sha256_file(path), "meta": meta, "cue_count": len(cues)}


def dialogue_display_text(cue: CanonicalSubtitleCue) -> str:
    if len(cue.lines) > 1:
        return "\\N".join(cue.lines)
    return cue.text if cue.text else cue.lines[0]


@dataclass(frozen=True)
class AssMaterializationResult:
    ass_path: Path
    manifest_path: Path | None
    cue_count: int
    style_name: str
    canonical_sha256: str
    baseline_sha256: str
    ass_sha256: str
    text_match: str


def write_external_ass(
    *,
    canonical_path: Path,
    ass_out: Path,
    baseline_path: Path | None = None,
    manifest_out: Path | None = None,
) -> AssMaterializationResult:
    cues, canon_info = load_canonical_cues(canonical_path)
    baseline = load_baseline(baseline_path)
    style = baseline["style"]
    style_name = style["Name"]
    px, py = play_res(baseline)

    header_lines = [
        "[Script Info]",
        "ScriptType: v4.00+",
        f"PlayResX: {px}",
        f"PlayResY: {py}",
        "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
        ass_style_line(style),
        "",
        "[Events]",
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
    ]
    events: list[str] = []
    for c in cues:
        disp = dialogue_display_text(c)
        events.append(
            f"Dialogue: 0,{sec_to_ass(c.start)},{sec_to_ass(c.end)},{style_name},,0,0,0,,{disp}"
        )
    body = "\r\n".join(header_lines + events) + "\r\n"
    ass_out.parent.mkdir(parents=True, exist_ok=True)
    ass_bytes = body.encode("utf-8-sig")
    ass_out.write_bytes(ass_bytes)

    canon_norm = [normalize_dialogue_text(c.text) for c in cues]
    ass_norm = [normalize_dialogue_text(d.split(",", 9)[9]) for d in events]
    text_match = "PASS" if canon_norm == ass_norm else "FAIL"

    manifest: dict[str, Any] = {
        "materialization": "external_ass",
        "baseline_id": baseline.get("baseline_id"),
        "baseline_sha256": baseline["_baseline_sha256"],
        "canonical_subtitle_cues_path": canon_info["path"],
        "canonical_subtitle_cues_sha256": canon_info["sha256"],
        "ass_path": str(ass_out.resolve()),
        "ass_sha256": sha256_bytes(ass_bytes),
        "cue_count": len(cues),
        "style_name": style_name,
        "CANONICAL_ASS_TEXT_MATCH": text_match,
    }
    if manifest_out:
        manifest_out.parent.mkdir(parents=True, exist_ok=True)
        manifest_out.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    return AssMaterializationResult(
        ass_path=ass_out,
        manifest_path=manifest_out,
        cue_count=len(cues),
        style_name=style_name,
        canonical_sha256=canon_info["sha256"],
        baseline_sha256=baseline["_baseline_sha256"],
        ass_sha256=manifest["ass_sha256"],
        text_match=text_match,
    )


def verify_ass_matches_baseline_style(ass_path: Path, baseline_path: Path | None = None) -> dict[str, str]:
    baseline = load_baseline(baseline_path)
    expected_line = ass_style_line(baseline["style"])
    for line in ass_path.read_text(encoding="utf-8-sig").splitlines():
        if line.startswith("Style:"):
            return {
                "ASS_STYLE_LINE_MATCH": "PASS" if line.strip() == expected_line else "FAIL",
                "expected": expected_line,
                "actual": line.strip(),
            }
    return {"ASS_STYLE_LINE_MATCH": "FAIL", "error": "no_style_line"}

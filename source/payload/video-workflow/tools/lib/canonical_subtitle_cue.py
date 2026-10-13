"""Canonical Subtitle Cue contract — renderer-neutral subtitle facts."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from asr_timing_evidence import AsrTimingEvidence, load_asr_timing_evidence
from frozen_script_authority import FrozenScriptAuthority, load_frozen_script_file, load_frozen_script_from_brief
from script_audio_monotonic_align import AlignmentResult, TimedScriptSpan, align_script_to_asr, alignment_result_to_dict
from semantic_cue_layout import layout_span_to_cue_parts

CANONICAL_CUE_SCHEMA_VERSION = 1
PIPELINE_ID = "subtitle.authority_alignment_v1"


@dataclass(frozen=True)
class CanonicalSubtitleCue:
    cue_id: str
    start: float
    end: float
    text: str
    lines: tuple[str, ...]
    confidence: float
    source_span_ids: tuple[str, ...]
    text_authority: str = "frozen_script"


def _assign_times(parts: list[dict[str, Any]], span: TimedScriptSpan, cue_prefix: str) -> list[CanonicalSubtitleCue]:
    total_chars = sum(max(p["char_len"], 1) for p in parts)
    dur = max(span.audio_end - span.audio_start, 1e-6)
    t = span.audio_start
    cues: list[CanonicalSubtitleCue] = []
    for i, p in enumerate(parts):
        frac = max(p["char_len"], 1) / total_chars
        end = span.audio_end if i == len(parts) - 1 else t + dur * frac
        cues.append(
            CanonicalSubtitleCue(
                cue_id=f"{cue_prefix}-{i + 1:02d}",
                start=t,
                end=end,
                text=p["text"],
                lines=tuple(p["lines"]),
                confidence=span.confidence,
                source_span_ids=(p["source_span_id"],),
            )
        )
        t = end
    return cues


def build_canonical_subtitle_cues(
    script: FrozenScriptAuthority,
    asr: AsrTimingEvidence,
    tools_dir: Path,
) -> tuple[list[CanonicalSubtitleCue], AlignmentResult, dict[str, Any]]:
    alignment = align_script_to_asr(script.normalized_text, asr)
    meta: dict[str, Any] = {
        "schema_version": CANONICAL_CUE_SCHEMA_VERSION,
        "pipeline_id": PIPELINE_ID,
        "text_authority": script.authority,
        "script_source_path": script.source_path,
        "alignment": alignment_result_to_dict(alignment),
    }

    if alignment.blocked:
        meta["status"] = "BLOCKED"
        meta["block_reason"] = alignment.block_reason
        return [], alignment, meta

    all_cues: list[CanonicalSubtitleCue] = []
    for si, span in enumerate(alignment.spans):
        span_id = f"S{si + 1:02d}"
        parts = layout_span_to_cue_parts(span, span_id, tools_dir)
        all_cues.extend(_assign_times(parts, span, span_id))

    # Verify full text preservation vs frozen script (layout newlines excluded)
    rendered_flat = "".join(c.text.replace("\n", "") for c in all_cues)
    if rendered_flat != script.normalized_text.replace("\n", ""):
        meta["status"] = "BLOCKED"
        meta["block_reason"] = "CANONICAL_TEXT_DRIFT_FROM_FROZEN_SCRIPT"
        return [], alignment, meta

    meta["status"] = "OK"
    meta["cue_count"] = len(all_cues)
    return all_cues, alignment, meta


def canonical_cues_to_dict(cues: list[CanonicalSubtitleCue], meta: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": CANONICAL_CUE_SCHEMA_VERSION,
        "pipeline_id": PIPELINE_ID,
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
                "text_authority": c.text_authority,
            }
            for c in cues
        ],
    }


def to_drt_subtitles(cues: list[CanonicalSubtitleCue], fps: float, timeline_start_frame: int = 0) -> list[dict[str, Any]]:
    """Minimal adapter for drt.assemble spec.subtitles[] (materialization only)."""
    out: list[dict[str, Any]] = []
    for c in cues:
        sf = timeline_start_frame + int(round(c.start * fps))
        ef = timeline_start_frame + int(round(c.end * fps))
        dur = max(ef - sf, 1)
        out.append(
            {
                "startFrame": sf,
                "durationFrames": dur,
                "text": c.text if "\n" in c.text else "\n".join(c.lines) if len(c.lines) > 1 else c.text,
            }
        )
    return out


def to_ass_dialogue_lines(cues: list[CanonicalSubtitleCue]) -> list[dict[str, Any]]:
    """Minimal adapter for external ASS burn-in routes (materialization only)."""
    return [
        {
            "cue_id": c.cue_id,
            "start": c.start,
            "end": c.end,
            "text": c.text.replace("\n", r"\N"),
        }
        for c in cues
    ]


def run_pipeline_from_paths(
    *,
    brief_path: Path | None,
    script_path: Path | None,
    asr_path: Path,
    tools_dir: Path,
) -> dict[str, Any]:
    if brief_path:
        script = load_frozen_script_from_brief(brief_path)
    elif script_path:
        script = load_frozen_script_file(script_path)
    else:
        raise RuntimeError("FROZEN_SCRIPT_REQUIRED: provide --brief or --script")

    asr = load_asr_timing_evidence(asr_path)
    cues, _alignment, meta = build_canonical_subtitle_cues(script, asr, tools_dir)
    doc = canonical_cues_to_dict(cues, meta)
    doc["frozen_script"] = {
        "authority": script.authority,
        "source_path": script.source_path,
        "normalized_text": script.normalized_text,
    }
    doc["renderer_adapters"] = {
        "drt_subtitles": to_drt_subtitles(cues, fps=24.0),
        "ass_dialogues": to_ass_dialogue_lines(cues),
    }
    return doc

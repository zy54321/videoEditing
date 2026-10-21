"""Acquire word-level subtitle timing evidence.

Episode N20261021 used Resolve transcription with include_words=true, then
monotonic alignment onto the frozen script. A single full-span ASR segment is
not precise timing. This module does not invent character-proportional times
and does not call a cloud ASR service.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from asr_timing_evidence import asr_evidence_to_dict, load_asr_timing_evidence

SCHEMA_VERSION = 1
METHOD_RESOLVE_WORDS = "resolve_word_timestamps"
METHOD_EXISTING_WORDS = "existing_word_cues"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def timecode_to_seconds(tc: str, fps: float) -> float:
    text = str(tc).strip()
    if ":" not in text:
        return float(text)
    parts = text.split(":")
    if len(parts) != 4:
        raise ValueError(f"TIMECODE_INVALID: {tc}")
    hh, mm, ss, ff = (int(p) for p in parts)
    if fps <= 0:
        raise ValueError("FPS_INVALID")
    return hh * 3600 + mm * 60 + ss + ff / fps


def _cue_duration(cue: dict[str, Any]) -> float:
    return float(cue["end"]) - float(cue["start"])


def classify_timing_cues(
    cues: list[dict[str, Any]],
    *,
    audio_duration: float | None = None,
) -> str:
    """WORD_LEVEL | SINGLE_SPAN | PROPORTIONAL_GRID | INSUFFICIENT | MISSING."""
    if not cues:
        return "MISSING"
    durations = [_cue_duration(c) for c in cues]
    if len(cues) == 1:
        only = durations[0]
        text_len = len(str(cues[0].get("recognized_text") or ""))
        covers_file = bool(audio_duration and audio_duration >= 8 and only >= 0.85 * audio_duration)
        if covers_file or only >= 8.0 or text_len >= 40:
            return "SINGLE_SPAN"
        return "WORD_LEVEL"
    if len(cues) >= 8:
        mean = sum(durations) / len(durations)
        if mean > 0 and max(abs(d - mean) for d in durations) / mean < 0.02:
            return "PROPORTIONAL_GRID"
    if max(durations) < 8.0:
        return "WORD_LEVEL"
    return "INSUFFICIENT"


def cues_from_resolve_word_transcription(doc: dict[str, Any], *, fps: float = 24.0) -> list[dict[str, Any]]:
    """Convert Resolve get_transcription(include_words=true) into timing cues.

    Recognized text is alignment evidence only. Parentheses-only tokens such as
    '(...)' are breaths, not subtitle words.
    """
    fps = float(doc.get("fps") or fps)
    cues: list[dict[str, Any]] = []
    for seg in doc.get("segments") or []:
        words = seg.get("words") or []
        if not words and seg.get("start") and seg.get("end"):
            continue
        for word in words:
            text = str(word.get("text") or "").strip()
            if not text or text in {"(...)", "…", "..."}:
                continue
            start = timecode_to_seconds(str(word["start"]), fps)
            end = timecode_to_seconds(str(word["end"]), fps)
            if end < start:
                raise ValueError(f"RESOLVE_WORD_RANGE: {text}")
            cues.append(
                {
                    "cue_id": f"w{len(cues) + 1:04d}",
                    "start": round(start, 3),
                    "end": round(end, 3),
                    "recognized_text": text,
                }
            )
    return cues


def reject_proportional_fabrication(cues: list[dict[str, Any]]) -> str | None:
    kind = classify_timing_cues(cues)
    if kind == "PROPORTIONAL_GRID":
        return "PROPORTIONAL_CHAR_TIMING_REJECTED"
    if kind == "SINGLE_SPAN":
        return "SINGLE_SPAN_NOT_PRECISE"
    return None


def probe_duration_seconds(path: Path | None) -> float | None:
    if path is None or not path.is_file():
        return None
    import json as _json
    import subprocess

    proc = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "json",
            str(path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        return None
    try:
        payload = _json.loads(proc.stdout or "{}")
        return float((payload.get("format") or {}).get("duration") or 0) or None
    except (TypeError, ValueError):
        return None


def quality_report(
    cues: list[dict[str, Any]],
    *,
    audio_duration: float | None,
    method: str,
) -> dict[str, Any]:
    gaps: list[dict[str, float]] = []
    ordered = sorted(cues, key=lambda c: float(c["start"]))
    for prev, nxt in zip(ordered, ordered[1:]):
        gap = float(nxt["start"]) - float(prev["end"])
        if gap >= 0.8:
            gaps.append({"after_cue": prev["cue_id"], "gap_sec": round(gap, 3)})
    last_end = float(ordered[-1]["end"]) if ordered else None
    problems: list[str] = []
    if audio_duration and last_end is not None and audio_duration - last_end > 2.0:
        problems.append("TAIL_UNCOVERED")
    if not ordered:
        problems.append("NO_CUES")
    return {
        "schema_version": SCHEMA_VERSION,
        "method": method,
        "cue_count": len(ordered),
        "audio_duration_sec": audio_duration,
        "last_cue_end_sec": last_end,
        "long_pauses_sec": gaps,
        "problems": problems,
        "text_authority": "frozen_script",
        "asr_replaces_script": False,
        "proportional_char_timing": False,
    }


def load_binding(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8-sig"))


def binding_matches(
    binding: dict[str, Any] | None,
    *,
    script_sha256: str | None,
    voice_sha256: str | None,
    evidence_sha256: str | None,
) -> bool:
    """A missing hash is not a match. None does not wildcard the current WAV."""
    if not isinstance(binding, dict) or not evidence_sha256:
        return False
    if binding.get("evidence_sha256") != evidence_sha256:
        return False
    if script_sha256 is not None and binding.get("script_sha256") != script_sha256:
        return False
    if voice_sha256 is not None and binding.get("voice_audio_sha256") != voice_sha256:
        return False
    return bool(script_sha256 or voice_sha256)


def transcription_matches_voice(doc: dict[str, Any] | None, voice_audio_path: Path | None) -> bool:
    """Resolve word JSON is usable only when it records this WAV's SHA256."""
    if not isinstance(doc, dict) or voice_audio_path is None or not voice_audio_path.is_file():
        return False
    stored = str(doc.get("voice_audio_sha256") or "").strip()
    if not stored:
        return False
    return stored == sha256_file(voice_audio_path)


def _alignment_or_block(
    cues: list[dict[str, Any]],
    *,
    script_path: Path | None,
    evidence_path: Path,
    audio_duration: float | None,
    strict: bool,
) -> dict[str, Any] | None:
    """Run the episode monotonic aligner when a frozen script is present.

    Fresh Resolve acquisitions fail closed. Reused word cues still record the
    QA result, and the existing Canonical path keeps its previous contract.
    """
    if script_path is None or not script_path.is_file() or not cues:
        return None
    from frozen_script_word_align import align_frozen_script_to_words, load_script_lines, write_alignment

    words = [
        {"text": c["recognized_text"], "start": c["start"], "end": c["end"]}
        for c in cues
    ]
    aligned = align_frozen_script_to_words(
        load_script_lines(script_path),
        words,
        audio_duration=audio_duration,
    )
    write_alignment(evidence_path.parent / "subtitle-word-alignment.json", aligned)
    if strict and aligned["status"] != "OK":
        return {
            "status": "BLOCKED",
            "reason": "ALIGNMENT_INCOMPLETE",
            "detail": aligned["problems"],
            "alignment": aligned,
        }
    return None


def acquire_subtitle_timing(
    *,
    evidence_path: Path,
    script_path: Path | None = None,
    voice_audio_path: Path | None = None,
    resolve_transcription_path: Path | None = None,
    binding_path: Path | None = None,
    report_path: Path | None = None,
    fps: float = 24.0,
    auto_transcribe: bool = True,
    allow_project_switch: bool = False,
) -> dict[str, Any]:
    """Write asr-timing-evidence.json or return BLOCKED. Never fabricates even splits."""
    audio_duration = probe_duration_seconds(voice_audio_path)
    script_sha = sha256_file(script_path) if script_path and script_path.is_file() else None
    voice_sha = sha256_file(voice_audio_path) if voice_audio_path and voice_audio_path.is_file() else None
    binding = load_binding(binding_path) if binding_path else None

    existing_cues: list[dict[str, Any]] = []
    if evidence_path.is_file():
        ev = load_asr_timing_evidence(evidence_path)
        existing_cues = [
            {
                "cue_id": c.cue_id,
                "start": c.start,
                "end": c.end,
                "recognized_text": c.recognized_text,
            }
            for c in ev.cues
        ]
        kind = classify_timing_cues(existing_cues, audio_duration=audio_duration)
        evidence_sha = sha256_file(evidence_path)
        fresh = binding_matches(
            binding,
            script_sha256=script_sha,
            voice_sha256=voice_sha,
            evidence_sha256=evidence_sha,
        )
        legacy_without_voice = kind == "WORD_LEVEL" and voice_sha is None and binding is None
        if kind == "WORD_LEVEL" and (fresh or legacy_without_voice):
            report = quality_report(existing_cues, audio_duration=audio_duration, method=METHOD_EXISTING_WORDS)
            blocked = _alignment_or_block(
                existing_cues,
                script_path=script_path,
                evidence_path=evidence_path,
                audio_duration=audio_duration,
                strict=False,
            )
            if blocked:
                blocked["report"] = report
                _write_report(report_path, blocked)
                return blocked
            result = {"status": "SKIPPED_EXISTING", "classification": kind, "report": report}
            _write_report(report_path, result)
            return result
        evidence_path.unlink()
        existing_cues = []

    resolve_doc = None
    if resolve_transcription_path and resolve_transcription_path.is_file():
        resolve_doc = json.loads(resolve_transcription_path.read_text(encoding="utf-8-sig"))
    if resolve_doc is None:
        sibling = evidence_path.parent / "resolve-word-transcription.json"
        if sibling.is_file():
            resolve_doc = json.loads(sibling.read_text(encoding="utf-8-sig"))
            resolve_transcription_path = sibling

    if resolve_doc is not None and not transcription_matches_voice(resolve_doc, voice_audio_path):
        if (
            resolve_transcription_path
            and resolve_transcription_path.is_file()
            and resolve_transcription_path.resolve() == (evidence_path.parent / "resolve-word-transcription.json").resolve()
        ):
            resolve_transcription_path.unlink()
        resolve_doc = None
        resolve_transcription_path = None

    if resolve_doc is not None:
        words = resolve_doc.get("segments") and any((s.get("words") or []) for s in resolve_doc["segments"])
        if not words:
            result = {
                "status": "BLOCKED",
                "reason": "RESOLVE_TRANSCRIPTION_WITHOUT_WORDS",
                "detail": "include_words=true is required; a single segment is not timing evidence",
            }
            _write_report(report_path, result)
            return result
        cues = cues_from_resolve_word_transcription(resolve_doc, fps=fps)
        rejection = reject_proportional_fabrication(cues)
        if rejection or classify_timing_cues(cues, audio_duration=audio_duration) != "WORD_LEVEL":
            result = {
                "status": "BLOCKED",
                "reason": rejection or "WORD_TIMING_INSUFFICIENT",
            }
            _write_report(report_path, result)
            return result
        blocked = _alignment_or_block(
            cues,
            script_path=script_path,
            evidence_path=evidence_path,
            audio_duration=audio_duration,
            strict=True,
        )
        if blocked:
            _write_report(report_path, blocked)
            return blocked
        _write_evidence(evidence_path, cues, method=METHOD_RESOLVE_WORDS)
        _write_binding(binding_path, script_sha, voice_sha, sha256_file(evidence_path), METHOD_RESOLVE_WORDS)
        report = quality_report(cues, audio_duration=audio_duration, method=METHOD_RESOLVE_WORDS)
        result = {"status": "ACQUIRED", "classification": "WORD_LEVEL", "reason": None, "report": report}
        _write_report(report_path, result)
        return result

    if auto_transcribe and voice_audio_path and voice_audio_path.is_file():
        from resolve_word_transcribe import transcribe_voice_to_word_json

        fetched = transcribe_voice_to_word_json(
            voice_audio_path,
            evidence_path.parent / "resolve-word-transcription.json",
            allow_project_switch=allow_project_switch,
        )
        if fetched.get("status") != "ACQUIRED":
            result = {
                "status": "BLOCKED",
                "reason": fetched.get("reason") or "RESOLVE_NOT_RUNNING",
                "detail": fetched.get("detail"),
                "live_resolve": fetched.get("live_resolve"),
            }
            _write_report(report_path, result)
            return result
        acquired = acquire_subtitle_timing(
            evidence_path=evidence_path,
            script_path=script_path,
            voice_audio_path=voice_audio_path,
            resolve_transcription_path=evidence_path.parent / "resolve-word-transcription.json",
            binding_path=binding_path,
            report_path=report_path,
            fps=fps,
            auto_transcribe=False,
            allow_project_switch=False,
        )
        if fetched.get("live_resolve"):
            acquired["live_resolve"] = True
        return acquired

    result = {
        "status": "BLOCKED",
        "reason": "WORD_TIMING_PROVIDER_UNAVAILABLE",
        "detail": (
            "No validated word-level cues. Resolve transcription was not started "
            "because no narration WAV was supplied. Do not ask the Owner for timecodes."
        ),
    }
    _write_report(report_path, result)
    return result


def _write_evidence(path: Path, cues: list[dict[str, Any]], *, method: str) -> None:
    doc = asr_evidence_to_dict(
        load_asr_timing_evidence_from_cues(cues),
    )
    doc["timing_method"] = method
    doc["text_authority"] = "frozen_script"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_asr_timing_evidence_from_cues(cues: list[dict[str, Any]]):
    from asr_timing_evidence import AsrTimingCue, AsrTimingEvidence

    built = tuple(
        AsrTimingCue(
            cue_id=str(c["cue_id"]),
            start=float(c["start"]),
            end=float(c["end"]),
            recognized_text=str(c["recognized_text"]),
        )
        for c in cues
    )
    return AsrTimingEvidence(schema_version=SCHEMA_VERSION, cues=built)


def _write_binding(
    path: Path | None,
    script_sha: str | None,
    voice_sha: str | None,
    evidence_sha: str,
    method: str,
) -> None:
    if path is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "schema_version": SCHEMA_VERSION,
                "script_sha256": script_sha,
                "voice_audio_sha256": voice_sha,
                "evidence_sha256": evidence_sha,
                "method": method,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def _write_report(path: Path | None, result: dict[str, Any]) -> None:
    if path is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

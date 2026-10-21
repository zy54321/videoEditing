"""Global monotonic alignment: Frozen Script chars → ASR timing anchors."""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Any

from asr_timing_evidence import AsrTimingCue, AsrTimingEvidence

ALIGNMENT_METHOD = "needleman_wunsch_monotonic_v1"

# Fail-closed thresholds
MAX_CONTIGUOUS_UNALIGNED_CHARS = 8
MAX_UNALIGNED_FRACTION = 0.12

_PUNCT_SKIP = set("，。！？；、：""''（）()【】[]《》…—·,.!?;:")


def _nfc(s: str) -> str:
    return unicodedata.normalize("NFC", s)


def _chars_for_align(s: str) -> list[str]:
    s = _nfc(s)
    return [c for c in s if not c.isspace()]


@dataclass(frozen=True)
class CharTimingAnchor:
    script_index: int
    char: str
    audio_time: float
    asr_cue_id: str
    match_score: int  # 2=exact, 1=mismatch aligned, 0=gap-filled


@dataclass(frozen=True)
class TimedScriptSpan:
    script_start: int
    script_end: int
    text: str
    audio_start: float
    audio_end: float
    confidence: float
    source_asr_cue_ids: tuple[str, ...]
    alignment_method: str
    low_confidence: bool


@dataclass(frozen=True)
class AlignmentResult:
    spans: tuple[TimedScriptSpan, ...]
    low_confidence_spans: tuple[TimedScriptSpan, ...]
    coverage: float
    alignment_method: str
    char_anchors: tuple[CharTimingAnchor, ...]
    blocked: bool
    block_reason: str | None


def _build_asr_char_stream(cues: tuple[AsrTimingCue, ...]) -> tuple[list[str], list[dict[str, Any]]]:
    chars: list[str] = []
    meta: list[dict[str, Any]] = []
    for cue in cues:
        cue_chars = _chars_for_align(cue.recognized_text)
        n = len(cue_chars)
        if n == 0:
            continue
        dur = max(cue.end - cue.start, 1e-6)
        for i, ch in enumerate(cue_chars):
            t = cue.start + (dur * i / n) if n > 1 else cue.start
            chars.append(ch)
            meta.append({"cue_id": cue.cue_id, "time": t, "cue_start": cue.start, "cue_end": cue.end})
    return chars, meta


def _nw_align(a: list[str], b: list[str]) -> list[tuple[int | None, int | None]]:
    """Needleman–Wunsch; returns pairs (i in a or None, j in b or None)."""
    n, m = len(a), len(b)
    match, mismatch, gap = 2, -1, -2
    dp = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        dp[i][0] = dp[i - 1][0] + gap
    for j in range(1, m + 1):
        dp[0][j] = dp[0][j - 1] + gap
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            score_diag = dp[i - 1][j - 1] + (match if a[i - 1] == b[j - 1] else mismatch)
            score_up = dp[i - 1][j] + gap
            score_left = dp[i][j - 1] + gap
            dp[i][j] = max(score_diag, score_up, score_left)

    pairs: list[tuple[int | None, int | None]] = []
    i, j = n, m
    while i > 0 or j > 0:
        if i > 0 and j > 0:
            score_diag = dp[i - 1][j - 1] + (match if a[i - 1] == b[j - 1] else mismatch)
            if dp[i][j] == score_diag:
                pairs.append((i - 1, j - 1))
                i -= 1
                j -= 1
                continue
        if i > 0 and dp[i][j] == dp[i - 1][j] + gap:
            pairs.append((i - 1, None))
            i -= 1
        elif j > 0:
            pairs.append((None, j - 1))
            j -= 1
        else:
            break
    pairs.reverse()
    return pairs


def _interpolate_time(target_idx: int, anchors: dict[int, float]) -> float | None:
    if target_idx in anchors:
        return anchors[target_idx]
    lower = max([k for k in anchors if k < target_idx], default=None)
    upper = min([k for k in anchors if k > target_idx], default=None)
    if lower is None or upper is None:
        return None
    t0, t1 = anchors[lower], anchors[upper]
    frac = (target_idx - lower) / (upper - lower)
    return t0 + (t1 - t0) * frac


def align_script_to_asr(
    script_text: str,
    asr: AsrTimingEvidence,
) -> AlignmentResult:
    script_chars = _chars_for_align(script_text)
    asr_chars, asr_meta = _build_asr_char_stream(asr.cues)

    if not script_chars:
        return AlignmentResult(
            spans=(),
            low_confidence_spans=(),
            coverage=0.0,
            alignment_method=ALIGNMENT_METHOD,
            char_anchors=(),
            blocked=True,
            block_reason="EMPTY_SCRIPT",
        )
    if not asr_chars:
        return AlignmentResult(
            spans=(),
            low_confidence_spans=(),
            coverage=0.0,
            alignment_method=ALIGNMENT_METHOD,
            char_anchors=(),
            blocked=True,
            block_reason="EMPTY_ASR",
        )

    pairs = _nw_align(script_chars, asr_chars)
    time_by_script: dict[int, float] = {}
    cue_by_script: dict[int, str] = {}
    match_score_by_script: dict[int, int] = {}
    aligned_script_indices: set[int] = set()

    for si, aj in pairs:
        if si is None:
            continue
        if aj is not None:
            time_by_script[si] = asr_meta[aj]["time"]
            cue_by_script[si] = asr_meta[aj]["cue_id"]
            ch_s, ch_a = script_chars[si], asr_chars[aj]
            match_score_by_script[si] = 2 if ch_s == ch_a else 1
            aligned_script_indices.add(si)

    # Local interpolation only between confirmed ASR-backed anchors
    for si in range(len(script_chars)):
        if si in time_by_script:
            continue
        t = _interpolate_time(si, time_by_script)
        if t is not None:
            time_by_script[si] = t
            match_score_by_script[si] = 0
            # nearest cue id
            lower = max([k for k in cue_by_script if k < si], default=None)
            upper = min([k for k in cue_by_script if k > si], default=None)
            ref = lower if lower is not None else upper
            if ref is not None:
                cue_by_script[si] = cue_by_script[ref]

    # Trailing script suffix without ASR chars: attach to last cue end (timing evidence), text stays frozen
    last_matched = max(
        [si for si in range(len(script_chars)) if match_score_by_script.get(si, 0) >= 1],
        default=None,
    )
    if last_matched is not None:
        last_cid = cue_by_script.get(last_matched, "")
        cue_end = max((c.end for c in asr.cues if c.cue_id == last_cid), default=time_by_script[last_matched])
        for si in range(last_matched + 1, len(script_chars)):
            if match_score_by_script.get(si, 0) >= 1:
                continue
            time_by_script[si] = cue_end
            match_score_by_script[si] = 1
            cue_by_script[si] = last_cid
            aligned_script_indices.add(si)

    # Punctuation without ASR counterpart inherits previous anchor (not a timing boundary)
    for si in range(len(script_chars)):
        if script_chars[si] not in _PUNCT_SKIP:
            continue
        if match_score_by_script.get(si, 0) >= 1:
            continue
        prev = si - 1
        while prev >= 0 and script_chars[prev] in _PUNCT_SKIP:
            prev -= 1
        if prev >= 0 and prev in time_by_script:
            time_by_script[si] = time_by_script[prev]
            match_score_by_script[si] = 2
            cue_by_script[si] = cue_by_script.get(prev, cue_by_script.get(si, ""))
            aligned_script_indices.add(si)

    def _is_gap_only(si: int) -> bool:
        if si not in time_by_script:
            return True
        return match_score_by_script.get(si, 0) == 0

    # Fail-closed: contiguous gap-filled / unmapped runs (homophone mismatch score=1 is allowed)
    unaligned_run = 0
    max_run = 0
    for si in range(len(script_chars)):
        if not _is_gap_only(si):
            unaligned_run = 0
        else:
            unaligned_run += 1
            max_run = max(max_run, unaligned_run)
    unaligned_count = sum(1 for si in range(len(script_chars)) if _is_gap_only(si))
    frac = unaligned_count / len(script_chars)

    blocked = False
    block_reason = None
    if max_run > MAX_CONTIGUOUS_UNALIGNED_CHARS:
        blocked = True
        block_reason = f"UNALIGNED_RUN_EXCEEDS_{MAX_CONTIGUOUS_UNALIGNED_CHARS}"
    elif frac > MAX_UNALIGNED_FRACTION:
        blocked = True
        block_reason = f"UNALIGNED_FRACTION_{frac:.3f}"

    char_anchors: list[CharTimingAnchor] = []
    for si, ch in enumerate(script_chars):
        if si not in time_by_script:
            continue
        char_anchors.append(
            CharTimingAnchor(
                script_index=si,
                char=ch,
                audio_time=time_by_script[si],
                asr_cue_id=cue_by_script.get(si, ""),
                match_score=match_score_by_script.get(si, 0),
            )
        )

    coverage = len(aligned_script_indices) / len(script_chars)

    # Segment into spans at major punctuation in original script_text (layout-newline-free)
    span_break_after = re.compile(r"([，。！？；])")
    spans: list[TimedScriptSpan] = []
    low_spans: list[TimedScriptSpan] = []

    # Map script_text char indices to align indices (skip whitespace in script_text)
    align_idx = 0
    text_to_align: list[int] = []
    for ch in _nfc(script_text):
        if ch.isspace():
            text_to_align.append(-1)
        else:
            text_to_align.append(align_idx)
            align_idx += 1

    def slice_span(start: int, end: int) -> None:
        if start >= end:
            return
        chunk = script_text[start:end]
        align_indices = [text_to_align[i] for i in range(start, end) if text_to_align[i] >= 0]
        if not align_indices:
            return
        times = [time_by_script[i] for i in align_indices if i in time_by_script]
        if not times:
            return
        cues_ids = tuple(
            sorted({cue_by_script[i] for i in align_indices if i in cue_by_script and cue_by_script[i]})
        )
        mism = sum(1 for i in align_indices if match_score_by_script.get(i, 0) == 1)
        gaps = sum(1 for i in align_indices if match_score_by_script.get(i, 0) == 0)
        conf = 1.0 - (mism * 0.15 + gaps * 0.25) / max(len(align_indices), 1)
        conf = max(0.0, min(1.0, conf))
        low = conf < 0.65 or gaps > 0
        span = TimedScriptSpan(
            script_start=start,
            script_end=end,
            text=chunk,
            audio_start=min(times),
            audio_end=max(times),
            confidence=conf,
            source_asr_cue_ids=cues_ids,
            alignment_method=ALIGNMENT_METHOD,
            low_confidence=low,
        )
        spans.append(span)
        if low:
            low_spans.append(span)

    boundaries = [0]
    for m in span_break_after.finditer(script_text):
        boundaries.append(m.end())
    if boundaries[-1] != len(script_text):
        boundaries.append(len(script_text))

    for bi in range(len(boundaries) - 1):
        slice_span(boundaries[bi], boundaries[bi + 1])

    if not spans and not blocked:
        slice_span(0, len(script_text))

    return AlignmentResult(
        spans=tuple(spans),
        low_confidence_spans=tuple(low_spans),
        coverage=coverage,
        alignment_method=ALIGNMENT_METHOD,
        char_anchors=tuple(char_anchors),
        blocked=blocked,
        block_reason=block_reason,
    )


def alignment_result_to_dict(result: AlignmentResult) -> dict[str, Any]:
    def span_dict(s: TimedScriptSpan) -> dict[str, Any]:
        return {
            "script_start": s.script_start,
            "script_end": s.script_end,
            "text": s.text,
            "audio_start": s.audio_start,
            "audio_end": s.audio_end,
            "confidence": s.confidence,
            "source_asr_cue_ids": list(s.source_asr_cue_ids),
            "alignment_method": s.alignment_method,
            "low_confidence": s.low_confidence,
        }

    return {
        "alignment_method": result.alignment_method,
        "coverage": result.coverage,
        "blocked": result.blocked,
        "block_reason": result.block_reason,
        "spans": [span_dict(s) for s in result.spans],
        "low_confidence_spans": [span_dict(s) for s in result.low_confidence_spans],
    }

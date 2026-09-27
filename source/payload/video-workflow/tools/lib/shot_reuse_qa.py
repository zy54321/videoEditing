"""Minimal shot reuse / ping-pong QA on assembly_plan.shots[]."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

from assembly_shot_utils import (
    CONTINUITY_GAP_SEC,
    build_logical_source_spans,
    build_timed_shots,
    is_editorial_exempt,
)
from shared_asset_library import load_catalog_file

VERDICT_PASS = "PASS"
VERDICT_WARNING = "SHOT_REUSE_WARNING"
VERDICT_REPAIR = "REPAIR_CANDIDATE"
VERDICT_STRONG = "STRONG_REPAIR_CANDIDATE"


@dataclass
class ShotReuseProfile:
    same_source_cooldown_sec: float = 12.0
    same_source_window_sec: float = 30.0
    same_source_max_in_window: int = 2


def load_shot_reuse_profile(path: Path) -> ShotReuseProfile:
    data = load_catalog_file(path)
    thresholds = data.get("thresholds") or {}
    return ShotReuseProfile(
        same_source_cooldown_sec=float(thresholds.get("same_source_cooldown_sec", 12.0)),
        same_source_window_sec=float(thresholds.get("same_source_window_sec", 30.0)),
        same_source_max_in_window=int(thresholds.get("same_source_max_in_window", 2)),
    )


def _ping_pong_patterns(sources: List[str]) -> List[Dict[str, Any]]:
    findings: List[Dict[str, Any]] = []
    n = len(sources)
    for i in range(n - 2):
        a, b, c = sources[i], sources[i + 1], sources[i + 2]
        if a and b and a != b and a == c:
            findings.append({
                "pattern": "A-B-A",
                "verdict": VERDICT_STRONG,
                "indices": [i, i + 1, i + 2],
                "sources": [a, b, a],
            })
    for i in range(n - 3):
        a, b, c, d = sources[i], sources[i + 1], sources[i + 2], sources[i + 3]
        if a and b and a != b and a == c and b == d:
            findings.append({
                "pattern": "A-B-A-B",
                "verdict": VERDICT_STRONG,
                "indices": [i, i + 1, i + 2, i + 3],
                "sources": [a, b, a, b],
            })
    for i in range(n - 4):
        seq = sources[i : i + 5]
        if len(seq) == 5 and seq[0] and seq[1] and seq[0] != seq[1]:
            if seq == [seq[0], seq[1], seq[0], seq[1], seq[0]]:
                findings.append({
                    "pattern": "A-B-A-B-A",
                    "verdict": VERDICT_REPAIR,
                    "indices": list(range(i, i + 5)),
                    "sources": seq,
                })
    return findings


def analyze_shot_reuse(
    assembly_plan: Dict[str, Any],
    profile: ShotReuseProfile,
) -> Dict[str, Any]:
    shots: List[Dict[str, Any]] = list(assembly_plan.get("shots") or [])
    findings: List[Dict[str, Any]] = []
    timed, _ = build_timed_shots(shots)
    logical_spans = build_logical_source_spans(timed, continuity_gap_sec=CONTINUITY_GAP_SEC)

    last_end_by_source: Dict[str, float] = {}
    for span in logical_spans:
        src = span["source_asset"]
        prev_end = last_end_by_source.get(src)
        if prev_end is not None:
            gap = float(span["start_sec"]) - prev_end
            if gap >= CONTINUITY_GAP_SEC and gap < profile.same_source_cooldown_sec:
                findings.append({
                    "verdict": VERDICT_STRONG,
                    "reason": "same_source_cooldown_violation",
                    "source_asset": src,
                    "gap_sec": round(gap, 3),
                    "logical_span_shot_ids": span.get("shot_ids"),
                    "timeline_start_sec": span["start_sec"],
                })
        last_end_by_source[src] = float(span["end_sec"])

    for span in logical_spans:
        src = span["source_asset"]
        window_start = float(span["start_sec"])
        window_end = window_start + profile.same_source_window_sec
        count = 0
        span_starts: List[float] = []
        for other in logical_spans:
            if other["source_asset"] != src:
                continue
            ostart = float(other["start_sec"])
            if ostart >= window_start and ostart < window_end:
                count += 1
                span_starts.append(ostart)
        if count > profile.same_source_max_in_window:
            findings.append({
                "verdict": VERDICT_REPAIR,
                "reason": "same_source_window_exceeded",
                "source_asset": src,
                "count_in_window": count,
                "window_sec": profile.same_source_window_sec,
                "logical_span_starts_sec": span_starts,
            })

    non_exempt_sources: List[str] = []
    for s in timed:
        if is_editorial_exempt(s):
            continue
        non_exempt_sources.append(str(s.get("source_asset") or ""))

    for ping in _ping_pong_patterns(non_exempt_sources):
        mapped = []
        idx = 0
        for s in timed:
            if is_editorial_exempt(s):
                continue
            if idx in ping["indices"]:
                mapped.append({
                    "shot_id": s.get("shot_id"),
                    "source_asset": s.get("source_asset"),
                    "timeline_start_sec": s["_start"],
                })
            idx += 1
        findings.append({
            "verdict": ping["verdict"],
            "reason": "ping_pong_pattern",
            "pattern": ping["pattern"],
            "shots": mapped,
        })

    aba = sum(1 for f in findings if f.get("pattern") == "A-B-A")
    abab = sum(1 for f in findings if f.get("pattern") == "A-B-A-B")
    ababa = sum(1 for f in findings if f.get("pattern") == "A-B-A-B-A")

    overall = VERDICT_PASS
    if any(f["verdict"] == VERDICT_STRONG for f in findings):
        overall = VERDICT_STRONG
    elif any(f["verdict"] == VERDICT_REPAIR for f in findings):
        overall = VERDICT_REPAIR
    elif any(f["verdict"] == VERDICT_WARNING for f in findings):
        overall = VERDICT_WARNING

    return {
        "ok": overall == VERDICT_PASS,
        "verdict": overall,
        "findings": findings,
        "metrics": {
            "ping_pong_aba_count": aba,
            "ping_pong_abab_count": abab,
            "ping_pong_ababa_count": ababa,
            "logical_source_span_count": len(logical_spans),
        },
        "logical_spans": logical_spans,
        "shot_count": len(shots),
    }

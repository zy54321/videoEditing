"""Beat-first pacing QA for Edit Blueprint assembly plans."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from assembly_shot_utils import (
    assembly_fps,
    build_timed_shots,
    is_editorial_exempt,
    is_micro_fragment,
    shot_timeline_duration_sec,
)
from shared_asset_library import load_catalog_file

VERDICT_PASS = "PASS"
VERDICT_WARNING = "PACING_WARNING"
VERDICT_REPAIR = "PACING_REPAIR_CANDIDATE"
VERDICT_MICRO = "MICRO_FRAGMENT_REPAIR_CANDIDATE"
VERDICT_EXEMPT = "PACING_EXEMPT"


@dataclass
class PacingProfile:
    warning_duration_sec: float = 6.0
    repair_review_duration_sec: float = 10.0
    micro_fragment_max_frames: int = 2
    micro_fragment_max_sec: float = 0.084


def load_pacing_profile(path: Path) -> PacingProfile:
    data = load_catalog_file(path)
    thresholds = data.get("thresholds") or {}
    micro = thresholds.get("micro_fragment") or {}
    return PacingProfile(
        warning_duration_sec=float(thresholds.get("warning_duration_sec", 6.0)),
        repair_review_duration_sec=float(thresholds.get("repair_review_duration_sec", 10.0)),
        micro_fragment_max_frames=int(micro.get("max_frames", 2)),
        micro_fragment_max_sec=float(micro.get("max_sec_fallback", 0.084)),
    )


def _same_visual(a: Dict[str, Any], b: Dict[str, Any]) -> bool:
    if a.get("source_asset") != b.get("source_asset"):
        return False
    ar = a.get("source_range") or {}
    br = b.get("source_range") or {}
    return ar == br


def _same_source_asset(a: Dict[str, Any], b: Dict[str, Any]) -> bool:
    return bool(a.get("source_asset")) and a.get("source_asset") == b.get("source_asset")


def analyze_assembly_plan(
    assembly_plan: Dict[str, Any],
    profile: PacingProfile,
    beat_semantic_map: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    shots: List[Dict[str, Any]] = list(assembly_plan.get("shots") or [])
    findings: List[Dict[str, Any]] = []
    beat_semantic_map = beat_semantic_map or {}
    fps = assembly_fps(assembly_plan)

    for shot in shots:
        duration = shot_timeline_duration_sec(shot)
        beat_id = str(shot.get("beat_id") or "")
        if is_editorial_exempt(shot):
            findings.append({
                "shot_id": shot.get("shot_id"),
                "beat_id": beat_id,
                "duration_sec": duration,
                "verdict": VERDICT_EXEMPT,
                "reason": "editorial_exempt",
            })
            continue

        if is_micro_fragment(
            shot,
            fps,
            profile.micro_fragment_max_frames,
            profile.micro_fragment_max_sec,
        ):
            findings.append({
                "shot_id": shot.get("shot_id"),
                "beat_id": beat_id,
                "duration_sec": duration,
                "duration_frames": int(round(duration * fps)),
                "verdict": VERDICT_MICRO,
                "reason": "unintentional_micro_fragment",
                "repair_route": ["clip.merge_same_source_adjacent"],
            })
            continue

        if duration >= profile.repair_review_duration_sec:
            findings.append({
                "shot_id": shot.get("shot_id"),
                "beat_id": beat_id,
                "duration_sec": duration,
                "verdict": VERDICT_REPAIR,
                "reason": "duration_exceeds_repair_threshold",
                "repair_route": ["clip.source_range", "clip.assemble"],
            })
        elif duration >= profile.warning_duration_sec:
            findings.append({
                "shot_id": shot.get("shot_id"),
                "beat_id": beat_id,
                "duration_sec": duration,
                "verdict": VERDICT_WARNING,
                "reason": "duration_exceeds_warning_threshold",
            })
        else:
            findings.append({
                "shot_id": shot.get("shot_id"),
                "beat_id": beat_id,
                "duration_sec": duration,
                "verdict": VERDICT_PASS,
            })

    i = 0
    while i < len(shots):
        j = i + 1
        while j < len(shots) and _same_visual(shots[i], shots[j]):
            j += 1
        span_shots = shots[i:j]
        span_duration = sum(shot_timeline_duration_sec(s) for s in span_shots)
        beat_ids = {str(s.get("beat_id") or "") for s in span_shots}
        semantics = {
            str(s.get("semantic_beat") or beat_semantic_map.get(str(s.get("beat_id") or ""), s.get("beat_id")))
            for s in span_shots
        }
        if len(semantics) > 1 and span_duration >= profile.repair_review_duration_sec:
            if not any(is_editorial_exempt(s) for s in span_shots):
                findings.append({
                    "shot_id": span_shots[0].get("shot_id"),
                    "beat_id": ",".join(sorted(beat_ids)),
                    "duration_sec": span_duration,
                    "verdict": VERDICT_REPAIR,
                    "reason": "unchanged_visual_span_across_semantic_beats",
                    "span_shot_ids": [s.get("shot_id") for s in span_shots],
                    "repair_route": ["clip.source_range", "clip.assemble", "visual.reframe.static"],
                })
        i = j

    i = 0
    while i < len(shots):
        j = i + 1
        while j < len(shots) and _same_source_asset(shots[i], shots[j]):
            j += 1
        span_shots = shots[i:j]
        span_duration = sum(shot_timeline_duration_sec(s) for s in span_shots)
        if len(span_shots) >= 2 and span_duration >= profile.repair_review_duration_sec:
            if not any(is_editorial_exempt(s) for s in span_shots):
                findings.append({
                    "shot_id": span_shots[0].get("shot_id"),
                    "beat_id": ",".join(str(s.get("beat_id") or "") for s in span_shots),
                    "duration_sec": span_duration,
                    "verdict": VERDICT_REPAIR,
                    "reason": "same_source_asset_span",
                    "span_shot_ids": [s.get("shot_id") for s in span_shots],
                    "source_asset": span_shots[0].get("source_asset"),
                    "repair_route": ["clip.source_range", "clip.assemble"],
                })
        i = j

    overall = VERDICT_PASS
    if any(f["verdict"] in (VERDICT_REPAIR, VERDICT_MICRO) for f in findings):
        overall = VERDICT_REPAIR
    elif any(f["verdict"] == VERDICT_WARNING for f in findings):
        overall = VERDICT_WARNING

    micro_count = sum(1 for f in findings if f["verdict"] == VERDICT_MICRO)

    return {
        "ok": overall == VERDICT_PASS,
        "verdict": overall,
        "findings": findings,
        "shot_count": len(shots),
        "metrics": {"micro_fragment_candidate_count": micro_count},
    }


def analyze_blueprint_file(path: Path, profile_path: Path) -> Dict[str, Any]:
    blueprint = load_catalog_file(path)
    profile = load_pacing_profile(profile_path)
    assembly = blueprint.get("assembly_plan") or {}
    beat_map = {}
    for beat in blueprint.get("beats") or []:
        bid = str(beat.get("beat_id") or "")
        beat_map[bid] = str(beat.get("narrative_function") or bid)
    return analyze_assembly_plan(assembly, profile, beat_map)

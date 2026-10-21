"""Apply one-pass assembly repairs — micro-fragment merge, validated source range, approved alternates only."""
from __future__ import annotations

import copy
from typing import Any, Dict, List, Optional, Tuple

from assembly_shot_utils import (
    assembly_fps,
    beat_ids_of,
    build_timed_shots,
    is_editorial_exempt,
    is_micro_fragment,
    joined_timing,
    pick_valid_approved_alternate,
    shot_timeline_duration_sec,
    source_join_decision,
    validate_source_range,
)
from pacing_qa import VERDICT_MICRO, VERDICT_REPAIR as PACING_REPAIR, analyze_assembly_plan, load_pacing_profile
from shot_reuse_qa import VERDICT_REPAIR as REUSE_REPAIR, VERDICT_STRONG, analyze_shot_reuse, load_shot_reuse_profile

REPAIR_ACTION_MERGE = "clip.merge_same_source_adjacent"
REPAIR_ACTION_CONTINUOUS = "clip.merge_continuous_source"
REPAIR_ACTION_SOURCE_RANGE = "clip.source_range"
REPAIR_ACTION_ALTERNATE = "clip.alternate_source"

STATUS_CONVERGED = "ASSEMBLY_REPAIR_CONVERGED"
STATUS_NOT_CONVERGED = "ASSEMBLY_REPAIR_NOT_CONVERGED"


def _qa_fully_pass(pacing: Dict[str, Any], reuse: Dict[str, Any]) -> bool:
    return bool(pacing.get("ok")) and bool(reuse.get("ok"))


def _merge_pair(prev: Dict[str, Any], nxt: Dict[str, Any], decision: Dict[str, Any]) -> Dict[str, Any]:
    """Join two shots whose timeline and Resolve source frames already abut."""
    merged = joined_timing(prev, nxt)
    merged_clip = decision.get("merged_clip") or {}
    if merged_clip.get("start_frame") is not None:
        merged["source_in_frame"] = int(merged_clip["start_frame"])
    if merged_clip.get("end_frame") is not None:
        merged["source_out_frame"] = int(merged_clip["end_frame"])
    beats = beat_ids_of(prev)
    for beat_id in beat_ids_of(nxt):
        if beat_id not in beats:
            beats.append(beat_id)
    if beats:
        merged["beat_id"] = beats[0]
        merged["beat_ids"] = beats
    absorbed = list(prev.get("absorbed_shot_ids") or [])
    absorbed.append(nxt.get("shot_id"))
    merged["absorbed_shot_ids"] = absorbed
    merged["continuous_shot_preservation"] = {
        "joined_shot_ids": [prev.get("shot_id"), nxt.get("shot_id")],
        "source_delta_frames": decision.get("source_delta_frames"),
        "timeline_delta_frames": decision.get("timeline_delta_frames", 0),
        "prev_clip": decision.get("prev_clip"),
        "next_clip": decision.get("next_clip"),
        "merged_clip": decision.get("merged_clip"),
        "source_range_replanned": False,
    }
    return merged


_BLOCKING_JOIN = {
    "source_gap",
    "source_overlap",
    "frame_inconsistent",
    "source_fps_conflict",
    "timeline_gap",
    "timeline_overlap",
    "timeline_position_unproven",
    "transform_conflict",
    "speed_conflict",
    "cut_intent",
    "effect_or_transition",
    "editorial_exempt",
}


def preserve_continuous_shots(assembly_plan: Dict[str, Any]) -> Dict[str, Any]:
    """Collapse adjacent shots whose timeline and source frames already abut.

    A timeline hole, a source-frame hole, or a one-frame overlap stays split.
    """
    plan = copy.deepcopy(assembly_plan)
    shots: List[Dict[str, Any]] = list(plan.get("shots") or [])
    fps = assembly_fps(plan)
    actions: List[Dict[str, Any]] = []
    blocked: List[Dict[str, Any]] = []
    index = 1
    while index < len(shots):
        decision = source_join_decision(shots[index - 1], shots[index], fps)
        if decision.get("decision") == "merge":
            survivor = _merge_pair(shots[index - 1], shots[index], decision)
            actions.append({
                "shot_id": shots[index].get("shot_id"),
                "absorbed_into": shots[index - 1].get("shot_id"),
                "beat_ids": survivor.get("beat_ids"),
                "repair": {
                    "action": REPAIR_ACTION_CONTINUOUS,
                    "reason": "continuous_source_and_timeline_abut",
                    "source_delta_frames": decision.get("source_delta_frames"),
                    "timeline_delta_frames": decision.get("timeline_delta_frames", 0),
                    "source_range_replanned": False,
                },
                "trigger": "continuous_shot_preservation",
            })
            shots = shots[: index - 1] + [survivor] + shots[index + 1 :]
            continue
        if decision.get("decision") in _BLOCKING_JOIN:
            blocked.append({**decision, "trigger": "continuous_shot_preservation"})
        index += 1
    plan["shots"] = shots
    return {
        "assembly_plan": plan,
        "actions": actions,
        "blocked": blocked,
        "action_count": len(actions),
    }


def _try_merge_micro_fragment(
    shots: List[Dict[str, Any]],
    idx: int,
    fps: float,
    profile,
) -> Tuple[Optional[List[Dict[str, Any]]], Optional[Dict[str, Any]]]:
    """Merge a micro fragment only when the continuous-shot checks already allow it.

    A source hole, a timeline hole, or a conflicting treatment is not absorbed.
    The survivor is built by the same join used for ordinary continuous shots.
    """
    if idx <= 0 or idx >= len(shots):
        return None, None
    micro = shots[idx]
    prev = shots[idx - 1]
    if not is_micro_fragment(
        micro,
        fps,
        profile.micro_fragment_max_frames,
        profile.micro_fragment_max_sec,
    ):
        return None, None
    decision = source_join_decision(prev, micro, fps)
    if decision.get("decision") != "merge":
        return None, {
            **decision,
            "trigger": "micro_fragment",
            "repair_applied": False,
            "source_range_replanned": False,
        }
    survivor = _merge_pair(prev, micro, decision)
    new_shots = shots[: idx - 1] + [survivor] + shots[idx + 1 :]
    action = {
        "shot_id": micro.get("shot_id"),
        "absorbed_into": prev.get("shot_id"),
        "beat_ids": survivor.get("beat_ids"),
        "repair": {
            "action": REPAIR_ACTION_CONTINUOUS,
            "reason": "micro_fragment_continuous_abut",
            "source_delta_frames": decision.get("source_delta_frames"),
            "timeline_delta_frames": decision.get("timeline_delta_frames", 0),
            "source_range_replanned": False,
        },
        "trigger": "micro_fragment",
    }
    return new_shots, action


def _try_approved_alternate_swap(
    shot: Dict[str, Any],
    avoid: set,
) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
    cand = pick_valid_approved_alternate(shot, avoid)
    if not cand:
        return None, None
    asset = str(cand["source_asset"])
    out = copy.deepcopy(shot)
    out["source_asset"] = asset
    need = shot_timeline_duration_sec(shot)
    default = cand.get("source_range")
    if isinstance(default, dict) and "in_sec" in default and "out_sec" in default:
        in_s, out_s = float(default["in_sec"]), float(default["out_sec"])
    else:
        sd = float(cand["source_duration_sec"])
        in_s, out_s = 0.0, min(sd, need)
    probe = {"source_asset": asset, "source_duration_sec": cand.get("source_duration_sec")}
    ok, err = validate_source_range(probe, in_s, out_s, min_duration_sec=need * 0.9)
    if not ok:
        return None, {"reason": "alternate_range_invalid", "error": err, "candidate": asset}
    out["source_range"] = {"in_sec": in_s, "out_sec": out_s}
    out["repair"] = {
        "action": REPAIR_ACTION_ALTERNATE,
        "reason": "approved_alternate",
        "from_source": shot.get("source_asset"),
        "to_source": asset,
    }
    return out, out.get("repair")


def repair_assembly_plan(
    assembly_plan: Dict[str, Any],
    *,
    pacing_profile_path: Any,
    reuse_profile_path: Any,
    max_actions: int = 16,
) -> Dict[str, Any]:
    preserved = preserve_continuous_shots(assembly_plan)
    plan = preserved["assembly_plan"]
    shots: List[Dict[str, Any]] = list(plan.get("shots") or [])
    pacing_profile = load_pacing_profile(pacing_profile_path)
    reuse_profile = load_shot_reuse_profile(reuse_profile_path)
    fps = assembly_fps(plan)

    before_pacing = analyze_assembly_plan(assembly_plan, pacing_profile)
    before_reuse = analyze_shot_reuse(assembly_plan, reuse_profile)
    actions: List[Dict[str, Any]] = list(preserved["actions"])
    blocked: List[Dict[str, Any]] = list(preserved["blocked"])

    # 1) Micro-fragment merge uses the same join decision. A refusal is not a completed repair.
    idx = 1
    while idx < len(shots) and len(actions) < max_actions:
        new_shots, outcome = _try_merge_micro_fragment(shots, idx, fps, pacing_profile)
        if new_shots and outcome and outcome.get("repair"):
            shots = new_shots
            actions.append(outcome)
            idx = max(1, idx - 1)
            continue
        if outcome and outcome.get("decision"):
            blocked.append(outcome)
        idx += 1

    # 2) Ping-pong — approved alternates only
    sources = [str(s.get("source_asset") or "") for s in shots]
    for i in range(len(sources) - 2):
        if len(actions) >= max_actions:
            break
        a, b, c = sources[i], sources[i + 1], sources[i + 2]
        if a and b and a != b and a == c:
            target = shots[i + 2]
            if is_editorial_exempt(target):
                continue
            swapped, repair = _try_approved_alternate_swap(target, {a, b})
            if swapped:
                shots[i + 2] = swapped
                sources[i + 2] = str(swapped.get("source_asset") or "")
                actions.append({
                    "shot_id": target.get("shot_id"),
                    "repair": repair,
                    "trigger": "ping_pong_aba",
                })
            else:
                blocked.append({
                    "shot_id": target.get("shot_id"),
                    "trigger": "ping_pong_aba",
                    "reason": "no_approved_alternate",
                })

    plan["shots"] = shots
    after_pacing = analyze_assembly_plan(plan, pacing_profile)
    after_reuse = analyze_shot_reuse(plan, reuse_profile)
    converged = _qa_fully_pass(after_pacing, after_reuse)

    return {
        "ok": converged,
        "converged": converged,
        "status": STATUS_CONVERGED if converged else STATUS_NOT_CONVERGED,
        "actions": actions,
        "action_count": len(actions),
        "blocked": blocked,
        "before": {"pacing": before_pacing, "reuse": before_reuse},
        "after": {"pacing": after_pacing, "reuse": after_reuse},
        "assembly_plan": plan,
    }

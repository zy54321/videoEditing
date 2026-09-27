"""Apply one-pass assembly repairs — micro-fragment merge, validated source range, approved alternates only."""
from __future__ import annotations

import copy
from typing import Any, Dict, List, Optional, Tuple

from assembly_shot_utils import (
    assembly_fps,
    build_timed_shots,
    is_editorial_exempt,
    is_micro_fragment,
    pick_valid_approved_alternate,
    shot_timeline_duration_sec,
    source_range_bounds,
    validate_source_range,
)
from pacing_qa import VERDICT_MICRO, VERDICT_REPAIR as PACING_REPAIR, analyze_assembly_plan, load_pacing_profile
from shot_reuse_qa import VERDICT_REPAIR as REUSE_REPAIR, VERDICT_STRONG, analyze_shot_reuse, load_shot_reuse_profile

REPAIR_ACTION_MERGE = "clip.merge_same_source_adjacent"
REPAIR_ACTION_SOURCE_RANGE = "clip.source_range"
REPAIR_ACTION_ALTERNATE = "clip.alternate_source"

STATUS_CONVERGED = "ASSEMBLY_REPAIR_CONVERGED"
STATUS_NOT_CONVERGED = "ASSEMBLY_REPAIR_NOT_CONVERGED"


def _qa_fully_pass(pacing: Dict[str, Any], reuse: Dict[str, Any]) -> bool:
    return bool(pacing.get("ok")) and bool(reuse.get("ok"))


def _try_merge_micro_fragment(
    shots: List[Dict[str, Any]],
    idx: int,
    fps: float,
    profile,
) -> Tuple[Optional[List[Dict[str, Any]]], Optional[Dict[str, Any]]]:
    if idx <= 0 or idx >= len(shots):
        return None, None
    micro = shots[idx]
    prev = shots[idx - 1]
    if is_editorial_exempt(micro) or is_editorial_exempt(prev):
        return None, None
    if str(prev.get("source_asset") or "") != str(micro.get("source_asset") or ""):
        return None, None
    if not is_micro_fragment(
        micro,
        fps,
        profile.micro_fragment_max_frames,
        profile.micro_fragment_max_sec,
    ):
        return None, None

    micro_dur = shot_timeline_duration_sec(micro)
    prev_dur = shot_timeline_duration_sec(prev)
    merged = copy.deepcopy(prev)
    merged["timeline_duration_sec"] = prev_dur + micro_dur
    if "timeline_start_sec" in prev:
        merged["timeline_start_sec"] = prev.get("timeline_start_sec")

    pb = source_range_bounds(prev)
    mb = source_range_bounds(micro)
    if pb and mb and abs(mb[0] - pb[1]) <= (2.0 / fps):
        merged["source_range"] = {"in_sec": pb[0], "out_sec": mb[1]}
        sd = merged.get("source_duration_sec") or prev.get("source_duration_sec")
        if sd is not None:
            probe = {**merged, "source_duration_sec": sd}
            ok, err = validate_source_range(probe, pb[0], mb[1], min_duration_sec=micro_dur * 0.5)
            if not ok:
                return None, {"reason": "merge_source_range_invalid", "error": err}
    elif pb:
        merged["source_range"] = {"in_sec": pb[0], "out_sec": pb[1]}

    new_shots = shots[: idx - 1] + [merged] + shots[idx + 1 :]
    action = {
        "shot_id": micro.get("shot_id"),
        "absorbed_into": prev.get("shot_id"),
        "repair": {
            "action": REPAIR_ACTION_MERGE,
            "reason": "micro_fragment_same_source_adjacent",
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
    plan = copy.deepcopy(assembly_plan)
    shots: List[Dict[str, Any]] = list(plan.get("shots") or [])
    pacing_profile = load_pacing_profile(pacing_profile_path)
    reuse_profile = load_shot_reuse_profile(reuse_profile_path)
    fps = assembly_fps(plan)

    before_pacing = analyze_assembly_plan(plan, pacing_profile)
    before_reuse = analyze_shot_reuse(plan, reuse_profile)
    actions: List[Dict[str, Any]] = []
    blocked: List[Dict[str, Any]] = []

    # 1) Micro-fragment merge (same source, adjacent)
    idx = 1
    while idx < len(shots) and len(actions) < max_actions:
        new_shots, action = _try_merge_micro_fragment(shots, idx, fps, pacing_profile)
        if new_shots and action:
            shots = new_shots
            actions.append(action)
            idx = max(1, idx - 1)
            continue
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

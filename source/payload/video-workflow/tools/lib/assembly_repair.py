"""Apply one-pass assembly repairs for pacing + shot reuse (source_range / alternate source)."""
from __future__ import annotations

import copy
from typing import Any, Dict, List, Optional, Set

from pacing_qa import VERDICT_REPAIR as PACING_REPAIR, analyze_assembly_plan, load_pacing_profile
from shot_reuse_qa import VERDICT_REPAIR as REUSE_REPAIR, VERDICT_STRONG, analyze_shot_reuse, load_shot_reuse_profile

REPAIR_ACTION_SOURCE_RANGE = "clip.source_range"
REPAIR_ACTION_ALTERNATE = "clip.alternate_source"
REPAIR_ACTION_ASSEMBLE = "clip.assemble"


def _shot_duration(shot: Dict[str, Any]) -> float:
    if "timeline_duration_sec" in shot:
        return float(shot["timeline_duration_sec"])
    src = shot.get("source_range") or {}
    if isinstance(src, dict) and "in_sec" in src and "out_sec" in src:
        return float(src["out_sec"]) - float(src["in_sec"])
    return float(shot.get("duration_sec") or 0)


def _same_visual(a: Dict[str, Any], b: Dict[str, Any]) -> bool:
    if a.get("source_asset") != b.get("source_asset"):
        return False
    return (a.get("source_range") or {}) == (b.get("source_range") or {})


def _same_source_asset(a: Dict[str, Any], b: Dict[str, Any]) -> bool:
    return bool(a.get("source_asset")) and a.get("source_asset") == b.get("source_asset")


def _pool_assets(shots: List[Dict[str, Any]]) -> List[str]:
    seen: List[str] = []
    for s in shots:
        src = str(s.get("source_asset") or "")
        if src and src not in seen:
            seen.append(src)
    return seen


def _pick_alternate(pool: List[str], avoid: Set[str]) -> Optional[str]:
    for src in pool:
        if src not in avoid:
            return src
    return None


def _shift_source_range(shot: Dict[str, Any], offset_sec: float) -> Dict[str, Any]:
    out = copy.deepcopy(shot)
    src = dict(out.get("source_range") or {"in_sec": 0, "out_sec": _shot_duration(shot)})
    dur = float(src.get("out_sec", 0)) - float(src.get("in_sec", 0))
    new_in = max(0.0, float(src.get("in_sec", 0)) + offset_sec)
    out["source_range"] = {"in_sec": new_in, "out_sec": new_in + dur}
    out["repair"] = {
        "action": REPAIR_ACTION_SOURCE_RANGE,
        "reason": "pacing_or_reuse",
        "offset_sec": offset_sec,
    }
    return out


def _swap_alternate(shot: Dict[str, Any], new_source: str, pool: List[str]) -> Dict[str, Any]:
    out = copy.deepcopy(shot)
    out["source_asset"] = new_source
    dur = _shot_duration(shot)
    out["source_range"] = {"in_sec": 0.0, "out_sec": dur}
    out["repair"] = {
        "action": REPAIR_ACTION_ALTERNATE,
        "reason": "ping_pong_break",
        "from_source": shot.get("source_asset"),
        "to_source": new_source,
    }
    return out


def repair_assembly_plan(
    assembly_plan: Dict[str, Any],
    *,
    pacing_profile_path: Any,
    reuse_profile_path: Any,
    max_actions: int = 8,
) -> Dict[str, Any]:
    plan = copy.deepcopy(assembly_plan)
    shots: List[Dict[str, Any]] = list(plan.get("shots") or [])
    pacing_profile = load_pacing_profile(pacing_profile_path)
    reuse_profile = load_shot_reuse_profile(reuse_profile_path)

    before_pacing = analyze_assembly_plan(plan, pacing_profile)
    before_reuse = analyze_shot_reuse(plan, reuse_profile)
    actions: List[Dict[str, Any]] = []
    pool = _pool_assets(shots)

    # Pacing: long consecutive same source_asset span — alternate middle shot or shift source_range
    i = 0
    while i < len(shots) and len(actions) < max_actions:
        j = i + 1
        while j < len(shots) and _same_source_asset(shots[i], shots[j]):
            j += 1
        span = shots[i:j]
        span_dur = sum(_shot_duration(s) for s in span)
        if len(span) >= 2 and span_dur >= pacing_profile.repair_review_duration_sec:
            mid_idx = i + len(span) // 2
            mid = shots[mid_idx]
            if not mid.get("editorial_reason") and not mid.get("pacing_exempt"):
                alt = _pick_alternate(pool, {str(mid.get("source_asset") or "")})
                if alt:
                    shots[mid_idx] = _swap_alternate(mid, alt, pool)
                    actions.append({
                        "shot_id": mid.get("shot_id"),
                        "repair": shots[mid_idx].get("repair"),
                        "trigger": "same_source_asset_span",
                        "item_index": mid.get("item_index"),
                    })
                else:
                    repaired = _shift_source_range(mid, offset_sec=4.0)
                    shots[mid_idx] = repaired
                    actions.append({
                        "shot_id": mid.get("shot_id"),
                        "repair": repaired.get("repair"),
                        "trigger": "same_source_asset_span",
                    })
        i = j

    # Reuse: break A-B-A by swapping the third A (index i+2) to alternate source
    sources = [str(s.get("source_asset") or "") for s in shots]
    for i in range(len(sources) - 2):
        if len(actions) >= max_actions:
            break
        a, b, c = sources[i], sources[i + 1], sources[i + 2]
        if a and b and a != b and a == c:
            target = shots[i + 2]
            if target.get("editorial_reason"):
                continue
            alt = _pick_alternate(pool, {a, b})
            if alt:
                shots[i + 2] = _swap_alternate(target, alt, pool)
                sources[i + 2] = alt
                actions.append({
                    "shot_id": target.get("shot_id"),
                    "repair": shots[i + 2].get("repair"),
                    "trigger": "ping_pong_aba",
                })

    plan["shots"] = shots
    after_pacing = analyze_assembly_plan(plan, pacing_profile)
    after_reuse = analyze_shot_reuse(plan, reuse_profile)

    return {
        "ok": after_pacing["verdict"] != PACING_REPAIR and after_reuse["verdict"] not in (REUSE_REPAIR, VERDICT_STRONG),
        "actions": actions,
        "action_count": len(actions),
        "before": {"pacing": before_pacing, "reuse": before_reuse},
        "after": {"pacing": after_pacing, "reuse": after_reuse},
        "assembly_plan": plan,
    }

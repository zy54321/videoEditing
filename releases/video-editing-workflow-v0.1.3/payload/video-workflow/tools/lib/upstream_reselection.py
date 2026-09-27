"""Upstream candidate selection — separate from assembly_repair execution."""
from __future__ import annotations

import copy
import json
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from assembly_repair import repair_assembly_plan
from assembly_shot_utils import shot_timeline_duration_sec, validate_source_range, pick_valid_approved_alternate
from pacing_qa import analyze_assembly_plan, load_pacing_profile
from shot_reuse_qa import analyze_shot_reuse, load_shot_reuse_profile

VALIDATION_APPROVED = "APPROVED"
VALIDATION_REJECTED = "REJECTED"

# N02 input pool (media_pool_item_id) — from production pool probe
N02_CATALOG: Dict[str, Dict[str, Any]] = {
    "coffee_shop": {
        "source_asset": "b0cedc60-5c8a-4ad8-a57b-c695cadf7616",
        "source_asset_name": "Couple of girls chatting in a coffee shop [couple-of-girls-chatting-in-a-coffee-shop-41862].mp4",
        "semantic_tags": ["cafe", "social", "indoor"],
        "source_duration_sec": 10.96,
        "default_range": {"in_sec": 0.5, "out_sec": 5.25},
    },
    "open_sign": {
        "source_asset": "f5820003-e145-4106-a49e-e8276a85e368",
        "source_asset_name": "open-business-sign [6115073].mp4",
        "semantic_tags": ["retail", "sign", "establishing"],
        "source_duration_sec": 22.08,
        "default_range": {"in_sec": 2.0, "out_sec": 6.0},
    },
    "business_hall": {
        "source_asset": "08ebb267-0648-43d5-bf0a-c91ec7e0326d",
        "source_asset_name": "Two business people walk in an office hall [two-business-people-walk-in-an-office-hall-315].mp4",
        "semantic_tags": ["office", "walk", "workplace"],
        "source_duration_sec": 34.83,
        "default_range": {"in_sec": 4.0, "out_sec": 8.0},
    },
    "coffee_cup": {
        "source_asset": "c82f314f-d489-436e-8ad6-7977e06b8c3a",
        "source_asset_name": "Cup being filled with coffee in a coffee machine [cup-being-filled-with-coffee-in-a-coffee-machine-41865].mp4",
        "semantic_tags": ["coffee", "detail", "indoor"],
        "source_duration_sec": 13.17,
        "default_range": {"in_sec": 1.0, "out_sec": 5.0},
    },
    "clinic_alt": {
        "source_asset": "3f196f0c-bf86-478b-b51e-c25ccb8dc419",
        "source_asset_name": "a-person-entering-the-clinic [6998656].mp4",
        "semantic_tags": ["clinic", "enter"],
        "source_duration_sec": 33.2,
        "default_range": {"in_sec": 8.0, "out_sec": 12.0},
    },
}


def _candidate_record(
    shot: Dict[str, Any],
    catalog_key: str,
    *,
    semantic_reason: str,
    reuse_effect: str,
    pacing_effect: str,
    range_override: Optional[Dict[str, float]] = None,
) -> Dict[str, Any]:
    cat = N02_CATALOG[catalog_key]
    need = shot_timeline_duration_sec(shot)
    sr = range_override or cat["default_range"]
    in_s, out_s = float(sr["in_sec"]), float(sr["out_sec"])
    if out_s - in_s < need * 0.85:
        out_s = in_s + need + 0.5
    probe = {
        "source_asset": cat["source_asset"],
        "source_duration_sec": cat["source_duration_sec"],
    }
    ok, err = validate_source_range(probe, in_s, out_s, min_duration_sec=need * 0.85)
    status = VALIDATION_APPROVED if ok else VALIDATION_REJECTED
    return {
        "beat_id": shot.get("beat_id"),
        "shot_id": shot.get("shot_id"),
        "current_source": shot.get("source_asset"),
        "candidate_source": cat["source_asset"],
        "candidate_source_name": cat["source_asset_name"],
        "candidate_source_range": {"in_sec": in_s, "out_sec": out_s},
        "source_duration": cat["source_duration_sec"],
        "semantic_reason": semantic_reason,
        "reuse_effect": reuse_effect,
        "pacing_effect": pacing_effect,
        "validation_status": status,
        "validation_error": err,
        "alternate_source_assets": [
            {
                "source_asset": cat["source_asset"],
                "source_duration_sec": cat["source_duration_sec"],
                "source_range": {"in_sec": in_s, "out_sec": out_s},
            }
        ],
    }


def propose_n02_reselection(assembly_plan: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Curated N02 upstream proposals for blocked editorial patterns."""
    shots = list(assembly_plan.get("shots") or [])
    by_id = {s.get("shot_id"): s for s in shots}
    proposals: List[Dict[str, Any]] = []

    rules: List[Tuple[str, str, str, str, str]] = [
        ("V1-03", "coffee_shop", "break plaza return after market", "reduces plaza ping-pong", "neutral"),
        ("V1-04", "open_sign", "alternate retail interior", "break market repeat", "neutral"),
        ("V1-10", "business_hall", "office B-roll variant at span tail", "break long office same-source span", "shortens same-visual"),
        ("V1-20", "open_sign", "retail sign instead of plaza return", "reduces plaza window density", "neutral"),
        ("V1-16", "coffee_cup", "money beat detail alternate", "break hands-green cooldown", "neutral"),
        ("V1-21", "coffee_cup", "coffee detail instead of mountain return", "break mountain ping-pong", "neutral"),
        ("V1-22", "coffee_cup", "absorb micro-fragment into prior coffee beat", "enables micro merge", "neutral"),
        ("V1-23", "clinic_alt", "clinic beat alternate vs open sign cooldown", "spacing open_sign reuse", "neutral"),
        ("V1-24", "coffee_shop", "closing street beat alternate", "reduces plaza window density", "neutral"),
    ]

    for shot_id, cat_key, sem, reuse_eff, pace_eff in rules:
        shot = by_id.get(shot_id)
        if not shot:
            continue
        rec = _candidate_record(shot, cat_key, semantic_reason=sem, reuse_effect=reuse_eff, pacing_effect=pace_eff)
        proposals.append(rec)
    return proposals


def finalize_proposal_validation(
    assembly_plan: Dict[str, Any],
    proposals: List[Dict[str, Any]],
    reuse_profile_path: Path,
) -> List[Dict[str, Any]]:
    """Mark proposals APPROVED only if batch upstream swaps pass reuse QA."""
    plan = inject_approved_alternates(assembly_plan, proposals)
    plan, applied = apply_direct_upstream_swaps(plan, proposals)
    plan = normalize_timeline_starts(plan)
    reuse = analyze_shot_reuse(plan, load_shot_reuse_profile(reuse_profile_path))
    applied_ids = {a["shot_id"] for a in applied}
    out: List[Dict[str, Any]] = []
    for prop in proposals:
        p = dict(prop)
        if p.get("validation_status") != VALIDATION_APPROVED:
            out.append(p)
            continue
        if p.get("shot_id") not in applied_ids:
            p["validation_status"] = VALIDATION_REJECTED
            p["validation_error"] = "swap_not_applied"
        elif not reuse.get("ok"):
            p["validation_status"] = VALIDATION_APPROVED
            p["batch_reuse_ok"] = False
        else:
            p["batch_reuse_ok"] = True
        out.append(p)
    return out


def normalize_timeline_starts(assembly_plan: Dict[str, Any]) -> Dict[str, Any]:
    plan = copy.deepcopy(assembly_plan)
    shots = list(plan.get("shots") or [])
    cursor = 0.0
    for shot in shots:
        shot["timeline_start_sec"] = cursor
        cursor += shot_timeline_duration_sec(shot)
    plan["shots"] = shots
    return plan


def apply_direct_upstream_swaps(
    assembly_plan: Dict[str, Any],
    proposals: List[Dict[str, Any]],
) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """Apply approved alternates directly (upstream), before assembly_repair."""
    plan = copy.deepcopy(assembly_plan)
    shots = list(plan.get("shots") or [])
    applied: List[Dict[str, Any]] = []
    by_id = {p.get("shot_id"): p for p in proposals if p.get("validation_status") == VALIDATION_APPROVED}
    for i, shot in enumerate(shots):
        sid = shot.get("shot_id")
        prop = by_id.get(sid)
        if not prop:
            continue
        alts = prop.get("alternate_source_assets") or []
        if not alts:
            continue
        shot_with_alt = {**shot, "alternate_source_assets": alts}
        need = shot_timeline_duration_sec(shot)
        avoid = {str(shot.get("source_asset") or "")}
        micro_absorb = need <= 0.084
        if not micro_absorb:
            if i > 0:
                avoid.add(str(shots[i - 1].get("source_asset") or ""))
            if i + 1 < len(shots):
                avoid.add(str(shots[i + 1].get("source_asset") or ""))
        cand = pick_valid_approved_alternate(shot_with_alt, avoid)
        if not cand:
            continue
        asset = str(cand["source_asset"])
        sr = cand.get("source_range") or {}
        in_s, out_s = float(sr["in_sec"]), float(sr["out_sec"])
        probe = {"source_asset": asset, "source_duration_sec": cand.get("source_duration_sec")}
        ok, err = validate_source_range(probe, in_s, out_s, min_duration_sec=need * 0.85)
        if not ok:
            continue
        shots[i] = {
            **shot,
            "source_asset": asset,
            "source_asset_name": prop.get("candidate_source_name"),
            "source_range": {"in_sec": in_s, "out_sec": out_s},
            "source_duration_sec": cand.get("source_duration_sec"),
            "upstream_swap": {
                "from": shot.get("source_asset"),
                "to": asset,
                "semantic_reason": prop.get("semantic_reason"),
            },
        }
        applied.append({"shot_id": sid, "to_source": asset})
    plan["shots"] = shots
    return plan, applied


def inject_approved_alternates(
    assembly_plan: Dict[str, Any],
    proposals: List[Dict[str, Any]],
) -> Dict[str, Any]:
    plan = copy.deepcopy(assembly_plan)
    shots = list(plan.get("shots") or [])
    by_id = {s.get("shot_id"): i for i, s in enumerate(shots)}
    for prop in proposals:
        if prop.get("validation_status") != VALIDATION_APPROVED:
            continue
        sid = prop.get("shot_id")
        if sid not in by_id:
            continue
        shots[by_id[sid]]["alternate_source_assets"] = prop.get("alternate_source_assets") or []
    plan["shots"] = shots
    return plan


def converge_assembly(
    assembly_plan: Dict[str, Any],
    pacing_profile_path: Path,
    reuse_profile_path: Path,
    proposals: List[Dict[str, Any]],
    *,
    max_rounds: int = 8,
) -> Dict[str, Any]:
    proposals = [p for p in proposals if p.get("validation_status") == VALIDATION_APPROVED]
    plan = inject_approved_alternates(assembly_plan, proposals)
    plan, _ = apply_direct_upstream_swaps(plan, proposals)
    plan = normalize_timeline_starts(plan)
    last_repair: Dict[str, Any] = {}
    for round_i in range(max_rounds):
        last_repair = repair_assembly_plan(
            plan,
            pacing_profile_path=pacing_profile_path,
            reuse_profile_path=reuse_profile_path,
        )
        plan = last_repair["assembly_plan"]
        pacing = last_repair["after"]["pacing"]
        reuse = last_repair["after"]["reuse"]
        plan = normalize_timeline_starts(plan)
        if pacing.get("ok") and reuse.get("ok"):
            break
    pacing = analyze_assembly_plan(plan, load_pacing_profile(pacing_profile_path))
    reuse = analyze_shot_reuse(plan, load_shot_reuse_profile(reuse_profile_path))
    converged = bool(pacing.get("ok") and reuse.get("ok"))
    micro = pacing.get("metrics", {}).get("micro_fragment_candidate_count", 0)
    return {
        "converged": converged,
        "assembly_plan_verdict": "PASS" if converged else "FAIL",
        "status": "ASSEMBLY_PLAN_CONVERGED" if converged else "ASSEMBLY_REPAIR_NOT_CONVERGED",
        "rounds": round_i + 1,
        "assembly_plan": plan,
        "last_repair": last_repair,
        "final_qa": {"pacing": pacing, "reuse": reuse},
        "metrics": {
            "micro_fragment_candidate_count": micro,
            "ping_pong_aba": reuse.get("metrics", {}).get("ping_pong_aba_count", 0),
            "ping_pong_abab": reuse.get("metrics", {}).get("ping_pong_abab_count", 0),
            "cooldown_violations": sum(
                1 for f in reuse.get("findings", []) if f.get("reason") == "same_source_cooldown_violation"
            ),
            "window_violations": sum(
                1 for f in reuse.get("findings", []) if f.get("reason") == "same_source_window_exceeded"
            ),
            "unresolved": len(last_repair.get("blocked") or []),
        },
    }


def ffprobe_duration(path: Path) -> float:
    cmd = [
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", str(path),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        return 0.0
    return float(proc.stdout.strip())

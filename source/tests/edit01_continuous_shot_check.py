#!/usr/bin/env python3
"""EDIT-01: keep one continuous clip, and never fill a real source gap."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB = ROOT / "payload" / "video-workflow" / "tools" / "lib"
sys.path.insert(0, str(LIB))

from assembly_repair import preserve_continuous_shots, repair_assembly_plan  # noqa: E402
from assembly_shot_utils import assembly_fps, joined_timing, resolve_clip_frames, source_join_decision  # noqa: E402
from pacing_qa import analyze_assembly_plan, load_pacing_profile  # noqa: E402
from resolve_materialization_frames import build_contiguous_clip_infos  # noqa: E402

PASS = 0
FAIL = 0
PROFILE = ROOT / "payload" / "video-workflow" / "runtime" / "informational-short-pacing-v1-profile.yaml"
N02 = ROOT.parent / "validation" / "n02-v1-timeline-assembly.json"


def check(cond: bool, name: str) -> None:
    global PASS, FAIL
    print(("[PASS] " if cond else "[FAIL] ") + name)
    if cond:
        PASS += 1
    else:
        FAIL += 1


def shot(sid: str, beat: str, start: float, dur: float, src_in: float, src_out: float, **extra):
    row = {
        "shot_id": sid,
        "beat_id": beat,
        "source_asset": "office",
        "timeline_start_sec": start,
        "timeline_duration_sec": dur,
        "source_range": {"in_sec": src_in, "out_sec": src_out},
        "source_fps": 24.0,
        "timeline_duration_frames": int(round(dur * 24)),
    }
    row.update(extra)
    return row


def main() -> int:
    plan = {
        "fps": 24,
        "shots": [
            shot("S1", "B1", 0, 2, 0, 2),
            shot("S2", "B2", 2, 2, 2, 4),
            shot("S3", "B3", 4, 2, 4, 6),
        ],
    }
    preserved = preserve_continuous_shots(plan)
    shots = preserved["assembly_plan"]["shots"]
    check(len(shots) == 1 and preserved["action_count"] == 2, "three abutting shots become one")
    only = shots[0]
    check(only["beat_ids"] == ["B1", "B2", "B3"] and only["beat_id"] == "B1", "beat ids survive on the surviving shot")
    check(abs(only["timeline_duration_sec"] - 6) < 1e-6, "timeline duration is the sum")
    check(only["source_range"] == {"in_sec": 0, "out_sec": 6}, "source in/out is the continuous span")
    check(only.get("absorbed_shot_ids") == ["S2", "S3"], "absorbed shot ids kept")

    infos, _parity, total = build_contiguous_clip_infos(shots, timeline_fps=24)
    check(len(infos) == 1 and total == only["timeline_duration_frames"], "L0 emits one clip for the preserved shot")
    check(infos[0]["record_frame"] == 0 and infos[0]["end_frame"] - infos[0]["start_frame"] == total, "L0 frame span matches the plan")

    gapped = {"fps": 24, "shots": [shot("G1", "B1", 0, 4, 0, 4), shot("G2", "B2", 4, 4, 7, 11)]}
    gap_result = preserve_continuous_shots(gapped)
    check(len(gap_result["assembly_plan"]["shots"]) == 2, "three-second source gap stays two shots")
    check(gap_result["assembly_plan"]["shots"][1]["source_range"]["in_sec"] == 7, "three-second gap is not filled")
    check(
        gap_result["blocked"][0]["decision"] == "source_gap"
        and gap_result["blocked"][0]["source_delta_frames"] > 1
        and gap_result["blocked"][0]["source_range_replanned"] is False,
        "three-second gap is a real source-frame hole and is not replanned",
    )

    zoomed = {
        "fps": 24,
        "shots": [
            shot("Z1", "B1", 0, 2, 0, 2, zoom=1.0),
            shot("Z2", "B2", 2, 2, 2, 4, zoom=1.25),
        ],
    }
    zoom_result = preserve_continuous_shots(zoomed)
    check(len(zoom_result["assembly_plan"]["shots"]) == 2 and zoom_result["blocked"][0]["decision"] == "transform_conflict", "different zoom stays split")

    cropped = {
        "fps": 24,
        "shots": [
            shot("C1", "B1", 0, 2, 0, 2, crop={"left": 0}),
            shot("C2", "B2", 2, 2, 2, 4, crop={"left": 40}),
        ],
    }
    crop_result = preserve_continuous_shots(cropped)
    check(crop_result["blocked"][0]["decision"] == "transform_conflict", "different crop stays split")

    sped = {
        "fps": 24,
        "shots": [
            shot("P1", "B1", 0, 2, 0, 2, playback_speed=1.0),
            shot("P2", "B2", 2, 2, 2, 4, playback_speed=1.5),
        ],
    }
    speed_result = preserve_continuous_shots(sped)
    check(speed_result["blocked"][0]["decision"] == "speed_conflict", "different speed stays split")

    jumped = {
        "fps": 24,
        "shots": [
            shot("J1", "B1", 0, 2, 0, 2),
            shot("J2", "B2", 2, 2, 2, 4, jump_cut=True, jump_cut_reason="intentional rhythm"),
        ],
    }
    jump_result = preserve_continuous_shots(jumped)
    check(len(jump_result["assembly_plan"]["shots"]) == 2 and jump_result["blocked"][0]["decision"] == "cut_intent", "marked jump cut stays split")

    REUSE = ROOT / "payload" / "video-workflow" / "runtime" / "informational-short-shot-reuse-v1-profile.yaml"
    micro = {
        "fps": 24,
        "shots": [
            shot("M0", "B0", 0, 5, 0, 5),
            shot("M1", "B1", 5, 0.042, 5, 5.042),
        ],
    }
    repaired = repair_assembly_plan(micro, pacing_profile_path=PROFILE, reuse_profile_path=REUSE)
    check(len(repaired["assembly_plan"]["shots"]) == 1, "abutting micro fragment still merges through the repair entry")

    office_plan = json.loads(N02.read_text(encoding="utf-8"))
    before = {
        row["shot_id"]: dict(row["source_range"])
        for row in office_plan["shots"]
        if row["shot_id"] in {"V1-08", "V1-09", "V1-10"}
    }
    office = preserve_continuous_shots(office_plan)
    after = {
        row["shot_id"]: dict(row["source_range"])
        for row in office["assembly_plan"]["shots"]
        if row["shot_id"] in {"V1-08", "V1-09", "V1-10"}
    }
    check(after == before and set(after) == {"V1-08", "V1-09", "V1-10"}, "N02 office trims stay three shots")
    gaps = sorted(round(float(item["gap_sec"]), 3) for item in office["blocked"] if item.get("prev_shot_id") in {"V1-08", "V1-09"})
    check(gaps == [0.213, 0.421], f"N02 office gaps recorded and not filled ({gaps})")
    office_blocks = [item for item in office["blocked"] if item.get("prev_shot_id") in {"V1-08", "V1-09"}]
    check(
        [item.get("decision") for item in office_blocks] == ["source_gap", "source_gap"]
        and all(item.get("source_delta_frames", 0) > 1 for item in office_blocks)
        and all(item.get("source_range_replanned") is False for item in office_blocks),
        f"N02 office stays a source-frame gap ({[item.get('source_delta_frames') for item in office_blocks]})",
    )

    office_only = {
        "fps": assembly_fps(office_plan),
        "shots": [row for row in office_plan["shots"] if row["shot_id"] in {"V1-08", "V1-09", "V1-10"}],
    }
    pacing = analyze_assembly_plan(office_only, load_pacing_profile(PROFILE))
    span = next(item for item in pacing["findings"] if item.get("reason") == "source_gap_blocks_continuous_merge")
    check(
        "clip.assemble" not in span["repair_route"]
        and span["repair_route"] == ["replan_continuous_source_range"]
        and span["repair_route_role"] == "suggestion"
        and span["repair_route_executed"] is False
        and span["source_range_replanned"] is False,
        "office replan route is only a suggestion",
    )

    before_infos, _parity, before_total = build_contiguous_clip_infos(plan["shots"], timeline_fps=24)
    check(
        infos[0]["start_frame"] == before_infos[0]["start_frame"]
        and infos[0]["end_frame"] == before_infos[-1]["end_frame"]
        and infos[0]["record_frame"] == before_infos[0]["record_frame"]
        and total == before_total
        and before_infos[1]["record_frame"] == before_infos[0]["record_frame"] + before_infos[0]["end_frame"] - before_infos[0]["start_frame"],
        "merged clip_info uses the same source frames and record position as the three clips",
    )

    timeline_gap = {
        "fps": 24,
        "shots": [shot("TG1", "B1", 0, 2, 0, 2), shot("TG2", "B2", 5, 2, 2, 4)],
    }
    timeline_gap_result = preserve_continuous_shots(timeline_gap)
    check(
        len(timeline_gap_result["assembly_plan"]["shots"]) == 2
        and timeline_gap_result["blocked"][0]["decision"] == "timeline_gap"
        and timeline_gap_result["blocked"][0]["timeline_delta_frames"] > 0,
        "timeline 0-2 then 5-7 stays split",
    )

    timeline_overlap = {
        "fps": 24,
        "shots": [shot("TO1", "B1", 0, 2, 0, 2), shot("TO2", "B2", 1, 2, 2, 4)],
    }
    timeline_overlap_result = preserve_continuous_shots(timeline_overlap)
    check(
        len(timeline_overlap_result["assembly_plan"]["shots"]) == 2
        and timeline_overlap_result["blocked"][0]["decision"] == "timeline_overlap"
        and timeline_overlap_result["blocked"][0]["timeline_delta_frames"] < 0,
        "timeline 0-2 overlapping 1-3 stays split",
    )

    one_sided = {
        "fps": 24,
        "shots": [
            shot("TS1", "B1", 0, 2, 0, 2),
            {k: v for k, v in shot("TS2", "B2", 2, 2, 2, 4).items() if k != "timeline_start_sec"},
        ],
    }
    one_sided_result = preserve_continuous_shots(one_sided)
    check(one_sided_result["blocked"][0]["decision"] == "timeline_position_unproven", "a missing explicit timeline position is not invented")

    def framed(sid, beat, start_frame, dur_frames, src_in, src_out_delta, source_fps, timeline_fps):
        return {
            "shot_id": sid,
            "beat_id": beat,
            "source_asset": "office",
            "source_fps": source_fps,
            "timeline_start_frame": start_frame,
            "timeline_end_frame": start_frame + dur_frames,
            "timeline_duration_frames": dur_frames,
            "timeline_duration_sec": dur_frames / timeline_fps,
            "source_in_frame": src_in,
            "source_range": {
                "in_sec": src_in / source_fps,
                "out_sec": (src_in + src_out_delta) / source_fps,
            },
        }

    def frame_case(fps, second_in, dur=48):
        return {
            "fps": fps,
            "shots": [
                framed("F1", "B1", 0, dur, 0, dur, fps, fps),
                framed("F2", "B2", dur, dur, second_in, dur, fps, fps),
            ],
        }

    strict = preserve_continuous_shots(frame_case(24, 48))
    strict_shot = strict["assembly_plan"]["shots"][0]
    check(len(strict["assembly_plan"]["shots"]) == 1 and strict_shot["continuous_shot_preservation"]["source_delta_frames"] == 0, "strict frame abutment merges")
    check(strict_shot["beat_ids"] == ["B1", "B2"], "strict frame join keeps both beats")
    strict_before, _p, strict_before_total = build_contiguous_clip_infos(frame_case(24, 48)["shots"], timeline_fps=24)
    strict_after, _p, strict_after_total = build_contiguous_clip_infos(strict["assembly_plan"]["shots"], timeline_fps=24)
    check(
        strict_after[0]["start_frame"] == strict_before[0]["start_frame"]
        and strict_after[0]["end_frame"] == strict_before[1]["end_frame"]
        and strict_after[0]["record_frame"] == strict_before[0]["record_frame"]
        and strict_after_total == strict_before_total,
        "strict join keeps Resolve clip_info frames",
    )

    plus_one = preserve_continuous_shots(frame_case(24, 49))
    check(
        len(plus_one["assembly_plan"]["shots"]) == 2
        and plus_one["blocked"][0]["decision"] == "source_gap"
        and plus_one["blocked"][0]["source_delta_frames"] == 1
        and plus_one["assembly_plan"]["shots"][1]["source_in_frame"] == 49,
        "positive one source frame stays split",
    )
    plus_one_repair = repair_assembly_plan(
        frame_case(24, 49),
        pacing_profile_path=PROFILE,
        reuse_profile_path=ROOT / "payload" / "video-workflow" / "runtime" / "informational-short-shot-reuse-v1-profile.yaml",
    )
    check(len(plus_one_repair["assembly_plan"]["shots"]) == 2, "positive one source frame is not absorbed as a micro fragment")

    minus_one = preserve_continuous_shots(frame_case(24, 47))
    check(
        len(minus_one["assembly_plan"]["shots"]) == 2
        and minus_one["blocked"][0]["decision"] == "source_overlap"
        and minus_one["blocked"][0]["source_delta_frames"] == -1,
        "negative one source frame stays split",
    )

    wider = preserve_continuous_shots(frame_case(24, 53))
    check(
        wider["blocked"][0]["decision"] == "source_gap" and wider["blocked"][0]["source_delta_frames"] > 1,
        "source gap larger than one frame stays split",
    )

    at_30 = preserve_continuous_shots(frame_case(30, 48))
    check(len(at_30["assembly_plan"]["shots"]) == 1, "strict abutment also merges at 30 fps")

    rate_mismatch = {
        "fps": 24,
        "shots": [
            framed("R1", "B1", 0, 1, 0, 2, 25, 24),
            framed("R2", "B2", 1, 1, 2, 2, 25, 24),
        ],
    }
    rate_decision = source_join_decision(rate_mismatch["shots"][0], rate_mismatch["shots"][1], 24)
    rate_before, _p, _t = build_contiguous_clip_infos(rate_mismatch["shots"], timeline_fps=24)
    rate_merged_clip = resolve_clip_frames(joined_timing(rate_mismatch["shots"][0], rate_mismatch["shots"][1]), 24)
    check(rate_before[1]["start_frame"] == rate_before[0]["end_frame"], "25 fps pair is source-frame adjacent before the join")
    check(
        rate_decision["decision"] == "frame_inconsistent"
        and rate_merged_clip["end_frame"] != rate_before[1]["end_frame"],
        "25 fps timeline rounding does not merge when the joined clip_info would change frames",
    )
    check(len(preserve_continuous_shots(rate_mismatch)["assembly_plan"]["shots"]) == 2, "inconsistent frame-rate join stays two shots")

    fps_conflict = {
        "fps": 24,
        "shots": [
            {**framed("Q1", "B1", 0, 48, 0, 48, 24, 24), "playback_speed": 1.0},
            {**framed("Q2", "B2", 48, 48, 48, 48, 30, 24), "playback_speed": 1.0},
        ],
    }
    check(preserve_continuous_shots(fps_conflict)["blocked"][0]["decision"] == "source_fps_conflict", "different source frame rates stay split")

    exempt = {
        "fps": 24,
        "shots": [
            shot("E1", "B1", 0, 2, 0, 2),
            shot("E2", "B2", 2, 2, 2, 4, pacing_exempt=True),
        ],
    }
    check(preserve_continuous_shots(exempt)["blocked"][0]["decision"] == "editorial_exempt", "pacing exemption still blocks a merge")

    dissolved = {
        "fps": 24,
        "shots": [
            shot("D1", "B1", 0, 2, 0, 2),
            shot("D2", "B2", 2, 2, 2, 4, transition_in="cross_dissolve"),
        ],
    }
    check(preserve_continuous_shots(dissolved)["blocked"][0]["decision"] == "effect_or_transition", "a real transition stays split")

    long_take = {"fps": 24, "shots": [shot("L1", "B1", 0, 12, 0, 12, timeline_duration_frames=288)]}
    long_pacing = analyze_assembly_plan(long_take, load_pacing_profile(PROFILE))
    long_finding = next(item for item in long_pacing["findings"] if item.get("reason") == "long_take_hold")
    check(long_pacing["ok"] is True and long_pacing["verdict"] == "PASS" and long_finding["blocking"] is False, "a legal long take passes and keeps a non-blocking note")

    mixed = {
        "fps": 24,
        "shots": [
            shot("L1", "B1", 0, 12, 0, 12),
            shot("M1", "B2", 12, 0.042, 0, 0.042, source_asset="other"),
        ],
    }
    mixed_pacing = analyze_assembly_plan(mixed, load_pacing_profile(PROFILE))
    check(mixed_pacing["ok"] is False and mixed_pacing["verdict"] == "PACING_REPAIR_CANDIDATE", "a long take does not hide another repair")

    warning = {"fps": 24, "shots": [shot("W1", "B1", 0, 7, 0, 7)]}
    warning_pacing = analyze_assembly_plan(warning, load_pacing_profile(PROFILE))
    check(warning_pacing["ok"] is False and warning_pacing["verdict"] == "PACING_WARNING", "a 7 second warning still blocks")

    reuse_profile = ROOT / "payload" / "video-workflow" / "runtime" / "informational-short-shot-reuse-v1-profile.yaml"
    loop = ROOT / "payload" / "video-workflow" / "tools" / "assembly-qa-repair-loop.py"
    preview_path = ROOT / "tests" / ".tmp-edit01-preview.json"
    preview_path.write_text(json.dumps(plan), encoding="utf-8")
    preview_run = subprocess.run(
        [sys.executable, str(loop), "--assembly-json", str(preview_path), "--pacing-profile", str(PROFILE), "--reuse-profile", str(reuse_profile)],
        capture_output=True,
        text=True,
        check=False,
    )
    preview = json.loads(preview_run.stdout)
    check(preview_run.returncode == 2, "preview with merge candidates does not exit as a pass")
    check(
        preview["repair_applied"] is False
        and preview["normalization_applied"] is False
        and preview["normalization_complete"] is False
        and preview["status"] == "CONTINUOUS_SHOT_NORMALIZATION_PENDING"
        and preview["ok"] is False
        and len(preview["assembly_plan"]["shots"]) == 3,
        "preview does not report normalization as complete",
    )
    apply_run = subprocess.run(
        [sys.executable, str(loop), "--assembly-json", str(preview_path), "--pacing-profile", str(PROFILE), "--reuse-profile", str(reuse_profile), "--apply-repair"],
        capture_output=True,
        text=True,
        check=False,
    )
    applied = json.loads(apply_run.stdout)
    check(
        applied["repair_applied"] is True
        and applied["normalization_applied"] is True
        and len(applied["assembly_plan"]["shots"]) == 1
        and applied["source_range_replanned"] is False,
        "apply-repair is what actually joins the shots",
    )
    skill = (ROOT / "payload" / ".cursor" / "skills" / "video-production" / "SKILL.md").read_text(encoding="utf-8")
    check("assembly-qa-repair-loop.py --apply-repair" in skill, "production entry tells the agent to run --apply-repair")
    preview_path.unlink(missing_ok=True)

    def run_repair(body):
        return repair_assembly_plan(body, pacing_profile_path=PROFILE, reuse_profile_path=REUSE)

    def refused(body, name):
        result = run_repair(body)
        kept = result["assembly_plan"]["shots"]
        original = body["shots"]
        check(
            len(kept) == 2
            and result["ok"] is False
            and result["status"] != "ASSEMBLY_REPAIR_CONVERGED"
            and not any(item.get("shot_id") == "M" and item.get("repair") for item in result["actions"])
            and kept[1].get("source_in_frame") == original[1].get("source_in_frame")
            and kept[0].get("source_range") == original[0].get("source_range")
            and kept[1].get("source_range") == original[1].get("source_range"),
            name,
        )

    legal = {
        "fps": 24,
        "shots": [
            framed("P", "B1", 0, 48, 0, 48, 24, 24),
            framed("M", "B2", 48, 1, 48, 1, 24, 24),
        ],
    }
    legal_result = run_repair(legal)
    legal_shot = legal_result["assembly_plan"]["shots"][0]
    before_infos, _parity, before_total = build_contiguous_clip_infos(legal["shots"], timeline_fps=24)
    after_infos, _parity, after_total = build_contiguous_clip_infos(legal_result["assembly_plan"]["shots"], timeline_fps=24)
    check(
        len(legal_result["assembly_plan"]["shots"]) == 1
        and legal_shot["timeline_duration_frames"] == 49
        and abs(legal_shot["timeline_duration_sec"] - (49 / 24)) < 1e-9,
        "repair entry joins a legal 48-frame shot and a 1-frame tail into 49 frames",
    )
    check(legal_shot["beat_ids"] == ["B1", "B2"] and legal_shot["beat_id"] == "B1", "repair entry keeps both beat ids")
    check(legal_shot.get("absorbed_shot_ids") == ["M"], "repair entry keeps the absorbed shot id")
    check(
        after_infos[0]["start_frame"] == before_infos[0]["start_frame"]
        and after_infos[0]["end_frame"] == before_infos[1]["end_frame"]
        and after_total == before_total == 49,
        "repair entry keeps Resolve clip_info source frames and total frame count",
    )

    refused(
        {"fps": 24, "shots": [framed("P", "B1", 0, 48, 0, 48, 24, 24), framed("M", "B2", 50, 1, 48, 1, 24, 24)]},
        "repair entry leaves a timeline gap split",
    )
    refused(
        {"fps": 24, "shots": [framed("P", "B1", 0, 48, 0, 48, 24, 24), framed("M", "B2", 47, 1, 48, 1, 24, 24)]},
        "repair entry leaves a timeline overlap split",
    )
    refused(
        {"fps": 24, "shots": [framed("P", "B1", 0, 48, 0, 48, 24, 24), framed("M", "B2", 48, 1, 49, 1, 24, 24)]},
        "repair entry leaves a positive one-frame source gap split",
    )
    refused(
        {"fps": 24, "shots": [framed("P", "B1", 0, 48, 0, 48, 24, 24), framed("M", "B2", 48, 1, 47, 1, 24, 24)]},
        "repair entry leaves a negative one-frame source overlap split",
    )
    zoom_micro = {
        "fps": 24,
        "shots": [
            {**framed("P", "B1", 0, 48, 0, 48, 24, 24), "zoom": 1.0},
            {**framed("M", "B2", 48, 1, 48, 1, 24, 24), "zoom": 1.25},
        ],
    }
    crop_micro = {
        "fps": 24,
        "shots": [
            {**framed("P", "B1", 0, 48, 0, 48, 24, 24), "crop": {"left": 0}},
            {**framed("M", "B2", 48, 1, 48, 1, 24, 24), "crop": {"left": 40}},
        ],
    }
    speed_micro = {
        "fps": 24,
        "shots": [
            {**framed("P", "B1", 0, 48, 0, 48, 24, 24), "playback_speed": 1.0},
            {**framed("M", "B2", 48, 1, 48, 1, 24, 24), "playback_speed": 1.5},
        ],
    }
    jump_micro = {
        "fps": 24,
        "shots": [
            framed("P", "B1", 0, 48, 0, 48, 24, 24),
            {**framed("M", "B2", 48, 1, 48, 1, 24, 24), "jump_cut": True, "jump_cut_reason": "intentional rhythm"},
        ],
    }
    dissolve_micro = {
        "fps": 24,
        "shots": [
            framed("P", "B1", 0, 48, 0, 48, 24, 24),
            {**framed("M", "B2", 48, 1, 48, 1, 24, 24), "transition_in": "cross_dissolve"},
        ],
    }
    refused(zoom_micro, "repair entry leaves a zoom conflict split")
    refused(crop_micro, "repair entry leaves a crop conflict split")
    refused(speed_micro, "repair entry leaves a speed conflict split")
    refused(jump_micro, "repair entry leaves a marked jump cut split")
    refused(dissolve_micro, "repair entry leaves a transition split")

    print(f"Results: {PASS} passed, {FAIL} failed")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

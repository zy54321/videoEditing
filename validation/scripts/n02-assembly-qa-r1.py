#!/usr/bin/env python3
"""N02 V1 assembly re-evaluation (R1 logical spans + micro-fragments)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LIB = ROOT / "source" / "payload" / "video-workflow" / "tools" / "lib"
sys.path.insert(0, str(LIB))

from assembly_repair import repair_assembly_plan  # noqa: E402
from assembly_shot_utils import assembly_fps, build_timed_shots, is_micro_fragment  # noqa: E402
from pacing_qa import analyze_assembly_plan, load_pacing_profile  # noqa: E402
from shot_reuse_qa import analyze_shot_reuse, load_shot_reuse_profile  # noqa: E402


def main() -> int:
    asm_path = ROOT / "validation" / "n02-v1-timeline-assembly.json"
    pacing_prof = ROOT / "source" / "payload" / "video-workflow" / "runtime" / "informational-short-pacing-v1-profile.yaml"
    reuse_prof = ROOT / "source" / "payload" / "video-workflow" / "runtime" / "informational-short-shot-reuse-v1-profile.yaml"
    assembly = json.loads(asm_path.read_text(encoding="utf-8-sig"))
    pacing_profile = load_pacing_profile(pacing_prof)
    reuse_profile = load_shot_reuse_profile(reuse_prof)
    fps = assembly_fps(assembly)

    micro_ids = []
    for shot in assembly.get("shots") or []:
        if is_micro_fragment(shot, fps, pacing_profile.micro_fragment_max_frames, pacing_profile.micro_fragment_max_sec):
            micro_ids.append(shot.get("shot_id"))

    pacing = analyze_assembly_plan(assembly, pacing_profile)
    reuse = analyze_shot_reuse(assembly, reuse_profile)
    repair = repair_assembly_plan(
        assembly,
        pacing_profile_path=pacing_prof,
        reuse_profile_path=reuse_prof,
    )

    safe_actions = repair.get("actions") or []
    blocked = repair.get("blocked") or []

    report = {
        "assembly": asm_path.name,
        "fps": fps,
        "micro_fragment_shot_ids": micro_ids,
        "micro_fragment_count": len(micro_ids),
        "logical_source_span_count": reuse.get("metrics", {}).get("logical_source_span_count"),
        "cooldown_violations": [f for f in reuse.get("findings", []) if f.get("reason") == "same_source_cooldown_violation"],
        "window_violations": [f for f in reuse.get("findings", []) if f.get("reason") == "same_source_window_exceeded"],
        "ping_pong": reuse.get("metrics", {}),
        "pacing_verdict": pacing.get("verdict"),
        "reuse_verdict": reuse.get("verdict"),
        "repair_status": repair.get("status"),
        "repair_converged": repair.get("converged"),
        "safe_repair_action_count": len(safe_actions),
        "blocked_repair_count": len(blocked),
        "after_reuse_verdict": repair.get("after", {}).get("reuse", {}).get("verdict"),
        "after_pacing_ok": repair.get("after", {}).get("pacing", {}).get("ok"),
    }
    out = ROOT / "validation" / "n02-assembly-qa-r1-metrics.json"
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

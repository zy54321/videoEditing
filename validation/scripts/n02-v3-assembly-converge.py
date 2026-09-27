#!/usr/bin/env python3
"""N02 V3 upstream reselection + assembly converge (plan only)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LIB = ROOT / "source" / "payload" / "video-workflow" / "tools" / "lib"
sys.path.insert(0, str(LIB))

from assembly_plan_frames import enrich_plan_frames  # noqa: E402
from upstream_reselection import converge_assembly, propose_n02_reselection  # noqa: E402


def main() -> int:
    asm_path = ROOT / "validation" / "n02-v1-timeline-assembly.json"
    pacing_prof = ROOT / "source" / "payload" / "video-workflow" / "runtime" / "informational-short-pacing-v1-profile.yaml"
    reuse_prof = ROOT / "source" / "payload" / "video-workflow" / "runtime" / "informational-short-shot-reuse-v1-profile.yaml"
    assembly = json.loads(asm_path.read_text(encoding="utf-8-sig"))
    proposals = propose_n02_reselection(assembly)
    result = converge_assembly(assembly, pacing_prof, reuse_prof, proposals)
    reselection_out = {
        "production": "N02",
        "version": "0.1.3-dev",
        "blocked_beats_r1": ["V1-03", "V1-04", "V1-09", "V1-16", "V1-20", "V1-21", "V1-23"],
        "proposals": proposals,
        "direct_swaps_applied": True,
        "converged": result["converged"],
        "metrics": result["metrics"],
        "status": result["status"],
    }
    (ROOT / "validation" / "n02-v3-reselection-plan.json").write_text(
        json.dumps(reselection_out, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    final_plan = enrich_plan_frames(result["assembly_plan"], timeline_fps=24.0)
    final_plan["assembly_plan_verdict"] = result["assembly_plan_verdict"]
    final_plan["ASSEMBLY_PLAN_CONVERGED"] = "YES" if result["converged"] else "NO"
    (ROOT / "validation" / "n02-v3-final-assembly-plan.json").write_text(
        json.dumps(final_plan, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(json.dumps({"converged": result["converged"], "metrics": result["metrics"]}, indent=2))
    return 0 if result["converged"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

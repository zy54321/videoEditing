#!/usr/bin/env python3
"""Pacing + shot reuse QA → assembly repair → re-QA (production closure)."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_TOOLS = Path(__file__).resolve().parent
_LIB = _TOOLS / "lib"
if str(_LIB) not in sys.path:
    sys.path.insert(0, str(_LIB))

from assembly_repair import repair_assembly_plan  # noqa: E402
from pacing_qa import analyze_assembly_plan, load_pacing_profile  # noqa: E402
from shot_reuse_qa import analyze_shot_reuse, load_shot_reuse_profile  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--assembly-json", type=Path, required=True)
    ap.add_argument("--pacing-profile", type=Path, required=True)
    ap.add_argument("--reuse-profile", type=Path, required=True)
    ap.add_argument("--apply-repair", action="store_true")
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()

    assembly = json.loads(args.assembly_json.read_text(encoding="utf-8-sig"))
    pacing_profile = load_pacing_profile(args.pacing_profile)
    reuse_profile = load_shot_reuse_profile(args.reuse_profile)

    pacing_before = analyze_assembly_plan(assembly, pacing_profile)
    reuse_before = analyze_shot_reuse(assembly, reuse_profile)

    result: dict = {
        "before_qa": {"pacing": pacing_before, "reuse": reuse_before},
        "repair_applied": False,
    }

    needs_repair = (
        pacing_before["verdict"] == "PACING_REPAIR_CANDIDATE"
        or reuse_before["verdict"] in ("REPAIR_CANDIDATE", "STRONG_REPAIR_CANDIDATE")
    )

    if args.apply_repair and needs_repair:
        repaired = repair_assembly_plan(
            assembly,
            pacing_profile_path=args.pacing_profile,
            reuse_profile_path=args.reuse_profile,
        )
        result["repair_applied"] = True
        result["repair"] = repaired
        result["after_qa"] = repaired["after"]
        result["assembly_plan"] = repaired["assembly_plan"]
        result["ok"] = repaired["ok"]
    else:
        result["after_qa"] = result["before_qa"]
        result["ok"] = pacing_before["ok"] and reuse_before["ok"]

    out = json.dumps(result, indent=2, ensure_ascii=False)
    if args.out:
        args.out.write_text(out, encoding="utf-8")
    print(out)
    return 0 if result["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())

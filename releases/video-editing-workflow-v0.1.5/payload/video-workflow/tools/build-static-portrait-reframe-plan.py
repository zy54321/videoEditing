#!/usr/bin/env python3
"""Build static portrait reframe plan from timeline probe_timeline_structure JSON."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_LIB = Path(__file__).resolve().parent / "lib"
if str(_LIB) not in sys.path:
    sys.path.insert(0, str(_LIB))

from static_portrait_reframe import build_plan_from_timeline_probe  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--probe", type=Path, required=True, help="probe_timeline_structure JSON")
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--max-safe-zoom", type=float, default=3.5)
    args = ap.parse_args()

    probe = json.loads(args.probe.read_text(encoding="utf-8-sig"))
    plan = build_plan_from_timeline_probe(probe, max_safe_zoom=args.max_safe_zoom)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": plan["status"], "shot_count": plan["shot_count"], "errors": plan["errors"]}, ensure_ascii=False))
    return 0 if plan["status"] == "OK" else 2


if __name__ == "__main__":
    raise SystemExit(main())

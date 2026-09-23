#!/usr/bin/env python3
"""Extract leaf materialized cues from A1.1 plan JSON."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("plan")
    ap.add_argument("--out")
    args = ap.parse_args()
    plan = json.loads(Path(args.plan).read_text(encoding="utf-8-sig"))
    cues: list[dict] = []
    for cue in plan.get("materialized_cues") or []:
        if isinstance(cue, dict) and cue.get("styled_text") and cue.get("cue_id"):
            cues.append(cue)
    result = {
        "materialization_status": plan.get("materialization_status"),
        "cue_count": len(cues),
        "materialized_cues": cues,
    }
    text = json.dumps(result, ensure_ascii=False, indent=2)
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

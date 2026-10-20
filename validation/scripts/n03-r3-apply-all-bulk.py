#!/usr/bin/env python3
"""Apply static_portrait_reframe plan bulk_ops on current Resolve timeline (local API)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
APPLY_CLI = ROOT / "source/payload/video-workflow/tools/apply-static-portrait-reframe-bulk.py"
EVIDENCE = Path(r"E:\03_Media\02_Video\Davinci\Astra\2026-10-12\N03\evidence\r3-reframe-closure")
PLAN = EVIDENCE / "static_portrait_reframe_plan_v10.json"


def main() -> int:
    import subprocess

    if not APPLY_CLI.is_file():
        print("MISSING_PAYLOAD_APPLY_CLI", APPLY_CLI)
        return 2
    p = subprocess.run(
        [
            sys.executable,
            str(APPLY_CLI),
            "--plan",
            str(PLAN),
            "--expected-timeline",
            "N03_V10_Assembly-merged",
            "--result-out",
            str(EVIDENCE / "bulk_apply_result.json"),
        ],
        check=False,
    )
    return p.returncode


if __name__ == "__main__":
    raise SystemExit(main())

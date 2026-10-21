#!/usr/bin/env python3
"""CLI: clean master + external ASS → libass burn-in MP4 (verified encode params)."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_LIB = Path(__file__).resolve().parent / "lib"
if str(_LIB) not in sys.path:
    sys.path.insert(0, str(_LIB))

from external_ass_burnin import burnin_external_ass  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description="FFmpeg libass subtitle burn-in")
    ap.add_argument("--clean-master", type=Path, required=True)
    ap.add_argument("--ass", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    try:
        result = burnin_external_ass(
            clean_master=args.clean_master,
            ass_path=args.ass,
            output_path=args.out,
            dry_run=args.dry_run,
        )
    except RuntimeError as e:
        print(str(e), file=sys.stderr)
        return 2

    print(json.dumps(result, ensure_ascii=False))
    return 0 if result.get("ok") else 2


if __name__ == "__main__":
    raise SystemExit(main())

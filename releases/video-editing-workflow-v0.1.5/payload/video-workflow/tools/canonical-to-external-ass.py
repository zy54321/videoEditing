#!/usr/bin/env python3
"""CLI: R1 canonical-subtitle-cues.json → external ASS (versioned N02Prod baseline)."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_LIB = Path(__file__).resolve().parent / "lib"
if str(_LIB) not in sys.path:
    sys.path.insert(0, str(_LIB))

from canonical_to_external_ass import write_external_ass  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description="Materialize external ASS from canonical cues")
    ap.add_argument("--canonical", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True, help="Output .ass path")
    ap.add_argument("--baseline", type=Path, help="Override style baseline JSON")
    ap.add_argument("--manifest", type=Path, help="Optional materialization manifest JSON")
    args = ap.parse_args()

    try:
        result = write_external_ass(
            canonical_path=args.canonical,
            ass_out=args.out,
            baseline_path=args.baseline,
            manifest_out=args.manifest,
        )
    except RuntimeError as e:
        print(str(e), file=sys.stderr)
        return 2

    if result.text_match != "PASS":
        print("CANONICAL_ASS_TEXT_MATCH: FAIL", file=sys.stderr)
        return 2

    print(
        json.dumps(
            {
                "ass_path": str(result.ass_path),
                "cue_count": result.cue_count,
                "style_name": result.style_name,
                "ass_sha256": result.ass_sha256,
                "CANONICAL_ASS_TEXT_MATCH": result.text_match,
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

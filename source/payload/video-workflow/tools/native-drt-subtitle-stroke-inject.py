#!/usr/bin/env python3
"""Inject verified native subtitle stroke template into a DRT (style only)."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

LIB = Path(__file__).resolve().parent / "lib"
sys.path.insert(0, str(LIB))

from native_subtitle_stroke_template import (  # noqa: E402
    inject_template_into_drt,
    load_template_blob_from_manifest,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Inject EffectFiltersBA stroke template into DRT")
    parser.add_argument("input_drt", type=Path)
    parser.add_argument("output_drt", type=Path)
    parser.add_argument("--template-dir", type=Path)
    args = parser.parse_args()

    payload = Path(__file__).resolve().parents[1]
    template_dir = args.template_dir or (payload / "runtime" / "native-drt-subtitle-stroke-template")
    blob = load_template_blob_from_manifest(template_dir.resolve())
    result = inject_template_into_drt(args.input_drt.resolve(), args.output_drt.resolve(), blob)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

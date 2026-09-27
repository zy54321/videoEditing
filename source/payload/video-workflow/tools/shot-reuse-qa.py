#!/usr/bin/env python3
"""CLI: shot reuse / ping-pong QA on assembly JSON."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_TOOLS = Path(__file__).resolve().parent
_LIB = _TOOLS / "lib"
if str(_LIB) not in sys.path:
    sys.path.insert(0, str(_LIB))

from shot_reuse_qa import analyze_shot_reuse, load_shot_reuse_profile  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--assembly-json", type=Path, required=True)
    ap.add_argument("--profile", type=Path, required=True)
    args = ap.parse_args()
    assembly = json.loads(args.assembly_json.read_text(encoding="utf-8-sig"))
    profile = load_shot_reuse_profile(args.profile)
    result = analyze_shot_reuse(assembly, profile)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())

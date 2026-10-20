#!/usr/bin/env python3
"""R1 — Frozen Script + ASR timing → Canonical Subtitle Cue list (renderer-neutral)."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_TOOLS = Path(__file__).resolve().parent
_LIB = _TOOLS / "lib"
if str(_LIB) not in sys.path:
    sys.path.insert(0, str(_LIB))

from canonical_subtitle_cue import run_pipeline_from_paths  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description="Build Canonical Subtitle Cue list (R1)")
    ap.add_argument("--brief", type=Path, help="Production Brief YAML (content.authority + script path)")
    ap.add_argument("--script", type=Path, help="Frozen script file (when not using --brief)")
    ap.add_argument("--asr", type=Path, required=True, help="ASR timing evidence JSON")
    ap.add_argument("--out", type=Path, required=True, help="Output canonical-subtitle-cues.json")
    args = ap.parse_args()

    doc = run_pipeline_from_paths(
        brief_path=args.brief,
        script_path=args.script,
        asr_path=args.asr,
        tools_dir=_TOOLS,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    status = doc.get("meta", {}).get("status", "UNKNOWN")
    print(status)
    return 0 if status == "OK" else 2


if __name__ == "__main__":
    raise SystemExit(main())

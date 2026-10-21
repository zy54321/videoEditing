#!/usr/bin/env python3
"""Pin Canonical cue bounds to the frozen-script word alignment."""
from __future__ import annotations

import json
import sys
from pathlib import Path

_LIB = Path(__file__).resolve().parent / "lib"
if str(_LIB) not in sys.path:
    sys.path.insert(0, str(_LIB))

from frozen_script_word_align import apply_alignment_bounds  # noqa: E402


def main() -> int:
    canonical_path = Path(sys.argv[sys.argv.index("--canonical") + 1])
    alignment_path = Path(sys.argv[sys.argv.index("--alignment") + 1])
    if not alignment_path.is_file():
        print(json.dumps({"status": "SKIPPED", "reason": "ALIGNMENT_FILE_MISSING"}))
        return 0
    canonical = json.loads(canonical_path.read_text(encoding="utf-8-sig"))
    alignment = json.loads(alignment_path.read_text(encoding="utf-8-sig"))
    if alignment.get("status") != "OK":
        print(json.dumps({"status": "SKIPPED", "reason": alignment.get("status")}))
        return 0
    errors = apply_alignment_bounds(canonical, alignment)
    if errors:
        print(json.dumps({"status": "BLOCKED", "errors": errors}, ensure_ascii=False))
        return 4
    canonical_path.write_text(json.dumps(canonical, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "APPLIED", "cue_count": len(canonical.get("cues") or [])}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

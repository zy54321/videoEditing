#!/usr/bin/env python3
"""CLI wrapper — SUBTITLE_CANONICAL_AUTHORITY_GATE."""
from __future__ import annotations

import sys
from pathlib import Path

_LIB = Path(__file__).resolve().parent / "lib"
if str(_LIB) not in sys.path:
    sys.path.insert(0, str(_LIB))

from validate_canonical_subtitle_authority_gate import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())

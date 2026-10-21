#!/usr/bin/env python3
"""CLI: acquire word-level ASR timing evidence for Canonical alignment."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_LIB = Path(__file__).resolve().parent / "lib"
if str(_LIB) not in sys.path:
    sys.path.insert(0, str(_LIB))

from subtitle_timing_acquire import acquire_subtitle_timing  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description="Acquire subtitle timing evidence")
    ap.add_argument("--evidence", type=Path, required=True)
    ap.add_argument("--script", type=Path)
    ap.add_argument("--voice-audio", type=Path)
    ap.add_argument("--resolve-transcription", type=Path)
    ap.add_argument("--binding", type=Path)
    ap.add_argument("--report", type=Path)
    ap.add_argument("--fps", type=float, default=24.0)
    args = ap.parse_args()
    result = acquire_subtitle_timing(
        evidence_path=args.evidence,
        script_path=args.script,
        voice_audio_path=args.voice_audio,
        resolve_transcription_path=args.resolve_transcription,
        binding_path=args.binding,
        report_path=args.report,
        fps=args.fps,
        allow_project_switch=True,
    )
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result.get("status") in {"ACQUIRED", "SKIPPED_EXISTING"} else 4


if __name__ == "__main__":
    raise SystemExit(main())

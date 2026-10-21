#!/usr/bin/env python3
"""U1 — Run voice subtitle text review and write production artifacts."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_TOOLS = Path(__file__).resolve().parent
_LIB = _TOOLS / "lib"
if str(_LIB) not in sys.path:
    sys.path.insert(0, str(_LIB))

from voice_subtitle_review import (  # noqa: E402
    ReviewStatus,
    draft_reviewed_text_from_primary,
    run_voice_subtitle_review,
    write_blocked_review_result,
    write_review_artifacts,
)
from asr_timing_evidence import load_asr_timing_evidence  # noqa: E402
from voice_subtitle_paths import asr_primary_path  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workspace", type=Path, required=True)
    ap.add_argument("--brief", type=Path, required=True)
    ap.add_argument("--voice-audio", type=Path, default=None)
    ap.add_argument("--json", action="store_true")
    ap.add_argument(
        "--force-regenerate",
        action="store_true",
        help="Invalidate Owner approval and overwrite reviewed text from ASR draft",
    )
    args = ap.parse_args()

    ws = args.workspace.resolve()
    brief = args.brief.resolve()
    result = run_voice_subtitle_review(
        workspace_root=ws,
        brief_path=brief,
        voice_audio_path=args.voice_audio,
    )
    status = result.get("status")
    if status == ReviewStatus.NOT_APPLICABLE.value:
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(status)
        return 0

    if status == ReviewStatus.BLOCKED.value:
        write_blocked_review_result(ws, result)
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(status)
        reason = (result.get("fingerprints") or {}).get("reason") or "BLOCKED"
        print(reason, file=sys.stderr)
        return 1

    primary = load_asr_timing_evidence(asr_primary_path(ws))
    draft = draft_reviewed_text_from_primary(primary)
    write_review_artifacts(ws, result, draft_text=draft, force_regenerate=args.force_regenerate)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(status)

    if status == ReviewStatus.NEEDS_OWNER_REVIEW.value:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

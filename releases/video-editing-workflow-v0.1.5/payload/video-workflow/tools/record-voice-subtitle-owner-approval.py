#!/usr/bin/env python3
"""Record Owner confirmation — requires pre-written owner intent artifact (not CLI actor alone)."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_TOOLS = Path(__file__).resolve().parent
_LIB = _TOOLS / "lib"
if str(_LIB) not in sys.path:
    sys.path.insert(0, str(_LIB))

from voice_subtitle_paths import (  # noqa: E402
    owner_approval_intent_path,
    review_result_path,
    reviewed_text_path,
)
from brief_subtitle_authority import load_brief_dict  # noqa: E402
from voice_subtitle_review import write_owner_approval  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workspace", type=Path, required=True)
    ap.add_argument(
        "--intent-file",
        type=Path,
        default=None,
        help="Owner-written intent JSON (default: production/voice-subtitle-owner-approval-intent.json)",
    )
    ap.add_argument("--text", type=Path, help="Defaults to reviewed-subtitle-text.txt")
    args = ap.parse_args()

    ws = args.workspace.resolve()
    brief_path = ws / "video-workflow" / "production" / "brief.yaml"
    if not brief_path.is_file():
        print("BRIEF_MISSING", file=sys.stderr)
        return 4
    brief = load_brief_dict(brief_path)

    rp = review_result_path(ws)
    if not rp.is_file():
        print("VOICE_REVIEW_RESULT_MISSING", file=sys.stderr)
        return 4
    result = json.loads(rp.read_text(encoding="utf-8-sig"))
    text_p = args.text or reviewed_text_path(ws)
    if not text_p.is_file():
        print("REVIEWED_TEXT_MISSING", file=sys.stderr)
        return 4
    text = text_p.read_text(encoding="utf-8-sig")
    intent_p = args.intent_file or owner_approval_intent_path(ws)
    try:
        write_owner_approval(
            ws,
            intent_path=intent_p,
            accepted_text=text,
            result=result,
            brief=brief,
        )
    except ValueError as e:
        print(str(e), file=sys.stderr)
        return 1
    print("OWNER_ACCEPTED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

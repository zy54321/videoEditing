#!/usr/bin/env python3
"""CLI: materialized cue → Resolve-native Text+ StyledTextCLS .setting."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

LIB = Path(__file__).resolve().parent / "lib"
sys.path.insert(0, str(LIB))

from textplus_cls_setting import (  # noqa: E402
    ClsError,
    generate_from_production_request_file,
    logical_char_count,
)


def default_font_profiles_path() -> Path:
    return Path(__file__).resolve().parents[1] / "runtime" / "textplus-font-profiles.yaml"


def main() -> int:
    ap = argparse.ArgumentParser(description="Generate Text+ StyledTextCLS .setting (v1 size emphasis)")
    ap.add_argument("--request", type=Path, required=True, help="JSON request (materialized_cue + typography)")
    ap.add_argument("--out", type=Path, required=True, help="Output .setting path")
    ap.add_argument(
        "--font-profiles",
        type=Path,
        default=default_font_profiles_path(),
        help="textplus-font-profiles.yaml path",
    )
    args = ap.parse_args()
    try:
        content = generate_from_production_request_file(args.request, args.font_profiles)
    except ClsError as exc:
        print(json.dumps({"error": exc.code, "message": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(content, encoding="utf-8")
    req = json.loads(args.request.read_text(encoding="utf-8"))
    text = req.get("materialized_cue", {}).get("styled_text") or ""
    print(
        json.dumps(
            {
                "out": str(args.out),
                "text_len": logical_char_count(str(text)),
                "route": "textplus_cls_setting_v1",
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

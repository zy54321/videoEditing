#!/usr/bin/env python3
"""Parse CharacterLevelStyling Array from exported Fusion .setting."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ARRAY_TUPLE_RE = re.compile(
    r"\{\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(?:Value\s*=\s*([\d.]+)|String\s*=\s*\"([^\"]*)\")\s*\}"
)


def parse_cls_array(setting_text: str) -> list[dict]:
    entries: list[dict] = []
    in_array = False
    for line in setting_text.splitlines():
        if "Array = {" in line:
            in_array = True
            continue
        if in_array:
            if line.strip().startswith("},") or line.strip() == "},":
                break
            m = ARRAY_TUPLE_RE.search(line)
            if m:
                param, first, last, value, string = (
                    int(m.group(1)),
                    int(m.group(2)),
                    int(m.group(3)),
                    m.group(4),
                    m.group(5),
                )
                row: dict = {"parameter": param, "first": first, "last": last}
                if value is not None:
                    row["value"] = float(value)
                if string is not None:
                    row["string"] = string
                entries.append(row)
    return entries


def unescape_fusion_string(value: str) -> str:
    out: list[str] = []
    i = 0
    while i < len(value):
        if value[i] == "\\" and i + 1 < len(value):
            nxt = value[i + 1]
            if nxt == "n":
                out.append("\n")
            elif nxt == "r":
                out.append("\r")
            elif nxt == "t":
                out.append("\t")
            elif nxt == "\\":
                out.append("\\")
            elif nxt == '"':
                out.append('"')
            else:
                out.append(nxt)
            i += 2
            continue
        out.append(value[i])
        i += 1
    return "".join(out)


def parse_text_input(setting_text: str) -> str | None:
    m = re.search(r'Text = Input \{ Value = "((?:\\.|[^"\\])*)"', setting_text)
    if not m:
        return None
    return unescape_fusion_string(m.group(1))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("setting", type=Path)
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()
    text = args.setting.read_text(encoding="utf-8")
    result = {
        "setting": str(args.setting),
        "text": parse_text_input(text),
        "cls_array": parse_cls_array(text),
    }
    out = json.dumps(result, ensure_ascii=False, indent=2)
    if args.out:
        args.out.write_text(out, encoding="utf-8")
    print(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())

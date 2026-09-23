#!/usr/bin/env python3
"""Build splittable A07-A09 request variants (multi-run) for A1.1 materialization.

Original atomic single-run cases trigger NO_LEGAL_INTERNAL_BREAK.
These variants preserve original concatenated text but insert prefer/allow
boundaries between chunks sized to fit under L1 ceiling per run.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CASES = ROOT / "cases"
CHUNK = 15  # chars per run; validated ~48px/char YaHei → under 864px ceiling


def splittable_runs(text: str) -> list[dict]:
    runs: list[dict] = []
    for i in range(0, len(text), CHUNK):
        chunk = text[i : i + CHUNK]
        policy = "prefer" if i + CHUNK < len(text) else "forbid"
        runs.append(
            {
                "text": chunk,
                "semantic_role": "phrase",
                "emphasis_level": "normal",
                "break_after": policy,
            }
        )
    return runs


def main() -> int:
    for case_id in ("A07", "A08", "A09"):
        src = CASES / f"{case_id}.request.json"
        data = json.loads(src.read_text(encoding="utf-8"))
        text = data["cues"][0]["runs"][0]["text"]
        out = copy.deepcopy(data)
        out["cues"][0]["runs"] = splittable_runs(text)
        out["cues"][0]["cue_id"] = case_id
        dest = CASES / f"{case_id}-splittable.request.json"
        dest.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
        print(case_id, len(text), "runs", len(out["cues"][0]["runs"]), "->", dest.name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

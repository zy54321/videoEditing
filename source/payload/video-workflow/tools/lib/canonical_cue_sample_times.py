"""Select representative active-cue sample times from canonical-subtitle-cues.json."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_canonical_cues(path: Path) -> list[dict[str, Any]]:
    doc = json.loads(path.read_text(encoding="utf-8-sig"))
    return list(doc.get("cues") or [])


def cue_midpoint(cue: dict[str, Any]) -> float:
    start = float(cue.get("start", 0))
    end = float(cue.get("end", start))
    return start + max(end - start, 0) / 2.0


def select_active_cue_sample_times(
    cues: list[dict[str, Any]],
    duration: float | None = None,
    max_samples: int = 5,
) -> list[dict[str, Any]]:
    if not cues:
        return []
    mids = [cue_midpoint(c) for c in cues]
    if duration is not None and duration > 0:
        mids = [m for m in mids if 0 <= m < duration]
    if not mids:
        mids = [cue_midpoint(cues[0])]

    anchors = [0.0, 0.25, 0.5, 0.75, 0.92]
    if duration and duration > 0:
        targets = [duration * a for a in anchors]
    else:
        lo, hi = min(mids), max(mids)
        span = max(hi - lo, 1e-3)
        targets = [lo + span * a for a in anchors]

    picked: list[float] = []
    used: set[int] = set()
    for t in targets:
        best_i = min(range(len(mids)), key=lambda i: abs(mids[i] - t))
        if best_i not in used:
            used.add(best_i)
            picked.append(mids[best_i])
    for i, m in enumerate(mids):
        if len(picked) >= max_samples:
            break
        if i not in used:
            picked.append(m)
            used.add(i)

    picked = sorted(set(round(t, 3) for t in picked))[:max_samples]
    return [{"id": f"cue_{i + 1:02d}", "sec": t, "role": "canonical_active_cue"} for i, t in enumerate(picked)]

"""ASR transcript cues — timing evidence only (text is alignment evidence, not authority)."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class AsrTimingCue:
    cue_id: str
    start: float
    end: float
    recognized_text: str


@dataclass(frozen=True)
class AsrTimingEvidence:
    schema_version: int
    cues: tuple[AsrTimingCue, ...]


def load_asr_timing_evidence(path: Path) -> AsrTimingEvidence:
    path = path.resolve()
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    version = int(data.get("schema_version", 1))
    cues_raw = data.get("cues") or []
    if not cues_raw:
        raise RuntimeError("ASR_EVIDENCE_EMPTY")

    cues: list[AsrTimingCue] = []
    for i, c in enumerate(cues_raw):
        cid = str(c.get("cue_id") or f"asr_{i + 1}")
        start = float(c["start"])
        end = float(c["end"])
        if end < start:
            raise RuntimeError(f"ASR_INVALID_RANGE: {cid}")
        text = str(c.get("recognized_text") or c.get("text") or "")
        cues.append(AsrTimingCue(cue_id=cid, start=start, end=end, recognized_text=text))

    cues.sort(key=lambda c: (c.start, c.end))
    return AsrTimingEvidence(schema_version=version, cues=tuple(cues))


def asr_evidence_to_dict(ev: AsrTimingEvidence) -> dict[str, Any]:
    return {
        "schema_version": ev.schema_version,
        "cues": [
            {
                "cue_id": c.cue_id,
                "start": c.start,
                "end": c.end,
                "recognized_text": c.recognized_text,
            }
            for c in ev.cues
        ],
    }

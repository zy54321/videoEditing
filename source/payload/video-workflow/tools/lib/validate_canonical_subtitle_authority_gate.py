"""SUBTITLE_CANONICAL_AUTHORITY_GATE — fail-closed validator for production artifact."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

from asr_timing_evidence import load_asr_timing_evidence
from brief_subtitle_authority import load_brief_dict
from canonical_subtitle_cue import CANONICAL_CUE_SCHEMA_VERSION, PIPELINE_ID
from frozen_script_authority import load_frozen_script_from_brief, load_frozen_script_file

_GATE_ID = "SUBTITLE_CANONICAL_AUTHORITY_GATE"


def _flatten_cue_text(cues: list[dict[str, Any]]) -> str:
    return "".join(str(c.get("text", "")).replace("\n", "") for c in cues)


def _asr_flat(asr_path: Path) -> str:
    ev = load_asr_timing_evidence(asr_path)
    return "".join(c.recognized_text.replace("\n", "") for c in ev.cues)


def validate_canonical_subtitle_authority_gate(
    *,
    canonical_path: Path,
    brief_path: Path | None = None,
    frozen_script_path: Path | None = None,
    asr_path: Path | None = None,
) -> dict[str, Any]:
    canonical_path = canonical_path.resolve()
    if not canonical_path.is_file():
        return {
            "gate": _GATE_ID,
            "verdict": "FAIL",
            "reason": "CANONICAL_ARTIFACT_MISSING",
            "path": str(canonical_path),
        }

    doc = json.loads(canonical_path.read_text(encoding="utf-8-sig"))
    errors: list[str] = []

    if int(doc.get("schema_version", 0)) != CANONICAL_CUE_SCHEMA_VERSION:
        errors.append("SCHEMA_VERSION_MISMATCH")
    if doc.get("pipeline_id") != PIPELINE_ID:
        errors.append("PIPELINE_ID_MISMATCH")

    meta = doc.get("meta") or {}
    if meta.get("status") != "OK":
        errors.append(f"META_STATUS_{meta.get('status')}")
    if meta.get("text_authority") != "frozen_script":
        errors.append("TEXT_AUTHORITY_NOT_FROZEN_SCRIPT")

    alignment = meta.get("alignment") or {}
    if alignment.get("blocked"):
        errors.append(f"ALIGNMENT_BLOCKED_{alignment.get('block_reason')}")

    cues = doc.get("cues") or []
    if not cues:
        errors.append("EMPTY_CUE_LIST")

    starts = [float(c.get("start", 0)) for c in cues]
    if starts != sorted(starts):
        errors.append("CUE_TIMING_NOT_MONOTONIC")
    for c in cues:
        if float(c.get("end", 0)) < float(c.get("start", 0)):
            errors.append(f"CUE_INVALID_RANGE_{c.get('cue_id')}")
        lines = c.get("lines") or []
        if len(lines) > 2:
            errors.append(f"CUE_TOO_MANY_LINES_{c.get('cue_id')}")

    frozen_norm = None
    fs = doc.get("frozen_script") or {}
    if fs.get("normalized_text"):
        frozen_norm = str(fs["normalized_text"]).replace("\n", "")
    elif brief_path:
        frozen_norm = load_frozen_script_from_brief(brief_path).normalized_text.replace("\n", "")
    elif frozen_script_path:
        frozen_norm = load_frozen_script_file(frozen_script_path).normalized_text.replace("\n", "")

    flat = _flatten_cue_text(cues)
    if frozen_norm is not None and flat != frozen_norm:
        errors.append("CUE_TEXT_DRIFT_FROM_FROZEN_SCRIPT")

    if asr_path and asr_path.is_file() and frozen_norm:
        asr_flat = _asr_flat(asr_path)
        if flat == asr_flat and frozen_norm != asr_flat:
            errors.append("ASR_TEXT_LEAKED_INTO_CUES")

    verdict = "PASS" if not errors else "FAIL"
    return {
        "gate": _GATE_ID,
        "verdict": verdict,
        "errors": errors,
        "canonical_path": str(canonical_path),
        "cue_count": len(cues),
        "pipeline_id": doc.get("pipeline_id"),
    }


def main() -> int:
    import argparse

    ap = argparse.ArgumentParser(description="Validate SUBTITLE_CANONICAL_AUTHORITY_GATE")
    ap.add_argument("--canonical", type=Path, required=True)
    ap.add_argument("--brief", type=Path)
    ap.add_argument("--script", type=Path)
    ap.add_argument("--asr", type=Path)
    ap.add_argument("--out", type=Path, help="Write gate result JSON")
    args = ap.parse_args()

    result = validate_canonical_subtitle_authority_gate(
        canonical_path=args.canonical,
        brief_path=args.brief,
        frozen_script_path=args.script,
        asr_path=args.asr,
    )
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(result["verdict"])
    return 0 if result["verdict"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())

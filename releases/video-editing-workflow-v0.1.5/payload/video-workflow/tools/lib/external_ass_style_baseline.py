"""Versioned external ASS style baseline (N02Prod / libass route)."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

BASELINE_ID = "astra-external-ass-n02prod-v1"
BASELINE_FILENAME = "subtitle-external-ass-style-baseline.v1.json"

STYLE_FIELD_ORDER = (
    "Name",
    "Fontname",
    "Fontsize",
    "PrimaryColour",
    "SecondaryColour",
    "OutlineColour",
    "BackColour",
    "Bold",
    "Italic",
    "Underline",
    "StrikeOut",
    "ScaleX",
    "ScaleY",
    "Spacing",
    "Angle",
    "BorderStyle",
    "Outline",
    "Shadow",
    "Alignment",
    "MarginL",
    "MarginR",
    "MarginV",
    "Encoding",
)


def default_baseline_path(tools_dir: Path | None = None) -> Path:
    root = tools_dir or Path(__file__).resolve().parent.parent
    return root.parent / "templates" / BASELINE_FILENAME


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_baseline(path: Path | None = None) -> dict[str, Any]:
    p = (path or default_baseline_path()).resolve()
    if not p.is_file():
        raise RuntimeError(f"EXTERNAL_ASS_BASELINE_MISSING: {p}")
    doc = json.loads(p.read_text(encoding="utf-8-sig"))
    validate_baseline_document(doc, path=p)
    doc["_baseline_path"] = str(p)
    doc["_baseline_sha256"] = sha256_file(p)
    return doc


def validate_baseline_document(doc: dict[str, Any], *, path: Path | None = None) -> None:
    if int(doc.get("schema_version", 0)) != 1:
        raise RuntimeError("EXTERNAL_ASS_BASELINE_INVALID: schema_version")
    if doc.get("baseline_id") != BASELINE_ID:
        raise RuntimeError("EXTERNAL_ASS_BASELINE_INVALID: baseline_id")
    style = doc.get("style")
    if not isinstance(style, dict):
        raise RuntimeError("EXTERNAL_ASS_BASELINE_INVALID: style")
    for key in STYLE_FIELD_ORDER:
        if key not in style:
            raise RuntimeError(f"EXTERNAL_ASS_BASELINE_INVALID: missing style.{key}")
    prov = doc.get("provenance") or {}
    expected_sha = prov.get("source_ass_sha256")
    if not expected_sha or len(str(expected_sha)) != 64:
        raise RuntimeError("EXTERNAL_ASS_BASELINE_INVALID: provenance.source_ass_sha256")


def ass_style_line(style: dict[str, Any]) -> str:
    name = style["Name"]
    parts = [style[k] for k in STYLE_FIELD_ORDER[1:]]
    return f"Style: {name}," + ",".join(str(p) for p in parts)


def play_res(doc: dict[str, Any]) -> tuple[int, int]:
    pr = doc.get("play_res") or {}
    return int(pr.get("x", 1080)), int(pr.get("y", 1920))

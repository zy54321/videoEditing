"""Native DRT subtitle track stroke template — capture, diff, inject (Route A)."""
from __future__ import annotations

import base64
import hashlib
import json
import re
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

SUBTITLE_TRACK_FIELDS_RE = re.compile(
    r"(<SubtitleTrackVec>[\s\S]*?<Sm2TiTrack DbId=\"[^\"]+\">\s*<FieldsBlob>)([0-9a-fA-F]*)(</FieldsBlob>)",
    re.MULTILINE,
)

FORBIDDEN_IN_TEMPLATE = (
    "Native字幕",
    "Sm2TiGenerator",
    "<Start>",
    "<Duration>",
    "MediaPoolItem",
    "FilePath",
)

SUBTITLE_TRACK_MARKER = "<SubtitleTrackVec>"
STYLED_MARKER_HEX = "450066006600650063007400460069006c00740065007200730042004100"  # EffectFiltersBA UTF-16LE


def _read_drt_seq_xml(drt_path: Path) -> Tuple[str, str]:
    with zipfile.ZipFile(drt_path, "r") as zf:
        seq_names = [n for n in zf.namelist() if n.startswith("SeqContainer/") and n.endswith(".xml")]
        if not seq_names:
            raise RuntimeError(f"No SeqContainer XML in {drt_path}")
        seq_name = seq_names[0]
        return seq_name, zf.read(seq_name).decode("utf-8", "replace")


def extract_subtitle_track_fields_blob(seq_xml: str) -> str:
    if SUBTITLE_TRACK_MARKER not in seq_xml:
        raise RuntimeError("SubtitleTrackVec not found")
    m = SUBTITLE_TRACK_FIELDS_RE.search(seq_xml)
    if not m:
        raise RuntimeError("Subtitle track FieldsBlob not found")
    return (m.group(2) or "").strip()


def validate_template_blob(blob_hex: str) -> List[str]:
    errors: List[str] = []
    if not blob_hex:
        errors.append("EMPTY_BLOB")
        return errors
    if STYLED_MARKER_HEX.lower() not in blob_hex.lower():
        errors.append("MISSING_EFFECTFILTERSBA_MARKER")
    for token in FORBIDDEN_IN_TEMPLATE:
        if token in blob_hex:
            errors.append(f"FORBIDDEN_TOKEN:{token}")
    return errors


def diff_subtitle_track_fields_blob(baseline_xml: str, styled_xml: str) -> Dict[str, Any]:
    base = extract_subtitle_track_fields_blob(baseline_xml)
    styled = extract_subtitle_track_fields_blob(styled_xml)
    return {
        "baseline_empty": base == "",
        "styled_empty": styled == "",
        "baseline_sha256": hashlib.sha256((base or "").encode()).hexdigest(),
        "styled_sha256": hashlib.sha256((styled or "").encode()).hexdigest(),
        "changed": base != styled,
        "baseline_len": len(base or ""),
        "styled_len": len(styled or ""),
        "route": "subtitle_track_fields_blob",
    }


def capture_from_pair(baseline_drt: Path, styled_drt: Path) -> Dict[str, Any]:
    _, base_xml = _read_drt_seq_xml(baseline_drt)
    _, styled_xml = _read_drt_seq_xml(styled_drt)
    diff = diff_subtitle_track_fields_blob(base_xml, styled_xml)
    blob = extract_subtitle_track_fields_blob(styled_xml)
    errors = validate_template_blob(blob)
    return {
        "baseline": str(baseline_drt.resolve()),
        "styled": str(styled_drt.resolve()),
        "diff": diff,
        "template_blob_hex": blob,
        "template_valid": len(errors) == 0 and diff.get("changed") and not diff.get("styled_empty"),
        "validation_errors": errors,
    }


def save_template_manifest(out_dir: Path, capture: Dict[str, Any]) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    blob = capture.get("template_blob_hex") or ""
    hex_path = out_dir / "subtitle-track-fields-blob.hex"
    manifest_path = out_dir / "template-manifest.json"
    if blob:
        hex_path.write_text(blob, encoding="utf-8")
    payload = {
        "schema_version": 1,
        "route": "native_drt_subtitle_track_fields_blob_template",
        "status": "READY" if capture.get("template_valid") else "PENDING_GOLD_STANDARD",
        "capture": {
            "baseline": capture.get("baseline"),
            "styled": capture.get("styled"),
            "diff": capture.get("diff"),
            "validation_errors": capture.get("validation_errors"),
        },
        "artifact": {
            "subtitle_track_fields_blob_hex": str(hex_path.name) if blob else None,
            "sha256": hashlib.sha256(blob.encode()).hexdigest() if blob else None,
        },
        "safety": {
            "contains_cue_text": False,
            "contains_timing": False,
            "style_only": True,
        },
    }
    manifest_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return manifest_path


def inject_template_into_drt(
    input_drt: Path,
    output_drt: Path,
    template_blob_hex: str,
) -> Dict[str, Any]:
    errors = validate_template_blob(template_blob_hex)
    if errors:
        raise RuntimeError(f"template invalid: {errors}")

    with zipfile.ZipFile(input_drt, "r") as zin:
        seq_name, seq_xml = _read_drt_seq_xml(input_drt)
        m = SUBTITLE_TRACK_FIELDS_RE.search(seq_xml)
        if not m:
            raise RuntimeError("Subtitle track FieldsBlob not found for injection")
        new_seq = seq_xml[: m.start(2)] + template_blob_hex + seq_xml[m.end(2) :]

        output_drt.parent.mkdir(parents=True, exist_ok=True)
        temp_out = output_drt.with_name(f"{output_drt.stem}.part{output_drt.suffix}")
        with zipfile.ZipFile(temp_out, "w", zipfile.ZIP_DEFLATED) as zout:
            for item in zin.infolist():
                data = zin.read(item.filename)
                if item.filename == seq_name:
                    data = new_seq.encode("utf-8")
                zout.writestr(item, data)
        if output_drt.exists():
            output_drt.unlink()
        temp_out.replace(output_drt)

    verify_blob = extract_subtitle_track_fields_blob(new_seq)
    return {
        "input": str(input_drt.resolve()),
        "output": str(output_drt.resolve()),
        "injected_sha256": hashlib.sha256(verify_blob.encode()).hexdigest(),
        "injected_len": len(verify_blob),
        "route": "subtitle_track_fields_blob",
    }


def load_template_blob_from_manifest(template_dir: Path) -> str:
    manifest_path = template_dir / "template-manifest.json"
    if not manifest_path.exists():
        raise RuntimeError("template-manifest.json missing")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    if manifest.get("status") != "READY":
        raise RuntimeError(f"template status {manifest.get('status')}")
    artifact = manifest.get("artifact") or {}
    hex_name = artifact.get("subtitle_track_fields_blob_hex") or artifact.get("effect_filters_ba_b64")
    if not hex_name:
        raise RuntimeError("no subtitle track fields blob artifact")
    hex_path = template_dir / hex_name
    if hex_path.suffix == ".b64":
        raw = base64.b64decode(hex_path.read_text(encoding="utf-8").strip())
        return raw.decode("utf-8")
    return hex_path.read_text(encoding="utf-8").strip()

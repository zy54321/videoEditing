"""Native DRT subtitle track stroke template — capture, diff, inject (Route A)."""
from __future__ import annotations

import base64
import hashlib
import json
import re
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

EFFECT_FILTERS_RE = re.compile(
    r"(<EffectFiltersBA\s*/>)|(<EffectFiltersBA>)([\s\S]*?)(</EffectFiltersBA>)",
    re.MULTILINE,
)

FORBIDDEN_IN_TEMPLATE = (
    "Sm2Subtitle",
    "<Text>",
    "startFrame",
    "durationFrames",
    "MediaPoolItem",
    "FilePath",
)

SUBTITLE_TRACK_MARKER = "<SubtitleTrackVec>"


def _read_drt_seq_xml(drt_path: Path) -> Tuple[str, str]:
    with zipfile.ZipFile(drt_path, "r") as zf:
        seq_names = [n for n in zf.namelist() if n.startswith("SeqContainer/") and n.endswith(".xml")]
        if not seq_names:
            raise RuntimeError(f"No SeqContainer XML in {drt_path}")
        seq_name = seq_names[0]
        return seq_name, zf.read(seq_name).decode("utf-8", "replace")


def extract_subtitle_effect_filters_ba(seq_xml: str) -> Optional[str]:
    if SUBTITLE_TRACK_MARKER not in seq_xml:
        raise RuntimeError("SubtitleTrackVec not found")
    sub_idx = seq_xml.index(SUBTITLE_TRACK_MARKER)
    tail = seq_xml[sub_idx:]
    m = EFFECT_FILTERS_RE.search(tail)
    if not m:
        raise RuntimeError("EffectFiltersBA not found under subtitle track")
    if m.group(1):
        return ""
    return (m.group(3) or "").strip()


def validate_template_blob(blob_inner: str) -> List[str]:
    errors: List[str] = []
    if not blob_inner:
        errors.append("EMPTY_BLOB")
        return errors
    for token in FORBIDDEN_IN_TEMPLATE:
        if token in blob_inner:
            errors.append(f"FORBIDDEN_TOKEN:{token}")
    return errors


def diff_effect_filters_ba(baseline_xml: str, styled_xml: str) -> Dict[str, Any]:
    base = extract_subtitle_effect_filters_ba(baseline_xml)
    styled = extract_subtitle_effect_filters_ba(styled_xml)
    return {
        "baseline_empty": base == "",
        "styled_empty": styled == "",
        "baseline_sha256": hashlib.sha256((base or "").encode()).hexdigest(),
        "styled_sha256": hashlib.sha256((styled or "").encode()).hexdigest(),
        "changed": base != styled,
        "baseline_len": len(base or ""),
        "styled_len": len(styled or ""),
    }


def capture_from_pair(baseline_drt: Path, styled_drt: Path) -> Dict[str, Any]:
    _, base_xml = _read_drt_seq_xml(baseline_drt)
    _, styled_xml = _read_drt_seq_xml(styled_drt)
    diff = diff_effect_filters_ba(base_xml, styled_xml)
    blob = extract_subtitle_effect_filters_ba(styled_xml)
    errors = validate_template_blob(blob)
    return {
        "baseline": str(baseline_drt.resolve()),
        "styled": str(styled_drt.resolve()),
        "diff": diff,
        "template_blob_inner": blob,
        "template_valid": len(errors) == 0 and diff.get("changed") and not diff.get("styled_empty"),
        "validation_errors": errors,
    }


def save_template_manifest(out_dir: Path, capture: Dict[str, Any]) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    blob = capture.get("template_blob_inner") or ""
    b64_path = out_dir / "effect-filters-ba.b64"
    manifest_path = out_dir / "template-manifest.json"
    if blob:
        b64_path.write_text(base64.b64encode(blob.encode("utf-8")).decode("ascii"), encoding="utf-8")
    payload = {
        "schema_version": 1,
        "route": "native_drt_effect_filters_ba_template",
        "status": "READY" if capture.get("template_valid") else "PENDING_GOLD_STANDARD",
        "capture": {
            "baseline": capture.get("baseline"),
            "styled": capture.get("styled"),
            "diff": capture.get("diff"),
            "validation_errors": capture.get("validation_errors"),
        },
        "artifact": {
            "effect_filters_ba_b64": str(b64_path.name) if blob else None,
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
    template_blob_inner: str,
) -> Dict[str, Any]:
    errors = validate_template_blob(template_blob_inner)
    if errors:
        raise RuntimeError(f"template invalid: {errors}")

    with zipfile.ZipFile(input_drt, "r") as zin:
        seq_name, seq_xml = _read_drt_seq_xml(input_drt)
        sub_idx = seq_xml.index(SUBTITLE_TRACK_MARKER)
        head, tail = seq_xml[:sub_idx], seq_xml[sub_idx:]
        m = EFFECT_FILTERS_RE.search(tail)
        if not m:
            raise RuntimeError("EffectFiltersBA not found for injection")
        replacement = f"<EffectFiltersBA>{template_blob_inner}</EffectFiltersBA>"
        if m.group(1):
            new_tail = tail[: m.start()] + replacement + tail[m.end() :]
        else:
            new_tail = tail[: m.start()] + replacement + tail[m.end() :]
        new_seq = head + new_tail

        output_drt.parent.mkdir(parents=True, exist_ok=True)
        temp_out = output_drt.with_suffix(output_drt.suffix + ".part")
        with zipfile.ZipFile(temp_out, "w", zipfile.ZIP_DEFLATED) as zout:
            for item in zin.infolist():
                data = zin.read(item.filename)
                if item.filename == seq_name:
                    data = new_seq.encode("utf-8")
                zout.writestr(item, data)
        if output_drt.exists():
            output_drt.unlink()
        temp_out.replace(output_drt)

    verify_blob = extract_subtitle_effect_filters_ba(new_seq)
    return {
        "input": str(input_drt.resolve()),
        "output": str(output_drt.resolve()),
        "injected_sha256": hashlib.sha256(verify_blob.encode()).hexdigest(),
        "injected_len": len(verify_blob),
    }


def load_template_blob_from_manifest(template_dir: Path) -> str:
    manifest_path = template_dir / "template-manifest.json"
    if not manifest_path.exists():
        raise RuntimeError("template-manifest.json missing")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    if manifest.get("status") != "READY":
        raise RuntimeError(f"template status {manifest.get('status')}")
    b64_name = (manifest.get("artifact") or {}).get("effect_filters_ba_b64")
    if not b64_name:
        raise RuntimeError("no effect_filters_ba artifact")
    b64_path = template_dir / b64_name
    raw = base64.b64decode(b64_path.read_text(encoding="utf-8").strip())
    return raw.decode("utf-8")

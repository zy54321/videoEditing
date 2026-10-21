"""ASR JSON provenance — independent dual-ASR verification (no fake trust)."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

REQUIRED_PROVENANCE_KEYS = (
    "asr_run_id",
    "provider_id",
    "source_audio_sha256",
    "captured_at",
)

# Repository ships no trusted ASR runtime; dual JSON alone cannot auto-approve subtitles.
AUTO_REVIEW_RUNTIME_AVAILABLE = False


def load_asr_document(path: Path) -> dict[str, Any]:
    path = path.resolve()
    return json.loads(path.read_text(encoding="utf-8-sig"))


def provenance_block(doc: dict[str, Any]) -> dict[str, Any]:
    p = doc.get("provenance")
    return p if isinstance(p, dict) else {}


def validate_provenance_fields(prov: dict[str, Any], label: str) -> list[str]:
    errors: list[str] = []
    for key in REQUIRED_PROVENANCE_KEYS:
        val = str(prov.get(key) or "").strip()
        if not val:
            errors.append(f"{label}_PROVENANCE_MISSING_{key}")
    return errors


def assess_dual_asr_independence(
    *,
    primary_path: Path,
    secondary_path: Path,
    expected_voice_audio_sha256: str | None,
) -> dict[str, Any]:
    """Return verdict dict; never treats duplicate files as independent."""
    from voice_subtitle_review import sha256_file

    primary_path = primary_path.resolve()
    secondary_path = secondary_path.resolve()
    pri_doc = load_asr_document(primary_path)
    sec_doc = load_asr_document(secondary_path)
    pri_prov = provenance_block(pri_doc)
    sec_prov = provenance_block(sec_doc)

    errors: list[str] = []
    errors.extend(validate_provenance_fields(pri_prov, "PRIMARY"))
    errors.extend(validate_provenance_fields(sec_prov, "SECONDARY"))

    pri_file_sha = sha256_file(primary_path)
    sec_file_sha = sha256_file(secondary_path)
    if pri_file_sha == sec_file_sha:
        errors.append("ASR_SECONDARY_DUPLICATE_FILE")

    pri_run = str(pri_prov.get("asr_run_id") or "").strip()
    sec_run = str(sec_prov.get("asr_run_id") or "").strip()
    if pri_run and sec_run and pri_run == sec_run:
        errors.append("ASR_RUN_ID_COLLISION")

    pri_pid = str(pri_prov.get("provider_id") or "").strip().lower()
    sec_pid = str(sec_prov.get("provider_id") or "").strip().lower()
    if pri_pid and sec_pid and pri_pid == sec_pid:
        errors.append("ASR_PROVIDER_NOT_INDEPENDENT")

    pri_audio = str(pri_prov.get("source_audio_sha256") or "").strip()
    sec_audio = str(sec_prov.get("source_audio_sha256") or "").strip()
    if pri_audio and sec_audio and pri_audio != sec_audio:
        errors.append("ASR_SOURCE_AUDIO_SHA_MISMATCH")
    if expected_voice_audio_sha256:
        if pri_audio != expected_voice_audio_sha256 or sec_audio != expected_voice_audio_sha256:
            errors.append("ASR_SOURCE_AUDIO_SHA_VOICE_MISMATCH")

    independent = not errors
    return {
        "independent_asr_evidence": independent,
        "errors": errors,
        "primary_file_sha256": pri_file_sha,
        "secondary_file_sha256": sec_file_sha,
        "primary_provider_id": pri_prov.get("provider_id"),
        "secondary_provider_id": sec_prov.get("provider_id"),
        "source_audio_sha256": pri_audio or sec_audio,
        "auto_review_runtime_available": AUTO_REVIEW_RUNTIME_AVAILABLE,
    }

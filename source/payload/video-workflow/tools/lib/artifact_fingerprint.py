"""SHA256 bindings for final artifact gate results."""
from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def sha256_file(path: Path) -> str:
    path = path.resolve()
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def build_evidence_bindings(
    *,
    contract_path: Path,
    final_artifact_path: Path,
    canonical_cues_path: Path | None,
    qa_report_path: Path | None = None,
) -> dict[str, Any]:
    bindings: dict[str, Any] = {
        "contract_sha256": sha256_file(contract_path),
        "final_artifact_sha256": sha256_file(final_artifact_path),
        "final_artifact_size": final_artifact_path.stat().st_size,
        "gate_generated_at": datetime.now(timezone.utc).isoformat(),
    }
    if canonical_cues_path and canonical_cues_path.is_file():
        bindings["canonical_subtitle_cues_sha256"] = sha256_file(canonical_cues_path)
    if qa_report_path and qa_report_path.is_file():
        bindings["qa_report_sha256"] = sha256_file(qa_report_path)
    return bindings


def verify_evidence_bindings(
    gate_result: dict[str, Any],
    *,
    contract_path: Path,
    final_artifact_path: Path,
    canonical_cues_path: Path | None,
    qa_report_path: Path | None = None,
) -> list[str]:
    errors: list[str] = []
    ev = gate_result.get("evidence_bindings") or {}
    if not ev:
        return ["EVIDENCE_BINDINGS_MISSING"]

    expected_contract = sha256_file(contract_path)
    if ev.get("contract_sha256") != expected_contract:
        errors.append("FINAL_RENDER_CONTRACT_CHANGED_AFTER_GATE")

    if not final_artifact_path.is_file():
        errors.append("FINAL_ARTIFACT_MISSING")
    else:
        if ev.get("final_artifact_sha256") != sha256_file(final_artifact_path):
            errors.append("FINAL_ARTIFACT_CHANGED_AFTER_GATE")

    if canonical_cues_path and canonical_cues_path.is_file():
        if ev.get("canonical_subtitle_cues_sha256") != sha256_file(canonical_cues_path):
            errors.append("CANONICAL_CUES_CHANGED_AFTER_GATE")

    if qa_report_path and qa_report_path.is_file():
        stored = ev.get("qa_report_sha256")
        if stored and stored != sha256_file(qa_report_path):
            errors.append("QA_REPORT_CHANGED_AFTER_GATE")

    return errors

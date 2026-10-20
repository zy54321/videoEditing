"""Detect when Production Brief mandates Canonical Subtitle Cue route."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def load_brief_dict(brief_path: Path) -> dict[str, Any]:
    brief_path = brief_path.resolve()
    if not brief_path.is_file():
        raise FileNotFoundError(f"BRIEF_NOT_FOUND: {brief_path}")
    return yaml.safe_load(brief_path.read_text(encoding="utf-8-sig")) or {}


def brief_requires_canonical_subtitle_route(brief: dict[str, Any]) -> bool:
    features = brief.get("features") or {}
    if features.get("subtitles") is False:
        return False
    content = brief.get("content") or {}
    authority = content.get("authority") or {}
    auth_type = (authority.get("type") or "").strip().lower()
    if auth_type == "script":
        return True
    assets = brief.get("assets") or {}
    script_asset = assets.get("script") or {}
    if bool(script_asset.get("frozen")):
        return True
    return False


def production_canonical_cue_path(workspace_root: Path) -> Path:
    return workspace_root / "video-workflow" / "production" / "canonical-subtitle-cues.json"


def production_asr_evidence_path(workspace_root: Path) -> Path:
    return workspace_root / "video-workflow" / "production" / "asr-timing-evidence.json"


def production_gate_result_path(workspace_root: Path) -> Path:
    return workspace_root / "video-workflow" / "production" / "subtitle-canonical-gate-result.json"

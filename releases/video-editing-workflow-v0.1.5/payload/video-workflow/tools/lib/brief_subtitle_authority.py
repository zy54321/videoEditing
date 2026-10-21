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


def brief_requires_canonical_subtitle_route(
    brief: dict[str, Any],
    *,
    workspace_root: Path | None = None,
    brief_path: Path | None = None,
) -> bool:
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
    if auth_type == "voice" and workspace_root is not None and brief_path is not None:
        from voice_subtitle_review import approval_allows_canonical

        ok, _ = approval_allows_canonical(workspace_root, brief_path)
        return ok
    return False


def voice_subtitle_review_pending(brief: dict[str, Any]) -> bool:
    """Voice + subtitles enabled but canonical text not yet approved."""
    features = brief.get("features") or {}
    if features.get("subtitles") is False:
        return False
    content = brief.get("content") or {}
    auth_type = (content.get("authority") or {}).get("type", "").strip().lower()
    if auth_type != "voice":
        return False
    if bool((brief.get("assets") or {}).get("script", {}).get("frozen")):
        return False
    return True


def voice_canonical_script_path(workspace_root: Path) -> Path:
    from voice_subtitle_paths import reviewed_text_path

    return reviewed_text_path(workspace_root)


def production_canonical_cue_path(workspace_root: Path) -> Path:
    return workspace_root / "video-workflow" / "production" / "canonical-subtitle-cues.json"


def production_asr_evidence_path(workspace_root: Path) -> Path:
    return workspace_root / "video-workflow" / "production" / "asr-timing-evidence.json"


def production_gate_result_path(workspace_root: Path) -> Path:
    return workspace_root / "video-workflow" / "production" / "subtitle-canonical-gate-result.json"

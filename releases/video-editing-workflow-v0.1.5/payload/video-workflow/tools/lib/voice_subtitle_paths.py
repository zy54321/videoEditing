"""Production paths for voice subtitle text review (U1)."""
from __future__ import annotations

from pathlib import Path


def production_dir(workspace_root: Path) -> Path:
    return workspace_root.resolve() / "video-workflow" / "production"


def review_result_path(workspace_root: Path) -> Path:
    return production_dir(workspace_root) / "voice-subtitle-review-result.json"


def reviewed_text_path(workspace_root: Path) -> Path:
    return production_dir(workspace_root) / "reviewed-subtitle-text.txt"


def asr_draft_subtitle_text_path(workspace_root: Path) -> Path:
    return production_dir(workspace_root) / "asr-draft-subtitle-text.txt"


def approval_path(workspace_root: Path) -> Path:
    return production_dir(workspace_root) / "voice-subtitle-approval.json"


def owner_approval_intent_path(workspace_root: Path) -> Path:
    return production_dir(workspace_root) / "voice-subtitle-owner-approval-intent.json"


def asr_primary_path(workspace_root: Path) -> Path:
    return production_dir(workspace_root) / "asr-timing-evidence.json"


def asr_secondary_path(workspace_root: Path) -> Path:
    return production_dir(workspace_root) / "asr-timing-evidence-alt.json"

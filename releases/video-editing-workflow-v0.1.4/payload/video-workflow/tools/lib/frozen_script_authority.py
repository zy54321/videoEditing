"""Frozen Script text authority — load from Production Brief + script file."""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

AUTHORITY_FROZEN_SCRIPT = "frozen_script"


@dataclass(frozen=True)
class FrozenScriptAuthority:
    authority: str
    source_path: str
    canonical_text: str
    normalized_text: str
    content_text: str  # punctuation retained; layout newlines removed


_LAYOUT_BREAK_RE = re.compile(r"[\r\n]+")
_MULTISPACE_RE = re.compile(r"[ \t]+")


def _nfc(s: str) -> str:
    return unicodedata.normalize("NFC", s)


def normalize_frozen_script_text(raw: str) -> FrozenScriptAuthority:
    """Remove layout line breaks and outer whitespace; preserve punctuation."""
    raw = raw.replace("\ufeff", "")
    # Layout newlines are not semantic — join to continuous text.
    collapsed = _LAYOUT_BREAK_RE.sub("", raw)
    collapsed = _MULTISPACE_RE.sub(" ", collapsed).strip()
    canonical = _nfc(collapsed)
    return FrozenScriptAuthority(
        authority=AUTHORITY_FROZEN_SCRIPT,
        source_path="",
        canonical_text=canonical,
        normalized_text=canonical,
        content_text=canonical,
    )


def _resolve_script_path(brief: dict[str, Any], brief_dir: Path) -> Path:
    content = brief.get("content") or {}
    authority = content.get("authority") or {}
    assets = brief.get("assets") or {}
    script_asset = assets.get("script") or {}

    auth_type = (authority.get("type") or "").strip().lower()
    auth_path = (authority.get("path") or "").strip()
    asset_path = (script_asset.get("path") or "").strip()
    frozen = bool(script_asset.get("frozen"))

    if auth_type == "script" and auth_path:
        p = Path(auth_path)
        if not p.is_absolute():
            p = (brief_dir / p).resolve()
        return p

    if frozen and asset_path:
        p = Path(asset_path)
        if not p.is_absolute():
            p = (brief_dir / p).resolve()
        return p

    if auth_type in ("voice", "subtitle", "owner"):
        raise RuntimeError(
            f"FROZEN_SCRIPT_REQUIRED: content.authority.type={auth_type!r} "
            "cannot supply subtitle text authority"
        )

    raise RuntimeError(
        "FROZEN_SCRIPT_REQUIRED: set content.authority.type=script with path "
        "or assets.script.frozen=true with assets.script.path"
    )


def load_frozen_script_from_brief(brief_path: Path) -> FrozenScriptAuthority:
    brief_path = brief_path.resolve()
    if not brief_path.is_file():
        raise FileNotFoundError(f"BRIEF_NOT_FOUND: {brief_path}")

    text = brief_path.read_text(encoding="utf-8-sig")
    brief = yaml.safe_load(text) or {}
    script_path = _resolve_script_path(brief, brief_path.parent)
    if not script_path.is_file():
        raise FileNotFoundError(f"FROZEN_SCRIPT_NOT_FOUND: {script_path}")

    raw = script_path.read_text(encoding="utf-8-sig")
    norm = normalize_frozen_script_text(raw)
    return FrozenScriptAuthority(
        authority=norm.authority,
        source_path=str(script_path),
        canonical_text=norm.canonical_text,
        normalized_text=norm.normalized_text,
        content_text=norm.content_text,
    )


def load_frozen_script_file(script_path: Path) -> FrozenScriptAuthority:
    script_path = script_path.resolve()
    if not script_path.is_file():
        raise FileNotFoundError(f"FROZEN_SCRIPT_NOT_FOUND: {script_path}")
    raw = script_path.read_text(encoding="utf-8-sig")
    norm = normalize_frozen_script_text(raw)
    return FrozenScriptAuthority(
        authority=norm.authority,
        source_path=str(script_path),
        canonical_text=norm.canonical_text,
        normalized_text=norm.normalized_text,
        content_text=norm.content_text,
    )

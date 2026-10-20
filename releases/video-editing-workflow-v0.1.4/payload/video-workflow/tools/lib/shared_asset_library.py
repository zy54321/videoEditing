"""Shared Asset Library V1 — catalog validate, music filter, asset_id resolve."""
from __future__ import annotations

import json
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

MOODS = frozenset({"calm", "curious", "tense", "warm", "neutral"})
ENERGIES = frozenset({"low", "medium", "high"})
PRIORITIES = frozenset({"PRIMARY", "SECONDARY"})
STATUSES = frozenset({"READY", "UNVERIFIED", "REJECTED", "MISSING"})
ASSET_LIST_FIELDS = frozenset(
    {"moods", "styles", "usage_tags", "vibe_tags", "purpose_tags"}
)
MISSING_CODE = "MUSIC_ASSET_NOT_AVAILABLE"


class CatalogError(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


@dataclass
class MusicSelectionQuery:
    mood: Optional[str] = None
    energy: Optional[str] = None
    required_duration: Optional[float] = None
    commercial_use: bool = True
    loopable: Optional[bool] = None
    status: str = "READY"


@dataclass
class MusicRequirement:
    moods: List[str] = field(default_factory=list)
    styles: List[str] = field(default_factory=list)
    usage: List[str] = field(default_factory=list)
    energy: Optional[str] = None
    required_duration: Optional[float] = None
    commercial_use: bool = True
    loopable: Optional[bool] = None
    status: str = "READY"

    @classmethod
    def from_selection_query(cls, query: MusicSelectionQuery) -> "MusicRequirement":
        moods = [query.mood] if query.mood else []
        return cls(
            moods=moods,
            energy=query.energy,
            required_duration=query.required_duration,
            commercial_use=query.commercial_use,
            loopable=query.loopable,
            status=query.status,
        )


def _strip_quotes(value: str) -> str:
    value = value.strip()
    if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
        return value[1:-1]
    return value


def _parse_scalar(raw: str) -> Any:
    raw = raw.strip()
    if not raw or raw.lower() in {"null", "~"}:
        return None
    if raw.lower() == "true":
        return True
    if raw.lower() == "false":
        return False
    if re.fullmatch(r"-?\d+", raw):
        return int(raw)
    if re.fullmatch(r"-?\d+\.\d+", raw):
        return float(raw)
    return _strip_quotes(raw)


def load_catalog_file(path: Path) -> Dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".json":
        return json.loads(text)
    return parse_catalog_yaml(text)


def parse_catalog_yaml(text: str) -> Dict[str, Any]:
    """Minimal YAML parser for V1 catalog/config shape (no external deps)."""
    lines = text.splitlines()
    root: Dict[str, Any] = {}
    assets: List[Dict[str, Any]] = []
    current_asset: Optional[Dict[str, Any]] = None
    asset_nested: Optional[str] = None
    root_nested_key: Optional[str] = None

    for line in lines:
        if not line.strip() or line.strip().startswith("#"):
            continue

        list_item_match = re.match(r"^(\s*)-\s+(.*)$", line)
        if list_item_match and current_asset is not None:
            nested = current_asset.get(asset_nested) if asset_nested else None
            if isinstance(nested, list):
                nested.append(_parse_scalar(list_item_match.group(2)))
                continue

        if re.match(r"^\s*-\s+", line) and isinstance(root.get("assets"), list):
            current_asset = {}
            assets.append(current_asset)
            asset_nested = None
            item_match = re.match(r"^\s*-\s+(\w+):\s*(.*)$", line)
            if item_match:
                current_asset[item_match.group(1)] = _parse_scalar(item_match.group(2))
            continue

        key_match = re.match(r"^(\s*)(\w+):\s*(.*)$", line)
        if not key_match:
            continue
        indent, key, rest = key_match.groups()
        depth = len(indent)

        if depth == 0:
            if key == "assets" and not rest.strip():
                root["assets"] = assets
                current_asset = None
                asset_nested = None
                root_nested_key = None
                continue
            if not rest.strip():
                root[key] = {}
                root_nested_key = key
                current_asset = None
                asset_nested = None
                continue
            root[key] = _parse_scalar(rest)
            root_nested_key = None
            current_asset = None
            asset_nested = None
            continue

        if depth == 2 and root_nested_key and current_asset is None:
            container = root.get(root_nested_key)
            if isinstance(container, dict):
                if not rest.strip():
                    container[key] = {}
                    asset_nested = key
                else:
                    container[key] = _parse_scalar(rest)
            continue

        if depth == 4 and root_nested_key and current_asset is None and asset_nested:
            container = root.get(root_nested_key, {}).get(asset_nested)
            if isinstance(container, dict):
                container[key] = _parse_scalar(rest)
            continue

        if current_asset is None:
            continue
        if depth == 4 and not rest.strip():
            if key in ASSET_LIST_FIELDS:
                current_asset[key] = []
                asset_nested = key
            else:
                asset_nested = key
                current_asset[asset_nested] = {}
            continue
        if depth == 6 and asset_nested and isinstance(current_asset.get(asset_nested), dict):
            current_asset[asset_nested][key] = _parse_scalar(rest)
            continue
        if depth == 4:
            current_asset[key] = _parse_scalar(rest)
            asset_nested = None

    if "assets" not in root:
        root["assets"] = assets
    return root


def load_library_config(config_path: Path) -> Dict[str, Any]:
    return load_catalog_file(config_path)


def resolve_library_paths(config: Dict[str, Any], config_dir: Path) -> Tuple[Path, Path]:
    root_raw = config.get("shared_asset_root")
    if not root_raw:
        raise CatalogError("CONFIG_INVALID", "shared_asset_root is required")
    root = Path(str(root_raw)).resolve()
    rel_catalog = config.get("catalog", {}).get("music", "catalog/music.yaml")
    catalog_path = (root / rel_catalog).resolve()
    return root, catalog_path


def _is_safe_relative_path(rel: str) -> bool:
    if not rel or rel.startswith(("/", "\\")):
        return False
    parts = Path(rel.replace("\\", "/")).parts
    return ".." not in parts


def resolve_asset_path(library_root: Path, relative_path: str) -> Path:
    if not _is_safe_relative_path(relative_path):
        raise CatalogError("PATH_TRAVERSAL", f"unsafe asset path: {relative_path}")
    resolved = (library_root / relative_path).resolve()
    try:
        resolved.relative_to(library_root)
    except ValueError:
        raise CatalogError("PATH_TRAVERSAL", f"path escapes library root: {relative_path}")
    return resolved


def probe_music_file(path: Path) -> Dict[str, Any]:
    """Read technical audio metadata via ffprobe (authority for registration)."""
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration,size,bit_rate",
        "-show_entries",
        "stream=codec_name,sample_rate,channels,sample_fmt,bits_per_sample",
        "-of",
        "json",
        str(path),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise CatalogError("PROBE_FAILED", proc.stderr.strip() or "ffprobe failed")
    payload = json.loads(proc.stdout)
    streams = payload.get("streams") or [{}]
    fmt = payload.get("format") or {}
    stream = streams[0]
    return {
        "codec": stream.get("codec_name"),
        "sample_format": stream.get("sample_fmt"),
        "sample_rate": int(stream.get("sample_rate") or 0),
        "channels": int(stream.get("channels") or 0),
        "bits_per_sample": int(stream.get("bits_per_sample") or 0),
        "duration": float(fmt.get("duration") or 0),
        "file_size_bytes": int(fmt.get("size") or 0),
        "bit_rate": int(fmt.get("bit_rate") or 0),
    }


def validate_music_asset(
    asset: Dict[str, Any],
    library_root: Path,
    *,
    check_file: bool = True,
) -> List[str]:
    errors: List[str] = []
    required = [
        "asset_id",
        "type",
        "path",
        "title",
        "duration",
        "mood",
        "energy",
        "loopable",
        "license",
        "status",
    ]
    for field_name in required:
        if field_name not in asset or asset[field_name] in (None, ""):
            errors.append(f"missing:{field_name}")

    if asset.get("type") != "music":
        errors.append("type:not_music")
    if asset.get("mood") not in MOODS:
        errors.append("mood:invalid")
    if asset.get("energy") not in ENERGIES:
        errors.append("energy:invalid")
    if asset.get("status") not in STATUSES:
        errors.append("status:invalid")
    priority = asset.get("priority")
    if priority is not None and priority not in PRIORITIES:
        errors.append("priority:invalid")

    rel = str(asset.get("path", ""))
    if not _is_safe_relative_path(rel):
        errors.append("path:unsafe")

    license_obj = asset.get("license") or {}
    for lf in ("type", "source", "commercial_use", "attribution_required"):
        if lf not in license_obj:
            errors.append(f"license:missing:{lf}")
    if not str(license_obj.get("source", "")).strip():
        errors.append("license:empty_source")

    status = asset.get("status")
    if status == "READY":
        if errors:
            errors.append("ready:incomplete_metadata")
        if license_obj.get("commercial_use") is not True:
            errors.append("license:commercial_use_not_true")
        if license_obj.get("attribution_required") is not True and license_obj.get("attribution_required") is not False:
            errors.append("license:attribution_not_explicit")
        if not str(license_obj.get("evidence_url", "")).strip():
            errors.append("license:missing_evidence_url")
        if check_file and rel:
            try:
                target = resolve_asset_path(library_root, rel)
            except CatalogError:
                errors.append("path:unsafe")
            else:
                if not target.is_file():
                    errors.append("file:missing")

    return errors


def validate_music_catalog(
    catalog: Dict[str, Any],
    library_root: Path,
    *,
    check_files: bool = True,
) -> Dict[str, Any]:
    assets = catalog.get("assets") or []
    seen_ids: set[str] = set()
    results = []
    ok = True
    for idx, asset in enumerate(assets):
        aid = str(asset.get("asset_id", f"#{idx}"))
        if aid in seen_ids:
            ok = False
            results.append({"asset_id": aid, "valid": False, "errors": ["asset_id:duplicate"]})
            continue
        seen_ids.add(aid)
        errors = validate_music_asset(asset, library_root, check_file=check_files)
        if errors:
            ok = False
        results.append({"asset_id": aid, "valid": not errors, "errors": errors})
    return {"valid": ok, "assets": results}


def _normalize_tag(value: str) -> str:
    return re.sub(r"\s+", " ", str(value).lower().strip().replace("-", " "))


def _tag_match(query_tag: str, candidate_tags: Sequence[str]) -> bool:
    query = _normalize_tag(query_tag)
    for tag in candidate_tags:
        normalized = _normalize_tag(tag)
        if not normalized:
            continue
        if query == normalized or query in normalized or normalized in query:
            return True
    return False


def _asset_mood_tags(asset: Dict[str, Any]) -> List[str]:
    tags: List[str] = []
    primary = asset.get("mood")
    if primary:
        tags.append(str(primary))
    for item in asset.get("moods") or []:
        tags.append(str(item))
    for item in asset.get("vibe_tags") or []:
        tags.append(str(item))
    return tags


def _asset_style_tags(asset: Dict[str, Any]) -> List[str]:
    tags = [str(item) for item in asset.get("styles") or []]
    for item in asset.get("purpose_tags") or []:
        tags.append(str(item))
    return tags


def _asset_usage_tags(asset: Dict[str, Any]) -> List[str]:
    tags = [str(item) for item in asset.get("usage_tags") or []]
    for item in asset.get("purpose_tags") or []:
        tags.append(str(item))
    return tags


def _requirement_matches(asset: Dict[str, Any], requirement: MusicRequirement) -> bool:
    if asset.get("type") != "music":
        return False
    if asset.get("status") != requirement.status:
        return False
    lic = asset.get("license") or {}
    if requirement.commercial_use and lic.get("commercial_use") is not True:
        return False
    if requirement.energy and asset.get("energy") != requirement.energy:
        return False
    if requirement.required_duration is not None and float(asset.get("duration") or 0) < requirement.required_duration:
        return False
    if requirement.loopable is True and asset.get("loopable") is not True:
        return False
    return True


def _score_tag_match(
    query_tag: str,
    primary_tags: Sequence[str],
    secondary_tags: Sequence[str],
    *,
    base: int,
    primary_bonus: int,
) -> int:
    score = 0
    matched = False
    if _tag_match(query_tag, primary_tags):
        score += base + primary_bonus
        matched = True
    elif _tag_match(query_tag, secondary_tags):
        score += base
        matched = True
    return score if matched else 0


def _score_requirement(asset: Dict[str, Any], requirement: MusicRequirement) -> int:
    score = 0
    if asset.get("priority") == "PRIMARY":
        score += 1000
    elif asset.get("priority") == "SECONDARY":
        score -= 300

    primary_moods = [str(asset.get("mood") or "")] + [str(x) for x in asset.get("moods") or []]
    secondary_moods = [str(x) for x in asset.get("vibe_tags") or []]
    primary_styles = [str(x) for x in asset.get("styles") or []]
    secondary_styles = [str(x) for x in asset.get("purpose_tags") or []]
    primary_usage = [str(x) for x in asset.get("usage_tags") or []]
    secondary_usage = [str(x) for x in asset.get("purpose_tags") or []]

    for mood in requirement.moods:
        score += _score_tag_match(mood, primary_moods, secondary_moods, base=100, primary_bonus=50)
    for style in requirement.styles:
        score += _score_tag_match(style, primary_styles, secondary_styles, base=80, primary_bonus=40)
    for usage in requirement.usage:
        score += _score_tag_match(usage, primary_usage, secondary_usage, base=60, primary_bonus=40)

    if requirement.energy and asset.get("energy") == requirement.energy:
        score += 50

    duration = float(asset.get("duration") or 0)
    if requirement.required_duration is not None and duration >= requirement.required_duration:
        score += 25
    if requirement.loopable is True and asset.get("loopable") is True:
        score += 10

    notes = str(asset.get("notes") or "").lower()
    if "preferred candidate" in notes:
        score += 15

    return score


def _requirement_dimension_match(asset: Dict[str, Any], requirement: MusicRequirement) -> bool:
    if requirement.moods and not any(_tag_match(m, _asset_mood_tags(asset)) for m in requirement.moods):
        return False
    if requirement.styles and not any(_tag_match(s, _asset_style_tags(asset)) for s in requirement.styles):
        return False
    if requirement.usage and not any(_tag_match(u, _asset_usage_tags(asset)) for u in requirement.usage):
        return False
    return True


def select_music_for_requirement(
    catalog: Dict[str, Any],
    requirement: MusicRequirement,
) -> List[Dict[str, Any]]:
    candidates: List[Dict[str, Any]] = []
    for asset in catalog.get("assets") or []:
        if not _requirement_matches(asset, requirement):
            continue
        if not _requirement_dimension_match(asset, requirement):
            continue
        score = _score_requirement(asset, requirement)
        enriched = dict(asset)
        enriched["_selection_score"] = score
        candidates.append(enriched)

    candidates.sort(key=lambda a: (a.get("_selection_score", 0), float(a.get("duration") or 0)), reverse=True)
    return candidates


def search_music_library(
    catalog: Dict[str, Any],
    requirement: MusicRequirement,
) -> Dict[str, Any]:
    matches = select_music_for_requirement(catalog, requirement)
    return {
        "ok": bool(matches),
        "code": None if matches else MISSING_CODE,
        "candidates": matches,
        "count": len(matches),
    }


def _rank_asset(asset: Dict[str, Any], query: MusicSelectionQuery) -> Tuple[int, float]:
    requirement = MusicRequirement.from_selection_query(query)
    score = _score_requirement(asset, requirement)
    if query.status and asset.get("status") == query.status:
        score += 1000
    return score, float(asset.get("duration") or 0)


def select_music_assets(
    catalog: Dict[str, Any],
    query: MusicSelectionQuery,
) -> List[Dict[str, Any]]:
    requirement = MusicRequirement.from_selection_query(query)
    if query.mood:
        requirement.moods = [query.mood]
    return select_music_for_requirement(catalog, requirement)


def select_music_or_missing(
    catalog: Dict[str, Any],
    query: MusicSelectionQuery,
) -> Dict[str, Any]:
    matches = select_music_assets(catalog, query)
    if not matches:
        return {"ok": False, "code": MISSING_CODE, "candidates": []}
    return {"ok": True, "code": None, "candidates": matches}


def select_music_requirement_or_missing(
    catalog: Dict[str, Any],
    requirement: MusicRequirement,
) -> Dict[str, Any]:
    result = search_music_library(catalog, requirement)
    if not result["ok"]:
        return {"ok": False, "code": MISSING_CODE, "candidates": []}
    return {"ok": True, "code": None, "candidates": result["candidates"]}


def resolve_music_asset_id(
    catalog: Dict[str, Any],
    library_root: Path,
    asset_id: str,
) -> Dict[str, Any]:
    for asset in catalog.get("assets") or []:
        if asset.get("asset_id") != asset_id:
            continue
        rel = str(asset.get("path", ""))
        path = resolve_asset_path(library_root, rel)
        return {
            "asset_id": asset_id,
            "path": str(path),
            "relative_path": rel,
            "status": asset.get("status"),
            "exists": path.is_file(),
        }
    raise CatalogError("ASSET_NOT_FOUND", f"unknown asset_id: {asset_id}")

"""Shared Asset Library V1 — catalog validate, music filter, asset_id resolve."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

MOODS = frozenset({"calm", "curious", "tense", "warm", "neutral"})
ENERGIES = frozenset({"low", "medium", "high"})
STATUSES = frozenset({"READY", "UNVERIFIED", "REJECTED", "MISSING"})
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
            asset_nested = key
            current_asset[asset_nested] = {}
            continue
        if depth == 6 and asset_nested:
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
    for field in required:
        if field not in asset or asset[field] in (None, ""):
            errors.append(f"missing:{field}")

    if asset.get("type") != "music":
        errors.append("type:not_music")
    if asset.get("mood") not in MOODS:
        errors.append("mood:invalid")
    if asset.get("energy") not in ENERGIES:
        errors.append("energy:invalid")
    if asset.get("status") not in STATUSES:
        errors.append("status:invalid")

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
        if license_obj.get("commercial_use") is not True and license_obj.get("commercial_use") is not False:
            errors.append("license:commercial_use_not_explicit")
        if license_obj.get("attribution_required") is not True and license_obj.get("attribution_required") is not False:
            errors.append("license:attribution_not_explicit")
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


def _rank_asset(asset: Dict[str, Any], query: MusicSelectionQuery) -> Tuple[int, float]:
    score = 0
    if asset.get("status") == query.status:
        score += 1000
    if query.mood and asset.get("mood") == query.mood:
        score += 100
    if query.energy and asset.get("energy") == query.energy:
        score += 50
    duration = float(asset.get("duration") or 0)
    if query.required_duration is not None and duration >= query.required_duration:
        score += 25
    if query.loopable is True and asset.get("loopable") is True:
        score += 10
    return score, duration


def select_music_assets(
    catalog: Dict[str, Any],
    query: MusicSelectionQuery,
) -> List[Dict[str, Any]]:
    candidates: List[Dict[str, Any]] = []
    for asset in catalog.get("assets") or []:
        if asset.get("type") != "music":
            continue
        if asset.get("status") != query.status:
            continue
        lic = asset.get("license") or {}
        if query.commercial_use and lic.get("commercial_use") is not True:
            continue
        if query.mood and asset.get("mood") != query.mood:
            continue
        if query.energy and asset.get("energy") != query.energy:
            continue
        if query.required_duration is not None and float(asset.get("duration") or 0) < query.required_duration:
            continue
        if query.loopable is True and asset.get("loopable") is not True:
            continue
        candidates.append(asset)
    candidates.sort(key=lambda a: _rank_asset(a, query), reverse=True)
    return candidates


def select_music_or_missing(
    catalog: Dict[str, Any],
    query: MusicSelectionQuery,
) -> Dict[str, Any]:
    matches = select_music_assets(catalog, query)
    if not matches:
        return {"ok": False, "code": MISSING_CODE, "candidates": []}
    return {"ok": True, "code": None, "candidates": matches}


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

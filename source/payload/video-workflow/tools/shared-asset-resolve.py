#!/usr/bin/env python3
"""Resolve music asset_id to absolute path under Shared Asset root."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

LIB = Path(__file__).resolve().parent / "lib"
sys.path.insert(0, str(LIB))

from shared_asset_library import (  # noqa: E402
    CatalogError,
    load_catalog_file,
    load_library_config,
    resolve_library_paths,
    resolve_music_asset_id,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Resolve shared asset_id to path")
    parser.add_argument("asset_id")
    parser.add_argument("--config", type=Path)
    parser.add_argument("--catalog", type=Path)
    parser.add_argument("--root", type=Path)
    args = parser.parse_args()

    payload = Path(__file__).resolve().parents[1]
    config_path = args.config or (payload / "runtime" / "shared-asset-library-config.yaml")
    config = load_library_config(config_path)
    root, catalog_path = resolve_library_paths(config, config_path.parent)
    if args.root:
        root = args.root.resolve()
    if args.catalog:
        catalog_path = args.catalog.resolve()

    catalog = load_catalog_file(catalog_path)
    try:
        result = resolve_music_asset_id(catalog, root, args.asset_id)
    except CatalogError as exc:
        print(json.dumps({"ok": False, "code": exc.code, "message": str(exc)}))
        return 1
    print(json.dumps({"ok": True, **result}, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

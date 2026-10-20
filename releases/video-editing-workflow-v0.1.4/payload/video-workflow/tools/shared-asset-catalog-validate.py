#!/usr/bin/env python3
"""Validate Shared Asset music catalog against V1 contract."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

LIB = Path(__file__).resolve().parent / "lib"
sys.path.insert(0, str(LIB))

from shared_asset_library import (  # noqa: E402
    load_catalog_file,
    load_library_config,
    resolve_library_paths,
    validate_music_catalog,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate shared asset music catalog")
    parser.add_argument("--config", type=Path, help="shared-asset-library-config.yaml path")
    parser.add_argument("--catalog", type=Path, help="music catalog path (overrides config)")
    parser.add_argument("--root", type=Path, help="library root (overrides config)")
    parser.add_argument("--no-file-check", action="store_true")
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
    result = validate_music_catalog(catalog, root, check_files=not args.no_file_check)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

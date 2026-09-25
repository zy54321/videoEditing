#!/usr/bin/env python3
"""List / filter music assets from Shared Asset Library catalog."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

LIB = Path(__file__).resolve().parent / "lib"
sys.path.insert(0, str(LIB))

from shared_asset_library import (  # noqa: E402
    MusicRequirement,
    MusicSelectionQuery,
    load_catalog_file,
    load_library_config,
    resolve_library_paths,
    select_music_or_missing,
    select_music_requirement_or_missing,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Filter music assets from shared catalog")
    parser.add_argument("--config", type=Path)
    parser.add_argument("--catalog", type=Path)
    parser.add_argument("--root", type=Path, help="library root override for catalog-relative paths")
    parser.add_argument("--mood")
    parser.add_argument("--moods", help="comma-separated mood tags")
    parser.add_argument("--styles", help="comma-separated style tags")
    parser.add_argument("--usage", help="comma-separated usage tags")
    parser.add_argument("--energy", choices=["low", "medium", "high"])
    parser.add_argument("--required-duration", type=float)
    parser.add_argument("--loopable", action="store_true")
    parser.add_argument("--commercial-use", action="store_true", default=True)
    parser.add_argument("--no-commercial-use", action="store_true")
    parser.add_argument("--requirement-json", type=Path, help="JSON MusicRequirement payload")
    args = parser.parse_args()

    payload = Path(__file__).resolve().parents[1]
    config_path = args.config or (payload / "runtime" / "shared-asset-library-config.yaml")
    config = load_library_config(config_path)
    root, catalog_path = resolve_library_paths(config, config_path.parent)
    if args.root:
        root = args.root.resolve()
    if args.catalog:
        catalog_path = args.catalog.resolve()

    commercial = not args.no_commercial_use
    catalog = load_catalog_file(catalog_path)

    if args.requirement_json:
        payload = json.loads(args.requirement_json.read_text(encoding="utf-8"))
        requirement = MusicRequirement(
            moods=list(payload.get("moods") or []),
            styles=list(payload.get("styles") or []),
            usage=list(payload.get("usage") or []),
            energy=payload.get("energy"),
            required_duration=payload.get("required_duration"),
            commercial_use=payload.get("commercial_use", commercial),
            loopable=payload.get("loopable"),
            status=payload.get("status", "READY"),
        )
        result = select_music_requirement_or_missing(catalog, requirement)
    elif args.moods or args.styles or args.usage:
        moods = [m.strip() for m in (args.moods or "").split(",") if m.strip()]
        if args.mood and args.mood not in moods:
            moods.insert(0, args.mood)
        requirement = MusicRequirement(
            moods=moods,
            styles=[s.strip() for s in (args.styles or "").split(",") if s.strip()],
            usage=[u.strip() for u in (args.usage or "").split(",") if u.strip()],
            energy=args.energy,
            required_duration=args.required_duration,
            commercial_use=commercial,
            loopable=True if args.loopable else None,
        )
        result = select_music_requirement_or_missing(catalog, requirement)
    else:
        query = MusicSelectionQuery(
            mood=args.mood,
            energy=args.energy,
            required_duration=args.required_duration,
            commercial_use=commercial,
            loopable=True if args.loopable else None,
        )
        result = select_music_or_missing(catalog, query)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())

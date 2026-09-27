#!/usr/bin/env python3
"""Analyze Edit Blueprint assembly plan for pacing warnings / repair candidates."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

LIB = Path(__file__).resolve().parent / "lib"
sys.path.insert(0, str(LIB))

from pacing_qa import analyze_assembly_plan, analyze_blueprint_file, load_pacing_profile  # noqa: E402
from shared_asset_library import load_catalog_file  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Beat-first pacing QA")
    parser.add_argument("--blueprint", type=Path, help="edit-blueprint.yaml path")
    parser.add_argument("--assembly-json", type=Path, help="standalone assembly_plan JSON")
    parser.add_argument("--profile", type=Path)
    args = parser.parse_args()

    payload = Path(__file__).resolve().parents[1]
    profile_path = args.profile or (payload / "runtime" / "informational-short-pacing-v1-profile.yaml")

    if args.blueprint:
        result = analyze_blueprint_file(args.blueprint.resolve(), profile_path.resolve())
    elif args.assembly_json:
        assembly = json.loads(args.assembly_json.read_text(encoding="utf-8-sig"))
        profile = load_pacing_profile(profile_path.resolve())
        result = analyze_assembly_plan(assembly, profile)
    else:
        raise SystemExit("Provide --blueprint or --assembly-json")

    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result.get("ok") else 2


if __name__ == "__main__":
    raise SystemExit(main())

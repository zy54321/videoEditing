#!/usr/bin/env python3
"""Derive the music bed before render preparation. Profile targets are authoritative."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

_LIB = Path(__file__).resolve().parent / "lib"
if str(_LIB) not in sys.path:
    sys.path.insert(0, str(_LIB))

from brief_final_render_contract import load_brief_yaml  # noqa: E402
from shared_asset_library import (  # noqa: E402
    CatalogError,
    load_catalog_file,
    load_library_config,
    resolve_library_paths,
    resolve_music_asset_id,
)


def _sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _resolve(workspace: Path, raw: str) -> Path | None:
    text = str(raw or "").strip()
    if not text:
        return None
    path = Path(text)
    if not path.is_absolute():
        path = workspace / path
    return path


def _load_derive():
    source = Path(__file__).resolve().parent / "derive-music-bed.py"
    spec = importlib.util.spec_from_file_location("derive_music_bed_mod", source)
    if spec is None or spec.loader is None:
        raise RuntimeError("DERIVE_MUSIC_BED_MISSING")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.derive_music_bed


def _library_config(workspace: Path) -> Path | None:
    local = workspace / "video-workflow" / "runtime" / "shared-asset-library-config.yaml"
    if local.is_file():
        return local
    bundled = Path(__file__).resolve().parent.parent / "runtime" / "shared-asset-library-config.yaml"
    return bundled if bundled.is_file() else None


def _resolve_asset_id(workspace: Path, asset_id: str) -> dict:
    config_path = _library_config(workspace)
    if config_path is None:
        raise CatalogError("CONFIG_MISSING", "shared-asset-library-config.yaml not found")
    config = load_library_config(config_path)
    root, catalog_path = resolve_library_paths(config, config_path.parent)
    catalog = load_catalog_file(catalog_path)
    return resolve_music_asset_id(catalog, root, asset_id)


def _selection(workspace: Path, brief_path: Path) -> dict:
    brief = load_brief_yaml(brief_path)
    features = brief.get("features") or {}
    music_asset = (brief.get("assets") or {}).get("music") or {}
    voice = _resolve(workspace, str(((brief.get("assets") or {}).get("voice") or {}).get("path") or ""))
    raw_path = str(music_asset.get("path") or "").strip()
    asset_id = str(music_asset.get("asset_id") or "").strip()
    if features.get("background_music") is False:
        return {"music_pass": "SKIPPED", "reason": "BACKGROUND_MUSIC_DISABLED", "voice": voice}
    if not raw_path and not asset_id:
        if features.get("background_music") is True:
            return {"music_pass": "PENDING", "reason": "MUSIC_NOT_SELECTED", "voice": voice, "fallback_is_pass": False}
        return {"music_pass": "SKIPPED", "reason": "MUSIC_NOT_SELECTED", "voice": voice}
    resolved_path: Path | None = None
    if asset_id:
        try:
            resolved = _resolve_asset_id(workspace, asset_id)
        except CatalogError as exc:
            return {
                "music_pass": "FAIL",
                "reason": "MUSIC_ASSET_UNRESOLVED",
                "detail": exc.code,
                "asset_id": asset_id,
                "voice": voice,
                "fallback_is_pass": False,
            }
        if not resolved.get("exists"):
            return {
                "music_pass": "FAIL",
                "reason": "MUSIC_ASSET_FILE_MISSING",
                "asset_id": asset_id,
                "music": resolved.get("path"),
                "voice": voice,
                "fallback_is_pass": False,
            }
        resolved_path = Path(str(resolved["path"]))
    path_obj = _resolve(workspace, raw_path) if raw_path else None
    if path_obj is not None and resolved_path is not None and path_obj.resolve() != resolved_path.resolve():
        return {
            "music_pass": "FAIL",
            "reason": "MUSIC_PATH_ASSET_ID_CONFLICT",
            "asset_id": asset_id,
            "music": str(path_obj),
            "resolved_music": str(resolved_path),
            "voice": voice,
            "fallback_is_pass": False,
        }
    music = resolved_path or path_obj
    return {
        "music_pass": "REQUIRED",
        "music": music,
        "voice": voice,
        "asset_id": asset_id,
        "music_source": "asset_id" if asset_id else "path",
    }


def ensure_music_bed(
    *,
    workspace: Path,
    brief_path: Path,
    profile: Path,
    check_only: bool,
) -> dict:
    workspace = workspace.resolve()
    brief_path = brief_path.resolve()
    selected = _selection(workspace, brief_path)
    if selected["music_pass"] != "REQUIRED":
        selected["fallback_is_pass"] = False
        return selected

    prod = workspace / "video-workflow" / "production"
    derived = prod / "derived-music-bed.wav"
    report_path = prod / "music-bed-derivation-report.json"
    binding_path = prod / "music-bed-binding.json"
    music: Path = selected["music"]
    voice: Path | None = selected["voice"]
    if voice is None or not voice.is_file() or not music.is_file() or not profile.is_file():
        return {
            "music_pass": "FAIL",
            "verdict": "MEASUREMENT_FAILED",
            "reason": "MUSIC_OR_VOICE_OR_PROFILE_MISSING",
            "voice": str(voice) if voice else "",
            "music": str(music),
            "fallback_is_pass": False,
        }

    voice_sha = _sha(voice)
    music_sha = _sha(music)
    profile_sha = _sha(profile)

    def binding_ok() -> bool:
        if not binding_path.is_file() or not derived.is_file() or not report_path.is_file():
            return False
        binding = json.loads(binding_path.read_text(encoding="utf-8-sig"))
        report = json.loads(report_path.read_text(encoding="utf-8-sig"))
        return (
            binding.get("voice_sha256") == voice_sha
            and binding.get("music_sha256") == music_sha
            and binding.get("profile_sha256") == profile_sha
            and binding.get("derived_sha256") == _sha(derived)
            and report.get("verdict") == "PASS"
            and report.get("music_pass") == "PASS"
        )

    def _deliver(reason: str, *, reused: bool) -> dict:
        digest = _sha(derived)
        return {
            "music_pass": "PASS",
            "reason": reason,
            "derived": str(derived),
            "derived_wav": str(derived),
            "derived_sha256": digest,
            "render_input_wav": str(derived),
            "render_input_sha256": digest,
            "source_music": str(music),
            "source_music_sha256": music_sha,
            "voice_audio": str(voice),
            "voice_sha256": voice_sha,
            "asset_id": selected.get("asset_id") or "",
            "music_source": selected.get("music_source"),
            "reused": reused,
            "fallback_is_pass": False,
        }

    if check_only:
        if binding_ok():
            return _deliver("BINDING_MATCH", reused=True)
        return {"music_pass": "FAIL", "reason": "MUSIC_BED_STALE_OR_MISSING", "fallback_is_pass": False}

    if binding_ok():
        return _deliver("REUSED", reused=True)

    derive = _load_derive()
    report = derive(voice=voice, music=music, out=derived, profile=profile)
    report["music_pass"] = "PASS" if report.get("verdict") == "PASS" else "FAIL"
    if report["music_pass"] == "PASS" and not report.get("reason"):
        report["reason"] = "DERIVED"
    report["voice_sha256"] = voice_sha
    report["music_sha256"] = music_sha
    report["profile_sha256"] = profile_sha
    report["source_music"] = str(music)
    report["voice_audio"] = str(voice)
    report["fallback_is_pass"] = False
    if derived.is_file() and report["music_pass"] == "PASS":
        digest = _sha(derived)
        report["derived_sha256"] = digest
        report["derived_wav"] = str(derived)
        report["render_input_wav"] = str(derived)
        report["render_input_sha256"] = digest
        report["asset_id"] = selected.get("asset_id") or ""
        report["music_source"] = selected.get("music_source")
    prod.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if report["music_pass"] != "PASS":
        if binding_path.is_file():
            binding_path.unlink()
        return report
    binding_path.write_text(
        json.dumps(
            {
                "voice_sha256": voice_sha,
                "music_sha256": music_sha,
                "profile_sha256": profile_sha,
                "derived_sha256": report["derived_sha256"],
                "derived": str(derived),
                "render_input_wav": str(derived),
                "asset_id": selected.get("asset_id") or "",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    report["reused"] = False
    return report


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workspace", type=Path, required=True)
    ap.add_argument("--brief", type=Path, required=True)
    ap.add_argument("--profile", type=Path)
    ap.add_argument("--check-only", action="store_true")
    args = ap.parse_args()
    profile = args.profile
    if profile is None:
        profile = Path(__file__).resolve().parent.parent / "runtime" / "narration-short-v1-audio-mix-profile.yaml"
    result = ensure_music_bed(
        workspace=args.workspace,
        brief_path=args.brief,
        profile=profile.resolve(),
        check_only=args.check_only,
    )
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result.get("music_pass") in {"PASS", "SKIPPED"} else 2


if __name__ == "__main__":
    raise SystemExit(main())

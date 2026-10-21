#!/usr/bin/env python3
"""AUD-01 R3: shared-library asset_id must resolve, and PASS must name the render WAV."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "payload" / "video-workflow" / "tools"
PROFILE = ROOT / "payload" / "video-workflow" / "runtime" / "narration-short-v1-audio-mix-profile.yaml"
TMP = Path(__file__).resolve().parent / ".tmp-aud01-r3"
sys.path.insert(0, str(TOOLS))
sys.path.insert(0, str(TOOLS / "lib"))

_spec = importlib.util.spec_from_file_location("ensure_music_bed_mod", TOOLS / "ensure-music-bed.py")
assert _spec and _spec.loader
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
ensure_music_bed = _mod.ensure_music_bed

PASS = 0
FAIL = 0


def check(cond: bool, name: str) -> None:
    global PASS, FAIL
    print(("[PASS] " if cond else "[FAIL] ") + name)
    if cond:
        PASS += 1
    else:
        FAIL += 1


def tone(path: Path, lufs: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["ffmpeg", "-y", "-hide_banner", "-f", "lavfi", "-i", "sine=frequency=330:duration=4", "-af", f"loudnorm=I={lufs}:TP=-3:LRA=7", str(path)],
        check=True,
        capture_output=True,
    )


def workspace() -> Path:
    if TMP.exists():
        shutil.rmtree(TMP)
    root = TMP / "libroot"
    catalog = root / "catalog"
    runtime = TMP / "ws" / "video-workflow" / "runtime"
    prod = TMP / "ws" / "video-workflow" / "production"
    catalog.mkdir(parents=True)
    runtime.mkdir(parents=True)
    prod.mkdir(parents=True)
    tone(TMP / "voice.wav", "-20")
    tone(root / "bed.wav", "-36")
    tone(TMP / "other.wav", "-28")
    (catalog / "music.yaml").write_text(
        "schema_version: 1\nassets:\n  - asset_id: music-r3-ready\n    path: bed.wav\n    status: READY\n",
        encoding="utf-8",
    )
    (runtime / "shared-asset-library-config.yaml").write_text(
        f'shared_asset_root: "{root.as_posix()}"\ncatalog:\n  music: catalog/music.yaml\n',
        encoding="utf-8",
    )
    return TMP / "ws"


def contract_workspace(name: str, brief_text: str) -> Path:
    """Copy the real preparation scripts and run them as PowerShell, not as a Python call."""
    payload = ROOT / "payload"
    ws = TMP / name
    if ws.exists():
        shutil.rmtree(ws)
    prod = ws / "video-workflow" / "production"
    runtime = ws / "video-workflow" / "runtime"
    tpl = ws / "video-workflow" / "templates"
    prod.mkdir(parents=True)
    runtime.mkdir()
    tpl.mkdir()
    shutil.copytree(TOOLS, ws / "video-workflow" / "tools")
    shutil.copy(PROFILE, runtime / PROFILE.name)
    for item in ("subtitle-external-ass-style-baseline.v1.json", "subtitle-series-style-registry.v1.json"):
        shutil.copy(payload / "video-workflow" / "templates" / item, tpl / item)
    (prod / "brief.yaml").write_text(brief_text, encoding="utf-8")
    return ws


def powershell_orchestration() -> None:
    fixture = (ROOT / "tests" / "fixtures" / "brief-final-render-contract" / "native-drt-brief.yaml").read_text(encoding="utf-8")
    voice = json.dumps(str((TMP / "voice.wav").resolve()))
    library = (TMP / "libroot").resolve().as_posix()
    selected = fixture.replace("  subtitles: true\n", "  subtitles: true\n  background_music: true\n", 1)
    selected += "\nassets:\n  voice:\n    path: " + voice + "\n  music:\n    asset_id: music-r3-ready\n"
    ws = contract_workspace("ps-asset", selected)
    (ws / "video-workflow" / "runtime" / "shared-asset-library-config.yaml").write_text(
        f'shared_asset_root: "{library}"\ncatalog:\n  music: catalog/music.yaml\n',
        encoding="utf-8",
    )
    prep = subprocess.run(
        ["powershell", "-NoProfile", "-File", str(ws / "video-workflow" / "tools" / "invoke-production-preparation-contract.ps1"), "-WorkspaceRoot", str(ws)],
        capture_output=True,
        text=True,
    )
    result_path = ws / "video-workflow" / "production" / "preparation-contract-result.json"
    result = json.loads(result_path.read_text(encoding="utf-8-sig")) if result_path.is_file() else {}
    render = Path(str(result.get("render_input_wav") or ""))
    digest = hashlib.sha256(render.read_bytes()).hexdigest() if render.is_file() else ""
    check(
        prep.returncode == 0 and result.get("music_pass") == "PASS" and render.is_file() and result.get("render_input_sha256") == digest,
        f"PowerShell prep delivers render WAV path and SHA256 ({prep.returncode} {result.get('music_pass')})",
    )
    check(render.name == "derived-music-bed.wav", "PowerShell prep names the derived bed, not the library file")

    pending_text = fixture.replace("  subtitles: true\n", "  subtitles: true\n  background_music: true\n", 1)
    pending_ws = contract_workspace("ps-pending", pending_text)
    pending = subprocess.run(
        ["powershell", "-NoProfile", "-File", str(pending_ws / "video-workflow" / "tools" / "invoke-production-preparation-contract.ps1"), "-WorkspaceRoot", str(pending_ws)],
        capture_output=True,
        text=True,
    )
    pending_doc = json.loads((pending_ws / "video-workflow" / "production" / "preparation-contract-result.json").read_text(encoding="utf-8-sig"))
    check(
        pending.returncode == 2 and pending_doc.get("music_pass") == "PENDING" and pending_doc.get("render_preparation_contract") == "PENDING" and not pending_doc.get("render_input_wav"),
        f"PowerShell prep leaves unselected music PENDING ({pending.returncode} {pending_doc.get('music_pass')})",
    )


def brief(ws: Path, text: str) -> Path:
    path = ws / "video-workflow" / "production" / "brief.yaml"
    path.write_text(text, encoding="utf-8")
    return path


def main() -> int:
    ws = workspace()
    voice = json.dumps(str(TMP / "voice.wav"))
    other = json.dumps(str(TMP / "other.wav"))
    base = "version: 1\nfeatures:\n  background_music: true\nassets:\n  voice:\n    path: " + voice + "\n"

    pending = ensure_music_bed(workspace=ws, brief_path=brief(ws, base + "  music:\n    path: \"\"\n    asset_id: \"\"\n"), profile=PROFILE, check_only=False)
    check(pending.get("music_pass") == "PENDING", f"music requested but not selected is PENDING ({pending.get('music_pass')})")

    missing = ensure_music_bed(
        workspace=ws,
        brief_path=brief(ws, base + "  music:\n    asset_id: does-not-exist\n"),
        profile=PROFILE,
        check_only=False,
    )
    check(missing.get("music_pass") == "FAIL" and missing.get("reason") == "MUSIC_ASSET_UNRESOLVED", f"unknown asset_id fails ({missing.get('reason')})")

    conflict = ensure_music_bed(
        workspace=ws,
        brief_path=brief(ws, base + "  music:\n    path: " + other + "\n    asset_id: music-r3-ready\n"),
        profile=PROFILE,
        check_only=False,
    )
    check(conflict.get("reason") == "MUSIC_PATH_ASSET_ID_CONFLICT", f"path/asset_id conflict rejected ({conflict.get('reason')})")

    got = ensure_music_bed(
        workspace=ws,
        brief_path=brief(ws, base + "  music:\n    asset_id: music-r3-ready\n"),
        profile=PROFILE,
        check_only=False,
    )
    derived = Path(str(got.get("render_input_wav") or ""))
    check(got.get("music_pass") == "PASS" and got.get("music_source") == "asset_id", f"asset_id resolves and derives ({got.get('music_pass')} {got.get('reason')})")
    check(derived.is_file() and got.get("render_input_sha256") == __import__("hashlib").sha256(derived.read_bytes()).hexdigest(), "PASS names the render WAV and its SHA256")
    check(got.get("render_input_wav") != str((TMP / "libroot" / "bed.wav").resolve()), "render input is the derived WAV, not the library file")

    disabled = ensure_music_bed(
        workspace=ws,
        brief_path=brief(ws, "version: 1\nfeatures:\n  background_music: false\n"),
        profile=PROFILE,
        check_only=False,
    )
    check(disabled.get("music_pass") == "SKIPPED", "background music disabled stays SKIPPED")
    powershell_orchestration()
    print(f"Results: {PASS} passed, {FAIL} failed")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

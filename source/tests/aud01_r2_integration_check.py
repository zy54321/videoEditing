#!/usr/bin/env python3
"""AUD-01 R2: render-prep must derive the music bed and drop a stale PASS."""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAYLOAD = ROOT / "payload"
TOOLS = PAYLOAD / "video-workflow" / "tools"
PROFILE = PAYLOAD / "video-workflow" / "runtime" / "narration-short-v1-audio-mix-profile.yaml"
FIX = Path(__file__).resolve().parent / "fixtures" / "brief-final-render-contract" / "native-drt-brief.yaml"
TMP = Path(__file__).resolve().parent / ".tmp-aud01-r2"
LISTEN = Path(r"C:\Users\the_z\Desktop\AUD01_listen")
sys.path.insert(0, str(TOOLS / "lib"))

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
        ["ffmpeg", "-y", "-hide_banner", "-f", "lavfi", "-i", "sine=frequency=220:duration=6", "-af", f"loudnorm=I={lufs}:TP=-3:LRA=7", str(path)],
        check=True,
        capture_output=True,
    )


def workspace(name: str) -> Path:
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
        shutil.copy(PAYLOAD / "video-workflow" / "templates" / item, tpl / item)
    return ws


def write_brief(ws: Path, voice: Path, music: Path | None) -> Path:
    text = FIX.read_text(encoding="utf-8")
    extra = "\nassets:\n  voice:\n    path: " + json.dumps(str(voice)) + "\n"
    if music is not None:
        extra += "  music:\n    path: " + json.dumps(str(music)) + "\n"
    extra += "features:\n  background_music: true\n"
    # The fixture already has a features block. Append assets only.
    brief = ws / "video-workflow" / "production" / "brief.yaml"
    brief.write_text(text + "\nassets:\n  voice:\n    path: " + json.dumps(str(voice)) + "\n  music:\n    path: " + json.dumps(str(music or "")) + "\n", encoding="utf-8")
    return brief


def run_prep(ws: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["powershell", "-NoProfile", "-File", str(ws / "video-workflow" / "tools" / "invoke-production-preparation-contract.ps1"), "-WorkspaceRoot", str(ws)],
        capture_output=True,
        text=True,
    )


def main() -> int:
    if TMP.exists():
        shutil.rmtree(TMP)
    TMP.mkdir()
    voice = TMP / "voice.wav"
    weak = TMP / "weak.wav"
    tone(voice, "-20")
    tone(weak, "-40")
    ws = workspace("prep")
    write_brief(ws, voice, weak)
    first = run_prep(ws)
    result = json.loads((ws / "video-workflow" / "production" / "preparation-contract-result.json").read_text(encoding="utf-8-sig"))
    check(first.returncode == 0 and result.get("music_pass") == "PASS", f"prep derives music ({first.returncode} {result.get('music_pass')} {first.stdout[-240:]})")
    report = json.loads((ws / "video-workflow" / "production" / "music-bed-derivation-report.json").read_text(encoding="utf-8"))
    gap = None
    if report.get("derived_measurement") and report.get("voice_measurement"):
        gap = float(report["voice_measurement"]["integrated_lufs"]) - float(report["derived_measurement"]["integrated_lufs"])
    check(report.get("verdict") == "PASS" and gap is not None and abs(gap - 14) <= 2, f"derived gap {gap}")
    derived = ws / "video-workflow" / "production" / "derived-music-bed.wav"
    sha_before = derived.read_bytes()
    second = run_prep(ws)
    check(second.returncode == 0 and derived.read_bytes() == sha_before, "second prep reuses derived audio")

    tone(voice, "-16")
    check_only = subprocess.run(
        ["powershell", "-NoProfile", "-File", str(ws / "video-workflow" / "tools" / "invoke-music-bed-derivation.ps1"), "-WorkspaceRoot", str(ws), "-CheckOnly"],
        capture_output=True,
        text=True,
    )
    check(check_only.returncode != 0 and "MUSIC_BED_STALE" in check_only.stdout, f"changed voice invalidates PASS ({check_only.stdout.strip()})")

    missing = workspace("missing")
    write_brief(missing, voice, missing / "no-such-music.wav")
    failed = run_prep(missing)
    failed_doc = json.loads((missing / "video-workflow" / "production" / "preparation-contract-result.json").read_text(encoding="utf-8-sig"))
    check(failed.returncode != 0 and failed_doc.get("render_preparation_contract") == "FAIL", f"failed derive blocks prep ({failed_doc.get('render_preparation_contract')})")

    plain = workspace("nomusic")
    brief = plain / "video-workflow" / "production" / "brief.yaml"
    brief.write_text(FIX.read_text(encoding="utf-8"), encoding="utf-8")
    skipped = run_prep(plain)
    skipped_doc = json.loads((plain / "video-workflow" / "production" / "preparation-contract-result.json").read_text(encoding="utf-8-sig"))
    check(skipped.returncode == 0 and skipped_doc.get("music_pass") == "SKIPPED", f"script brief without music still passes ({skipped_doc.get('music_pass')})")

    from audio_loudness_qa import judge_loudness, judge_music_gap, load_loudness_profile

    profile = load_loudness_profile(PROFILE)
    check(
        judge_loudness(-16.0, -1.4, profile, has_audio=True) == "PASS"
        and judge_music_gap(-20.0, -40.0) == "MUSIC_TOO_WEAK",
        "integrated PASS is not a music-gap PASS",
    )

    LISTEN.mkdir(exist_ok=True)
    listen_voice = LISTEN / "voice.wav"
    tone(listen_voice, "-20")
    for gap_lu, name in ((14, "minus_14LU"), (9, "minus_9LU")):
        music = LISTEN / f"music_src_{name}.wav"
        tone(music, "-18")
        custom = LISTEN / f"profile_{name}.yaml"
        text = PROFILE.read_text(encoding="utf-8")
        text = text.replace("music_below_voice_lu: 14", f"music_below_voice_lu: {gap_lu}", 1)
        custom.write_text(text, encoding="utf-8")
        out = LISTEN / f"derived_{name}.wav"
        proc = subprocess.run(
            [sys.executable, str(TOOLS / "derive-music-bed.py"), "--voice", str(listen_voice), "--music", str(music), "--out", str(out), "--profile", str(custom), "--report", str(LISTEN / f"report_{name}.json")],
            capture_output=True,
            text=True,
        )
        mix = LISTEN / f"AUD01_listen_{name}.wav"
        subprocess.run(
            ["ffmpeg", "-y", "-hide_banner", "-i", str(listen_voice), "-i", str(out), "-filter_complex", "[0:a][1:a]amix=inputs=2:duration=first:dropout_transition=0", str(mix)],
            check=True,
            capture_output=True,
        )
        rep = json.loads((LISTEN / f"report_{name}.json").read_text(encoding="utf-8"))
        measured = None
        if rep.get("voice_measurement") and rep.get("derived_measurement"):
            measured = float(rep["voice_measurement"]["integrated_lufs"]) - float(rep["derived_measurement"]["integrated_lufs"])
        check(proc.returncode == 0 and measured is not None and abs(measured - gap_lu) <= 2, f"listen sample {name} gap {measured}")
    print(f"Results: {PASS} passed, {FAIL} failed")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

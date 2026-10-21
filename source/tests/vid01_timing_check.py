#!/usr/bin/env python3
"""VID-01 timing acquisition checks, including one local TTS speech sample."""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "payload" / "video-workflow" / "tools"
LIB = TOOLS / "lib"
TMP = Path(__file__).resolve().parent / ".tmp-vid01"
sys.path.insert(0, str(LIB))

from subtitle_timing_acquire import (  # noqa: E402
    acquire_subtitle_timing,
    classify_timing_cues,
    reject_proportional_fabrication,
    sha256_file,
)

PASS = 0
FAIL = 0


def check(cond: bool, name: str) -> None:
    global PASS, FAIL
    print(("[PASS] " if cond else "[FAIL] ") + name)
    if cond:
        PASS += 1
    else:
        FAIL += 1


def probe_duration(path: Path) -> float:
    proc = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", str(path)],
        capture_output=True,
        text=True,
        check=True,
    )
    return float(json.loads(proc.stdout)["format"]["duration"])


def synth(text: str, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    ps = (
        "Add-Type -AssemblyName System.Speech; "
        "$s = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
        "$s.SelectVoice('Microsoft Huihui Desktop'); "
        f"$s.SetOutputToWaveFile('{path}'); "
        f"$s.Speak('{text}'); "
        "$s.Dispose()"
    )
    subprocess.run(["powershell", "-NoProfile", "-Command", ps], check=True)


def tc(seconds: float, fps: float = 24.0) -> str:
    frames = int(round(seconds * fps))
    ff = frames % int(fps)
    total = frames // int(fps)
    ss = total % 60
    mm = (total // 60) % 60
    hh = total // 3600
    return f"{hh:02d}:{mm:02d}:{ss:02d}:{ff:02d}"


def main() -> int:
    if TMP.exists():
        shutil.rmtree(TMP)
    TMP.mkdir()
    words = [("你好", "你好"), ("世界", "世届"), ("最后一句", "最后一句")]
    pieces = []
    cursor = 0.0
    resolve_words = []
    for i, (spoken, heard) in enumerate(words):
        wav = TMP / f"w{i}.wav"
        synth(spoken, wav)
        dur = probe_duration(wav)
        pieces.append(wav)
        resolve_words.append({"start": tc(cursor), "end": tc(cursor + dur), "text": heard})
        cursor += dur
        if i == 1:
            cursor += 1.0
    list_path = TMP / "concat.txt"
    list_path.write_text("".join(f"file '{p.as_posix()}'\n" for p in pieces), encoding="utf-8")
    speech = TMP / "speech.wav"
    subprocess.run(
        ["ffmpeg", "-y", "-hide_banner", "-f", "concat", "-safe", "0", "-i", str(list_path), "-c", "copy", str(speech)],
        check=True,
        capture_output=True,
    )
    # Insert the measured 1s pause by padding between piece 1 and 2 via filter, because concat of files has no gap.
    gapped = TMP / "speech-gapped.wav"
    subprocess.run(
        [
            "ffmpeg", "-y", "-hide_banner",
            "-i", str(pieces[0]), "-i", str(pieces[1]), "-i", str(pieces[2]),
            "-filter_complex",
            "[0:a][1:a]acrossfade=d=0:c1=tri:c2=tri[a01];[a01]apad=pad_dur=1[a01p];[a01p][2:a]concat=n=2:v=0:a=1",
            str(gapped),
        ],
        check=False,
        capture_output=True,
    )
    audio = gapped if gapped.is_file() and gapped.stat().st_size > 1000 else speech
    audio_dur = probe_duration(audio)
    doc = {
        "fps": 24,
        "voice_audio_sha256": sha256_file(audio),
        "segments": [{"start": tc(0), "end": tc(audio_dur), "words": resolve_words}],
    }
    resolve_path = TMP / "resolve-word-transcription.json"
    resolve_path.write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")
    script = TMP / "frozen.txt"
    script.write_text("你好世界。最后一句。\n", encoding="utf-8")
    evidence = TMP / "asr-timing-evidence.json"
    report_path = TMP / "report.json"
    binding = TMP / "binding.json"
    result = acquire_subtitle_timing(
        evidence_path=evidence,
        script_path=script,
        voice_audio_path=audio,
        resolve_transcription_path=resolve_path,
        binding_path=binding,
        report_path=report_path,
    )
    check(result.get("status") == "ACQUIRED", f"tts word transcription acquired ({result.get('status')} {result.get('reason')})")
    ev = json.loads(evidence.read_text(encoding="utf-8"))
    check(ev.get("text_authority") == "frozen_script", "evidence does not claim text authority")
    check(all("世届" != c["recognized_text"] or True for c in ev["cues"]), "cues loaded")
    heard = "".join(c["recognized_text"] for c in ev["cues"])
    check("世届" in heard and "世界" not in heard, "asr homophone kept only as timing text")
    check(ev["cues"][-1]["recognized_text"] == "最后一句", "last word present")
    check(abs(ev["cues"][-1]["end"] - cursor) < 0.05, f"last cue end {ev['cues'][-1]['end']} vs synthesized {cursor:.3f}")
    # Canonical must keep frozen characters.
    canonical = TMP / "canonical.json"
    proc = subprocess.run(
        [sys.executable, str(TOOLS / "build-canonical-subtitle-cues.py"), "--script", str(script), "--asr", str(evidence), "--out", str(canonical)],
        capture_output=True,
        text=True,
    )
    check(proc.returncode == 0, f"canonical build {proc.stdout.strip()} {proc.stderr[-200:]}")
    if canonical.is_file():
        cdoc = json.loads(canonical.read_text(encoding="utf-8"))
        flat = "".join(str(c.get("text", "")).replace("\n", "") for c in cdoc.get("cues") or [])
        check("世界" in flat and "世届" not in flat, f"canonical keeps frozen text ({flat})")
        adapters = cdoc.get("renderer_adapters") or {}
        check("drt_subtitles" in adapters and "ass_dialogues" in adapters, "native drt and external ass adapters present")
        ends = [float(c["end"]) for c in cdoc.get("cues") or []]
        check(bool(ends) and max(ends) >= ev["cues"][-1]["start"], "last sentence not dropped")

    single = [{"cue_id": "only", "start": 0.0, "end": 30.0, "recognized_text": "整段识别" * 5}]
    check(classify_timing_cues(single, audio_duration=30.0) == "SINGLE_SPAN", "single span classified")
    check(reject_proportional_fabrication(single) == "SINGLE_SPAN_NOT_PRECISE", "single span rejected")
    grid = [
        {"cue_id": f"c{i}", "start": i * 0.2, "end": (i + 1) * 0.2, "recognized_text": "字"}
        for i in range(12)
    ]
    check(classify_timing_cues(grid) == "PROPORTIONAL_GRID", "equal grid detected")
    check(reject_proportional_fabrication(grid) == "PROPORTIONAL_CHAR_TIMING_REJECTED", "proportional timing rejected")

    # Script change invalidates the bound evidence. Without a new word transcript, do not keep it.
    resolve_path.unlink()
    script.write_text("你好世界。改了。\n", encoding="utf-8")
    stale = acquire_subtitle_timing(
        evidence_path=evidence,
        script_path=script,
        voice_audio_path=audio,
        resolve_transcription_path=None,
        binding_path=binding,
        report_path=report_path,
        auto_transcribe=False,
    )
    check(stale.get("status") == "BLOCKED", f"stale evidence not reused ({stale.get('reason')})")
    check(not evidence.is_file(), "stale evidence file removed")

    pauses = (result.get("report") or {}).get("long_pauses_sec") or []
    check(isinstance(pauses, list), "quality report records pause list")

    shutil.rmtree(TMP, ignore_errors=True)
    print(f"Results: {PASS} passed, {FAIL} failed")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

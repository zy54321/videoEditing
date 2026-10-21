#!/usr/bin/env python3
"""VID-01 R2: formal acquire from WAV+TXT, live Resolve separated from the orchestration stub."""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "payload" / "video-workflow" / "tools"
LIB = TOOLS / "lib"
TMP = Path(__file__).resolve().parent / ".tmp-vid01-r2"
sys.path.insert(0, str(LIB))

from subtitle_timing_acquire import acquire_subtitle_timing  # noqa: E402

PASS = 0
FAIL = 0
LIVE: dict = {}


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


def main() -> int:
    if TMP.exists():
        shutil.rmtree(TMP)
    prod = TMP / "video-workflow" / "production"
    prod.mkdir(parents=True)
    words = ["你好", "世界", "最后一句"]
    pieces = []
    cursor = 0.0
    measured = []
    for i, word in enumerate(words):
        wav = TMP / f"w{i}.wav"
        synth(word, wav)
        dur = probe_duration(wav)
        measured.append({"text": word if word != "世界" else "世届", "start": round(cursor, 3), "end": round(cursor + dur, 3)})
        pieces.append(wav)
        cursor += dur
    speech = TMP / "narration.wav"
    subprocess.run(
        ["ffmpeg", "-y", "-hide_banner", *[arg for p in pieces for arg in ("-i", str(p))], "-filter_complex", f"concat=n={len(pieces)}:v=0:a=1", str(speech)],
        check=True,
        capture_output=True,
    )
    script = prod / "frozen.txt"
    script.write_text("你好世界。\n最后一句。\n", encoding="utf-8")
    evidence = prod / "asr-timing-evidence.json"
    live = acquire_subtitle_timing(
        evidence_path=evidence,
        script_path=script,
        voice_audio_path=speech,
        binding_path=prod / "subtitle-timing-binding.json",
        report_path=prod / "subtitle-timing-quality-report.json",
        auto_transcribe=True,
    )
    LIVE.update({"status": live.get("status"), "reason": live.get("reason"), "detail": live.get("detail"), "live_resolve": live.get("live_resolve")})
    (TMP / "live-resolve-result.json").write_text(json.dumps(LIVE, ensure_ascii=False, indent=2), encoding="utf-8")
    print("LIVE", json.dumps(LIVE, ensure_ascii=False))
    check(live.get("reason") != "WORD_TIMING_PROVIDER_UNAVAILABLE" or live.get("live_resolve") is False, "missing words attempt Resolve instead of stopping at absent JSON")
    no_preset = not (prod / "resolve-word-transcription.json").exists() or live.get("live_resolve") is True or live.get("status") == "BLOCKED"
    check(no_preset, "test did not start from a hand-written ASR JSON")

    for path in (evidence, prod / "resolve-word-transcription.json", prod / "subtitle-word-alignment.json"):
        if path.exists():
            path.unlink()

    import resolve_word_transcribe as provider

    def fake(voice: Path, out: Path, allow_project_switch: bool = False) -> dict:
        import hashlib
        digest = hashlib.sha256(voice.read_bytes()).hexdigest()
        doc = {
            "fps": 24,
            "voice_audio_sha256": digest,
            "segments": [{"words": [{"text": w["text"], "start": w["start"], "end": w["end"]} for w in measured]}],
        }
        out.write_text(json.dumps(doc), encoding="utf-8")
        return {"status": "ACQUIRED", "document": doc, "live_resolve": False, "simulated": True}

    provider.transcribe_voice_to_word_json = fake  # type: ignore[method-assign]
    orch = acquire_subtitle_timing(
        evidence_path=evidence,
        script_path=script,
        voice_audio_path=speech,
        binding_path=prod / "subtitle-timing-binding.json",
        report_path=prod / "subtitle-timing-quality-report.json",
        auto_transcribe=True,
    )
    check(orch.get("status") == "ACQUIRED", f"orchestration acquire ({orch.get('status')} {orch.get('reason')})")
    align = json.loads((prod / "subtitle-word-alignment.json").read_text(encoding="utf-8"))
    check(align.get("status") == "OK", f"monotonic alignment OK ({align.get('problems')})")
    check(align.get("proportional_char_timing") is False, "alignment does not claim proportional timing")
    check(align["cues"][-1]["text"].startswith("最后一句"), "last sentence aligned")
    spoken_end = align["cues"][-1]["end"]
    check(abs(spoken_end - measured[-1]["end"]) < 0.05, f"last sentence end {spoken_end} follows last word {measured[-1]['end']}")
    canonical = prod / "canonical-subtitle-cues.json"
    proc = subprocess.run(
        [sys.executable, str(TOOLS / "build-canonical-subtitle-cues.py"), "--script", str(script), "--asr", str(evidence), "--out", str(canonical)],
        capture_output=True,
        text=True,
    )
    check(proc.returncode == 0, "canonical build")
    applied = subprocess.run(
        [sys.executable, str(TOOLS / "apply-frozen-word-alignment.py"), "--canonical", str(canonical), "--alignment", str(prod / "subtitle-word-alignment.json")],
        capture_output=True,
        text=True,
    )
    check(applied.returncode == 0, f"apply bounds {applied.stdout.strip()}")
    doc = json.loads(canonical.read_text(encoding="utf-8"))
    flat = "".join(str(c.get("text") or "").replace("\n", "") for c in doc["cues"])
    check("世界" in flat and "世届" not in flat, "canonical keeps frozen text")
    adapters = doc.get("renderer_adapters") or {}
    check("drt_subtitles" in adapters and "ass_dialogues" in adapters, "DRT and ASS adapters present")
    ends = [float(c["end"]) for c in doc["cues"]]
    check(ends and abs(max(ends) - float(align["cues"][-1]["display_end"])) < 0.05, "canonical end uses word-boundary display end")

    import hashlib
    bad = prod / "bad-resolve.json"
    bad.write_text(
        json.dumps(
            {
                "voice_audio_sha256": hashlib.sha256(speech.read_bytes()).hexdigest(),
                "segments": [{"words": [{"text": "无关", "start": "00:00:00:00", "end": "00:00:00:12"}]}],
            }
        ),
        encoding="utf-8",
    )
    if evidence.exists():
        evidence.unlink()
    blocked = acquire_subtitle_timing(
        evidence_path=evidence,
        script_path=script,
        voice_audio_path=speech,
        resolve_transcription_path=bad,
        auto_transcribe=False,
    )
    check(blocked.get("status") == "BLOCKED" and blocked.get("reason") == "ALIGNMENT_INCOMPLETE", f"incomplete words blocked ({blocked.get('reason')})")
    print(f"Results: {PASS} passed, {FAIL} failed")
    print("LIVE_JSON", TMP / "live-resolve-result.json")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

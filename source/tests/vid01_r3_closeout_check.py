#!/usr/bin/env python3
"""VID-01 R3: evidence identity binding and scratch-project isolation."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB = ROOT / "payload" / "video-workflow" / "tools" / "lib"
sys.path.insert(0, str(LIB))

from resolve_word_transcribe import (  # noqa: E402
    SCRATCH_PROJECT,
    prepare_transcription_project,
    restore_previous_project,
)
from subtitle_timing_acquire import (  # noqa: E402
    acquire_subtitle_timing,
    binding_matches,
    sha256_file,
)

PASS = 0
FAIL = 0
TMP = Path(__file__).resolve().parent / ".tmp-vid01-r3"


def check(cond: bool, name: str) -> None:
    global PASS, FAIL
    print(("[PASS] " if cond else "[FAIL] ") + name)
    if cond:
        PASS += 1
    else:
        FAIL += 1


def word_evidence(path: Path) -> None:
    path.write_text(
        json.dumps(
            {"schema_version": 1, "cues": [{"cue_id": "w1", "start": 0.0, "end": 0.4, "recognized_text": "你好"}]},
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


class FakePM:
    def __init__(self, current: str, saved: list[str], *, scratch_opens: bool = True, restore_ok: bool = True):
        self.current = current
        self.saved = list(saved)
        self.scratch_opens = scratch_opens
        self.restore_ok = restore_ok
        self.calls: list[tuple[str, str]] = []

    def GetCurrentProject(self):
        return self

    def GetName(self):
        return self.current

    def GetProjectListInCurrentFolder(self):
        return list(self.saved)

    def LoadProject(self, name: str):
        self.calls.append(("load", name))
        if name == SCRATCH_PROJECT:
            if name not in self.saved:
                return None
            self.current = name
            return self
        if not self.restore_ok:
            return None
        if name not in self.saved:
            return None
        self.current = name
        return self

    def CreateProject(self, name: str):
        self.calls.append(("create", name))
        if name == SCRATCH_PROJECT and not self.scratch_opens:
            return None
        if name not in self.saved:
            self.saved.append(name)
        self.current = name
        return self

    def GetMediaPool(self):
        raise AssertionError("import path must not run in the planner test")


def main() -> int:
    if TMP.exists():
        import shutil
        shutil.rmtree(TMP)
    TMP.mkdir()
    old_wav = TMP / "old.wav"
    new_wav = TMP / "new.wav"
    old_wav.write_bytes(b"RIFF-old-voice")
    new_wav.write_bytes(b"RIFF-new-voice")
    script = TMP / "frozen.txt"
    script.write_text("你好。\n", encoding="utf-8")
    evidence = TMP / "asr-timing-evidence.json"
    binding = TMP / "binding.json"
    word_evidence(evidence)

    unbound = acquire_subtitle_timing(
        evidence_path=evidence,
        script_path=script,
        voice_audio_path=new_wav,
        binding_path=binding,
        auto_transcribe=False,
    )
    check(unbound.get("status") == "BLOCKED", f"unbound evidence is not reused ({unbound.get('reason')})")
    check(not evidence.is_file(), "unbound evidence file removed")
    check(not binding.is_file(), "unbound evidence did not receive the new WAV fingerprint")

    word_evidence(evidence)
    binding.write_text(
        json.dumps(
            {
                "script_sha256": sha256_file(script),
                "voice_audio_sha256": None,
                "evidence_sha256": sha256_file(evidence),
            }
        ),
        encoding="utf-8",
    )
    missing_voice = binding_matches(
        json.loads(binding.read_text(encoding="utf-8")),
        script_sha256=sha256_file(script),
        voice_sha256=sha256_file(new_wav),
        evidence_sha256=sha256_file(evidence),
    )
    check(missing_voice is False, "binding without voice SHA256 does not match")
    stale = acquire_subtitle_timing(
        evidence_path=evidence,
        script_path=script,
        voice_audio_path=new_wav,
        binding_path=binding,
        auto_transcribe=False,
    )
    check(stale.get("status") == "BLOCKED" and not evidence.is_file(), "incomplete binding does not keep the evidence")

    word_evidence(evidence)
    binding.write_text(
        json.dumps(
            {
                "script_sha256": sha256_file(script),
                "voice_audio_sha256": sha256_file(old_wav),
                "evidence_sha256": sha256_file(evidence),
            }
        ),
        encoding="utf-8",
    )
    changed = acquire_subtitle_timing(
        evidence_path=evidence,
        script_path=script,
        voice_audio_path=new_wav,
        binding_path=binding,
        auto_transcribe=False,
    )
    check(changed.get("status") == "BLOCKED" and not evidence.is_file(), "new WAV invalidates old word evidence")

    old_json = TMP / "resolve-word-transcription.json"
    old_json.write_text(
        json.dumps(
            {
                "voice_audio_sha256": sha256_file(old_wav),
                "segments": [{"words": [{"text": "你好", "start": 0.0, "end": 0.4}]}],
            }
        ),
        encoding="utf-8",
    )
    if evidence.exists():
        evidence.unlink()
    mismatched = acquire_subtitle_timing(
        evidence_path=evidence,
        script_path=script,
        voice_audio_path=new_wav,
        resolve_transcription_path=old_json,
        binding_path=binding,
        auto_transcribe=False,
    )
    check(mismatched.get("status") == "BLOCKED", f"old Resolve JSON is not applied to the new WAV ({mismatched.get('reason')})")
    check(not evidence.is_file(), "mismatched JSON did not become the evidence")

    import resolve_word_transcribe as provider

    calls = {"n": 0}

    def fake(voice: Path, out: Path, allow_project_switch: bool = False) -> dict:
        calls["n"] += 1
        digest = sha256_file(voice)
        doc = {
            "voice_audio_sha256": digest,
            "segments": [{"words": [{"text": "你好", "start": 0.1, "end": 0.5}]}],
        }
        out.write_text(json.dumps(doc), encoding="utf-8")
        return {"status": "ACQUIRED", "document": doc, "live_resolve": False}

    provider.transcribe_voice_to_word_json = fake  # type: ignore[method-assign]
    if evidence.exists():
        evidence.unlink()
    refreshed = acquire_subtitle_timing(
        evidence_path=evidence,
        script_path=script,
        voice_audio_path=new_wav,
        binding_path=binding,
        auto_transcribe=True,
    )
    check(calls["n"] == 1 and refreshed.get("status") == "ACQUIRED", f"changed audio re-calls the provider ({refreshed.get('status')})")
    rebound = json.loads(binding.read_text(encoding="utf-8"))
    check(rebound.get("voice_audio_sha256") == sha256_file(new_wav), "new binding stores the new WAV SHA256")
    again = acquire_subtitle_timing(
        evidence_path=evidence,
        script_path=script,
        voice_audio_path=new_wav,
        binding_path=binding,
        auto_transcribe=True,
    )
    check(again.get("status") == "SKIPPED_EXISTING" and calls["n"] == 1, "matching binding skips a second transcription")

    saved = FakePM("Cut", ["Cut"])
    opened = prepare_transcription_project(saved, allow_project_switch=True)
    check(opened.get("ok") is True and saved.current == SCRATCH_PROJECT, "saved project opens scratch")
    check(restore_previous_project(saved, "Cut") and saved.current == "Cut", "saved project restores")

    failed = FakePM("Cut", ["Cut"], scratch_opens=False)
    blocked = prepare_transcription_project(failed, allow_project_switch=True)
    check(
        blocked.get("ok") is False
        and blocked.get("reason") == "RESOLVE_SCRATCH_PROJECT_UNAVAILABLE"
        and failed.current == "Cut",
        "scratch failure stays on the current project and does not import",
    )

    untitled = FakePM("Untitled Project", ["Cut", "N20261021"])
    stopped = prepare_transcription_project(untitled, allow_project_switch=True)
    check(
        stopped.get("reason") == "UNSAVED_PROJECT_NOT_RESTORABLE" and untitled.calls == [] and untitled.current == "Untitled Project",
        "unsaved project is not switched",
    )

    other = FakePM("N03", ["N03"], scratch_opens=True)
    refused = prepare_transcription_project(other, allow_project_switch=True)
    check(refused.get("ok") is True and other.current == SCRATCH_PROJECT, "a non-episode name is still isolated from import")
    other.restore_ok = False
    check(restore_previous_project(other, "N03") is False, "restore failure is reported")

    class MismatchedRestore(FakePM):
        def LoadProject(self, name: str):
            self.calls.append(("load", name))
            self.current = "SomeOtherProject"
            return self

    mismatched_restore = MismatchedRestore("N03", ["N03"])
    check(
        restore_previous_project(mismatched_restore, "N03") is False and mismatched_restore.current != "N03",
        "a restored project with the wrong name is not accepted",
    )

    live = {"status": "NOT_RUN"}
    try:
        import os
        os.environ.setdefault("RESOLVE_SCRIPT_LIB", r"D:\soft\davinci\app\fusionscript.dll")
        module_dir = r"C:\ProgramData\Blackmagic Design\DaVinci Resolve\Support\Developer\Scripting\Modules"
        if module_dir not in sys.path:
            sys.path.insert(0, module_dir)
        import DaVinciResolveScript as dvr  # type: ignore

        resolve = dvr.scriptapp("Resolve")
        if resolve is None:
            live = {"status": "RESOLVE_NOT_RUNNING"}
        else:
            current = resolve.GetProjectManager().GetCurrentProject()
            name = str(current.GetName() or "") if current else ""
            live = {"status": "READ_ONLY", "project": name, "switched": False}
            if name != SCRATCH_PROJECT:
                live["note"] = "stopped before any project switch or import"
    except Exception as exc:  # noqa: BLE001
        live = {"status": "RESOLVE_NOT_RUNNING", "detail": str(exc)}
    (TMP / "live-resolve-probe.json").write_text(json.dumps(live, ensure_ascii=False, indent=2), encoding="utf-8")
    print("LIVE", json.dumps(live, ensure_ascii=False))
    check(live.get("switched") is not True, "live probe did not switch a Resolve project")

    print(f"Results: {PASS} passed, {FAIL} failed")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

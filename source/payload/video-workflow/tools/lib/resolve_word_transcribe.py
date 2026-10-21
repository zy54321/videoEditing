"""Call the running DaVinci Resolve scripting API for word-level transcription.

This is the same MediaPoolItem.TranscribeAudio / GetTranscription surface used
for episode N20261021. It does not modify the Resolve/MCP installation.
It refuses to import media into that episode's project.
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from typing import Any

EPISODE_ROOT = Path(r"E:\03_Media\02_Video\Davinci\Astra\2026-10-21")
SCRATCH_PROJECT = "video-workflow-timing-scratch"
UNSAVED_PROJECT_NAMES = {"", "untitled", "untitled project"}
SCRIPT_MODULE_DIR = Path(r"C:\ProgramData\Blackmagic Design\DaVinci Resolve\Support\Developer\Scripting\Modules")
FUSION_CANDIDATES = (
    Path(r"D:\soft\davinci\app\fusionscript.dll"),
    Path(r"C:\Program Files\Blackmagic Design\DaVinci Resolve\fusionscript.dll"),
)


def _project_name(project: Any) -> str:
    if project is None:
        return ""
    getter = getattr(project, "GetName", None)
    if not callable(getter):
        return ""
    return str(getter() or "")


def _project_list(pm: Any) -> list[str]:
    getter = getattr(pm, "GetProjectListInCurrentFolder", None)
    if not callable(getter):
        return []
    return [str(name) for name in (getter() or [])]


def prepare_transcription_project(pm: Any, *, allow_project_switch: bool) -> dict[str, Any]:
    """Open the scratch project or refuse. Never imports into the caller's project.

    A saved project may be left only when its name is in the current folder list,
    so LoadProject can restore it. An unsaved Untitled project stops the switch.
    Scratch open failure does not fall back to the current project.
    """
    current = pm.GetCurrentProject()
    current_name = _project_name(current)
    saved_names = _project_list(pm)
    if current_name == SCRATCH_PROJECT and current is not None:
        return {"ok": True, "project": current, "restore_name": "", "reason": None}

    unsaved = (not current_name) or current_name.casefold() in UNSAVED_PROJECT_NAMES or current_name not in saved_names
    if unsaved:
        return {
            "ok": False,
            "project": None,
            "restore_name": "",
            "reason": "UNSAVED_PROJECT_NOT_RESTORABLE",
            "detail": current_name or "untitled",
        }
    if not allow_project_switch:
        return {
            "ok": False,
            "project": None,
            "restore_name": current_name,
            "reason": "RESOLVE_SWITCH_NOT_CONFIRMED",
            "detail": current_name,
        }
    opened = pm.LoadProject(SCRATCH_PROJECT) or pm.CreateProject(SCRATCH_PROJECT)
    opened_name = _project_name(opened)
    if opened is None or opened_name != SCRATCH_PROJECT:
        return {
            "ok": False,
            "project": None,
            "restore_name": current_name,
            "reason": "RESOLVE_SCRATCH_PROJECT_UNAVAILABLE",
            "detail": current_name,
        }
    return {"ok": True, "project": opened, "restore_name": current_name, "reason": None}


def restore_previous_project(pm: Any, restore_name: str) -> bool:
    if not restore_name or restore_name == SCRATCH_PROJECT:
        return True
    try:
        restored = pm.LoadProject(restore_name)
    except Exception:
        return False
    return _project_name(restored) == restore_name


def _connect() -> tuple[Any | None, str | None]:
    if not os.environ.get("RESOLVE_SCRIPT_LIB"):
        for candidate in FUSION_CANDIDATES:
            if candidate.is_file():
                os.environ["RESOLVE_SCRIPT_LIB"] = str(candidate)
                break
    if str(SCRIPT_MODULE_DIR) not in sys.path:
        sys.path.insert(0, str(SCRIPT_MODULE_DIR))
    try:
        import DaVinciResolveScript as dvr  # type: ignore
    except Exception as exc:  # noqa: BLE001
        return None, f"RESOLVE_SCRIPT_IMPORT_FAILED: {exc}"
    try:
        resolve = dvr.scriptapp("Resolve")
    except Exception as exc:  # noqa: BLE001
        return None, f"RESOLVE_SCRIPTAPP_FAILED: {exc}"
    if resolve is None:
        return None, "RESOLVE_NOT_RUNNING"
    return resolve, None


def _normalize_transcription(raw: Any) -> dict[str, Any] | None:
    if isinstance(raw, str):
        text = raw.strip()
        if not text:
            return None
        if text.startswith("{") or text.startswith("["):
            try:
                raw = json.loads(text)
            except json.JSONDecodeError:
                return None
        else:
            return None
    if not isinstance(raw, dict):
        return None
    segments = raw.get("segments")
    if isinstance(segments, list) and any(isinstance(seg, dict) and seg.get("words") for seg in segments):
        return raw
    words = raw.get("words")
    if isinstance(words, list) and words:
        return {"segments": [{"words": words}]}
    return None


def _read_words(item: Any) -> dict[str, Any] | None:
    attempts = []
    for kwargs in ({"include_words": True}, {"includeWords": True}):
        try:
            attempts.append(item.GetTranscription(kwargs))
        except Exception:
            continue
    for arg in (True,):
        try:
            attempts.append(item.GetTranscription(arg))
        except Exception:
            continue
    try:
        attempts.append(item.GetTranscription())
    except Exception:
        pass
    getter = getattr(item, "GetClipProperty", None)
    if callable(getter):
        try:
            attempts.append(getter("Transcription"))
        except Exception:
            pass
    for raw in attempts:
        doc = _normalize_transcription(raw)
        if doc is not None:
            return doc
    return None


def transcribe_voice_to_word_json(
    voice_audio: Path,
    out_json: Path,
    *,
    allow_project_switch: bool = False,
) -> dict[str, Any]:
    """Import one WAV into the scratch project only and write Resolve word JSON."""
    voice_audio = voice_audio.resolve()
    if not voice_audio.is_file():
        return {"status": "BLOCKED", "reason": "VOICE_AUDIO_MISSING", "live_resolve": False}
    try:
        voice_audio.relative_to(EPISODE_ROOT)
        under_episode = True
    except ValueError:
        under_episode = False
    if under_episode:
        return {
            "status": "BLOCKED",
            "reason": "EPISODE_MEDIA_FORBIDDEN",
            "detail": "Refusing to transcribe episode 3 media",
            "live_resolve": False,
        }

    resolve, err = _connect()
    if resolve is None:
        return {"status": "BLOCKED", "reason": "RESOLVE_NOT_RUNNING", "detail": err, "live_resolve": False}

    pm = resolve.GetProjectManager()
    prepared = prepare_transcription_project(pm, allow_project_switch=allow_project_switch)
    if not prepared.get("ok"):
        return {
            "status": "BLOCKED",
            "reason": prepared.get("reason") or "RESOLVE_SCRATCH_PROJECT_UNAVAILABLE",
            "detail": prepared.get("detail"),
            "live_resolve": True,
            "project": prepared.get("restore_name") or "",
        }
    project = prepared["project"]
    restore_name = str(prepared.get("restore_name") or "")
    result: dict[str, Any]
    try:
        if _project_name(project) != SCRATCH_PROJECT:
            result = {
                "status": "BLOCKED",
                "reason": "RESOLVE_SCRATCH_PROJECT_UNAVAILABLE",
                "detail": "Refusing to import into a project that is not the timing scratch project",
                "live_resolve": True,
            }
            return result
        pool = project.GetMediaPool()
        root = pool.GetRootFolder()
        scratch = None
        for folder in root.GetSubFolderList() or []:
            if str(folder.GetName() or "") == "timing-scratch":
                scratch = folder
                break
        if scratch is None:
            scratch = pool.AddSubFolder(root, "timing-scratch")
        if scratch is None:
            return {"status": "BLOCKED", "reason": "RESOLVE_SCRATCH_BIN_FAILED", "live_resolve": True}
        pool.SetCurrentFolder(scratch)
        imported = pool.ImportMedia([str(voice_audio)]) or []
        if not imported:
            return {"status": "BLOCKED", "reason": "RESOLVE_IMPORT_FAILED", "live_resolve": True}
        item = imported[0]
        started = item.TranscribeAudio()
        if started is False:
            return {"status": "BLOCKED", "reason": "RESOLVE_TRANSCRIBE_REJECTED", "live_resolve": True}
        doc = None
        deadline = time.time() + 180
        while time.time() < deadline:
            doc = _read_words(item)
            if doc is not None:
                break
            time.sleep(2)
        if doc is None:
            return {
                "status": "BLOCKED",
                "reason": "RESOLVE_TRANSCRIPTION_WITHOUT_WORDS",
                "detail": "TranscribeAudio ran but GetTranscription did not return word timings. include_words was requested.",
                "live_resolve": True,
            }
        doc["source"] = "resolve_media_pool_transcribe_audio"
        doc["include_words"] = True
        doc["voice_audio"] = str(voice_audio)
        doc["voice_audio_sha256"] = _sha256(voice_audio)
        out_json.parent.mkdir(parents=True, exist_ok=True)
        out_json.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        result = {
            "status": "ACQUIRED",
            "reason": None,
            "path": str(out_json),
            "document": doc,
            "live_resolve": True,
            "project": _project_name(project),
        }
    finally:
        if restore_name and not restore_previous_project(pm, restore_name):
            return {
                "status": "BLOCKED",
                "reason": "PROJECT_RESTORE_FAILED",
                "detail": restore_name,
                "live_resolve": True,
                "project": SCRATCH_PROJECT,
            }
    return result


def _sha256(path: Path) -> str:
    import hashlib

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()

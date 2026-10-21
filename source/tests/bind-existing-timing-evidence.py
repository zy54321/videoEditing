#!/usr/bin/env python3
"""Bind a fixture's existing word cues to its narration and reviewed script.

Used by tests that already own a matching WAV and evidence file. This is not
a production trust migration.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "payload" / "video-workflow" / "tools" / "lib"))

from brief_subtitle_authority import load_brief_dict, voice_subtitle_review_pending  # noqa: E402
from subtitle_timing_acquire import sha256_file  # noqa: E402
from voice_subtitle_paths import reviewed_text_path  # noqa: E402
from voice_subtitle_review import resolve_voice_audio_path  # noqa: E402


def main() -> int:
    ws = Path(sys.argv[1]).resolve()
    prod = ws / "video-workflow" / "production"
    brief = load_brief_dict(prod / "brief.yaml")
    script = reviewed_text_path(ws) if voice_subtitle_review_pending(brief) else None
    voice = resolve_voice_audio_path(brief, ws)
    evidence = prod / "asr-timing-evidence.json"
    payload = {
        "script_sha256": sha256_file(script) if script is not None and script.is_file() else None,
        "voice_audio_sha256": sha256_file(voice) if voice is not None and voice.is_file() else None,
        "evidence_sha256": sha256_file(evidence),
    }
    (prod / "subtitle-timing-binding.json").write_text(json.dumps(payload), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

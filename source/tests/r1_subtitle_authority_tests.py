#!/usr/bin/env python3
"""R1 — Frozen Script authority, monotonic alignment, canonical cues (unit + integration)."""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
LIB = ROOT / "payload" / "video-workflow" / "tools" / "lib"
TOOLS = ROOT / "payload" / "video-workflow" / "tools"
FIX = Path(__file__).resolve().parent / "fixtures" / "r1-subtitle-authority"

if str(LIB) not in sys.path:
    sys.path.insert(0, str(LIB))

from asr_timing_evidence import load_asr_timing_evidence  # noqa: E402
from frozen_script_authority import load_frozen_script_file, normalize_frozen_script_text  # noqa: E402
from script_audio_monotonic_align import align_script_to_asr  # noqa: E402
from canonical_subtitle_cue import (  # noqa: E402
    build_canonical_subtitle_cues,
    to_ass_dialogue_lines,
    to_drt_subtitles,
)


class TestFrozenAuthority(unittest.TestCase):
    def test_asr_homophone_does_not_replace_frozen_text(self) -> None:
        script = load_frozen_script_file(FIX / "frozen-asr-homophone.txt")
        asr = load_asr_timing_evidence(FIX / "asr-homophone.json")
        result = align_script_to_asr(script.normalized_text, asr)
        self.assertFalse(result.blocked)
        merged = "".join(s.text for s in result.spans)
        self.assertIn("十件", merged)
        self.assertNotIn("实践", merged)
        self.assertEqual(merged, script.normalized_text)

    def test_layout_newline_not_timing_boundary(self) -> None:
        raw = (FIX / "frozen-layout-newline.txt").read_text(encoding="utf-8")
        norm = normalize_frozen_script_text(raw)
        self.assertNotIn("\n", norm.normalized_text)
        script = load_frozen_script_file(FIX / "frozen-layout-newline.txt")
        asr = load_asr_timing_evidence(FIX / "asr-layout-newline.json")
        result = align_script_to_asr(script.normalized_text, asr)
        self.assertFalse(result.blocked)
        # Single-clause timing: first span should not end at layout newline position
        self.assertGreaterEqual(len(result.spans), 1)
        for sp in result.spans:
            self.assertNotIn("\n", sp.text)


class TestMonotonicAlignment(unittest.TestCase):
    def test_span_times_monotonic(self) -> None:
        script = load_frozen_script_file(FIX / "frozen-asr-homophone.txt")
        asr = load_asr_timing_evidence(FIX / "asr-homophone.json")
        result = align_script_to_asr(script.normalized_text, asr)
        starts = [s.audio_start for s in result.spans]
        self.assertEqual(starts, sorted(starts))


class TestFailClosed(unittest.TestCase):
    def test_large_mismatch_blocks(self) -> None:
        script = load_frozen_script_file(FIX / "frozen-asr-homophone.txt")
        bad = {
            "schema_version": 1,
            "cues": [{"cue_id": "x", "start": 0.0, "end": 1.0, "recognized_text": "完全不同"}],
        }
        path = FIX / "_tmp_bad_asr.json"
        path.write_text(json.dumps(bad), encoding="utf-8")
        asr = load_asr_timing_evidence(path)
        result = align_script_to_asr(script.normalized_text, asr)
        path.unlink(missing_ok=True)
        self.assertTrue(result.blocked)
        self.assertIsNotNone(result.block_reason)


class TestNoGlobalProportional(unittest.TestCase):
    def test_no_whole_video_proportional_helper(self) -> None:
        import script_audio_monotonic_align as mod

        forbidden = [
            n
            for n in dir(mod)
            if "proportional" in n.lower() or "line_count" in n.lower()
        ]
        self.assertEqual(forbidden, [])


class TestRendererIndependence(unittest.TestCase):
    def test_adapters_do_not_mutate_text(self) -> None:
        from canonical_subtitle_cue import CanonicalSubtitleCue

        cues = [
            CanonicalSubtitleCue(
                cue_id="C01",
                start=0.0,
                end=1.0,
                text="测试\n行二",
                lines=("测试", "行二"),
                confidence=1.0,
                source_span_ids=("S01",),
            )
        ]
        drt = to_drt_subtitles(cues, fps=24.0)
        ass = to_ass_dialogue_lines(cues)
        self.assertIn("测试", drt[0]["text"])
        self.assertIn("行二", drt[0]["text"])
        self.assertIn(r"\N", ass[0]["text"])


@unittest.skipUnless(sys.platform == "win32", "layout engine requires Windows PowerShell")
class TestSemanticWrapIntegration(unittest.TestCase):
    def test_canonical_cues_preserve_frozen_text(self) -> None:
        script = load_frozen_script_file(FIX / "frozen-asr-homophone.txt")
        asr = load_asr_timing_evidence(FIX / "asr-homophone.json")
        cues, alignment, meta = build_canonical_subtitle_cues(script, asr, TOOLS)
        self.assertFalse(alignment.blocked)
        self.assertEqual(meta.get("status"), "OK")
        flat = "".join(c.text.replace("\n", "") for c in cues)
        self.assertEqual(flat, script.normalized_text)
        for c in cues:
            self.assertLessEqual(len(c.lines), 2)
            if len(c.lines) == 2:
                self.assertIn("\n", c.text)


if __name__ == "__main__":
    unittest.main(verbosity=2)

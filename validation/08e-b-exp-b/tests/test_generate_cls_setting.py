#!/usr/bin/env python3
"""Unit tests for dynamic CLS .setting generation."""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "helpers"))

from generate_cls_setting import (  # noqa: E402
    EmphasisSpan,
    escape_fusion_string,
    generate_from_request,
    span_indices_from_substring,
    validate_spans,
)
from parse_cls_export import parse_cls_array, parse_text_input  # noqa: E402


class TestClsGeneration(unittest.TestCase):
    def test_b00_unicode_index_matches_gui(self) -> None:
        text = "价格直接涨了 40%"
        start, end = span_indices_from_substring(text, "40%")
        self.assertEqual((start, end), (7, 9))

    def test_b10_index(self) -> None:
        text = "价格上涨了 40%"
        start, end = span_indices_from_substring(text, "40%")
        self.assertEqual((start, end), (6, 8))

    def test_b11_indices(self) -> None:
        text = "AI 让效率提升了 35%"
        self.assertEqual(span_indices_from_substring(text, "AI"), (0, 1))
        self.assertEqual(span_indices_from_substring(text, "35%"), (10, 12))

    def test_b12_indices(self) -> None:
        text = "今年增长 18%，成本下降 7%"
        self.assertEqual(span_indices_from_substring(text, "18%"), (5, 7))
        self.assertEqual(span_indices_from_substring(text, "7%"), (14, 15))

    def test_escape_quotes_and_backslash(self) -> None:
        self.assertEqual(escape_fusion_string('a"b\\c'), 'a\\"b\\\\c')

    def test_overlap_rejected(self) -> None:
        with self.assertRaises(ValueError):
            validate_spans(
                "abcd",
                [EmphasisSpan(0, 2, "strong"), EmphasisSpan(2, 3, "medium")],
            )

    def test_roundtrip_parse_b10(self) -> None:
        req = json.loads((ROOT / "cases" / "B10.request.json").read_text(encoding="utf-8"))
        setting = generate_from_request(req)
        self.assertIn("{ 102, 6, 8, Value =", setting)
        parsed = parse_cls_array(setting)
        self.assertEqual(len(parsed), 1)
        self.assertEqual(parsed[0]["first"], 6)
        self.assertEqual(parsed[0]["last"], 8)
        self.assertEqual(parse_text_input(setting), req["text"])

    def test_deterministic_b10(self) -> None:
        req = json.loads((ROOT / "cases" / "B10.request.json").read_text(encoding="utf-8"))
        a = generate_from_request(req)
        b = generate_from_request(req)
        self.assertEqual(a, b)


if __name__ == "__main__":
    unittest.main()

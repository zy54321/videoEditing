#!/usr/bin/env python3
"""Static tests for Text+ StyledTextCLS production backend (Stage 08E-B B-R2)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
PAYLOAD = REPO / "source" / "payload"
LIB = PAYLOAD / "video-workflow" / "tools" / "lib"
sys.path.insert(0, str(LIB))

from textplus_cls_setting import (  # noqa: E402
    CANONICAL_GRAPH,
    KNOWN_NON_WORKING_ROUTE,
    ClsError,
    escape_fusion_string,
    generate_from_legacy_test_request,
    generate_from_materialized_request,
    reject_unverified_cls_inputs,
    span_indices_from_substring_unique,
    spans_from_materialized_cue,
)

FONT_PROFILES = PAYLOAD / "video-workflow" / "runtime" / "textplus-font-profiles.yaml"
INSTALLER = REPO / "source" / "installer" / "init-video-workflow.ps1"

_fail = 0


def check(name: str, cond: bool, detail: str = "") -> None:
    global _fail
    if cond:
        print(f"PASS {name}")
    else:
        _fail += 1
        print(f"FAIL {name}" + (f" — {detail}" if detail else ""))


def std_typography() -> dict:
    return {
        "font_family": "Microsoft YaHei",
        "fallback_font_family": "SimSun",
        "base_font_size_px": 48,
        "emphasis_style_mapping": {
            "normal": {"size_multiplier": 1.0, "font_style": "Regular", "tracking_px": 0},
            "subtle": {"size_multiplier": 1.0, "font_style": "Regular", "tracking_px": 1},
            "medium": {"size_multiplier": 1.1, "font_style": "Bold", "tracking_px": 0},
            "strong": {"size_multiplier": 1.25, "font_style": "Bold", "tracking_px": 0},
        },
    }


def legacy_request(text: str, spans: list[dict], base_size: float = 0.073) -> dict:
    typo = std_typography()
    typo["font_family"] = "Microsoft YaHei UI"
    typo["base_size"] = base_size
    return {
        "text": text,
        "typography": typo,
        "emphasis_spans": spans,
    }


def materialized_request(materialized_cue: dict, typography: dict | None = None) -> dict:
    return {
        "materialized_cue": materialized_cue,
        "typography": typography or std_typography(),
        "canvas": {"width_px": 1080, "height_px": 1920},
    }


def run_tests() -> int:
    # 1. B00 Unicode codepoint index truth
    start, end = span_indices_from_substring_unique("价格上涨了 40%", "40%")
    check("unicode_index_b00", start == 6 and end == 8, f"got {start},{end}")

    # 2. Chinese span generation
    b10 = generate_from_legacy_test_request(
        legacy_request("价格上涨了 40%", [{"start": 6, "end": 8, "semantic_role": "strong"}])
    )
    check("chinese_span", "{ 102, 6, 8, Value = 0.09125 }" in b10)

    # 3. English + Chinese mixed
    b11 = generate_from_legacy_test_request(
        legacy_request(
            "AI 让效率提升了 35%",
            [
                {"start": 0, "end": 1, "semantic_role": "medium"},
                {"start": 10, "end": 12, "semantic_role": "strong"},
            ],
        )
    )
    check("mixed_en_zh", "{ 102, 0, 1, Value = 0.0803 }" in b11 and "{ 102, 10, 12, Value = 0.09125 }" in b11)

    # 4. Multiple spans
    b12 = generate_from_legacy_test_request(
        legacy_request(
            "今年增长 18%，成本下降 7%",
            [
                {"start": 5, "end": 7, "semantic_role": "strong"},
                {"start": 14, "end": 15, "semantic_role": "strong"},
            ],
        )
    )
    check("multiple_spans", b12.count("{ 102,") == 2)

    # 5. Overlapping spans fail closed
    overlap = False
    try:
        generate_from_legacy_test_request(
            legacy_request("abc", [{"start": 0, "end": 1}, {"start": 1, "end": 2}])
        )
    except ClsError as exc:
        overlap = exc.code == "OVERLAPPING_SPANS"
    check("overlapping_fail_closed", overlap)

    # 6. Duplicate substring fail closed
    ambiguous = False
    try:
        span_indices_from_substring_unique("foo bar foo", "foo")
    except ClsError as exc:
        ambiguous = exc.code == "AMBIGUOUS_SUBSTRING"
    check("duplicate_substring_fail_closed", ambiguous)

    # 7. Newline index recomputation from materialized runs
    mc_newline = {
        "styled_text": "第一行关键词\n第二行",
        "lines": [
            {
                "runs": [
                    {"text": "第一行", "emphasis_level": "normal"},
                    {"text": "关键词", "emphasis_level": "strong"},
                ]
            },
            {"runs": [{"text": "第二行", "emphasis_level": "normal"}]},
        ],
    }
    spans_nl = spans_from_materialized_cue(mc_newline, std_typography(), 0.073)
    check("newline_index", len(spans_nl) == 1 and spans_nl[0].start == 3 and spans_nl[0].end == 5)

    # 8. Split cue — each cue indexes from 0
    cue_a = {
        "styled_text": "40%",
        "lines": [{"runs": [{"text": "40%", "emphasis_level": "strong"}]}],
    }
    cue_b = {
        "styled_text": "7%",
        "lines": [{"runs": [{"text": "7%", "emphasis_level": "strong"}]}],
    }
    sa = spans_from_materialized_cue(cue_a, std_typography(), 0.073)[0]
    sb = spans_from_materialized_cue(cue_b, std_typography(), 0.073)[0]
    check("split_cue_from_zero", sa.start == 0 and sb.start == 0)

    # 9. Deterministic generation
    req = legacy_request("价格上涨了 40%", [{"substring": "40%", "semantic_role": "strong"}])
    a = generate_from_legacy_test_request(req)
    b = generate_from_legacy_test_request(req)
    check("deterministic", a == b)

    # 10. Escaping quote/backslash/newline
    esc = escape_fusion_string('say "hi"\\path\nline')
    check("escape", esc == 'say \\"hi\\"\\\\path\\nline')
    esc_out = generate_from_legacy_test_request(
        legacy_request('A"B\\\nC', [{"start": 0, "end": 0, "size": 0.08}])
    )
    check("escape_in_setting", 'Value = "A\\"B\\\\\\nC"' in esc_out)

    # 11. Unverified color fails closed
    color_fail = False
    try:
        reject_unverified_cls_inputs({"emphasis_spans": [{"color_rgb": [1, 0, 0]}]})
    except ClsError as exc:
        color_fail = exc.code == "CLS_COLOR_NOT_VERIFIED"
    check("color_fail_closed", color_fail)

    # 12. Unverified weight fails closed
    weight_fail = False
    try:
        reject_unverified_cls_inputs({"weight": "Bold"})
    except ClsError as exc:
        weight_fail = exc.code == "CLS_WEIGHT_NOT_VERIFIED"
    check("weight_fail_closed", weight_fail)

    # 13. Normal run does not emit CLS Size; subtle multiplier 1.0 also skipped
    mc_normal = {
        "styled_text": "普通词强调词",
        "lines": [
            {
                "runs": [
                    {"text": "普通词", "emphasis_level": "normal"},
                    {"text": "强调词", "emphasis_level": "strong"},
                ]
            }
        ],
    }
    spans_mix = spans_from_materialized_cue(mc_normal, std_typography(), 0.073)
    check("normal_no_cls", len(spans_mix) == 1 and spans_mix[0].start == 3)

    # 14. medium/strong consume canonical resolved size from mapping × font profile
    mat_req = materialized_request(
        {
            "styled_text": "AI 35%",
            "lines": [
                {
                    "runs": [
                        {"text": "AI", "emphasis_level": "medium"},
                        {"text": " 35%", "emphasis_level": "strong"},
                    ]
                }
            ],
        }
    )
    mat_out = generate_from_materialized_request(mat_req, FONT_PROFILES)
    check("profile_medium_size", "{ 102, 0, 1, Value = 0.0803 }" in mat_out)
    check("profile_strong_size", "{ 102, 2, 5, Value = 0.09125 }" in mat_out)

    # 15. Generated graph structure
    check("graph_cls", "CharacterLevelStyling1 = StyledTextCLS" in b10)
    check("graph_textplus", "Template = TextPlus" in b10)
    check("graph_mediaout", "MediaOut1 = Saver" in b10)
    check("graph_canonical_doc", "StyledTextCLS" in CANONICAL_GRAPH and "TextPlus" in CANONICAL_GRAPH)

    # 16. Installer contains generator/template
    installer_text = INSTALLER.read_text(encoding="utf-8")
    check("installer_generator", "generate-textplus-cls-setting.py" in installer_text)
    check("installer_lib", "textplus_cls_setting.py" in installer_text)
    check("installer_template", "textplus-cls-canonical.setting" in installer_text)

    # 17. Direct set_input route is not production route
    check(
        "set_input_non_production",
        KNOWN_NON_WORKING_ROUTE == "fusion_comp.set_input(CharacterLevelStyling)",
    )

    return _fail


if __name__ == "__main__":
    fails = run_tests()
    if fails:
        print(f"FAILED: {fails}")
        sys.exit(1)
    print("ALL PASS")
    sys.exit(0)

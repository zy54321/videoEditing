#!/usr/bin/env python3
"""Static tests for Text+ StyledTextCLS production backend (Stage 08E-B B-R2 / B-R3)."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
PAYLOAD = REPO / "source" / "payload"
LIB = PAYLOAD / "video-workflow" / "tools" / "lib"
CLI = PAYLOAD / "video-workflow" / "tools" / "generate-textplus-cls-setting.py"
FONT_PROFILES = PAYLOAD / "video-workflow" / "runtime" / "textplus-font-profiles.yaml"
GOLDEN_FIXTURE = PAYLOAD / "video-workflow" / "runtime" / "textplus-cls-canonical.setting"
INSTALLER = REPO / "source" / "installer" / "init-video-workflow.ps1"
sys.path.insert(0, str(LIB))

from textplus_cls_setting import (  # noqa: E402
    CANONICAL_GRAPH,
    EXECUTABLE_GRAPH_AUTHORITY,
    GOLDEN_GRAPH_FIXTURE,
    GRAPH_TOPOLOGY_MARKERS,
    KNOWN_NON_WORKING_ROUTE,
    ClsError,
    assert_graph_topology,
    escape_fusion_string,
    generate_from_legacy_test_request,
    generate_from_materialized_request,
    generate_from_production_request_file,
    reject_unverified_cls_inputs,
    resolve_font_profile,
    span_indices_from_substring_unique,
    spans_from_materialized_cue,
    load_font_profiles,
)

_fail = 0


def check(name: str, cond: bool, detail: str = "") -> None:
    global _fail
    if cond:
        print(f"PASS {name}")
    else:
        _fail += 1
        print(f"FAIL {name}" + (f" — {detail}" if detail else ""))


def std_typography(font_family: str = "Microsoft YaHei", base_px: int = 48) -> dict:
    return {
        "font_family": font_family,
        "fallback_font_family": "SimSun",
        "base_font_size_px": base_px,
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


def run_production_cli(request: dict, out_path: Path) -> subprocess.CompletedProcess[str]:
    with tempfile.TemporaryDirectory() as tmp:
        req_path = Path(tmp) / "request.json"
        req_path.write_text(json.dumps(request, ensure_ascii=False), encoding="utf-8")
        return subprocess.run(
            [sys.executable, str(CLI), "--request", str(req_path), "--out", str(out_path)],
            capture_output=True,
            text=True,
            encoding="utf-8",
        )


def run_tests() -> int:
    profiles_doc = load_font_profiles(FONT_PROFILES)

    # --- B-R2 regression (TEST_ONLY legacy path) ---
    start, end = span_indices_from_substring_unique("价格上涨了 40%", "40%")
    check("unicode_index_b00", start == 6 and end == 8, f"got {start},{end}")

    b10 = generate_from_legacy_test_request(
        legacy_request("价格上涨了 40%", [{"start": 6, "end": 8, "semantic_role": "strong"}])
    )
    check("chinese_span", "{ 102, 6, 8, Value = 0.09125 }" in b10)

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

    overlap = False
    try:
        generate_from_legacy_test_request(
            legacy_request("abc", [{"start": 0, "end": 1}, {"start": 1, "end": 2}])
        )
    except ClsError as exc:
        overlap = exc.code == "OVERLAPPING_SPANS"
    check("overlapping_fail_closed", overlap)

    ambiguous = False
    try:
        span_indices_from_substring_unique("foo bar foo", "foo")
    except ClsError as exc:
        ambiguous = exc.code == "AMBIGUOUS_SUBSTRING"
    check("duplicate_substring_fail_closed", ambiguous)

    req = legacy_request("价格上涨了 40%", [{"substring": "40%", "semantic_role": "strong"}])
    check("deterministic", generate_from_legacy_test_request(req) == generate_from_legacy_test_request(req))

    esc = escape_fusion_string('say "hi"\\path\nline')
    check("escape", esc == 'say \\"hi\\"\\\\path\\nline')
    esc_out = generate_from_legacy_test_request(
        legacy_request('A"B\\\nC', [{"start": 0, "end": 0, "size": 0.08}])
    )
    check("escape_in_setting", 'Value = "A\\"B\\\\\\nC"' in esc_out)

    color_fail = False
    try:
        reject_unverified_cls_inputs({"emphasis_spans": [{"color_rgb": [1, 0, 0]}]})
    except ClsError as exc:
        color_fail = exc.code == "CLS_COLOR_NOT_VERIFIED"
    check("color_fail_closed", color_fail)

    weight_fail = False
    try:
        reject_unverified_cls_inputs({"weight": "Bold"})
    except ClsError as exc:
        weight_fail = exc.code == "CLS_WEIGHT_NOT_VERIFIED"
    check("weight_fail_closed", weight_fail)

    check("set_input_non_production", KNOWN_NON_WORKING_ROUTE == "fusion_comp.set_input(CharacterLevelStyling)")

    installer_text = INSTALLER.read_text(encoding="utf-8")
    check("installer_generator", "generate-textplus-cls-setting.py" in installer_text)
    check("installer_lib", "textplus_cls_setting.py" in installer_text)
    check("installer_template", "textplus-cls-canonical.setting" in installer_text)

    # --- R3-01 font profile exact size ---
    yahei48 = resolve_font_profile(profiles_doc, std_typography("Microsoft YaHei", 48))
    check("font_yahei_48_pass", yahei48["textplus_size"] == 0.073)

    arial48 = resolve_font_profile(profiles_doc, std_typography("Arial", 48))
    check("font_arial_48_pass", arial48["textplus_size"] == 0.064)

    yahei60_fail = False
    try:
        resolve_font_profile(profiles_doc, std_typography("Microsoft YaHei", 60))
    except ClsError as exc:
        yahei60_fail = exc.code == "TEXTPLUS_FONT_SIZE_PROFILE_NOT_VALIDATED"
    check("font_yahei_60_fail_closed", yahei60_fail)

    arial52_fail = False
    try:
        resolve_font_profile(profiles_doc, std_typography("Arial", 52))
    except ClsError as exc:
        arial52_fail = exc.code == "TEXTPLUS_FONT_SIZE_PROFILE_NOT_VALIDATED"
    check("font_arial_52_fail_closed", arial52_fail)

    unknown_fail = False
    try:
        resolve_font_profile(profiles_doc, std_typography("Comic Sans MS", 48))
    except ClsError as exc:
        unknown_fail = exc.code == "FONT_PROFILE_NOT_FOUND"
    check("font_unknown_fail_closed", unknown_fail)

    # --- R3-02 production CLI rejects legacy ---
    with tempfile.TemporaryDirectory() as tmp:
        legacy_path = Path(tmp) / "legacy.json"
        legacy_path.write_text(json.dumps(legacy_request("x", [{"start": 0, "end": 0}]), ensure_ascii=False), encoding="utf-8")
        legacy_cli_fail = False
        try:
            generate_from_production_request_file(legacy_path, FONT_PROFILES)
        except ClsError as exc:
            legacy_cli_fail = exc.code == "MATERIALIZED_CUE_REQUIRED"
        check("production_file_rejects_legacy", legacy_cli_fail)

        flat_cli = run_production_cli(legacy_request("x", [{"start": 0, "end": 0}]), Path(tmp) / "out.setting")
        check("production_cli_rejects_flat", flat_cli.returncode == 2 and "MATERIALIZED_CUE_REQUIRED" in flat_cli.stderr)

    # --- R3-05 materialized authority via production CLI ---
    mc_normal_strong = {
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
    spans_mix = spans_from_materialized_cue(mc_normal_strong, std_typography(), 0.073)
    check("materialized_normal_strong", len(spans_mix) == 1 and spans_mix[0].start == 3)

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
    check("materialized_newline_index", spans_nl[0].start == 3 and spans_nl[0].end == 5)

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
    check("materialized_split_from_zero", sa.start == 0 and sb.start == 0)

    mc_dup_text = {
        "styled_text": "涨涨",
        "lines": [
            {
                "runs": [
                    {"text": "涨", "emphasis_level": "normal"},
                    {"text": "涨", "emphasis_level": "strong"},
                ]
            }
        ],
    }
    dup_spans = spans_from_materialized_cue(mc_dup_text, std_typography(), 0.073)
    check("materialized_dup_text_no_ambiguity", dup_spans[0].start == 1 and dup_spans[0].end == 1)

    with tempfile.TemporaryDirectory() as tmp:
        mat_out_path = Path(tmp) / "mat.setting"
        mat_cli = run_production_cli(materialized_request(mc_normal_strong), mat_out_path)
        check("production_cli_materialized_pass", mat_cli.returncode == 0 and mat_out_path.exists())
        if mat_out_path.exists():
            mat_content = mat_out_path.read_text(encoding="utf-8")
            check("production_cli_span_from_runs", "{ 102, 3, 5, Value = 0.09125 }" in mat_content)

    # --- R3-03 graph authority ---
    check("executable_graph_authority", EXECUTABLE_GRAPH_AUTHORITY == "textplus_cls_setting.generate_setting")
    check("golden_fixture_path", GOLDEN_GRAPH_FIXTURE.endswith("textplus-cls-canonical.setting"))

    golden_text = GOLDEN_FIXTURE.read_text(encoding="utf-8")
    golden_ok = True
    try:
        assert_graph_topology(golden_text)
    except ClsError:
        golden_ok = False
    check("golden_fixture_topology", golden_ok)

    mat_out = generate_from_materialized_request(
        materialized_request(
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
        ),
        FONT_PROFILES,
    )
    gen_topo_ok = True
    try:
        assert_graph_topology(mat_out)
    except ClsError:
        gen_topo_ok = False
    check("generator_topology_matches_golden", gen_topo_ok)
    for marker in GRAPH_TOPOLOGY_MARKERS:
        check(f"topology_marker_{marker[:20]}", marker in mat_out and marker in golden_text)

    check("graph_canonical_doc", "StyledTextCLS" in CANONICAL_GRAPH and "TextPlus" in CANONICAL_GRAPH)

    return _fail


if __name__ == "__main__":
    fails = run_tests()
    if fails:
        print(f"FAILED: {fails}")
        sys.exit(1)
    print("ALL PASS")
    sys.exit(0)

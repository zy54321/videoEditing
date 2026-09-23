#!/usr/bin/env python3
"""Static tests for Text+ StyledTextCLS production backend (Stage 08E-B Final)."""
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
PRODUCTION_PROFILE = PAYLOAD / "video-workflow" / "runtime" / "textplus-production-profile.yaml"
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
    fusion_global_out_from_duration,
    generate_from_legacy_test_request,
    generate_from_materialized_request,
    generate_from_production_request_file,
    reject_unverified_cls_inputs,
    resolve_font_profile,
    span_indices_from_substring_unique,
    spans_from_materialized_cue,
    load_font_profiles,
    validate_textplus_v1_typography,
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
        "tracking_px": 0,
        "stroke_px": 0,
        "emphasis_style_mapping": {
            "normal": {"size_multiplier": 1.0, "font_style": "Regular", "tracking_px": 0},
            "subtle": {"size_multiplier": 1.0, "font_style": "Regular", "tracking_px": 0},
            "medium": {"size_multiplier": 1.1, "font_style": "Regular", "tracking_px": 0},
            "strong": {"size_multiplier": 1.25, "font_style": "Regular", "tracking_px": 0},
        },
    }


def legacy_request(text: str, spans: list[dict], base_size: float = 0.073) -> dict:
    typo = std_typography()
    typo["font_family"] = "Microsoft YaHei UI"
    typo["base_size"] = base_size
    return {"text": text, "typography": typo, "emphasis_spans": spans}


def materialized_request(materialized_cue: dict, typography: dict | None = None) -> dict:
    return {
        "materialized_cue": materialized_cue,
        "typography": typography or std_typography(),
        "canvas": {"width_px": 1080, "height_px": 1920},
    }


def with_timing(cue: dict, start: int = 0, duration: int = 72) -> dict:
    out = dict(cue)
    out["start_frame"] = start
    out["duration_frames"] = duration
    return out


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

    # Legacy TEST_ONLY replay
    start, end = span_indices_from_substring_unique("价格上涨了 40%", "40%")
    check("unicode_index_b00", start == 6 and end == 8)
    b10 = generate_from_legacy_test_request(
        legacy_request("价格上涨了 40%", [{"start": 6, "end": 8, "semantic_role": "strong"}])
    )
    check("chinese_span", "{ 102, 6, 8, Value = 0.09125 }" in b10)
    check("deterministic", generate_from_legacy_test_request(legacy_request("x", [{"start": 0, "end": 0, "size": 0.08}])) == generate_from_legacy_test_request(legacy_request("x", [{"start": 0, "end": 0, "size": 0.08}])))

    # 1 size-only production mapping
    prod_yaml = json.loads(json.dumps(__import__("yaml").safe_load(PRODUCTION_PROFILE.read_text(encoding="utf-8"))))
    validate_textplus_v1_typography(std_typography(), prod_yaml)
    check("size_only_mapping_pass", True)

    # 2 Bold fail closed
    bold_fail = False
    try:
        bad = std_typography()
        bad["emphasis_style_mapping"]["strong"]["font_style"] = "Bold"
        validate_textplus_v1_typography(bad, prod_yaml)
    except ClsError as exc:
        bold_fail = exc.code == "CLS_FONT_STYLE_NOT_VERIFIED"
    check("bold_fail_closed", bold_fail)

    # 3 tracking fail closed
    track_fail = False
    try:
        bad = std_typography()
        bad["emphasis_style_mapping"]["subtle"]["tracking_px"] = 1
        validate_textplus_v1_typography(bad, prod_yaml)
    except ClsError as exc:
        track_fail = exc.code == "CLS_TRACKING_NOT_VERIFIED"
    check("tracking_fail_closed", track_fail)

    # 4 production stroke truth
    stroke_fail = False
    try:
        bad = std_typography()
        bad["stroke_px"] = 2
        validate_textplus_v1_typography(bad, prod_yaml)
    except ClsError as exc:
        stroke_fail = exc.code == "TEXTPLUS_STROKE_NOT_VERIFIED"
    check("production_stroke_zero", stroke_fail)

    # 5 exact font profile
    check("font_yahei_48_pass", resolve_font_profile(profiles_doc, std_typography("Microsoft YaHei", 48))["textplus_size"] == 0.073)
    check("font_arial_48_pass", resolve_font_profile(profiles_doc, std_typography("Arial", 48))["textplus_size"] == 0.064)
    yahei60_fail = False
    try:
        resolve_font_profile(profiles_doc, std_typography("Microsoft YaHei", 60))
    except ClsError as exc:
        yahei60_fail = exc.code == "TEXTPLUS_FONT_SIZE_PROFILE_NOT_VALIDATED"
    check("font_yahei_60_fail_closed", yahei60_fail)

    # 6 production cue timing required
    timing_fail = False
    try:
        generate_from_materialized_request(
            materialized_request({"styled_text": "x", "lines": [{"runs": [{"text": "x", "emphasis_level": "normal"}]}]}),
            FONT_PROFILES,
        )
    except ClsError as exc:
        timing_fail = exc.code == "PRODUCTION_CUE_TIMING_REQUIRED"
    check("production_timing_required", timing_fail)

    # 7 no default production global_out=119
    check("fusion_duration_from_frames", fusion_global_out_from_duration(72) == 71)

    # 8 Fusion range derived from duration
    plain_cue = with_timing(
        {"styled_text": "普通字幕", "lines": [{"runs": [{"text": "普通字幕", "emphasis_level": "normal"}]}]},
        duration=72,
    )
    plain_out = generate_from_materialized_request(materialized_request(plain_cue), FONT_PROFILES)
    check("plain_global_out_from_duration", "GlobalOut = Input { Value = 71," in plain_out)
    check("plain_render_range", "RenderRange = { 0, 71 }" in plain_out)

    # 9 plain cue production path
    check("plain_no_cls_node", "CharacterLevelStyling1" not in plain_out and "Template = TextPlus" in plain_out)

    # 10 emphasized cue production path
    emph_cue = with_timing(
        {
            "styled_text": "价格直接涨了 40%",
            "lines": [
                {
                    "runs": [
                        {"text": "价格直接涨了 ", "emphasis_level": "normal"},
                        {"text": "40%", "emphasis_level": "strong"},
                    ]
                }
            ],
        },
        duration=96,
    )
    emph_out = generate_from_materialized_request(materialized_request(emph_cue), FONT_PROFILES)
    check("emphasized_cls_node", "CharacterLevelStyling1 = StyledTextCLS" in emph_out)
    check("emphasized_global_out", "GlobalOut = Input { Value = 95," in emph_out)

    # 11 materialized runs authority + newline/split
    mc_newline = with_timing(
        {
            "styled_text": "第一行关键词\n第二行",
            "lines": [
                {"runs": [{"text": "第一行", "emphasis_level": "normal"}, {"text": "关键词", "emphasis_level": "strong"}]},
                {"runs": [{"text": "第二行", "emphasis_level": "normal"}]},
            ],
        }
    )
    spans_nl = spans_from_materialized_cue(mc_newline, std_typography(), 0.073)
    check("newline_index", spans_nl[0].start == 3)
    cue_a = with_timing({"styled_text": "40%", "lines": [{"runs": [{"text": "40%", "emphasis_level": "strong"}]}]})
    cue_b = with_timing({"styled_text": "7%", "lines": [{"runs": [{"text": "7%", "emphasis_level": "strong"}]}]})
    sa = spans_from_materialized_cue(cue_a, std_typography(), 0.073)[0]
    sb = spans_from_materialized_cue(cue_b, std_typography(), 0.073)[0]
    check("split_cue_from_zero", sa.start == 0 and sb.start == 0)

    # production CLI rejects flat legacy
    with tempfile.TemporaryDirectory() as tmp:
        flat_cli = run_production_cli(legacy_request("x", [{"start": 0, "end": 0}]), Path(tmp) / "out.setting")
        check("production_cli_rejects_flat", flat_cli.returncode == 2)
        mat_cli = run_production_cli(materialized_request(emph_cue), Path(tmp) / "mat.setting")
        check("production_cli_materialized_pass", mat_cli.returncode == 0)

    # 14 installer files
    installer_text = INSTALLER.read_text(encoding="utf-8")
    check("installer_generator", "generate-textplus-cls-setting.py" in installer_text)
    check("installer_production_profile", "textplus-production-profile.yaml" in installer_text)

    # 15 set_input non-production
    check("set_input_non_production", KNOWN_NON_WORKING_ROUTE == "fusion_comp.set_input(CharacterLevelStyling)")

    # graph authority
    check("executable_graph_authority", EXECUTABLE_GRAPH_AUTHORITY == "textplus_cls_setting.generate_setting")
    golden_text = GOLDEN_FIXTURE.read_text(encoding="utf-8")
    assert_graph_topology(golden_text)
    assert_graph_topology(emph_out)
    check("generator_topology_matches_golden", True)
    check("lower_placement_not_center", "VerticalJustificationNew = Input { Value = 2," in plain_out)
    check("graph_canonical_doc", "StyledTextCLS" in CANONICAL_GRAPH)

    # color/weight still fail closed
    color_fail = False
    try:
        reject_unverified_cls_inputs({"color_rgb": [1, 0, 0]})
    except ClsError as exc:
        color_fail = exc.code == "CLS_COLOR_NOT_VERIFIED"
    check("color_fail_closed", color_fail)

    esc = escape_fusion_string('say "hi"\\path\nline')
    check("escape", esc == 'say \\"hi\\"\\\\path\\nline')

    return _fail


if __name__ == "__main__":
    fails = run_tests()
    if fails:
        print(f"FAILED: {fails}")
        sys.exit(1)
    print("ALL PASS")
    sys.exit(0)

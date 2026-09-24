#!/usr/bin/env python3
"""Production Text+ StyledTextCLS .setting generator (v1: static inline SIZE emphasis only).

Executable graph authority:
  textplus_cls_setting.generate_setting() in this module.

Golden reference fixture (structural topology only — NOT a runtime dependency):
  video-workflow/runtime/textplus-cls-canonical.setting

Production request authority:
  materialized_cue.lines[].runs + typography → CLS spans → .setting → import_comp

TEST_ONLY / VALIDATION_ONLY:
  generate_from_legacy_test_request() — B10–B12 historical replay; not for Production CLI.

NOT production-safe:
  fusion_comp.set_input(CharacterLevelStyling)  # KNOWN_NON_WORKING_ROUTE
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

PARAM_SIZE = 102

CANONICAL_GRAPH = (
    "CharacterLevelStyling1 (StyledTextCLS) → Template (TextPlus) → MediaOut1"
)
EXECUTABLE_GRAPH_AUTHORITY = "textplus_cls_setting.generate_setting"
GOLDEN_GRAPH_FIXTURE = "video-workflow/runtime/textplus-cls-canonical.setting"
GRAPH_TOPOLOGY_MARKERS = (
    "CharacterLevelStyling1 = StyledTextCLS",
    "Template = TextPlus",
    "MediaOut1 = Saver",
    'SourceOp = "CharacterLevelStyling1"',
    'Source = "StyledText"',
    'SourceOp = "Template"',
    'Source = "Output"',
    'TEMPLATE_ID = "Text+"',
)
KNOWN_NON_WORKING_ROUTE = "fusion_comp.set_input(CharacterLevelStyling)"
PRODUCTION_PROFILE_REL = "video-workflow/runtime/textplus-production-profile.yaml"

CANONICAL_EMPHASIS_LEVELS = ("normal", "subtle", "medium", "strong")

PLAIN_GRAPH_TOPOLOGY_MARKERS = (
    "Template = TextPlus",
    "MediaOut1 = Saver",
    'SourceOp = "Template"',
    'Source = "Output"',
    'TEMPLATE_ID = "Text+"',
)


class ClsError(Exception):
    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(message)


@dataclass(frozen=True)
class EmphasisSpan:
    start: int
    end: int
    size: float


def logical_char_count(text: str) -> int:
    return len(text)


def escape_fusion_string(value: str) -> str:
    return (
        value.replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\n", "\\n")
        .replace("\r", "\\r")
        .replace("\t", "\\t")
    )


def span_indices_from_substring_unique(text: str, substring: str) -> tuple[int, int]:
    count = text.count(substring)
    if count == 0:
        raise ClsError("SUBSTRING_NOT_FOUND", f"substring not found: {substring!r}")
    if count > 1:
        raise ClsError(
            "AMBIGUOUS_SUBSTRING",
            f"substring {substring!r} occurs {count} times; use explicit start/end",
        )
    start = text.index(substring)
    end = start + len(substring) - 1
    return start, end


def resolve_emphasis_level(value: str | None) -> str:
    key = (value or "normal").strip().lower()
    if key not in CANONICAL_EMPHASIS_LEVELS:
        raise ClsError("EMPHASIS_LEVEL_UNSUPPORTED", f"unsupported emphasis_level: {value!r}")
    return key


def get_emphasis_size_multiplier(typography: dict[str, Any], emphasis_level: str) -> float:
    mapping = typography.get("emphasis_style_mapping")
    if not mapping:
        raise ClsError("EMPHASIS_MAPPING_MISSING", "typography.emphasis_style_mapping is required")
    key = resolve_emphasis_level(emphasis_level)
    entry = mapping.get(key)
    if not entry:
        raise ClsError("EMPHASIS_MAPPING_MISSING", f"missing mapping for {key}")
    return float(entry["size_multiplier"])


def load_font_profiles(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not data or "profiles" not in data:
        raise ClsError("FONT_PROFILES_INVALID", f"invalid font profiles: {path}")
    return data


def default_production_profile_path() -> Path:
    return Path(__file__).resolve().parents[2] / "runtime" / "textplus-production-profile.yaml"


def load_production_profile(path: Path | None = None) -> dict[str, Any]:
    profile_path = path or default_production_profile_path()
    data = yaml.safe_load(profile_path.read_text(encoding="utf-8"))
    if not data or "production_typography" not in data:
        raise ClsError("PRODUCTION_PROFILE_INVALID", f"invalid production profile: {profile_path}")
    return data


def validate_textplus_v1_typography(typography: dict[str, Any], production_profile: dict[str, Any]) -> None:
    """Production Text+ v1 = SIZE-only emphasis; Regular font; zero tracking; zero stroke."""
    expected = production_profile["production_typography"]["emphasis_style_mapping"]
    mapping = typography.get("emphasis_style_mapping")
    if not mapping:
        raise ClsError("EMPHASIS_MAPPING_MISSING", "typography.emphasis_style_mapping is required")

    for level, spec in expected.items():
        entry = mapping.get(level)
        if not entry:
            raise ClsError("EMPHASIS_MAPPING_MISSING", f"missing mapping for {level}")
        if str(entry.get("font_style", "")) != str(spec["font_style"]):
            raise ClsError(
                "CLS_FONT_STYLE_NOT_VERIFIED",
                f"Text+ v1 production requires font_style={spec['font_style']} for {level}",
            )
        if int(entry.get("tracking_px", 0)) != int(spec["tracking_px"]):
            raise ClsError(
                "CLS_TRACKING_NOT_VERIFIED",
                f"Text+ v1 production requires tracking_px={spec['tracking_px']} for {level}",
            )
        if float(entry.get("size_multiplier")) != float(spec["size_multiplier"]):
            raise ClsError(
                "EMPHASIS_MAPPING_MISMATCH",
                f"production mapping size_multiplier for {level} must be {spec['size_multiplier']}",
            )

    prod_stroke = int(production_profile["production_typography"].get("stroke_px", 0))
    if int(typography.get("stroke_px", 0)) != prod_stroke:
        raise ClsError(
            "TEXTPLUS_STROKE_NOT_VERIFIED",
            f"Text+ v1 production requires stroke_px={prod_stroke}",
        )


def require_production_timing(materialized_cue: dict[str, Any]) -> tuple[int, int]:
    start = materialized_cue.get("start_frame")
    duration = materialized_cue.get("duration_frames")
    if start is None or duration is None:
        raise ClsError(
            "PRODUCTION_CUE_TIMING_REQUIRED",
            "materialized_cue.start_frame and duration_frames are required for production",
        )
    start_i = int(start)
    duration_i = int(duration)
    if duration_i < 1:
        raise ClsError("PRODUCTION_CUE_TIMING_INVALID", "duration_frames must be >= 1")
    return start_i, duration_i


def fusion_global_out_from_duration(duration_frames: int) -> int:
    """Fusion GlobalOut is inclusive end frame index for a comp of duration_frames."""
    return max(0, int(duration_frames) - 1)


def cue_has_size_emphasis(materialized_cue: dict[str, Any], typography: dict[str, Any]) -> bool:
    for line in materialized_cue.get("lines") or []:
        for run in line.get("runs") or []:
            level = resolve_emphasis_level(run.get("emphasis_level"))
            if get_emphasis_size_multiplier(typography, level) > 1.0:
                return True
    return False


def placement_inputs(production_profile: dict[str, Any]) -> dict[str, int]:
    placement = production_profile.get("placement") or {}
    return {
        "horizontal_center": int(placement.get("horizontal_justification_center", 1)),
        "horizontal_new": int(placement.get("horizontal_justification_new", 3)),
        "vertical_center": int(placement.get("vertical_justification_center", 1)),
        "vertical_new": int(placement.get("vertical_justification_new", 2)),
    }


def _require_base_font_size_px(typography: dict[str, Any]) -> int:
    raw = typography.get("base_font_size_px")
    if raw is None:
        raise ClsError("BASE_FONT_SIZE_MISSING", "typography.base_font_size_px is required")
    try:
        return int(raw)
    except (TypeError, ValueError):
        raise ClsError(
            "BASE_FONT_SIZE_INVALID",
            f"typography.base_font_size_px must be an integer, got {raw!r}",
        )


def resolve_font_profile(
    profiles_doc: dict[str, Any],
    typography: dict[str, Any],
) -> dict[str, Any]:
    """Match font family AND exact validated l1_base_font_size_px — no scaling or interpolation."""
    base_px = _require_base_font_size_px(typography)
    candidates = [
        typography.get("font_family"),
        typography.get("fallback_font_family"),
    ]
    profiles = profiles_doc.get("profiles", {})
    family_match: dict[str, Any] | None = None
    family_key: str | None = None
    for name, profile in profiles.items():
        for cand in candidates:
            if not cand:
                continue
            if profile.get("l1_font_family") == cand or profile.get("resolve_font_family") == cand:
                family_match = profile
                family_key = name
                break
        if family_match is not None:
            break
    if family_match is None:
        raise ClsError(
            "FONT_PROFILE_NOT_FOUND",
            f"no Text+ font profile for typography.font_family={typography.get('font_family')!r}",
        )
    validated_px = int(family_match.get("l1_base_font_size_px", -1))
    if base_px != validated_px:
        raise ClsError(
            "TEXTPLUS_FONT_SIZE_PROFILE_NOT_VALIDATED",
            (
                f"typography.base_font_size_px={base_px} is not validated for "
                f"{typography.get('font_family')!r} (validated: {validated_px}px only)"
            ),
        )
    out = dict(family_match)
    out["profile_key"] = family_key
    return out


def build_styled_text_from_lines(lines: list[dict[str, Any]]) -> str:
    parts: list[str] = []
    for line in lines:
        runs = line.get("runs") or []
        parts.append("".join(str(r.get("text", "")) for r in runs))
    return "\n".join(parts)


def spans_from_materialized_cue(
    materialized_cue: dict[str, Any],
    typography: dict[str, Any],
    base_textplus_size: float,
) -> list[EmphasisSpan]:
    lines = materialized_cue.get("lines") or []
    if not lines:
        raise ClsError("MATERIALIZED_LINES_EMPTY", "materialized cue has no lines")

    styled_text = materialized_cue.get("styled_text")
    if styled_text is None:
        styled_text = build_styled_text_from_lines(lines)
    reconstructed = build_styled_text_from_lines(lines)
    if styled_text != reconstructed:
        raise ClsError(
            "STYLED_TEXT_MISMATCH",
            "materialized styled_text does not match lines[] reconstruction",
        )

    spans: list[EmphasisSpan] = []
    offset = 0
    for line_index, line in enumerate(lines):
        for run in line.get("runs") or []:
            text = str(run.get("text", ""))
            if not text:
                continue
            start = offset
            end = offset + len(text) - 1
            level = resolve_emphasis_level(run.get("emphasis_level"))
            multiplier = get_emphasis_size_multiplier(typography, level)
            if multiplier > 1.0:
                spans.append(
                    EmphasisSpan(start=start, end=end, size=base_textplus_size * multiplier)
                )
            offset += len(text)
        if line_index < len(lines) - 1:
            offset += 1

    if not spans:
        raise ClsError("NO_SIZE_EMPHASIS_SPANS", "no size emphasis spans after materialization")
    validate_spans(styled_text, spans)
    return spans


def validate_spans(text: str, spans: list[EmphasisSpan]) -> None:
    n = logical_char_count(text)
    if n == 0:
        raise ClsError("TEXT_EMPTY", "styled text must not be empty")
    seen: list[tuple[int, int]] = []
    for span in spans:
        if span.start < 0 or span.end < span.start or span.end >= n:
            raise ClsError(
                "SPAN_OUT_OF_RANGE",
                f"span ({span.start},{span.end}) invalid for text length {n}",
            )
        for a, b in seen:
            if not (span.end < a or span.start > b):
                raise ClsError(
                    "OVERLAPPING_SPANS",
                    f"overlapping spans ({span.start},{span.end}) and ({a},{b})",
                )
        seen.append((span.start, span.end))


def reject_unverified_cls_inputs(payload: dict[str, Any]) -> None:
    for span in payload.get("emphasis_spans") or []:
        if span.get("color_rgb") is not None:
            raise ClsError("CLS_COLOR_NOT_VERIFIED", "per-span color is not verified in v1")
        if span.get("weight") is not None:
            raise ClsError("CLS_WEIGHT_NOT_VERIFIED", "per-span weight is not verified in v1")
    if payload.get("color_rgb") is not None:
        raise ClsError("CLS_COLOR_NOT_VERIFIED", "per-span color is not verified in v1")
    if payload.get("weight") is not None:
        raise ClsError("CLS_WEIGHT_NOT_VERIFIED", "per-span weight is not verified in v1")


def format_array_entries(spans: list[EmphasisSpan]) -> list[str]:
    return [
        f"\t\t\t\t\t\t{{ {PARAM_SIZE}, {span.start}, {span.end}, Value = {span.size:g} }}"
        for span in spans
    ]


def assert_graph_topology(setting_text: str) -> None:
    """Verify generator output matches golden fixture graph topology (not byte-equal)."""
    for marker in GRAPH_TOPOLOGY_MARKERS:
        if marker not in setting_text:
            raise ClsError("GRAPH_TOPOLOGY_MISMATCH", f"missing topology marker: {marker}")


def assert_plain_graph_topology(setting_text: str) -> None:
    for marker in PLAIN_GRAPH_TOPOLOGY_MARKERS:
        if marker not in setting_text:
            raise ClsError("GRAPH_TOPOLOGY_MISMATCH", f"missing plain topology marker: {marker}")


def _textplus_input_block(
    *,
    global_out: int,
    width: int,
    height: int,
    font_family: str,
    font_style: str,
    base_size: float,
    text: str | None = None,
    styled_text_source: bool = False,
    placement: dict[str, int] | None = None,
) -> str:
    place = placement or {
        "horizontal_center": 1,
        "horizontal_new": 3,
        "vertical_center": 1,
        "vertical_new": 3,
    }
    escaped_font = escape_fusion_string(font_family)
    escaped_style = escape_fusion_string(font_style)
    if styled_text_source:
        styled_text_input = """\t\t\t\tStyledText = Input {
\t\t\t\t\tSourceOp = "CharacterLevelStyling1",
\t\t\t\t\tSource = "StyledText",
\t\t\t\t},"""
        text_input = ""
    else:
        styled_text_input = ""
        text_input = f'\t\t\t\tText = Input {{ Value = "{escape_fusion_string(text or "")}", }},'
    return f"""\t\tTemplate = TextPlus {{
\t\t\tInputs = {{
\t\t\t\tGlobalOut = Input {{ Value = {global_out}, }},
\t\t\t\tWidth = Input {{ Value = {width}, }},
\t\t\t\tHeight = Input {{ Value = {height}, }},
\t\t\t\tUseFrameFormatSettings = Input {{ Value = 1, }},
{styled_text_input}
{text_input}
\t\t\t\tFont = Input {{ Value = "{escaped_font}", }},
\t\t\t\tStyle = Input {{ Value = "{escaped_style}", }},
\t\t\t\tSize = Input {{ Value = {base_size:g}, }},
\t\t\t\tVerticalJustificationCenter = Input {{ Value = {place["vertical_center"]}, }},
\t\t\t\tVerticalJustificationNew = Input {{ Value = {place["vertical_new"]}, }},
\t\t\t\tHorizontalJustificationCenter = Input {{ Value = {place["horizontal_center"]}, }},
\t\t\t\tHorizontalJustificationNew = Input {{ Value = {place["horizontal_new"]}, }}
\t\t\t}},
\t\t\tVersion = 1
\t\t}}"""


def generate_plain_setting(
    text: str,
    font_family: str,
    font_style: str,
    base_size: float,
    global_out: int,
    width: int = 1080,
    height: int = 1920,
    placement: dict[str, int] | None = None,
) -> str:
    textplus_block = _textplus_input_block(
        global_out=global_out,
        width=width,
        height=height,
        font_family=font_family,
        font_style=font_style,
        base_size=base_size,
        text=text,
        styled_text_source=False,
        placement=placement,
    )
    content = f"""Composition {{
\tCurrentTime = 0,
\tRenderRange = {{ 0, {global_out} }},
\tGlobalRange = {{ 0, {global_out} }},
\tHiQ = true,
\tPlaybackUpdateMode = 0,
\tStereoMode = false,
\tCustomData = {{ TEMPLATE_ID = "Text+" }},
\tTools = {{
{textplus_block},
\t\tMediaOut1 = Saver {{
\t\t\tInputs = {{
\t\t\t\tIndex = Input {{ Value = "0", }},
\t\t\t\tInput = Input {{
\t\t\t\t\tSourceOp = "Template",
\t\t\t\t\tSource = "Output",
\t\t\t\t}}
\t\t\t}}
\t\t}}
\t}},
\tFrames = {{
\t}},
}}"""
    assert_plain_graph_topology(content)
    return content


def generate_setting(
    text: str,
    font_family: str,
    font_style: str,
    base_size: float,
    spans: list[EmphasisSpan],
    global_out: int,
    width: int = 1080,
    height: int = 1920,
    placement: dict[str, int] | None = None,
) -> str:
    validate_spans(text, spans)
    escaped_text = escape_fusion_string(text)
    array_block = ",\n".join(format_array_entries(spans))
    textplus_block = _textplus_input_block(
        global_out=global_out,
        width=width,
        height=height,
        font_family=font_family,
        font_style=font_style,
        base_size=base_size,
        text=text,
        styled_text_source=True,
        placement=placement,
    )

    content = f"""Composition {{
\tCurrentTime = 0,
\tRenderRange = {{ 0, {global_out} }},
\tGlobalRange = {{ 0, {global_out} }},
\tHiQ = true,
\tPlaybackUpdateMode = 0,
\tStereoMode = false,
\tCustomData = {{ TEMPLATE_ID = "Text+" }},
\tTools = {{
\t\tCharacterLevelStyling1 = StyledTextCLS {{
\t\t\tInputs = {{
\t\t\t\tTransformRotation = Input {{ Value = 1, }},
\t\t\t\tSoftness = Input {{ Value = 1, }},
\t\t\t\tText = Input {{ Value = "{escaped_text}", }},
\t\t\t\tCharacterLevelStyling = Input {{
\t\t\t\t\tValue = StyledText {{
\t\t\t\t\t\tArray = {{
{array_block}
\t\t\t\t\t\t}},
\t\t\t\t\t\tValue = ""
\t\t\t\t\t}},
\t\t\t\t}}
\t\t\t}}
\t\t}},
{textplus_block},
\t\tMediaOut1 = Saver {{
\t\t\tInputs = {{
\t\t\t\tIndex = Input {{ Value = "0", }},
\t\t\t\tInput = Input {{
\t\t\t\t\tSourceOp = "Template",
\t\t\t\t\tSource = "Output",
\t\t\t\t}}
\t\t\t}}
\t\t}}
\t}},
\tFrames = {{
\t}},
}}"""
    assert_graph_topology(content)
    return content


def generate_from_materialized_request(
    request: dict[str, Any],
    font_profiles_path: Path,
    production_profile_path: Path | None = None,
) -> str:
    reject_unverified_cls_inputs(request)
    materialized = request.get("materialized_cue")
    typography = request.get("typography")
    if not materialized or not typography:
        raise ClsError("REQUEST_INVALID", "materialized_cue and typography are required")

    production_profile = load_production_profile(production_profile_path)
    validate_textplus_v1_typography(typography, production_profile)
    _, duration_frames = require_production_timing(materialized)
    global_out = fusion_global_out_from_duration(duration_frames)

    profiles_doc = load_font_profiles(font_profiles_path)
    profile = resolve_font_profile(profiles_doc, typography)
    base_size = float(profile["textplus_size"])
    place = placement_inputs(production_profile)

    canvas = request.get("canvas") or {}
    width = int(canvas.get("width_px", 1080))
    height = int(canvas.get("height_px", 1920))
    styled_text = str(materialized.get("styled_text") or build_styled_text_from_lines(materialized["lines"]))

    if cue_has_size_emphasis(materialized, typography):
        spans = spans_from_materialized_cue(materialized, typography, base_size)
        return generate_setting(
            text=styled_text,
            font_family=str(profile["resolve_font_family"]),
            font_style=str(profile.get("textplus_style", "Regular")),
            base_size=base_size,
            spans=spans,
            global_out=global_out,
            width=width,
            height=height,
            placement=place,
        )

    return generate_plain_setting(
        text=styled_text,
        font_family=str(profile["resolve_font_family"]),
        font_style=str(profile.get("textplus_style", "Regular")),
        base_size=base_size,
        global_out=global_out,
        width=width,
        height=height,
        placement=place,
    )


def generate_from_legacy_test_request(request: dict[str, Any]) -> str:
    """TEST_ONLY / VALIDATION_ONLY — flat text + manual spans for B10–B12 replay.

    Production CLI must NOT call this. Use generate_from_materialized_request only.
    """
    reject_unverified_cls_inputs(request)
    text = str(request["text"])
    typography = request.get("typography") or {}
    if "emphasis_style_mapping" not in typography:
        raise ClsError("EMPHASIS_MAPPING_MISSING", "legacy request requires emphasis_style_mapping")
    spans: list[EmphasisSpan] = []
    base_size = float(typography.get("base_size", 0.073))
    for raw in request.get("emphasis_spans") or []:
        if "substring" in raw:
            start, end = span_indices_from_substring_unique(text, raw["substring"])
        else:
            start = int(raw["start"])
            end = int(raw["end"])
        level = resolve_emphasis_level(raw.get("semantic_role") or raw.get("emphasis_level", "strong"))
        if raw.get("size") is not None:
            size = float(raw["size"])
        elif raw.get("size_multiplier") is not None:
            size = base_size * float(raw["size_multiplier"])
        else:
            size = base_size * get_emphasis_size_multiplier(typography, level)
        spans.append(EmphasisSpan(start=start, end=end, size=size))

    legacy_global_out = int(
        request.get("global_out")
        or load_production_profile()["timing"]["validation_only_default_global_out"]
    )
    return generate_setting(
        text=text,
        font_family=str(typography.get("font_family", "Microsoft YaHei UI")),
        font_style=str(typography.get("font_style", "Regular")),
        base_size=base_size,
        spans=spans,
        global_out=legacy_global_out,
        width=int(request.get("width", 1080)),
        height=int(request.get("height", 1920)),
    )


def generate_from_production_request_file(request_path: Path, font_profiles_path: Path) -> str:
    """Production CLI entry — materialized_cue authority only."""
    request = json.loads(request_path.read_text(encoding="utf-8"))
    if not request.get("materialized_cue"):
        raise ClsError(
            "MATERIALIZED_CUE_REQUIRED",
            "production route requires materialized_cue; legacy flat requests are TEST_ONLY",
        )
    return generate_from_materialized_request(request, font_profiles_path)

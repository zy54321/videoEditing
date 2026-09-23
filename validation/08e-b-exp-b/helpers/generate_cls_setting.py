#!/usr/bin/env python3
"""Generate Resolve-native Fusion .setting for Text+ StyledTextCLS emphasis.

Canonical graph: CharacterLevelStyling1 → Template (TextPlus) → MediaOut1
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

PARAM_SIZE = 102
PARAM_STYLE = 109
PARAM_RED = 2401
PARAM_GREEN = 2402
PARAM_BLUE = 2403

ROLE_MULTIPLIERS = {
    "normal": 1.0,
    "subtle": 1.0,
    "medium": 1.1,
    "strong": 1.25,
}


@dataclass(frozen=True)
class EmphasisSpan:
    start: int
    end: int
    semantic_role: str = "strong"
    size: float | None = None
    size_multiplier: float | None = None
    color_rgb: tuple[float, float, float] | None = None
    weight: str | None = None


def logical_char_count(text: str) -> int:
    """Resolve CLS uses Python/Unicode codepoint indices (verified B00)."""
    return len(text)


def escape_fusion_string(value: str) -> str:
    return (
        value.replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\n", "\\n")
        .replace("\r", "\\r")
        .replace("\t", "\\t")
    )


def span_indices_from_substring(text: str, substring: str) -> tuple[int, int]:
    start = text.index(substring)
    end = start + len(substring) - 1
    return start, end


def validate_spans(text: str, spans: list[EmphasisSpan], allow_overlap: bool = False) -> None:
    n = logical_char_count(text)
    if n == 0:
        raise ValueError("text must not be empty")
    seen: list[tuple[int, int]] = []
    for span in spans:
        if span.start < 0:
            raise ValueError(f"span start must be >= 0, got {span.start}")
        if span.end < span.start:
            raise ValueError(f"span end must be >= start, got {span.end} < {span.start}")
        if span.end >= n:
            raise ValueError(
                f"span end {span.end} out of range for text length {n} (0..{n - 1})"
            )
        if not allow_overlap:
            for a, b in seen:
                if not (span.end < a or span.start > b):
                    raise ValueError(
                        f"overlapping spans ({span.start},{span.end}) and ({a},{b})"
                    )
        seen.append((span.start, span.end))


def resolve_span_size(span: EmphasisSpan, base_size: float) -> float | None:
    if span.size is not None:
        return span.size
    if span.size_multiplier is not None:
        return base_size * span.size_multiplier
    mult = ROLE_MULTIPLIERS.get(span.semantic_role)
    if mult is None:
        raise ValueError(f"unknown semantic_role: {span.semantic_role}")
    if mult == 1.0:
        return None
    return base_size * mult


def format_array_entries(spans: list[EmphasisSpan], base_size: float) -> list[str]:
    lines: list[str] = []
    for span in spans:
        size = resolve_span_size(span, base_size)
        if size is not None:
            lines.append(
                f"\t\t\t\t\t\t{{ {PARAM_SIZE}, {span.start}, {span.end}, Value = {size:g} }}"
            )
        if span.color_rgb is not None:
            r, g, b = span.color_rgb
            for param, val in ((PARAM_RED, r), (PARAM_GREEN, g), (PARAM_BLUE, b)):
                lines.append(
                    f"\t\t\t\t\t\t{{ {param}, {span.start}, {span.end}, Value = {val:g} }}"
                )
        if span.weight is not None:
            w = escape_fusion_string(span.weight)
            lines.append(
                f'\t\t\t\t\t\t{{ {PARAM_STYLE}, {span.start}, {span.end}, String = "{w}" }}'
            )
    if not lines:
        raise ValueError("no CLS array entries produced; spans must include size emphasis")
    return lines


def generate_setting(
    text: str,
    font_family: str = "Microsoft YaHei UI",
    font_style: str = "Regular",
    base_size: float = 0.073,
    spans: list[EmphasisSpan] | None = None,
    global_out: int = 119,
    width: int = 1080,
    height: int = 1920,
) -> str:
    spans = spans or []
    validate_spans(text, spans)
    escaped_text = escape_fusion_string(text)
    escaped_font = escape_fusion_string(font_family)
    escaped_style = escape_fusion_string(font_style)
    array_lines = format_array_entries(spans, base_size)
    array_block = ",\n".join(array_lines)

    return f"""Composition {{
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
\t\tTemplate = TextPlus {{
\t\t\tInputs = {{
\t\t\t\tGlobalOut = Input {{ Value = {global_out}, }},
\t\t\t\tWidth = Input {{ Value = {width}, }},
\t\t\t\tHeight = Input {{ Value = {height}, }},
\t\t\t\tUseFrameFormatSettings = Input {{ Value = 1, }},
\t\t\t\tStyledText = Input {{
\t\t\t\t\tSourceOp = "CharacterLevelStyling1",
\t\t\t\t\tSource = "StyledText",
\t\t\t\t}},
\t\t\t\tFont = Input {{ Value = "{escaped_font}", }},
\t\t\t\tStyle = Input {{ Value = "{escaped_style}", }},
\t\t\t\tSize = Input {{ Value = {base_size:g}, }},
\t\t\t\tVerticalJustificationCenter = Input {{ Value = 1, }},
\t\t\t\tVerticalJustificationNew = Input {{ Value = 3, }},
\t\t\t\tHorizontalJustificationCenter = Input {{ Value = 1, }},
\t\t\t\tHorizontalJustificationNew = Input {{ Value = 3, }}
\t\t\t}},
\t\t\tVersion = 1
\t\t}},
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


def load_request(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def spans_from_request(req: dict[str, Any], text: str) -> list[EmphasisSpan]:
    spans: list[EmphasisSpan] = []
    for raw in req.get("emphasis_spans", []):
        if "substring" in raw:
            start, end = span_indices_from_substring(text, raw["substring"])
        else:
            start = int(raw["start"])
            end = int(raw["end"])
        spans.append(
            EmphasisSpan(
                start=start,
                end=end,
                semantic_role=raw.get("semantic_role", "strong"),
                size=raw.get("size"),
                size_multiplier=raw.get("size_multiplier"),
                color_rgb=tuple(raw["color_rgb"]) if raw.get("color_rgb") else None,
                weight=raw.get("weight"),
            )
        )
    return spans


def generate_from_request(req: dict[str, Any]) -> str:
    text = req["text"]
    typo = req.get("typography", {})
    return generate_setting(
        text=text,
        font_family=typo.get("font_family", "Microsoft YaHei UI"),
        font_style=typo.get("font_style", "Regular"),
        base_size=float(typo.get("base_size", 0.073)),
        spans=spans_from_request(req, text),
        global_out=int(req.get("global_out", 119)),
        width=int(req.get("width", 1080)),
        height=int(req.get("height", 1920)),
    )


def main() -> int:
    ap = argparse.ArgumentParser(description="Generate Text+ StyledTextCLS .setting")
    ap.add_argument("--request", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    req = load_request(args.request)
    content = generate_from_request(req)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(content, encoding="utf-8")
    print(json.dumps({"out": str(args.out), "text_len": logical_char_count(req["text"])}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())

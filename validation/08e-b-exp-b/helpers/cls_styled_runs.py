#!/usr/bin/env python3
"""Thin re-exports for CLS span helpers. Prefer generate_cls_setting.py."""
from __future__ import annotations

from generate_cls_setting import (  # noqa: F401
    EmphasisSpan,
    ROLE_MULTIPLIERS,
    logical_char_count,
    span_indices_from_substring,
    validate_spans,
)

# Back-compat alias
span_indices = span_indices_from_substring
"""Monotonic frozen-script alignment used by the N20261021 temporary script.

Timing bounds come from Resolve word start/end. Cue text stays the frozen line.
Homophone pairs are location evidence only. This is not character-proportional
timing across the whole narration.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

METHOD = "resolve_word_timestamps_monotonic_align"

# Pairs verified on the episode-3 one-off. Do not treat them as subtitle text.
CONF = {
    ("察", "茶"),
    ("观", "官"),
    ("责", "泽"),
    ("地", "的"),
    ("的", "地"),
    ("得", "的"),
    ("地", "得"),
    ("了", "啦"),
}


def is_content(ch: str) -> bool:
    return "\u4e00" <= ch <= "\u9fff" or ch.isalnum()


def align_frozen_script_to_words(
    lines: list[str],
    words: list[dict[str, Any]],
    *,
    audio_duration: float | None = None,
) -> dict[str, Any]:
    script: list[tuple[int, str]] = []
    for si, line in enumerate(lines):
        for ch in line:
            if is_content(ch):
                script.append((si, ch))
    asr: list[tuple[int, str]] = []
    for wi, word in enumerate(words):
        for ch in str(word.get("text") or ""):
            if is_content(ch):
                asr.append((wi, ch))

    n, m = len(script), len(asr)
    inf = 10**9
    dp = [[inf] * (m + 1) for _ in range(n + 1)]
    prev: list[list[tuple[int, int, str] | None]] = [[None] * (m + 1) for _ in range(n + 1)]
    dp[0][0] = 0
    for j in range(1, m + 1):
        dp[0][j] = j * 2
        prev[0][j] = (0, j - 1, "drop_asr")
    for i in range(1, n + 1):
        dp[i][0] = i * 6
        prev[i][0] = (i - 1, 0, "drop_script")
        for j in range(1, m + 1):
            sc, ac = script[i - 1][1], asr[j - 1][1]
            if sc == ac:
                cost = 0
            elif (sc, ac) in CONF:
                cost = 1
            else:
                cost = 8
            options = [
                (dp[i - 1][j - 1] + cost, (i - 1, j - 1, "match")),
                (dp[i][j - 1] + 2, (i, j - 1, "drop_asr")),
                (dp[i - 1][j] + 6, (i - 1, j, "drop_script")),
            ]
            best = min(options, key=lambda item: item[0])
            dp[i][j] = best[0]
            prev[i][j] = best[1]

    match_of: list[int | None] = [None] * n
    i, j = n, m
    while not (i == 0 and j == 0):
        step = prev[i][j]
        if step is None:
            break
        pi, pj, kind = step
        if kind == "match":
            match_of[i - 1] = j - 1
        i, j = pi, pj

    sent_words: dict[int, list[int]] = {k: [] for k in range(len(lines))}
    mismatches: list[dict[str, Any]] = []
    for idx, (si, sch) in enumerate(script):
        aj = match_of[idx]
        if aj is None:
            mismatches.append({"sentence_index": si + 1, "script": sch, "asr": None})
            continue
        wi, ach = asr[aj]
        sent_words[si].append(wi)
        if sch != ach:
            mismatches.append({"sentence_index": si + 1, "script": sch, "asr": ach, "sentence": lines[si]})

    problems: list[str] = []
    cues: list[dict[str, Any]] = []
    for si, line in enumerate(lines):
        content_n = sum(1 for ss, _ in script if ss == si)
        matched_count = sum(1 for k, (ss, _) in enumerate(script) if ss == si and match_of[k] is not None)
        used = sorted(set(sent_words[si]))
        if content_n and matched_count < content_n:
            problems.append(f"INCOMPLETE {si + 1}: matched {matched_count}/{content_n} :: {line}")
        if not used:
            continue
        start = float(words[used[0]]["start"])
        end = float(words[used[-1]]["end"])
        cues.append(
            {
                "cue_id": f"c{si + 1:02d}",
                "sentence_index": si + 1,
                "text": line,
                "start": round(start, 3),
                "end": round(end, 3),
                "asr_text": "".join(str(words[w]["text"]) for w in used),
            }
        )

    timeline_end = audio_duration if audio_duration and audio_duration > 0 else (cues[-1]["end"] + 0.35 if cues else 0.0)
    long_pauses: list[dict[str, Any]] = []
    for idx, cue in enumerate(cues):
        if idx + 1 < len(cues):
            nxt = float(cues[idx + 1]["start"])
            gap = nxt - float(cue["end"])
            if gap < 0:
                problems.append(f"OVERLAP_EVIDENCE {cue['cue_id']} gap={gap:.3f}")
                cue["display_end"] = round(max(float(cue["start"]) + 0.2, nxt), 3)
            elif gap < 0.8:
                cue["display_end"] = round(nxt, 3)
            else:
                long_pauses.append({"after_cue": cue["cue_id"], "gap_sec": round(gap, 3)})
                cue["display_end"] = round(min(timeline_end, float(cue["end"]) + 0.2), 3)
        else:
            cue["display_end"] = round(min(timeline_end, float(cue["end"]) + 0.35), 3)
        cue["display_start"] = cue["start"]
        if float(cue["display_end"]) <= float(cue["display_start"]):
            problems.append(f"NONPOSITIVE {cue['cue_id']}")

    if lines and (not cues or cues[-1]["text"] != lines[-1]):
        problems.append("LAST_SENTENCE_MISSING")

    blocked = any(
        item.startswith("INCOMPLETE") or item.startswith("OVERLAP") or item.startswith("NONPOSITIVE") or item == "LAST_SENTENCE_MISSING"
        for item in problems
    )
    return {
        "schema_version": 1,
        "method": METHOD,
        "text_authority": "frozen_script",
        "status": "BLOCKED" if blocked else "OK",
        "proportional_char_timing": False,
        "problems": problems,
        "long_pauses_sec": long_pauses,
        "mismatch_samples": [item for item in mismatches if item.get("asr")][:40],
        "unmatched_script_chars": [item for item in mismatches if item.get("asr") is None][:40],
        "cue_count": len(cues),
        "script_line_count": len(lines),
        "cues": cues,
    }


def load_script_lines(path: Path) -> list[str]:
    return [ln.strip().lstrip("\ufeff") for ln in path.read_text(encoding="utf-8-sig").splitlines() if ln.strip()]


def write_alignment(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def apply_alignment_bounds(canonical: dict[str, Any], alignment: dict[str, Any]) -> list[str]:
    """Pin each frozen sentence's canonical span to word-boundary display times.

    Interior layout splits keep their existing duration ratios inside that span.
    They are not a new character grid over the whole file.
    """
    if alignment.get("status") != "OK":
        return ["ALIGNMENT_NOT_OK"]
    cues = canonical.get("cues") or []
    sentences = alignment.get("cues") or []
    errors: list[str] = []
    cursor = 0

    def _content(text: str) -> str:
        return "".join(ch for ch in text if is_content(ch))

    for sentence in sentences:
        target = _content(str(sentence["text"]))
        group: list[dict[str, Any]] = []
        acc = ""
        while cursor < len(cues) and acc != target:
            group.append(cues[cursor])
            acc += _content(str(cues[cursor].get("text") or ""))
            cursor += 1
            if len(acc) > len(target):
                break
        if acc != target or not group:
            errors.append(f"CANONICAL_SENTENCE_UNMAPPED:{sentence.get('cue_id')}")
            continue
        start = float(sentence["display_start"])
        end = float(sentence["display_end"])
        widths = [max(float(item["end"]) - float(item["start"]), 1e-3) for item in group]
        total = sum(widths)
        t = start
        for idx, item in enumerate(group):
            item_end = end if idx == len(group) - 1 else t + (end - start) * (widths[idx] / total)
            item["start"] = round(t, 3)
            item["end"] = round(item_end, 3)
            item["timing_bounds"] = "resolve_word_sentence"
            t = item_end
    if cursor != len(cues):
        errors.append("CANONICAL_CUES_LEFTOVER")
    return errors

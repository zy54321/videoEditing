"""Music mix balance QA — FINAL ARTIFACT authority only."""
from __future__ import annotations

import json
import math
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from shared_asset_library import load_catalog_file

VERDICT_PASS = "PASS"
VERDICT_FAIL_TOO_WEAK = "FAIL_TOO_WEAK"
VERDICT_FAIL_TOO_STRONG = "FAIL_TOO_STRONG"
VERDICT_FAIL_REGRESSION = "FAIL_REGRESSION_VS_REFERENCE"
PRECHECK_PASS = "PRECHECK_PASS"


@dataclass
class MusicMixProfile:
    music_below_voice_min: float = 12.0
    music_below_voice_max: float = 22.0
    too_weak_db: float = 24.0
    too_strong_db: float = 10.0
    min_sections_fail_ratio: float = 0.35
    regression_vs_reference_db: float = 3.0


def load_music_mix_profile(path: Path) -> MusicMixProfile:
    data = load_catalog_file(path)
    rel = data.get("relative_level_target_db") or {}
    thr = data.get("thresholds") or {}
    return MusicMixProfile(
        music_below_voice_min=float(rel.get("music_below_voice_min", 12.0)),
        music_below_voice_max=float(rel.get("music_below_voice_max", 22.0)),
        too_weak_db=float(thr.get("too_weak_music_below_voice_db", 24.0)),
        too_strong_db=float(thr.get("too_strong_music_below_voice_db", 10.0)),
        min_sections_fail_ratio=float(thr.get("min_sections_fail_ratio", 0.35)),
        regression_vs_reference_db=float(thr.get("regression_vs_reference_db", 3.0)),
    )


def rms_db(path: Path, start: float, dur: float) -> Optional[float]:
    cmd = [
        "ffmpeg",
        "-hide_banner",
        "-ss",
        str(start),
        "-t",
        str(dur),
        "-i",
        str(path),
        "-af",
        "volumedetect",
        "-f",
        "null",
        "-",
    ]
    p = subprocess.run(cmd, capture_output=True, text=True, check=False)
    text = (p.stderr or "") + (p.stdout or "")
    m = re.search(r"mean_volume:\s*([-\d.]+)\s*dB", text)
    return float(m.group(1)) if m else None


def _db_to_lin(db: float) -> float:
    return 10.0 ** (db / 10.0)


def _lin_to_db(lin: float) -> float:
    if lin <= 1e-12:
        return -120.0
    return 10.0 * math.log10(lin)


def music_bed_in_pause(
    voice_stem: Path,
    artifact: Path,
    start: float,
    dur: float,
    pause_voice_db_max: float = -42.0,
    slice_sec: float = 0.35,
) -> Optional[float]:
    """Measure mix RMS in a low-voice sub-window (direct music-bed proxy on final artifact)."""
    t = start
    end = start + dur
    best: Optional[float] = None
    while t + slice_sec <= end:
        v = rms_db(voice_stem, t, slice_sec)
        if v is not None and v <= pause_voice_db_max:
            m = rms_db(artifact, t, slice_sec)
            if m is not None:
                if best is None or m > best:
                    best = m
        t += slice_sec
    return best


def classify_bed_level(profile: MusicMixProfile, bed_db: float) -> str:
    if bed_db <= -50.0:
        return VERDICT_FAIL_TOO_WEAK
    if bed_db >= -28.0:
        return VERDICT_FAIL_TOO_STRONG
    return VERDICT_PASS


def classify_section_regression(
    profile: MusicMixProfile,
    candidate_mix_db: float,
    reference_mix_db: float,
) -> Tuple[str, Dict[str, Any]]:
    delta = candidate_mix_db - reference_mix_db
    if delta <= -profile.regression_vs_reference_db:
        verdict = VERDICT_FAIL_REGRESSION
    else:
        verdict = VERDICT_PASS
    return verdict, {
        "mix_rms_db": candidate_mix_db,
        "reference_mix_rms_db": reference_mix_db,
        "mix_delta_vs_reference_db": round(delta, 2),
        "section_verdict": verdict,
    }


def analyze_music_stem_regression(
    reference_music: Path,
    candidate_music: Path,
    duration_sec: float,
    profile: MusicMixProfile,
) -> Dict[str, Any]:
    ref_db = rms_db(reference_music, 0, duration_sec)
    cand_db = rms_db(candidate_music, 0, duration_sec)
    delta = None
    verdict = VERDICT_PASS
    if ref_db is not None and cand_db is not None:
        delta = cand_db - ref_db
        if delta <= -profile.regression_vs_reference_db:
            verdict = VERDICT_FAIL_REGRESSION
        elif delta >= profile.regression_vs_reference_db:
            verdict = VERDICT_FAIL_TOO_STRONG
    return {
        "authority": "PRODUCTION_MUSIC_STEM",
        "reference_music": str(reference_music),
        "candidate_music": str(candidate_music),
        "reference_rms_db": ref_db,
        "candidate_rms_db": cand_db,
        "delta_db": round(delta, 2) if delta is not None else None,
        "MUSIC_MIX_BALANCE": verdict,
    }


def analyze_final_artifact(
    artifact: Path,
    voice_stem: Path,
    sections: List[Dict[str, Any]],
    profile: MusicMixProfile,
    reference_artifact: Optional[Path] = None,
) -> Dict[str, Any]:
    rows = []
    bed_levels: List[float] = []
    weak_bed = 0
    strong_bed = 0
    reg_fail = 0
    deltas: List[float] = []

    for s in sections:
        start = float(s["start_sec"])
        dur = float(s["duration_sec"])
        m = rms_db(artifact, start, dur)
        bed = music_bed_in_pause(voice_stem, artifact, start, dur)
        row = {**s, "mix_rms_db": m, "music_bed_pause_db": bed}
        if bed is not None:
            bed_levels.append(bed)
            bed_verdict = classify_bed_level(profile, bed)
            row["bed_verdict"] = bed_verdict
            if bed_verdict == VERDICT_FAIL_TOO_WEAK:
                weak_bed += 1
            elif bed_verdict == VERDICT_FAIL_TOO_STRONG:
                strong_bed += 1
        if reference_artifact and reference_artifact.is_file() and m is not None:
            rm = rms_db(reference_artifact, start, dur)
            if rm is not None:
                verdict, metrics = classify_section_regression(profile, m, rm)
                row.update(metrics)
                deltas.append(metrics["mix_delta_vs_reference_db"])
                if verdict == VERDICT_FAIL_REGRESSION:
                    reg_fail += 1
        rows.append(row)

    n = max(len(rows), 1)
    overall = VERDICT_PASS
    if reg_fail / n >= profile.min_sections_fail_ratio:
        overall = VERDICT_FAIL_REGRESSION
    elif weak_bed / max(len(bed_levels), 1) >= profile.min_sections_fail_ratio:
        overall = VERDICT_FAIL_TOO_WEAK
    elif strong_bed / max(len(bed_levels), 1) >= profile.min_sections_fail_ratio:
        overall = VERDICT_FAIL_TOO_STRONG

    mean_delta = sum(deltas) / len(deltas) if deltas else None
    return {
        "authority": "FINAL_ARTIFACT",
        "artifact": str(artifact.resolve()),
        "voice_stem": str(voice_stem.resolve()),
        "reference_artifact": str(reference_artifact.resolve()) if reference_artifact else None,
        "profile": {
            "regression_vs_reference_db": profile.regression_vs_reference_db,
            "pause_bed_too_weak_db": -50.0,
            "pause_bed_too_strong_db": -28.0,
        },
        "sections": rows,
        "summary": {
            "mean_mix_delta_vs_reference_db": round(mean_delta, 2) if mean_delta is not None else None,
            "mean_music_bed_pause_db": round(sum(bed_levels) / len(bed_levels), 2) if bed_levels else None,
            "sections_regression_fail": reg_fail,
            "sections_bed_too_weak": weak_bed,
            "sections_bed_too_strong": strong_bed,
        },
        "MUSIC_MIX_BALANCE": overall,
        "MUSIC_MIX_QA_AUTHORITY": "PASS" if overall == VERDICT_PASS else "FAIL",
    }


def run_fixture_triplet(
    profile: MusicMixProfile,
    work_dir: Path,
    voice_db: float = -20.0,
) -> Dict[str, Any]:
    """Synthetic A/B/C fixtures via ffmpeg amix."""
    work_dir.mkdir(parents=True, exist_ok=True)
    voice = work_dir / "voice.wav"
    music = work_dir / "music.wav"
    dur = 3.0
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-f",
            "lavfi",
            "-i",
            f"sine=frequency=300:duration={dur}",
            "-ar",
            "48000",
            "-ac",
            "2",
            str(voice),
        ],
        check=True,
        capture_output=True,
    )
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-f",
            "lavfi",
            "-i",
            f"sine=frequency=900:duration={dur}",
            "-ar",
            "48000",
            "-ac",
            "2",
            str(music),
        ],
        check=True,
        capture_output=True,
    )
    ref = work_dir / "mix_balanced.wav"
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-i",
            str(voice),
            "-i",
            str(music),
            "-filter_complex",
            "[1:a]volume=0.06[m];[0:a][m]amix=inputs=2:duration=first",
            "-ar",
            "48000",
            "-ac",
            "2",
            str(ref),
        ],
        check=True,
        capture_output=True,
    )
    music_only = work_dir / "music_only.wav"
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-i",
            str(music),
            "-t",
            str(dur),
            "-ar",
            "48000",
            "-ac",
            "2",
            str(music_only),
        ],
        check=True,
        capture_output=True,
    )
    cases = [
        ("inaudible", 0.004, VERDICT_FAIL_REGRESSION),
        ("balanced", 0.06, VERDICT_PASS),
        ("loud", 0.35, VERDICT_FAIL_TOO_STRONG),
    ]
    ref_stem = work_dir / "stem_ref.wav"
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-i",
            str(music_only),
            "-af",
            "volume=0.06",
            str(ref_stem),
        ],
        check=True,
        capture_output=True,
    )
    results = []
    for name, music_vol, expected in cases:
        cand = work_dir / f"stem_{name}.wav"
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-hide_banner",
                "-i",
                str(music_only),
                "-af",
                f"volume={music_vol}",
                str(cand),
            ],
            check=True,
            capture_output=True,
        )
        stem = analyze_music_stem_regression(ref_stem, cand, dur, profile)
        verdict = stem["MUSIC_MIX_BALANCE"]
        results.append(
            {
                "case": name,
                "expected": expected,
                "got": verdict,
                "ok": verdict == expected,
            }
        )
    return {"fixture_results": results, "all_ok": all(r["ok"] for r in results)}

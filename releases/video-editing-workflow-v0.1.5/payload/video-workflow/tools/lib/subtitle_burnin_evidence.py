"""FINAL_RENDER_SUBTITLE_BURNIN — differential / negative-control evidence (R2 hardening)."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from canonical_cue_sample_times import load_canonical_cues, select_active_cue_sample_times
from final_render_contract import MATERIALIZATION_EXTERNAL, FinalRenderContract
from subtitle_final_artifact_qa import extract_frame, measure_subtitle_extent

try:
    from PIL import Image
except ImportError:
    Image = None  # type: ignore

SUBTITLE_BAND_TOP = 0.62
CONTROL_BAND_TOP = 0.12
CONTROL_BAND_BOTTOM = 0.38

MIN_BAND_MAE = 4.0
MIN_SUBTITLE_VS_CONTROL_RATIO = 1.6
MIN_CHANGED_PIXEL_RATIO = 0.008
PIXEL_CHANGE_THRESH = 22


def _band_mean_abs_diff(path_a: Path, path_b: Path, y_start_ratio: float, y_end_ratio: float) -> float:
    if Image is None:
        return 0.0
    a = Image.open(path_a).convert("RGB")
    b = Image.open(path_b).convert("RGB")
    w, h = min(a.size[0], b.size[0]), min(a.size[1], b.size[1])
    y0 = int(h * y_start_ratio)
    y1 = max(y0 + 1, int(h * y_end_ratio))
    total = 0.0
    count = 0
    for y in range(y0, y1):
        for x in range(w):
            pa = a.getpixel((x, y))
            pb = b.getpixel((x, y))
            total += abs(pa[0] - pb[0]) + abs(pa[1] - pb[1]) + abs(pa[2] - pb[2])
            count += 3
    return total / max(count, 1)


def _band_changed_pixel_ratio(path_a: Path, path_b: Path, y_start_ratio: float, y_end_ratio: float) -> float:
    if Image is None:
        return 0.0
    a = Image.open(path_a).convert("RGB")
    b = Image.open(path_b).convert("RGB")
    w, h = min(a.size[0], b.size[0]), min(a.size[1], b.size[1])
    y0 = int(h * y_start_ratio)
    y1 = max(y0 + 1, int(h * y_end_ratio))
    changed = 0
    total = 0
    for y in range(y0, y1):
        for x in range(w):
            pa = a.getpixel((x, y))
            pb = b.getpixel((x, y))
            if max(abs(pa[i] - pb[i]) for i in range(3)) >= PIXEL_CHANGE_THRESH:
                changed += 1
            total += 1
    return changed / max(total, 1)


def _negative_control_time(active_sec: float, duration: float, cues: list[dict[str, Any]]) -> float:
    """Pick a time unlikely to coincide with active subtitle overlay."""
    if duration > 1.0:
        for candidate in (0.12, duration * 0.05, active_sec - 1.5, duration - 0.2):
            if candidate < 0:
                continue
            if candidate >= duration:
                continue
            inside = any(float(c.get("start", 0)) <= candidate <= float(c.get("end", 0)) for c in cues)
            if not inside:
                return candidate
    return max(0.05, min(active_sec * 0.1, duration * 0.08))


def _score_differential(sub_mae: float, ctrl_mae: float, sub_chg: float, ctrl_chg: float) -> tuple[str, str]:
    ratio_mae = sub_mae / max(ctrl_mae, 0.5)
    ratio_chg = sub_chg / max(ctrl_chg, 0.0005)
    mae_ok = sub_mae >= MIN_BAND_MAE and ratio_mae >= MIN_SUBTITLE_VS_CONTROL_RATIO
    chg_ok = sub_chg >= MIN_CHANGED_PIXEL_RATIO and ratio_chg >= MIN_SUBTITLE_VS_CONTROL_RATIO
    if mae_ok or chg_ok:
        return "PASS", "differential_subtitle_band_elevated"
    if sub_chg >= MIN_CHANGED_PIXEL_RATIO * 0.5 or sub_mae >= MIN_BAND_MAE * 0.5:
        return "VISUAL_CONFIRM_REQUIRED", "weak_differential_evidence"
    return "FAIL", "no_subtitle_band_differential"


def evaluate_burnin_sample(
    *,
    final_video: Path,
    work_dir: Path,
    sample: dict[str, Any],
    contract: FinalRenderContract,
    cues: list[dict[str, Any]],
    duration: float,
) -> dict[str, Any]:
    work_dir.mkdir(parents=True, exist_ok=True)
    t_active = float(sample["sec"])
    final_active = work_dir / f"{sample['id']}_final_{t_active:.2f}s.png"
    extract_frame(final_video, t_active, final_active)

    features = measure_subtitle_extent(final_active)
    row: dict[str, Any] = {
        **sample,
        "final_frame": str(final_active),
        "bright_pixel_features": features,
        "evidence_model": "r2_differential_v1",
    }

    clean_path = contract.clean_master_path
    use_clean = (
        contract.subtitle_materialization == MATERIALIZATION_EXTERNAL
        and clean_path
        and Path(clean_path).is_file()
    )

    if use_clean:
        clean_active = work_dir / f"{sample['id']}_clean_{t_active:.2f}s.png"
        extract_frame(Path(clean_path), t_active, clean_active)
        sub_mae = _band_mean_abs_diff(clean_active, final_active, SUBTITLE_BAND_TOP, 1.0)
        ctrl_mae = _band_mean_abs_diff(clean_active, final_active, CONTROL_BAND_TOP, CONTROL_BAND_BOTTOM)
        sub_chg = _band_changed_pixel_ratio(clean_active, final_active, SUBTITLE_BAND_TOP, 1.0)
        ctrl_chg = _band_changed_pixel_ratio(clean_active, final_active, CONTROL_BAND_TOP, CONTROL_BAND_BOTTOM)
        verdict, reason = _score_differential(sub_mae, ctrl_mae, sub_chg, ctrl_chg)
        row.update(
            {
                "method": "clean_master_differential",
                "subtitle_band_mae": round(sub_mae, 3),
                "control_band_mae": round(ctrl_mae, 3),
                "band_mae_ratio": round(sub_mae / max(ctrl_mae, 0.5), 3),
                "subtitle_band_changed_ratio": round(sub_chg, 5),
                "control_band_changed_ratio": round(ctrl_chg, 5),
                "clean_frame": str(clean_active),
                "burnin_evidence_verdict": verdict,
                "burnin_evidence_reason": reason,
            }
        )
        return row

    t_neg = _negative_control_time(t_active, duration, cues)
    final_neg = work_dir / f"{sample['id']}_final_neg_{t_neg:.2f}s.png"
    extract_frame(final_video, t_neg, final_neg)
    sub_mae = _band_mean_abs_diff(final_neg, final_active, SUBTITLE_BAND_TOP, 1.0)
    ctrl_mae = _band_mean_abs_diff(final_neg, final_active, CONTROL_BAND_TOP, CONTROL_BAND_BOTTOM)
    sub_chg = _band_changed_pixel_ratio(final_neg, final_active, SUBTITLE_BAND_TOP, 1.0)
    ctrl_chg = _band_changed_pixel_ratio(final_neg, final_active, CONTROL_BAND_TOP, CONTROL_BAND_BOTTOM)
    verdict, reason = _score_differential(sub_mae, ctrl_mae, sub_chg, ctrl_chg)
    row.update(
        {
            "method": "temporal_negative_control",
            "negative_control_sec": t_neg,
            "subtitle_band_mae": round(sub_mae, 3),
            "control_band_mae": round(ctrl_mae, 3),
            "band_mae_ratio": round(sub_mae / max(ctrl_mae, 0.5), 3),
            "subtitle_band_changed_ratio": round(sub_chg, 5),
            "control_band_changed_ratio": round(ctrl_chg, 5),
            "negative_frame": str(final_neg),
            "burnin_evidence_verdict": verdict,
            "burnin_evidence_reason": reason,
        }
    )
    return row


def evaluate_subtitle_burnin_gate(
    *,
    contract: FinalRenderContract,
    final_video: Path,
    canonical_path: Path,
    work_dir: Path,
    duration: float,
) -> dict[str, Any]:
    if Image is None:
        return {
            "FINAL_RENDER_SUBTITLE_BURNIN": "VISUAL_CONFIRM_REQUIRED",
            "reason": "PIL_UNAVAILABLE",
            "samples": [],
        }

    cues = load_canonical_cues(canonical_path)
    samples = select_active_cue_sample_times(cues, duration=duration or None)
    if not samples:
        samples = [{"id": "mid", "sec": max(0.5, duration * 0.5), "role": "fallback"}]

    rows = [
        evaluate_burnin_sample(
            final_video=final_video,
            work_dir=work_dir,
            sample=s,
            contract=contract,
            cues=cues,
            duration=duration,
        )
        for s in samples
    ]

    passes = sum(1 for r in rows if r.get("burnin_evidence_verdict") == "PASS")
    weak = sum(1 for r in rows if r.get("burnin_evidence_verdict") == "VISUAL_CONFIRM_REQUIRED")
    fails = sum(1 for r in rows if r.get("burnin_evidence_verdict") == "FAIL")

    if passes >= max(1, len(rows) // 2):
        burnin = "PASS"
    elif fails >= len(rows) // 2 + 1 or (fails > 0 and passes == 0):
        burnin = "FAIL"
    else:
        burnin = "VISUAL_CONFIRM_REQUIRED"

    return {
        "FINAL_RENDER_SUBTITLE_BURNIN": burnin,
        "evidence_model": "r2_differential_v1",
        "pass_count": passes,
        "fail_count": fails,
        "visual_confirm_count": weak,
        "samples": rows,
    }

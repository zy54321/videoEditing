#!/usr/bin/env python3
"""Pair A1.1 materialization predictions with rendered measurements."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

TOL_ABS_PX = 8
TOL_REL = 0.03


def parity_pass(predicted: float, actual: float) -> bool:
    err = abs(actual - predicted)
    rel = err / predicted if predicted else 0.0
    return err <= TOL_ABS_PX or rel <= TOL_REL


def flatten_materialized(plan: dict) -> list[dict]:
    cues = plan.get("materialized_cues") or []
    out: list[dict] = []
    for cue in cues:
        if isinstance(cue, dict) and cue.get("cue_id"):
            out.append(cue)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", required=True)
    ap.add_argument("--measurement", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--case-id", required=True)
    args = ap.parse_args()

    plan = json.loads(Path(args.plan).read_text(encoding="utf-8-sig"))
    meas = json.loads(Path(args.measurement).read_text(encoding="utf-8-sig"))

    mat_status = plan.get("materialization_status")
    result = {
        "case_id": args.case_id,
        "materialization_status": mat_status,
        "l1_status": plan.get("l1_status"),
        "measurable": meas.get("measurable", False),
        "line_count_detected": meas.get("line_count_detected"),
        "pairs": [],
        "parity": "SKIPPED",
    }

    if mat_status in ("BLOCKED_NO_LEGAL_INTERNAL_BREAK", "BLOCKED_NO_SPLIT_CANDIDATE", "BLOCKED_L1_STATUS"):
        result["parity"] = "POLICY_BLOCKED"
        result["note"] = "No Text+ render attempted; pre-materialization policy pass"
    elif not meas.get("measurable"):
        result["parity"] = "FAIL_NO_TEXT"
    else:
        cues = flatten_materialized(plan)
        if len(cues) == 1:
            cue = cues[0]
            predicted = cue.get("predicted_line_widths_px") or []
            actual_lines = meas.get("lines") or []
            pairs = []
            all_pass = True
            if len(predicted) == 1 and not actual_lines and meas.get("actual_width_px") is not None:
                pred = float(predicted[0])
                act = float(meas["actual_width_px"])
                ok = parity_pass(pred, act)
                pairs.append(
                    {
                        "line_index": 1,
                        "predicted_px": pred,
                        "actual_px": act,
                        "abs_error_px": abs(act - pred),
                        "relative_error": abs(act - pred) / pred if pred else None,
                        "pass": ok,
                    }
                )
                all_pass = ok
            else:
                for i, pred in enumerate(predicted):
                    act = actual_lines[i]["width_px"] if i < len(actual_lines) else None
                    ok = act is not None and parity_pass(float(pred), float(act))
                    if not ok:
                        all_pass = False
                    pairs.append(
                        {
                            "line_index": i + 1,
                            "predicted_px": pred,
                            "actual_px": act,
                            "abs_error_px": abs(act - pred) if act is not None else None,
                            "relative_error": abs(act - pred) / pred if act is not None and pred else None,
                            "pass": ok,
                        }
                    )
            result["pairs"] = pairs
            result["line_count_l1"] = cue.get("line_count")
            result["newline_positions"] = cue.get("newline_positions")
            result["styled_text_readback_expected"] = cue.get("styled_text")
            single_line_ok = (
                len(predicted) == 1
                and not actual_lines
                and meas.get("actual_width_px") is not None
            )
            if all_pass and (len(predicted) == len(actual_lines) or single_line_ok):
                result["parity"] = "PASS"
            else:
                result["parity"] = "FAIL"
        else:
            result["parity"] = "MULTI_CUE_MANUAL"
            result["materialized_cue_count"] = len(cues)

    Path(args.out).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

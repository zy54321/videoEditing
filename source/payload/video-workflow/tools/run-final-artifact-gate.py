#!/usr/bin/env python3
"""Run FINAL_ARTIFACT_GATE (contract + optional final-artifact-qa.json)."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_LIB = Path(__file__).resolve().parent / "lib"
if str(_LIB) not in sys.path:
    sys.path.insert(0, str(_LIB))

from final_artifact_gate import evaluate_final_artifact_gate  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description="FINAL_ARTIFACT_GATE (R2)")
    ap.add_argument("--contract", type=Path, required=True)
    ap.add_argument("--qa-report", type=Path, help="final-artifact-qa.json from final-artifact-qa.ps1")
    ap.add_argument("--work-dir", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()

    result = evaluate_final_artifact_gate(
        contract_path=args.contract,
        qa_report_path=args.qa_report,
        work_dir=args.work_dir,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(result["verdict"])
    if result.get("checks", {}).get("FINAL_RENDER_SUBTITLE_BURNIN"):
        print(result["checks"]["FINAL_RENDER_SUBTITLE_BURNIN"])
    return 0 if result["verdict"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())

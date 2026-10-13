#!/usr/bin/env python3
"""Re-verify FINAL_ARTIFACT_GATE evidence bindings at Stage 10."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_LIB = Path(__file__).resolve().parent / "lib"
if str(_LIB) not in sys.path:
    sys.path.insert(0, str(_LIB))

from artifact_fingerprint import verify_evidence_bindings  # noqa: E402
from final_render_contract import load_final_render_contract  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workspace", type=Path, required=True)
    args = ap.parse_args()

    root = args.workspace.resolve()
    prod = root / "video-workflow" / "production"
    gate_path = prod / "final-artifact-gate-result.json"
    contract_path = prod / "final-render-contract.json"

    if not gate_path.is_file():
        print("PRODUCTION_COMPLETE_BLOCKED: gate result missing")
        return 4
    gate = json.loads(gate_path.read_text(encoding="utf-8-sig"))
    if gate.get("gate") != "FINAL_ARTIFACT_GATE":
        print("PRODUCTION_COMPLETE_BLOCKED: wrong gate id")
        return 4
    if gate.get("status") not in ("COMPLETE", None):
        print("PRODUCTION_COMPLETE_BLOCKED: gate run incomplete")
        return 4
    if gate.get("verdict") != "PASS":
        print("PRODUCTION_COMPLETE_BLOCKED: gate not PASS")
        return 4

    if not contract_path.is_file():
        print("PRODUCTION_COMPLETE_BLOCKED: contract missing")
        return 4

    contract = load_final_render_contract(contract_path)
    final_path = Path(contract.final_artifact_path)
    canonical_path = Path(contract.canonical_subtitle_cues_path or "") if contract.canonical_subtitle_cues_path else None
    qa_path = Path(gate.get("qa_report_path") or "") if gate.get("qa_report_path") else None

    errors = verify_evidence_bindings(
        gate,
        contract_path=contract_path,
        final_artifact_path=final_path,
        canonical_cues_path=canonical_path if canonical_path and canonical_path.is_file() else None,
        qa_report_path=qa_path if qa_path and qa_path.is_file() else None,
    )
    if errors:
        print("; ".join(errors))
        return 4

    print("PRODUCTION_FINAL_RENDER_PASS: bindings verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

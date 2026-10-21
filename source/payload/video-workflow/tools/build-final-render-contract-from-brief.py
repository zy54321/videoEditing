#!/usr/bin/env python3
"""U2 — Build final-render-contract.json from Production Brief (deterministic)."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_TOOLS = Path(__file__).resolve().parent
_LIB = _TOOLS / "lib"
if str(_LIB) not in sys.path:
    sys.path.insert(0, str(_LIB))

from brief_final_render_contract import (  # noqa: E402
    BuildStatus,
    build_final_render_contract_from_brief,
    write_contract_from_brief,
)
from final_render_contract import load_final_render_contract  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description="Build Final Render Contract from Production Brief")
    ap.add_argument("--brief", type=Path, required=True)
    ap.add_argument("--workspace", type=Path, required=True)
    ap.add_argument("--out", type=Path, help="Default: <workspace>/video-workflow/production/final-render-contract.json")
    ap.add_argument("--templates", type=Path, help="Default: <workspace>/video-workflow/templates")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--json", action="store_true", help="Emit machine-readable result on stdout")
    args = ap.parse_args()

    workspace = args.workspace.resolve()
    out = args.out or (workspace / "video-workflow" / "production" / "final-render-contract.json")
    templates = args.templates or (workspace / "video-workflow" / "templates")

    if args.dry_run:
        result = build_final_render_contract_from_brief(
            brief_path=args.brief,
            workspace_root=workspace,
            templates_dir=templates,
        )
    else:
        result = write_contract_from_brief(
            brief_path=args.brief,
            workspace_root=workspace,
            out_path=out,
            templates_dir=templates,
            force=args.force,
        )

    payload = {
        "status": result.status.value,
        "contract_preparation": result.status.value,
        "final_delivery_gate": "NOT_RUN",
        "final_delivery_note": "CONTRACT_READY does not imply FINAL_ARTIFACT_GATE PASS (U3)",
        "errors": list(result.errors),
        "resolved_baseline_id": result.resolved_baseline_id,
        "final_artifact_path": result.final_artifact_path,
        "out_path": str(out) if not args.dry_run and result.status == BuildStatus.CONTRACT_READY else None,
    }
    if result.contract is not None:
        payload["renderer_route"] = result.contract.renderer_route
        payload["subtitle_materialization"] = result.contract.subtitle_materialization

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(result.status.value)
        for err in result.errors:
            print(err, file=sys.stderr)

    if result.status == BuildStatus.CONTRACT_READY:
        if not args.dry_run and out.is_file():
            _ = load_final_render_contract(out)
        return 0
    if result.status == BuildStatus.INCOMPLETE:
        return 2
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

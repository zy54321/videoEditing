#!/usr/bin/env python3
"""Apply static_portrait_reframe plan bulk_ops on current Resolve timeline (local API)."""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path


def _mcp_root(explicit: str | None) -> Path:
    if explicit:
        return Path(explicit)
    env = os.environ.get("DAVINCI_RESOLVE_MCP_ROOT", "").strip()
    if env:
        return Path(env)
    raise RuntimeError(
        "DAVINCI_RESOLVE_MCP_ROOT unset — set to davinci-resolve-mcp install root or pass --mcp-root"
    )


def main() -> int:
    ap = argparse.ArgumentParser(description="Apply static portrait reframe bulk_ops via Resolve API")
    ap.add_argument("--plan", type=Path, required=True)
    ap.add_argument("--expected-timeline", type=str, default="", help="Fail if current timeline name differs")
    ap.add_argument("--result-out", type=Path, help="JSON summary (default: beside plan)")
    ap.add_argument("--mcp-root", type=str, default="")
    args = ap.parse_args()

    plan = json.loads(args.plan.read_text(encoding="utf-8"))
    ops = plan.get("bulk_ops") or []
    if not ops:
        print("NO_OPS", file=sys.stderr)
        return 2

    mcp_root = _mcp_root(args.mcp_root or None)
    sys.path.insert(0, str(mcp_root))
    sys.path.insert(0, str(mcp_root / "src"))

    from src.server import _timeline_bulk_set_item_properties  # noqa: E402
    from src.utils.resolve_connection import initialize_resolve  # noqa: E402

    resolve = initialize_resolve()
    if resolve is None:
        print("RESOLVE_UNAVAILABLE", file=sys.stderr)
        return 3
    project = resolve.GetProjectManager().GetCurrentProject()
    if project is None:
        print("NO_PROJECT", file=sys.stderr)
        return 4
    tl = project.GetCurrentTimeline()
    if tl is None:
        print("NO_TIMELINE", file=sys.stderr)
        return 5
    name = tl.GetName()
    expected = (args.expected_timeline or plan.get("timeline_name") or "").strip()
    if expected and name != expected:
        print(f"WRONG_TIMELINE: {name} expected {expected}", file=sys.stderr)
        return 6

    mid = (len(ops) + 1) // 2
    batches = [ops[:mid], ops[mid:]]
    summary = []
    for i, batch in enumerate(batches):
        if not batch:
            continue
        result = _timeline_bulk_set_item_properties(
            tl, {"ops": batch, "readback": i == len(batches) - 1}
        )
        ok = sum(1 for r in result.get("results", []) if r.get("success"))
        summary.append({"batch": i, "ok": ok, "total": len(batch), "success": result.get("success")})
        if not result.get("success"):
            fail_path = args.plan.parent / f"bulk_apply_fail_batch_{i}.json"
            fail_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
            print(json.dumps(summary, ensure_ascii=False), file=sys.stderr)
            return 7

    out_doc = {
        "timeline": name,
        "op_count": len(ops),
        "batches": summary,
        "policy_id": plan.get("policy_id"),
    }
    result_out = args.result_out or (args.plan.parent / "static-portrait-reframe-apply-result.json")
    result_out.parent.mkdir(parents=True, exist_ok=True)
    result_out.write_text(json.dumps(out_doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(out_doc, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

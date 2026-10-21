#!/usr/bin/env python3
"""P0-T02 F06 — cue.text must match cue.lines under frozen-script normalization."""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAYLOAD = ROOT / "payload"
TOOLS = PAYLOAD / "video-workflow" / "tools"
LIB = TOOLS / "lib"
FIX = Path(__file__).resolve().parent / "fixtures" / "voice-subtitle-review"
VOICE_BRIEF = (
    Path(__file__).resolve().parent
    / "fixtures"
    / "brief-final-render-contract"
    / "voice-only-brief.yaml"
)
NO_SUB_BRIEF = (
    Path(__file__).resolve().parent
    / "fixtures"
    / "brief-final-render-contract"
    / "voice-no-subtitles-brief.yaml"
)
SCRIPT_FIX = Path(__file__).resolve().parent / "fixtures" / "r1-subtitle-production-e2e"
TMP = Path(__file__).resolve().parent / ".tmp-f06"

sys.path.insert(0, str(LIB))

from brief_final_render_contract import validate_render_preparation_canonical_binding  # noqa: E402
from validate_canonical_subtitle_authority_gate import (  # noqa: E402
    validate_canonical_subtitle_authority_gate,
)
from voice_subtitle_review import approval_allows_canonical, sha256_text  # noqa: E402

PASS = 0
FAIL = 0
TEXT = "你好世界"


def check(cond: bool, name: str) -> None:
    global PASS, FAIL
    if cond:
        print(f"[PASS] {name}")
        PASS += 1
    else:
        print(f"[FAIL] {name}")
        FAIL += 1


def new_voice_ws(name: str) -> Path:
    ws = TMP / name
    if ws.exists():
        shutil.rmtree(ws)
    prod = ws / "video-workflow" / "production"
    tpl = ws / "video-workflow" / "templates"
    prod.mkdir(parents=True)
    tpl.mkdir(parents=True)
    for fname in (
        "subtitle-external-ass-style-baseline.v1.json",
        "subtitle-series-style-registry.v1.json",
    ):
        shutil.copy(PAYLOAD / "video-workflow" / "templates" / fname, tpl / fname)
    shutil.copytree(TOOLS, ws / "video-workflow" / "tools")
    shutil.copy(VOICE_BRIEF, prod / "brief.yaml")
    shutil.copy(FIX / "narration.wav", ws / "narration.wav")
    shutil.copy(FIX / "asr-primary-provenance.json", prod / "asr-timing-evidence.json")
    shutil.copy(FIX / "asr-alt-provenance.json", prod / "asr-timing-evidence-alt.json")
    return ws


def approve_and_build(ws: Path, text: str) -> None:
    prod = ws / "video-workflow" / "production"
    subprocess.run(
        [
            sys.executable,
            str(TOOLS / "run-voice-subtitle-review.py"),
            "--workspace",
            str(ws),
            "--brief",
            str(prod / "brief.yaml"),
        ],
        check=False,
    )
    (prod / "reviewed-subtitle-text.txt").write_text(text + "\n", encoding="utf-8")
    intent = {
        "schema_version": 1,
        "production_id": "voice-u2",
        "reviewed_text_sha256": sha256_text(text.strip()),
        "owner_display_name": "OwnerHuman",
        "confirmation_phrase": "I_APPROVE_VOICE_SUBTITLE_TEXT",
        "owner_confirmed": True,
    }
    (prod / "voice-subtitle-owner-approval-intent.json").write_text(
        json.dumps(intent, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    subprocess.run(
        [
            sys.executable,
            str(TOOLS / "record-voice-subtitle-owner-approval.py"),
            "--workspace",
            str(ws),
        ],
        check=True,
    )
    subprocess.run(
        [
            "powershell",
            "-NoProfile",
            "-File",
            str(TOOLS / "invoke-frozen-script-subtitle-route.ps1"),
            "-WorkspaceRoot",
            str(ws),
            "-NoPause",
        ],
        check=True,
    )


def regen(prod: Path) -> dict:
    result = validate_canonical_subtitle_authority_gate(
        canonical_path=prod / "canonical-subtitle-cues.json",
        frozen_script_path=prod / "reviewed-subtitle-text.txt",
        asr_path=prod / "asr-timing-evidence.json",
    )
    (prod / "subtitle-canonical-gate-result.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return result


def main() -> int:
    if TMP.exists():
        shutil.rmtree(TMP)
    TMP.mkdir(parents=True)

    ws = new_voice_ws("voice")
    approve_and_build(ws, TEXT)
    prod = ws / "video-workflow" / "production"
    canonical_path = prod / "canonical-subtitle-cues.json"
    original = json.loads(canonical_path.read_text(encoding="utf-8-sig"))
    ok, reason = approval_allows_canonical(ws, prod / "brief.yaml")
    check(ok, f"approval valid before mutation ({reason})")

    baseline = regen(prod)
    check(baseline.get("verdict") == "PASS", f"baseline gate PASS ({baseline.get('errors')})")

    # 1. text stays correct, lines disagree
    bad = json.loads(json.dumps(original))
    bad["cues"][0]["lines"] = ["错误行"]
    canonical_path.write_text(json.dumps(bad, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    mismatched = regen(prod)
    codes = mismatched.get("errors") or []
    check(mismatched.get("verdict") == "FAIL", "bad lines gate FAIL")
    check(
        any(str(e).startswith("CUE_LINES_TEXT_MISMATCH") for e in codes),
        f"CUE_LINES_TEXT_MISMATCH present ({codes})",
    )
    check(bool(mismatched.get("canonical_sha256")), "regenerated gate still has canonical sha")
    check(bool(mismatched.get("frozen_script_sha256")), "regenerated gate still has text sha")
    prep = validate_render_preparation_canonical_binding(ws, prod / "brief.yaml")
    check(bool(prep), f"render prep blocks bad lines ({prep})")

    # 2–3. legal two-line layout matches text and external confirmed script
    good = json.loads(json.dumps(original))
    good["cues"][0]["text"] = "你好\n世界"
    good["cues"][0]["lines"] = ["你好", "世界"]
    canonical_path.write_text(json.dumps(good, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    aligned = regen(prod)
    check(aligned.get("verdict") == "PASS", f"legal two-line gate PASS ({aligned.get('errors')})")
    prep_ok = validate_render_preparation_canonical_binding(ws, prod / "brief.yaml")
    check(prep_ok == [], f"render prep clean for legal lines ({prep_ok})")

    # missing lines fail-closed
    missing = json.loads(json.dumps(original))
    missing["cues"][0].pop("lines", None)
    canonical_path.write_text(json.dumps(missing, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    missing_gate = regen(prod)
    check(
        any(str(e).startswith("CUE_LINES_INVALID") for e in (missing_gate.get("errors") or [])),
        f"missing lines fail-closed ({missing_gate.get('errors')})",
    )

    # script route still passes, and the same lines mutation fails there too
    ws_g = TMP / "script"
    prod_g = ws_g / "video-workflow" / "production"
    prod_g.mkdir(parents=True)
    shutil.copytree(TOOLS, ws_g / "video-workflow" / "tools")
    shutil.copy(SCRIPT_FIX / "brief.yaml", prod_g / "brief.yaml")
    shutil.copy(SCRIPT_FIX / "frozen-script.txt", prod_g / "frozen-script.txt")
    shutil.copy(SCRIPT_FIX / "asr-timing-evidence.json", prod_g / "asr-timing-evidence.json")
    subprocess.run(
        [
            "powershell",
            "-NoProfile",
            "-File",
            str(TOOLS / "invoke-frozen-script-subtitle-route.ps1"),
            "-WorkspaceRoot",
            str(ws_g),
            "-NoPause",
        ],
        check=True,
    )
    script_gate = validate_canonical_subtitle_authority_gate(
        canonical_path=prod_g / "canonical-subtitle-cues.json",
        brief_path=prod_g / "brief.yaml",
        asr_path=prod_g / "asr-timing-evidence.json",
    )
    check(script_gate.get("verdict") == "PASS", f"script route PASS ({script_gate.get('errors')})")
    script_doc = json.loads((prod_g / "canonical-subtitle-cues.json").read_text(encoding="utf-8-sig"))
    script_doc["cues"][0]["lines"] = ["坏行"]
    (prod_g / "canonical-subtitle-cues.json").write_text(
        json.dumps(script_doc, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    script_bad = validate_canonical_subtitle_authority_gate(
        canonical_path=prod_g / "canonical-subtitle-cues.json",
        brief_path=prod_g / "brief.yaml",
        asr_path=prod_g / "asr-timing-evidence.json",
    )
    check(script_bad.get("verdict") == "FAIL", "script route rejects bad lines")
    prep_g = validate_render_preparation_canonical_binding(ws_g, prod_g / "brief.yaml")
    check(prep_g == [], f"script render prep binding skip ({prep_g})")

    ws_h = new_voice_ws("no-subs")
    shutil.copy(NO_SUB_BRIEF, ws_h / "video-workflow" / "production" / "brief.yaml")
    prep_h = validate_render_preparation_canonical_binding(
        ws_h, ws_h / "video-workflow" / "production" / "brief.yaml"
    )
    check(prep_h == [], f"subtitles false ({prep_h})")

    shutil.rmtree(TMP, ignore_errors=True)
    print(f"Results: {PASS} passed, {FAIL} failed")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

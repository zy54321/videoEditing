#!/usr/bin/env python3
"""P0-T02-R4 — F02 canonical text authority mismatch (direct gate + render prep)."""
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
TMP = Path(__file__).resolve().parent / ".tmp-r4-f02"

sys.path.insert(0, str(LIB))

from brief_final_render_contract import validate_render_preparation_canonical_binding  # noqa: E402
from validate_canonical_subtitle_authority_gate import (  # noqa: E402
    validate_canonical_subtitle_authority_gate,
)
from voice_subtitle_review import approval_allows_canonical, sha256_text  # noqa: E402

PASS = 0
FAIL = 0
OLD_TEXT = "你好世界"
NEW_TEXT = "你好世间"


def check(cond: bool, name: str) -> None:
    global PASS, FAIL
    if cond:
        print(f"[PASS] {name}")
        PASS += 1
    else:
        print(f"[FAIL] {name}")
        FAIL += 1


def new_ws(name: str) -> Path:
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


def run_review(ws: Path) -> None:
    subprocess.run(
        [
            sys.executable,
            str(TOOLS / "run-voice-subtitle-review.py"),
            "--workspace",
            str(ws),
            "--brief",
            str(ws / "video-workflow" / "production" / "brief.yaml"),
        ],
        check=False,
    )


def approve(ws: Path, text: str) -> None:
    prod = ws / "video-workflow" / "production"
    reviewed = prod / "reviewed-subtitle-text.txt"
    reviewed.write_text(text + "\n", encoding="utf-8")
    digest = sha256_text(text.strip())
    intent = {
        "schema_version": 1,
        "production_id": "voice-u2",
        "reviewed_text_sha256": digest,
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


def build_canonical(ws: Path) -> None:
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


def prepare_old_canonical_new_approval(ws: Path) -> None:
    run_review(ws)
    approve(ws, OLD_TEXT)
    build_canonical(ws)
    approve(ws, NEW_TEXT)


def main() -> int:
    if TMP.exists():
        shutil.rmtree(TMP)
    TMP.mkdir(parents=True)

    # A: valid approval for new text, canonical still old; real gate regen must FAIL
    ws_a = new_ws("mismatch")
    prepare_old_canonical_new_approval(ws_a)
    prod_a = ws_a / "video-workflow" / "production"
    ok_appr, appr_reason = approval_allows_canonical(ws_a, prod_a / "brief.yaml")
    check(ok_appr, f"A approval still valid ({appr_reason})")
    live = validate_canonical_subtitle_authority_gate(
        canonical_path=prod_a / "canonical-subtitle-cues.json",
        frozen_script_path=prod_a / "reviewed-subtitle-text.txt",
        asr_path=prod_a / "asr-timing-evidence.json",
    )
    (prod_a / "subtitle-canonical-gate-result.json").write_text(
        json.dumps(live, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    errs = set(live.get("errors") or [])
    check(live.get("verdict") == "FAIL", "A regenerated gate FAIL")
    check(
        "EXTERNAL_CONFIRMED_TEXT_EMBEDDED_MISMATCH" in errs,
        "A embedded text != external confirmed text",
    )
    check("CUE_TEXT_DRIFT_FROM_FROZEN_SCRIPT" in errs, "A cues != external confirmed text")
    prep = validate_render_preparation_canonical_binding(ws_a, prod_a / "brief.yaml")
    check(bool(prep), f"A render prep blocked ({prep})")

    # B: consistent artifacts, old gate format without SHA fields
    ws_b = new_ws("old-gate")
    run_review(ws_b)
    approve(ws_b, OLD_TEXT)
    build_canonical(ws_b)
    prod_b = ws_b / "video-workflow" / "production"
    gate_path = prod_b / "subtitle-canonical-gate-result.json"
    gate = json.loads(gate_path.read_text(encoding="utf-8-sig"))
    check(gate.get("verdict") == "PASS", "B baseline gate PASS")
    gate.pop("canonical_sha256", None)
    gate.pop("frozen_script_sha256", None)
    gate_path.write_text(json.dumps(gate, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    prep_b = validate_render_preparation_canonical_binding(ws_b, prod_b / "brief.yaml")
    check("CANONICAL_GATE_SHA_MISSING" in prep_b, f"B missing SHA blocked ({prep_b})")

    # C: canonical SHA present, confirmed-text SHA absent
    gate = json.loads(gate_path.read_text(encoding="utf-8-sig"))
    # restore canonical sha from a fresh validation, then drop text sha
    fresh = validate_canonical_subtitle_authority_gate(
        canonical_path=prod_b / "canonical-subtitle-cues.json",
        frozen_script_path=prod_b / "reviewed-subtitle-text.txt",
        asr_path=prod_b / "asr-timing-evidence.json",
    )
    check(fresh.get("verdict") == "PASS", "C consistent live gate PASS")
    fresh.pop("frozen_script_sha256", None)
    gate_path.write_text(json.dumps(fresh, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    prep_c = validate_render_preparation_canonical_binding(ws_b, prod_b / "brief.yaml")
    check(
        "CANONICAL_GATE_TEXT_SHA_MISSING" in prep_c,
        f"C missing text SHA blocked ({prep_c})",
    )

    # D: gate path does not match current canonical
    fresh = validate_canonical_subtitle_authority_gate(
        canonical_path=prod_b / "canonical-subtitle-cues.json",
        frozen_script_path=prod_b / "reviewed-subtitle-text.txt",
        asr_path=prod_b / "asr-timing-evidence.json",
    )
    fresh["canonical_path"] = str(prod_b / "other-canonical.json")
    gate_path.write_text(json.dumps(fresh, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    prep_d = validate_render_preparation_canonical_binding(ws_b, prod_b / "brief.yaml")
    check("CANONICAL_GATE_PATH_MISMATCH" in prep_d, f"D path mismatch ({prep_d})")

    # E: canonical bytes change after gate
    fresh = validate_canonical_subtitle_authority_gate(
        canonical_path=prod_b / "canonical-subtitle-cues.json",
        frozen_script_path=prod_b / "reviewed-subtitle-text.txt",
        asr_path=prod_b / "asr-timing-evidence.json",
    )
    gate_path.write_text(json.dumps(fresh, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    canonical_p = prod_b / "canonical-subtitle-cues.json"
    doc = json.loads(canonical_p.read_text(encoding="utf-8-sig"))
    doc["cues"][0]["text"] = "篡改"
    canonical_p.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    prep_e = validate_render_preparation_canonical_binding(ws_b, prod_b / "brief.yaml")
    check("CANONICAL_GATE_FILE_DRIFT" in prep_e, f"E canonical drift ({prep_e})")

    # F: new confirmed text, rebuilt canonical, regenerated gate — PASS
    ws_f = new_ws("aligned")
    run_review(ws_f)
    approve(ws_f, NEW_TEXT)
    build_canonical(ws_f)
    prod_f = ws_f / "video-workflow" / "production"
    aligned = validate_canonical_subtitle_authority_gate(
        canonical_path=prod_f / "canonical-subtitle-cues.json",
        frozen_script_path=prod_f / "reviewed-subtitle-text.txt",
        asr_path=prod_f / "asr-timing-evidence.json",
    )
    (prod_f / "subtitle-canonical-gate-result.json").write_text(
        json.dumps(aligned, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    prep_f = validate_render_preparation_canonical_binding(ws_f, prod_f / "brief.yaml")
    check(aligned.get("verdict") == "PASS", "F aligned gate PASS")
    check(prep_f == [], f"F render prep clean ({prep_f})")

    # G: script route gate still PASS; render prep skips voice binding
    ws_g = TMP / "script"
    if ws_g.exists():
        shutil.rmtree(ws_g)
    prod_g = ws_g / "video-workflow" / "production"
    prod_g.mkdir(parents=True)
    shutil.copytree(TOOLS, ws_g / "video-workflow" / "tools")
    shutil.copy(SCRIPT_FIX / "brief.yaml", prod_g / "brief.yaml")
    shutil.copy(SCRIPT_FIX / "frozen-script.txt", prod_g / "frozen-script.txt")
    shutil.copy(SCRIPT_FIX / "asr-timing-evidence.json", prod_g / "asr-timing-evidence.json")
    build_canonical(ws_g)
    script_gate = validate_canonical_subtitle_authority_gate(
        canonical_path=prod_g / "canonical-subtitle-cues.json",
        brief_path=prod_g / "brief.yaml",
        asr_path=prod_g / "asr-timing-evidence.json",
    )
    check(script_gate.get("verdict") == "PASS", f"G script gate PASS ({script_gate.get('errors')})")
    prep_g = validate_render_preparation_canonical_binding(ws_g, prod_g / "brief.yaml")
    check(prep_g == [], f"G script render prep skip ({prep_g})")

    # H: subtitles false
    ws_h = new_ws("no-subs")
    shutil.copy(NO_SUB_BRIEF, ws_h / "video-workflow" / "production" / "brief.yaml")
    prep_h = validate_render_preparation_canonical_binding(
        ws_h, ws_h / "video-workflow" / "production" / "brief.yaml"
    )
    check(prep_h == [], f"H subtitles false ({prep_h})")

    shutil.rmtree(TMP, ignore_errors=True)
    print(f"Results: {PASS} passed, {FAIL} failed")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

"""Deterministic Production Brief → Final Render Contract (U2)."""
from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

import yaml

from brief_subtitle_authority import voice_subtitle_review_pending
from external_ass_style_baseline import default_baseline_path, load_baseline
from voice_subtitle_review import approval_allows_canonical
from final_render_contract import (
    DELIVER_AUTHORITY_FINAL_MP4,
    EXPORT_MODE_BURN_IN,
    EXPORT_MODE_SEPARATE,
    MATERIALIZATION_EXTERNAL,
    MATERIALIZATION_NA,
    MATERIALIZATION_NATIVE,
    FinalRenderContract,
    load_final_render_contract,
    save_final_render_contract,
)

ROUTE_NATIVE = "native_drt"
ROUTE_EXTERNAL = "external_ass"

SERIES_REF_PATTERN = re.compile(r"^[a-z0-9][a-z0-9._:-]{0,127}$")


class BuildStatus(str, Enum):
    """CONTRACT_READY = brief→contract OK; not FINAL_ARTIFACT_GATE / delivery PASS (U3)."""

    CONTRACT_READY = "CONTRACT_READY"
    INCOMPLETE = "INCOMPLETE"
    BLOCKED = "BLOCKED"


@dataclass(frozen=True)
class BriefContractBuildResult:
    status: BuildStatus
    errors: tuple[str, ...]
    contract: FinalRenderContract | None = None
    resolved_baseline_id: str | None = None
    final_artifact_path: str | None = None


def load_brief_yaml(brief_path: Path) -> dict[str, Any]:
    brief_path = brief_path.resolve()
    if not brief_path.is_file():
        raise FileNotFoundError(f"BRIEF_NOT_FOUND: {brief_path}")
    return yaml.safe_load(brief_path.read_text(encoding="utf-8-sig")) or {}


def production_subdir(workspace_root: Path) -> Path:
    return workspace_root.resolve() / "video-workflow" / "production"


def default_series_style_registry_path(templates_dir: Path) -> Path:
    return templates_dir / "subtitle-series-style-registry.v1.json"


def load_series_style_registry(path: Path) -> dict[str, str]:
    if not path.is_file():
        return {}
    import json

    doc = json.loads(path.read_text(encoding="utf-8-sig"))
    refs = doc.get("refs") or {}
    return {str(k): str(v) for k, v in refs.items()}


def resolve_path_string(raw: str, *, workspace_root: Path, brief_dir: Path) -> Path:
    text = (raw or "").strip()
    if not text:
        raise ValueError("PATH_EMPTY")
    p = Path(text)
    if p.is_absolute():
        return p.resolve()
    # Workspace-relative first (bound media paths), then brief-adjacent.
    candidate = (workspace_root / p).resolve()
    if candidate.exists() or not (brief_dir / p).exists():
        return candidate
    return (brief_dir / p).resolve()


def resolve_final_artifact_path(brief: dict[str, Any], *, workspace_root: Path, brief_dir: Path) -> Path:
    media = brief.get("media") or {}
    output = brief.get("output") or {}
    out_dir = str(media.get("output") or "").strip()
    filename = str(output.get("filename") or "").strip()
    if not out_dir or not filename:
        raise ValueError("BRIEF_OUTPUT_PATH_INCOMPLETE")
    return resolve_path_string(str(Path(out_dir) / filename), workspace_root=workspace_root, brief_dir=brief_dir)


def paths_equal(a: Path, b: Path) -> bool:
    try:
        return a.resolve() == b.resolve()
    except OSError:
        return False


def _voice_subtitle_contract_incomplete(
    brief: dict[str, Any],
    *,
    workspace_root: Path,
    brief_path: Path,
) -> tuple[bool, str]:
    if not voice_subtitle_review_pending(brief):
        return False, ""
    ok, reason = approval_allows_canonical(workspace_root, brief_path)
    if ok:
        return False, ""
    return True, reason or "VOICE_SUBTITLE_REVIEW_PENDING"


def validate_baseline_id(baseline_id: str, *, templates_dir: Path) -> None:
    bid = (baseline_id or "").strip()
    if not bid:
        raise ValueError("EXTERNAL_ASS_BASELINE_ID_REQUIRED")
    tools_dir = templates_dir.parent / "tools"
    path = default_baseline_path(tools_dir)
    if not path.is_file():
        raise ValueError(f"EXTERNAL_ASS_BASELINE_UNKNOWN: {bid}")
    doc_baseline_id = load_baseline(path).get("baseline_id")
    if doc_baseline_id != bid:
        raise ValueError(f"EXTERNAL_ASS_BASELINE_UNKNOWN: {bid}")


def resolve_style_baseline_id(
    delivery: dict[str, Any],
    *,
    templates_dir: Path,
) -> str | None:
    explicit = str(delivery.get("external_ass_style_baseline_id") or "").strip()
    series_ref = str(delivery.get("subtitle_series_style_ref") or "").strip()

    if series_ref:
        if not SERIES_REF_PATTERN.match(series_ref):
            raise ValueError(f"SUBTITLE_SERIES_STYLE_REF_INVALID: {series_ref}")
        registry_path = default_series_style_registry_path(templates_dir)
        registry = load_series_style_registry(registry_path)
        mapped = registry.get(series_ref)
        if not mapped:
            raise ValueError(f"SUBTITLE_SERIES_STYLE_REF_UNRESOLVED: {series_ref}")
        if explicit and explicit != mapped:
            raise ValueError("SUBTITLE_STYLE_BASELINE_CONFLICT")
        validate_baseline_id(mapped, templates_dir=templates_dir)
        return mapped

    if explicit:
        validate_baseline_id(explicit, templates_dir=templates_dir)
        return explicit

    return None


def resolve_subtitle_renderer_route(brief: dict[str, Any]) -> str | None:
    delivery = brief.get("delivery") or {}
    route = str(delivery.get("subtitle_renderer_route") or "").strip().lower()
    if route:
        return route
    features = brief.get("features") or {}
    if features.get("subtitles") is False:
        return None
    # Legacy briefs without delivery: default native DRT when subtitles enabled.
    if "delivery" not in brief:
        return ROUTE_NATIVE
    return None


def build_final_render_contract_from_brief(
    *,
    brief_path: Path,
    workspace_root: Path,
    templates_dir: Path | None = None,
) -> BriefContractBuildResult:
    brief_path = brief_path.resolve()
    workspace_root = workspace_root.resolve()
    brief = load_brief_yaml(brief_path)
    brief_dir = brief_path.parent
    templates = (templates_dir or (workspace_root / "video-workflow" / "templates")).resolve()
    prod = production_subdir(workspace_root)

    pending, pending_reason = _voice_subtitle_contract_incomplete(
        brief, workspace_root=workspace_root, brief_path=brief_path
    )
    if pending:
        return BriefContractBuildResult(
            status=BuildStatus.INCOMPLETE,
            errors=(pending_reason or "VOICE_SUBTITLE_REVIEW_PENDING",),
        )

    try:
        final_path = resolve_final_artifact_path(brief, workspace_root=workspace_root, brief_dir=brief_dir)
    except ValueError as e:
        return BriefContractBuildResult(status=BuildStatus.INCOMPLETE, errors=(str(e),))

    features = brief.get("features") or {}
    subtitles = features.get("subtitles") is not False
    delivery = brief.get("delivery") or {}
    delivery_ready = delivery.get("ready")
    if delivery_ready is False:
        return BriefContractBuildResult(status=BuildStatus.INCOMPLETE, errors=("DELIVERY_NOT_READY",))

    route = resolve_subtitle_renderer_route(brief)
    if subtitles and not route:
        return BriefContractBuildResult(
            status=BuildStatus.INCOMPLETE,
            errors=("SUBTITLE_RENDERER_ROUTE_REQUIRED",),
        )

    fmt = brief.get("format") or {}
    width = int(fmt.get("width") or 1080)
    height = int(fmt.get("height") or 1920)
    fps = float(fmt.get("fps") or 24)
    runtime = brief.get("runtime") or {}
    timeline = str(runtime.get("timeline_name") or "").strip() or "Production Timeline"

    production = brief.get("production") or {}
    prod_id = str(production.get("id") or "production").strip() or "production"
    canonical = str(prod / "canonical-subtitle-cues.json")

    resolved_baseline: str | None = None
    try:
        if route == ROUTE_EXTERNAL:
            resolved_baseline = resolve_style_baseline_id(delivery, templates_dir=templates)
            if not resolved_baseline:
                return BriefContractBuildResult(
                    status=BuildStatus.BLOCKED,
                    errors=("EXTERNAL_ASS_BASELINE_ID_REQUIRED",),
                )
        elif route == ROUTE_NATIVE:
            if delivery.get("external_ass_style_baseline_id") or delivery.get("subtitle_series_style_ref"):
                return BriefContractBuildResult(
                    status=BuildStatus.BLOCKED,
                    errors=("NATIVE_ROUTE_EXTERNAL_STYLE_FIELDS_FORBIDDEN",),
                )
        elif route:
            return BriefContractBuildResult(
                status=BuildStatus.BLOCKED,
                errors=(f"SUBTITLE_RENDERER_ROUTE_INVALID: {route}",),
            )
    except ValueError as e:
        return BriefContractBuildResult(status=BuildStatus.BLOCKED, errors=(str(e),))

    if not subtitles or route is None:
        contract = FinalRenderContract(
            renderer_route=ROUTE_NATIVE,
            render_source_timeline=timeline,
            final_artifact_path=str(final_path),
            subtitle_materialization=MATERIALIZATION_NA,
            burnin_method="",
            canonical_subtitle_cues_path=None,
            clean_master_path=None,
            expected_width=width,
            expected_height=height,
            expected_fps=fps,
            resolve_subtitle_export_mode=None,
            deliver_authority=DELIVER_AUTHORITY_FINAL_MP4,
        )
        return BriefContractBuildResult(
            status=BuildStatus.CONTRACT_READY,
            errors=(),
            contract=contract,
            final_artifact_path=str(final_path),
        )

    if route == ROUTE_NATIVE:
        contract = FinalRenderContract(
            renderer_route=ROUTE_NATIVE,
            render_source_timeline=timeline,
            final_artifact_path=str(final_path),
            subtitle_materialization=MATERIALIZATION_NATIVE,
            burnin_method="resolve_export_burn_in",
            canonical_subtitle_cues_path=canonical,
            clean_master_path=None,
            expected_width=width,
            expected_height=height,
            expected_fps=fps,
            resolve_subtitle_export_mode=EXPORT_MODE_BURN_IN,
            deliver_authority=DELIVER_AUTHORITY_FINAL_MP4,
        )
        return BriefContractBuildResult(
            status=BuildStatus.CONTRACT_READY,
            errors=(),
            contract=contract,
            resolved_baseline_id=resolved_baseline,
            final_artifact_path=str(final_path),
        )

    clean_master = str(prod / f"{prod_id}_clean_master.mp4")
    series_ref = str(delivery.get("subtitle_series_style_ref") or "").strip() or None
    contract = FinalRenderContract(
        renderer_route=ROUTE_EXTERNAL,
        render_source_timeline=timeline,
        final_artifact_path=str(final_path),
        subtitle_materialization=MATERIALIZATION_EXTERNAL,
        burnin_method="ffmpeg_libass",
        canonical_subtitle_cues_path=canonical,
        clean_master_path=clean_master,
        expected_width=width,
        expected_height=height,
        expected_fps=fps,
        resolve_subtitle_export_mode=EXPORT_MODE_SEPARATE,
        deliver_authority=DELIVER_AUTHORITY_FINAL_MP4,
        external_ass_style_baseline_id=resolved_baseline,
        subtitle_series_style_ref=series_ref,
    )
    return BriefContractBuildResult(
        status=BuildStatus.CONTRACT_READY,
        errors=(),
        contract=contract,
        resolved_baseline_id=resolved_baseline,
        final_artifact_path=str(final_path),
    )


def validate_contract_matches_brief(
    brief: dict[str, Any],
    contract: FinalRenderContract,
    *,
    workspace_root: Path,
    brief_dir: Path,
    templates_dir: Path | None = None,
) -> list[str]:
    errors: list[str] = []
    try:
        expected = resolve_final_artifact_path(brief, workspace_root=workspace_root, brief_dir=brief_dir)
    except ValueError as e:
        errors.append(str(e))
        return errors
    actual = Path(contract.final_artifact_path)
    if not paths_equal(expected, actual):
        errors.append("BRIEF_CONTRACT_FINAL_PATH_MISMATCH")
    delivery = brief.get("delivery") or {}
    route_brief = str(delivery.get("subtitle_renderer_route") or "").strip().lower()
    if route_brief and route_brief != contract.renderer_route:
        errors.append("BRIEF_CONTRACT_RENDERER_ROUTE_MISMATCH")
    templates = (templates_dir or (workspace_root / "video-workflow" / "templates")).resolve()
    if contract.renderer_route == ROUTE_EXTERNAL:
        try:
            resolved = resolve_style_baseline_id(delivery, templates_dir=templates)
        except ValueError as e:
            errors.append(str(e))
            resolved = None
        if resolved and contract.external_ass_style_baseline_id != resolved:
            errors.append("BRIEF_CONTRACT_BASELINE_MISMATCH")
        series_ref = str(delivery.get("subtitle_series_style_ref") or "").strip()
        if series_ref and contract.subtitle_series_style_ref != series_ref:
            errors.append("BRIEF_CONTRACT_SERIES_REF_MISMATCH")
    return errors


def validate_render_preparation_canonical_binding(
    workspace_root: Path,
    brief_path: Path,
) -> list[str]:
    """Voice + subtitles: CONTRACT_READY must not bypass canonical + gate evidence."""
    import json
    from pathlib import Path as PathLib

    from validate_canonical_subtitle_authority_gate import validate_canonical_subtitle_authority_gate
    from voice_subtitle_paths import asr_primary_path, reviewed_text_path
    from voice_subtitle_review import confirmed_text_sha256_from_fingerprints, sha256_file, sha256_text

    brief = load_brief_yaml(brief_path)
    features = brief.get("features") or {}
    if features.get("subtitles") is False:
        return []
    auth_type = str((brief.get("content") or {}).get("authority", {}).get("type") or "").strip().lower()
    if auth_type != "voice":
        return []
    ok, reason = approval_allows_canonical(workspace_root, brief_path)
    if not ok:
        return [reason or "VOICE_SUBTITLE_APPROVAL_INCOMPLETE"]
    prod = production_subdir(workspace_root)
    canonical = prod / "canonical-subtitle-cues.json"
    if not canonical.is_file():
        return ["CANONICAL_CUES_MISSING_FOR_RENDER"]
    gate_path = prod / "subtitle-canonical-gate-result.json"
    if not gate_path.is_file():
        return ["CANONICAL_GATE_RESULT_MISSING"]
    gate = json.loads(gate_path.read_text(encoding="utf-8-sig"))
    if gate.get("gate") != "SUBTITLE_CANONICAL_AUTHORITY_GATE":
        return ["CANONICAL_GATE_ID_MISMATCH"]
    if gate.get("verdict") != "PASS":
        return ["CANONICAL_GATE_NOT_PASS"]

    gate_canonical = str(gate.get("canonical_path") or "").strip()
    if not gate_canonical:
        return ["CANONICAL_GATE_PATH_MISSING"]
    if PathLib(gate_canonical).resolve() != canonical.resolve():
        return ["CANONICAL_GATE_PATH_MISMATCH"]

    canonical_sha = sha256_file(canonical)
    gate_canonical_sha = str(gate.get("canonical_sha256") or "").strip()
    if not gate_canonical_sha:
        return ["CANONICAL_GATE_SHA_MISSING"]
    if gate_canonical_sha != canonical_sha:
        return ["CANONICAL_GATE_FILE_DRIFT"]

    reviewed_p = reviewed_text_path(workspace_root)
    if not reviewed_p.is_file():
        return ["REVIEWED_TEXT_MISSING"]
    confirmed_sha = sha256_text(reviewed_p.read_text(encoding="utf-8-sig").strip())
    gate_text_sha = str(gate.get("frozen_script_sha256") or "").strip()
    if not gate_text_sha:
        return ["CANONICAL_GATE_TEXT_SHA_MISSING"]
    if gate_text_sha != confirmed_sha:
        return ["CANONICAL_GATE_TEXT_BINDING_DRIFT"]

    asr_p = asr_primary_path(workspace_root)
    live = validate_canonical_subtitle_authority_gate(
        canonical_path=canonical,
        frozen_script_path=reviewed_p,
        asr_path=asr_p if asr_p.is_file() else None,
    )
    if live.get("verdict") != "PASS":
        errs = live.get("errors") or [live.get("reason") or "CANONICAL_GATE_REVALIDATION_FAIL"]
        return [str(e) for e in errs]

    result_p = prod / "voice-subtitle-review-result.json"
    if result_p.is_file():
        result = json.loads(result_p.read_text(encoding="utf-8-sig"))
        fp = result.get("fingerprints") or {}
        bound = confirmed_text_sha256_from_fingerprints(fp)
        if bound and bound != confirmed_sha:
            return ["CANONICAL_CONFIRMED_TEXT_MISMATCH"]
    return []


def write_contract_from_brief(
    *,
    brief_path: Path,
    workspace_root: Path,
    out_path: Path,
    templates_dir: Path | None = None,
    force: bool = False,
) -> BriefContractBuildResult:
    result = build_final_render_contract_from_brief(
        brief_path=brief_path,
        workspace_root=workspace_root,
        templates_dir=templates_dir,
    )
    if result.status != BuildStatus.CONTRACT_READY or result.contract is None:
        return result
    out_path = out_path.resolve()
    brief = load_brief_yaml(brief_path)
    mism = validate_contract_matches_brief(
        brief,
        result.contract,
        workspace_root=workspace_root,
        brief_dir=brief_path.parent,
    )
    if mism:
        return BriefContractBuildResult(status=BuildStatus.BLOCKED, errors=tuple(mism))
    save_final_render_contract(out_path, result.contract)
    return result

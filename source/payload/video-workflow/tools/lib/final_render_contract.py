"""Final Render Contract — deliver authority = burned MP4 (JSON artifact)."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
DELIVER_AUTHORITY_FINAL_MP4 = "final_mp4_burned"

MATERIALIZATION_NATIVE = "native_drt_burnin"
MATERIALIZATION_EXTERNAL = "external_ass_burnin"
MATERIALIZATION_NA = "na"

EXPORT_MODE_BURN_IN = "burn_into_video"
EXPORT_MODE_SEPARATE = "separate_subtitle_file"


@dataclass(frozen=True)
class FinalRenderContract:
    renderer_route: str
    render_source_timeline: str
    final_artifact_path: str
    subtitle_materialization: str
    burnin_method: str
    canonical_subtitle_cues_path: str | None
    clean_master_path: str | None = None
    expected_width: int = 1080
    expected_height: int = 1920
    expected_fps: float = 24.0
    expected_duration_seconds: float | None = None
    resolve_subtitle_export_mode: str | None = None
    sidecar_subtitle_paths: tuple[str, ...] = ()
    deliver_authority: str = DELIVER_AUTHORITY_FINAL_MP4
    external_ass_style_baseline_id: str | None = None
    subtitle_series_style_ref: str | None = None

    def to_dict(self) -> dict[str, Any]:
        doc = {
            "schema_version": SCHEMA_VERSION,
            "deliver_authority": self.deliver_authority,
            "renderer_route": self.renderer_route,
            "render_source_timeline": self.render_source_timeline,
            "clean_master_path": self.clean_master_path,
            "final_artifact_path": self.final_artifact_path,
            "subtitle_materialization": self.subtitle_materialization,
            "burnin_method": self.burnin_method,
            "resolve_subtitle_export_mode": self.resolve_subtitle_export_mode,
            "sidecar_subtitle_paths": list(self.sidecar_subtitle_paths),
            "expected_resolution": {"width": self.expected_width, "height": self.expected_height},
            "expected_fps": self.expected_fps,
            "expected_duration_seconds": self.expected_duration_seconds,
            "canonical_subtitle_cues_path": self.canonical_subtitle_cues_path,
        }
        if self.external_ass_style_baseline_id:
            doc["external_ass_style_baseline_id"] = self.external_ass_style_baseline_id
        if self.subtitle_series_style_ref:
            doc["subtitle_series_style_ref"] = self.subtitle_series_style_ref
        return doc


def load_final_render_contract(path: Path) -> FinalRenderContract:
    path = path.resolve()
    doc = json.loads(path.read_text(encoding="utf-8-sig"))
    res = doc.get("expected_resolution") or {}
    side = doc.get("sidecar_subtitle_paths") or []
    return FinalRenderContract(
        renderer_route=str(doc.get("renderer_route", "")),
        render_source_timeline=str(doc.get("render_source_timeline", "")),
        clean_master_path=doc.get("clean_master_path"),
        final_artifact_path=str(doc.get("final_artifact_path", "")),
        subtitle_materialization=str(doc.get("subtitle_materialization", MATERIALIZATION_NA)),
        burnin_method=str(doc.get("burnin_method", "")),
        resolve_subtitle_export_mode=doc.get("resolve_subtitle_export_mode"),
        sidecar_subtitle_paths=tuple(str(p) for p in side),
        expected_width=int(res.get("width", doc.get("expected_width", 1080))),
        expected_height=int(res.get("height", doc.get("expected_height", 1920))),
        expected_fps=float(doc.get("expected_fps", 24)),
        expected_duration_seconds=doc.get("expected_duration_seconds"),
        canonical_subtitle_cues_path=doc.get("canonical_subtitle_cues_path"),
        deliver_authority=str(doc.get("deliver_authority", DELIVER_AUTHORITY_FINAL_MP4)),
        external_ass_style_baseline_id=doc.get("external_ass_style_baseline_id"),
        subtitle_series_style_ref=doc.get("subtitle_series_style_ref"),
    )


def save_final_render_contract(path: Path, contract: FinalRenderContract) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(contract.to_dict(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

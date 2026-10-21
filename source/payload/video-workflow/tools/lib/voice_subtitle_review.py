"""Voice subtitle text review — deterministic checks + safe degradation (U1)."""
from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

from asr_timing_evidence import AsrTimingEvidence, load_asr_timing_evidence
from brief_subtitle_authority import load_brief_dict
from asr_evidence_provenance import (
    AUTO_REVIEW_RUNTIME_AVAILABLE,
    assess_dual_asr_independence,
)
from voice_subtitle_paths import (
    approval_path,
    asr_draft_subtitle_text_path,
    asr_primary_path,
    asr_secondary_path,
    owner_approval_intent_path,
    review_result_path,
    reviewed_text_path,
)

OWNER_CONFIRMATION_PHRASE = "I_APPROVE_VOICE_SUBTITLE_TEXT"
FORBIDDEN_OWNER_ACTOR_PREFIXES = ("agent", "assistant", "cursor", "composer", "gpt", "claude")

SCHEMA_VERSION = 1

# Episode-2 style risks (rule triggers — not ASR accuracy claims).
HOMOPHONE_RISK_GROUPS: tuple[tuple[str, ...], ...] = (
    ("仿佛", "反复"),
    ("响起", "想起"),
)
SCRIPT_VARIANT_PAIRS: tuple[tuple[str, str], ...] = (
    ("债务", "債務"),
)


class ReviewStatus(str, Enum):
    AUTO_ACCEPTED = "AUTO_ACCEPTED"
    OWNER_ACCEPTED = "OWNER_ACCEPTED"
    NEEDS_OWNER_REVIEW = "NEEDS_OWNER_REVIEW"
    BLOCKED = "BLOCKED"
    NOT_APPLICABLE = "NOT_APPLICABLE"


@dataclass(frozen=True)
class ReviewAnomaly:
    start: float | None
    end: float | None
    anomaly_type: str
    original_text: str
    candidate_text: str
    rationale: str
    suggested_action: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "start": self.start,
            "end": self.end,
            "type": self.anomaly_type,
            "original_text": self.original_text,
            "candidate_text": self.candidate_text,
            "rationale": self.rationale,
            "suggested_action": self.suggested_action,
        }


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _nfc(s: str) -> str:
    return unicodedata.normalize("NFC", s)


def flatten_asr(ev: AsrTimingEvidence) -> str:
    return _nfc("".join(c.recognized_text.replace("\n", "") for c in ev.cues))


def production_id_from_brief(brief: dict[str, Any]) -> str:
    return str((brief.get("production") or {}).get("id") or "").strip()


def resolve_voice_audio_path(brief: dict[str, Any], workspace_root: Path) -> Path | None:
    content = brief.get("content") or {}
    authority = content.get("authority") or {}
    raw = str(authority.get("path") or "").strip()
    if not raw:
        return None
    p = Path(raw)
    if p.is_absolute():
        return p.resolve() if p.is_file() else p
    cand = (workspace_root / p).resolve()
    return cand if cand.is_file() else p


def confirmed_text_sha256_from_fingerprints(fp: dict[str, Any]) -> str:
    """Authority hash for Owner-confirmed subtitle text (post-approval)."""
    confirmed = str(fp.get("confirmed_reviewed_text_sha256") or "").strip()
    if confirmed:
        return confirmed
    return str(fp.get("reviewed_text_sha256") or "").strip()


def invalidate_owner_subtitle_approval(workspace_root: Path, *, reason: str) -> None:
    for p in (approval_path(workspace_root), owner_approval_intent_path(workspace_root)):
        if p.is_file():
            p.unlink()
    result_p = review_result_path(workspace_root)
    if result_p.is_file():
        result = json.loads(result_p.read_text(encoding="utf-8-sig"))
        if result.get("status") == ReviewStatus.OWNER_ACCEPTED.value:
            result["status"] = ReviewStatus.NEEDS_OWNER_REVIEW.value
            result["approval_invalidated_reason"] = reason
            result_p.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def validate_owner_approval_intent(
    intent: dict[str, Any],
    *,
    production_id: str,
    reviewed_text_sha256: str,
) -> list[str]:
    errors: list[str] = []
    if int(intent.get("schema_version", 0)) != SCHEMA_VERSION:
        errors.append("INTENT_SCHEMA_VERSION")
    if not intent.get("owner_confirmed"):
        errors.append("INTENT_OWNER_NOT_CONFIRMED")
    if intent.get("confirmation_phrase") != OWNER_CONFIRMATION_PHRASE:
        errors.append("INTENT_PHRASE_MISMATCH")
    if str(intent.get("production_id") or "").strip() != production_id:
        errors.append("INTENT_PRODUCTION_ID_MISMATCH")
    if str(intent.get("reviewed_text_sha256") or "").strip() != reviewed_text_sha256:
        errors.append("INTENT_TEXT_HASH_MISMATCH")
    name = str(intent.get("owner_display_name") or "").strip()
    if not name:
        errors.append("INTENT_OWNER_NAME_MISSING")
    low = name.lower()
    if any(low.startswith(p) for p in FORBIDDEN_OWNER_ACTOR_PREFIXES):
        errors.append("INTENT_OWNER_NAME_FORBIDDEN")
    return errors


def draft_reviewed_text_from_primary(ev: AsrTimingEvidence) -> str:
    """Draft text for review — not canonical authority until approved."""
    return flatten_asr(ev)


def _detect_timing_issues(ev: AsrTimingEvidence) -> list[ReviewAnomaly]:
    out: list[ReviewAnomaly] = []
    seen: dict[str, int] = {}
    for c in ev.cues:
        if c.end < c.start:
            out.append(
                ReviewAnomaly(
                    c.start,
                    c.end,
                    "TIMING_INVALID",
                    c.recognized_text,
                    "",
                    f"cue {c.cue_id} end < start",
                    "BLOCK",
                )
            )
        key = c.recognized_text.strip()
        if key:
            seen[key] = seen.get(key, 0) + 1
    for text, count in seen.items():
        if count > 1:
            out.append(
                ReviewAnomaly(
                    None,
                    None,
                    "DUPLICATE_CUE_TEXT",
                    text,
                    "",
                    f"repeated {count} times in ASR cues",
                    "OWNER_REVIEW",
                )
            )
    return out


def _detect_homophone_risks(text: str, alt_text: str | None) -> list[ReviewAnomaly]:
    out: list[ReviewAnomaly] = []
    for group in HOMOPHONE_RISK_GROUPS:
        hits = [w for w in group if w in text]
        if len(hits) >= 2:
            out.append(
                ReviewAnomaly(
                    None,
                    None,
                    "HOMOPHONE_AMBIGUITY",
                    hits[0],
                    hits[1],
                    f"multiple homophone-risk tokens in draft: {hits}",
                    "OWNER_REVIEW",
                )
            )
        elif len(hits) == 1 and alt_text:
            alt_hits = [w for w in group if w in alt_text and w != hits[0]]
            if alt_hits:
                out.append(
                    ReviewAnomaly(
                        None,
                        None,
                        "DUAL_ASR_HOMOPHONE_DIVERGENCE",
                        hits[0],
                        alt_hits[0],
                        "primary vs secondary ASR disagree on homophone-risk token",
                        "OWNER_REVIEW",
                    )
                )
    for simp, trad in SCRIPT_VARIANT_PAIRS:
        if simp in text and trad in text:
            out.append(
                ReviewAnomaly(
                    None,
                    None,
                    "SCRIPT_VARIANT_MIX",
                    simp,
                    trad,
                    "simplified and traditional forms both present",
                    "OWNER_REVIEW",
                )
            )
        if alt_text and ((simp in text and trad in alt_text) or (trad in text and simp in alt_text)):
            out.append(
                ReviewAnomaly(
                    None,
                    None,
                    "DUAL_ASR_SCRIPT_VARIANT",
                    text[:40],
                    alt_text[:40],
                    "primary/secondary differ by script variant",
                    "OWNER_REVIEW",
                )
            )
    return out


def _detect_negation_digit_keywords(text: str) -> list[ReviewAnomaly]:
    out: list[ReviewAnomaly] = []
    if re.search(r"\d", text):
        out.append(
            ReviewAnomaly(
                None,
                None,
                "NUMERIC_TOKEN_PRESENT",
                text[:60],
                "",
                "digits present — require owner or dual-ASR confirmation",
                "OWNER_REVIEW",
            )
        )
    return out


def run_voice_subtitle_review(
    *,
    workspace_root: Path,
    brief_path: Path,
    voice_audio_path: Path | None = None,
) -> dict[str, Any]:
    workspace_root = workspace_root.resolve()
    brief = load_brief_dict(brief_path)
    features = brief.get("features") or {}
    if features.get("subtitles") is False:
        return _result_doc(ReviewStatus.NOT_APPLICABLE, [], {}, brief, None, None, None)

    content = brief.get("content") or {}
    auth_type = (content.get("authority") or {}).get("type", "").strip().lower()
    assets = brief.get("assets") or {}
    if auth_type == "script" or bool((assets.get("script") or {}).get("frozen")):
        return _result_doc(ReviewStatus.NOT_APPLICABLE, [], {}, brief, None, None, None)

    if auth_type != "voice":
        return _result_doc(
            ReviewStatus.BLOCKED,
            [],
            {"reason": "VOICE_AUTHORITY_REQUIRED_FOR_VOICE_REVIEW"},
            brief,
            None,
            None,
            None,
        )

    primary_p = asr_primary_path(workspace_root)
    if not primary_p.is_file():
        return _result_doc(
            ReviewStatus.BLOCKED,
            [],
            {"reason": "ASR_TIMING_EVIDENCE_MISSING"},
            brief,
            None,
            None,
            None,
        )

    primary = load_asr_timing_evidence(primary_p)
    secondary_p = asr_secondary_path(workspace_root)
    secondary: AsrTimingEvidence | None = None
    if secondary_p.is_file():
        secondary = load_asr_timing_evidence(secondary_p)

    draft = draft_reviewed_text_from_primary(primary)
    alt_flat = flatten_asr(secondary) if secondary else None

    anomalies: list[ReviewAnomaly] = []
    anomalies.extend(_detect_timing_issues(primary))
    anomalies.extend(_detect_homophone_risks(draft, alt_flat))
    anomalies.extend(_detect_negation_digit_keywords(draft))

    if secondary is None:
        anomalies.append(
            ReviewAnomaly(
                None,
                None,
                "INDEPENDENT_AUDIO_VERIFICATION_UNAVAILABLE",
                "",
                "",
                "only one ASR transcript; no secondary ASR — auto-accept disabled",
                "OWNER_REVIEW",
            )
        )
    elif _nfc(draft) != _nfc(alt_flat or ""):
        anomalies.append(
            ReviewAnomaly(
                None,
                None,
                "DUAL_ASR_TEXT_MISMATCH",
                draft[:80],
                (alt_flat or "")[:80],
                "primary and secondary ASR flattened text differ",
                "OWNER_REVIEW",
            )
        )

    voice_p = voice_audio_path
    if voice_p is None:
        voice_p = resolve_voice_audio_path(brief, workspace_root)
    voice_sha = sha256_file(voice_p) if voice_p and voice_p.is_file() else None

    provenance_assessment: dict[str, Any] | None = None
    if secondary is not None:
        provenance_assessment = assess_dual_asr_independence(
            primary_path=primary_p,
            secondary_path=secondary_p,
            expected_voice_audio_sha256=voice_sha,
        )
        for err in provenance_assessment.get("errors") or []:
            anomalies.append(
                ReviewAnomaly(
                    None,
                    None,
                    err,
                    "",
                    "",
                    "dual ASR provenance check failed",
                    "OWNER_REVIEW",
                )
            )

    draft_sha = sha256_text(draft)
    fingerprints = {
        "production_id": production_id_from_brief(brief),
        "asr_primary_sha256": sha256_file(primary_p),
        "asr_secondary_sha256": sha256_file(secondary_p) if secondary else None,
        "asr_draft_text_sha256": draft_sha,
        "confirmed_reviewed_text_sha256": None,
        "reviewed_text_sha256": draft_sha,
        "voice_audio_sha256": voice_sha,
    }

    has_block = any(a.suggested_action == "BLOCK" for a in anomalies)

    # Independent dual-ASR text agreement does NOT auto-approve without trusted runtime + provenance.
    status = ReviewStatus.NEEDS_OWNER_REVIEW
    if has_block:
        status = ReviewStatus.BLOCKED
    elif secondary is None:
        status = ReviewStatus.NEEDS_OWNER_REVIEW

    doc = _result_doc(status, anomalies, fingerprints, brief, draft, primary_p, secondary_p)
    doc["auto_review_runtime_available"] = AUTO_REVIEW_RUNTIME_AVAILABLE
    doc["independent_audio_verification"] = (
        "VERIFIED_PROVENANCE_ONLY"
        if provenance_assessment and provenance_assessment.get("independent_asr_evidence")
        else "UNAVAILABLE_IN_REPO"
    )
    doc["asr_provenance_assessment"] = provenance_assessment
    doc["note"] = (
        "AUTO_ACCEPTED disabled in repo runtime; OWNER intent required. "
        "Dual-ASR text match is not accuracy proof."
    )
    # AUTO_ACCEPTED reserved for future trusted runtime hook — never emitted here.
    return doc


def _result_doc(
    status: ReviewStatus,
    anomalies: list[ReviewAnomaly],
    fingerprints: dict[str, Any],
    brief: dict[str, Any],
    draft: str | None,
    primary_p: Path | None,
    secondary_p: Path | None,
) -> dict[str, Any]:
    unresolved = sum(1 for a in anomalies if a.suggested_action != "ACCEPT")
    return {
        "schema_version": SCHEMA_VERSION,
        "status": status.value,
        "review_method": "DETERMINISTIC_ASR_COMPARE_V1",
        "independent_audio_verification": "UNAVAILABLE_IN_REPO",
        "auto_review_runtime_available": AUTO_REVIEW_RUNTIME_AVAILABLE,
        "note": "See asr_provenance_assessment; OWNER intent required for canonical",
        "anomaly_count": len(anomalies),
        "unresolved_mandatory_count": unresolved,
        "anomalies": [a.to_dict() for a in anomalies],
        "fingerprints": fingerprints,
        "evidence_paths": {
            "asr_primary": str(primary_p) if primary_p else None,
            "asr_secondary": str(secondary_p) if secondary_p else None,
        },
        "draft_reviewed_text_preview": (draft or "")[:120],
    }


def write_review_artifacts(
    workspace_root: Path,
    result: dict[str, Any],
    *,
    draft_text: str,
    force_regenerate: bool = False,
) -> dict[str, Any]:
    prod = workspace_root / "video-workflow" / "production"
    prod.mkdir(parents=True, exist_ok=True)
    meta: dict[str, Any] = {"reviewed_text_written": False, "reviewed_text_preserved": False}

    if force_regenerate:
        invalidate_owner_subtitle_approval(workspace_root, reason="FORCE_REGENERATE_REVIEW")

    asr_draft_subtitle_text_path(workspace_root).write_text(draft_text + "\n", encoding="utf-8")

    appr = load_approval(workspace_root)
    reviewed_p = reviewed_text_path(workspace_root)
    draft_sha = sha256_text(draft_text)
    existing_sha: str | None = None
    if reviewed_p.is_file():
        existing_sha = sha256_text(reviewed_p.read_text(encoding="utf-8-sig").strip())

    preserve = False
    if appr and appr.get("status") == ReviewStatus.OWNER_ACCEPTED.value and not force_regenerate:
        preserve = True
    elif existing_sha and existing_sha != draft_sha and not force_regenerate:
        preserve = True

    if preserve:
        meta["reviewed_text_preserved"] = True
        if appr and appr.get("status") == ReviewStatus.OWNER_ACCEPTED.value:
            meta["preserve_reason"] = "OWNER_APPROVAL_EXISTS"
        else:
            meta["preserve_reason"] = "REVIEWED_TEXT_EDITED"
    else:
        reviewed_p.write_text(draft_text + "\n", encoding="utf-8")
        meta["reviewed_text_written"] = True

    result = dict(result)
    result["review_artifact_write"] = meta
    review_result_path(workspace_root).write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return meta


def load_approval(workspace_root: Path) -> dict[str, Any] | None:
    p = approval_path(workspace_root)
    if not p.is_file():
        return None
    return json.loads(p.read_text(encoding="utf-8-sig"))


def approval_allows_canonical(workspace_root: Path, brief_path: Path) -> tuple[bool, str]:
    brief = load_brief_dict(brief_path)
    features = brief.get("features") or {}
    if features.get("subtitles") is False:
        return True, "NOT_APPLICABLE"
    content = brief.get("content") or {}
    auth = (content.get("authority") or {}).get("type", "").strip().lower()
    if auth == "script" or bool((brief.get("assets") or {}).get("script", {}).get("frozen")):
        return True, "SCRIPT_ROUTE"

    result_p = review_result_path(workspace_root)
    if not result_p.is_file():
        return False, "VOICE_REVIEW_RESULT_MISSING"

    result = json.loads(result_p.read_text(encoding="utf-8-sig"))
    status = result.get("status")
    if status != ReviewStatus.OWNER_ACCEPTED.value:
        return False, f"VOICE_REVIEW_STATUS_{status}"

    text_p = reviewed_text_path(workspace_root)
    if not text_p.is_file():
        return False, "REVIEWED_TEXT_MISSING"

    fp = result.get("fingerprints") or {}
    prod_id = production_id_from_brief(brief)
    if fp.get("production_id") and prod_id and fp.get("production_id") != prod_id:
        return False, "PRODUCTION_ID_MISMATCH"

    text_hash = sha256_text(text_p.read_text(encoding="utf-8-sig").strip())
    confirmed_fp = confirmed_text_sha256_from_fingerprints(fp)
    if not confirmed_fp:
        return False, "CONFIRMED_TEXT_FINGERPRINT_MISSING"
    if text_hash != confirmed_fp:
        return False, "CONFIRMED_TEXT_HASH_DRIFT"

    asr_draft_fp = str(fp.get("asr_draft_text_sha256") or "").strip()
    if not asr_draft_fp:
        return False, "ASR_DRAFT_FINGERPRINT_MISSING"
    draft_p = asr_draft_subtitle_text_path(workspace_root)
    if draft_p.is_file() and sha256_text(draft_p.read_text(encoding="utf-8-sig").strip()) != asr_draft_fp:
        return False, "ASR_DRAFT_TEXT_DRIFT"

    primary_p = asr_primary_path(workspace_root)
    pri_fp = str(fp.get("asr_primary_sha256") or "").strip()
    if not pri_fp:
        return False, "ASR_PRIMARY_FINGERPRINT_MISSING"
    if not primary_p.is_file():
        return False, "ASR_PRIMARY_MISSING"
    if sha256_file(primary_p) != pri_fp:
        return False, "ASR_PRIMARY_HASH_DRIFT"

    secondary_p = asr_secondary_path(workspace_root)
    sec_fp = fp.get("asr_secondary_sha256")
    if sec_fp:
        if not secondary_p.is_file():
            return False, "ASR_SECONDARY_MISSING"
        if sha256_file(secondary_p) != sec_fp:
            return False, "ASR_SECONDARY_HASH_DRIFT"

    voice_p = resolve_voice_audio_path(brief, workspace_root)
    voice_fp = str(fp.get("voice_audio_sha256") or "").strip()
    if not voice_fp:
        return False, "VOICE_AUDIO_FINGERPRINT_MISSING"
    if not voice_p or not voice_p.is_file():
        return False, "VOICE_AUDIO_MISSING"
    if sha256_file(voice_p) != voice_fp:
        return False, "VOICE_AUDIO_HASH_DRIFT"

    intent_p = owner_approval_intent_path(workspace_root)
    if not intent_p.is_file():
        return False, "OWNER_APPROVAL_INTENT_MISSING"
    intent = json.loads(intent_p.read_text(encoding="utf-8-sig"))

    appr = load_approval(workspace_root)
    if not appr:
        return False, "VOICE_APPROVAL_MISSING"
    if appr.get("status") != status:
        return False, "APPROVAL_STATUS_MISMATCH"

    confirmed_appr = str(
        appr.get("confirmed_reviewed_text_sha256") or appr.get("reviewed_text_sha256") or ""
    ).strip()
    if not confirmed_appr or confirmed_appr != confirmed_fp:
        return False, "APPROVAL_TEXT_HASH_DRIFT"

    intent_errors = validate_owner_approval_intent(
        intent, production_id=prod_id, reviewed_text_sha256=confirmed_fp
    )
    if intent_errors:
        return False, intent_errors[0]
    if appr.get("production_id") != prod_id:
        return False, "APPROVAL_PRODUCTION_ID_MISMATCH"
    if not appr.get("owner_confirmed"):
        return False, "OWNER_NOT_CONFIRMED"
    if appr.get("intent_sha256") != sha256_file(intent_p):
        return False, "APPROVAL_INTENT_DRIFT"

    return True, "OK"


def write_owner_approval(
    workspace_root: Path,
    *,
    intent_path: Path,
    accepted_text: str,
    result: dict[str, Any],
    brief: dict[str, Any],
) -> None:
    intent_path = intent_path.resolve()
    if not intent_path.is_file():
        raise ValueError("OWNER_APPROVAL_INTENT_MISSING")
    intent = json.loads(intent_path.read_text(encoding="utf-8-sig"))
    fp = result.get("fingerprints") or {}
    text_hash = sha256_text(accepted_text.strip())
    prod_id = production_id_from_brief(brief)
    intent_errors = validate_owner_approval_intent(
        intent, production_id=prod_id, reviewed_text_sha256=text_hash
    )
    if intent_errors:
        raise ValueError(intent_errors[0])
    owner_name = str(intent.get("owner_display_name") or "").strip()
    draft_p = asr_draft_subtitle_text_path(workspace_root)
    if draft_p.is_file():
        asr_draft_sha = sha256_text(draft_p.read_text(encoding="utf-8-sig").strip())
    else:
        asr_draft_sha = str(fp.get("asr_draft_text_sha256") or "").strip()
    if not asr_draft_sha:
        raise ValueError("ASR_DRAFT_TEXT_MISSING")
    doc = {
        "schema_version": SCHEMA_VERSION,
        "status": ReviewStatus.OWNER_ACCEPTED.value,
        "approval_method": "OWNER_INTENT_ARTIFACT",
        "owner_confirmed": True,
        "owner_actor": owner_name,
        "production_id": prod_id,
        "asr_draft_text_sha256": asr_draft_sha,
        "confirmed_reviewed_text_sha256": text_hash,
        "reviewed_text_sha256": text_hash,
        "asr_primary_sha256": fp.get("asr_primary_sha256"),
        "asr_secondary_sha256": fp.get("asr_secondary_sha256"),
        "voice_audio_sha256": fp.get("voice_audio_sha256"),
        "intent_sha256": sha256_file(intent_path),
        "intent_confirmation_phrase": OWNER_CONFIRMATION_PHRASE,
        "final_delivery_gate": "NOT_RUN",
        "identity_authentication": "NOT_PROVIDED_CURSOR_WORKFLOW_BOUNDARY",
    }
    approval_path(workspace_root).write_text(
        json.dumps(doc, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    reviewed_text_path(workspace_root).write_text(accepted_text.strip() + "\n", encoding="utf-8")
    new_fp = dict(fp)
    new_fp["asr_draft_text_sha256"] = asr_draft_sha
    new_fp["confirmed_reviewed_text_sha256"] = text_hash
    new_fp["reviewed_text_sha256"] = text_hash
    result = dict(result)
    result["status"] = ReviewStatus.OWNER_ACCEPTED.value
    result["fingerprints"] = new_fp
    review_result_path(workspace_root).write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def write_blocked_review_result(workspace_root: Path, result: dict[str, Any]) -> None:
    prod = workspace_root / "video-workflow" / "production"
    prod.mkdir(parents=True, exist_ok=True)
    review_result_path(workspace_root).write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

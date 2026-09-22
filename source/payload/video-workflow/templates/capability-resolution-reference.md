# Capability Resolution Reference

## Purpose

Records L3 **Capability Resolution** output after Edit Blueprint and before Plan Execution.

This is **not** a Runtime action plan. No MCP method names.

## L1 Canonical Capability States

Only these states exist in `logical-capability-vocabulary.yaml`:

| State | Meaning |
|-------|---------|
| `VERIFIED` | Production may `SELECT` |
| `AVAILABLE_UNVERIFIED` | Not production-VERIFIED — `CAPABILITY_VALIDATION_REQUIRED` |
| `UNKNOWN` | Unavailable |
| `FAILED` | Unavailable |
| `UNSAFE` | Prohibited — never select |
| `DEFERRED` | Unavailable for current Production |

## Resolution State Matrix

| L1 Status | Production Resolution |
|-----------|----------------------|
| `VERIFIED` | May `SELECTED` |
| `AVAILABLE_UNVERIFIED` | **Must not** direct `SELECTED` — `CAPABILITY_VALIDATION_REQUIRED` or Style `FALLBACK` with degradation |
| `UNKNOWN` | Unavailable — `FALLBACK` / `OMITTED` / `BLOCKED` per criticality |
| `FAILED` | Unavailable |
| `UNSAFE` | Prohibited — never select |
| `DEFERRED` | Unavailable |

### Combined with L2 Criticality

| Criticality | Non-VERIFIED behavior |
|-------------|----------------------|
| `REQUIRED` | `BLOCKED` or explicit review — no silent substitute |
| `PREFERRED` | Style-defined `fallback` with **semantic degradation metadata**; no fallback → unresolved / omit per policy |
| `OPTIONAL` | `OMITTED` |

**AVAILABLE_UNVERIFIED must never be treated as VERIFIED.**

## Fallback Semantics (required)

Each fallback entry in `capability-policy.yaml` must document:

- `target` — logical capability ID
- `effect_preservation` — full | high | partial | low | none
- `degradation_level` — low | medium | high
- `style_impact` — what the audience/perceptual intent loses or changes
- `reason` — why this fallback is allowed

Resolution **must record degradation** — no silent fallback.

## Resolution Status Values

| Status | Meaning |
|--------|---------|
| `SELECTED` | VERIFIED capability chosen |
| `FALLBACK` | Non-VERIFIED request resolved via Style fallback |
| `OMITTED` | Optional capability skipped |
| `BLOCKED` | Required capability unavailable |

## Coverage Fields

Capability Coverage is inventory only — **not an aesthetic score**.

Derived mechanically from `capability-policy.yaml` + vocabulary (`verify-capability-coverage.ps1`).

Unit: **logical_capability_id** (not decision count).

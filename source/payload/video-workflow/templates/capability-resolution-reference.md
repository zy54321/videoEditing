# Capability Resolution Reference

## Purpose

Records L3 **Capability Resolution** output after Edit Blueprint and before Plan Execution.

This is **not** a Runtime action plan. No MCP method names.

## Flow

```
Edit Blueprint (capability_requirements per beat / global)
  → L1 vocabulary lookup (status)
  → L2 capability-policy.yaml (criticality, fallback, forbidden)
  → resolution entries + coverage summary
  → Plan Execution
```

## Resolution Status Values

| Status | Meaning |
|--------|---------|
| `SELECTED` | Requested capability available and chosen |
| `FALLBACK` | Preferred unavailable; Style-defined fallback used |
| `OMITTED` | Optional capability skipped |
| `BLOCKED` | Required capability unavailable — fail closed / review |

## Rules

1. **REQUIRED** unavailable → `BLOCKED` (or Owner review if policy allows)
2. **PREFERRED** unavailable → Style `fallback` from capability-policy
3. **OPTIONAL** unavailable → `OMITTED`
4. **UNKNOWN** must not be treated as VERIFIED
5. Must not modify Owner Author Intent or Style identity silently

## Coverage Fields

Capability Coverage is inventory only — **not an aesthetic score**.

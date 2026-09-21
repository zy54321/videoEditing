# User Entry & Production Intake (V0.1)

**Stage:** 05A-R1 — Governed Production Entry & Intake  
**Status:** IMPLEMENTED

---

## Purpose

Define how an Owner starts video production in a Cursor workspace with minimal prompting, stable paths, and a single bound Production per workspace.

---

## Authority Model

| Layer | Role | Artifact |
|-------|------|----------|
| **Rules (normative)** | What the product **must** and **must not** do | `production-entry-intake.mdc` |
| **L3 Skill (execution)** | How to perform checks and workflow stages **under** the Rule | `video-production/SKILL.md` |
| **L4 Brief (data)** | Owner intent and production requirements | `video-workflow/production/brief.yaml` |

```
production-entry-intake.mdc  =  governance contract (cannot be bypassed)
video-production/SKILL.md      =  execution implementation (subordinate)
```

The Skill is **not** equivalent to a prompt. Rules define product behavior that Agents cannot skip.

Supporting routing in `video-workflow-core.mdc` §11 points `【制作视频】` to the intake Rule without duplicating its full text.

---

## Standard Entry

Owner says:

```
【制作视频】
```

Agent must:

1. Read `production-entry-intake.mdc`
2. Read `video-production/SKILL.md`
3. Resolve **FIRST_RUN** or **CONTINUE_EXISTING**
4. Never require `/video-production`, Skill names, Brief paths, or YAML editing for normal use

---

## Single-Production Instance

| Concept | Rule |
|---------|------|
| Release package | Reusable to initialize many workspaces |
| Initialized workspace | Binds **one** Production |
| Bound marker | `video-workflow/production/brief.yaml` (valid) |

Another video in the same workspace → `SINGLE_PRODUCTION_INSTANCE_BOUND` → use a new workspace.

---

## Preparation Pipeline (FIRST_RUN)

Strict order:

```
ENTRY → TYPE_SELECTION → PATH_COLLECTION → PATH_VALIDATION
→ ASSET_AUDIT → REQUIREMENT_CLASSIFICATION → NECESSARY_OWNER_CONFIRMATION
→ BRIEF_BUILD → PREPARATION_GATE
```

| Gate state | Behavior |
|------------|----------|
| `COLLECTING` | Intake in progress |
| `READY` | Save Brief → auto-enter L3 Preflight (no “是否继续？”) |
| `BLOCKED` | Stop; explain what is missing |

Brief creation happens **only** after READY prerequisites — never during Installer, never as a half-empty stub.

---

## Path & Date Policy

- `media.input` / `media.output` are Owner-provided; written as **absolute paths** at Brief creation
- Paths remain stable across days; workflow does **not** create or switch date-based media folders
- Changing paths requires re-validation and re-gating

---

## Repeat Entry

When Brief exists and Owner says `【制作视频】`:

- Load Brief
- Verify bound paths
- Continue appropriate stage (edit, repair, render, closeout)
- Do **not** re-run type selection or path collection

---

## Workspace Layout

```
<workspace>/
├─ .cursor/
│  ├─ rules/
│  │  ├─ video-workflow-core.mdc
│  │  ├─ davinci-production.mdc
│  │  └─ production-entry-intake.mdc
│  └─ skills/
│     ├─ video-production/SKILL.md
│     └─ video-editing/<skill>/SKILL.md
└─ video-workflow/
   ├─ capabilities/
   ├─ templates/
   └─ production/
      └─ brief.yaml          ← created after governed Intake only
```

---

## What This Stage Does Not Include

- Installer / Release packaging
- N02 production execution
- Runtime / MCP / Resolve changes
- `workspace-config` or multi-production registry

---

## Related Documents

- L4 template: `source/payload/video-workflow/templates/production-brief.yaml`
- L4 reference: `source/payload/video-workflow/templates/production-brief-reference.md`
- Scope: `docs/03-v0.1-scope.md`

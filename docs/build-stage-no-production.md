# Build Stage — No Production Policy

**Policy ID:** `BUILD_STAGE_NO_PRODUCTION`  
**Effective:** v0.1.1-dev, Stage 08C+

---

## Principle

When the project is in a **Construction Stage**, video production actions are **forbidden**.

Construction stages include:

- architecture
- documentation
- skill construction
- knowledge construction
- tooling construction
- static test
- refactor
- release preparation

---

## Forbidden During Construction

- Create or run real video **Production**
- Edit real video media
- Create or modify real **Resolve Project** / **Timeline**
- **Render** deliverable video
- Modify real `media.input` / `media.output`
- Execute N02 or any other bound Production
- Start video editing “to verify quickly”
- Disposable Resolve capability spike
- MCP **write** actions against production runtime
- FFmpeg video transform / transcode for validation

---

## Allowed During Construction

- File create / modify (Markdown, YAML, JSON, PowerShell)
- Static lint / consistency tests
- Schema / fixture text tests
- Unit tests that do **not** touch real media

---

## Capability Validation Deferral

If a new design requires Runtime proof:

Record only:

```
CAPABILITY_VALIDATION_REQUIRED
```

Do **not** execute validation during Construction.

---

## Lifecycle Separation

| Stage | Purpose |
|-------|---------|
| **Construction** | Product architecture, skills, knowledge, tests |
| **Production / Acceptance** | Real media, Resolve, render, Owner review |

These stages **must not** be mixed in one task without explicit Owner authorization.

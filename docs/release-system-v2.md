# Release System V2 — One-click Local Release

## Entry

- Double-click `release.bat` (or run `source/build/release.ps1`)

## Authority

| Concern | Authority |
|---------|-----------|
| Product files | `source/payload/` (+ `.productignore`) |
| Installer file list | `source/installer/product-files.generated.ps1` (auto-sync) |
| Current version | `source/VERSION` |
| Release tag | annotated `vX.Y.Z` on single `release: vX.Y.Z` commit |

## Flow

1. Version menu (Patch / Minor / Major / Custom)
2. Transaction snapshot (stash safety net)
3. Formalize `source/VERSION`
4. Sync product inventory
5. `release-gate.ps1 -Phase PreBuild`
6. `build-release.ps1 -AllowWorkingTree`
7. `release-gate.ps1 -Phase PostBuild` (+ ZIP-only install)
8. One confirmation → `git commit` + `git tag -a`
9. `REMOTE_PUSH = NOT_PERFORMED`

## Tests

- `source/tests/release-v2.ps1`
- `source/tests/release-gate.ps1`

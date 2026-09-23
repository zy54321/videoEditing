#Requires -Version 5.1
<#
.SYNOPSIS
  Documented manual/MCP preflight before A1 timeline_frame captures.

  After Resolve restart, disposable project may still inherit Deliver format
  png/RGB16 from prior sessions. timeline_frame requires RGB8-compatible pair.

  MCP (once per session, before captures):
    render set_format_and_codec format=png codec=RGB8

  Do NOT call fusion_comp.render during A1 — it poisons render settings.
#>
Write-Host 'A1 Resolve preflight checklist:'
Write-Host '  1. project_manager.load Astra-08E-B-Subtitle-Validation'
Write-Host '  2. render get_format_and_codec -> expect png / RGB8 (not RGB16)'
Write-Host '  3. If RGB16: render set_format_and_codec png RGB8'
Write-Host '  4. timeline set_current A1-EXP-A (or v2 with black still under Text+)'
Write-Host '  5. fusion_comp safe_set_inputs on Text+ clip'
Write-Host '  6. timeline_markers set_current_timecode inside Text+ range'
Write-Host '  7. timeline_frame capture quality=frame format=png (1080x1920)'
Write-Host '  8. Verify saved PNG has bright pixels before A01-A10'

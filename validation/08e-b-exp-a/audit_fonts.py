#!/usr/bin/env python3
"""Stage 08E-B BR1 — Windows / System.Drawing font authority audit."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

OUT = Path(__file__).resolve().parent / "evidence" / "b1-font-audit.json"
OUT.parent.mkdir(parents=True, exist_ok=True)

FONTS_DIR = Path(r"C:\Windows\Fonts")
PATTERNS = ["*yahei*", "*msyh*", "*simsun*", "*simhei*", "*mingliu*", "*arial*", "*segoe*"]

CANDIDATES = [
    "Microsoft YaHei",
    "Microsoft YaHei UI",
    "SimSun",
    "NSimSun",
    "SimHei",
    "Malgun Gothic",
    "Arial",
    "Segoe UI",
    "Tahoma",
    "Times New Roman",
]


def list_font_files() -> list[dict]:
    hits: list[dict] = []
    for pat in PATTERNS:
        for p in sorted(FONTS_DIR.glob(pat)):
            hits.append({"pattern": pat, "file": p.name, "path": str(p)})
    return hits


def registry_fonts() -> list[dict]:
    ps = r"""
    $rp = 'HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts'
    $props = Get-ItemProperty $rp
    $rows = @()
    $props.PSObject.Properties | Where-Object { $_.Name -notmatch '^PS' } | ForEach-Object {
      $rows += [pscustomobject]@{ display_name = $_.Name; file = $props.($_.Name) }
    }
    $rows | ConvertTo-Json -Depth 4
    """
    raw = subprocess.check_output(
        ["powershell", "-NoProfile", "-Command", ps], text=True, encoding="utf-8", errors="replace"
    )
    data = json.loads(raw) if raw.strip() else []
    if isinstance(data, dict):
        data = [data]
    keywords = ("YaHei", "SimSun", "SimHei", "MingLi", "Arial", "Segoe")
    return [r for r in data if any(k in r.get("display_name", "") for k in keywords)]


def system_drawing_probe() -> dict:
    ps = r"""
    Add-Type -AssemblyName System.Drawing
    $all = [System.Drawing.FontFamily]::Families | ForEach-Object { $_.Name }
    $candidates = @(
      'Microsoft YaHei','Microsoft YaHei UI','SimSun','NSimSun','SimHei',
      'Malgun Gothic','Arial','Segoe UI','Tahoma','Times New Roman'
    )
    $rows = @()
    foreach ($c in $candidates) {
      $enum = $all -contains $c
      $inst = 'SKIP'
      if ($enum) {
        try {
          $ff = New-Object System.Drawing.FontFamily($c)
          if ($ff.IsStyleAvailable([System.Drawing.FontStyle]::Regular)) {
            $font = New-Object System.Drawing.Font($ff, 48, [System.Drawing.FontStyle]::Regular, [System.Drawing.GraphicsUnit]::Pixel)
            $font.Dispose(); $inst = 'OK'
          } else { $inst = 'NO_REGULAR' }
          $ff.Dispose()
        } catch { $inst = 'FAIL:' + $_.Exception.Message }
      }
      $rows += [pscustomobject]@{ family = $c; enumerated = $enum; instantiate_regular = $inst }
    }
    [pscustomobject]@{ total_families = $all.Count; candidates = $rows } | ConvertTo-Json -Depth 6
    """
    raw = subprocess.check_output(
        ["powershell", "-NoProfile", "-Command", ps], text=True, encoding="utf-8", errors="replace"
    )
    return json.loads(raw)


def main() -> int:
    report = {
        "fonts_dir": str(FONTS_DIR),
        "font_files": list_font_files(),
        "registry_entries": registry_fonts(),
        "system_drawing": system_drawing_probe(),
        "candidates": CANDIDATES,
    }
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(OUT)
    for row in report["system_drawing"]["candidates"]:
        print(
            f"{row['family']}: enumerated={row['enumerated']} instantiate={row['instantiate_regular']}"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())

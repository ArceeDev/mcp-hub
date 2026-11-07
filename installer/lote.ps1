# Flint · Procesa en lote o vigila una carpeta de extractos Norma 43 (.n43/.c43) y Facturae (.xml).
#   $env:KEYFLINT_LICENSE='LIC-tu-licencia'; irm __SITE__/lote.ps1 | iex
$ErrorActionPreference = 'Stop'
$tmp = Join-Path $env:TEMP 'flint-lote.py'
Invoke-WebRequest -UseBasicParsing -Uri '__SITE__/lote.py' -OutFile $tmp
try { python $tmp @args } finally { Remove-Item $tmp -ErrorAction SilentlyContinue }

# Flint · Procesa en lote o vigila una carpeta de extractos Norma 43 (.n43/.c43) y Facturae/VeriFactu (.xml/.xsig).
#   $env:KEYFLINT_LICENSE='LIC-tu-licencia'; irm __SITE__/lote.ps1 | iex
$ErrorActionPreference = 'Stop'
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
  Write-Host 'Instalando motor ligero uv (una sola vez)...'
  powershell -NoProfile -ExecutionPolicy ByPass -Command "irm https://astral.sh/uv/install.ps1 | iex"
  $env:Path = "$env:USERPROFILE\.local\bin;$env:Path"
}
$tmp = Join-Path $env:TEMP 'flint-lote.py'
Invoke-WebRequest -UseBasicParsing -Uri '__SITE__/lote.py' -OutFile $tmp
try { uv run --no-project --python 3.12 --quiet $tmp @args } finally { Remove-Item $tmp -ErrorAction SilentlyContinue }

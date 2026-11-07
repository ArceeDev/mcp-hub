# Flint · instala los servidores MCP en Claude Desktop, Cursor, VS Code, Windsurf y Claude Code.
#   $env:KEYFLINT_LICENSE='LIC-tu-licencia'; irm __SITE__/instalar.ps1 | iex
$ErrorActionPreference = 'Stop'
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
  Write-Host 'Instalando uv (una sola vez)...'
  powershell -NoProfile -ExecutionPolicy ByPass -Command "irm https://astral.sh/uv/install.ps1 | iex"
  $env:Path = "$env:USERPROFILE\.local\bin;$env:Path"
}
$tmp = Join-Path $env:TEMP 'flint-instalar.py'
Invoke-WebRequest -UseBasicParsing -Uri '__SITE__/instalar.py' -OutFile $tmp
try { uv run --no-project --python 3.12 --quiet $tmp @args } finally { Remove-Item $tmp -ErrorAction SilentlyContinue }

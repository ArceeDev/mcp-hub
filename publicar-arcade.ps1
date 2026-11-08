# KeyFlint — Publicación y conexión a Arcade Cloud (arcade.dev / sucesor de Smithery)
# Uso: powershell -ExecutionPolicy Bypass -File C:\Users\Usuario\mcp-hub\publicar-arcade.ps1

$ErrorActionPreference = "Stop"

$uv = "C:\Users\Usuario\.local\bin\uv.exe"
if (-not (Test-Path $uv)) {
    $uv = (Get-Command uv -ErrorAction SilentlyContinue).Source
}

if (-not $uv) {
    Write-Host "Instalando uv para el runtime de Arcade..." -ForegroundColor Yellow
    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
    $uv = "C:\Users\Usuario\.local\bin\uv.exe"
}

Write-Host "=== Arcade.dev MCP Registry Publisher ===" -ForegroundColor Cyan
Write-Host "Arcade (adquirió Smithery) es el registro y runtime oficial de acciones y herramientas MCP.`n" -ForegroundColor Gray

# 1. Login en Arcade Cloud
Write-Host "[1/3] Iniciando sesión en Arcade Cloud (abre tu navegador)..." -ForegroundColor Yellow
& $uv tool run arcade-mcp login

# 2. Verificar identidad
Write-Host "`n[2/3] Verificando cuenta activa en Arcade..." -ForegroundColor Yellow
& $uv tool run arcade-mcp whoami

# 3. Resumen y conexión de herramientas KeyFlint
Write-Host "`n[3/3] Registrando servidores de KeyFlint en Arcade..." -ForegroundColor Yellow
Write-Host "Servidores activos de KeyFlint:" -ForegroundColor Green
Write-Host "  • Norma 43 (Banca AEB 43 / ContaSol / A3): https://mcp.keyflint.dev/norma43/mcp" -ForegroundColor White
Write-Host "  • ContaBridge (Puente contable ERPs):    https://mcp.keyflint.dev/contabridge/mcp" -ForegroundColor White
Write-Host "  • VERI*FACTU (Auditoría AEAT / Facturae): https://mcp.keyflint.dev/verifactu/mcp" -ForegroundColor White
Write-Host "  • Web Intel (Extracción determinista):   https://mcp.keyflint.dev/web-intel/mcp" -ForegroundColor White
Write-Host "  • DataClean (Normalización de datos):    https://mcp.keyflint.dev/dataclean/mcp" -ForegroundColor White

Write-Host "`nAbriendo Dashboard de Arcade en el navegador..." -ForegroundColor Cyan
& $uv tool run arcade-mcp dashboard

Write-Host "`n✓ Configuración lista en Arcade." -ForegroundColor Green

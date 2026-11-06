# scripts/lanzar-releases.ps1
# Lanza los releases oficiales v0.2.0 (y v0.1.0 para verifactu) en GitHub para disparar release.yml y publicar en PyPI.
$releases = @(
    @{ Repo = "ArceeDev/web-intel-mcp"; Tag = "v0.2.0"; Title = "v0.2.0: MCP Apps result cards + MCP Registry server.json" },
    @{ Repo = "ArceeDev/norma43-mcp"; Tag = "v0.2.0"; Title = "v0.2.0: MCP Apps result cards + MCP Registry server.json" },
    @{ Repo = "ArceeDev/contabridge-mcp"; Tag = "v0.2.0"; Title = "v0.2.0: QuickBooks/Xero formats + MCP Apps + MCP Registry server.json" },
    @{ Repo = "ArceeDev/dataclean-mcp"; Tag = "v0.2.0"; Title = "v0.2.0: Data cleaning + MCP Apps + MCP Registry server.json" },
    @{ Repo = "ArceeDev/verifactu-mcp"; Tag = "v0.1.0"; Title = "v0.1.0: Facturae 3.2.2 + Veri*Factu fingerprint + AEAT QR + MCP Registry" }
)

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " LANZANDO RELEASES DE LOS 5 MCPS DE KEYFLINT" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

foreach ($r in $releases) {
    Write-Host "`n--> Procesando $($r.Repo) ($($r.Tag))..." -ForegroundColor Yellow
    
    # Crear el release directamente en GitHub apuntando a main
    gh release create $r.Tag --repo $r.Repo --title $r.Title --generate-notes --target main
    if ($LASTEXITCODE -eq 0) {
        Write-Host "    [OK] Release $($r.Tag) creado con exito." -ForegroundColor Green
    } else {
        Write-Host "    [AVISO] Verificando estado en $($r.Repo)..." -ForegroundColor Magenta
    }
}

Write-Host "`n==========================================================" -ForegroundColor Cyan
Write-Host " RELEASES LANZADOS. MONITORIZA LOS WORKFLOWS EN GITHUB ACTIONS." -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

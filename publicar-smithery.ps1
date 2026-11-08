# Alta de los 5 MCPs en Smithery como servidores remotos (mcp.keyflint.dev, OAuth con licencia).
# Requisitos: Node 18+ (npx). Uso: powershell -ExecutionPolicy Bypass -File publicar-smithery.ps1
$ErrorActionPreference = "Stop"
$cli = "@smithery/cli@4.11.1"

npx -y $cli auth login          # abre el navegador: entra con GitHub (ArceeDev)
npx -y $cli auth whoami
$ns = Read-Host "Namespace de Smithery (Enter = arceedev)"
if (-not $ns) { $ns = "arceedev" }

$mcps = [ordered]@{
  "web-intel-mcp"   = "web-intel"
  "norma43-mcp"     = "norma43"
  "contabridge-mcp" = "contabridge"
  "verifactu-mcp"   = "verifactu"
  "dataclean-mcp"   = "dataclean"
}
foreach ($name in $mcps.Keys) {
  $url = "https://mcp.keyflint.dev/$($mcps[$name])/mcp"
  Write-Host "`n== $ns/$name  <-  $url" -ForegroundColor Cyan
  npx -y $cli mcp publish $url -n "$ns/$name"
  if ($LASTEXITCODE -ne 0) {
    # Smithery pausa la publicacion hasta autorizar OAuth: pega tu licencia LIC-... en la ventana que se abre.
    Read-Host "Autoriza en el navegador (pega tu licencia) y pulsa Enter para reanudar"
    npx -y $cli mcp publish --resume -n "$ns/$name"
  }
}
Write-Host "`nListo. Revisa https://smithery.ai/@$ns" -ForegroundColor Green

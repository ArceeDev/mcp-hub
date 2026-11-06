# scripts/publicar-registro-mcp.ps1
# Publica los 5 servidores MCP en el registro oficial de Model Context Protocol (registry.modelcontextprotocol.io)
$ErrorActionPreference = "Stop"
$tmp = Join-Path $env:TEMP "mcp-release"
$exe = Join-Path $tmp "mcp-publisher.exe"

if (-not (Test-Path $exe)) {
  $zip = Join-Path $tmp "mcp-publisher.tar.gz"
  New-Item -ItemType Directory -Force -Path $tmp | Out-Null
  Invoke-WebRequest "https://github.com/modelcontextprotocol/registry/releases/latest/download/mcp-publisher_windows_amd64.tar.gz" -OutFile $zip
  tar -xzf $zip -C $tmp mcp-publisher.exe
}

# Login con GitHub token existente
$token = (gh auth token).Trim()
& $exe login github -token $token

# Publicar cada servidor
foreach ($r in "web-intel-mcp","norma43-mcp","contabridge-mcp","dataclean-mcp","verifactu-mcp") {
  $repoDir = Join-Path $tmp $r
  if (-not (Test-Path $repoDir)) {
    git clone -q "https://github.com/ArceeDev/$r.git" $repoDir
  }
  Push-Location $repoDir
  git pull -q
  Write-Host "`n--> Publicando $r en el MCP Registry..." -ForegroundColor Yellow
  & $exe publish
  Pop-Location
}

Write-Host "`n[OK] Todos los servidores se han procesado en el MCP Registry." -ForegroundColor Green

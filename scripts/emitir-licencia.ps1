<#
.SYNOPSIS
  Emite una licencia de regalo (beta testers, prensa, soporte) en KeyFlint y la copia al portapapeles.

.EXAMPLE
  .\scripts\emitir-licencia.ps1 -Email ana@gestoria.es
  .\scripts\emitir-licencia.ps1 -Email ana@gestoria.es -Plan indie -Motivo "prensa"
  .\scripts\emitir-licencia.ps1 -Email ana@gestoria.es -Plan community -Dias 7

.NOTES
  Planes y créditos (los fija KeyFlint por plan): community 25, pro 1.000/mes, indie 10.000, agency 50.000.
  Por defecto: pro durante 30 días (1.000 créditos), suficiente para probar todo en serio.
  La clave de admin se lee de la variable de entorno KEYFLINT_ADMIN_KEY o se pide sin mostrarla. No se guarda en ningún sitio.
#>
param(
  [Parameter(Mandatory = $true)][string]$Email,
  [ValidateSet("community", "pro", "indie", "agency")][string]$Plan = "pro",
  [int]$Dias = 30,
  [string]$Motivo = "beta",
  [string]$Gateway = "https://licenses.keyflint.dev"
)
$ErrorActionPreference = "Stop"

if ($Email -notmatch '^[^@\s]+@[^@\s]+\.[^@\s]+$') { throw "Email no válido: $Email" }

$key = $env:KEYFLINT_ADMIN_KEY
if (-not $key) {
  $sec = Read-Host "Clave de admin de KeyFlint (no se muestra)" -AsSecureString
  $key = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($sec))
}
if (-not $key) { throw "Falta la clave de admin." }

$body = @{
  customer_email = $Email
  tier           = $Plan
  metadata       = @{ gift = $true; reason = $Motivo; source = "emitir-licencia.ps1" }
}
if ($Dias -gt 0) { $body.expires_in_days = $Dias }

try {
  $r = Invoke-RestMethod -Method Post -Uri "$Gateway/api/v1/licenses/issue" `
    -Headers @{ "X-Admin-Key" = $key } -ContentType "application/json" `
    -Body ($body | ConvertTo-Json -Depth 4)
} catch {
  $code = $_.Exception.Response.StatusCode.value__
  if ($code -eq 401 -or $code -eq 403) { throw "KeyFlint rechaza la clave de admin ($code)." }
  throw "KeyFlint no ha emitido la licencia: $($_.Exception.Message)"
}

$lic = $r.data.license_key
if (-not $lic) { throw "Respuesta inesperada de KeyFlint: $($r | ConvertTo-Json -Depth 4)" }

try { Set-Clipboard -Value $lic; $clip = " (copiada al portapapeles)" } catch { $clip = "" }
$credits = @{ community = "25"; pro = "1.000 al mes"; indie = "10.000"; agency = "50.000" }[$Plan]
$vence = if ($Dias -gt 0) { "$Dias días" } else { "sin caducidad" }

Write-Host ""
Write-Host "Licencia $Plan para $Email · $credits créditos · $vence$clip" -ForegroundColor Green
Write-Host $lic
Write-Host ""
Write-Host "Mensaje para enviarle:" -ForegroundColor Cyan
Write-Host @"
¡Hola! Aquí tienes tu licencia de Flint ($credits créditos, $vence):

$lic

Cómo usarla en 1 minuto: https://mcp.keyflint.dev/empezar/
Tu saldo, cuando quieras: https://mcp.keyflint.dev/saldo/
Cualquier fallo o idea, responde a este mensaje. ¡Gracias por probarlo!
"@

# Proceso seguido

## 1. Base
- KeyFlint (`licenses.keyflint.dev`, Fly) es solo el servicio de licencias y créditos. Cada MCP vive en su repo; nada va al repo `keyflint`.
- Cobro: licencia Ed25519 firmada + créditos consumidos por llamada vía `keyflint-verify` (PyPI). Reembolso automático si la llamada falla.
- Licencia BSL 1.1, Change Date 2030-11-05, contacto `legal@keyflint.dev`.

## 2. Elección de nichos
- Descartados por saturados: BORME, sanciones, TARIC, modelos AEAT dentro de SaaS, Verifactu, e-factura, SEPA/camt/MT940, CSRD, DORA, etc.
- Hueco elegido: herramientas **deterministas y sin estado** (coste marginal ~0), útiles para gestorías multi-cliente y, en global, para cualquiera con datos sucios.

## 3. MCPs construidos (Python, `mcp>=2`)
| MCP | Qué hace | Créditos/llamada |
|---|---|---|
| web-intel | Leer URL a Markdown, metadatos, enlaces, stack, auditoría SEO | 1-3 |
| norma43 | Parsear extractos N43, a CSV, conciliar con facturas, validar IBAN/NIF | 0-3 |
| contabridge | Convertir diario A3 / ContaPlus / QuickBooks / Xero / CSV; N43 a asientos | 0-3 |
| dataclean | Perfilar, limpiar, validar esquema y normalizar tablas CSV/Excel | 1 |
| verifactu | Nicho saturado; repo existe, fuera del catálogo | - |

Cada uno: tests con gateway falso + licencias firmadas en local, sin depender de KeyFlint.

## 4. Endurecimiento
Pasada de estrés: slowloris, DNS rebinding, ReDoS, OOM en conciliación, charset, CSV con CR. Cobro exacto con 100 llamadas concurrentes.

## 5. Distribución
- PyPI con Trusted Publishing (tag `vX.Y.Z` → tests → PyPI + `.mcpb` en GitHub Release).
- Bundles `.mcpb` (MCPB v0.4, `uv`), solo piden la licencia.
- Tarjetas en el chat (MCP Apps, `ui://<slug>/card.html`).

## 6. Hub `mcp.keyflint.dev`
- Generador estático (`data/catalog.json` → `build.py` → `public/`) en Cloudflare Workers (Vercel Hobby no permite uso comercial).
- Pestañas de instalación: Claude, ChatGPT, Cursor, VS Code, Codex, Antigravity.
- Stripe: Pro 29 $/mes por Payment Link y recarga libre (5-500 €) por Checkout dinámico del gateway; `/gracias/` muestra la licencia y `/saldo/?recarga=` el saldo nuevo. (Los packs Indie 149 $ y Agency 349 $ se retiraron el 2026-11-07.)
- `/api/saldo`, `/api/recuperar`, `/api/licencia`, `/api/uso` en el Worker.

## 7. Modo remoto (en producción desde 2026-11-05)
- Workers Paid + OAuth 2.1 (`workers-oauth-provider`, DCR/CIMD), licencia cifrada en props, `Bearer LIC-` también vale.
- `/<slug>/mcp` → Cloudflare Container `McpRuntime` (5 MCP en un uvicorn).
- KV `OAUTH_KV`, D1 `mcp-usage` (uso por herramienta, purga a 180 días), límite 120 llamadas/min por licencia, cron diario de salud.

## 8. Pendiente (lado Arcee)
1. Mergear PR #1 y #2 de web-intel, norma43 y contabridge.
2. Dar de alta el publisher pendiente en PyPI por repo y sacar `v0.1.0`; luego `pypi`/`mcpb: true` en el catálogo.
3. Mergear contabridge #3 (QuickBooks/Xero) y añadir `meta=UI` a `bank_statement_csv`.
4. Mergear keyflint #50 y desplegar en Fly (activa la licencia en `/gracias/`).
5. Prueba real de compra con licencia de producción (nunca se ha hecho fuera del entorno de test).

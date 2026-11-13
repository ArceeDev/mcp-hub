# Enlaces con UTM para el Día D (14-15 nov 2026)

El registro propio (`/api/v`) lee `utm_source`, `utm_medium`, `utm_campaign` y, como atajo, `ref`.
Usa siempre estos enlaces; sin UTM, la visita solo queda con el dominio de origen (si el navegador lo envía).

| Canal | Cuándo | Enlace |
|---|---|---|
| Product Hunt | sáb 14, 09:01 | https://mcp.keyflint.dev/en/?utm_source=producthunt&utm_medium=launch&utm_campaign=dia-d |
| X (post fijado) | sáb 14, 09:30 | https://mcp.keyflint.dev/?utm_source=x&utm_medium=social&utm_campaign=dia-d |
| Show HN | dom 15, 15:00 | https://mcp.keyflint.dev/en/?ref=hn (HN penaliza UTM largos) |
| Reddit | dom 15, 16:00 | https://mcp.keyflint.dev/visor-norma-43/?utm_source=reddit&utm_medium=social&utm_campaign=dia-d |
| LinkedIn | cualquier post | https://mcp.keyflint.dev/asesorias/?utm_source=linkedin&utm_medium=social&utm_campaign=dia-d |
| Grupos Facebook asesores | rescate | https://mcp.keyflint.dev/visor-norma-43/?utm_source=facebook&utm_medium=grupo&utm_campaign=rescate |
| Grupos Telegram asesores | rescate | https://mcp.keyflint.dev/visor-norma-43/?utm_source=telegram&utm_medium=grupo&utm_campaign=rescate |
| Demo asesoría (WhatsApp) | rescate | https://mcp.keyflint.dev/asesorias/?utm_source=whatsapp&utm_medium=directo&utm_campaign=demo |

## Consultar
```powershell
curl.exe -s -H "x-admin-key: $env:HUB_ADMIN_KEY" "https://mcp.keyflint.dev/api/admin/visitas?dias=7"
```
Devuelve totales (`vistas` = páginas vistas, `visitas` = primeras páginas), por día, país, origen, UTM y página.

## Qué no guarda (RGPD)
Ni cookies ni localStorage, ni IP (solo un hash diario en `hub_limits` como freno anti-inflado de 300/día),
ni user-agent, ni query string. Respeta Global Privacy Control y Do Not Track. Ignora bots por user-agent.
No hay visitantes únicos: es imposible sin identificadores, y es a propósito.

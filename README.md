# mcp-hub

Sitio estático de **https://mcp.keyflint.dev**: catálogo, instalación, precios y guía de todos los MCPs de KeyFlint.

- `data/catalog.json`: única fuente de datos (MCPs, planes y enlaces de pago de Stripe).
- `python3 build.py` genera `public/` (HTML, sitemap.xml, robots.txt, llms.txt, JSON-LD, `_headers`). Sin dependencias.
- La clave pública del gateway se lee en cada build de `https://licenses.keyflint.dev/api/v1/licenses/public-key` (o de la variable `KEYFLINT_PUBLIC_KEYS`). Si no hay clave válida, el build falla a propósito para no publicar instrucciones rotas.

## Publicar en PyPI y .mcpb

Cada MCP de `data/catalog.json` tiene dos interruptores:

- `"pypi": true` cuando el paquete está en PyPI: la configuración pasa a `uvx <paquete>` con solo `KEYFLINT_LICENSE`.
- `"mcpb": true` cuando el `.mcpb` está publicado en `<repo>/releases/latest`: Claude Desktop muestra el botón de descarga.

## Añadir un MCP

Añade una entrada a `mcps` en `data/catalog.json` y haz push. Cloudflare Pages vuelve a publicar.

## Despliegue (Cloudflare Workers, gratis y con uso comercial permitido)

1. Cloudflare › Workers & Pages › Create › Import a repository › `ArceeDev/mcp-hub`.
2. Build command: `python3 build.py`. Deploy command: `npx wrangler deploy` (lee `wrangler.jsonc`).
3. Settings › Domains & Routes › Add › Custom domain › `mcp.keyflint.dev`.

## API (`src/worker.js`)

`src/index.js` enruta `/api/*` a `src/worker.js`; el resto lo sirven los assets estáticos.

- `GET /api/saldo?license=…`: plan, estado y créditos (vía `/api/v1/billing/status` del gateway). No devuelve correo ni licencia.
- `POST /api/recuperar {email}`: pide al gateway un enlace de acceso de un solo uso. Responde igual exista o no el correo.

Probar en local: `npx wrangler dev --var GATEWAY_URL:http://127.0.0.1:9009` con un gateway falso.

## MCP remotos con OAuth (`src/index.js`, `container/`)

Cada MCP vive también en `https://mcp.keyflint.dev/<slug>/mcp` (Streamable HTTP). Claude, ChatGPT, Cursor, VS Code,
Codex y Claude Code lo añaden por URL; la primera vez abren `/authorize`, el usuario pega su licencia y listo.

**Conector único para despachos:** `https://mcp.keyflint.dev/despacho/mcp` junta Norma 43 + ContaBridge (17 herramientas,
mismo OAuth con código de 6 dígitos, misma facturación por herramienta). Código: `container/despacho.py`; test:
`test/despacho_check.py`. No necesita rutas ni dominios nuevos en Cloudflare: lo cubre `"/*/mcp"` de `run_worker_first`.

- `src/index.js`: servidor de autorización OAuth 2.1 (`@cloudflare/workers-oauth-provider`: DCR, CIMD, PKCE, refresh) y
  un recurso protegido por MCP. La licencia queda cifrada en los props del token (KV `OAUTH_KV`). Cada token sirve solo
  para el MCP que se autorizó. Los clientes con cabeceras (Antigravity, Windsurf, `config.toml` de Codex) pueden mandar
  `Authorization: Bearer LIC-…` sin OAuth.
- `container/`: imagen con los 5 MCP (rama `main` de cada repo) en un solo uvicorn (`/<slug>/mcp`). El Worker la arranca
  como Cloudflare Container (`McpRuntime`, hasta 3 instancias) y le reenvía cada petición con `X-License-Key`, sin el token.

Con el plan de pago, además:

- **Uso por herramienta** (D1 `USAGE_DB`): cada llamada por URL guarda MCP, herramienta, resultado, créditos y duración
  con el hash de la licencia (nunca la licencia ni el contenido). `/api/uso?license=` lo devuelve y `/saldo/` lo muestra.
- **Límite por licencia** (`MCP_LIMIT`): 120 llamadas a herramientas por minuto; después responde `429` en JSON-RPC.
- **Cron diario** (04:17 UTC): borra el uso de más de 180 días y comprueba `/healthz` de los 5 MCP (aparece en los logs).

### Activarlo (una vez)

1. Plan **Workers Paid** (5 $/mes): los Containers no existen en el plan gratis.
2. `npx wrangler kv namespace create OAUTH_KV` y pega el `id` en `wrangler.jsonc`.
3. `npm ci && npx wrangler deploy` desde una máquina con **Docker** (construye y sube la imagen). Si Workers Builds no
   construye contenedores en tu cuenta, haz este primer despliegue a mano.
4. `npx wrangler d1 create mcp-usage`, pega el `database_id` en `wrangler.jsonc` y aplica el esquema:
   `npx wrangler d1 migrations apply mcp-usage --remote`.
5. Prueba: `curl -i -X POST https://mcp.keyflint.dev/norma43/mcp` debe dar `401` con `WWW-Authenticate`.
6. Pon `"remote": true` en `data/catalog.json` y haz push: el instalador pasa a URL + OAuth (Claude, ChatGPT…) y deja
   la instalación local como alternativa. `MCP_REMOTE=1 python3 build.py` lo previsualiza.

Al cambiar un MCP en su repo, vuelve a desplegar para reconstruir la imagen (`docker` cachea por capa; fuerza con
`--build-arg REF=<commit>` si hace falta).

### Probar en local sin Docker

```sh
# 1) los MCP en HTTP (con un gateway real o falso en KEYFLINT_URL)
cd container && WEB_INTEL_TRANSPORT=http NORMA43_TRANSPORT=http CONTABRIDGE_TRANSPORT=http VERIFACTU_TRANSPORT=http \
  DATACLEAN_TRANSPORT=http uvicorn app:app --port 8091
# 2) el Worker apuntando a ese proceso en vez del contenedor
printf 'PUBLIC_ORIGIN=http://localhost:8787\nMCP_UPSTREAM=http://127.0.0.1:8091\n' > .dev.vars
npx wrangler d1 migrations apply mcp-usage --local
npx wrangler dev --enable-containers=false --test-scheduled  # cron: /cdn-cgi/handler/scheduled
```

## Pagos

Los enlaces de Stripe llevan `metadata.tier` (`pro`, `indie`, `agency`) y `source=mcp-hub`. El webhook del gateway (`/api/v1/webhooks/stripe`) emite la licencia y la envía por correo. Tras pagar, Stripe redirige a `/gracias/`.

## Prueba gratis y demos web

- `/probar/`: el visitante pone su correo y recibe al momento una licencia Community (25 créditos), ya puesta en los
  fragmentos de instalación. El Worker la emite con `POST /api/v1/licenses/issue` usando el secreto `KEYFLINT_ADMIN_KEY`.
  Sin ese secreto, cae a `POST /api/v1/billing/trial` (KeyFlint la envía por correo).
- Demos sin instalar en las fichas de Web Intel, Norma 43 y ContaBridge (`POST /api/demo/<slug>`): llaman al MCP real con
  la licencia interna `HUB_DEMO_LICENSE`; el visitante no paga nada.
- Límites en D1 (`hub_limits`, solo hashes): 1 licencia de prueba por correo para siempre, `TRIAL_PER_IP_DAY` (2) por IP y
  día, `DEMO_PER_IP_DAY` (5) demos por IP y día y `DEMO_DAILY_CAP` (300) en total al día. Un fallo no gasta cupo.

```sh
npx wrangler d1 migrations apply mcp-usage --remote   # crea hub_limits
npx wrangler secret put KEYFLINT_ADMIN_KEY             # clave X-Admin-Key del gateway
npx wrangler secret put HUB_DEMO_LICENSE               # licencia LIC-… con créditos para las demos
npx wrangler secret put LIMITS_SALT                    # cualquier texto aleatorio (sal de los hashes)
npm test && npm run deploy
```

# mcp-hub

Sitio estático de **https://mcp.keyflint.dev**: catálogo, instalación, precios y guía de todos los MCPs de KeyFlint.

- `data/catalog.json`: única fuente de datos (MCPs, planes y enlaces de pago de Stripe).
- `python3 build.py` genera `public/` (HTML, sitemap.xml, robots.txt, llms.txt, JSON-LD, `_headers`). Sin dependencias.
- La clave pública del gateway se lee en cada build de `https://licenses.keyflint.dev/api/v1/licenses/public-key` (o de la variable `KEYFLINT_PUBLIC_KEYS`). Si no hay clave válida, el build falla a propósito para no publicar instrucciones rotas.

## Añadir un MCP

Añade una entrada a `mcps` en `data/catalog.json` y haz push. Cloudflare Pages vuelve a publicar.

## Despliegue (Cloudflare Workers, gratis y con uso comercial permitido)

1. Cloudflare › Workers & Pages › Create › Import a repository › `ArceeDev/mcp-hub`.
2. Build command: `python3 build.py`. Deploy command: `npx wrangler deploy` (lee `wrangler.jsonc`).
3. Settings › Domains & Routes › Add › Custom domain › `mcp.keyflint.dev`.

## API (`src/worker.js`)

El Worker solo atiende `/api/*`; el resto lo sirven los assets estáticos.

- `GET /api/saldo?license=…`: plan, estado y créditos (vía `/api/v1/billing/status` del gateway). No devuelve correo ni licencia.
- `POST /api/recuperar {email}`: pide al gateway un enlace de acceso de un solo uso. Responde igual exista o no el correo.

Probar en local: `npx wrangler dev --var GATEWAY_URL:http://127.0.0.1:9009` con un gateway falso.

## Pagos

Los enlaces de Stripe llevan `metadata.tier` (`pro`, `indie`, `agency`) y `source=mcp-hub`. El webhook del gateway (`/api/v1/webhooks/stripe`) emite la licencia y la envía por correo. Tras pagar, Stripe redirige a `/gracias/`.

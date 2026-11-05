# mcp-hub

Sitio estático de **https://mcp.keyflint.dev**: catálogo, instalación, precios y guía de todos los MCPs de KeyFlint.

- `data/catalog.json`: única fuente de datos (MCPs, planes y enlaces de pago de Stripe).
- `python3 build.py` genera `public/` (HTML, sitemap.xml, robots.txt, llms.txt, JSON-LD, `_headers`). Sin dependencias.
- La clave pública del gateway se lee en cada build de `https://licenses.keyflint.dev/api/v1/licenses/public-key` (o de la variable `KEYFLINT_PUBLIC_KEYS`). Si no hay clave válida, el build falla a propósito para no publicar instrucciones rotas.

## Añadir un MCP

Añade una entrada a `mcps` en `data/catalog.json` y haz push. Cloudflare Pages vuelve a publicar.

## Despliegue (Cloudflare Pages, gratis y con uso comercial permitido)

1. Cloudflare › Workers & Pages › Create › Pages › Connect to Git › `ArceeDev/mcp-hub`.
2. Framework preset: *None*. Build command: `python3 build.py`. Output directory: `public`.
3. Custom domains › `mcp.keyflint.dev`. En el DNS de keyflint.dev: `CNAME mcp → <proyecto>.pages.dev`.

## Pagos

Los enlaces de Stripe llevan `metadata.tier` (`pro`, `indie`, `agency`) y `source=mcp-hub`. El webhook del gateway (`/api/v1/webhooks/stripe`) emite la licencia y la envía por correo. Tras pagar, Stripe redirige a `/gracias/`.

# Guía de Alta en Directorios MCP Gratuitos (Paso a Paso)

Con el registro oficial de MCP, PyPI, Cloudflare Workers y Fly.io 100% operativos, el siguiente paso para tracción orgánica y descubrimiento sin coste publicitario es dar de alta los 5 servidores en los principales agregadores y directorios del ecosistema.

---

## 1. Smithery (smithery.ai)
Smithery es el mayor registro comunitario de MCPs. Lee automáticamente el repositorio y permite a los usuarios instalar servidores con un solo comando (`npx -y @smithery/cli install ...`).

- **URL:** https://smithery.ai
- **Pasos:**
  1. Inicia sesión con tu cuenta de GitHub (`ArceeDev`).
  2. Haz clic en **Publish Server** / **Submit**.
  3. Introduce la URL de cada repositorio:
     - `https://github.com/ArceeDev/web-intel-mcp`
     - `https://github.com/ArceeDev/norma43-mcp`
     - `https://github.com/ArceeDev/contabridge-mcp`
     - `https://github.com/ArceeDev/dataclean-mcp`
     - `https://github.com/ArceeDev/verifactu-mcp`
  4. Smithery detectará automáticamente el `server.json` y el `manifest.json`.

---

## 2. Glama (glama.ai/mcp/servers)
Directorio muy popular entre usuarios de Cursor, Windsurf y Claude.

- **URL:** https://glama.ai/mcp/servers
- **Pasos:**
  1. Haz clic en **Submit Server**.
  2. Pega el enlace del repositorio GitHub de cada servidor.
  3. Selecciona la etiqueta correspondiente:
     - `web-intel-mcp`: **Web Scraping / SEO / Tools**
     - `norma43-mcp`: **Finance / Banking / Accounting**
     - `contabridge-mcp`: **Accounting / Productivity**
     - `dataclean-mcp`: **Data / Developer Tools**
     - `verifactu-mcp`: **Legal / Tax / Compliance**

---

## 3. MCP.so (mcp.so)
Directorio indexado enfocado en el ecosistema Claude Desktop y terminales.

- **URL:** https://mcp.so
- **Pasos:**
  1. Inicia sesión con GitHub.
  2. Haz clic en **Submit an MCP**.
  3. Introduce el nombre, enlace de GitHub y enlace a la web oficial (`https://mcp.keyflint.dev`).

---

## 4. PulseMCP (pulsemcp.com)
Explorador y agregador automático de servidores MCP en tiempo real.

- **URL:** https://pulsemcp.com
- **Pasos:**
  1. Ve a **Add Server**.
  2. Añade los enlaces de GitHub. Si ya están en el registro oficial de Anthropic, muchos se indexan automáticamente en 24-48 horas.

---

## 5. Awesome MCP Servers (GitHub) - ¡PR ENVIADO Y EN VERDE!
El repositorio de referencia con más de 10.000 estrellas donde la comunidad de desarrolladores busca servidores MCP.

- **Repositorio:** https://github.com/punkpeye/awesome-mcp-servers
- **Pull Request Creado:** [PR #18793](https://github.com/punkpeye/awesome-mcp-servers/pull/18793)
- **Estado:** OPEN / En cola rápida 🤖🤖🤖 con todas las comprobaciones en verde (has-emoji, alid-name, has-glama).
- **Secciones añadidas:**
  - Browser Automation: ArceeDev/web-intel-mcp
  - Finance & Fintech: ArceeDev/contabridge-mcp, ArceeDev/norma43-mcp, ArceeDev/verifactu-mcp
  - Data Science Tools: ArceeDev/dataclean-mcp
---

## Fichas y Textos Rápidos para Copiar y Pegar

### Web Intel
- **Title:** Web Intel MCP
- **Short Description:** Extract clean Markdown, tech stack, and scored SEO audits for AI agents. Pay per call.
- **Website:** https://mcp.keyflint.dev/web-intel/
- **PyPI:** `pip install web-intel-mcp`

### Norma 43
- **Title:** Norma 43 MCP
- **Short Description:** Parse Spanish AEB43 bank statements, export to Excel, and reconcile movements with invoices.
- **Website:** https://mcp.keyflint.dev/norma43/
- **PyPI:** `pip install norma43-mcp`

### ContaBridge
- **Title:** ContaBridge MCP
- **Short Description:** Transfer accounting journals between a3ASESOR, Sage ContaPlus, QuickBooks, Xero, and CSV.
- **Website:** https://mcp.keyflint.dev/contabridge/
- **PyPI:** `pip install contabridge-mcp`

### DataClean
- **Title:** DataClean MCP
- **Short Description:** Clean messy CSV and Excel tables deterministically: European/US numbers, dates, emails, and schemas.
- **Website:** https://mcp.keyflint.dev/dataclean/
- **PyPI:** `pip install dataclean-mcp`

### Veri*Factu
- **Title:** Veri*Factu MCP
- **Short Description:** Spanish tax compliance for AI: audit hash chains, create AEAT tax QR codes, and validate Facturae XML.
- **Website:** https://mcp.keyflint.dev/verifactu/
- **PyPI:** `pip install verifactu-keyflint-mcp`

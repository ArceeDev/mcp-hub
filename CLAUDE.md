# CLAUDE.md — Protocolo Operativo 4 Argon (Directiva 10x)

Rol: **Principal Staff Software Engineer, Systems Architect & Chief of Innovation**.
Estándar: producción militar, determinismo matemático (SHA-256), seguridad LSSI/GDPR, cero relleno conversacional, ahorro de tokens 10x.

---

## 1. Reglas de Ahorro Extremo de Tokens (10x)

1. **Prohibido leer archivos enteros**:
   - Nunca leas más de 80-90 líneas por llamada si buscas una función o bloque específico.
   - Localiza primero con `grep` / `Select-String` y abre solo el rango exacto (`StartLine`–`EndLine`).
2. **Diffs Quirúrgicos**:
   - Edita bloques mínimos (`Target` -> `Replacement`). Prohibido reimprimir archivos completos.
3. **Zero-Fluff (Estilo Caveman Técnico)**:
   - Prohibidos saludos, disculpas, introducciones y resúmenes redundantes.
   - Formato obligatorio: **Hallazgo/Acción -> Evidencia/Test -> Siguiente paso**.
4. **Salidas de Consola Truncadas**:
   - Ejecuta tests con salida concisa (`pytest -q --tb=short -x`, `node --test`). Nunca vuelques logs crudos de más de 25 líneas.

---

## 2. Enrutamiento Autónomo por Nivel de Complejidad

- **Nivel 1 (Mecánico -> Subagente `flash_lite` / ejecución directa rápida)**:
  - Git status, linting, lectura de logs, comprobación de endpoints HTTP (`curl -I`), conteo de líneas.
- **Nivel 2 (Implementación -> Subagente `flash` / TDD directo)**:
  - Maquetación CSS/HTML, ajustes de copy, tests unitarios aislados, scripts CLI.
- **Nivel 3 (Arquitectura Crítica -> Agente Principal `4 Argon` / `pro`)**:
  - Pasarela Stripe, webhooks, descuento y reembolso atómico de créditos, criptografía Ed25519/HMAC, seguridad OAuth 2.1, concurrencia en Cloudflare Containers y SQLite/Litestream.

---

## 3. Invariantes de Producción del Ecosistema Flint (`mcp-hub` + `keyflint`)

1. **Determinismo Financiero**:
   - Norma 43, VeriFactu, ContaBridge y DataClean jamás inventan importes ni fechas. Misma entrada = mismo hash SHA-256. Movimientos ambiguos se marcan para revisión humana.
2. **Cobro Justo (No-Fault Billing)**:
   - Si una herramienta MCP lanza excepción o devuelve `isError: true`, el crédito se reembolsa automáticamente.
3. **UI B2B Quiet Luxury**:
   - Fondos sólidos (`#0B0D17` / `#FFFFFF`), acento único `#CCFF00`, tipografía Inter/Geist/JetBrains Mono, matriz espacial 8pt, cero emojis en CTAs.
4. **Verificación Obligatoria**:
   - `mcp-hub`: `python build.py` + `npm test` (22/22 pass).
   - `keyflint`: `python run_tests.py` (234/234 pass).

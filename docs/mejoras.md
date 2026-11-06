# Mejoras y nuevas variaciones

Prioridad: **A** = alto impacto/poco esfuerzo, **B** = medio, **C** = apuesta.

## Embudo y negocio (lo que más mueve ingresos)
| P | Mejora | Por qué |
|---|---|---|
| A | Licencia gratis autoservicio (25 créditos `community`) desde el hub | Hoy no existe: nadie puede probar sin pagar. Es el mayor freno |
| A | Publicar en directorios: registro oficial MCP, Smithery, Glama, mcp.so, PulseMCP, directorio de conectores de Claude | Modo remoto ya listo; casi coste cero |
| A | Precios en EUR para España (mantener USD global) | Gestorías esperan € e IVA claro |
| B | Recargas de créditos (top-ups) en el gateway | Hoy solo packs fijos, 1 licencia por compra |
| B | Plan anual Pro (p. ej. 290 $/año) | Caja adelantada, menos churn |
| B | Landing por caso de uso ("conciliar N43 con Claude", "pasar A3 a ContaPlus") | SEO de cola larga con intención de compra |
| B | Panel de uso en `/saldo/` con alertas al 80 % de créditos | Ya hay D1; empuja a recomprar |
| C | Programa de afiliados para gestorías/consultores | Canal B2B barato |

## Calidad de los MCP actuales
| P | MCP | Mejora |
|---|---|---|
| A | norma43 | Probar con extractos reales de 4-5 bancos (Santander, BBVA, CaixaBank, Sabadell, ING) |
| A | contabridge | No devolver `content` y `content_base64` a la vez (duplica respuestas grandes, ~200 MB con 10 MB de entrada) |
| A | todos | Test E2E contra `licenses.keyflint.dev` real con licencia de prueba |
| B | norma43 | Bajar el peor caso de `reconcile_movements` (~13 s): poda por fecha/importe antes de buscar grupos |
| B | web-intel | `render_url` con Cloudflare Browser Rendering para webs JS (SPA); 3-5 créditos |
| B | web-intel | `screenshot` y `pdf_of_page` con el mismo navegador |
| B | contabridge | Presets Holded, Odoo, Sage 200, Contasol |
| B | dataclean | `merge_tables` (join difuso), `dedupe_fuzzy` (CRM), normalizar direcciones |
| C | todos | Versión TypeScript nativa en Worker (sin Container) para web-intel: menos latencia y coste |

## MCPs nuevos
| P | MCP | Mercado | Herramientas | Encaje |
|---|---|---|---|---|
| A | **Norma 19/34 (SEPA ES)** | ES | Generar remesas de recibos (19.14) y transferencias (34.14) XML/plano desde CSV; validar mandatos | Mismo cliente que norma43; reutiliza validadores |
| A | **Modelos 347/349 fichero** | ES | Generar el fichero AEAT desde diario/facturas, sin estado | Complementa contabridge; competidores atados a su SaaS |
| B | **WebWatch** | Global | Cambios en páginas, precios de competencia, SSL/dominio, enlaces rotos | Uso recurrente = ingreso recurrente; necesita cron + D1 (ya hay) |
| B | **FEC / SAF-T** | FR, PT, PL, NO | Exportar diario a FEC francés y SAF-T; validar | Variante global de contabridge, regulado = disposición a pagar |
| B | **DATEV export** | DE | Diario a formato DATEV | Mercado contable mayor de la UE |
| C | **InvoiceExtract** | Global | PDF de factura a JSON validado (NIF, IVA, totales) | Mucha demanda pero OCR/LLM tiene coste y competencia |
| C | **DocDiff** | Global | Diferencias entre contratos/Excel versionados | Determinista, nicho legal/finanzas |

Regla para elegir: determinista, sin estado, coste por llamada ~0, sin MCP dominante, cliente que ya paga otro MCP.

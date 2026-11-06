# MCP + KeyFlint: proceso, comparación y estimaciones a 12 meses

2026-11-05. Cifras orientativas en USD. Los ingresos son supuestos, no datos reales: aún no hay ventas medidas. Los precios de terceros (Cloudflare, Stripe, Fly) hay que verificarlos.

## 1. Resumen

- **Hoy** hay 5 MCP de pago (web-intel, norma43, contabridge, dataclean y verifactu), un hub en mcp.keyflint.dev con modo remoto OAuth, y KeyFlint como gateway de licencias y créditos (self-hosted, BSL).
- **La versión Ultra** es un único hub remoto con prueba gratis, créditos universales, alcance global y KeyFlint Cloud: una plataforma donde cualquier dev publica su MCP y cobra.
- **A 12 meses, escenario base:** la versión actual suma ~18.000 $ acumulados y la Ultra ~66.000 $. La Ultra pide ~150 h de trabajo extra.

## 2. Proceso seguido

1. **Base:** KeyFlint emite licencias Ed25519 y descuenta créditos por llamada (`keyflint-verify`). Cada MCP va en su propio repo.
2. **Nichos:** se descartaron los saturados (BORME, sanciones, TARIC, Verifactu, e-factura, SEPA/camt). El elegido son herramientas **deterministas y sin estado** (coste por llamada ~0) para gestorías multi-cliente y, en global, para datos sucios.
3. **5 MCP en Python**, con tests que usan un gateway falso y licencias firmadas en local.
4. **Estrés:** se corrigieron slowloris, DNS rebinding, ReDoS, OOM y charset. El cobro sale exacto con 100 llamadas concurrentes.
5. **Distribución:** PyPI con Trusted Publishing, bundles `.mcpb` y tarjetas en el chat (MCP Apps).
6. **Hub:** Cloudflare Workers, Stripe Payment Links (Pro 29 $/mes, Indie 149 $, Agency 349 $), `/gracias/`, `/saldo/`.
7. **Remoto (en vivo desde 2026-11-05):** OAuth 2.1, Containers, KV, D1 de uso, límite de 120 llamadas/min y cron diario.
8. **Pendiente (Arcee):** PRs #1/#2 de 3 MCP, publishers en PyPI, contabridge #3, keyflint #50 + deploy en Fly, una compra real de prueba y arreglar Workers Builds en Cloudflare.

## 3. Comparación: versión actual vs Ultra

| Dimensión | Actual | Ultra (simplificada, global, innovada) |
|---|---|---|
| Entrada | Una URL por MCP, licencia `LIC-` | **Una sola URL** (`mcp.keyflint.dev/mcp`) con todas las herramientas; login con Google o GitHub |
| Prueba | No hay licencia gratis autoservicio | **100 créditos/mes gratis** sin tarjeta |
| Precios | 3 packs fijos en USD, sin recargas | **Gratis / Pro 19 $/mes / Team 99 $/mes + recargas de 10 $** y auto-recarga; precio local con Adaptive Pricing |
| Créditos | Por licencia, sin top-ups | Universales entre MCP, con alertas al 80 % |
| Idioma y mercado | ES (+ EN en dataclean) | ES, EN, FR, DE, PT; **packs por país**: ES (N43, 19/34, 347, A3/ContaPlus), FR (FEC), PT/PL (SAF-T), DE (DATEV), global (DataClean, WebIntel, WebWatch) |
| Instalación | Pestañas por cliente, `.mcpb`, PyPI | 1 clic desde el directorio de conectores de Claude, apps de ChatGPT y enlace profundo de Cursor/VS Code |
| Descubrimiento | Solo el hub | Registro oficial MCP, Smithery, Glama, mcp.so, PulseMCP y landings SEO por caso de uso |
| Web | HTML estático | Igual de simple, más un playground para probar herramientas en el navegador sin instalar nada |
| Web Intel | HTML estático | + `render_url`, `screenshot` y `pdf` con Browser Rendering |
| Pago | Payment Links + email | Lo mismo, más **pagos agénticos** (el agente compra créditos con aprobación del usuario) como experimento |
| Fiabilidad | Tests con datos sintéticos | Ficheros reales de 5 bancos, página de estado y SLA en Team |
| Uso | D1 por herramienta en `/saldo/` | Panel con gráficos, exportación CSV y facturas descargables |

## 4. KeyFlint como plataforma

| | Actual | Ultra: **KeyFlint Cloud** |
|---|---|---|
| Qué es | Gateway self-hosted (Docker) de licencias y créditos para MCP, CLI y apps | SaaS gestionado: **sube tu MCP (Python o TS) y cobra en 5 minutos** |
| Quién paga | Devs que se lo instalan: Indie 149 $, Agency 349 $, Founder 199 $, Pro 29 $/mes | Devs que publican: gratis hasta 1.000 $/mes facturados, luego **5 % de comisión** o planes de 29 o 99 $/mes |
| Qué incluye | Firma Ed25519, créditos, webhooks de Stripe y Lemon Squeezy | Hosting en Containers, OAuth remoto, licencias, créditos, Stripe Connect, panel de uso y listado en el marketplace |
| Distribución | GitHub, keyflint.dev | El hub pasa a ser **marketplace** de MCP de terceros; tus 5 MCP son el escaparate |
| Fricción | Desplegar, configurar claves, integrar el SDK | `keyflint deploy` o conectar el repo; cero servidores |
| Foso | Licencias offline verificables | Red de MCP más pagos más datos de uso; los devs se quedan por la base de compradores |

## 5. Estimaciones a 12 meses

Supuestos:
- **Actual:** crecimiento lineal desde 0. El acumulado es ~6,5 veces el mes 12.
- **Ultra:** 2-3 meses de construcción y luego rampa. El acumulado es ~5,5 veces el mes 12.
- **Conversión Ultra:** entre el 3 % y el 4 % de los usuarios gratis pasan a pago, con un ARPU de ~25 $.
- **Ojo:** Indie y Agency son pagos únicos, así que no son MRR.

### 5.1 Ingreso del mes 12

| Escenario | Actual: MCP | Actual: KeyFlint | **Actual total** | Ultra: MCP | Ultra: KeyFlint Cloud | **Ultra total** |
|---|---|---|---|---|---|---|
| Conservador | 381 $ (8 Pro + 1 Indie) | 200 $ | **581 $** | 1.200 $ (1.500 gratis → 45 de pago) | 800 $ (20 devs) | **2.000 $** |
| Base | 1.819 $ (25 Pro + 5 Indie + 1 Agency) | 941 $ | **2.760 $** | 6.000 $ (6.000 gratis → 240 de pago) | 6.000 $ (100 devs + 5 % de 40.000 $) | **12.000 $** |
| Optimista | 6.300 $ (80 Pro + 15 Indie + 5 Agency) | 3.117 $ | **9.417 $** | 20.000 $ (20.000 gratis → 800 de pago) | 23.500 $ (300 devs + 5 % de 200.000 $) | **43.500 $** |

### 5.2 Acumulado de 12 meses

| Escenario | Actual: ingreso | Actual: costes | **Actual neto** | Ultra: ingreso | Ultra: costes | **Ultra neto** |
|---|---|---|---|---|---|---|
| Conservador | 3.777 $ | ~500 $ | **~3.270 $** | 11.000 $ | ~1.370 $ | **~9.630 $** |
| Base | 17.924 $ | ~1.500 $ | **~16.430 $** | 66.000 $ | ~8.220 $ | **~57.780 $** |
| Optimista | 61.250 $ | ~4.900 $ | **~56.360 $** | 239.250 $ | ~34.750 $ | **~204.500 $** |

Costes = infraestructura más ~7 % de Stripe (Managed Payments incluido).
- **Infraestructura Actual:** ~20 $/mes (50 $ en el escenario optimista).
- **Infraestructura Ultra:** 50, 300 o 1.500 $/mes según el escenario (Containers, Browser Rendering, Fly escalado y email).

### 5.3 Costes fijos mensuales (Actual)

| Concepto | $/mes |
|---|---|
| Cloudflare Workers Paid | 5 |
| Containers (`basic`, duermen sin tráfico) | 0-15 |
| Fly.io (gateway KeyFlint) | 2-5 |
| Dominio (prorrateado) | ~1 |
| **Total** | **~10-25** |

Con 1 Pro se cubren. El margen bruto supera el 90 % porque las herramientas son deterministas.

## 6. Esfuerzo para llegar a Ultra

| Bloque | Claude | Arcee |
|---|---|---|
| Pendientes actuales | 0 | 1-2 h |
| Licencia gratis + login Google/GitHub | 5-8 h | 0,5 h |
| Créditos universales, recargas y auto-recarga (gateway) | 10-15 h | 1 h (Stripe) |
| Planes nuevos + precio local | 2 h | 0,5 h |
| Hub remoto de una sola URL | 6-10 h | 0,5 h |
| Directorios + landings SEO + i18n (5 idiomas) | 10-15 h | 1-2 h (cuentas) |
| Browser Rendering en web-intel | 4-6 h | 0,5 h |
| 4 MCP de país (19/34, 347, FEC/SAF-T, DATEV) | 30-40 h | 2 h |
| WebWatch | 10-15 h | 1 h |
| **KeyFlint Cloud** (multi-tenant, Connect, deploy de terceros, marketplace) | 60-80 h | 5-10 h (legal, Connect, soporte) |
| **Total** | **~140-190 h** | **~15-20 h** |

## 7. Orden recomendado

1. Cerrar los pendientes. Sin eso no hay compra real verificada.
2. Licencia gratis y directorios. Es lo que más mueve el escenario.
3. Créditos universales, recargas y planes nuevos.
4. Hub de una sola URL y Browser Rendering.
5. MCP de país (primero Norma 19/34, que es el mismo cliente que norma43).
6. KeyFlint Cloud, cuando haya ≥ 50 clientes de pago propios que demuestren el modelo.

## 8. Riesgos

- **Estimaciones sin datos:** hay que revisarlas al mes 3 con ventas reales del D1 y de Stripe.
- **Marketplace (KeyFlint Cloud):** exige soporte, revisión de MCP de terceros y responsabilidad por su código.
- **Competencia:** la de Smithery, Apify y otros hosts de MCP con cobro. El foso son los nichos regulados por país y las licencias offline.
- **Legal:** VeriFactu y AEAT cambian de plazos, así que las herramientas quedan como de auditoría o generación de ficheros, nunca como SIF.

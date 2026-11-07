# MCP + KeyFlint: proceso, comparación y estimaciones a 12 meses

Actualizado el 2026-11-07 con la recarga libre y los precios nuevos (antes: 2026-11-05). Cifras orientativas en USD; las recargas se cobran en euros y se pasan a dólares a 1 € ≈ 1,1 $. Los ingresos son supuestos, no datos reales: aún no hay ventas medidas. Los precios de terceros (Cloudflare, Stripe, Fly) hay que verificarlos.

## 1. Resumen

- **Hoy** hay 5 MCP de pago (web-intel, norma43, contabridge, dataclean y verifactu), un hub en mcp.keyflint.dev con modo remoto OAuth y prueba gratis de 25 créditos, y KeyFlint como gateway de licencias y créditos (self-hosted, BSL).
- **Cambio del 2026-11-07:** los créditos de los MCP ya no se venden en packs cerrados de pago único. Se compran con **recarga libre desde 5 €** sobre la misma licencia, o con **Pro a 29 $/mes con 1.000 créditos**. Las licencias Lifetime quedan solo para el Gateway self-hosted: **Indie 249 $, Agency 499 $ y Founder 299 $ (50 unidades)**.
- **A 12 meses, escenario base:** la versión actual sube de ~18.000 $ a ~33.000 $ acumulados. El salto viene de cobrar a usuarios ocasionales que antes no compraban (recargas) y de no regalar créditos a 0,007-0,015 $.
- **La versión Ultra** (un hub remoto, créditos universales, KeyFlint Cloud) sigue en ~66.000 $ en el escenario base, y ya tiene hecha una de sus piezas: las recargas.

## 2. Proceso seguido

1. **Base:** KeyFlint emite licencias Ed25519 y descuenta créditos por llamada (`keyflint-verify`). Cada MCP va en su propio repo.
2. **Nichos:** herramientas **deterministas y sin estado** (coste por llamada ~0) para gestorías multi-cliente y, en global, para datos sucios.
3. **5 MCP en Python**, con tests que usan un gateway falso y licencias firmadas en local.
4. **Estrés:** se corrigieron slowloris, DNS rebinding, ReDoS, OOM y charset. El cobro sale exacto con 100 llamadas concurrentes.
5. **Distribución:** PyPI con Trusted Publishing, bundles `.mcpb`, MCP Registry, Smithery y Awesome MCP Servers.
6. **Hub:** Cloudflare Workers, `/probar/` (25 créditos gratis), `/saldo/` con **recarga libre**, Pro por Payment Link, `/gracias/`.
7. **Remoto:** OAuth 2.1, Containers, KV, D1 de uso, límite de 120 llamadas/min y cron diario.
8. **Recarga libre (2026-11-07, keyflint #52 y mcp-hub #9):** sesión dinámica de Stripe Checkout creada por el gateway, créditos calculados en el servidor y sumados a la misma clave; reembolsos y disputas solo tocan esa recarga.

## 3. Modelo de precios nuevo

### 3.1 MCP (mcp.keyflint.dev): solo por uso

| Producto | Precio | Créditos | Precio por crédito |
|---|---|---|---|
| Prueba | 0 € | 25 (una vez) | — |
| Recarga Starter | 5-19 € | 20 por € | 0,050 € |
| Recarga Plus | 20-49 € | 22 por € (+10 %) | 0,045 € |
| Recarga Business | 50-99 € | 25 por € (+25 %) | 0,040 € |
| Recarga Enterprise | 100-500 € | 28 por € (+40 %) | 0,036 € |
| Pro | 29 $/mes | 1.000 al mes | 0,029 $ |

- Las recargas llevan IVA incluido y no caducan. Pro es lo más barato por crédito porque exige recurrencia y los créditos del mes no se acumulan. Si sobran créditos de recarga, se conservan al renovar Pro.
- **Ya no se vende** ningún pack a 0,007-0,015 $ por crédito (antiguos Indie 149 $ / Agency 349 $ del hub).

**Margen de una recarga** (comisión Stripe con Managed Payments estimada en 1,5 % + 0,25 € + 3,5 %, tarjeta EEE):

| Pagas | Créditos | Comisión | % | Neto sin IVA por crédito |
|---|---|---|---|---|
| 5 € | 100 | 0,50 € | 10 % | 0,036 € |
| 19 € | 380 | 1,20 € | 6,3 % | 0,038 € |
| 37 € | 814 | 2,10 € | 5,7 % | 0,035 € |
| 50 € | 1.250 | 2,75 € | 5,5 % | 0,031 € |
| 100 € | 2.800 | 5,25 € | 5,2 % | 0,028 € |

El coste marginal por llamada es ~0, así que el margen bruto supera el 85 % incluso a 5 €.

### 3.2 KeyFlint Gateway (keyflint.dev): software self-hosted

| Licencia | Antes | Ahora | Qué incluye |
|---|---|---|---|
| Indie | 149 $ | **249 $** | Perpetua, 3 nodos, 10.000 créditos iniciales, actualizaciones v1.x |
| Agency | 349 $ | **499 $** | Perpetua, 25 nodos, 50.000 créditos iniciales, v1.x, soporte ≤ 1 día |
| Founder | 199 $ (100 uds.) | **299 $ (50 uds.)** | Indie + todas las actualizaciones v1.x y v2.x |
| Pro | 29 $/mes, 500 cr | 29 $/mes, **1.000 cr** | Uso comercial y actualizaciones mientras esté suscrito |

Founder cuesta 50 $ más que Indie porque incluye la v2; el límite de 50 lo aplica Stripe (Payment Link con tope).

## 4. Comparación: versión actual vs Ultra

| Dimensión | Actual (2026-11-07) | Ultra |
|---|---|---|
| Entrada | Una URL por MCP, licencia `LIC-` | **Una sola URL** (`mcp.keyflint.dev/mcp`) con login Google o GitHub |
| Prueba | 25 créditos gratis en pantalla (`/probar/`) | 100 créditos/mes gratis |
| Precios | **Recarga libre desde 5 € con bonus + Pro 29 $/mes** | + Team 99 $/mes, auto-recarga y precio local |
| Créditos | Universales entre los 5 MCP, sobre la misma clave, sin caducidad | + alertas al 80 % y auto-recarga |
| Idioma y mercado | ES (+ EN en dataclean) | ES, EN, FR, DE, PT con packs por país |
| Instalación | Pestañas por cliente, `.mcpb`, PyPI | 1 clic desde directorios de conectores |
| Descubrimiento | Hub, MCP Registry, Smithery, Awesome MCP Servers | + landings SEO por caso de uso |
| Pago | Checkout dinámico (recargas) + Payment Link (Pro) | + pagos agénticos (experimento) |
| Uso | D1 por herramienta en `/saldo/` | Panel con gráficos, CSV y facturas |

## 5. Estimaciones a 12 meses

Supuestos:
- **Actual:** crecimiento lineal desde 0; el acumulado es ~6,5 veces el mes 12. Founder se suma aparte porque se agota (10, 30 o 50 unidades según el escenario).
- **Recargas:** ticket medio de 15, 18 o 20 € y ingreso neto de IVA (÷ 1,21). Sustituyen a las ventas de Indie/Agency del hub y captan a quien antes no compraba nada por 149 $.
- **Gateway:** con la subida se asume un 25-40 % menos de unidades que en la versión del 2026-11-05, compensado por el precio.

### 5.1 Ingreso del mes 12

| Escenario | MCP: Pro | MCP: recargas | KeyFlint | **Actual total** | Antes (2026-11-05) | Ultra total |
|---|---|---|---|---|---|---|
| Conservador | 232 $ (8) | 341 $ (25 × 15 €) | 249 $ (1 Indie) | **822 $** | 581 $ | 2.000 $ |
| Base | 725 $ (25) | 1.964 $ (120 × 18 €) | 1.055 $ (2 Indie + 1 Agency + 2 Pro) | **3.744 $** | 2.760 $ | 12.000 $ |
| Optimista | 2.320 $ (80) | 7.273 $ (400 × 20 €) | 3.281 $ (6 Indie + 3 Agency + 10 Pro) | **12.874 $** | 9.417 $ | 43.500 $ |

### 5.2 Acumulado de 12 meses

| Escenario | Ingreso (incl. Founder) | Costes | **Neto** | Antes: neto | Ultra: neto |
|---|---|---|---|---|---|
| Conservador | ~8.330 $ | ~820 $ | **~7.500 $** | ~3.270 $ | ~9.630 $ |
| Base | ~33.300 $ | ~2.570 $ | **~30.700 $** | ~16.430 $ | ~57.780 $ |
| Optimista | ~98.600 $ | ~7.500 $ | **~91.100 $** | ~56.360 $ | ~204.500 $ |

Costes = ~7 % de Stripe con Managed Payments (más en recargas pequeñas) más infraestructura (~20 $/mes; 50 $ en el optimista). El IVA ya está descontado de las recargas y no cuenta como coste.

### 5.3 Costes fijos mensuales

| Concepto | $/mes |
|---|---|
| Cloudflare Workers Paid | 5 |
| Containers (`basic`, duermen sin tráfico) | 0-15 |
| Fly.io (gateway KeyFlint) | 2-5 |
| Dominio (prorrateado) | ~1 |
| **Total** | **~10-25** |

Con 1 Pro o 3 recargas de 20 € se cubren.

## 6. Esfuerzo para llegar a Ultra

| Bloque | Claude | Arcee |
|---|---|---|
| Licencia gratis autoservicio | Hecho | — |
| **Recargas sobre la misma licencia + reembolsos** | **Hecho (2026-11-07)** | 0,5 h (secret de Stripe, eventos del webhook, deploy) |
| Login Google/GitHub | 4-6 h | 0,5 h |
| Auto-recarga y alertas al 80 % | 5-8 h | 0,5 h |
| Team 99 $/mes + precio local | 2 h | 0,5 h |
| Hub remoto de una sola URL | 6-10 h | 0,5 h |
| Landings SEO + i18n (5 idiomas) | 10-15 h | 1-2 h |
| Browser Rendering en web-intel | 4-6 h | 0,5 h |
| 4 MCP de país (19/34, 347, FEC/SAF-T, DATEV) | 30-40 h | 2 h |
| WebWatch | 10-15 h | 1 h |
| **KeyFlint Cloud** | 60-80 h | 5-10 h |
| **Total pendiente** | **~130-180 h** | **~12-18 h** |

## 7. Orden recomendado

1. Desplegar keyflint #52 y mcp-hub #9 y hacer una recarga real de 5 €: es la prueba de que el cobro funciona de punta a punta.
2. Venta en España (lun 2026-11-09) con recargas en euros; Día D global (jue 2026-11-12).
3. Medir con D1 y Stripe: ticket medio, % que repite recarga y % que pasa a Pro. Revisar estas cifras al mes 3.
4. Auto-recarga y alertas, luego hub de una sola URL.
5. MCP de país (primero Norma 19/34).
6. KeyFlint Cloud cuando haya ≥ 50 clientes de pago propios.

## 8. Riesgos

- **Estimaciones sin datos:** revisarlas al mes 3 con ventas reales.
- **Recargas pequeñas:** a 5 € la comisión es ~10 %. Si la mayoría compra 5 €, subir el mínimo a 10 €.
- **Fraude con tarjetas robadas:** mitigado con 500 € máximos por pago, 3 recargas por licencia y día, 10 intentos por IP y día y suspensión si se devuelve una recarga ya gastada.
- **Subida de Lifetime:** puede bajar las unidades vendidas; Founder a 299 $ hace de ancla durante el lanzamiento.
- **Legal:** casilla de renuncia al desistimiento en cada recarga; VeriFactu solo como herramienta de auditoría, nunca como SIF.

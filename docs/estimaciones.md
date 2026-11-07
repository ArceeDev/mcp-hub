# Estimaciones

Cifras orientativas en USD. Precios de terceros a verificar en su web.

## 1. Costes fijos mensuales
| Concepto | Coste/mes | Nota |
|---|---|---|
| Cloudflare Workers Paid | 5 $ | Incluye KV, D1 y cuotas base |
| Containers (`basic`, máx. 5) | 0-15 $ | Se cobra por uso; duerme sin tráfico. ~6 $ si una instancia estuviera 24/7 |
| Fly.io (gateway KeyFlint) | 2-5 $ | Máquina pequeña |
| Dominio | ~1 $ | Prorrateado |
| PyPI, GitHub, GitHub Actions | 0 $ | Repos públicos |
| **Total** | **~10-25 $** | |

Variables: Stripe ~3-7 % + 0,30 $ por cobro (Managed Payments suma comisión sobre la estándar). Browser Rendering: horas incluidas en Workers Paid y luego ~0,09 $/hora de navegador.

## 2. Ingreso por crédito (desde 2026-11-07)
| Producto | Precio | Créditos | Precio por crédito |
|---|---|---|---|
| Recarga 5-19 € | libre | 20 por € | 0,050 € |
| Recarga 20-49 € | libre | 22 por € (+10 %) | 0,045 € |
| Recarga 50-99 € | libre | 25 por € (+25 %) | 0,040 € |
| Recarga 100-500 € | libre | 28 por € (+40 %) | 0,036 € |
| Pro | 29 $/mes | 1.000 al mes | 0,029 $ |

Las recargas llevan IVA incluido (neto ÷ 1,21) y se suman a la misma licencia. Se retiraron los packs Indie 149 $ (0,015 $/cr) y Agency 349 $ (0,007 $/cr) del hub: canibalizaban todo lo demás. Coste marginal por llamada ~0; margen bruto > 85 % incluso en recargas de 5 € (comisión ~10 %). Si se añaden herramientas con navegador, cobrar ≥ 3 créditos.

## 3. Escenarios a 6 meses (ingreso mensual)
| Escenario | Pro | Recargas/mes | Ingreso | Neto aprox. |
|---|---|---|---|---|
| Conservador | 4 | 12 × 15 € | ~280 $ | ~240 $ |
| Base | 12 | 60 × 18 € | ~1.330 $ | ~1.220 $ |
| Optimista | 40 | 200 × 20 € | ~4.800 $ | ~4.440 $ |

Supuestos: recargas netas de IVA a 1 € ≈ 1,1 $; neto = menos ~7 % de Stripe y ~20 $ de infraestructura. Las recargas no son MRR, pero quien recarga suele repetir; solo Pro es recurrente. Las licencias del Gateway (Indie 249 $, Agency 499 $, Founder 299 $) se cuentan aparte en [mcp-keyflint-comparacion-12m.md](mcp-keyflint-comparacion-12m.md).

Punto de equilibrio: 1 Pro o 3 recargas de 20 € cubren los costes fijos.

## 4. Esfuerzo (horas Claude + revisión de Arcee)
| Trabajo | Claude | Arcee |
|---|---|---|
| Licencia gratis autoservicio | Hecho | — |
| Recarga libre sobre la misma licencia | Hecho (keyflint #52, mcp-hub #9) | 0,5 h (secret Stripe, eventos del webhook, deploy) |
| Publicar en directorios | Hecho | — |
| Auto-recarga y alerta al 80 % | 5-8 h | 0,5 h |
| `render_url` con Browser Rendering | 4-6 h | 0,5 h |
| MCP nuevo (Norma 19/34 o 347/349) | 6-10 h | 1 h |
| WebWatch (con cron + D1) | 10-15 h | 1 h |
| Pruebas con extractos N43 reales | 2 h | 1 h (conseguir ficheros anonimizados) |

## 5. Orden recomendado
1. Desplegar la recarga y hacer una recarga real de 5 €.
2. Medir ticket medio y repetición de recargas durante el lanzamiento.
3. Auto-recarga y alertas.
4. Norma 19/34 (mismo cliente que norma43).
5. `render_url` en web-intel.
6. WebWatch.

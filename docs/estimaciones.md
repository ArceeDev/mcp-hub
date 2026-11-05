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

## 2. Ingreso por crédito
| Pack | Precio | Créditos | $/crédito |
|---|---|---|---|
| Pro | 29 $/mes | 500 | 0,058 |
| Indie | 149 $ | 10.000 | 0,015 |
| Agency | 349 $ | 50.000 | 0,007 |

Coste marginal por llamada ~0 (deterministas). Margen bruto > 90 % salvo Browser Rendering u OCR. Si se añaden herramientas con navegador, cobrar ≥ 3 créditos.

## 3. Escenarios a 6 meses (ingreso mensual)
| Escenario | Pro | Indie/mes | Agency/mes | Ingreso | Neto aprox. |
|---|---|---|---|---|---|
| Conservador | 5 | 1 | 0 | 294 $ | ~255 $ |
| Base | 15 | 4 | 1 | 1.380 $ | ~1.270 $ |
| Optimista | 50 | 12 | 4 | 4.634 $ | ~4.300 $ |

Supuestos: sin licencia gratuita, la conversión depende de directorios y SEO. Indie/Agency son pagos únicos: no son MRR, hay que reponerlos cada mes. Solo Pro es recurrente.

Punto de equilibrio: 1 Pro cubre los costes fijos.

## 4. Esfuerzo (horas Claude + revisión de Arcee)
| Trabajo | Claude | Arcee |
|---|---|---|
| Cerrar pendientes (merges, PyPI, Fly) | 0 | 1-2 h |
| Licencia gratis autoservicio | 3-5 h | 0,5 h (merge + deploy) |
| Publicar en directorios | 2-3 h | 1 h (cuentas) |
| Precios EUR + plan anual en Stripe | 1 h | 0,5 h |
| `render_url` con Browser Rendering | 4-6 h | 0,5 h |
| MCP nuevo (Norma 19/34 o 347/349) | 6-10 h | 1 h |
| WebWatch (con cron + D1) | 10-15 h | 1 h |
| Pruebas con extractos N43 reales | 2 h | 1 h (conseguir ficheros anonimizados) |

## 5. Orden recomendado
1. Pendientes de Arcee (desbloquea PyPI y `/gracias/`).
2. Licencia gratis + directorios (embudo).
3. Precios EUR.
4. Norma 19/34 (mismo cliente que norma43).
5. `render_url` en web-intel.
6. WebWatch.

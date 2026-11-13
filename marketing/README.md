# Sistema de marketing con aprobación (mínimo trabajo manual)

| Pieza | Automático | Lo que hace Arcee |
|---|---|---|
| `marketing/cola.json` | Claude la genera en lote (ES/EN, X y LinkedIn, con UTM por día) | Nada |
| Issue semanal (`cola-marketing`, lunes 07:00) | GitHub abre un issue con los textos de la semana | Marcar casillas y decir «aprueba la cola» en el hilo de Claude |
| X (@ArceLcn_) | Claude programa los aprobados vía vidIQ (cuesta créditos de vidIQ, más con enlace) | Nada |
| LinkedIn | Programador nativo de LinkedIn (no hay API para perfiles personales sin app aprobada) | Pegar y programar: ~2 min por semana |
| Reddit / Hacker News | Fuera de la cola: sus normas piden publicar y responder a mano | Publicar el día marcado y contestar |
| SEO programático | `build.py` genera guías por banco y rutas banco → ContaSol/A3/ContaPlus | Desplegar (`npm run deploy`) |
| Informe semanal | Worker cron lunes 07:00 UTC → correo a `REPORT_EMAIL` | Poner el secreto una vez |

Reglas: nada de correo en frío (LSSI art. 21), nada de cuentas falsas ni bots que publiquen
en webs sin API (incluido controlar el navegador por depuración remota: incumple las condiciones de LinkedIn y X).
Ningún texto sale sin aprobación de Arcee. Estados en `cola.json`: pendiente → aprobado → programado → publicado (o descartado).

Comandos:

```
python scripts/cola_semana.py --check
python scripts/cola_semana.py --semana 2026-11-16
```

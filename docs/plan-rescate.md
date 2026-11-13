# Plan de rescate de ingresos (13 nov 2026)

## Punto de partida (medido hoy)
- Ingresos externos: **0 €**. Stripe live solo tiene compras de prueba de Arcee. 0 checkouts Despacho abiertos.
- Embudo: 8 altas de prueba (D1 `trial_email`), 16 llamadas a herramientas (la última, el 9 nov), probablemente casi todas de Arcee.
- Tráfico humano medible: ~85 vistas en GitHub en 14 días (7 repos), 3 estrellas. Las descargas de PyPI (~1.480 en un mes)
  y npm (~1.700) son sobre todo espejos, escáneres y CI: solo 1 descarga viene de Windows, que es donde trabajan los asesores.
- Resend: 54 correos transaccionales, 0 aperturas y 0 clics medidos (el seguimiento está desactivado), 0 suscriptores del boletín.
- Conclusión: **el problema no es el producto ni el precio, es que ningún asesor lo ha visto todavía.** Developers y agregadores MCP
  generan descargas, pero no pagan por Norma 43 → ContaSol.

## Regla de oro
Cada hora va a conversaciones con despachos. Nada de funciones nuevas hasta tener 1 cliente de pago, salvo lo que pida un despacho en una demo.
Sin correo comercial en frío (LSSI art. 21). Sí: contacto presencial, presentación personal, grupos donde el asesor está y contenido útil.

## 14 días (13-27 nov): primer euro externo

| # | Acción | Responsable | Fecha | Éxito |
|---|---|---|---|---|
| 1 | Desplegar el registro de visitas propio (PR de este plan) y usar los enlaces de `docs/utm-dia-d.md` | Arcee (deploy) | vie 13 | `/api/admin/visitas` devuelve datos |
| 2 | **Probar ContaSol y a3 de verdad** con el kit de `/kit-prueba/` (importar el APU.ods y el SUENLACE.DAT) | Arcee | antes de la demo | importación sin errores, captura |
| 3 | **Demo con la asesoría de la conocida**: 20 min, con un extracto real suyo en su ContaSol/a3, guion ya entregado | Arcee | semana del 16 | fecha cerrada |
| 4 | Oferta de piloto: 30 días gratis del plan Despacho Básico a cambio de feedback semanal y testimonio con nombre; después 49 €/mes | Arcee | en la demo | piloto aceptado |
| 5 | Día D (PH, X, HN, Reddit) con UTMs. Expectativa: visibilidad dev, no ventas a despachos | Arcee | 14-15 nov | visitas por origen medidas |
| 6 | Grupos de Facebook y Telegram de asesores: entrar en 5, leer normas, aportar el **visor N43 gratis** como recurso (sin vender), 2 publicaciones por semana máx. | Arcee | desde lun 16 | 10 usos del visor con `utm_source=facebook/telegram` |
| 7 | Pedir 2 presentaciones más a la conocida y a su asesoría ("¿a quién más le pasa esto?") | Arcee | tras la demo | 2 nombres |
| 8 | Revisar `/api/admin/visitas` y Stripe cada lunes y jueves (10 min) | Arcee | lun/jue | registro en `informes/` |

**Meta a 14 días:** 2 demos hechas, 1 piloto activo, primer cobro externo ≥ 5 € (recarga) o piloto con fecha de cobro.

## 30 días (hasta el 13 dic): 3 despachos de pago

| # | Acción | Éxito |
|---|---|---|
| 9 | Convertir el piloto en Despacho Básico (49 €/mes) o Pro (99 €/mes) | 1 suscripción |
| 10 | Caso de éxito con el piloto: "de N43 a ContaSol en 2 minutos" (página + post LinkedIn + vídeo de 60 s) | publicado |
| 11 | 3 visitas presenciales a gestorías del barrio/ciudad con el portátil y el visor; dejar tarjeta con QR (`utm_source=qr`) | 3 demos |
| 12 | Charla gratuita de 30 min en una asociación (AECE, REAF, colegio de economistas o de gestores) | fecha cerrada |
| 13 | Boletín del cierre: primer número con el caso de éxito; alta desde visor y validador | 20 suscriptores |
| 14 | SEO ya publicado (bancos → a3/ContaSol, visor, validador): revisar Search Console y reforzar las 3 páginas con más impresiones | 300 vistas humanas/semana |

**Meta a 30 días:** 3 despachos pagando (≈ 150-300 €/mes), 5 demos hechas, 20 suscriptores.

## Criterio de corte (13 dic)
Si tras 5 demos no hay ningún pago, el fallo es de oferta, no de visibilidad. Opciones en este orden:
1. Venderlo como **servicio** ("os mando cada lunes los extractos ya convertidos a vuestro programa", 49 €/mes), sin que el despacho instale nada.
2. Bajar la entrada a un plan de 19 €/mes con menos créditos.
3. Cambiar de nicho dentro de la misma tecnología (pymes que llevan su propia contabilidad con Holded/Excel).

## Qué NO hacer estas 4 semanas
- Más MCPs, más integraciones o rediseños del hub.
- Publicidad de pago (`docs/inversion-por-fases.md`: no gastar sin ingresos).
- Correo en frío a listas compradas o inventadas.
- Medir el éxito por descargas de PyPI/npm o estrellas: no son clientes.

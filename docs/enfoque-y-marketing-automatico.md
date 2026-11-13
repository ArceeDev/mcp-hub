# Enfoque, variantes a testear y marketing automático (2026-11-13)

## 1. Diagnóstico honesto

**Datos a hoy:** 0 € externos, 4 pruebas (probablemente de Arcee), boletín con 0 altas, tráfico real casi nulo
(la mayoría de las 2,07k «visitas» son el escáner MCP «Talaria» y bots). Es decir: **aún no sabemos si el nicho convierte,
porque casi nadie del nicho ha visto el producto.** El problema hoy es distribución, no producto.

**Lo bueno del nicho despachos:**
- Dolor real y repetitivo (cierre mensual, extractos de muchos clientes), formatos españoles que nadie quiere construir (foso).
- Ticket B2B de 49–149 €/mes: con 20 despachos ya son ~1–3 k€/mes.
- Producto determinista y verificable (cuadre de saldos, 555 sin adivinar), que es lo que un asesor necesita para fiarse.

**Lo malo:**
- Asesores compran por confianza y recomendación, no por redes de devs (PH, HN, X no son su canal).
- «MCP» y «Claude» no significan nada para ellos: hay que vender «Norma 43 a ContaSol/A3 sin teclear».
- Ciclo de venta lento y diciembre es el peor mes para que prueben algo nuevo.

**Conclusión:** el enfoque es razonable, pero apostar todo a él sin datos es arriesgado. Lo correcto es **testear tres
posicionamientos en paralelo con coste casi cero** y decidir el 13 de diciembre con números.

## 2. Tres variantes a testear (4 semanas, mismo producto)

| Variante | A quién | Mensaje | Canal barato | Página |
|---|---|---|---|---|
| A. Despachos (actual) | Asesorías y gestorías | «Norma 43 a ContaSol/A3/ContaPlus, cuadrado y sin teclear» | SEO por banco/programa, LinkedIn, grupos de Facebook/Telegram de asesores, 1 contacto cálido | /asesorias/, guías por banco |
| B. Autónomos y pymes que llevan su contabilidad | Pyme con ContaSol/Holded/Excel | «Tu extracto del banco a Excel o a tu programa en 1 minuto, gratis el visor» | SEO de herramientas gratis (visor, validador IBAN), boletín | /visor-norma-43/, /validar-iban-cif/, /norma43-a-excel/ |
| C. Desarrolladores globales | Devs que crean MCP y quieren cobrar | «Cobra por tu MCP: créditos, reembolso si falla, licencias Ed25519» (KeyFlint) | Show HN, r/mcp, X en inglés, registros MCP, GitHub | keyflint.dev |

Variante D, si nada de lo anterior da señal: **servicio gestionado** («te dejo los extractos de tus clientes en A3 cada mes
por X €/cliente»), vendido a 3–5 despachos a mano. Es menos escalable pero valida que el dolor existe y paga.

### Criterio de decisión (13-dic, con el informe semanal)

Medir por variante con `utm_campaign` y la página de entrada:

| Señal (4 semanas) | Umbral para seguir | Si no se alcanza |
|---|---|---|
| Visitas humanas a las páginas de la variante | ≥ 150 / semana en la última semana | El canal no funciona: cambiar canal antes que producto |
| Visitas → prueba gratis | ≥ 3 % | El mensaje o la página no convencen: reescribir copy/CTA |
| Pruebas → uso real (≥ 2 llamadas) | ≥ 40 % | Fricción de instalación: priorizar modo web/lote |
| Pruebas → pago | ≥ 1 cliente o 1 piloto comprometido | Pasar a la variante D (servicio) para ese segmento |

Regla: la variante con mejor **coste en horas de Arcee por prueba activa** se queda con el 70 % del esfuerzo en enero.

## 3. Product Hunt: plan B

La cuenta nueva **sí puede publicar**, pero desde 2025–2026 PH pondera los votos por antigüedad e historial de las cuentas y
solo destaca en portada una minoría de lanzamientos. Con cuenta y red nuevas, lo esperable es un lanzamiento sin destacar.
Además el público de PH son devs y makers, no asesores (solo encaja con la variante C).

Opciones, de mejor a peor:
1. **Mover PH a sáb 5-dic** y usar estas 3 semanas para calentar la cuenta (comentar con criterio 10 min al día en lanzamientos
   de herramientas MCP/IA, completar perfil, seguir a makers). El sáb 14 se mantiene X + LinkedIn y el dom 15 Show HN + Reddit.
2. **Pedir un hunter con cuenta establecida** (mensaje educado a alguien que haya cazado herramientas MCP); no hace falta,
   desde 2024 PH no da ventaja por hunter, pero su red ayuda.
3. **Lanzar el 14 igualmente** como prueba sin expectativas, sin pedir votos (pedir votos explícitamente va contra sus normas).

**Decidido por Arcee (13-nov): opción 1, Product Hunt el sábado 5 de diciembre a las 09:01.**
El 14 siguen X y LinkedIn; el 15, Show HN y Reddit.

### Calentamiento de la cuenta de PH (Arcee, ~10 min/día)

| Fecha | Tarea |
|---|---|
| 14-20 nov | Perfil completo (foto, bio de Flint, enlaces a X/LinkedIn/GitHub). Seguir 20 makers de herramientas IA/MCP/fintech. 1 comentario útil al día en lanzamientos del día (pregunta concreta o feedback, nunca «felicidades» vacío). |
| 21-27 nov | Votar y comentar 1-2 lanzamientos al día de tu ámbito. Publicar 1 hilo en las discusiones de PH (p. ej. «¿Cómo cobráis por un servidor MCP?»). Crear la página «Coming soon» de Flint. |
| 28 nov-4 dic | Revisar galería (lanzamiento/product-hunt/), primer comentario y tagline. Programar el lanzamiento para el 5-dic 00:01 PT. Avisar a contactos reales con un enlace a la página, sin pedir votos (va contra las normas de PH). |
| 5 dic | Estar disponible de 09:00 a 21:00 para responder cada comentario en menos de 30 min. Post en X y LinkedIn de la cola. |

Alternativas el sáb 14 con el mismo esfuerzo: Alternativas el sáb 14 con el mismo esfuerzo: Peerlist Launchpad, Uneed, MicroLaunch,
y los directorios MCP en los que ya estamos (Registro oficial, Glama, Arcade).

## 4. Marketing automatizado (lo que ya queda montado en el repo)

Ver `marketing/README.md`. Resumen:
- **Cola de 20 publicaciones** (16-nov a 10-dic) ES/EN en `marketing/cola.json`, cada una con UTM propio para medir.
- **Issue semanal automático** los lunes con los textos para aprobar (GitHub Action `cola-marketing`).
- **X**: tras aprobar, Claude los programa en @ArceLcn_ vía vidIQ. **LinkedIn**: programador nativo (2 min/semana).
- **SEO programático ampliado**: +6 bancos (Bankinter, Unicaja, Kutxabank, Ibercaja, Abanca, Cajamar) × guía de descarga,
  página a ContaSol, a A3 y a ContaPlus = 24 páginas nuevas.
- **Informe semanal por correo** (Worker cron lunes 07:00 UTC): visitas propias vs semana anterior, origen, campañas,
  pruebas nuevas, licencias activas, con semáforo frente a las metas. También en `GET /api/admin/semanal`.
- **Por qué no «remote debugging» para publicar:** automatizar el navegador para postear en LinkedIn/X incumple sus
  condiciones y puede costar la cuenta. Las rutas de arriba usan APIs oficiales o el programador nativo.

## 5. Desarrollo de producto (siguientes pasos, por orden)

1. Probar ContaSol y A3 reales con el kit (`/kit-prueba/`): sin esto, la variante A no se puede vender con garantías.
2. Modo web sin instalación para pymes (variante B): ya existe `/lote/`; añadir «arrastra y descarga» para un solo extracto.
3. Página de KeyFlint para devs con ejemplo de 10 líneas (variante C), para el post del Show HN.

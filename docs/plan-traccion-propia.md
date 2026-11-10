# Plan de tracción propia: 30 días (11-nov → 10-dic-2026)

Objetivo: que Flint by KeyFlint consiga visitas, pruebas y clientes **por canales que controlamos** (web, buscadores, lista de correo, contenido descargable, presencia directa en comunidades de asesores), sin depender de que un algoritmo, un directorio o un mantenedor nos elija.

Leído antes: `docs/plan-mercado-amplio.md` (despachos primero, decidido el 8-nov), `docs/plan-maestro-lanzamiento.md` (Día D 14-15 nov), `docs/marketing-lanzamiento.md` y la memoria del proyecto. Este plan **no repite** lo ya hecho: landings `norma43-a-{a3,contaplus,contasol,excel}`, `csv-a-{a3,contaplus,contasol}`, 6 páginas banco/pasarela → ContaSol, `/asesorias/`, `/confianza/`, `/probar/`, `/kit-prueba/`, `/en/`, feed.xml, IndexNow, llms.txt, Registro MCP, PyPI, Glama, Arcade, 100 contactos de LinkedIn.

---

## 1. Diagnóstico: por qué Reddit y X no han dado visitas

No hay cifras de tráfico por canal (la analítica está en el HTML pero nadie ha mirado el panel ni hay UTM), así que esto es razonamiento sobre lo que sí sabemos, no una medición.

1. **Público equivocado.** El comprador decidido el 8-nov es el despacho (asesor de 45 años con a3/ContaSol). Ese perfil no está en r/mcp ni en X; está en Google, YouTube, grupos de Facebook/Telegram de asesores y en su colegio o asociación (memoria: solo el 4 % usa LinkedIn como canal principal). En Reddit/X hablamos a desarrolladores que no compran Norma 43.
2. **Cuentas sin historial.** Cuentas nuevas con poco karma y pocos seguidores: Reddit filtra o retira enlaces propios y X apenas muestra posts de cuentas sin interacción. Un post suelto con enlace es casi invisible.
3. **Mensaje en jerga.** «Servidor MCP», «créditos», «determinista» no es un dolor reconocible. El asesor busca «cómo importar el extracto del BBVA en ContaSol», no «MCP».
4. **Pico sin captura.** Aunque alguien entrara, no había forma de quedarse con él si no compraba ese día: no hay lista de correo («One per email. No newsletter.») ni recurso descargable a cambio del correo.
5. **Un solo intento.** Las redes premian la repetición durante semanas; los buscadores premian páginas útiles que se acumulan. Lo segundo encaja mejor con un fundador que trabaja entre semana.

Conclusión: **pasar de «anunciar» a «ser encontrado»**. Cada pieza de trabajo debe quedarse publicada en nuestro dominio y seguir trayendo gente el mes siguiente.

---

## 2. Los cinco motores (por orden de impacto esperado)

### Motor A. SEO con intención de compra (lo que falta)

Ya cubrimos «formato → programa» para N43/CSV y 6 bancos → ContaSol. Faltan estas familias, que responden a búsquedas reales de asesores y llevan directo a la herramienta:

| # | Familia de páginas | Ejemplo de consulta | Nº páginas | Herramienta |
|---|---|---|---|---|
| A1 | **Cómo descargar el Norma 43 en cada banco** (paso a paso + enlace a convertirlo) | «descargar norma 43 sabadell», «cuaderno 43 bankinter» | 12 (Santander, BBVA, CaixaBank, Sabadell, Bankinter, Unicaja, Kutxabank, Abanca, Ibercaja, Cajamar, ING, Openbank) | norma43 |
| A2 | **Banco → a3 / ContaPlus / Sage 50 / Holded** (hoy solo → ContaSol) | «extracto bbva a a3», «importar banco en holded» | 6 bancos × 3 programas = 18, publicar solo las 6 de mayor volumen primero | contabridge |
| A3 | **Diario entre programas** | «pasar contabilidad de contaplus a a3», «migrar a3 a contasol» | 6 parejas (ContaPlus↔a3, ContaPlus→ContaSol, a3→ContaSol, Sage 50→a3, Excel→a3) | convert_journal |
| A4 | **Extracto PDF → Excel / programa** | «convertir extracto pdf a excel», «extracto pdf a contasol» | 3 | pdf_bank_to_journal |
| A5 | **Remesas SEPA** | «generar remesa sepa xml cuaderno 19», «fichero transferencias pain.001» | 2 | sepa_* |
| A6 | **Guías de referencia** (atraen enlaces y respuestas de IA) | «qué es norma 43», «formato cuaderno 43 registros 11 22 23 33 88», «cuenta 572 555 conciliación» | 3 | — |

Reglas para que no sea «contenido basura» (Google penaliza páginas generadas en masa):
- Cada página con un dato propio y verificable: ruta de menú real del banco o programa, columnas reales, error típico y su arreglo, captura o fichero de ejemplo.
- Si no podemos verificar el paso a paso de un banco, la página dice «cómo suele ser» y pide corrección; nunca inventar menús.
- Enlazado interno: guía → página de conversión → `/probar/`; cada banco enlaza a sus programas.
- Respetar los límites reales de `movements_from_csv` (memoria `mcp-hub-bank-pages`): mientras no estén los alias de columnas, la página indica qué columna renombrar.

### Motor B. Herramientas gratis en el navegador (imán de tráfico y enlaces)

Las herramientas gratuitas son lo que la gente comparte y enlaza sin que se lo pidamos. Todas en el propio hub, en JavaScript del lado del cliente (el fichero no sale del navegador: refuerza el mensaje de privacidad):

| # | Herramienta | Consulta | Por qué |
|---|---|---|---|
| B1 | **Visor Norma 43 online** (abre el .n43, muestra cuentas, saldos y movimientos, comprueba los totales del registro 33) | «visor norma 43», «abrir fichero n43» | Uso recurrente; al final, botón «pasarlo a ContaSol/a3» → `/probar/` |
| B2 | **Validador IBAN / NIF / NIE / CIF / identificador de acreedor SEPA** | «validar cif», «comprobar iban» | Volumen de búsqueda alto; ya existe la lógica en `validate_identifier` (gratis) |
| B3 | **Calculadora de horas ahorradas** (nº clientes × extractos/mes × minutos) | «coste conciliación bancaria» | Convierte el ahorro en euros y enlaza al Plan Despacho |

### Motor C. Lista de correo propia (el único canal que nadie nos puede quitar)

- **«Boletín del cierre»**: un correo al mes con un truco práctico (p. ej. «el error de la cuenta 555 que da a3 al importar»), novedades de Flint y fechas fiscales. Alta con **doble opt-in** vía Resend (ya integrado), baja en un clic. Cumple LSSI art. 21 y RGPD porque la persona se apunta.
- **Imanes** a cambio del correo: (1) Kit de prueba del despacho (ya existe en `/kit-prueba/`), (2) **Plantilla Excel de conciliación bancaria** con fórmulas, (3) **Checklist de cierre trimestral** en PDF, (4) Guía PDF «Norma 43 en 10 minutos».
- La prueba gratis (`/probar/`) ya pide correo: añadir casilla **separada y no marcada** «quiero el boletín» (sin ella no se puede enviar el boletín).
- RSS: `feed.xml` existe; incluir en él las guías nuevas para que lectores y agregadores lo recojan solos.

### Motor D. Presencia directa en comunidades de asesores (manual y legal)

Nada de correo en frío (LSSI art. 21 lo prohíbe también a empresas). Lo que sí:

1. **Responder, no anunciar.** 15 min al día en grupos de Facebook/Telegram de asesores, foros como el de Comunidad Fiscal y preguntas en LinkedIn. Regla 9:1: nueve respuestas útiles sin enlace por cada mención a Flint, y solo cuando alguien pregunta justo por eso. Enlazar a la **guía**, no a la portada.
2. **Asociaciones y colegios** (AECE, REAF-Colegio de Economistas, asociaciones provinciales de asesores): ofrecer **una charla gratuita de 30 min** «Conciliar bancos e importar en a3/ContaSol sin teclear» para sus socios. Ellos convocan; nosotros aportamos contenido. Contacto por su formulario o teléfono público (relación institucional, no envío masivo).
3. **Prescriptores** (Javier D., Comunidad Fiscal, grupo Experto Contable, ya identificados): ofrecer acceso gratis y un código para su comunidad a cambio de que lo prueben, no de que lo anuncien.
4. **Accountex España (18-19 nov, IFEMA, entrada gratis profesionales)**: si Arcee puede ir un día, es la mayor concentración de despachos del año. Ir con el visor (B1) en el móvil y tarjetas con QR a `/kit-prueba/?utm_source=accountex`.
5. **La conocida secretaria de empresa** (memoria 9-nov): conseguir la presentación a su asesoría. Un caso real vale más que cien posts.

### Motor E. Vídeo en YouTube (buscador nº 2, sin algoritmo de seguidores)

Los tutoriales cortos con título de búsqueda («Importar el extracto del BBVA en ContaSol en 2 minutos») se encuentran por búsqueda, no por seguidores. Ya existe la cadena de producción (Playwright + ffmpeg + ElevenLabs). 1 vídeo por cada página A1/A2 de más volumen, insertado en esa página (sube el tiempo en página y aparece en Google Vídeos).

### Alianzas con fabricantes de software contable (más lento, alto valor)

- **Holded** (tiene marketplace de apps y MCP propio), **Software DELSOL/ContaSol** (programa de distribuidores), **a3 innuva / Wolters Kluwer** y **Sage** (marketplaces): solicitar el alta como integración. Es dependencia de terceros, así que va al final y sin esperar respuesta: lo que controlamos es que nuestras páginas «→ ContaSol/a3/Holded» ya funcionan aunque no nos listen.
- **Distribuidores locales** de ContaSol y a3 (pequeñas empresas que instalan el programa a despachos): proponer reventa con comisión. Contacto por teléfono o formulario.

---

## 3. Medición (sin esto no sabremos qué funciona)

| Qué | Cómo | Quién |
|---|---|---|
| Visitas por página y origen | Cloudflare Web Analytics (el token ya está en `data/catalog.json`; comprobar que el panel recibe datos tras el último deploy) | Arcee comprueba, Claude lee el panel si Arcee pasa capturas o exporta |
| Búsquedas e indexación | **Google Search Console** y **Bing Webmaster Tools**: verificar `mcp.keyflint.dev` y enviar `sitemap.xml` | Arcee (requiere su cuenta) |
| Origen de cada enlace que compartimos | UTM obligatorio: `?utm_source=<sitio>&utm_medium=<social|comunidad|video|evento>&utm_campaign=<pieza>` | Ambos |
| Embudo | Visita → `/probar/` → licencia de prueba emitida → primera llamada con éxito → compra o recarga. Contar con datos que ya existen en D1 (pruebas) y en el gateway (licencias, compras) | Claude: consulta semanal y tabla en este doc |
| Lista de correo | Altas confirmadas y bajas (Resend) | Claude |

Revisión cada domingo: 15 min con 5 números (visitas orgánicas, impresiones en Search Console, pruebas, suscriptores, pagos). Si una familia de páginas no tiene impresiones a las 3 semanas, se reescribe su título antes de añadir más.

---

## 4. Plan semana a semana

Supuesto de tiempo de Arcee: **30-45 min los días laborables y 2-3 h el fin de semana**. Todo lo que Claude prepara llega como PR al hub sobre `production`; Arcee revisa, fusiona y despliega (`npm run deploy`).

### Semana 1 (11-17 nov): medir, capturar y primeras páginas

| Tarea | Quién |
|---|---|
| Verificar el dominio en Search Console y Bing Webmaster; enviar sitemap | **Solo Arcee** |
| Comprobar que Cloudflare Web Analytics recibe visitas | **Solo Arcee** |
| PR: formulario «Boletín del cierre» con doble opt-in (Resend) + casilla separada en `/probar/` + página de baja | Claude |
| PR: **Visor Norma 43 online** (B1) en el navegador | Claude |
| PR: 4 guías A1 (Santander, BBVA, CaixaBank, Sabadell) + guía A6 «Qué es Norma 43» | Claude |
| Plantilla de enlaces con UTM para cada canal | Claude |
| Día D global (14-15 nov) tal como está planificado, pero **todos los enlaces con UTM y apuntando al visor o al kit**, no a la portada | Arcee publica; Claude deja los textos con UTM |
| 15 min/día respondiendo en 2 grupos de asesores (sin enlaces la primera semana) | **Solo Arcee** |
| Decidir si va a Accountex el 18 o 19 nov | **Solo Arcee** |

### Semana 2 (18-24 nov): herramientas gratis y diarios entre programas

| Tarea | Quién |
|---|---|
| PR: **Validador IBAN/NIF/CIF/SEPA** (B2) | Claude |
| PR: 6 páginas A3 (diario entre programas) | Claude |
| PR: 4 guías A1 más (Bankinter, Unicaja, ING, Kutxabank) | Claude |
| Imán: plantilla Excel de conciliación bancaria (descarga a cambio del correo) | Claude |
| Accountex (si va): 20 conversaciones, tarjetas con QR + UTM | **Solo Arcee** |
| Contactar 3 asociaciones/colegios ofreciendo la charla gratuita (formulario o teléfono) | **Solo Arcee**; Claude redacta el texto |
| Presentación a la asesoría de la conocida | **Solo Arcee**; Claude prepara la demo con sus ficheros si lo autorizan |

### Semana 3 (25 nov-1 dic): vídeo y banco → a3/Holded

| Tarea | Quién |
|---|---|
| 3 vídeos tutoriales (guion, voz, render) para las páginas con más impresiones | Claude produce; **Arcee sube a YouTube** |
| PR: 6 páginas A2 de más volumen (BBVA/Santander/CaixaBank → a3 y Holded) | Claude |
| PR: Calculadora de horas ahorradas (B3) | Claude |
| Primer «Boletín del cierre» (borrador) | Claude redacta; **Arcee aprueba y envía** |
| Solicitar alta en marketplace de Holded y programa de distribuidores DELSOL | **Solo Arcee** (cuenta de empresa) |
| Ajustar títulos de páginas con impresiones pero sin clics (datos de Search Console) | Claude, con captura o exportación de Arcee |

### Semana 4 (2-10 dic): consolidar y decidir

| Tarea | Quién |
|---|---|
| PR: páginas A4 (PDF → Excel/programa) y A5 (remesas SEPA) | Claude |
| PR: checklist de cierre trimestral (PDF) como imán, con fecha de modelos del 4T (enero) | Claude |
| Primera charla en una asociación (si alguna aceptó) | **Solo Arcee** |
| Caso real publicado (solo con permiso escrito y datos verdaderos) | Arcee consigue el permiso; Claude lo redacta |
| Informe de 30 días: qué familia de páginas y qué canal trajo pruebas; recortar lo que no funcione y doblar lo que sí | Claude |

---

## 5. Métricas objetivo (honestas)

Un dominio nuevo tarda de 2 a 6 meses en posicionar. En 30 días lo realista es **empezar a aparecer**, no dominar. Rangos, no promesas:

| Métrica (día 30) | Mínimo | Bueno | Notas |
|---|---|---|---|
| Páginas nuevas indexadas | 25 | 40 | Search Console → Páginas |
| Impresiones en Google (acumulado del mes) | 2.000 | 8.000 | La primera señal de que el SEO funciona |
| Visitas orgánicas (último mes) | 150 | 500 | Sin contar Día D |
| Usos del visor/validador | 100 | 400 | Herramientas gratis |
| Suscriptores confirmados | 30 | 100 | Lista propia |
| Pruebas gratis activadas | 20 | 50 | `/probar/` |
| Despachos pagando | 1 | 5 | Plan Despacho o recarga |
| Charlas en asociaciones cerradas | 1 | 3 | Canal de mayor confianza |

A 90 días, si el SEO se comporta como es normal en nichos con poca competencia como este, las visitas orgánicas deberían multiplicarse por 3-5 respecto al día 30. Si a los 30 días hay menos de 1.000 impresiones, el problema es de títulos o indexación, no de volumen de páginas.

---

## 6. Qué NO hacer

- No enviar correos comerciales a quien no se ha apuntado (LSSI art. 21), ni comprar ni raspar listas, ni usar `leads_gestorias_sprint7d.csv` (nombres no verificados).
- No automatizar LinkedIn ni publicar con bots en grupos.
- No generar cientos de páginas iguales cambiando solo el nombre del banco.
- No prometer que la IA no ve los datos; usar el mensaje validado: «tus extractos no salen de tu equipo hacia KeyFlint, solo viaja licencia y crédito» (solo instalación local).
- No inventar casos de éxito, cifras de clientes ni testimonios.
- No gastar en anuncios hasta tener ingresos (`docs/inversion-por-fases.md`).

## 7. Pendientes que bloquean parte del plan

- **ContaSol y a3 no se han probado con un programa real.** Antes de empujar las páginas A2/A3 con fuerza, conviene una prueba real (la asesoría de la conocida o un piloto de Accountex).
- **Alias de columnas CSV** (Revolut, Stripe, PayPal, «Movimiento») pendientes en contabridge: hasta entonces, las páginas de esos bancos deben indicar qué columna renombrar.

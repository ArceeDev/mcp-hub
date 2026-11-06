# Marketing y lanzamiento: el universo Flint

2026-11-05. Objetivo: que el día de salida cause impacto y, a partir de ahí, que cada mes aparezca algo nuevo bajo la misma marca.

## 1. Idea central

**No vendemos MCPs sueltos. Vendemos un universo en expansión con una sola marca.**

- **KeyFlint** es el sol: plataforma, cuenta, créditos y pagos.
- **Flint** es la familia de productos. Cada MCP es un *planeta* con el mismo apellido, el mismo color y la misma cuenta.
- Cada mes nace un planeta nuevo, así que siempre hay una noticia que contar.

**Mensaje único:** *"La IA propone. Flint lo comprueba."*
Todas las herramientas son deterministas: no inventan, dan el mismo resultado siempre y cobran solo si funcionan. Ese es el diferencial frente a "pedírselo al chat".

## 2. Arquitectura de marca

| Hoy | Nombre universo | Promesa en una línea | Mercado |
|---|---|---|---|
| web-intel | **Flint Web** | Lee y audita cualquier web para tu IA | Global |
| norma43 | **Flint Bank** | Tus extractos bancarios, leídos y conciliados | ES, y luego UE |
| contabridge | **Flint Ledger** | Mueve la contabilidad entre programas sin teclear | ES + QuickBooks/Xero |
| dataclean | **Flint Data** | Excel y CSV limpios sin perder ni un dato | Global |
| verifactu | **Flint Fiscal** | Revisa VeriFactu y Facturae antes de que lo haga Hacienda | ES |
| (futuro) | Flint Watch, Flint SEPA, Flint FEC, Flint DATEV… | Mismo patrón | País a país |

Reglas de marca:
- **Mismos colores** (#0B0D17 + #CCFF00), la fuente IBM Plex y el mismo estilo de icono en todos los planetas.
- **Dominios:** `flint.keyflint.dev/<planeta>`, o comprar `flint.dev`, `getflint.ai` o `useflint.com` si están libres (comprobarlo antes de anunciar nada).
- **Los nombres de paquete técnicos se quedan** (`norma43-mcp`…) por SEO técnico. La marca visible es Flint.
- **Una cuenta y unos créditos** valen para todo el universo. Esto es lo que hace que sea un universo y no una colección.
- Antes de fijar el nombre, buscar "Flint" en EUIPO, OEPM y USPTO (clase 9 y 42), porque existen marcas parecidas.

## 3. Requisitos antes de anunciar nada (bloqueantes)

Una mala primera impresión no se repite. Sin esto, no hay lanzamiento:

1. **Compra real verificada** de principio a fin: Stripe → licencia → llamada → saldo.
2. **Prueba gratis sin tarjeta** (100 créditos), en menos de 2 minutos desde que llegas a la web hasta el primer resultado.
3. **Una sola URL remota** que funcione en Claude, ChatGPT, Cursor y VS Code.
4. **Vídeo de 30-60 s por planeta** con el problema, el agente usándolo y el resultado.
5. **Página de estado**, analítica (Plausible o Cloudflare Web Analytics) y un email de soporte que alguien conteste en menos de 24 h.
6. **Demo en el navegador** (playground) para quien no tenga un cliente MCP.
7. **Web en ES y EN** como mínimo.

## 4. Pre-lanzamiento (T-30 a T-1)

| Cuándo | Acción |
|---|---|
| T-30 | Landing "Próximamente" con lista de espera (con 500 créditos extra para quien se apunte) |
| T-30 | Reclutar **20 beta testers**: 10 gestorías, 5 agencias SEO y 5 devs. A cambio, pack Agency gratis y su logo en la web si aceptan |
| T-21 | Casos reales: "Gestoría X concilia 3 bancos en 4 minutos". Solo con permiso y datos verdaderos |
| T-14 | Kit de prensa: logos, capturas, vídeos, fundador, cifras y una frase citable |
| T-14 | Fichas preparadas en: registro oficial MCP, directorio de conectores de Claude, Smithery, Glama, mcp.so, PulseMCP y awesome-mcp-servers |
| T-10 | Contactar con newsletters de IA (TLDR AI, Ben's Bites, The Rundown) y medios ES (Xataka, Genbeta, Hipertextual) con el embargo hasta el día D |
| T-7 | Preparar Product Hunt: maker, galería, primer comentario y un *hunter* con audiencia |
| T-7 | Escribir el hilo de X/LinkedIn, el post de Show HN y los de Reddit (r/ClaudeAI, r/mcp, r/SaaS, r/LocalLLaMA, r/spain y foros de asesores) |
| T-3 | Ensayo general: probar todo con 5 personas que no lo conozcan y corregir lo que falle |
| T-1 | Congelar el código. Nada de deploys el día D salvo arreglos críticos |

## 5. Día D: "Flint Launch Week"

En vez de un solo anuncio, **5 días seguidos con un planeta por día**. Es una semana entera de noticias y cada día da una razón para volver a hablar del proyecto.

| Día | Planeta | Gancho |
|---|---|---|
| Lunes | **KeyFlint + Flint Web** | "El universo de herramientas que tu IA puede usar sin equivocarse". Product Hunt + Show HN |
| Martes | **Flint Data** | "Pega un Excel de 50.000 filas sucio y recupéralo limpio" (global, muy viral) |
| Miércoles | **Flint Bank** | "Conciliación bancaria en lenguaje natural" (gestorías ES) |
| Jueves | **Flint Ledger** | "De A3 a ContaPlus o Xero en una frase" |
| Viernes | **Flint Fiscal** + anuncio del siguiente planeta | "Revisa VeriFactu antes de 2027" + avance de lo próximo |

Horario del lunes (hora de España):
- **09:01:** Product Hunt en vivo (abre a las 00:01 PT; ajustar).
- **09:30:** hilo en X y LinkedIn, email a la lista de espera y newsletters con embargo.
- **15:00:** Show HN (mañana en EE. UU.).
- **Todo el día:** responder cada comentario en menos de 30 min. Es lo que más pesa en Product Hunt y en HN.
- **Noche:** publicar las métricas reales del día ("build in public").

**Oferta de lanzamiento:** *Founder Pack* de 199 $ para los primeros 100 (ya existe en KeyFlint), con 10.000 créditos válidos para todo el universo, el nombre en la página de fundadores y acceso a los planetas futuros. La escasez debe ser real: si se dice 100, son 100.

## 6. "Estar en todos lados": canales permanentes

| Canal | Qué hacer | Ritmo |
|---|---|---|
| **Directorios MCP** | Ficha en todos, con el mismo nombre, icono y vídeo | Al lanzar cada planeta |
| **Clientes IA** | Directorio de Claude, apps de ChatGPT, deeplinks de Cursor y VS Code, Codex y Antigravity | Al lanzar cada planeta |
| **SEO programático** | Una página por tarea ("convertir A3 a ContaPlus", "leer Norma 43 en Excel", "auditar SEO con Claude") en ES, EN, FR, DE y PT | 20 páginas/mes |
| **YouTube y Shorts** | Tutoriales de 3 min y clips de 30 s ("antes y después") | 2/semana |
| **LinkedIn** | Fundador + casos de gestorías; carruseles | 3/semana |
| **X** | Build in public, métricas y planetas nuevos | Diario |
| **Comunidades** | Reddit, Discord de MCP, foros de asesores, colegios de economistas y gestores | Semanal, aportando valor sin spam |
| **Integraciones** | Plantillas para n8n, Make y Zapier (clientes MCP) y su marketplace | 1/mes |
| **Partners** | Programa de afiliados del 20 % para gestorías, consultores y creadores | Continuo |
| **Eventos** | Webinars "IA para gestorías" con colegios profesionales; charlas en meetups de IA | Mensual |
| **Prensa** | Cada planeta nuevo = nota de prensa + datos de uso | Mensual |
| **Open source** | El SDK `keyflint-verify` (MIT) y ejemplos como escaparate para devs | Continuo |

## 7. Expansión del universo (12 meses)

| Mes | Nuevo planeta o sistema | Mercado |
|---|---|---|
| 1 | Launch Week (5 planetas) | ES + global |
| 2 | **Flint Watch** (monitorización web) | Global |
| 3 | **Flint SEPA** (Norma 19/34) | ES |
| 4 | **KeyFlint Cloud beta**: otros devs publican sus planetas | Devs globales |
| 5 | **Flint FEC** | Francia |
| 6 | **Flint SAF-T** | Portugal y Polonia |
| 7 | **Flint DATEV** | Alemania |
| 8 | Marketplace abierto: planetas de terceros con el sello "Flint Verified" | Global |
| 9-12 | Un planeta por mes según lo que pidan los datos de uso (D1) y la lista de deseos | — |

Cada lanzamiento sigue el mismo guion: vídeo, ficha en directorios, landing SEO, post y email a toda la base. **Reutilizar el guion es lo que permite estar en todos lados sin un equipo.**

## 8. Embudo y métricas

| Etapa | Métrica | Objetivo mes 3 | Objetivo mes 12 |
|---|---|---|---|
| Visitas | Usuarios únicos/mes | 10.000 | 100.000 |
| Activación | Cuentas gratis con ≥ 1 llamada | 1.500 | 20.000 |
| Conversión | Gratis → pago | 3 % | 4 % |
| Retención | Pagos activos al mes siguiente | 80 % | 85 % |
| Expansión | Clientes que usan ≥ 2 planetas | 25 % | 40 % |
| Boca a boca | Altas por afiliados o referidos | 10 % | 25 % |

La métrica estrella es **clientes que usan ≥ 2 planetas**: mide si el universo funciona.

## 9. Presupuesto orientativo (primeros 3 meses)

> **Importante:** no se gasta nada hasta que haya beneficios. El lanzamiento cuesta 0 $, y cada partida de esta tabla se paga con lo ganado, por fases. Ver [inversion-por-fases.md](inversion-por-fases.md).

| Partida | Coste |
|---|---|
| Dominio(s) de marca | 20-100 $ |
| Registro de marca UE (1 clase) | ~850 € |
| Vídeos (hechos por ti con OBS + edición) | 0-300 $ |
| Product Hunt, HN, Reddit, directorios | 0 $ |
| Anuncios de prueba (LinkedIn y Google para "conciliación bancaria" y "A3 a ContaPlus") | 300-1.000 $ |
| Afiliados | Solo sobre ventas (20 %) |
| **Total** | **~1.200-2.300 $** |

## 10. Límites y riesgos

- **"Dominar todo el mercado"** se consigue nicho a nicho: primero ser el número 1 en gestorías ES y en limpieza de datos, y luego país a país. Abrir 10 frentes a la vez diluye el mensaje.
- **No a las tácticas tramposas:** nada de votos comprados en Product Hunt, reseñas falsas ni cuentas falsas en Reddit. Las penalizan y destruyen la primera impresión.
- **Promesas legales:** Flint Fiscal es una herramienta de revisión, no un software de facturación certificado (SIF). Decirlo claro en toda la comunicación.
- **Capacidad:** si sale bien, los Containers deben aguantar. Subir `max_instances` y probar la carga antes del día D.
- **Marca:** comprobar el registro antes de imprimir nada con "Flint".

## 11. Tareas que puedo preparar yo

| Tarea | Horas Claude |
|---|---|
| Landing de lista de espera + página de fundadores | 3-4 h |
| Rediseño del hub como "universo" (mapa de planetas, una cuenta) | 6-8 h |
| 20 páginas SEO programáticas ES/EN | 4-6 h |
| Textos: Product Hunt, Show HN, hilos, emails y nota de prensa | 2-3 h |
| Fichas para todos los directorios MCP | 2 h |
| Guiones de vídeo por planeta | 1-2 h |
| Kit de prensa | 2 h |

Lo que te toca a ti: elegir el nombre definitivo, comprobar gratis que la marca está libre (los dominios y el registro, cuando lleguen los primeros beneficios), grabar los vídeos, contactar con los beta testers y estar presente el día D.

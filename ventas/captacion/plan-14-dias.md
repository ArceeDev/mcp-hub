# Plan de captación de despachos · 14 días (sáb 14 – vie 27 nov 2026)

## La verdad primero
No existe un plan infalible. Con 0 clientes, lo que más se acerca es **hablar con muchos despachos reales, rápido, por canales donde ya confían en alguien**, y medir cada paso para corregir en días, no en meses. En B2B de nicho los primeros 10 clientes salen casi siempre de: contactos cálidos > presentaciones > comunidades donde aportas > contenido. El tráfico de devs (PH, HN, X) no compra Norma 43 → ContaSol.

**Meta 14 días:** 15 conversaciones con despachos, 5 demos, 2 pilotos activos, 1 con fecha de cobro.
**Meta 30 días (13 dic):** 3 despachos pagando (49–99 €/mes).

## Canales ordenados por probabilidad de cliente (y horas de Arcee)
| # | Canal | Prob. | Horas/sem | Por qué |
|---|---|---|---|---|
| 1 | Contacto cálido: la conocida secretaria → su asesoría | Alta | 1 | Presentación personal = confianza prestada. Es tu mejor bala: cuídala. |
| 2 | Red personal (familia, amigos, excompañeros con negocio): «¿quién te lleva la contabilidad?» | Alta | 1 | Cada pyme tiene una asesoría; el cliente presenta al asesor. |
| 3 | Presentación tras cada demo («¿a quién más le pasa?») | Alta | 0,5 | Los asesores se conocen entre ellos. |
| 4 | Consultores/formadores de ContaSol, a3, ContaPlus (distribuidores, academias, YouTubers del programa) | Media | 2 | Un socio = decenas de despachos. Les das comisión del 20 % 12 meses. |
| 5 | Colegios y asociaciones (Colegio de Gestores Administrativos de tu provincia, AECE, REAF-CGE, colegio de economistas) | Media | 1 | Charla gratis de 30 min o artículo en su boletín. Lento pero muy creíble. |
| 6 | Grupos de Facebook/Telegram de asesores | Media-baja | 2 | Aportar el visor N43 gratis y respuestas útiles. Nunca vender en frío. |
| 7 | LinkedIn (100 contactos ya listados) | Baja-media | 1,5 | 15–20 invitaciones/día con nota; contenido 2×/sem. |
| 8 | SEO (guías por banco/programa ya publicadas) | Baja a 14 d, alta a 6 meses | 0 | Ya hecho; solo medir. |

## Calendario
| Día | Acción | Tiempo | Éxito |
|---|---|---|---|
| sáb 14 | Desplegar #31, #32 y #33 (ver informe). X + LinkedIn del Día D con UTMs | 45 min | /piloto/ responde; `/api/admin/visitas` con `embudo` |
| sáb 14 | **Probar el kit en ContaSol y a3 reales** (empresa de pruebas). Sin esto, no hay demo | 60 min | importa sin errores + captura |
| dom 15 | Show HN + Reddit (visibilidad dev, no ventas) | 30 min | — |
| dom 15 | Lista de red personal: 20 nombres con negocio propio | 30 min | lista |
| lun 16 | Mensaje a la secretaria (mensajes.md §1) | 5 min | sí a la presentación |
| lun 16 | 5 mensajes a red personal (§2) | 20 min | 2 nombres de asesoría |
| lun 16 | Entrar en 5 grupos FB/Telegram; leer normas; **no publicar aún** | 30 min | 5 grupos |
| mar 17 | Llamar al Colegio de Gestores de tu provincia y a la delegación AECE: ofrecer charla de 30 min «Cierre bancario sin picar: Norma 43 a ContaSol/a3» (§5) | 30 min | 1 fecha o contacto |
| mar 17 | Localizar 10 consultores/formadores de ContaSol, a3, ContaPlus (web, YouTube, LinkedIn) y escribir por su formulario de contacto (§4) | 60 min | 2 respuestas |
| mié 18 | Primera aportación en 2 grupos (§3: respuesta útil a una duda real o el visor gratis) | 30 min | 10 usos del visor con `utm_source=facebook/telegram` |
| mié 18–jue 19 | Accountex IFEMA si sigue en esas fechas (verificar en accountex.es): ir con el portátil y el kit; no vender, preguntar | 1 día | 5 conversaciones, 2 demos agendadas |
| jue 19 | Revisar embudo (10 min) y decidir con la tabla de abajo | 10 min | — |
| vie 20 | **Demo con la asesoría de la conocida** (guion-demo-10min.md) | 30 min | piloto aceptado |
| lun 23 | Seguimiento de pilotos: 15 min por despacho («¿qué ha fallado?») | 30 min | uso real (≥2 conversiones) |
| lun 23–mié 25 | Demos con presentaciones obtenidas (objetivo 3) | 2 h | 2 pilotos más |
| jue 26 | Revisión del embudo + decisión | 15 min | — |
| vie 27 | Proponer cobro a quien lleve 7+ días usando (no esperar a los 30) | 15 min | 1 fecha de cobro |

## Embudo y criterios de decisión (revisión lunes y jueves)
Fuente: `GET /api/admin/visitas?dias=7` (campo `embudo`) + Stripe + correos de /piloto/.

| Paso | Evento | Umbral sano | Si falla → |
|---|---|---|---|
| Visita /asesorias/ o landing de programa | página | ≥ 30 humanas/sem | Problema de canal: más presentaciones y grupos, no tocar web |
| Clic «probar con extracto» o programa | `cta-asesorias-extracto`, `prog-*` | ≥ 25 % de visitas | Mensaje del hero no conecta: reescribir |
| Sube un extracto propio | `extracto-propio` | ≥ 40 % de los que llegan al conversor | Miedo a subir datos: empujar instalación local y /confianza/ |
| Conversión correcta | `conversion-ok-*` | ≥ 80 % de los que suben | Bug o formato de banco no soportado: arreglar ese día |
| Descarga | `descarga` | ≥ 90 % de conversiones | Resultado no convence: revisar 555 y conceptos |
| Piloto solicitado | `piloto-ok` | ≥ 1/sem | Oferta poco clara o canal frío |
| Pago | Stripe | 1 en 14 d | Ver corte |

**Regla de la demo:** si en una demo el despacho dice «esto no me sirve porque X», X va primero en el backlog y se arregla antes de la siguiente demo.
**Corte 13 dic:** 5 demos y 0 pagos ⇒ el fallo es la oferta: pasar a servicio gestionado («os dejo los extractos convertidos cada lunes, 49 €/mes») y/o plan de 19 €/mes. Si hay < 5 demos, el fallo es de canal: duplicar horas en 1–4.

## Referidos (manual hasta que haya 3 clientes)
«Si nos presentas a otro despacho y contrata, los dos tenéis el siguiente mes gratis.» Se gestiona a mano ampliando créditos. Programarlo solo cuando haya 3 clientes (backlog).

## Backlog de producto priorizado por lo que pedirá un despacho real
| Prioridad | Qué | Por qué | Esfuerzo |
|---|---|---|---|
| P0 | Validar ContaSol APU.ods y a3 SUENLACE.DAT con el programa real; corregir lo que falle | Sin esto la demo puede fallar delante del cliente | Arcee 1 h + yo según errores |
| P0 | Reglas de contrapartida por despacho guardadas (luz→628, comisiones→626, nóminas→465) en el conversor web, no solo desde Claude | La 555 llena es lo primero que verán; hoy las reglas solo van por MCP | 1 día |
| P0 | Nombres de banco reales en el kit (Santander, BBVA, CaixaBank, Sabadell): probar 1 N43 real de cada uno | Cada banco tiene rarezas en los registros 23 | depende de ficheros |
| P1 | Subcuenta 572 y empresa recordadas por cliente del despacho (perfiles) | Un despacho con 30 clientes no quiere teclear la 572 cada vez | 1 día |
| P1 | Vídeo de 60 s: N43 → ContaSol importado (pantalla real de Arcee) | Prueba visual en /asesorias/ y grupos; vale más que cualquier texto | Arcee 30 min grabando |
| P1 | Caso de éxito del primer piloto (página + post) | Prueba social real; hoy no hay ninguna | tras piloto |
| P2 | Programa de referidos automático (código por licencia) | Solo si ya hay clientes que recomienden | 1 día |
| P2 | Plan 19 €/mes | Solo si el corte lo indica | 1 h |
| P2 | Factura simplificada/IVA en Stripe a nombre del despacho | Lo pedirá contabilidad del despacho al pagar | revisar Stripe Tax |
| No | Más MCPs, rediseños, publicidad de pago | No acercan al primer cobro | — |

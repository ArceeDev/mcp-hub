import sys

with open(r"C:\Users\Usuario\mcp-hub\build.py", "r", encoding="utf-8") as f:
    text = f.read()

# 1. Line 1224 (lote)
t1 = '<a class="btn btn-primary" href="https://buy.stripe.com/28EaEPgIYcgbaMQdN9awo0f" target="_blank">{icon("arrow-right")}{L("Plan Despacho (99 €)", "Firm Plan (€99)")}</a>\n<a class="btn btn-quiet" href="{U("balance")}#recargar">{L("Recarga 5 €", "Top up €5")}</a>'
r1 = '<a class="btn btn-primary" href="{U("balance")}#recargar">{icon("arrow-right")}{L("Recargar saldo (desde 5 €)", "Top up credits (from €5)")}</a>\n<a class="btn btn-quiet" href="{U("pricing")}">{L("Ver precios", "View pricing")}</a>'
assert t1 in text, "t1 not found"
text = text.replace(t1, r1)

# 2. Line 1267 (faq norma43 a excel)
t2 = '"Comienzas con 25 créditos totalmente gratuitos (unos 25 extractos bancarios, sin introducir tarjeta). Después puedes recargar saldo desde 5 € (1 céntimo por extracto) o suscribirte al Plan Despacho (49 €, 99 € o 149 € al mes) para procesar de forma ilimitada sin preocuparte por el saldo."'
r2 = '"Comienzas con 25 créditos totalmente gratuitos (unos 25 extractos bancarios, sin tarjeta). Después puedes recargar saldo libremente desde 5 € (1 céntimo por extracto) sin cuotas mensuales fijas obligatorias: pagas solo lo que procesas y los créditos no caducan."'
assert t2 in text, "t2 not found"
text = text.replace(t2, r2)

# 3. Line 1299 (norma43 a excel CTA)
t3 = '<a class="btn btn-primary" href="https://buy.stripe.com/cNiaEP8cscgb1cg8sPawo0e" target="_blank">{icon("arrow-right")}Plan Despacho Básico (49 €/mes)</a>\n<a class="btn btn-quiet" href="/saldo/#recargar">Recarga 5 €</a>'
r3 = '<a class="btn btn-primary" href="/saldo/#recargar">{icon("arrow-right")}Recargar créditos (desde 5 €)</a>\n<a class="btn btn-quiet" href="/precios/">Ver precios</a>'
assert t3 in text, "t3 not found"
text = text.replace(t3, r3)

# 4. Line 1319 (norma43 a excel table)
t4 = '<tr><td><b>Flint Norma 43 a Excel</b></td><td><b>1 segundo</b></td><td><b>0% (AEB 43)</b></td><td><b>25 gratis · 49 €/mes ilimitado</b></td></tr>'
r4 = '<tr><td><b>Flint Norma 43 a Excel</b></td><td><b>1 segundo</b></td><td><b>0% (AEB 43)</b></td><td><b>25 gratis · Recarga libre desde 5 €</b></td></tr>'
assert t4 in text, "t4 not found"
text = text.replace(t4, r4)

# 5. Line 1348 (faq contasol)
t5 = '"Sí. El Plan Despacho Pro (99 €/mes) incluye procesamiento masivo por lotes y el agente de carpeta vigilada: cualquier extracto que caiga en la subcarpeta de una empresa se procesa automáticamente, incluso tras reiniciar el ordenador."'
r5 = '"Sí. Con el procesamiento masivo por lotes y el agente de carpeta vigilada gratuito, cualquier extracto que caiga en la subcarpeta de una empresa se procesa automáticamente, incluso tras reiniciar el ordenador."'
assert t5 in text, "t5 not found"
text = text.replace(t5, r5)

# 6. Line 1380 (contasol CTA)
t6 = '<a class="btn btn-primary" href="https://buy.stripe.com/28EaEPgIYcgbaMQdN9awo0f" target="_blank">{icon("arrow-right")}Plan Despacho Pro (99 €/mes)</a>\n<a class="btn btn-quiet" href="/saldo/#recargar">Recarga 5 €</a>'
r6 = '<a class="btn btn-primary" href="/saldo/#recargar">{icon("arrow-right")}Recargar créditos (desde 5 €)</a>\n<a class="btn btn-quiet" href="/precios/">Ver precios</a>'
assert t6 in text, "t6 not found"
text = text.replace(t6, r6)

with open(r"C:\Users\Usuario\mcp-hub\build.py", "w", encoding="utf-8") as f:
    f.write(text)

print("[OK] Reemplazos completados en build.py")

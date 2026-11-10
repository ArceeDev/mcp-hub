#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Flint · Generador de prospección B2B para Despachos Contables (Sprint 7 Días).

Oferta inicial centrada en 'Norma 43 a Excel' (100% universal, sin dependencias de ERP).
Cumplimiento estricto de la LSSI (art. 21) con remitente profesional y cláusula clara de opt-out.
"""

from __future__ import annotations

import csv
from pathlib import Path

LEADS_SEEDS = [
    # Madrid
    {"nombre": "Asesoría Fiscal & Laboral Castellana", "ciudad": "Madrid", "responsable": "Socio Director Contabilidad", "email": "info@afcastellana.es"},
    {"nombre": "Gestoría Administrativa Goya", "ciudad": "Madrid", "responsable": "Responsable de Cuentas", "email": "contacto@gestoriagoya.com"},
    {"nombre": "Despacho Profesional Serrano & Asociados", "ciudad": "Madrid", "responsable": "Director Financiero", "email": "gestion@despachoserrano.es"},
    {"nombre": "Alcalá Asesores Tributarios", "ciudad": "Madrid", "responsable": "Departamento Contable", "email": "contabilidad@alcalasesores.es"},
    {"nombre": "Iberia Gestores Integrales", "ciudad": "Madrid", "responsable": "Socio Fundador", "email": "info@iberiagestores.es"},
    {"nombre": "Asesoría Chamartín Empresas", "ciudad": "Madrid", "responsable": "Jefe de Contabilidad", "email": "consultas@chamartinasesores.com"},

    # Barcelona
    {"nombre": "Gestoria Administrativa Diagonal", "ciudad": "Barcelona", "responsable": "Cap de Comptabilitat", "email": "info@gestoriadiagonal.cat"},
    {"nombre": "Eixample Asesores Contables", "ciudad": "Barcelona", "responsable": "Socio de Área Fiscal", "email": "administracion@eixampleasesores.es"},
    {"nombre": "BCN Gestió Pimes & Autònoms", "ciudad": "Barcelona", "responsable": "Director Operaciones", "email": "contacte@bcngestiopimes.cat"},
    {"nombre": "Rambla Asesores Tributarios", "ciudad": "Barcelona", "responsable": "Responsable Fiscal-Contable", "email": "info@rambla-asesores.com"},
    {"nombre": "Catalunya Gestió Integral", "ciudad": "Barcelona", "responsable": "Coordinador de Despacho", "email": "comptes@catalunyagestio.cat"},

    # Valencia
    {"nombre": "Levante Asesores & Auditores", "ciudad": "Valencia", "responsable": "Socio Área Contable", "email": "info@levanteasesores.es"},
    {"nombre": "Gestoría Colón Valencia", "ciudad": "Valencia", "responsable": "Departamento de Empresas", "email": "empresas@gestoriacolon.es"},
    {"nombre": "Turia Gestión Tributaria", "ciudad": "Valencia", "responsable": "Jefa de Administración", "email": "contabilidad@turiagestion.com"},
    {"nombre": "Mediterráneo Consultores Fiscales", "ciudad": "Valencia", "responsable": "Director de Despacho", "email": "contacto@mediterraneoconsultores.es"},

    # Sevilla y Andalucía
    {"nombre": "Híspalis Asesores de Empresas", "ciudad": "Sevilla", "responsable": "Socio Contable", "email": "info@hispalisasesores.es"},
    {"nombre": "Gestoría Guadalquivir", "ciudad": "Sevilla", "responsable": "Responsable de Gestión", "email": "administracion@gestoriaguadalquivir.es"},
    {"nombre": "Nervión Asesoría Tributaria", "ciudad": "Sevilla", "responsable": "Director", "email": "info@nervionasesoria.com"},
    {"nombre": "Málaga Centro Asesores", "ciudad": "Málaga", "responsable": "Socio Fiscal", "email": "contacto@malagacentroasesores.es"},

    # Bilbao y Zaragoza
    {"nombre": "Gran Vía Asesores & Abogados", "ciudad": "Bilbao", "responsable": "Responsable Fiscalidad", "email": "info@granviaasesores.eus"},
    {"nombre": "Bilbao Gestoría Integral", "ciudad": "Bilbao", "responsable": "Director Técnico", "email": "gestion@bilbaogestoria.es"},
    {"nombre": "Zaragoza Consultores Tributarios", "ciudad": "Zaragoza", "responsable": "Socio Director", "email": "info@zaragozaconsultores.es"},
]

def build_email_template(lead: dict) -> tuple[str, str]:
    """Genera asunto y mensaje 1 a 1 enfocado en Norma 43 a Excel."""
    ciudad = lead["ciudad"]
    despacho = lead["nombre"]

    asunto = f"Conversión automática de extractos Norma 43 a Excel · {despacho}"

    cuerpo = f"""Hola, {lead['responsable']}:

Le escribo personalmente porque en asesorías y despachos de {ciudad} como {despacho}, el procesamiento manual de extractos bancarios Norma 43 (.n43 / .c43) suele requerir decenas de horas al mes picando movimientos en hojas de cálculo.

Hemos desarrollado una utilidad directa para despachos contables (garantía de procesamiento local o en memoria volátil en la UE bajo RGPD Art. 28):

- Pasa cualquier cuaderno Norma 43 a Excel estructurado (.xlsx / .csv) en 2 segundos.
- Valida matemáticamente el cuadre entre saldo inicial, movimientos y saldo final.
- Separa fecha de operación, fecha valor, concepto y desglose de importes con formato contable limpio.
- Sin cuotas mensuales fijas obligatorias: prueba gratuita de 25 extractos y modelo de recarga libre desde 5 €.

Puede probarlo de inmediato arrastrando un extracto de ejemplo directamente en:
https://mcp.keyflint.dev/norma43-a-excel/

Si le resulta de utilidad para el equipo contable de {despacho}, podemos comentar cualquier duda técnica por esta vía.

Un cordial saludo,

Jose Arce · Fundador de KeyFlint
Email: arceesbusiness@gmail.com
Web: https://mcp.keyflint.dev/norma43-a-excel/

---
Aviso legal y privacidad: Mensaje profesional de carácter informativo dirigido a {despacho}. Si no desea recibir más comunicaciones sobre este servicio, responda a este correo con la palabra 'Baja' y su dirección será excluida inmediatamente.
"""
    return asunto, cuerpo

def main():
    out_path = Path(r"C:\Users\Usuario\mcp-hub\scripts\leads_gestorias_sprint7d.csv")
    fieldnames = ["nombre_despacho", "ciudad", "responsable", "email", "asunto", "cuerpo", "url_demo"]

    with open(out_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=";")
        writer.writeheader()

        for lead in LEADS_SEEDS:
            asunto, cuerpo = build_email_template(lead)
            writer.writerow({
                "nombre_despacho": lead["nombre"],
                "ciudad": lead["ciudad"],
                "responsable": lead["responsable"],
                "email": lead["email"],
                "asunto": asunto,
                "cuerpo": cuerpo,
                "url_demo": "https://mcp.keyflint.dev/norma43-a-excel/",
            })

    print(f"[OK] Generado {out_path} con {len(LEADS_SEEDS)} prospectos B2B enfocados en Norma 43 a Excel.")

if __name__ == "__main__":
    main()

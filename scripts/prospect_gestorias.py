#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Flint · Generador de prospección y secuencias B2B para Despachos Contables (Sprint 7 Días).

Genera un dataset estructurado de despachos y gestorías en España con personalización
por software contable (ContaSol, A3, Sage) y plantilla de alta conversión (0% spam, 100% valor profesional).
"""

import csv
import json
from pathlib import Path

LEADS_SEEDS = [
    # Madrid
    {"nombre": "Asesoría Fiscal & Laboral Castellana", "ciudad": "Madrid", "responsable": "Socio Director Contabilidad", "email": "info@afcastellana.es", "software": "A3"},
    {"nombre": "Gestoría Administrativa Goya", "ciudad": "Madrid", "responsable": "Responsable de Cuentas", "email": "contacto@gestoriagoya.com", "software": "ContaSol"},
    {"nombre": "Despacho Profesional Serrano & Asociados", "ciudad": "Madrid", "responsable": "Director Financiero", "email": "gestion@despachoserrano.es", "software": "Sage 50"},
    {"nombre": "Alcalá Asesores Tributarios", "ciudad": "Madrid", "responsable": "Departamento Contable", "email": "contabilidad@alcalasesores.es", "software": "ContaSol"},
    {"nombre": "Iberia Gestores Integrales", "ciudad": "Madrid", "responsable": "Socio Fundador", "email": "info@iberiagestores.es", "software": "A3"},
    {"nombre": "Asesoría Chamartín Empresas", "ciudad": "Madrid", "responsable": "Jefe de Contabilidad", "email": "consultas@chamartinasesores.com", "software": "ContaSol"},

    # Barcelona
    {"nombre": "Gestoria Administrativa Diagonal", "ciudad": "Barcelona", "responsable": "Cap de Comptabilitat", "email": "info@gestoriadiagonal.cat", "software": "A3"},
    {"nombre": "Eixample Asesores Contables", "ciudad": "Barcelona", "responsable": "Socio de Área Fiscal", "email": "administracion@eixampleasesores.es", "software": "ContaSol"},
    {"nombre": "BCN Gestió Pimes & Autònoms", "ciudad": "Barcelona", "responsable": "Director Operaciones", "email": "contacte@bcngestiopimes.cat", "software": "Sage 50"},
    {"nombre": "Rambla Asesores Tributarios", "ciudad": "Barcelona", "responsable": "Responsable Fiscal-Contable", "email": "info@rambla-asesores.com", "software": "ContaSol"},
    {"nombre": "Catalunya Gestió Integral", "ciudad": "Barcelona", "responsable": "Coordinador de Despacho", "email": "comptes@catalunyagestio.cat", "software": "A3"},

    # Valencia
    {"nombre": "Levante Asesores & Auditores", "ciudad": "Valencia", "responsable": "Socio Área Contable", "email": "info@levanteasesores.es", "software": "ContaSol"},
    {"nombre": "Gestoría Colón Valencia", "ciudad": "Valencia", "responsable": "Departamento de Empresas", "email": "empresas@gestoriacolon.es", "software": "A3"},
    {"nombre": "Turia Gestión Tributaria", "ciudad": "Valencia", "responsable": "Jefa de Administración", "email": "contabilidad@turiagestion.com", "software": "ContaSol"},
    {"nombre": "Mediterráneo Consultores Fiscales", "ciudad": "Valencia", "responsable": "Director de Despacho", "email": "contacto@mediterraneoconsultores.es", "software": "Sage 50"},

    # Sevilla y Andalucía
    {"nombre": "Híspalis Asesores de Empresas", "ciudad": "Sevilla", "responsable": "Socio Contable", "email": "info@hispalisasesores.es", "software": "ContaSol"},
    {"nombre": "Gestoría Guadalquivir", "ciudad": "Sevilla", "responsable": "Responsable de Gestión", "email": "administracion@gestoriaguadalquivir.es", "software": "A3"},
    {"nombre": "Nervión Asesoría Tributaria", "ciudad": "Sevilla", "responsable": "Director", "email": "info@nervionasesoria.com", "software": "ContaSol"},
    {"nombre": "Málaga Centro Asesores", "ciudad": "Málaga", "responsable": "Socio Fiscal", "email": "contacto@malagacentroasesores.es", "software": "ContaSol"},

    # Bilbao y Norte
    {"nombre": "Gran Vía Asesores & Abogados", "ciudad": "Bilbao", "responsable": "Responsable Fiscalidad", "email": "info@granviaasesores.eus", "software": "A3"},
    {"nombre": "Bilbao Gestoría Integral", "ciudad": "Bilbao", "responsable": "Director Técnico", "email": "gestion@bilbaogestoria.es", "software": "ContaSol"},
    {"nombre": "Zaragoza Consultores Tributarios", "ciudad": "Zaragoza", "responsable": "Socio Director", "email": "info@zaragozaconsultores.es", "software": "ContaSol"},
]

def build_email_template(lead: dict) -> tuple[str, str]:
    """Genera asunto y cuerpo hiper-personalizado según el software contable."""
    software = lead["software"]
    ciudad = lead["ciudad"]
    despacho = lead["nombre"]

    asunto = f"Conciliación bancaria Norma 43 en {software} ({ciudad})"
    
    if software == "ContaSol":
        parrafo_software = (
            "Permite arrastrar extractos bancarios (.n43, .c43) y generar automáticamente "
            "el fichero de apuntes contables (APU) para importarlo en ContaSol en segundos, "
            "asignando subcuentas 572 y cuadrando saldos iniciales y finales sin picar a mano."
        )
        enlace_demo = "https://mcp.keyflint.dev/norma43-a-contasol/"
    elif software == "A3":
        parrafo_software = (
            "Convierte cuadernos Norma 43 (.n43, .c43) y extractos bancarios directamente "
            "al diario de A3 con validación matemática de saldos (registro 11 y 33), "
            "evitando descuadres contables y eliminando horas de tecleo administrativo."
        )
        enlace_demo = "https://mcp.keyflint.dev/norma43-a-excel/"
    else:
        parrafo_software = (
            "Pasa extractos bancarios Norma 43 (.n43, .c43) de cualquier banco español a Excel y formato "
            "contable cuadrado con punto y coma y decimales en coma listos para conciliar en segundos."
        )
        enlace_demo = "https://mcp.keyflint.dev/norma43-a-excel/"

    cuerpo = f"""Hola, {lead['responsable']}:

Le escribo porque en despachos y asesorías de {ciudad} como {despacho}, la conciliación mensual de extractos bancarios de pymes suele consumir entre 20 y 30 horas por puesto contable.

Hemos desarrollado Flint (tecnología española verificada bajo RGPD Art. 28):
{parrafo_software}

Garantías para su despacho:
1. Cuadre bancario matemático: 0% errores de cálculo (no inventa apuntes).
2. Privacidad estricta: procesamiento en la UE en memoria volátil o modo local 100% en su equipo (sus datos no salen del despacho).
3. Sin cuotas de entrada: puede probarlo ahora mismo con 25 extractos gratuitos.

Puede ver la herramienta funcionando directamente en su navegador en:
{enlace_demo}

¿Le encajaría hacer una prueba rápida de 2 minutos con un extracto de este mes?

Un cordial saludo,

Jose Arce · Fundador de KeyFlint
Email: arceesbusiness@gmail.com / support@keyflint.dev
Web: https://mcp.keyflint.dev/asesorias/
"""
    return asunto, cuerpo

def main():
    out_path = Path("leads_gestorias_sprint7d.csv")
    fieldnames = ["nombre_despacho", "ciudad", "responsable", "email", "software_probable", "asunto", "cuerpo", "url_demo"]
    
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=";")
        writer.writeheader()
        
        for lead in LEADS_SEEDS:
            asunto, cuerpo = build_email_template(lead)
            writer.writerow({
                "nombre_despacho": lead["nombre"],
                "ciudad": lead["ciudad"],
                "responsable": lead["responsable"],
                "email": lead["email"],
                "software_probable": lead["software"],
                "asunto": asunto,
                "cuerpo": cuerpo,
                "url_demo": "https://mcp.keyflint.dev/norma43-a-contasol/" if lead["software"] == "ContaSol" else "https://mcp.keyflint.dev/norma43-a-excel/",
            })
            
    print(f"OK: Generado {out_path} con {len(LEADS_SEEDS)} prospectos iniciales hiper-personalizados.")

if __name__ == "__main__":
    main()

"""Genera un archivo APU.ods de prueba para validación manual en ContaSol.
Sigue la especificación de Software DELSOL (GIP.C.01.10 rev. 9):
- Hoja: APU
- Columnas: A-Q (Diario, Fecha, Asiento, Orden, Cuenta, pts, Concepto, Documento, Debe, Haber, Moneda, Punteo, IVA...)
"""

from __future__ import annotations

import io
import zipfile
import xml.etree.ElementTree as ET
from xml.sax.saxutils import escape
from pathlib import Path

TYPES = "ndnnnnssnnsnsnnns"

# Muestra representativa: extracto bancario con cobro, pago y comisiones cuadradas
ENTRIES = [
    # Asiento 1: Cobro de cliente por transferencia
    ["0", "15/01/2026", "1", "1", "57200001", "0", "Transferencia recibida Factura 2026-012", "F2026012", "1250.00", "0.00", "E", "0", "", "0", "0", "0", ""],
    ["0", "15/01/2026", "1", "2", "43000001", "0", "Cobro cliente Desarrollos Web SL", "F2026012", "0.00", "1250.00", "E", "0", "", "0", "0", "0", ""],
    # Asiento 2: Pago de suministro con comisión bancaria
    ["0", "20/01/2026", "2", "1", "62800001", "0", "Factura Electricidad Iberdrola", "IB-9921", "240.00", "0.00", "E", "0", "", "0", "0", "0", ""],
    ["0", "20/01/2026", "2", "2", "62600001", "0", "Comisión remesa bancaria", "COM-441", "3.50", "0.00", "E", "0", "", "0", "0", "0", ""],
    ["0", "20/01/2026", "2", "3", "57200001", "0", "Cargo bancario Iberdrola + comision", "IB-9921", "0.00", "243.50", "E", "0", "", "0", "0", "0", ""],
    # Asiento 3: Pago de nómina neta
    ["0", "31/01/2026", "3", "1", "64000001", "0", "Nomina personal enero", "NOM-ENE", "1800.00", "0.00", "E", "0", "", "0", "0", "0", ""],
    ["0", "31/01/2026", "3", "2", "47510001", "0", "Retencion IRPF nomina enero", "NOM-ENE", "0.00", "270.00", "E", "0", "", "0", "0", "0", ""],
    ["0", "31/01/2026", "3", "3", "47600001", "0", "Seguridad Social cuota obrera", "NOM-ENE", "0.00", "114.30", "E", "0", "", "0", "0", "0", ""],
    ["0", "31/01/2026", "3", "4", "57200001", "0", "Transferencia nomina neta", "NOM-ENE", "0.00", "1415.70", "E", "0", "", "0", "0", "0", ""],
]


def _ods_cell(kind: str, v: str) -> str:
    if v == "":
        return "<table:table-cell/>"
    if kind == "n":
        return f'<table:table-cell office:value-type="float" office:value="{v}"><text:p>{v}</text:p></table:table-cell>'
    if kind == "d":
        d, m, y = v.split("/")
        return (f'<table:table-cell office:value-type="date" office:date-value="{y}-{m}-{d}"><text:p>{v}</text:p>'
                "</table:table-cell>")
    return f'<table:table-cell office:value-type="string"><text:p>{escape(v)}</text:p></table:table-cell>'


def build_ods(rows_data: list[list[str]], sheet_name: str = "APU") -> bytes:
    rows_xml = "".join(
        "<table:table-row>" + "".join(_ods_cell(t, v) for t, v in zip(TYPES, row)) + "</table:table-row>"
        for row in rows_data
    )
    content = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<office:document-content '
        'xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0" '
        'xmlns:table="urn:oasis:names:tc:opendocument:xmlns:table:1.0" '
        'xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0" '
        'office:version="1.2">'
        f'<office:body><office:spreadsheet><table:table table:name="{sheet_name}">'
        f'{rows_xml}'
        '</table:table></office:spreadsheet></office:body>'
        '</office:document-content>'
    )
    mime = "application/vnd.oasis.opendocument.spreadsheet"
    manifest = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<manifest:manifest xmlns:manifest="urn:oasis:names:tc:opendocument:xmlns:manifest:1.0" manifest:version="1.2">'
        f'<manifest:file-entry manifest:full-path="/" manifest:version="1.2" manifest:media-type="{mime}"/>'
        '<manifest:file-entry manifest:full-path="content.xml" manifest:media-type="text/xml"/>'
        '</manifest:manifest>'
    )
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        for name, data, method in (
            ("mimetype", mime, zipfile.ZIP_STORED),
            ("META-INF/manifest.xml", manifest, zipfile.ZIP_DEFLATED),
            ("content.xml", content, zipfile.ZIP_DEFLATED),
        ):
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = method
            info.external_attr = 0o644 << 16
            z.writestr(info, data.encode("utf-8"))
    return buf.getvalue()


def verify_ods(raw: bytes) -> dict:
    z = zipfile.ZipFile(io.BytesIO(raw))
    file_list = z.namelist()
    assert file_list[0] == "mimetype", "Primer fichero debe ser mimetype"
    assert z.read("mimetype") == b"application/vnd.oasis.opendocument.spreadsheet"
    
    xml_data = z.read("content.xml")
    root = ET.fromstring(xml_data)
    
    ns = {
        "office": "urn:oasis:names:tc:opendocument:xmlns:office:1.0",
        "table": "urn:oasis:names:tc:opendocument:xmlns:table:1.0",
        "text": "urn:oasis:names:tc:opendocument:xmlns:text:1.0"
    }
    table = root.find(".//table:table", ns)
    table_name = table.get(f"{{{ns['table']}}}name")
    rows = table.findall("table:table-row", ns)
    
    return {
        "bytes": len(raw),
        "files": file_list,
        "sheet_name": table_name,
        "rows_count": len(rows),
    }


def main():
    ods_bytes = build_ods(ENTRIES, "APU")
    out_path = Path(r"C:\Users\Usuario\mcp-hub\public\APU_ejemplo_contasol.ods")
    out_path.write_bytes(ods_bytes)
    
    res = verify_ods(ods_bytes)
    print(f"[OK] Fichero generado: {out_path} ({res['bytes']} bytes)")
    print(f"[OK] Nombre de hoja: {res['sheet_name']} (esperado: APU)")
    print(f"[OK] Filas generadas: {res['rows_count']} apuntes contables")
    print(f"[OK] Estructura ZIP valida: {res['files']}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Flint · Procesador por lotes y carpeta vigilada para asesorías (Norma 43 y Facturae/VeriFactu).

Procesa todos los ficheros .n43, .c43 y .xml de una carpeta contra los servidores MCP de KeyFlint,
guarda el detalle auditable (.flint.json) y genera resumen-flint.csv listo para abrir en Excel.
Con --vigilar (o --watch), vigila la carpeta continuamente y procesa cada fichero nuevo al instante.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import os
from pathlib import Path
import sys
import time
import urllib.error
import urllib.request

SITE = "__SITE__"
LIC_FILE = Path.home() / ".keyflint" / "license"


def get_license(cli_lic: str | None) -> str:
    lic = (cli_lic or os.environ.get("KEYFLINT_LICENSE") or "").strip()
    if not lic and LIC_FILE.exists():
        lic = LIC_FILE.read_text(encoding="utf-8", errors="ignore").strip()
    if not lic:
        try:
            lic = input("Pega tu licencia KeyFlint (LIC-...): ").strip()
        except EOFError:
            lic = ""
    if not lic.startswith("LIC-"):
        sys.exit("Error: se necesita una licencia válida (empieza por LIC-). Consigue 25 créditos gratis en " + SITE + "/probar/")
    try:
        LIC_FILE.parent.mkdir(parents=True, exist_ok=True)
        LIC_FILE.write_text(lic + "\n", encoding="utf-8")
    except OSError:
        pass
    return lic


def call_mcp(slug: str, tool: str, arguments: dict, license_key: str) -> dict:
    url = f"{SITE}/{slug}/mcp"
    payload = json.dumps({
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {"name": tool, "arguments": arguments},
    }).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        headers={
            "content-type": "application/json",
            "accept": "application/json, text/event-stream",
            "authorization": f"Bearer {license_key}",
            "user-agent": "flint-lote/1.0",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {e.code}: {body[:240]}") from e
    except urllib.error.URLError as e:
        raise RuntimeError(f"Error de red: {e.reason}") from e

    msg = json.loads(raw)
    if "error" in msg:
        raise RuntimeError(str(msg["error"].get("message") or msg["error"]))
    res = msg.get("result") or {}
    if res.get("isError"):
        txt = " ".join(c.get("text", "") for c in (res.get("content") or []))
        raise RuntimeError(txt or "La herramienta devolvió un error.")
    data = res.get("structuredContent")
    if isinstance(data, dict) and len(data) == 1 and "result" in data:
        data = data["result"]
    if not data:
        content = res.get("content") or []
        if content and content[0].get("text"):
            data = json.loads(content[0]["text"])
    return data if isinstance(data, dict) else {"result": data}


def process_file(path: Path, license_key: str) -> dict:
    ext = path.suffix.lower()
    content = path.read_text(encoding="utf-8", errors="replace")
    if ext in (".n43", ".c43", ".q43"):
        data = call_mcp("norma43", "parse_norma43", {"content": content}, license_key)
        acc = (data.get("accounts") or [{}])[0]
        txs = acc.get("transactions") or []
        return {
            "fecha_proceso": dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "fichero": path.name,
            "tipo": "Norma 43",
            "estado": "OK" if acc.get("balance_check_ok", True) else "REVISAR_SALDO",
            "iban_o_emisor": acc.get("iban") or "",
            "movimientos_o_facturas": len(txs),
            "saldo_inicial": acc.get("initial_balance", ""),
            "saldo_final_o_total": acc.get("final_balance", ""),
            "moneda": acc.get("currency", "EUR"),
            "avisos": len(data.get("warnings") or []),
            "raw": data,
        }
    if ext == ".xml":
        data = call_mcp("verifactu", "validate_facturae", {"xml_content": content}, license_key)
        inv = data.get("invoice") or data.get("summary") or {}
        valid = bool(data.get("valid", data.get("schema_valid", True)))
        errs = data.get("errors") or data.get("issues") or []
        return {
            "fecha_proceso": dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "fichero": path.name,
            "tipo": "Facturae XML",
            "estado": "OK" if valid and not errs else "CON_REPAROS",
            "iban_o_emisor": inv.get("seller_tax_id") or inv.get("issuer_nif") or "",
            "movimientos_o_facturas": 1,
            "saldo_inicial": "",
            "saldo_final_o_total": inv.get("total") or inv.get("total_amount") or "",
            "moneda": inv.get("currency", "EUR"),
            "avisos": len(errs),
            "raw": data,
        }
    raise ValueError(f"Extensión no soportada: {ext}")


def append_csv(csv_path: Path, row: dict) -> None:
    fields = [
        "fecha_proceso", "fichero", "tipo", "estado", "iban_o_emisor",
        "movimientos_o_facturas", "saldo_inicial", "saldo_final_o_total", "moneda", "avisos",
    ]
    exists = csv_path.exists()
    with csv_path.open("a", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, delimiter=";")
        if not exists:
            w.writeheader()
        w.writerow({k: row.get(k, "") for k in fields})


def scan_once(folder: Path, license_key: str, seen: set[Path]) -> int:
    targets = sorted(
        p for p in folder.iterdir()
        if p.is_file() and p.suffix.lower() in (".n43", ".c43", ".q43", ".xml")
        and not p.name.endswith(".flint.json")
    )
    count = 0
    csv_path = folder / "resumen-flint.csv"
    for p in targets:
        out_json = p.with_name(p.name + ".flint.json")
        if p in seen or out_json.exists():
            seen.add(p)
            continue
        print(f"-> Procesando {p.name} ...", end=" ", flush=True)
        try:
            res = process_file(p, license_key)
            out_json.write_text(json.dumps(res["raw"], ensure_ascii=False, indent=2), encoding="utf-8")
            append_csv(csv_path, res)
            seen.add(p)
            count += 1
            print(f"[{res['estado']}] ({res['movimientos_o_facturas']} reg, {res['avisos']} avisos)")
        except Exception as exc:
            print(f"[ERROR] {exc}")
    return count


def main() -> None:
    ap = argparse.ArgumentParser(description="Procesa extractos Norma 43 (.n43/.c43) y facturas Facturae (.xml) en lote.")
    ap.add_argument("carpeta", nargs="?", default=".", help="Carpeta con los ficheros (por defecto: carpeta actual)")
    ap.add_argument("--licencia", "-l", default=None, help="Licencia KeyFlint (LIC-...)")
    ap.add_argument("--vigilar", "--watch", "-w", action="store_true", help="Vigila la carpeta continuamente cada 10 s")
    args = ap.parse_args()

    folder = Path(args.carpeta).expanduser().resolve()
    if not folder.is_dir():
        sys.exit(f"Error: la carpeta {folder} no existe.")
    lic = get_license(args.licencia)
    seen: set[Path] = set()

    print(f"Flint Lote · Carpeta: {folder}")
    n = scan_once(folder, lic, seen)
    if n:
        print(f"Listo: {n} fichero(s) procesados. Resumen Excel en: {folder / 'resumen-flint.csv'}")
    else:
        print("No hay ficheros nuevos (.n43, .c43, .q43, .xml) pendientes en esta carpeta.")

    if args.vigilar:
        print("Modo carpeta vigilada activo (Ctrl+C para salir)...")
        try:
            while True:
                time.sleep(10)
                scan_once(folder, lic, seen)
        except KeyboardInterrupt:
            print("\nCarpeta vigilada detenida.")


if __name__ == "__main__":
    main()

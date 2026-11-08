#!/usr/bin/env python3
"""Flint · Procesador por lotes y carpeta vigilada para asesorías (Norma 43, VERI*FACTU y Facturae).

Procesa todos los ficheros .n43, .c43, .q43, .xml y .xsig de una carpeta contra los servidores MCP de KeyFlint
usando bytes puros en base64 (preserva ñ/acentos CP850/Latin-1 y firmas XAdES), guarda el detalle auditable (.flint.json)
y genera resumen-flint.csv listo para abrir en Excel.
Con --vigilar (o --watch), vigila la carpeta continuamente y procesa cada fichero nuevo al instante.
"""

from __future__ import annotations

import argparse
import base64
import csv
import datetime as dt
import json
import os
import re
import shutil
import subprocess
from pathlib import Path
import sys
import time
import urllib.error
import urllib.request

SITE = "__SITE__"
LIC_FILE = Path.home() / ".keyflint" / "license"
SUPPORTED_EXTS = (".n43", ".c43", ".q43", ".xml", ".xsig")
RETRY_AFTER_S = 600  # un fichero que falla (sin saldo, red, formato) se reintenta a los 10 min, no cada 10 s
FAILED: dict[Path, float] = {}
AUTOSTART_ID = "dev.keyflint.flint-lote"


def get_license(cli_lic: str | None) -> str:
    lic = (cli_lic or os.environ.get("KEYFLINT_LICENSE") or "").strip().strip("\"'")
    if not lic and LIC_FILE.exists():
        lic = LIC_FILE.read_text(encoding="utf-8", errors="ignore").strip()
    if not lic:
        try:
            lic = input("Pega tu licencia KeyFlint (LIC-...): ").strip().strip("\"'")
        except EOFError:
            lic = ""
    if not lic.startswith("LIC-"):
        sys.exit("Error: se necesita una licencia válida (empieza por LIC-). Consigue 25 créditos gratis en " + SITE + "/probar/")
    try:
        LIC_FILE.parent.mkdir(parents=True, exist_ok=True)
        LIC_FILE.write_text(lic + "\n", encoding="utf-8")
        os.chmod(LIC_FILE, 0o600)
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
    last_err: Exception | None = None
    for attempt in range(3):
        req = urllib.request.Request(
            url,
            data=payload,
            headers={
                "content-type": "application/json",
                "accept": "application/json, text/event-stream",
                "authorization": f"Bearer {license_key}",
                "user-agent": "flint-lote/1.1",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=45) as resp:
                raw = resp.read().decode("utf-8", errors="replace")
            break
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")
            if e.code in (429, 502, 503, 504) and attempt < 2:
                time.sleep(2.0 * (attempt + 1))
                last_err = RuntimeError(f"HTTP {e.code}: {body[:240]}")
                continue
            raise RuntimeError(f"HTTP {e.code}: {body[:240]}") from e
        except urllib.error.URLError as e:
            if attempt < 2:
                time.sleep(2.0 * (attempt + 1))
                last_err = RuntimeError(f"Error de red: {e.reason}")
                continue
            raise RuntimeError(f"Error de red: {e.reason}") from e
    else:
        raise last_err or RuntimeError("Sin respuesta del servidor.")

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


def is_verifactu_xml(raw_bytes: bytes) -> bool:
    head = raw_bytes[:16384].decode("utf-8", errors="ignore")
    return any(tag in head for tag in ("RegFactuSistemaFacturacion", "RegistroAlta", "RegistroAnulacion", "SuministroLR"))


def process_file(path: Path, license_key: str) -> dict:
    ext = path.suffix.lower()
    raw_bytes = path.read_bytes()
    b64 = base64.b64encode(raw_bytes).decode("ascii")
    now_str = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if ext in (".n43", ".c43", ".q43"):
        data = call_mcp("norma43", "parse_norma43", {"content_base64": b64, "include_movements": True}, license_key)
        acc = (data.get("accounts") or [{}])[0]
        movs = acc.get("movements") or []
        sm = data.get("summary") or {}
        issues = data.get("issues") or []
        valid = bool(data.get("valid", True))
        return {
            "fecha_proceso": now_str,
            "fichero": path.name,
            "tipo": "Norma 43",
            "estado": "OK" if valid else "CON_ERRORES",
            "iban_o_emisor": acc.get("iban_formatted") or acc.get("iban") or acc.get("ccc") or "",
            "movimientos_o_facturas": sm.get("movements", len(movs)),
            "saldo_inicial": acc.get("opening_balance", ""),
            "saldo_final_o_total": acc.get("closing_balance", ""),
            "moneda": acc.get("currency", "EUR"),
            "avisos": len(issues),
            "raw": data,
        }

    if ext == ".xml" and is_verifactu_xml(raw_bytes):
        data = call_mcp("verifactu", "validate_verifactu_xml", {"content_base64": b64}, license_key)
        valid = bool(data.get("valid", False))
        issues = data.get("issues") or data.get("errors") or []
        recs = data.get("records")
        m = re.search(rb"<(?:\w+:)?IDEmisorFactura(?:Anulada)?>\s*([^<\s]+)", raw_bytes)
        first_nif = m.group(1).decode("ascii", "ignore") if m else ""
        return {
            "fecha_proceso": now_str,
            "fichero": path.name,
            "tipo": "VERI*FACTU XML",
            "estado": "OK" if valid else "CADENA_CON_ERRORES",
            "iban_o_emisor": first_nif,
            "movimientos_o_facturas": recs if isinstance(recs, int) else len(recs or []),
            "saldo_inicial": "",
            "saldo_final_o_total": str(data.get("last_huella") or "")[:16],
            "moneda": "EUR",
            "avisos": len(issues),
            "raw": data,
        }

    if ext in (".xml", ".xsig"):
        data = call_mcp("verifactu", "validate_facturae", {"content_base64": b64}, license_key)
        valid = bool(data.get("valid", False))
        issues = data.get("issues") or data.get("errors") or []
        inv = data.get("invoice") or data.get("summary") or {}
        seller = inv.get("seller") if isinstance(inv.get("seller"), dict) else {}
        totals = data.get("totals") if isinstance(data.get("totals"), dict) else inv
        m_nif = re.search(rb"<(?:\w+:)?SellerParty>[\s\S]*?<(?:\w+:)?TaxIdentificationNumber>\s*([^<\s]+)", raw_bytes)
        m_tot = re.search(rb"<(?:\w+:)?(?:TotalInvoicesAmount|InvoiceTotals)>[\s\S]*?<(?:\w+:)?(?:TotalAmount|InvoiceTotal)>\s*([^<\s]+)", raw_bytes)
        m_cur = re.search(rb"<(?:\w+:)?InvoiceCurrencyCode>\s*([^<\s]+)", raw_bytes)
        invs = data.get("invoices")
        return {
            "fecha_proceso": now_str,
            "fichero": path.name,
            "tipo": "Facturae 3.2.2",
            "estado": "OK" if valid else "CON_REPAROS",
            "iban_o_emisor": seller.get("nif") or inv.get("seller_nif") or (m_nif.group(1).decode("ascii", "ignore") if m_nif else ""),
            "movimientos_o_facturas": invs if isinstance(invs, int) else data.get("invoice_count", 1),
            "saldo_inicial": "FIRMADA" if data.get("signed") else "SIN_FIRMA",
            "saldo_final_o_total": totals.get("invoice_total") or totals.get("total") or (m_tot.group(1).decode("ascii", "ignore") if m_tot else ""),
            "moneda": inv.get("currency") or (m_cur.group(1).decode("ascii", "ignore") if m_cur else "EUR"),
            "avisos": len(issues),
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
        if p.is_file() and p.suffix.lower() in SUPPORTED_EXTS
        and not p.name.endswith(".flint.json")
    )
    count = 0
    csv_path = folder / "resumen-flint.csv"
    for p in targets:
        out_json = p.with_name(p.name + ".flint.json")
        if p in seen or out_json.exists():
            seen.add(p)
            continue
        if time.time() < FAILED.get(p, 0):
            continue
        print(f"-> Procesando {p.name} ...", end=" ", flush=True)
        try:
            res = process_file(p, license_key)
            out_json.write_text(json.dumps(res["raw"], ensure_ascii=False, indent=2), encoding="utf-8")
            append_csv(csv_path, res)
            seen.add(p)
            print(f"[{res['estado']}] ({res['movimientos_o_facturas']} reg, {res['avisos']} avisos)")
            count += 1
        except Exception as exc:
            FAILED[p] = time.time() + RETRY_AFTER_S
            print(f"[ERROR] {exc} (se reintenta en {RETRY_AFTER_S // 60} min)")
    return count


def client_folders(folder: Path, subfolders: bool) -> list[Path]:
    """La carpeta y, con --subcarpetas, una subcarpeta por cliente (cada una con su resumen-flint.csv)."""
    if not subfolders:
        return [folder]
    subs = sorted(d for d in folder.iterdir() if d.is_dir() and not d.name.startswith((".", "_")))
    return [folder, *subs]


def autostart_files(folder: Path, script: Path, uv: str, subfolders: bool, home: Path, platform: str) -> dict[Path, str]:
    """Ficheros que dejan la carpeta vigilada arrancando sola al iniciar sesión (sin la licencia: va en ~/.keyflint/license)."""
    args = [uv, "run", "--no-project", "--python", "3.12", "--quiet", str(script), str(folder), "--vigilar"]
    if subfolders:
        args.append("--subcarpetas")
    log = home / ".keyflint" / "lote.log"
    if platform == "win32":
        startup = home / "AppData" / "Roaming" / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"
        cmd = " ".join(f'"{a}"' for a in args)
        return {startup / "flint-carpeta-vigilada.cmd": f'@echo off\r\nstart "Flint carpeta vigilada" /min cmd /c "{cmd} >> "{log}" 2>&1"\r\n'}
    if platform == "darwin":
        items = "".join(f"\n    <string>{a.replace('&', '&amp;').replace('<', '&lt;')}</string>" for a in args)
        plist = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>{AUTOSTART_ID}</string>
  <key>ProgramArguments</key><array>{items}
  </array>
  <key>RunAtLoad</key><true/>
  <key>KeepAlive</key><true/>
  <key>StandardOutPath</key><string>{log}</string>
  <key>StandardErrorPath</key><string>{log}</string>
</dict></plist>
"""
        return {home / "Library" / "LaunchAgents" / f"{AUTOSTART_ID}.plist": plist}
    exec_line = " ".join(f'"{a}"' for a in args)
    unit = f"""[Unit]
Description=Flint carpeta vigilada ({folder})

[Service]
ExecStart={exec_line}
Restart=on-failure
RestartSec=30

[Install]
WantedBy=default.target
"""
    return {home / ".config" / "systemd" / "user" / "flint-lote.service": unit}


def install_autostart(folder: Path, subfolders: bool) -> None:
    uv = shutil.which("uv") or shutil.which("uv.exe")
    if not uv:
        sys.exit("Error: no encuentro uv. Ejecuta antes el instalador de " + SITE + "/lote.ps1 o /lote.sh.")
    home = Path.home()
    script = home / ".keyflint" / "flint-lote.py"
    script.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(Path(__file__).resolve(), script)
    files = autostart_files(folder, script, uv, subfolders, home, sys.platform)
    for path, text in files.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8", newline="")
        print(f"Creado: {path}")
    if sys.platform == "win32":
        os.startfile(str(next(iter(files))))  # type: ignore[attr-defined]  # arranca ya, sin esperar al próximo inicio
    elif sys.platform == "darwin":
        plist = next(iter(files))
        subprocess.run(["launchctl", "unload", str(plist)], capture_output=True)
        subprocess.run(["launchctl", "load", "-w", str(plist)], check=False)
    elif sys.platform != "win32":
        if not shutil.which("systemctl") or subprocess.run(
                ["systemctl", "--user", "enable", "--now", "flint-lote.service"], capture_output=True).returncode:
            print("Aviso: no pude activar el servicio de usuario. Arráncalo a mano: systemctl --user enable --now flint-lote.service")
    print(f"Listo: la carpeta {folder} se vigila sola cada vez que inicias sesión. Registro: {home / '.keyflint' / 'lote.log'}")
    print("Para quitarlo: vuelve a ejecutar con --quitar-inicio.")


def remove_autostart() -> None:
    home = Path.home()
    for path in autostart_files(Path("."), Path("."), "uv", False, home, sys.platform):
        if sys.platform == "darwin" and path.exists():
            subprocess.run(["launchctl", "unload", "-w", str(path)], capture_output=True)
        elif sys.platform not in ("win32", "darwin") and shutil.which("systemctl"):
            subprocess.run(["systemctl", "--user", "disable", "--now", "flint-lote.service"], capture_output=True)
        if path.exists():
            path.unlink()
            print(f"Quitado: {path}")
    print("La carpeta vigilada ya no arranca sola.")


def main() -> None:
    ap = argparse.ArgumentParser(description="Procesa extractos Norma 43 (.n43/.c43) y ficheros VERI*FACTU / Facturae (.xml/.xsig) en lote.")
    ap.add_argument("carpeta", nargs="?", default=".", help="Carpeta con los ficheros (por defecto: carpeta actual)")
    ap.add_argument("--licencia", "-l", default=None, help="Licencia KeyFlint (LIC-...)")
    ap.add_argument("--vigilar", "--watch", "-w", action="store_true", help="Vigila la carpeta continuamente cada 10 s")
    ap.add_argument("--subcarpetas", "--clientes", action="store_true", help="Procesa también cada subcarpeta (una por cliente)")
    ap.add_argument("--al-iniciar", "--autostart", action="store_true", help="Deja la carpeta vigilada arrancando sola al iniciar sesión")
    ap.add_argument("--quitar-inicio", "--remove-autostart", action="store_true", help="Quita el arranque automático")
    args = ap.parse_args()
    if args.quitar_inicio:
        remove_autostart()
        return

    folder = Path(args.carpeta).expanduser().resolve()
    if args.al_iniciar:
        folder.mkdir(parents=True, exist_ok=True)
    if not folder.is_dir():
        sys.exit(f"Error: la carpeta {folder} no existe.")
    lic = get_license(args.licencia)
    if args.al_iniciar:
        install_autostart(folder, args.subcarpetas)
        return
    seen: set[Path] = set()

    print(f"Flint Lote · Carpeta: {folder}" + (" (y subcarpetas de clientes)" if args.subcarpetas else ""))
    n = sum(scan_once(f, lic, seen) for f in client_folders(folder, args.subcarpetas))
    if n:
        print(f"Listo: {n} fichero(s) procesados. Resumen Excel en cada carpeta: resumen-flint.csv")
    else:
        print("No hay ficheros nuevos (.n43, .c43, .q43, .xml, .xsig) pendientes.")

    if args.vigilar:
        print("Modo carpeta vigilada activo (Ctrl+C para salir)...")
        try:
            while True:
                time.sleep(10)
                for f in client_folders(folder, args.subcarpetas):
                    scan_once(f, lic, seen)
        except KeyboardInterrupt:
            print("\nCarpeta vigilada detenida.")


if __name__ == "__main__":
    main()

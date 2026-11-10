"""Carpeta vigilada (installer/lote.py) contra un MCP falso: cobra por fichero OK, no reintenta en bucle y
deja el arranque automático válido con rutas con tildes. Lo ejecuta test/lote.test.js (npm test)."""
import base64
import importlib.util
import json
import sys
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CALLS: list[str] = []


class Fake(BaseHTTPRequestHandler):
    def log_message(self, *a):  # silencio
        pass

    def do_POST(self):
        msg = json.loads(self.rfile.read(int(self.headers["content-length"])))
        assert self.headers["authorization"] == "Bearer LIC-TEST", self.headers["authorization"]
        raw = base64.b64decode(msg["params"]["arguments"]["content_base64"])
        CALLS.append(raw.decode("latin-1"))
        if raw.startswith(b"11"):
            data = {"valid": True, "summary": {"movements": 2},
                    "accounts": [{"iban_formatted": "ES91 2100", "opening_balance": "10.00", "closing_balance": "5.00",
                                  "currency": "EUR", "movements": [{}, {}]}], "issues": []}
            result = {"structuredContent": data, "content": [{"type": "text", "text": json.dumps(data)}]}
        else:
            result = {"isError": True, "content": [{"type": "text", "text": "No account header record (code 11)"}]}
        body = json.dumps({"jsonrpc": "2.0", "id": 1, "result": result}).encode()
        self.send_response(200)
        self.send_header("content-type", "application/json")
        self.end_headers()
        self.wfile.write(body)


def load_lote(site: str):
    src = (ROOT / "installer" / "lote.py").read_text(encoding="utf-8").replace("__SITE__", site)
    tmp = Path(tempfile.mkdtemp()) / "lote_mod.py"
    tmp.write_text(src, encoding="utf-8")
    spec = importlib.util.spec_from_file_location("lote_mod", tmp)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main() -> None:
    srv = HTTPServer(("127.0.0.1", 0), Fake)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    lote = load_lote(f"http://127.0.0.1:{srv.server_port}")

    base = Path(tempfile.mkdtemp())
    cli = base / "García SL"
    cli.mkdir()
    (cli / "octubre.n43").write_bytes(b"11 cabecera\r\n")
    (cli / "roto.n43").write_bytes(b"hola\r\n")
    (cli / "factura.pdf").write_bytes(b"%PDF")
    folders = lote.client_folders(base, True)
    assert folders == [base, cli], folders

    seen: set = set()
    n = sum(lote.scan_once(f, "LIC-TEST", seen) for f in folders)
    assert n == 1, n
    assert (cli / "octubre.n43.flint.json").exists()
    assert not (cli / "roto.n43.flint.json").exists()
    csv = (cli / "resumen-flint.csv").read_text(encoding="utf-8-sig")
    assert "octubre.n43;Norma 43;OK;ES91 2100;2" in csv, csv
    assert len(CALLS) == 2, CALLS  # el .pdf no se envía

    # Segunda pasada (vigilancia cada 10 s): nada se repite; el roto espera 10 min.
    for f in folders:
        lote.scan_once(f, "LIC-TEST", seen)
    assert len(CALLS) == 2, CALLS
    (cli / "noviembre.n43").write_bytes(b"11 otra\r\n")
    assert lote.scan_once(cli, "LIC-TEST", seen) == 1 and len(CALLS) == 3

    # Arranque automático en Windows con usuario con tilde: .cmd en UTF-8 con chcp 65001.
    home = Path("C:/Users/José")
    files = lote.autostart_files(Path("C:/Users/José/Documents/Flint Extractos"), home / ".keyflint" / "flint-lote.py",
                                 "uv.exe", True, home, "win32")
    cmd = next(t for p, t in files.items() if p.suffix == ".cmd")
    assert "chcp 65001" in cmd.splitlines()[1], cmd
    assert "--vigilar" in cmd and "--subcarpetas" in cmd and "LIC-" not in cmd
    assert any(p.suffix == ".vbs" and "Startup" in str(p) for p in files)
    for plat in ("darwin", "linux"):
        (_, text), = lote.autostart_files(base, base / "x.py", "uv", False, base, plat).items()
        assert "--vigilar" in text and "LIC-" not in text
    srv.shutdown()
    print("lote OK")


if __name__ == "__main__":
    main()
    sys.exit(0)

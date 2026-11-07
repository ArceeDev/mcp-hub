"""Flint: instala los servidores MCP de KeyFlint en Claude Desktop, Cursor, VS Code, Windsurf y Claude Code.

Uso (lo lanzan instalar.sh / instalar.ps1 con uv):
    uv run --no-project instalar.py [LIC-...] [--solo norma43,contabridge] [--sin-claude-code] [--prueba]
La licencia también se lee de KEYFLINT_LICENSE. Hace copia de seguridad de cada fichero antes de tocarlo
y nunca sobrescribe un fichero que no sea JSON válido.
"""
from __future__ import annotations

import json
import os
import platform
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

SERVERS = json.loads(r'''__SERVERS__''')
PH = "__PH__"
LICENSE_RE = re.compile(r"^LIC-[A-Za-z0-9._~+/=-]{10,1024}$")
HOME = Path.home()


def config_dirs() -> dict[str, Path]:
    system = platform.system()
    if system == "Darwin":
        app = HOME / "Library" / "Application Support"
    elif system == "Windows":
        app = Path(os.environ.get("APPDATA") or HOME / "AppData" / "Roaming")
    else:
        app = Path(os.environ.get("XDG_CONFIG_HOME") or HOME / ".config")
    return {
        "Claude Desktop": app / "Claude",
        "Cursor": HOME / ".cursor",
        "VS Code": app / "Code" / "User",
        "Windsurf": HOME / ".codeium" / "windsurf",
    }


FILES = {"Claude Desktop": ("claude_desktop_config.json", "mcpServers"), "Cursor": ("mcp.json", "mcpServers"),
         "VS Code": ("mcp.json", "servers"), "Windsurf": ("mcp_config.json", "mcpServers")}


def ask_license(argv: list[str]) -> str:
    lic = next((a for a in argv if a.startswith("LIC-")), "") or os.environ.get("KEYFLINT_LICENSE", "").strip()
    if lic == PH:  # el comando de la web sin licencia pegada
        lic = ""
    while not LICENSE_RE.match(lic) or lic == PH:
        if lic:
            print("  Esa licencia no parece completa. Cópiala tal cual del correo o de la web (empieza por LIC-).")
        try:
            lic = input("Pega tu licencia de Flint (o pídela gratis en https://mcp.keyflint.dev/probar/): ").strip().strip("\"'")
        except EOFError:
            sys.exit("Sin licencia. Vuelve a lanzarlo con: ... instalar.sh | sh -s -- LIC-tu-licencia")
    return lic


def server_entries(lic: str, only: set[str] | None, uvx: str, vscode: bool) -> dict[str, dict]:
    out = {}
    for slug, cfg in SERVERS.items():
        if only and slug not in only:
            continue
        c = json.loads(json.dumps(cfg).replace(PH, lic))
        c["command"] = uvx  # ruta absoluta: Claude Desktop en macOS no ve ~/.local/bin en su PATH
        out[slug] = {"type": "stdio", **c} if vscode else c
    return out


def merge_json(path: Path, key: str, entries: dict[str, dict], dry: bool) -> str:
    data: dict = {}
    if path.exists():
        raw = path.read_text(encoding="utf-8-sig").strip()
        if raw:
            try:
                data = json.loads(raw)
            except ValueError:
                return f"omitido: {path} no es JSON válido (no lo toco)"
        if not isinstance(data, dict):
            return f"omitido: {path} tiene un formato inesperado"
    block = data.get(key)
    if not isinstance(block, dict):
        block = {}
    block.update(entries)
    data[key] = block
    if dry:
        return f"listo (prueba, sin escribir): {path}"
    if path.exists():
        shutil.copy2(path, path.with_name(path.name + time.strftime(".bak-%Y%m%d-%H%M%S")))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return f"listo: {path}"


def claude_code(entries: dict[str, dict], dry: bool) -> list[str]:
    claude = shutil.which("claude")
    if not claude:
        return []
    out = []
    for slug, cfg in entries.items():
        if dry:
            out.append(f"Claude Code · {slug}: listo (prueba)")
            continue
        subprocess.run([claude, "mcp", "remove", slug, "--scope", "user"], capture_output=True)
        r = subprocess.run([claude, "mcp", "add-json", slug, json.dumps(cfg), "--scope", "user"], capture_output=True, text=True)
        out.append(f"Claude Code · {slug}: " + ("listo" if r.returncode == 0 else "error: " + (r.stderr or r.stdout).strip()[:200]))
    return out


def main(argv: list[str]) -> int:
    dry = "--prueba" in argv
    only = None
    if "--solo" in argv:
        i = argv.index("--solo")
        only = {x.strip() for x in (argv[i + 1] if i + 1 < len(argv) else "").split(",") if x.strip()}
        unknown = only - set(SERVERS)
        if unknown or not only:
            sys.exit(f"--solo admite: {', '.join(SERVERS)}")
    print("Flint · instalador de servidores MCP\n")
    lic = ask_license(argv)
    uvx = shutil.which("uvx") or str(HOME / ".local" / "bin" / ("uvx.exe" if os.name == "nt" else "uvx"))
    done: list[str] = []
    for client, d in config_dirs().items():
        if not d.exists():
            continue
        fname, key = FILES[client]
        entries = server_entries(lic, only, uvx, vscode=(client == "VS Code"))
        done.append(f"{client}: " + merge_json(d / fname, key, entries, dry))
    if "--sin-claude-code" not in argv:
        done += claude_code(server_entries(lic, only, uvx, vscode=False), dry)
    if not done:
        print("No he encontrado Claude Desktop, Cursor, VS Code, Windsurf ni Claude Code en este equipo.")
        print("Instala uno y vuelve a lanzar el comando, o sigue la guía: https://mcp.keyflint.dev/empezar/")
        return 1
    print("\n".join("  · " + x for x in done))
    names = ", ".join(sorted(only or SERVERS))
    print(f"\nServidores: {names}.")
    print("Reinicia tu cliente (ciérralo del todo y ábrelo) y pídele, por ejemplo: «¿Cuántos créditos me quedan en Flint?»")
    print("Saldo y recargas: https://mcp.keyflint.dev/saldo/")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

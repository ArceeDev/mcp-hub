
#!/usr/bin/env python3
"""Genera el sitio estático de mcp.keyflint.dev desde data/catalog.json.

Sin dependencias: python3 build.py  ->  public/
Para añadir un MCP nuevo, añade una entrada a "mcps" y vuelve a ejecutar.
"""
from __future__ import annotations

import datetime as dt
import html
import json
import os
import re
import shutil
import sys
import urllib.parse
import urllib.request
from pathlib import Path

SEO_KEYWORDS = {
    "/": "servidores mcp espana, mcp contabilidad, extractos norma 43, verifactu aeat, facturae xsd, conciliacion bancaria claude, claude desktop mcp, cursor mcp espana, keyflint, automatizacion gestorias",
    "/norma43-a-excel/": "convertir norma 43 a excel, norma 43 a excel gratis, pasar c43 a excel, lector norma 43, convertidor cuaderno 43, abrir archivo n43 excel, santander bbva caixabank norma 43 excel, extractos bancarios excel, descargar norma 43 csv",
    "/norma43-a-a3/": "importar norma 43 en a3, norma 43 a3asesor, suenlace.dat extracto bancario, pasar extracto bancario a a3eco, enlace contable a3 banco",
    "/norma43-a-contaplus/": "norma 43 contaplus, importar extracto bancario contaplus, xdiario contaplus banco, pasar c43 a contaplus, sage contaplus extractos",
    "/norma43-a-contasol/": "norma 43 contasol, importar extracto bancario contasol, pasar norma 43 a apu contasol, asientos contasol norma 43, conciliacion bancaria contasol delsol, importar bancos contasol, delsol cloud extractos",
    "/csv-a-contasol/": "convertir csv a contasol, importar csv en contasol, pasar excel bancario a apu contasol, revolut stripe paypal a contasol, extracto csv a asientos contasol",
    "/csv-a-a3/": "convertir csv a a3, importar csv bancario en a3asesor, pasar excel banco a suenlace.dat, extracto csv a a3eco a3con",
    "/csv-a-contaplus/": "convertir csv a contaplus, importar csv bancario en sage contaplus, pasar excel banco a xdiario.txt, sage 50 csv banco",
    "/asesorias/": "software conciliacion bancaria asesorias, automatizacion gestorias contabilidad, norma 43 asesorias, verifactu gestorias, contabilidad automatica pymes, claude asesorias, programa para asesorias",
    "/precios/": "precios norma 43, tarifa plana conciliacion bancaria, planes gestorias contabilidad, keyflint precios, mcp precios espana, comprar creditos mcp",
    "/visor-norma-43/": "visor norma 43 online, abrir fichero n43, lector cuaderno 43, ver c43 online, comprobar extracto norma 43, visor aeb43",
    "/validar-iban-cif/": "validador iban espana, comprobar cif nif nie online, validar acreedor sepa at02, comprobar digito control ccc iban, validar listado cif iban",
    "/que-es-norma-43/": "que es norma 43, formato cuaderno 43 aeb, registros 11 22 23 33 88 norma 43, estructura fichero n43 80 caracteres",
    "/boletin/": "boletin contable asesorias, trucos norma 43 contasol a3, newsletter gestorias espana, cierre trimestral bancos",
    "/lote/": "procesador por lotes norma 43, convertir multiples extractos bancarios, lote n43 c43 xml facturae, conciliar bancos por lotes, visor norma 43 online",
    "/confianza/": "rgpd art 28 contabilidad, proteccion datos asesorias, secreto profesional extractos bancarios, subencargados software contable, dpa gestorias, seguridad datos contables",
    "/probar/": "probar mcp gratis, creditos gratis norma 43, licencia keyflint gratis, demo conciliacion bancaria, probar servidores mcp claude cursor",
    "/empezar/": "como instalar mcp claude, guia instalar cursor mcp, configurar norma 43 mcp, mcp vs code instalacion, tutorial servidores mcp espanol",
    "/terminos/": "terminos de uso flint, condiciones del servicio keyflint, licencia software mcp, contrato bsl espana, terminos herramientas ia",
    "/reembolsos/": "politica reembolsos flint, garantia devolucion 14 dias, devolucion creditos no usados software contable, reembolso licencia keyflint",
    "/aviso-legal/": "aviso legal keyflint, datos del titular flint, identificacion fiscal lssi espana, titular mcp keyflint dev",
    "/estado/": "estado del servicio flint, status servidores mcp, disponibilidad api licencias keyflint, uptime herramientas mcp",
    "/en/": "mcp servers, model context protocol tools, claude desktop mcp, cursor mcp tools, bank statement reconciliation mcp, deterministic ai tools, verified ai accounting, uvx mcp server",
    "/en/try/": "try mcp free, free mcp credits, test mcp tools claude, free license keyflint, ai accounting demo",
    "/en/start/": "how to install mcp server, claude desktop mcp guide, cursor ai mcp setup, vs code mcp install, uvx mcp installation",
    "/en/batch/": "batch bank statements processor, convert norma 43 online, batch n43 to csv excel, online bank statement converter, audit bank files batch",
    "/norma43/": "servidor mcp norma 43, mcp extractos bancarios espana, cuadre bancario claude, mcp santander bbva caixabank, parsear cuaderno 43 ai, mcp conciliacion bancaria",
    "/verifactu/": "servidor mcp verifactu, validar xml verifactu aeat, mcp facturae xsd, firma electronica xades factura, mcp fiscal espanol, auditar huella verifactu",
    "/contabridge/": "servidor mcp contabilidad, generar asientos contables ia, mcp plan general contable, exportar contasol a3 mcp, mcp asientos balance, cuadre contable",
    "/dataclean/": "servidor mcp limpieza datos, normalizar csv ia, formatear iban cif nif, validar datos contables mcp, limpieza masiva de datos",
    "/web-intel/": "servidor mcp auditoria web, scraping etico ia, analisis web mcp, verificacion dominios empresas, auditoria seo accesibilidad ia",
}


sys.path.insert(0, str(Path(__file__).parent))
from icons import BRANDS, ICONS  # noqa: E402

ROOT = Path(__file__).parent
OUT = ROOT / "public"
DATA = json.loads((ROOT / "data" / "catalog.json").read_text(encoding="utf-8"))
SITE = DATA["site"]
# Modo remoto (MCP por URL + OAuth): "remote": true en el catálogo cuando el contenedor esté desplegado. MCP_REMOTE=1 lo previsualiza.
SITE["remote"] = os.environ.get("MCP_REMOTE") == "1" or bool(SITE.get("remote"))
MCPS = DATA["mcps"]
TODAY = dt.date.today().isoformat()
VERSION = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d%H%M")
KEY_RE = r"[0-9a-f]{64}(,[0-9a-f]{64})*|[\w.-]+=[0-9a-f]{64}(,[\w.-]+=[0-9a-f]{64})*"
e = html.escape

# Idioma de render: las secciones compartidas (instalador, demos, sello, calculadora, saldo) salen en ES o EN
# según el contexto activo. L(es, en) elige el texto; U(clave) la ruta equivalente.
_LANG = ["es"]


def L(es: str, en: str) -> str:
    return en if _LANG[-1] == "en" else es


def U(key: str) -> str:
    return {"try": ("/probar/", "/en/try/"), "balance": ("/saldo/", "/en/balance/"), "start": ("/empezar/", "/en/start/"),
            "pricing": ("/precios/", "/en/#pricing"), "batch": ("/lote/", "/en/batch/"), "home": ("/", "/en/"), "install": ("/#instalar", "/en/#install"),
            "catalog": ("/#catalogo", "/en/#tools")}[key][_LANG[-1] == "en"]


class lang_ctx:
    def __init__(self, lang: str): self.lang = lang
    def __enter__(self): _LANG.append(self.lang)
    def __exit__(self, *a): _LANG.pop()


def _gateway_keyring() -> str:
    """Lee la clave pública actual del gateway (sigue las rotaciones de clave en cada build)."""
    url = SITE["keyflint_url"].rstrip("/") + "/api/v1/licenses/public-key"
    try:
        with urllib.request.urlopen(url, timeout=15) as r:
            return str(json.load(r)["data"]["keyring"]).strip()
    except Exception as exc:  # noqa: BLE001
        print(f"aviso: no se pudo leer {url}: {exc}")
        return ""


NEEDS_KEYS = any(not m.get("pypi") for m in MCPS)  # los paquetes de PyPI ya traen la clave pública
SITE["public_keys"] = "" if not NEEDS_KEYS else (os.environ.get("KEYFLINT_PUBLIC_KEYS", "").strip()
                       or (SITE["public_keys"] if re.fullmatch(KEY_RE, SITE["public_keys"]) else "")
                       or _gateway_keyring())
if NEEDS_KEYS and not re.fullmatch(KEY_RE, SITE["public_keys"]):
    raise SystemExit("ERROR: falta la clave pública del gateway. Pon KEYFLINT_PUBLIC_KEYS (hex de "
                     "https://licenses.keyflint.dev/api/v1/licenses/public-key) en data/catalog.json o como variable de entorno.")

CONTACT = SITE["contact"].removeprefix("mailto:")
LIC_PLACEHOLDER = "LIC-tu-licencia"


# ---------------------------------------------------------------- helpers

def icon(name: str, cls: str = "i") -> str:
    return (f'<svg class="{cls}" viewBox="0 0 24 24" aria-hidden="true" focusable="false">'
            f'{ICONS[name]}</svg>')


FLINT = '<polygon points="20,5 44,3 36,16 4,29" fill="#E0FF4D"/><polygon points="44,3 59,19 49,24 36,16" fill="#CCFF00"/><polygon points="59,19 57,42 49,24" fill="#9FCC00"/><polygon points="57,42 38,61 30,46 49,24" fill="#8DB300"/><polygon points="38,61 13,55 30,46" fill="#9FCC00"/><polygon points="13,55 4,29 18,34 30,46" fill="#C2F000"/><polygon points="4,29 36,16 49,24 30,46 18,34" fill="#B5E300"/><polygon points="15,34 22,27 29,34 43,17 50,24 29,45" fill="#0B0D17"/>'


def flint(cls: str = "logo") -> str:
    """Símbolo Flint: pedernal facetado con un ✓ grabado."""
    return f'<svg class="{cls}" viewBox="0 0 64 64" aria-hidden="true" focusable="false">{FLINT}</svg>'


def brand(name: str, cls: str = "b") -> str:
    vb, inner, hexc = BRANDS[name]
    return (f'<svg class="{cls} b-{name}" viewBox="{vb}" role="img" aria-hidden="true" focusable="false" '
            f'style="--brand-c:#{hexc}">{inner}</svg>')


def money(n: float) -> str:
    return f"{n:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".").removesuffix(",00")


def jsonld(obj) -> str:
    return f'<script type="application/ld+json">{json.dumps(obj, ensure_ascii=False)}</script>'


def code_block(id_: str, text: str, label: str = "") -> str:
    head = f'<span class="code-label">{e(label)}</span>' if label else "<span></span>"
    return (f'<div class="code"><div class="code-head">{head}'
            f'<button type="button" class="copy" data-copy="{id_}">{icon("copy")}<span>{L("Copiar", "Copy")}</span></button></div>'
            f'<pre id="{id_}" tabindex="0"><code>{e(text)}</code></pre></div>')


def faq_html(items) -> str:
    return "".join(f'<details class="qa"><summary><span>{e(q)}</span>{icon("chevron")}</summary><p>{e(a)}</p></details>'
                   for q, a in items)


def faq_ld(items) -> dict:
    return {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in items]}


def server_env(m: dict) -> dict:
    # Publicado en PyPI (v0.1.0+): el servidor ya trae gateway, clave pública y checkout por defecto.
    if m.get("pypi"):
        return {"KEYFLINT_LICENSE": LIC_PLACEHOLDER}
    return {"KEYFLINT_LICENSE": LIC_PLACEHOLDER, "KEYFLINT_URL": SITE["keyflint_url"],
            "KEYFLINT_PUBLIC_KEYS": SITE["public_keys"]}


def uvx_args(m: dict) -> list[str]:
    cmd = m.get("command", m["package"])
    if m.get("pypi"):
        return [cmd] if cmd == m["package"] else ["--from", m["package"], cmd]
    return ["--from", f"git+{m['repo']}", cmd]


def server_cfg(m: dict) -> dict:
    return {"command": "uvx", "args": uvx_args(m), "env": server_env(m)}


def members(m: dict) -> list[dict]:
    return [x for x in MCPS] if m.get("all") else [m]


def snippets(m: dict) -> dict[str, str]:
    ms = members(m)
    std = json.dumps({"mcpServers": {x["slug"]: server_cfg(x) for x in ms}}, indent=2, ensure_ascii=False)
    vscode = json.dumps({"servers": {x["slug"]: {"type": "stdio", **server_cfg(x)} for x in ms}}, indent=2, ensure_ascii=False)
    cc = "\n\n".join(f"claude mcp add {x['slug']} --scope user \\\n"
                      + "".join(f"  -e {k}={v} \\\n" for k, v in server_env(x).items())
                      + "  -- uvx " + " ".join(uvx_args(x)) for x in ms)
    codex = "\n\n".join(f"codex mcp add {x['slug']} "
                         + "".join(f"--env {k}={v} " for k, v in server_env(x).items())
                         + "-- uvx " + " ".join(uvx_args(x)) for x in ms)
    toml = "\n\n".join(f"[mcp_servers.{x['slug']}]\ncommand = \"uvx\"\nargs = {json.dumps(uvx_args(x))}\nenv = {{ "
                        + ", ".join(f"{k} = {json.dumps(v)}" for k, v in server_env(x).items()) + " }" for x in ms)
    return {"desktop": std, "code": cc, "cursor": std, "vscode": vscode, "windsurf": std, "codex": codex,
            "codex_toml": toml, "antigravity": std}


def remote_url(m: dict) -> str:
    return f"{SITE['url']}/{m['slug']}/mcp"


def remote_snippets(m: dict) -> dict[str, str]:
    """Modo remoto: el cliente se conecta por URL y hace OAuth (pega la licencia una vez). Sin uv ni Python."""
    ms = members(m)
    auth = {"Authorization": f"Bearer {LIC_PLACEHOLDER}"}
    dump = lambda d: json.dumps(d, indent=2, ensure_ascii=False)
    return {
        "url": "\n".join(remote_url(x) for x in ms),
        "code": "\n".join(f"claude mcp add --transport http --scope user {x['slug']} {remote_url(x)}" for x in ms),
        "cursor": dump({"mcpServers": {x["slug"]: {"url": remote_url(x)} for x in ms}}),
        "vscode": dump({"servers": {x["slug"]: {"type": "http", "url": remote_url(x)} for x in ms}}),
        "codex": "\n".join(f"codex mcp add {x['slug']} --url {remote_url(x)}\ncodex mcp login {x['slug']}" for x in ms),
        "codex_toml": "\n\n".join(f"[mcp_servers.{x['slug']}]\nurl = \"{remote_url(x)}\"\n"
                                   f"http_headers = {{ Authorization = \"Bearer {LIC_PLACEHOLDER}\" }}" for x in ms),
        "headers": dump({"mcpServers": {x["slug"]: {"serverUrl": remote_url(x), "headers": auth} for x in ms}}),
        "gemini": "\n".join(f"gemini mcp add --transport http --scope user {x['slug']} {remote_url(x)}" for x in ms),
        "url_headers": dump({"mcpServers": {x["slug"]: {"url": remote_url(x), "headers": auth} for x in ms}}),
    }


ALL = {"slug": "todos", "name": "Todos", "all": True, "icon": "stack"}


CLIENTS_REMOTE = [
    ("desktop", "Claude", "claude"),
    ("chatgpt", "ChatGPT", "chatgpt"),
    ("code", "Claude Code", "claude"),
    ("cursor", "Cursor", "cursor"),
    ("vscode", "VS Code", "vscode"),
    ("codex", "Codex", "codex"),
    ("antigravity", "Antigravity", "antigravity"),
    ("windsurf", "Windsurf / Devin", "windsurf"),
    ("more", ("Más clientes", "More clients"), "icon:plug"),
]

CLIENTS = [
    ("desktop", "Claude Desktop", "claude"),
    ("code", "Claude Code", "claude"),
    ("cursor", "Cursor", "cursor"),
    ("vscode", "VS Code", "vscode"),
    ("codex", "Codex", "codex"),
    ("antigravity", "Antigravity", "antigravity"),
    ("windsurf", "Windsurf", "windsurf"),
]
# Cinta "Compatible con": ChatGPT solo conecta por URL (modo remoto)
_cl = {c[0]: c for c in CLIENTS + CLIENTS_REMOTE}
MARQUEE = [_cl[k] for k in ("desktop", "cursor", "chatgpt", "code", "vscode", "codex", "antigravity", "windsurf")
           if k != "chatgpt" or SITE["remote"]]


def client_name(name) -> str:
    return L(*name) if isinstance(name, tuple) else name


def client_icon(ic: str) -> str:
    return icon(ic[5:], "b") if ic.startswith("icon:") else brand(ic)


def installer(m: dict) -> str:
    """Instalador por cliente. Sin JS: paneles apilados. Con JS: pestañas, licencia en vivo y enlaces de 1 clic."""
    s = m["slug"]
    sn = snippets(m)
    tabs = "".join(
        f'<button type="button" role="tab" id="tab-{s}-{cid}" aria-controls="pan-{s}-{cid}" '
        f'aria-selected="{"true" if i == 0 else "false"}" tabindex="{0 if i == 0 else -1}" data-client="{cid}">'
        f'{brand(ic)}<span>{e(name)}</span></button>'
        for i, (cid, name, ic) in enumerate(CLIENTS))
    multi = bool(m.get("all"))
    key_line = (L("Si ya tienes servidores, copia solo los bloques de dentro de <code>mcpServers</code>.",
                  "Already have servers? Copy only the blocks inside <code>mcpServers</code>.") if multi
                else L(f'Si ya tienes servidores, añade solo <code>"{s}"</code> dentro de <code>mcpServers</code>.',
                       f'Already have servers? Add only <code>"{s}"</code> inside <code>mcpServers</code>.'))
    uv_note = (f'<p class="note">{icon("info")}<span>' + L(f'Necesita <a href="{U("start")}#uv">uv</a> instalado: un comando, una sola vez.',
                                                           f'Needs <a href="{U("start")}#uv">uv</a> installed: one command, once.') + '</span></p>')
    cards = (f'<p class="note">{icon("card")}<span>' + L('Los resultados se ven como <b>tarjetas visuales</b> en el chat: saldo de créditos, cifras clave e incidencias.',
                                                         'Results show up as <b>visual cards</b> in the chat: credit balance, key figures and issues.') + '</span></p>')
    panels = {
        "desktop": (f"""<a class="btn btn-primary btn-block" href="{m['repo']}/releases/latest" rel="noopener">{brand("claude")}{L("Descargar extensión para Claude Desktop", "Download the Claude Desktop extension")}</a>
<p class="muted small center gap">{L("Abre el archivo <code>.mcpb</code> descargado, pulsa <b>Instalar</b> y pega tu licencia. Sin terminal.", "Open the downloaded <code>.mcpb</code> file, click <b>Install</b> and paste your license. No terminal.")}</p>
<details class="manual"><summary><span>{L("Instalación manual", "Manual install")}</span>{icon("chevron")}</summary>""" if m.get("mcpb") else "") + f"""<ol class="mini-steps">
<li>{L("Abre Claude Desktop › <b>Ajustes</b> › <b>Desarrollador</b> › <b>Editar configuración</b>.", "Open Claude Desktop › <b>Settings</b> › <b>Developer</b> › <b>Edit Config</b>.")}</li>
<li>{L("Pega el bloque en", "Paste the block into")} <code>claude_desktop_config.json</code>. {key_line}</li>
<li>{L("Guarda y reinicia Claude Desktop por completo.", "Save and fully restart Claude Desktop.")}</li></ol>
{code_block(f"sn-{s}-desktop", sn["desktop"], "claude_desktop_config.json")}
<p class="path">macOS <code>~/Library/Application Support/Claude/</code><br>Windows <code>%APPDATA%\\Claude\\</code></p>""" + ("</details>" if m.get("mcpb") else "") + cards + uv_note,
        "code": f"""<ol class="mini-steps"><li>{L(f'Ejecuta {"los comandos" if multi else "el comando"} en tu terminal. Queda{"n" if multi else ""} disponible{"s" if multi else ""} en todos tus proyectos.', f'Run the command{"s" if multi else ""} in your terminal. Available in all your projects.')}</li>
<li>{L("Compruébalo con", "Check it with")} <code>claude mcp list</code>.</li></ol>
{code_block(f"sn-{s}-code", sn["code"], "Terminal")}{uv_note}""",
        "cursor": (f"""<p class="muted small">{L("Pega el bloque en <code>~/.cursor/mcp.json</code>. Para instalar con un clic, elige un solo servidor.", "Paste the block into <code>~/.cursor/mcp.json</code>. For one-click install, pick a single server.")}</p>
{code_block(f"sn-{s}-cursor", sn["cursor"], "mcp.json")}{uv_note}""" if multi else
                   f"""<a class="btn btn-primary btn-block" data-deeplink="cursor" href="#">{brand("cursor")}{L("Añadir a Cursor", "Add to Cursor")}</a>
<p class="muted small center gap">{L("Cursor se abre y te pide confirmar la instalación.", "Cursor opens and asks you to confirm.")}</p>
<details class="manual"><summary><span>{L("Instalación manual", "Manual install")}</span>{icon("chevron")}</summary>
<p>{L("Pega el bloque en <code>~/.cursor/mcp.json</code> (todos los proyectos) o en <code>.cursor/mcp.json</code> (solo este).", "Paste the block into <code>~/.cursor/mcp.json</code> (all projects) or <code>.cursor/mcp.json</code> (this one only).")}</p>
{code_block(f"sn-{s}-cursor", sn["cursor"], "mcp.json")}</details>{uv_note}"""),
        "vscode": (f"""<p class="muted small">{L("Pega el bloque en <code>.vscode/mcp.json</code>. Para instalar con un clic, elige un solo servidor.", "Paste the block into <code>.vscode/mcp.json</code>. For one-click install, pick a single server.")}</p>
{code_block(f"sn-{s}-vscode", sn["vscode"], ".vscode/mcp.json")}{uv_note}""" if multi else
                   f"""<a class="btn btn-primary btn-block" data-deeplink="vscode" href="#">{brand("vscode")}{L("Añadir a VS Code", "Add to VS Code")}</a>
<p class="muted small center gap">{L("Para VS Code 1.102 o superior, con el chat de Copilot en modo agente.", "VS Code 1.102 or later, with Copilot chat in agent mode.")}</p>
<details class="manual"><summary><span>{L("Instalación manual", "Manual install")}</span>{icon("chevron")}</summary>
<p>{L("Pega el bloque en <code>.vscode/mcp.json</code> de tu proyecto.", "Paste the block into your project's <code>.vscode/mcp.json</code>.")}</p>
{code_block(f"sn-{s}-vscode", sn["vscode"], ".vscode/mcp.json")}</details>{cards}{uv_note}"""),
        "codex": f"""<ol class="mini-steps"><li>{L(f'Ejecuta {"los comandos" if multi else "el comando"} en tu terminal. Sirve{"n" if multi else ""} para la CLI, la app y la extensión de Codex, que comparten configuración.', "Run it in your terminal. Works for the Codex CLI, app and extension, which share one config.")}</li>
<li>{L("Compruébalo con <code>codex mcp list</code> o con <code>/mcp</code> dentro de Codex.", "Check it with <code>codex mcp list</code> or <code>/mcp</code> inside Codex.")}</li></ol>
{code_block(f"sn-{s}-codex", sn["codex"], "Terminal")}
<details class="manual"><summary><span>{L("Instalación manual", "Manual install")}</span>{icon("chevron")}</summary>
<p>{L("Pega el bloque en", "Paste the block into")} <code>~/.codex/config.toml</code>.</p>
{code_block(f"sn-{s}-codex-toml", sn["codex_toml"], "config.toml")}</details>{uv_note}""",
        "antigravity": f"""<ol class="mini-steps"><li>{L("Antigravity › panel del agente › menú", "Antigravity › agent panel › menu")} <b>…</b> › <b>MCP Servers</b> › <b>Manage MCP Servers</b> › <b>View raw config</b>.</li>
<li>{L("Pega el bloque, guarda y pulsa <b>Refresh</b>.", "Paste the block, save and click <b>Refresh</b>.")} {key_line}</li></ol>
{code_block(f"sn-{s}-antigravity", sn["antigravity"], "mcp_config.json")}
<p class="path"><code>~/.gemini/antigravity/mcp_config.json</code></p>{uv_note}""",
        "windsurf": f"""<ol class="mini-steps"><li>Windsurf › <b>Settings</b> › <b>Cascade</b> › <b>MCP Servers</b> › <b>View raw config</b>.</li>
<li>{L("Pega el bloque, guarda y pulsa <b>Refresh</b>.", "Paste the block, save and click <b>Refresh</b>.")}</li></ol>
{code_block(f"sn-{s}-windsurf", sn["windsurf"], "mcp_config.json")}
<p class="path"><code>~/.codeium/windsurf/mcp_config.json</code></p>{uv_note}""",
    }
    clients, server = CLIENTS, None if multi else server_cfg(m)
    if SITE.get("remote"):
        clients, server = CLIENTS_REMOTE, None if multi else {"url": remote_url(m)}
        panels = remote_panels(m, panels["desktop"], cards)
        tabs = "".join(
            f'<button type="button" role="tab" id="tab-{s}-{cid}" aria-controls="pan-{s}-{cid}" '
            f'aria-selected="{"true" if i == 0 else "false"}" tabindex="{0 if i == 0 else -1}" data-client="{cid}">'
            f'{client_icon(ic)}<span>{e(client_name(name))}</span></button>'
            for i, (cid, name, ic) in enumerate(clients))
    body = "".join(
        f'<div role="tabpanel" id="pan-{s}-{cid}" aria-labelledby="tab-{s}-{cid}" class="panel"'
        f'{"" if i == 0 else " data-hidden"}><h4 class="panel-title">{e(client_name(name))}</h4>{panels[cid]}</div>'
        for i, (cid, name, _) in enumerate(clients))
    cfg_json = e(json.dumps({"slug": s, "server": server, "name": m["name"], "desc": m.get("headline", "")}, ensure_ascii=False))
    return f"""<div class="installer" data-installer="{cfg_json}">
<label class="lic"><span class="lic-label">{icon("key")}{L("Tu licencia", "Your license")} <span class="muted">· {L("opcional", "optional")}</span></span>
<span class="lic-field"><input type="text" autocomplete="off" spellcheck="false" placeholder="{L("Pega aquí tu LIC-…", "Paste your LIC-… here")}" data-license aria-describedby="lic-help-{s}"><span class="lic-state" data-license-state aria-live="polite"></span></span>
<span id="lic-help-{s}" class="lic-help">{L("Se rellena en todos los fragmentos. No sale de tu navegador.", "Fills in every snippet. It never leaves your browser.")}</span></label>
<div class="tabs" role="tablist" aria-label="{L("Elige tu cliente", "Choose your client")}">{tabs}</div>
<div class="panels">{body}</div>
</div>"""


MORE_LINKS = [  # (data-deeplink id, brand label, needs license in the link)
    ("goose", "Goose", False),
    ("lmstudio", "LM Studio", True),
    ("kiro", "Kiro", False),
    ("vscode-insiders", "VS Code Insiders", False),
]


def more_panel(m: dict, sn: dict, multi: bool, oauth: str) -> str:
    """Clientes con menos cuota: botones de 1 clic (un servidor), Gemini CLI y JSON con cabecera para el resto."""
    s = m["slug"]
    if multi:
        buttons = f'<p class="muted small">{L("Para instalar con un clic, elige un solo servidor.", "For one-click install, pick a single server.")}</p>'
    else:
        btn = lambda cid, name, lic: (f'<a class="btn btn-ghost btn-block" data-deeplink="{cid}" href="#" rel="nofollow">{icon("plug")}'
                                      f'{L("Añadir a", "Add to")} {name}{" *" if lic else ""}</a>')
        buttons = (f'<div class="more-links">{"".join(btn(*x) for x in MORE_LINKS)}</div>'
                   f'<p class="muted small">{L("* LM Studio guarda la licencia que pegues arriba en su configuración. El resto inicia sesión con tu licencia al conectar.", "* LM Studio stores the license you paste above in its config. The others sign in with your license when they connect.")}</p>')
    return f"""{buttons}
<h5 class="sub">Gemini CLI</h5>{code_block(f"sn-{s}-gemini", sn["gemini"], "Terminal")}
<p class="muted small">{L("La primera vez, <code>/mcp auth</code> abre la página de KeyFlint para pegar tu licencia.", "The first time, <code>/mcp auth</code> opens the KeyFlint page to paste your license.")}</p>
<h5 class="sub">Zed · JetBrains Junie · Warp · Cline · Raycast</h5>
<p class="muted small">{L("Pega el bloque en la configuración MCP de tu cliente (lleva tu licencia). En Zed va dentro de <code>context_servers</code>; en Cline añade <code>\"type\": \"streamableHttp\"</code>.", "Paste the block into your client's MCP config (it carries your license). In Zed it goes inside <code>context_servers</code>; in Cline add <code>\"type\": \"streamableHttp\"</code>.")}</p>
{code_block(f"sn-{s}-more-json", sn["url_headers"], "mcp.json")}"""


def remote_panels(m: dict, local_desktop: str, cards: str) -> dict[str, str]:
    s, sn, multi = m["slug"], remote_snippets(m), bool(m.get("all"))
    pl = "s" if multi else ""
    oauth = ('<p class="note">' + icon("key") + '<span>' + L('La primera vez se abre una página de KeyFlint: pega tu licencia y pulsa <b>Conectar</b>. No hay que instalar nada.',
                                                             'The first time, a KeyFlint page opens: paste your license and click <b>Connect</b>. Nothing to install.') + '</span></p>')
    url_block = code_block(f"sn-{s}-url", sn["url"], "URL" + ("s" if multi else ""))
    one_click = lambda cid, label, note: (
        f'<p class="muted small">{L("Pega el bloque. Para instalar con un clic, elige un solo servidor.", "Paste the block. For one-click install, pick a single server.")}</p>' if multi else
        f'<a class="btn btn-primary btn-block" data-deeplink="{cid}" href="#">{brand(cid)}{label}</a>'
        f'<p class="muted small center gap">{note}</p><details class="manual"><summary><span>{L("Instalación manual", "Manual install")}</span>{icon("chevron")}</summary>')
    end = "" if multi else "</details>"
    return {
        "desktop": f"""<ol class="mini-steps"><li>{L("En Claude (web, escritorio o móvil): <b>Ajustes</b> › <b>Conectores</b> › <b>Añadir conector personalizado</b>.", "In Claude (web, desktop or mobile): <b>Settings</b> › <b>Connectors</b> › <b>Add custom connector</b>.")}</li>
<li>{L(f'Ponle nombre y pega {"las URL" if multi else "la URL"}. {"Repite con cada una." if multi else ""}', f'Name it and paste the URL{pl}. {"Repeat for each one." if multi else ""}')}</li><li>{L("Pulsa <b>Conectar</b> e inicia sesión con tu licencia.", "Click <b>Connect</b> and sign in with your license.")}</li></ol>
{url_block}<a class="btn btn-block" href="https://claude.ai/settings/connectors" target="_blank" rel="noopener">{brand("claude")}{L("Abrir conectores de Claude", "Open Claude connectors")}</a>
{oauth}{cards}<details class="manual"><summary><span>{L("Instalación local (.mcpb o configuración)", "Local install (.mcpb or config)")}</span>{icon("chevron")}</summary>{local_desktop}</details>""",
        "chatgpt": f"""<ol class="mini-steps"><li>{L("ChatGPT › <b>Ajustes</b> › <b>Apps y conectores</b> › <b>Avanzado</b>: activa el <b>modo desarrollador</b>.", "ChatGPT › <b>Settings</b> › <b>Apps &amp; Connectors</b> › <b>Advanced</b>: turn on <b>developer mode</b>.")}</li>
<li>{L(f"<b>Crear</b> conector: pega {'las URL' if multi else 'la URL'}, autenticación <b>OAuth</b>.", f"<b>Create</b> a connector: paste the URL{pl}, authentication <b>OAuth</b>.")}</li><li>{L("Conecta e inicia sesión con tu licencia.", "Connect and sign in with your license.")}</li></ol>
{code_block(f"sn-{s}-gpt-url", sn["url"], "URL" + ("s" if multi else ""))}{oauth}""",
        "code": f"""<ol class="mini-steps"><li>{L(f'Ejecuta {"los comandos" if multi else "el comando"} en tu terminal.', "Run it in your terminal.")}</li>
<li>{L("Abre Claude Code, escribe <code>/mcp</code> y elige <b>Authenticate</b> para pegar tu licencia.", "Open Claude Code, type <code>/mcp</code> and choose <b>Authenticate</b> to paste your license.")}</li></ol>
{code_block(f"sn-{s}-code", sn["code"], "Terminal")}{oauth}""",
        "cursor": one_click("cursor", L("Añadir a Cursor", "Add to Cursor"), L("Cursor se abre, confirma y pulsa <b>Connect</b> para pegar tu licencia.", "Cursor opens: confirm and click <b>Connect</b> to paste your license."))
        + f"""<p>{L("Pega el bloque en", "Paste the block into")} <code>~/.cursor/mcp.json</code>.</p>{code_block(f"sn-{s}-cursor", sn["cursor"], "mcp.json")}{end}{oauth}""",
        "vscode": one_click("vscode", L("Añadir a VS Code", "Add to VS Code"), L("VS Code 1.102 o superior. Te pedirá iniciar sesión con tu licencia.", "VS Code 1.102 or later. It asks you to sign in with your license."))
        + f"""<p>{L("Pega el bloque en", "Paste the block into")} <code>.vscode/mcp.json</code>.</p>{code_block(f"sn-{s}-vscode", sn["vscode"], ".vscode/mcp.json")}{end}{cards}{oauth}""",
        "codex": f"""<ol class="mini-steps"><li>{L(f'Ejecuta {"los comandos" if multi else "el comando"}: añade{"n" if multi else ""} el servidor{"es" if multi else ""} e inicia sesión con tu licencia.', f'Run the command{"s" if multi else ""}: {"they add the servers" if multi else "it adds the server"} and sign you in with your license.')}</li>
<li>{L("Sirve para la CLI, la app y la extensión de Codex.", "Works for the Codex CLI, app and extension.")}</li></ol>
{code_block(f"sn-{s}-codex", sn["codex"], "Terminal")}
<details class="manual"><summary><span>{L("Sin OAuth: licencia en config.toml", "No OAuth: license in config.toml")}</span>{icon("chevron")}</summary>
<p>{L("Pega el bloque en", "Paste the block into")} <code>~/.codex/config.toml</code>.</p>{code_block(f"sn-{s}-codex-toml", sn["codex_toml"], "config.toml")}</details>""",
        "antigravity": f"""<ol class="mini-steps"><li>{L("Antigravity › panel del agente", "Antigravity › agent panel")} › <b>…</b> › <b>MCP Servers</b> › <b>Manage MCP Servers</b> › <b>View raw config</b>.</li>
<li>{L("Pega el bloque (lleva tu licencia), guarda y pulsa <b>Refresh</b>.", "Paste the block (it carries your license), save and click <b>Refresh</b>.")}</li></ol>
{code_block(f"sn-{s}-antigravity", sn["headers"], "mcp_config.json")}<p class="path"><code>~/.gemini/config/mcp_config.json</code> · {L("versiones anteriores", "older versions")}: <code>~/.gemini/antigravity/mcp_config.json</code></p>""",
        "windsurf": f"""<ol class="mini-steps"><li>{L("Windsurf (ahora Devin Desktop)", "Windsurf (now Devin Desktop)")} › <b>Settings</b> › <b>Cascade</b> › <b>MCP Servers</b> › <b>View raw config</b>.</li>
<li>{L("Pega el bloque (lleva tu licencia), guarda y pulsa <b>Refresh</b>.", "Paste the block (it carries your license), save and click <b>Refresh</b>.")}</li></ol>
{code_block(f"sn-{s}-windsurf", sn["headers"], "mcp_config.json")}<p class="path"><code>~/.config/devin/mcp_config.json</code> · Windsurf: <code>~/.codeium/windsurf/mcp_config.json</code></p>""",
        "more": more_panel(m, sn, multi, oauth),
    }


# ---------------------------------------------------------------- layout

def build_page_ld(path: str, title: str, desc: str, lang: str = "es", custom_ld: list | None = None) -> list:
    url = SITE["url"] + path
    items = []
    custom = custom_ld or []

    # WebPage schema
    has_webpage = any(isinstance(x, dict) and x.get("@type") == "WebPage" for x in custom)
    if not has_webpage:
        items.append({
            "@context": "https://schema.org",
            "@type": "WebPage",
            "@id": f"{url}#webpage",
            "url": url,
            "name": title,
            "description": desc,
            "inLanguage": lang,
            "isPartOf": {
                "@type": "WebSite",
                "@id": f"{SITE['url']}/#website",
                "name": SITE["name"],
                "url": f"{SITE['url']}/"
            }
        })

    # WebSite definition on root pages
    has_website = any(isinstance(x, dict) and x.get("@type") == "WebSite" for x in custom)
    if not has_website and path in ("/", "/en/"):
        items.append({
            "@context": "https://schema.org",
            "@type": "WebSite",
            "@id": f"{SITE['url']}/#website",
            "name": SITE["name"],
            "alternateName": "Flint",
            "url": f"{SITE['url']}/",
            "description": SITE["description"],
            "inLanguage": lang,
            "publisher": {"@id": f"{SITE['url']}/#organization"}
        })

    # Organization schema
    has_org = any(isinstance(x, dict) and x.get("@type") == "Organization" for x in custom)
    if not has_org:
        items.append({
            "@context": "https://schema.org",
            "@type": "Organization",
            "@id": f"{SITE['url']}/#organization",
            "name": "KeyFlint",
            "url": "https://keyflint.dev",
            "logo": f"{SITE['url']}/assets/flint-icon.svg",
            "email": CONTACT,
            "sameAs": ["https://twitter.com/keyflint", "https://github.com/keyflint"]
        })

    # BreadcrumbList for subpages (avoid duplicates and exclude 404/thanks)
    has_crumb = any(isinstance(x, dict) and x.get("@type") == "BreadcrumbList" for x in custom)
    if not has_crumb and path not in ("/", "/en/", "/404", "/gracias/"):
        crumb_title = title.split("·")[0].split(":")[0].strip()
        crumbs = [
            {"@type": "ListItem", "position": 1, "name": ("Inicio" if lang == "es" else "Home"), "item": (f"{SITE['url']}/" if lang == "es" else f"{SITE['url']}/en/")},
            {"@type": "ListItem", "position": 2, "name": crumb_title, "item": url}
        ]
        items.append({
            "@context": "https://schema.org",
            "@type": "BreadcrumbList",
            "itemListElement": crumbs
        })

    # WebApplication schema for tool & batch pages
    is_tool = any(path.startswith(f"/{m['slug']}/") for m in MCPS)
    is_app = path in ("/lote/", "/en/batch/", "/norma43-a-excel/", "/norma43-a-contasol/", "/norma43-a-a3/", "/norma43-a-contaplus/", "/visor-norma-43/", "/validar-iban-cif/")
    has_app = any(isinstance(x, dict) and x.get("@type") in ("SoftwareApplication", "WebApplication") for x in custom)
    if (is_tool or is_app) and not has_app:
        items.append({
            "@context": "https://schema.org",
            "@type": "WebApplication",
            "name": title.split("·")[0].strip(),
            "url": url,
            "description": desc,
            "applicationCategory": "BusinessApplication",
            "operatingSystem": "Windows, macOS, Linux, Web",
            "offers": {
                "@type": "Offer",
                "price": "0",
                "priceCurrency": "EUR",
                "description": ("Prueba gratuita disponible con créditos de bienvenida" if lang == "es" else "Free trial with complimentary credits")
            }
        })

    # Append custom LD
    items.extend(custom)
    return items


def page(path: str, title: str, desc: str, body: str, ld: list | None = None, noindex: bool = False, lang: str | None = None) -> str:
    if lang is None:
        lang = _LANG[-1]
    url = SITE["url"] + path
    all_ld = build_page_ld(path, title, desc, lang, ld)
    lds = "".join(jsonld(x) for x in all_ld)
    robots = '<meta name="robots" content="noindex">\n' if noindex else ""
    en = lang == "en"
    pair = ALT_LANG.get(path) or {v: k for k, v in ALT_LANG.items()}.get(path)
    nav = ([("/en/#tools", "Tools"), ("/en/#install", "Install"), ("/en/#pricing", "Pricing"), ("/en/start/", "Guide"), ("/en/balance/", "My balance"), (pair or "/", "ES")] if en else
           [("/#catalogo", "Catálogo"), ("/#instalar", "Instalar"), ("/precios/", "Precios"), ("/empezar/", "Guía"), ("/saldo/", "Mi saldo"), (pair or "/en/", "EN")])
    alts = ""
    if pair:
        es_p, en_p = (pair, path) if en else (path, pair)
        alts = (f'<link rel="alternate" hreflang="es" href="{SITE["url"]}{es_p}">\n'
                f'<link rel="alternate" hreflang="en" href="{SITE["url"]}{en_p}">\n')
    T = ({"locale": "en_US", "alt_locale": "es_ES", "skip": "Skip to content", "home": "/en/", "cta": ("/en/try/", "Try free"), "navl": "Main"} if en else
         {"locale": "es_ES", "alt_locale": "en_US", "skip": "Saltar al contenido", "home": "/", "cta": ("/probar/", "Probar gratis"), "navl": "Principal"})
    navh = "".join(f'<a href="{h}"' + (' aria-current="page"' if h == path else "") + f">{t}</a>" for h, t in nav)
    tok = SITE.get("cf_analytics_token", "").strip()
    analytics = (f'<script defer src="https://static.cloudflareinsights.com/beacon.min.js" data-cf-beacon=\'{{"token": "{e(tok)}"}}\'></script>\n'
                 if tok and not noindex else "")
    foot_es = "" if en else f"""<footer class="foot"><div class="wrap">
<div class="foot-grid">
<div class="foot-brand"><a class="brand" href="/">{flint()}<span>Flint</span><span class="brand-tag">by KeyFlint</span></a>
<p class="muted small">Herramientas contables y bancarias verificadas para agentes de IA, con licencias criptográficas y pago por uso.</p></div>
<div><h3>Servidores</h3><ul>{''.join(f'<li><a href="/{m["slug"]}/">{e(m["name"])}</a></li>' for m in MCPS)}</ul></div>
<div><h3>Recursos</h3><ul><li><a href="/visor-norma-43/">Visor Norma 43</a></li><li><a href="/validar-iban-cif/">Validador IBAN y CIF</a></li><li><a href="/que-es-norma-43/">Qué es Norma 43</a></li><li><a href="/boletin/">Boletín del cierre</a></li><li><a href="/asesorias/">Para asesorías</a></li><li><a href="/lote/">Procesar por lotes</a></li><li><a href="/empezar/">Guía de instalación</a></li><li><a href="https://keyflint.dev">KeyFlint</a></li></ul></div>
<div><h3>Legal y soporte</h3><ul><li><a href="/terminos/">Términos de uso</a></li><li><a href="/reembolsos/">Reembolsos</a></li><li><a href="/aviso-legal/">Aviso legal</a></li><li><a href="/estado/">Estado del servicio</a></li><li><a href="https://keyflint.dev/privacy.html">Privacidad</a></li><li><a href="/confianza/">Confianza y datos</a></li><li><a href="https://keyflint.dev/dpa.html">Encargo de tratamiento</a></li><li><a href="{SITE['contact']}">{e(CONTACT)}</a></li></ul></div>
</div>
<div class="foot-base">
<p class="muted small">© {dt.date.today().year} KeyFlint · Los servidores se ejecutan en tu equipo y no guardan tus datos.</p>
<div class="badges">
<a class="badge-pill" href="https://stripe.com" rel="noopener"><span class="muted">Pagos con</span>{brand("stripe")}<b>Stripe</b></a>
<a class="badge-pill kf" href="https://keyflint.dev"><span class="muted">Licencias</span><span class="kf-mark">{icon("logo", "logo")}by&nbsp;KeyFlint</span></a>
</div></div>
</div></footer>"""

    hero_preload = f'<link rel="preload" href="/assets/video/{"flint-launch-en.webp" if en else "flint-lanzamiento-es.webp"}" as="image" type="image/webp" fetchpriority="high">\n' if path in ("/", "/en/") else ""

    return f"""<!doctype html>
<html lang="{lang}" class="no-js">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<meta name="keywords" content="{e(SEO_KEYWORDS.get(path, 'mcp servidores, norma 43, contabilidad, verifactu, flint, keyflint'))}">
<meta name="geo.region" content="ES">
<meta name="geo.placename" content="{'Spain' if en else 'España'}">
<meta http-equiv="content-language" content="{lang}">
{robots}<link rel="canonical" href="{url}">
{alts}<meta property="og:type" content="website">
<meta property="og:site_name" content="Flint">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{SITE['url']}/assets/{'og-flint-en.png' if T['locale'].startswith('en') else 'og-flint.png'}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="Flint">
<meta property="og:locale" content="{T['locale']}">
<meta property="og:locale:alternate" content="{T['alt_locale']}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:site" content="@keyflint">
<meta name="twitter:creator" content="@keyflint">
<meta name="twitter:title" content="{e(title)}">
<meta name="twitter:description" content="{e(desc)}">
<meta name="twitter:image" content="{SITE['url']}/assets/{'og-flint-en.png' if T['locale'].startswith('en') else 'og-flint.png'}">
<meta name="twitter:image:alt" content="Flint">
<meta name="theme-color" content="#0B0D17">
<meta name="color-scheme" content="light">
<script>document.documentElement.className="js"</script>
<link rel="icon" href="/favicon.ico" sizes="any">
<link rel="icon" type="image/svg+xml" href="/favicon.svg">
<link rel="icon" type="image/png" sizes="48x48" href="/icon-48.png">
<link rel="icon" type="image/png" sizes="192x192" href="/icon-192.png">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<link rel="preload" href="/assets/fonts/inter-400.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="/assets/fonts/interdisplay-600.woff2" as="font" type="font/woff2" crossorigin>

{hero_preload}<link rel="stylesheet" href="/assets/style.css?v={VERSION}">
<script defer src="/assets/app.js?v={VERSION}"></script>
{analytics}{lds}
</head>
<body>
<a class="skip" href="#main">{T['skip']}</a>
<header class="top"><div class="wrap top-in">
<a class="brand" href="{T['home']}" aria-label="Flint by KeyFlint">{flint()}<span>Flint</span><span class="brand-tag">by KeyFlint</span></a>
<nav class="nav" aria-label="{T['navl']}">{navh}</nav>
<a class="top-saldo" href="{"/en/balance/" if en else "/saldo/"}" aria-label="{"My balance" if en else "Mi saldo"}"{" aria-current=\"page\"" if path in ("/saldo/", "/en/balance/") else ""}>{icon("key")}<span>{"My balance" if en else "Mi saldo"}</span></a>
<a class="btn btn-primary btn-sm top-cta" href="{T['cta'][0]}">{T['cta'][1]}</a>
</div></header>
<main id="main">
{body}
</main>
{foot_en() if en else foot_es}
</body>
</html>
"""


# ---------------------------------------------------------------- sections

def mcp_card(m: dict) -> str:
    chips = "".join(f'<li><code>{e(t[0].split(",")[0])}</code></li>' for t in m["tools"][:3])
    glyph = {t[1]: t[0] for t in EN_TOOLS}.get(m["slug"])
    top = (f'<img class="flint-glyph" src="/assets/flint/{glyph}.svg" alt="" width="44" height="44">' if glyph
           else f'<span class="tile">{icon(m["icon"])}</span>')
    return f"""<div class="card mcp-card en-tool">
<div class="card-top">{top}<code class="muted small">{e(m['package'])}</code></div>
<h3><a href="/{m['slug']}/">{e(m['name'])}</a></h3>
<p><b>{e(m['headline'])}</b></p>
<p class="muted small">{e(m['category'])} · {len(m['tools'])} herramientas</p>
<ul class="chips">{chips}</ul>
<span class="card-foot"><a class="link-arrow" href="/{m['slug']}/">Ver ficha{icon("arrow-right")}</a>
<a class="link-arrow" href="{e(m['repo'])}" rel="noopener">GitHub{icon("arrow-right")}</a>
<a class="link-arrow" href="https://pypi.org/project/{e(m['package'])}/" rel="noopener">PyPI{icon("arrow-right")}</a></span>
</div>"""


def install_picker() -> tuple[str, str]:
    """Selector de servidor + instalador de cada uno (inicio y /probar/)."""
    opts = MCPS + [ALL]
    picker = "".join(
        f'<button type="button" class="pick" aria-pressed="{"true" if i == 0 else "false"}" data-pick="{m["slug"]}">'
        f'{icon(m["icon"])}<span>{e(L(m["name"], "All") if m.get("all") else m["name"])}</span></button>' for i, m in enumerate(opts))
    installers = "".join(f'<div class="pick-panel" data-pick-panel="{m["slug"]}"{"" if i == 0 else " data-hidden"}>'
                         f'<h3 class="panel-title">{e(L(m["name"], "All") if m.get("all") else m["name"])}</h3>{installer(m)}</div>'
                         for i, m in enumerate(opts))
    return picker, installers


def quick_install() -> str:
    """Instalador de un comando (installer/instalar.*): todos los servidores en todos los clientes detectados."""
    sh = f"curl -LsSf {SITE['url']}/instalar.sh | sh -s -- {LIC_PLACEHOLDER}"
    ps = f"$env:KEYFLINT_LICENSE='{LIC_PLACEHOLDER}'; irm {SITE['url']}/instalar.ps1 | iex"
    return f"""<div class="quick" data-installer='{{"slug": "quick"}}'>
<p class="quick-title">{icon("terminal")}<b>{L("Un solo comando", "One command")}</b><span class="muted small">{L(f"Instala los {len(MCPS)} servidores en Claude Desktop, Cursor, VS Code, Windsurf y Claude Code (los que tengas).", f"Installs all {len(MCPS)} tools in Claude Desktop, Cursor, VS Code, Windsurf and Claude Code (whichever you have).")}</span></p>
<span class="lic-field"><input type="text" autocomplete="off" spellcheck="false" placeholder="{L("Pega aquí tu LIC-…", "Paste your LIC-… here")}" data-license aria-label="{L("Tu licencia", "Your license")}"><span class="lic-state" data-license-state aria-live="polite"></span></span>
<p class="lic-help"></p>
{code_block("q-sh", sh, "macOS / Linux · Terminal")}
{code_block("q-ps", ps, "Windows · PowerShell")}
<p class="muted small">{L(f'Instala <a href="{U("start")}#uv">uv</a> si falta, guarda una copia de cada configuración antes de tocarla y no envía nada salvo la licencia a KeyFlint. <a href="/instalar.py">Ver el código</a>.', f'Installs <a href="{U("start")}#uv">uv</a> if missing, backs up every config before touching it and sends nothing but the license to KeyFlint. <a href="/instalar.py">Read the code</a>.')}</p>
</div>"""


def installer_files() -> None:
    servers = {m["slug"]: server_cfg(m) for m in MCPS}
    src = (ROOT / "installer" / "instalar.py").read_text(encoding="utf-8")
    write("instalar.py", src.replace("__SERVERS__", json.dumps(servers, ensure_ascii=False)).replace("__PH__", LIC_PLACEHOLDER))
    for f in ("instalar.sh", "instalar.ps1", "lote.py", "lote.sh", "lote.ps1"):
        write(f, (ROOT / "installer" / f).read_text(encoding="utf-8").replace("__SITE__", SITE["url"]))


DEMO_N43 = "112100041802000513322610012610312000000001500009783ACME SOLUCIONES SL           \n22    0418261003261003020002000000001250000000000000000000000000                \n2301CLIENTE DEMO SL                                                             \n2303        FACTURA 2026-104                                                    \n22    0418261015261015030001000000000042350000012345000000000000                \n3321000418020005133200001000000000042350000100000000125000200000000270765978    \n88999999999999999999000006                                                      \n"
DEMO_CSV = ("Asiento;Fecha;Cuenta;Concepto;Debe;Haber\n"
            "1;02/11/2026;4300001;Factura 104 Cliente Demo;1.210,00;\n1;02/11/2026;7000001;Factura 104 Cliente Demo;;1.000,00\n"
            "1;02/11/2026;4770001;IVA 21% factura 104;;210,00\n"
            "2;05/11/2026;5720001;Cobro factura 104;1.210,00;\n2;05/11/2026;4300001;Cobro factura 104;;1.210,00\n")


DEMO_SLUGS = ("norma43", "contabridge", "web-intel")


def demo_block(m: dict, head: bool = True) -> str:
    """Prueba sin instalar (usa créditos del hub, no del visitante). Solo para los servidores con demo.
    head=False devuelve solo el formulario (pestañas de la portada y /asesorias/)."""
    s = m["slug"]
    if s == "web-intel":
        field = ('<label class="demo-field"><span>URL</span><input type="url" name="url" inputmode="url" '
                 f'placeholder="{L("https://tu-web.com", "https://your-site.com")}" value="https://keyflint.dev" required></label>')
        btn, tool = L("Ver Markdown limpio", "Get clean Markdown"), "read_url"
    elif s == "norma43":
        field = (f'<label class="demo-field"><span>{L("Extracto Norma 43 (ejemplo)", "Norma 43 bank statement (sample)")}</span><textarea name="content" rows="7" '
                 f'spellcheck="false" required>{e(DEMO_N43)}</textarea></label>')
        btn, tool = L("Validar y leer", "Validate and parse"), "parse_norma43"
    elif s == "contabridge":
        opts = "".join(f'<option value="{v}">{t}</option>' for v, t in
                       [("a3", "A3 (SUENLACE.DAT)"), ("contaplus_csv", "ContaPlus / Sage 50"), ("xero_csv", "Xero"), ("quickbooks_csv", "QuickBooks Online")])
        field = (f'<label class="demo-field"><span>{L("Dos asientos de ejemplo (CSV)", "Two sample journal entries (CSV)")}</span><textarea name="content" rows="6" '
                 f'spellcheck="false" required>{e(DEMO_CSV)}</textarea></label>'
                 f'<label class="demo-field demo-inline"><span>{L("Convertir a", "Convert to")}</span><select name="target">{opts}</select></label>')
        btn, tool = L("Convertir", "Convert"), "convert_journal"
    else:
        return ""
    form = f"""<form class="glass demo-form" data-demo="{s}" novalidate>{field}
<div class="demo-actions"><button class="btn btn-primary" type="submit">{icon("arrow-right")}{btn}</button>
<span class="muted small">{L(f'5 pruebas al día. Para tus propios ficheros, <a href="{U("try")}">licencia gratis</a>.', f'5 runs a day. For your own files, get a <a href="{U("try")}">free license</a>.')}</span></div>
<p class="lic-help" data-demo-msg aria-live="polite"></p>
<div class="demo-out" data-demo-out hidden></div>
</form>"""
    if not head:
        return form
    return f"""<div class="block demo-try" id="probar-aqui"><h2>Pruébalo aquí, sin instalar</h2>
<p class="muted">Es el servidor real (<code>{tool}</code>). La demo corre de nuestra cuenta: no gastas créditos ni necesitas licencia.</p>
{form}</div>
"""


def live_demo(slugs=DEMO_SLUGS, title: str = "", lead: str = "") -> str:
    """Playground de la portada: pestañas con las demos reales (/api/demo/<slug>)."""
    title = title or L("Pruébalo en vivo, sin instalar nada", "Try it live, nothing to install")
    lead = lead or L("Elige un ejemplo y pulsa el botón: es el servidor real, el mismo resultado que recibe tu agente. Sin licencia, sin configurar nada.",
                     "Pick an example and press the button: it is the real server, the same result your agent gets. No license, no setup.")
    by = {m["slug"]: m for m in MCPS}
    ms = [by[x] for x in slugs if x in by]
    tabs = "".join(f'<button type="button" class="pick" role="tab" aria-selected="{"true" if i == 0 else "false"}" '
                   f'data-live="{m["slug"]}">{icon(m["icon"])}<span>{e(m["name"])}</span></button>' for i, m in enumerate(ms))
    panels = "".join(f'<div class="live-panel" role="tabpanel" data-live-panel="{m["slug"]}"{"" if i == 0 else " hidden"}>{demo_block(m, head=False)}</div>'
                     for i, m in enumerate(ms))
    return f"""<section class="section alt" id="{L("en-vivo", "live")}"><div class="wrap narrow">
<div class="section-head"><p class="eyebrow">{L("Demo en vivo", "Live demo")}</p><h2>{title}</h2><p class="lead-sm">{lead}</p></div>
<div class="picker live-tabs" role="tablist" aria-label="{L("Elige una demo", "Pick a demo")}">{tabs}</div>
{panels}
<p class="muted small center">{L(f'¿Te convence? <a href="{U("try")}">Pide tu licencia gratis</a> y úsalo con tus propios ficheros desde Claude, Cursor o VS Code.', f'Convinced? <a href="{U("try")}">Get your free license</a> and use it on your own files from Claude, Cursor or VS Code.')}</p>
</div></section>"""


def seal(compact: bool = False) -> str:
    """Sello de Rigor Contable & Seguridad: cuadre matemático auditado bajo norma oficial AEB 43 y AEAT."""
    items = [("target", L("Cuadre bancario matemático exacto", "Exact mathematical balance"),
              L("Algoritmos verificados bajo la norma oficial AEB 43 y la AEAT. Dos ejecuciones generan exactamente el mismo fichero, sin IA intermedia en el cálculo numérico.",
                "Verified algorithms following official AEB 43 and AEAT standards. Two runs produce the exact same result, with zero AI in mathematical computations.")),
             ("shield", L("Cero invenciones ni asientos falsos", "Zero fabricated entries"),
              L("Flint jamás adivina ni genera apuntes ficticios. Si un movimiento presenta ambigüedad, queda marcado con aviso claro para revisión de tu gestor.",
                "Flint never guesses or fabricates accounting entries. Any ambiguous transaction is clearly flagged for human review.")),
             ("refund", L("Garantía de devolución automática", "Automatic refund guarantee"),
              L("Los ficheros dañados o con errores de formato se rechazan sin coste y, si ocurre un fallo de red, los créditos se reintegran a tu cuenta en el acto.",
                "Corrupted or invalid files are rejected at zero cost, and any transient network failure instantly refunds credits to your balance."))]
    lis = "".join(f'<li><span class="tile tile-sm">{icon(i)}</span><div><h3>{t}</h3><p>{d}</p></div></li>' for i, t, d in items)
    return f"""<section class="section{' tight' if compact else ''}"><div class="wrap"><div class="seal glass">
<div class="seal-badge" aria-hidden="true">{icon("check")}<span>{L("Cuadre 100%<br>Certificado", "100% Certified<br>Balance")}</span></div>
<div><h2>{L("Rigor contable estricto: 0% errores de cálculo, 0% alucinaciones", "Strict accounting rigor: 0% calculation errors, 0% hallucinations")}</h2><ul class="seal-list">{lis}</ul></div>
</div></div></section>"""


def trial_page() -> str:
    picker, installers = install_picker()
    body = f"""
<section class="hero hero-sm"><div class="glow" aria-hidden="true"></div><div class="wrap narrow">
<nav class="crumbs" aria-label="Ruta"><a href="/">Inicio</a>{icon("chevron-right")}<span aria-current="page">Probar gratis</span></nav>
<h1>{SITE['free_credits']} créditos gratis, sin tarjeta</h1>
<p class="lead">Escribe tu correo y te damos una licencia al momento. Sirve para todos los servidores; si luego compras un plan con el mismo correo, se amplía la misma.</p>
</div></section>
<section class="section tight"><div class="wrap narrow">
<form class="recover glass" data-trial-form novalidate>
<div><h2 class="h3">Tu licencia de prueba</h2>
<p class="muted small">Una por correo. En tu primera semana te enviamos 3 consejos de uso; te das de baja en 1 clic.</p></div>
<div class="recover-row"><input type="email" name="email" autocomplete="email" placeholder="tu@correo.com" required aria-label="Correo electrónico">
<button class="btn btn-primary" type="submit">{icon("key")}Darme la licencia</button></div>
<label class="news-opt"><input type="checkbox" name="newsletter"><span>Quiero recibir también el <b>Boletín del cierre</b> (1 correo al mes con trucos de Norma 43, ContaSol y a3; requiere confirmar enlace).</span></label>
<p class="lic-help" data-trial-msg aria-live="polite"></p>
</form>
<div class="reveal glass" data-trial-out hidden>
<div class="reveal-head"><span class="tile tile-sm">{icon("check")}</span><div><h2 class="h3">Lista: {SITE['free_credits']} créditos</h2>
<p class="muted small">Guardada en este navegador: los fragmentos de abajo ya la llevan puesta.</p></div></div>
{code_block("lic-trial", "LIC-…", "KEYFLINT_LICENSE")}
<p class="lic-help good" data-trial-news-note hidden>Te enviamos también el correo de confirmación para el Boletín del cierre.</p>
</div>
</div></section>
<section class="section" id="instalar"><div class="wrap install-grid">
<div class="section-head left"><p class="eyebrow">Siguiente paso</p><h2>Instálalo en tu cliente</h2>
<p class="lead-sm">Claude Desktop (extensión .mcpb), Claude Code, Cursor, VS Code y más. Elige servidor y copia.</p></div>
<div class="install-card glass">{quick_install()}<p class="quick-or muted small">o elige servidor y cliente</p><div class="picker" role="group" aria-label="Elige servidor">{picker}</div>{installers}</div>
</div></section>"""
    return page("/probar/", f"Prueba gratis los servidores MCP: {SITE['free_credits']} créditos · Flint by KeyFlint",
                f"Licencia gratis al momento con {SITE['free_credits']} créditos para todos los servidores MCP de KeyFlint. Sin tarjeta.", body)


def home() -> str:
    cards = "\n".join(mcp_card(m) for m in MCPS)
    clients = "".join(f'<li>{brand(ic)}<span>{e(n)}</span></li>' for _, n, ic in MARQUEE) + \
        f'<li>{icon("plug")}<span>Cualquier cliente MCP</span></li>'
    feats = [
        ("key", "Una licencia para todo", "La misma clave funciona en todos los servidores. Sin cuentas ni contraseñas que recordar."),
        ("gauge", "Pagas por uso", "Cada herramienta tiene un coste fijo en créditos. Validaciones y utilidades, gratis."),
        ("refund", "Lo que falla no se cobra", "Los ficheros no válidos se rechazan antes de cobrar y, si algo falla después, se reembolsa solo."),
        ("lock", "Tus ficheros no salen de tu equipo", "El servidor se ejecuta en tu ordenador. Solo se comunica con KeyFlint para la licencia y el saldo."),
        ("target", "Cálculo exacto al céntimo", "La misma entrada da siempre el mismo resultado matemático, sin IA inventando cifras. Cada apunte es 100% auditable."),
        ("shield", "Licencias criptográficas", "Firmadas con Ed25519 y verificadas en local en menos de un milisegundo."),
    ]
    feat_html = "".join(f'<div class="feat"><span class="tile tile-sm">{icon(i)}</span><h3>{t}</h3><p>{d}</p></div>'
                        for i, t, d in feats)
    steps = [
        ("key", "Consigue tu licencia", f"{SITE['free_credits']} créditos gratis o un plan de pago. Llega a tu correo en segundos."),
        ("download", "Instala en tu cliente", "Un clic en Claude Desktop, Cursor y VS Code. Un comando en Claude Code y Codex. Copiar y pegar en Antigravity y Windsurf."),
        ("chat", "Pídeselo a tu agente", "En lenguaje natural. El agente elige la herramienta y te dice lo que cuesta."),
    ]
    steps_html = "".join(f'<li class="step"><span class="tile tile-sm">{icon(i)}</span>'
                         f'<div><h3><span class="step-n">{n}</span>{t}</h3><p>{d}</p></div></li>'
                         for n, (i, t, d) in enumerate(steps, 1))
    picker, installers = install_picker()
    faq = [
        ("¿Qué es un servidor MCP?", "MCP (Model Context Protocol) es el estándar abierto con el que agentes de IA como Claude o Cursor usan herramientas externas. Un servidor MCP le da a tu agente capacidades nuevas: leer extractos bancarios, convertir ficheros contables o auditar webs."),
        ("¿Necesito saber programar?", "No. Pulsas un botón en Claude Desktop, Cursor o VS Code, o copias un bloque en Codex, Antigravity o Windsurf. Solo hay que instalar uv una vez, con un comando que te damos."),
        ("¿Cómo se cuentan los créditos?", "Cada herramienta tiene un coste fijo que el agente ve antes de usarla. Las validaciones y utilidades cuestan 0. Si una llamada falla, el crédito se devuelve automáticamente."),
        ("¿Dónde se procesan mis datos?", "En tu propio ordenador. El servidor se ejecuta en local y solo contacta con KeyFlint para verificar la licencia y descontar créditos. Tus ficheros no salen de tu equipo."),
        ("¿Funciona en Windows, macOS y Linux?", "Sí, en los tres. Los servidores se ejecutan con uv, que funciona igual en todos ellos."),
    ]
    min_price = min(p["price"] for p in SITE["packs"])
    body = f"""
<section class="hero"><div class="glow" aria-hidden="true"></div><div class="wrap hero-grid">
<div class="hero-copy">
<div class="kicker"><span class="pill"><span class="pill-dot"></span><span>Herramientas contables y servidores MCP deterministas</span></span></div>
<h1>Herramientas para tu IA que no se inventan nada</h1>
<p class="lead">{e(SITE['tagline'])} Funcionan en Claude, Cursor, VS Code, Codex, Antigravity y 10 clientes más.</p>
<div class="doors-wrap">
<div class="doors-head"><p class="doors-title">Elige tu puerta de entrada</p><span class="doors-hint">Acceso optimizado según tu operativa</span></div>
<nav class="doors" aria-label="Elige tu perfil">
<a class="door door-main" href="/asesorias/">
  <span class="door-icon">{icon("ledger")}</span>
  <span class="door-body">
    <span class="door-badge">Para Asesorías y Despachos</span>
    <strong>Extractos Norma 43 a Excel, uno a uno o por lotes</strong>
    <small>Convierte ficheros .n43 de cualquier banco español a Excel con cuadre garantizado. Valida VeriFactu y Facturae sin tocar la terminal.</small>
  </span>
  <span class="door-arr">{icon("arrow-right")}</span>
</a>
<a class="door door-tech" href="#instalar">
  <span class="door-icon">{icon("terminal")}</span>
  <span class="door-body">
    <span class="door-badge">Para Desarrolladores e IA</span>
    <strong>Servidores MCP locales para Claude, Cursor y Codex</strong>
    <small>Herramientas uvx con cálculo determinista al céntimo, licencias Ed25519 y secreto profesional en tu propia máquina.</small>
  </span>
  <span class="door-arr">{icon("arrow-right")}</span>
</a>
</nav>
</div>
<div class="cta-row"><a class="btn btn-primary btn-lg" href="/probar/">{icon("key")}Probar con {SITE['free_credits']} créditos gratis</a>
<a class="btn btn-ghost btn-lg" href="#en-vivo">{icon("arrow-right")}Ver la demo en vivo</a></div>
<ul class="assure">
<li>{icon("check")}{SITE['free_credits']} créditos gratis sin tarjeta</li><li>{icon("check")}Sin permanencia ni suscripción obligatoria</li><li>{icon("check")}Tus datos contables nunca salen de tu equipo</li></ul>
</div>
<figure class="demo glass en-video"><video controls preload="none" playsinline poster="/assets/video/flint-lanzamiento-es.webp" width="1280" height="720">
<source src="/assets/video/flint-lanzamiento-es.mp4" type="video/mp4"></video>
<figcaption class="demo-foot"><span>{icon("shield")}Salida real de Flint Bank, dos ejecuciones: mismo hash</span><span class="tabnum nowrap">70&nbsp;s</span></figcaption></figure>
</div></section>

<section class="clients" aria-label="Clientes compatibles"><div class="wrap clients-in">
<p class="clients-title">Compatible con</p><div class="marquee"><div class="marquee-track"><ul class="client-list">{clients}</ul><ul class="client-list" aria-hidden="true">{clients}</ul></div></div></div></section>

{live_demo()}

<section class="section" id="catalogo"><div class="wrap">
<div class="section-head"><p class="eyebrow">Catálogo</p><h2>Servidores listos para trabajo real</h2>
<p class="lead-sm">Cada servidor resuelve una tarea de principio a fin y valida los datos igual que el programa de destino.</p></div>
<div class="grid-3">{cards}</div>
</div></section>

<section class="section alt"><div class="wrap">
<div class="section-head"><p class="eyebrow">Por qué Flint</p><h2>Pensados para producción, no para demos</h2></div>
<div class="feat-grid">{feat_html}</div>
</div></section>
{seal(compact=True)}
<section class="section alt" id="lote"><div class="wrap install-grid">
<div class="section-head left"><p class="eyebrow">Modo Carpeta Vigilada · Sin abrir el chat</p>
<h2>Procesa 50 extractos Norma 43 o facturas XML de golpe</h2>
<p class="lead-sm">¿No quieres ir uno por uno en el chat? Arrastra todos los ficheros <code>.n43</code>, <code>.c43</code> y <code>.xml</code> del mes al procesador del navegador y descarga un <code>resumen-flint.csv</code> listo para abrir en Excel. Sin terminal.</p>
<div class="cta-row"><a class="btn btn-primary btn-lg" href="/lote/">{icon("download")}Abrir el procesador por lotes</a></div>
<ul class="checks"><li>{icon("check")}<span>¿Prefieres terminal? Con <code>--vigilar</code> procesa cada fichero nuevo en cuanto cae en la carpeta</span></li><li>{icon("check")}<span>Guarda el informe auditable <code>.flint.json</code> junto a cada extracto</span></li><li>{icon("check")}<span>Plan Despacho desde 49 €/mes: <a href="/precios/#despacho"><b class="nowrap">2.500 créditos al mes</b></a>, sin permanencia</span></li></ul></div>
<div class="card-flat"><p class="small"><b>Windows (PowerShell)</b> — procesa la carpeta actual:</p>
{code_block("lote-ps", f"irm {SITE['url']}/lote.ps1 | iex", "PowerShell")}
<p class="small"><b>macOS y Linux</b> — procesa o deja vigilando una carpeta:</p>
{code_block("lote-sh", f"curl -LsSf {SITE['url']}/lote.sh | sh -s -- ./extractos --vigilar", "Terminal")}</div>
</div></section>

<section class="section" id="instalar"><div class="wrap install-grid">
<div class="section-head left"><p class="eyebrow">Instalación</p><h2>Elige servidor y cliente. Copia. Listo.</h2>
<p class="lead-sm">Pega tu licencia y todos los fragmentos se rellenan solos. En Claude Desktop, Cursor y VS Code basta un clic.</p>
<ol class="steps">{steps_html}</ol></div>
<div class="install-card glass">{quick_install()}<p class="quick-or muted small">o elige servidor y cliente</p><div class="picker" role="group" aria-label="Elige servidor">{picker}</div>{installers}</div>
</div></section>

<section class="section alt"><div class="wrap faq-grid">
<div class="section-head left"><p class="eyebrow">Preguntas frecuentes</p><h2>Lo que suelen preguntarnos</h2>
<p class="lead-sm">¿Otra duda? Escríbenos a <a href="{SITE['contact']}">{e(CONTACT)}</a> y te respondemos en un día laborable.</p></div>
<div class="faq">{faq_html(faq)}</div>
</div></section>

<section class="section"><div class="wrap"><div class="cta-band">
<div><h2>Empieza gratis hoy</h2><p class="lead-sm">{SITE['free_credits']} créditos para probar cualquier servidor. Recargas desde {SITE['topup']['min']} € o Pro a {money(min_price)}&nbsp;$/mes.</p></div>
<div class="cta-row"><a class="btn btn-primary btn-lg" href="/precios/">Ver planes</a><a class="btn btn-ghost btn-lg" href="/empezar/">Leer la guía</a></div>
</div></div></section>"""
    ld = [
        {"@context": "https://schema.org", "@type": "ItemList", "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "url": f"{SITE['url']}/{m['slug']}/", "name": m["name"]}
            for i, m in enumerate(MCPS)]},
        faq_ld(faq),
    ]
    return page("/", f"{SITE['name']}: servidores MCP para Claude, Cursor y agentes de IA", SITE["description"], body, ld)


def mcp_page(m: dict) -> str:
    s = m["slug"]
    rows = "".join(
        f'<tr><td><code>{e(t)}</code></td><td><span class="credit{" free" if c == "0" else ""}">'
        f'{"Gratis" if c == "0" else e(c) + " cr"}</span></td><td>{e(d)}</td></tr>' for t, c, d in m["tools"])
    prompts = "".join(
        f'<li><span class="q-ic">{icon("chat")}</span><span class="prompt-text" id="pr-{s}-{i}">{e(p)}</span>'
        f'<button type="button" class="copy icon-only" data-copy="pr-{s}-{i}" aria-label="Copiar ejemplo">{icon("copy")}</button></li>'
        for i, p in enumerate(m["prompts"]))
    facts = "".join(f'<div class="fact"><b>{e(v)}</b><span>{e(k)}</span></div>' for v, k in m["facts"])
    others = "".join(mcp_card(o) for o in MCPS if o["slug"] != s)
    body = f"""
<section class="hero hero-sm"><div class="glow" aria-hidden="true"></div><div class="wrap">
<nav class="crumbs" aria-label="Ruta"><a href="/">Inicio</a>{icon("chevron-right")}<a href="/#catalogo">Catálogo</a>{icon("chevron-right")}<span aria-current="page">{e(m['name'])}</span></nav>
<div class="mcp-hero">
<span class="tile tile-lg">{icon(m['icon'])}</span>
<div class="mcp-hero-copy"><p class="eyebrow">{e(m['category'])}</p>
<h1>{e(m['headline'])}</h1>
<p class="lead">{e(m['summary'])}</p>
<div class="cta-row"><a class="btn btn-primary btn-lg" href="#instalar">{icon("download")}Instalar</a>
<a class="btn btn-ghost btn-lg" href="/precios/">Comprar créditos</a>
<a class="btn btn-quiet btn-lg" href="{m['repo']}" rel="noopener">{icon("github")}Código</a></div>
<p class="muted small for">Para: {e(m['audience'])}</p>
</div></div>
<div class="facts">{facts}</div>
</div></section>

<section class="section"><div class="wrap detail-grid">
<div class="detail-main">
{demo_block(m)}<div class="block"><h2>Pídeselo así a tu agente</h2>
<p class="muted">Copia un ejemplo y pégalo en el chat de tu cliente.</p>
<ul class="prompts">{prompts}</ul></div>

<div class="block"><h2>Herramientas y coste</h2>
<p class="muted">El agente ve el coste de cada herramienta antes de usarla. Si una llamada falla, el crédito se devuelve.</p>
<div class="table-wrap"><table><thead><tr><th scope="col">Herramienta</th><th scope="col">Coste</th><th scope="col">Qué hace</th></tr></thead><tbody>{rows}</tbody></table></div></div>

<div class="block"><h2>Preguntas frecuentes</h2>
<div class="faq">{faq_html(m["faq"])}</div></div>
</div>
<aside class="detail-side" id="instalar" aria-label="Instalar {e(m['name'])}">
<div class="install-card glass sticky"><h2 class="h3">Instalar {e(m['name'])}</h2>{installer(m)}
<p class="muted small side-foot">¿Sin licencia? <a href="/probar/">{SITE['free_credits']} créditos gratis</a> o <a href="/precios/">elige un plan</a>.</p></div>
</aside>
</div></section>

<section class="section alt"><div class="wrap">
<div class="section-head"><p class="eyebrow">Con la misma licencia</p><h2>Otros servidores del catálogo</h2></div>
<div class="grid-2">{others}</div></div></section>"""
    ld = [
        {"@context": "https://schema.org", "@type": "SoftwareApplication", "name": f"{m['name']} MCP",
         "applicationCategory": "DeveloperApplication", "operatingSystem": "Windows, macOS, Linux",
         "description": m["summary"], "url": f"{SITE['url']}/{s}/", "keywords": ", ".join(m["keywords"]),
         "offers": {"@type": "AggregateOffer", "priceCurrency": "USD",
                    "lowPrice": 0, "highPrice": max(p["price"] for p in SITE["packs"])}},
        faq_ld(m["faq"]),
        {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Inicio", "item": SITE["url"] + "/"},
            {"@type": "ListItem", "position": 2, "name": m["name"], "item": f"{SITE['url']}/{s}/"}]},
    ]
    title = f"{m['name']} MCP: {m['headline'][0].lower()}{m['headline'][1:]}"
    return page(f"/{s}/", title, m["summary"][:158], body, ld)


ROI_TASKS = [  # (clave, (texto ES, texto EN), créditos por unidad, unidades/mes, min a mano, min de revisión) · costes = tabla de uso
    ("n43", ("Conciliar extractos Norma 43 (leer + conciliar)", "Reconcile Norma 43 bank statements (parse + reconcile)"), 4, 20, 30, 5),
    ("diario", ("Convertir diarios contables (validar + convertir)", "Convert accounting journals (validate + convert)"), 3, 10, 20, 3),
    ("web", ("Auditar webs (SEO completo)", "Audit websites (full SEO)"), 3, 10, 30, 5),
]


def roi_calc() -> str:
    """Calculadora de ahorro con las cifras del visitante. Coste por crédito = recarga mínima (sin bonus)."""
    tp = SITE["topup"]
    cfg = {"eur_per_credit": round(1 / tp["rate"], 4), "tasks": {k: [c, n, a, r] for k, _, c, n, a, r in ROI_TASKS}}
    opts = "".join(f'<option value="{k}">{e(L(*t))}</option>' for k, t, *_ in ROI_TASKS)
    k0, _, c0, n0, a0, r0 = ROI_TASKS[0]
    field = lambda name, label, val, suf, mx: (f'<label class="demo-field"><span>{label}</span><span class="roi-in">'
                                               f'<input type="number" name="{name}" value="{val}" min="0" max="{mx}" step="1" inputmode="numeric">'
                                               f'<em>{suf}</em></span></label>')
    return f"""<section class="section" id="{L("ahorro", "savings")}"><div class="wrap narrow">
<div class="section-head"><p class="eyebrow">{L("Calculadora de ahorro", "Savings calculator")}</p><h2>{L("¿Cuánto te cuesta hoy hacerlo a mano?", "What does doing it by hand cost you today?")}</h2>
<p class="lead-sm">{L(f'Pon tus cifras. Comparamos tu tiempo con el coste en créditos al precio de la recarga mínima ({money(1 / tp["rate"])} € por crédito).', f'Enter your numbers. We compare your time with the credit cost at the minimum top-up price (€{1 / tp["rate"]:.2f} per credit).')}</p></div>
<form class="glass roi" data-roi='{e(json.dumps(cfg))}' novalidate>
<label class="demo-field"><span>{L("Tarea", "Task")}</span><select name="task">{opts}</select></label>
<div class="roi-grid">
{field("n", L("Cuántas al mes", "How many per month"), n0, L("/mes", "/mo"), 10000)}
{field("manual", L("Minutos a mano, cada una", "Minutes by hand, each"), a0, "min", 600)}
{field("review", L("Minutos de revisión con Flint", "Minutes reviewing with Flint"), r0, "min", 600)}
{field("rate", L("Coste de una hora de trabajo", "Cost of one hour of work"), 20, "€/h", 500)}
</div>
<div class="roi-out" aria-live="polite">
<div><span class="muted small">{L("Horas que recuperas", "Hours you get back")}</span><b data-roi-hours>—</b></div>
<div><span class="muted small">{L("A mano te cuesta", "By hand it costs")}</span><b data-roi-manual>—</b></div>
<div><span class="muted small">{L("Con Flint", "With Flint")}</span><b data-roi-flint>—</b><span class="muted small" data-roi-credits></span></div>
<div class="roi-save"><span class="small">{L("Ahorro al mes", "Monthly savings")}</span><b data-roi-save>—</b></div>
</div>
<p class="muted small">{L(f'Estimación con tus datos: incluye el tiempo de revisión y el coste en créditos (<span data-roi-cpu>{c0}</span> por unidad), no el de instalar. <a href="{U("balance")}#recargar">Recarga desde {tp["min"]} €</a> o empieza con <a href="{U("try")}">{SITE["free_credits"]} créditos gratis</a>.', f'Estimate from your numbers: includes review time and credit cost (<span data-roi-cpu>{c0}</span> per unit), not setup. <a href="{U("balance")}#recargar">Top up from €{tp["min"]}</a> or start with <a href="{U("try")}">{SITE["free_credits"]} free credits</a>.')}</p>
</form></div></section>"""


CREDITS_PER_STATEMENT = 4  # leer (1) + conciliar (3) un extracto Norma 43


def despacho_plans() -> str:
    """Plan Despacho (suscripción mensual en €) con equivalencia honesta en extractos conciliados."""
    cards = []
    for p in (p for p in SITE["packs"] if p["id"].startswith("despacho")):
        n = p["credits"] // CREDITS_PER_STATEMENT
        badge = '<span class="badge">Más elegido</span>' if p.get("featured") else ""
        feats = "".join(f'<li>{icon("check")}<span>{e(f)}</span></li>' for f in p.get("features", []))
        cards.append(f"""<div class="plan{' featured' if p.get('featured') else ''}">{badge}
<div class="plan-head"><h3 class="h3">{e(p['name'])}</h3><p class="muted small">{e(p['who'])}</p></div>
<p class="price">{money(p['price'])} {p.get('currency', '€')}<span class="per">{e(p.get('period', ''))}</span></p>
<p class="credits">{money(p['credits'])} créditos al mes<span class="muted"> · ≈ {money(n)} extractos conciliados</span></p>
<a class="btn {'btn-primary' if p.get('featured') else 'btn-ghost'} btn-block" href="{e(p['checkout'])}" rel="nofollow">Contratar {e(p['name'])}</a>
<p class="muted small">{e(p.get('billing', ''))}</p>
<ul class="checks">{feats}</ul></div>""")
    return f"""<section class="section tight" id="despacho"><div class="wrap">
<div class="section-head center"><p class="eyebrow">Plan Despacho</p><h2>Una cuota fija para todo el despacho</h2>
<p class="lead-sm">Créditos nuevos cada mes, factura con NIF y sin permanencia. Leer y conciliar un extracto son {CREDITS_PER_STATEMENT} créditos; lo que falla no se cobra.</p></div>
<div class="plans">{''.join(cards)}</div>
<p class="muted small center">¿Primero quieres verlo? <a href="/probar/">{SITE['free_credits']} créditos gratis, sin tarjeta</a> · <a href="/confianza/">Protección de datos y encargo de tratamiento (art. 28)</a> · <a href="/asesorias/#alta">Alta en 1 minuto</a></p>
</div></section>"""


def pricing() -> str:
    common = ["Todos los servidores del catálogo", "Reembolso automático si algo falla", "Factura con NIF/VAT"]
    cards = [f"""<div class="plan">
<div class="plan-head"><h2 class="h3">Gratis</h2><p class="muted small">Para probar sin compromiso</p></div>
<p class="price">0 €</p><p class="credits">{SITE['free_credits']} créditos</p>
<a class="btn btn-ghost btn-block" href="/probar/">Pedir licencia gratis</a>
<ul class="checks"><li>{icon("check")}<span>1 equipo</span></li><li>{icon("check")}<span>Todos los servidores</span></li><li>{icon("check")}<span>Sin tarjeta</span></li></ul></div>"""]
    tp = SITE["topup"]
    tier_li = "".join(f'<li>{icon("check")}{a} € o más: {tp["rate"] * (100 + b) // 100} cr/€{f" (+{b} %)" if b else ""}</li>' for a, b, _ in tp["tiers"])
    cards.append(f"""<div class="plan featured"><span class="badge">Sin suscripción</span>
<div class="plan-head"><h2 class="h3">Recarga libre</h2><p class="muted small">Paga solo lo que vas a usar</p></div>
<p class="price">desde {tp['min']} €</p><p class="credits">{tp['rate']} créditos por euro<span class="muted"> · hasta +40 %</span></p>
<a class="btn btn-primary btn-block" href="/saldo/#recargar">Elegir importe</a>
<ul class="checks">{tier_li}<li>{icon("check")}<span>Se suma a tu misma licencia</span></li><li>{icon("check")}<span>Los créditos no caducan</span></li></ul></div>""")
    for p in (p for p in SITE["packs"] if not p["id"].startswith("despacho")):
        curr = p.get("currency", "€")
        per100 = money(round(p["price"] / p["credits"] * 100, 2))
        feats = p.get("features") or ([p["billing"], f"{p['seats']} equipos"] + common)
        badge = '<span class="badge">Más elegido</span>' if p.get("featured") else ""
        cards.append(f"""<div class="plan{' featured' if p.get('featured') else ''}">{badge}
<div class="plan-head"><h2 class="h3">{e(p['name'])}</h2><p class="muted small">{e(p['who'])}</p></div>
<p class="price">{money(p['price'])} {curr}<span class="per">{e(p.get('period', ''))}</span></p>
<p class="credits">{money(p['credits'])} créditos{' al mes' if p.get('period') else ''}<span class="muted"> · {per100} {curr} / 100</span></p>
<a class="btn {'btn-primary' if p.get('featured') else 'btn-ghost'} btn-block" href="{p['checkout']}" rel="nofollow">Elegir {e(p['name'])}</a>
<ul class="checks">{''.join(f'<li>{icon("check")}{e(f)}</li>' for f in feats)}</ul></div>""")
    usage = [("web-intel", "Leer una web", 1), ("web-intel", "Auditoría SEO completa", 3),
             ("norma43", "Leer un extracto Norma 43", 1), ("norma43", "Conciliar un extracto con facturas", 3),
             ("contabridge", "Convertir un diario de A3 a ContaPlus", 2), ("contabridge", "Validar un diario antes de importar", 1),
             ("norma43", "Validar un IBAN, NIF o CIF", 0)]
    by = {m["slug"]: m for m in MCPS}
    urows = "".join(f'<tr><td><span class="row"><span class="row-ic">{icon(by[s]["icon"])}</span>{e(t)}</span></td>'
                    f'<td class="r"><span class="credit{" free" if c == 0 else ""}">{"Gratis" if c == 0 else f"{c} cr"}</span></td></tr>'
                    for s, t, c in usage)
    faq = [
        ("¿Cómo recibo la licencia?", "Por correo, en el email que uses al pagar, unos segundos después del pago. Si no la ves, revisa la carpeta de spam."),
        ("¿Qué pasa si se me acaban los créditos?", "La herramienta te avisa y no se cobra nada. Recarga desde 5 € en Mi saldo: los créditos se suman a la misma licencia y no tienes que tocar la configuración de Claude, Cursor ni VS Code."),
        ("¿Caducan los créditos?", "Los de una recarga, no: se quedan en tu licencia hasta que los uses. Con Pro, cada mes recibes 1.000 créditos nuevos y se gastan antes que los recargados, que se conservan."),
        ("¿Qué es un equipo?", "Cada ordenador o servidor donde usas la licencia. La licencia gratis permite 1; Pro, 3."),
        ("¿Puedo cancelar Pro?", "Sí, cuando quieras y sin permanencia, desde el enlace de gestión del correo de Stripe o escribiéndonos."),
        ("¿El precio incluye impuestos?", "Las recargas en euros llevan el IVA incluido: pagas exactamente el importe que eliges. Pro se cobra en dólares y Stripe añade los impuestos de tu país y te muestra el total en tu moneda."),
        ("¿Qué datos guardáis?", "Ninguno de tus ficheros: los servidores se ejecutan en tu equipo. Solo registramos la licencia y el consumo de créditos."),
    ]
    body = f"""
<section class="hero hero-sm center"><div class="glow" aria-hidden="true"></div><div class="wrap narrow">
<p class="eyebrow">Precios</p>
<h1>Un saldo para todos los servidores</h1>
<p class="lead">Una licencia, un saldo de créditos y un coste fijo por herramienta. Lo que falla no se cobra.</p>
</div></section>
{despacho_plans()}
<section class="section tight"><div class="wrap">
<div class="section-head center"><p class="eyebrow">Pago por uso</p><h2>Sin cuota: prueba, recarga o plan de desarrollador</h2></div>
<div class="plans">{''.join(cards)}</div>
<p class="muted small center">¿Asesoría o gestoría? <a href="/lote/">Procesa los extractos Norma 43 y XML de VERI*FACTU del mes en el navegador</a>: arrastras, pegas la licencia y descargas el resumen para Excel.</p>
<p class="muted small center fine">{icon("lock")}Pago seguro con Stripe. Recargas en euros con IVA incluido; Pro en USD más impuestos según tu país. Recibes factura y puedes añadir tu NIF/VAT. Al comprar aceptas los <a href="/terminos/">términos de servicio</a>, la <a href="https://keyflint.dev/privacy.html">política de privacidad</a> y la <a href="/reembolsos/">política de reembolso</a>.</p>
</div></section>
<section class="section alt"><div class="wrap usage-grid">
<div class="section-head left"><p class="eyebrow">Cuánto da de sí</p><h2>Coste de las tareas más habituales</h2>
<p class="lead-sm">Con una recarga de 5 € (100 créditos) lees y concilias 25 extractos Norma 43 (4 créditos cada uno).</p></div>
<div class="table-wrap card-flat"><table><thead><tr><th scope="col">Tarea</th><th scope="col" class="r">Coste</th></tr></thead><tbody>{urows}</tbody></table></div>
</div></section>
{roi_calc()}
<section class="section"><div class="wrap faq-grid">
<div class="section-head left"><p class="eyebrow">Preguntas frecuentes</p><h2>Pagos y licencias</h2></div>
<div class="faq">{faq_html(faq)}</div></div></section>"""
    ld = [{"@context": "https://schema.org", "@type": "Product", "name": "Créditos KeyFlint MCP",
           "description": "Créditos de uso para todos los servidores MCP de KeyFlint.",
           "brand": {"@type": "Brand", "name": "KeyFlint"},
           "offers": [{"@type": "Offer", "name": p["name"], "price": p["price"], "priceCurrency": "EUR" if p.get("currency", "$") == "€" else "USD",
                       "url": f"{SITE['url']}/precios/", "availability": "https://schema.org/InStock"} for p in SITE["packs"]]
                     + [{"@type": "Offer", "name": "Recarga libre", "price": SITE["topup"]["min"], "priceCurrency": "EUR",
                         "url": f"{SITE['url']}/saldo/", "availability": "https://schema.org/InStock"}]},
          faq_ld(faq)]
    return page("/precios/", "Precios de los servidores MCP · Flint by KeyFlint",
                f"Un saldo de créditos para todos los servidores MCP de KeyFlint. Recargas desde {SITE['topup']['min']} € sin suscripción o gratis con {SITE['free_credits']} créditos.",
                body, ld)


def onboarding_block() -> str:
    """Alta del despacho en un minuto (/asesorias/#alta): licencia al momento + carpeta vigilada que arranca sola."""
    folder_win, folder_nix = r"$HOME\Documents\Flint Extractos", "$HOME/Flint Extractos"
    win = (f"$env:KEYFLINT_LICENSE='{LIC_PLACEHOLDER}'; & ([scriptblock]::Create((irm {SITE['url']}/lote.ps1))) "
           f'"{folder_win}" --subcarpetas --al-iniciar')
    nix = (f"curl -LsSf {SITE['url']}/lote.sh | KEYFLINT_LICENSE='{LIC_PLACEHOLDER}' sh -s -- "
           f'"{folder_nix}" --subcarpetas --al-iniciar')
    return f"""<section class="section" id="alta"><div class="wrap narrow">
<div class="section-head"><p class="eyebrow">Alta en 1 minuto · Automático desde el primer extracto</p>
<h2>Deja el despacho conciliando solo</h2>
<p class="lead-sm">Tu correo, un comando y listo. Cada extracto que caiga en la carpeta de un cliente se procesa solo, también después de reiniciar el ordenador. Sin chat y sin abrir ningún programa.</p></div>
<ol class="alta-steps">
<li class="card"><h3><span class="step-n">1</span>Tu licencia, al momento</h3>
<form class="recover" data-trial-form novalidate>
<div class="recover-row"><input type="email" name="email" autocomplete="email" placeholder="despacho@correo.com" required aria-label="Correo del despacho">
<button class="btn btn-primary" type="submit">{icon("key")}Darme {SITE['free_credits']} créditos gratis</button></div>
<p class="lic-help" data-trial-msg aria-live="polite">Sin tarjeta. Una por correo, con 3 consejos de uso la primera semana (baja en 1 clic). ¿Ya tienes licencia? Pégala en el paso 2.</p>
</form>
<div data-trial-out hidden><p class="small">Lista y guardada en este navegador: el comando del paso 2 ya la lleva.</p>
{code_block("lic-trial", "LIC-…", "KEYFLINT_LICENSE")}</div></li>
<li class="card" data-installer='{{"slug": "alta"}}'><h3><span class="step-n">2</span>Un comando, una sola vez</h3>
<label class="lic"><span class="lic-field"><input type="text" autocomplete="off" spellcheck="false" placeholder="Pega aquí tu LIC-…" data-license aria-label="Tu licencia"><span class="lic-state" data-license-state aria-live="polite"></span></span>
<span class="lic-help"></span></label>
{code_block("alta-win", win, "Windows · PowerShell")}
{code_block("alta-nix", nix, "macOS / Linux · Terminal")}
<p class="muted small">Crea la carpeta <b>Flint Extractos</b>, instala el motor si falta y deja la vigilancia arrancando sola al iniciar sesión (Windows: carpeta Inicio; macOS: LaunchAgent; Linux: servicio de usuario). Para quitarlo, repite el comando cambiando <code>--al-iniciar</code> por <code>--quitar-inicio</code>. <a href="/lote.py">Ver el código</a>.</p></li>
<li class="card"><h3><span class="step-n">3</span>Una subcarpeta por cliente</h3>
<p>Crea dentro <code>Flint Extractos/García SL</code>, <code>Flint Extractos/Bar Pepe</code>… y suelta ahí los <code>.n43</code>, <code>.c43</code> o facturas <code>.xml</code> que descargas del banco o del cliente.</p>
<ul class="checks"><li>{icon("check")}<span>En segundos aparece el informe auditable <code>.flint.json</code> junto a cada fichero</span></li>
<li>{icon("check")}<span>Cada cliente tiene su <code>resumen-flint.csv</code>, listo para Excel</span></li>
<li>{icon("check")}<span>Si se acaba el saldo, nada se pierde: el fichero espera y se reintenta solo cada 10 minutos. <a href="/saldo/#importe=50">Recarga desde {SITE['topup']['min']} €</a></span></li></ul></li>
</ol>
<p class="muted small center">¿Prefieres no instalar nada? Usa el <a href="/lote/">procesador en el navegador</a>: la licencia ya queda guardada.</p>
</div></section>"""


def advisors_page() -> str:
    """Landing ejecutiva y optimizada para asesorías y gestorías (/asesorias/). Cada herramienta en su sitio."""
    by = {m["slug"]: m for m in MCPS}
    
    faq = [
        ("¿Tengo que saber de informática para usarlo?", "No. Puedes usar el procesador en el navegador arrastrando los extractos sin instalar nada, o dejar una carpeta vigilada en tu ordenador con un solo comando."),
        ("¿Mis datos bancarios salen del despacho?", "Con la instalación local o carpeta vigilada, no: los ficheros se procesan en tu equipo. En el navegador viajan cifrados bajo TLS a la UE, se procesan en memoria volátil y nunca se almacenan (cumplimiento estricto RGPD Art. 28)."),
        ("¿Y si la herramienta se equivoca con un apunte?", "Flint no utiliza IA para el cálculo numérico: aplica el algoritmo matemático oficial del cuaderno AEB 43. Verifica saldo inicial, sumas de debe y haber y saldo final. Error de cálculo: 0%."),
        ("¿Es compatible con ContaSol, A3 y Sage?", "Sí. Exporta ficheros de asientos directamente compatibles con ContaSol (DELSOL), plantillas de diario para A3 y hojas de cálculo normalizadas para Excel y Sage 50."),
        ("¿Cuánto cuesta?", "Empiezas con 25 créditos totalmente gratuitos. Después eliges: Plan Despacho desde 49 €/mes (2.500 créditos al mes, unos 625 extractos leídos y conciliados, sin permanencia) o recargas sueltas desde 5 € que no caducan."),
    ]
    
    body = f"""
<section class="hero"><div class="glow" aria-hidden="true"></div><div class="wrap narrow center">
<div class="kicker"><span class="pill"><span class="pill-dot"></span><span>Software para despachos contables y asesorías</span></span></div>
<h1>Conciliación bancaria Norma 43 y facturas en 1 segundo, sin picar datos</h1>
<p class="lead">Pasa extractos bancarios (.n43, .c43) y facturas XML directamente a Excel, ContaSol o A3 con 100% de cuadre matemático certificado. Sin suscripciones cautivas ni módulos costosos.</p>
<div class="cta-row center">
<a class="btn btn-primary btn-lg" href="/lote/">{icon("download")}Abrir procesador por lotes</a>
<a class="btn btn-ghost btn-lg" href="/norma43-a-excel/">{icon("table")}Demo extracto en 1 clic</a>
</div>
<ul class="assure center"><li>{icon("check")}<span>25 extractos de prueba gratis</span></li><li>{icon("check")}<span>Sin tarjeta</span></li><li>{icon("check")}<span>RGPD Art. 28 estricto</span></li><li>{icon("check")}<span>Soporte en España</span></li></ul>
</div></section>

<!-- 1. SOLUCIONES DIRECTAS: ARRIBA Y SIN ESPERAS -->
<section class="section tight" id="soluciones"><div class="wrap">
<div class="section-head"><p class="eyebrow">Herramientas Inmediatas</p><h2>Elige tu flujo de trabajo sin configurar nada</h2></div>
<div class="grid-3">
  <div class="card glass">
    <span class="tile">{icon("table")}</span>
    <h3>Norma 43 a Excel</h3>
    <p>Convierte extractos .n43 y .c43 de cualquier banco español a Excel (.csv con ; y decimales en coma) con columnas normalizadas y saldo verificado.</p>
    <div style="margin-top:auto;padding-top:16px"><a class="btn btn-primary" href="/norma43-a-excel/">{icon("table")}<span>Convertir a Excel</span></a></div>
  </div>
  <div class="card glass">
    <span class="tile">{icon("landmark")}</span>
    <h3>Norma 43 a ContaSol</h3>
    <p>Genera directamente el fichero de apuntes contables para importar en DELSOL en segundos, asignando subcuentas 572 y comprobando saldos sin teclear.</p>
    <div style="margin-top:auto;padding-top:16px"><a class="btn btn-primary" href="/norma43-a-contasol/">{icon("landmark")}<span>Procesar para ContaSol</span></a><p class="muted small" style="margin-top:8px">También para <a href="/norma43-a-a3/">a3</a> y <a href="/norma43-a-contaplus/">ContaPlus</a>.</p></div>
  </div>
  <div class="card glass">
    <span class="tile">{icon("download")}</span>
    <h3>Procesador por lotes</h3>
    <p>¿Tienes 50 extractos o facturas del mes? Arrástralos todos juntos al navegador y descarga el resumen completo unificado. Sin límite de entidades.</p>
    <div style="margin-top:auto;padding-top:16px"><a class="btn btn-primary" href="/lote/">{icon("download")}<span>Abrir por lotes</span></a></div>
  </div>
</div>
</div></section>

<!-- 2. MODO CARPETA VIGILADA (PARA DESPACHOS CON ALTO VOLUMEN) -->
<section class="section alt" id="lote"><div class="wrap install-grid">
<div class="section-head left"><p class="eyebrow">Modo Carpeta Vigilada · Cero fricción</p>
<h2>Procesa 50 extractos de golpe sin abrir ningún programa</h2>
<p class="lead-sm">Arrastra todos los ficheros <code>.n43</code>, <code>.c43</code> y <code>.xml</code> del mes al navegador, o deja una carpeta vigilada en Windows que procese cada extracto en cuanto lo guardes de la banca online.</p>
<ul class="checks">
<li>{icon("check")}<span>Windows: un comando en PowerShell y vigila la carpeta de clientes</span></li>
<li>{icon("check")}<span>Genera el informe auditable <code>.flint.json</code> junto a cada extracto</span></li>
<li>{icon("check")}<span>Plan Despacho desde 49 €/mes: <a href="/precios/#despacho"><b class="nowrap">2.500 créditos al mes</b></a>, sin permanencia</span></li>
</ul>
<div class="cta-row" style="margin-top:18px"><a class="btn btn-primary" href="/lote/">{icon("download")}<span>Abrir procesador online</span></a></div>
</div>
<div class="card-flat"><p class="small"><b>Windows (PowerShell)</b> — procesa o vigila tu carpeta de extractos:</p>
{code_block("lote-ps", f"irm {SITE['url']}/lote.ps1 | iex", "PowerShell")}
<p class="small"><b>macOS y Linux</b> — terminal:</p>
{code_block("lote-sh", f"curl -LsSf {SITE['url']}/lote.sh | sh -s -- ./extractos --vigilar", "Terminal")}</div>
</div></section>

<!-- 2b. CONECTOR ÚNICO PARA EL DESPACHO (Norma 43 + ContaBridge en una URL) -->
<section class="section" id="conector"><div class="wrap install-grid">
<div class="section-head left"><p class="eyebrow">Un solo conector · Claude, ChatGPT, Antigravity</p>
<h2>Todo el despacho con una sola URL</h2>
<p class="lead-sm">Extractos Norma 43, conciliación, facturas al diario, exportación a a3, ContaPlus, Sage 50 o ContaSol y remesas SEPA en el mismo conector. Lo añades una vez y entras con el código de 6 dígitos que te llega por correo.</p>
<ul class="checks">
<li>{icon("check")}<span><code>reconcile_movements</code>, <code>bank_to_journal</code>, <code>invoices_to_journal</code>, <code>convert_journal</code>, <code>sepa_direct_debits</code> y el resto</span></li>
<li>{icon("check")}<span>Mismos precios y créditos que cada herramienta por separado; los fallos se reembolsan</span></li>
<li>{icon("check")}<span>Claude: Ajustes → Conectores → Añadir conector personalizado → pega la URL</span></li>
</ul>
</div>
<div class="card-flat"><p class="small"><b>URL del conector</b>:</p>
{code_block("despacho-url", f"{SITE['url']}/despacho/mcp", "URL")}
<p class="small muted" style="margin-top:14px">Clientes con cabeceras (Claude Code, Cursor, VS Code): <code>Authorization: Bearer LIC-…</code> y sin OAuth.</p></div>
</div></section>

<!-- 3. SELLO DE RIGOR CONTABLE & SEGURIDAD -->
{seal(compact=True)}

<!-- 4. CALCULADORA DE RENTABILIDAD / ROI PARA EL DESPACHO -->
{roi_calc()}

<!-- 4b. PLAN DESPACHO -->
{despacho_plans()}

<!-- 5. ALTA EN 1 MINUTO: LICENCIA GRATUITA -->
{onboarding_block()}

<!-- 6. PREGUNTAS FRECUENTES -->
<section class="section alt"><div class="wrap narrow">
<div class="section-head center"><p class="eyebrow">Dudas habituales</p><h2>Preguntas frecuentes de asesorías</h2></div>
<div class="faq">{faq_html(faq)}</div>
</div></section>

<!-- 7. BANDA DE CIERRE -->
<section class="section"><div class="wrap"><div class="cta-band">
<div><h2>Prueba con los extractos de este mes</h2><p class="lead-sm">{SITE['free_credits']} créditos gratis: suficientes para probar todo el flujo de tu despacho. Sin tarjeta.</p></div>
<div class="cta-row"><a class="btn btn-primary btn-lg" href="/probar/">{icon("key")}<span>Pedir licencia gratis</span></a><a class="btn btn-ghost btn-lg" href="/norma43-a-excel/"><span>Ver demo en 1 clic</span></a></div>
</div></div></section>"""
    return page("/asesorias/", "Conciliación bancaria Norma 43 y facturas para asesorías · Flint by KeyFlint",
                "Concilia extractos bancarios Norma 43, exporta asientos para ContaSol y A3 y audita facturas electrónicas. 0% errores de cálculo y 25 créditos gratis.",
                body, [faq_ld(faq)])


def batch_page() -> str:
    """Procesador por lotes en el navegador (/lote/ y /en/batch/): misma lógica que installer/lote.py, sin terminal."""
    term = f"curl -LsSf {SITE['url']}/lote.sh | sh -s -- ./extractos --vigilar"
    costs = [("Norma 43 (.n43 .c43 .q43)", "parse_norma43", 1), (L("VERI*FACTU (.xml exportado)", "VERI*FACTU (exported .xml)"), "validate_verifactu_xml", 3),
             (L("Facturae 3.2.2 (.xml .xsig)", "Facturae 3.2.2 (.xml .xsig)"), "validate_facturae", 2)]
    crows = "".join(f'<tr><td>{e(a)}</td><td><code>{t}</code></td><td class="num">{c} cr</td></tr>' for a, t, c in costs)
    body = f"""
<section class="hero hero-sm"><div class="glow" aria-hidden="true"></div><div class="wrap narrow">
<nav class="crumbs" aria-label="{L("Ruta", "Breadcrumb")}"><a href="{U("home")}">{L("Inicio", "Home")}</a>{icon("chevron-right")}<span aria-current="page">{L("Procesar por lotes", "Batch processing")}</span></nav>
<h1>{L("Procesa todos los extractos y facturas del mes de golpe", "Process a whole month of bank statements and invoices at once")}</h1>
<p class="lead">{L("Arrastra tus ficheros Norma 43 (.n43, .c43, .q43) y XML de VERI*FACTU o Facturae, pega tu licencia y descarga el resumen para Excel. Sin instalar nada y sin abrir la terminal.", "Drop your Norma 43 statements (.n43, .c43, .q43) and VERI*FACTU or Facturae XML, paste your license and download the Excel summary. Nothing to install, no terminal.")}</p>
</div></section>
<section class="section tight"><div class="wrap narrow" data-batch>
<form class="saldo-form glass batch" data-batch-form novalidate>
<label class="lic"><span class="lic-label">{icon("key")}{L("Tu correo o licencia", "Your email or license")}</span>
<span class="lic-field"><input type="text" name="license" autocomplete="email" spellcheck="false" placeholder="{L("tu@correo.com o LIC-…", "you@company.com or LIC-…")}" required aria-describedby="lote-help" data-batch-lic></span>
<span id="lote-help" class="lic-help">{L(f'Escribe tu correo para activar <b>{SITE["free_credits"]} créditos gratis</b> al instante (o cargar tu licencia activa), o pega tu clave LIC-….', f'Enter your email to activate <b>{SITE["free_credits"]} free credits</b> instantly (or load your active license), or paste your LIC-… key.')}</span></label>
<label class="drop" data-batch-drop><input type="file" multiple accept=".n43,.c43,.q43,.csv,.pdf,.xml,.xsig" class="sr-only" data-batch-input>
<span class="tile">{icon("download")}</span><b>{L("Arrastra aquí los ficheros o haz clic para elegirlos", "Drop files here or click to choose them")}</b>
<span class="muted small">.n43 · .c43 · .q43 · .csv · .pdf · .xml · .xsig · {L("hasta 10 MB cada uno", "up to 10 MB each")}</span></label>
<div class="sample-bar"><button type="button" class="btn-sample" data-batch-sample>{icon("refresh")}<span>{L("Cargar extracto de prueba (demo en 1 clic)", "Load sample bank statement (1-click demo)")}</span></button></div>
<div class="tw batch-list" data-batch-list hidden><table class="uso-t"><thead><tr><th>{L("Fichero", "File")}</th><th>{L("Tipo", "Type")}</th><th>{L("Estado", "Status")}</th><th>{L("Detalle", "Detail")}</th><th class="num"></th></tr></thead><tbody data-batch-rows></tbody></table></div>
<div class="batch-actions"><button class="btn btn-primary btn-lg" type="submit" data-batch-go disabled>{icon("refresh")}<span>{L("Procesar", "Process")}</span></button>
<button class="btn btn-ghost" type="button" data-batch-stop hidden>{L("Detener", "Stop")}</button>
<button class="btn btn-quiet" type="button" data-batch-clear hidden>{L("Vaciar lista", "Clear list")}</button>
<span class="muted small tabnum" data-batch-cost aria-live="polite"></span></div>
<p class="note" data-batch-msg aria-live="polite" hidden>{icon("info")}<span></span></p>
<div class="batch-out" data-batch-out hidden><h2 class="h4">{icon("check")}{L("Resultados listos", "Results ready")}</h2>
<p class="muted small">{L("El resumen se abre directamente en Excel (separador ; y coma decimal). El ZIP incluye además el informe auditable .flint.json de cada fichero.", "The summary opens straight in Excel. The ZIP also holds the auditable .flint.json report of each file.")}</p>
<div class="cta-row"><button class="btn btn-primary" type="button" data-batch-csv>{icon("table")}{L("Descargar resumen Excel (.csv)", "Download Excel summary (.csv)")}</button>
<button class="btn btn-ghost" type="button" data-batch-zip>{icon("download")}{L("Descargar todo (.zip)", "Download everything (.zip)")}</button>
<a class="btn btn-primary" href="{U("balance")}#recargar">{icon("arrow-right")}{L("Recargar saldo (desde 5 €)", "Top up credits (from €5)")}</a>
<a class="btn btn-quiet" href="{U("pricing")}">{L("Ver precios", "View pricing")}</a></div></div>
</form>
<div class="install-grid batch-info">
<div><h2 class="h3">{L("Qué hace con cada fichero", "What it does with each file")}</h2>
<ul class="checks"><li>{icon("check")}<span>{L("Norma 43: comprueba totales y saldos como el banco y saca IBAN, movimientos y saldo inicial y final.", "Norma 43: checks totals and balances the way the bank does and returns IBAN, movements and opening and closing balance.")}</span></li>
<li>{icon("check")}<span>{L("XML de VERI*FACTU: valida contra el XSD de la AEAT y audita huellas y encadenamiento.", "VERI*FACTU XML: validates against the AEAT XSD and audits fingerprints and chaining.")}</span></li>
<li>{icon("check")}<span>{L("Facturae: XSD, cuadre de importes, NIF, DIR3 y si está firmada.", "Facturae: XSD, amount checks, NIF, DIR3 and whether it is signed.")}</span></li>
<li>{icon("check")}<span>{L("Envía los bytes exactos: respeta Ñ y acentos de los ficheros CP850/Latin-1 y las firmas XAdES.", "Sends the exact bytes: keeps CP850/Latin-1 accents and XAdES signatures intact.")}</span></li>
<li>{icon("check")}<span>{L("Si un fichero falla, no se cobra. Puedes reintentar solo los pendientes.", "If a file fails, it is not charged. Retry only the pending ones.")}</span></li></ul></div>
<div><h2 class="h3">{L("Cuánto cuesta", "What it costs")}</h2>
<div class="tw uso"><table class="uso-t"><thead><tr><th>{L("Fichero", "File")}</th><th>{L("Herramienta", "Tool")}</th><th class="num">{L("Créditos", "Credits")}</th></tr></thead><tbody>{crows}</tbody></table></div>
<p class="muted small">{L('Para despachos: <a href="/saldo/#importe=100"><span class="nowrap">100 € → 2.800 créditos</span> <span class="nowrap">(+40 %)</span></a>, sin caducidad.', 'Credits never expire. <a href="/en/balance/">Top up from €5</a>.')}</p>
<p class="muted small">{L("Privacidad: cada fichero viaja cifrado a nuestro servidor, se procesa en memoria y no se guarda. Solo registramos herramienta, resultado y créditos.", "Privacy: each file travels encrypted to our server, is processed in memory and never stored. We only log tool, result and credits.")}</p></div>
</div>
<div class="card-flat batch-term"><p class="small"><b>{L("¿Prefieres dejar una carpeta vigilada?", "Prefer a watched folder?")}</b> {L("El mismo proceso por terminal procesa cada fichero nuevo en cuanto cae en la carpeta:", "The same process from a terminal handles each new file as soon as it lands in the folder:")}</p>
{code_block("lote-sh", term, "Terminal")}
<p class="muted small">Windows: <code>irm {SITE['url']}/lote.ps1 | iex</code></p></div>
{bank_links_section() if _LANG[-1] == "es" else ""}
</div></section>
<script defer src="/assets/lote.js?v={VERSION}"></script>"""
    return page(U("batch"), L("Procesador por lotes Norma 43, VERI*FACTU y Facturae · Flint by KeyFlint", "Batch processor for Norma 43, VERI*FACTU and Facturae · Flint by KeyFlint"),
                L("Arrastra extractos Norma 43 y XML de VERI*FACTU o Facturae, pega tu licencia y descarga el resumen .csv para Excel. Sin instalar nada.",
                  "Drop Norma 43 statements and VERI*FACTU or Facturae XML, paste your license and download the Excel .csv summary. Nothing to install."),
                body, lang=_LANG[-1])


def en_batch() -> str:
    with lang_ctx("en"):
        return batch_page()


def norma43_excel_page() -> str:
    """Landing SEO de alta intención: /norma43-a-excel/."""
    faq = [
        ("¿Qué entidades bancarias generan ficheros Norma 43 (.n43 o .c43)?",
         "Prácticamente todas las entidades financieras que operan en España: Banco Santander, BBVA, CaixaBank, Sabadell, Bankinter, Unicaja, Ibercaja, Kutxabank, Abanca, Cajamar, Laboral Kutxa, Deutsche Bank España y cooperativas de crédito."),
        ("¿Por qué Excel no abre bien los ficheros .n43 directamente?",
         "Norma 43 no es una hoja de cálculo ni un CSV común: es un estándar bancario español de registros de longitud fija (80 caracteres por línea) con codificación bancaria CP850/Latin-1. Si lo abres directamente en Excel, todo el contenido queda pegado en una única columna ilegible. Flint lo procesa de forma nativa y genera un fichero CSV con delimitador de punto y coma (;) y coma decimal (,) listo para filtrar, ordenar y conciliar en Excel en español."),
        ("¿Cómo comprueba Flint el cuadre bancario del extracto?",
         "Flint aplica el algoritmo matemático oficial del cuaderno AEB 43: verifica el registro 11 (saldo inicial), suma algebraicamente los movimientos de los registros 22 y 23 (debe y haber) y comprueba que coincidan de forma exacta con el registro 33 (saldo final). Si falta un movimiento o el fichero está cortado, te avisa antes de que descuadre tu contabilidad."),
        ("¿Mis datos bancarios están protegidos (RGPD)?",
         "Totalmente. Los ficheros viajan cifrados bajo TLS, se procesan exclusivamente en memoria volátil y se descartan inmediatamente tras generar el resultado. Nunca se almacenan ni se usan para entrenar modelos de IA (RGPD Art. 28). Para despachos con máxima exigencia de secreto profesional, el modo local con uvx procesa el extracto 100% dentro de tu propio ordenador sin que salga a internet."),
        ("¿Cuánto cuesta convertir extractos bancarios a Excel?",
         "Comienzas con 25 créditos totalmente gratuitos (unos 25 extractos bancarios, sin tarjeta). Después puedes recargar saldo libremente desde 5 € (unos 5 céntimos por extracto) sin cuotas mensuales fijas obligatorias: pagas solo lo que procesas y los créditos no caducan."),
    ]
    term = f"curl -LsSf {SITE['url']}/lote.sh | sh -s -- ./extractos --vigilar"
    body = f"""
<section class="hero"><div class="glow" aria-hidden="true"></div><div class="wrap narrow">
<nav class="crumbs" aria-label="Ruta"><a href="/">Inicio</a>{icon("chevron-right")}<span aria-current="page">Norma 43 a Excel</span></nav>
<h1>Convertir extractos bancarios Norma 43 a Excel online</h1>
<p class="lead">Pasa extractos bancarios (.n43, .c43, .q43) de cualquier banco español a Excel o CSV limpio con cuadre de saldos automático. Sin programas pesados, sin errores de tecleo y con 25 conversiones gratuitas.</p>
</div></section>

<section class="section tight"><div class="wrap narrow" data-batch>
<form class="saldo-form glass batch" data-batch-form novalidate>
<label class="lic"><span class="lic-label">{icon("key")}Tu correo o licencia</span>
<span class="lic-field"><input type="text" name="license" autocomplete="email" spellcheck="false" placeholder="tu@correo.com o LIC-…" required aria-describedby="n43-help" data-batch-lic></span>
<span id="n43-help" class="lic-help">Escribe tu correo para activar <b>25 créditos gratis</b> al instante (sin salir de aquí) o pega tu clave LIC-….</span></label>

<label class="drop" data-batch-drop><input type="file" multiple accept=".n43,.c43,.q43,.csv,.pdf" class="sr-only" data-batch-input>
<span class="tile">{icon("download")}</span><b>Arrastra aquí tus extractos bancarios (.n43, .c43 o PDF digital) o haz clic para elegirlos</b>
<span class="muted small">Santander, BBVA, CaixaBank, Sabadell, Bankinter… hasta 10 MB cada uno</span></label>
<div class="sample-bar"><button type="button" class="btn-sample" data-batch-sample>{icon("refresh")}<span>Cargar extracto de prueba (demo en 1 clic)</span></button></div>

<div class="tw batch-list" data-batch-list hidden><table class="uso-t"><thead><tr><th>Fichero</th><th>Tipo</th><th>Estado</th><th>Detalle</th><th class="num"></th></tr></thead><tbody data-batch-rows></tbody></table></div>
<div class="batch-actions"><button class="btn btn-primary btn-lg" type="submit" data-batch-go disabled>{icon("refresh")}<span>Convertir a Excel</span></button>
<button class="btn btn-ghost" type="button" data-batch-stop hidden>Detener</button>
<button class="btn btn-quiet" type="button" data-batch-clear hidden>Vaciar lista</button>
<span class="muted small tabnum" data-batch-cost aria-live="polite"></span></div>
<p class="note" data-batch-msg aria-live="polite" hidden>{icon("info")}<span></span></p>

<div class="batch-out" data-batch-out hidden><h2 class="h4">{icon("check")}Extractos convertidos con éxito</h2>
<p class="muted small">Descarga tu resumen listo para abrir en Excel en español (separador ; y coma decimal) o el archivo comprimido ZIP con el informe auditable de cada cuenta.</p>
<div class="cta-row"><button class="btn btn-primary" type="button" data-batch-csv>{icon("table")}Descargar resumen Excel (.csv)</button>
<button class="btn btn-ghost" type="button" data-batch-zip>{icon("download")}Descargar todo (.zip)</button>
<a class="btn btn-primary" href="/saldo/#recargar">{icon("arrow-right")}Recargar créditos (desde 5 €)</a>
<a class="btn btn-quiet" href="/precios/">Ver precios</a></div></div>
</form>

<div class="install-grid batch-info">
<div><h2 class="h3">Estructura del libro Excel generado</h2>
<p class="small muted">Cada fila del fichero Excel corresponde a un movimiento bancario individual, con las columnas normalizadas para su explotación contable:</p>
<ul class="checks">
<li>{icon("check")}<span><b>Fecha operación y Fecha valor:</b> formato estándar AAAA-MM-DD para filtrado cronológico.</span></li>
<li>{icon("check")}<span><b>Concepto común y propio:</b> código de operación bancaria normalizado según el cuaderno 43.</span></li>
<li>{icon("check")}<span><b>Concepto detallado (Registros 23):</b> descripción completa del movimiento (hasta 5 líneas de detalle).</span></li>
<li>{icon("check")}<span><b>Importe (€):</b> debe (-) y haber (+) separados con signo contable exacto.</span></li>
<li>{icon("check")}<span><b>Saldo final comprobado:</b> cuadre matemático garantizado con el saldo bancario real.</span></li>
</ul></div>

<div><h2 class="h3">Por qué usar Flint frente a otros métodos</h2>
<div class="tw uso"><table class="uso-t"><thead><tr><th>Método</th><th>Tiempo</th><th>Riesgo error</th><th>Coste</th></tr></thead>
<tbody>
<tr><td>Picar a mano en Excel</td><td>20 min/cuenta</td><td>Muy alto</td><td>Horas perdidas</td></tr>
<tr><td>Software tradicional de escritorio</td><td>5 min/cuenta</td><td>Medio</td><td>300 €/año + licencias</td></tr>
<tr><td><b>Flint Norma 43 a Excel</b></td><td><b>1 segundo</b></td><td><b>0% (AEB 43)</b></td><td><b>25 gratis · Recarga libre desde 5 €</b></td></tr>
</tbody></table></div>
<p class="muted small">Garantía de privacidad: procesamiento en memoria volátil bajo RGPD Art. 28, sin guardar tus ficheros. <a href="/confianza/">Ver informe de confianza</a>.</p></div>
</div>

<div class="card-flat batch-term"><p class="small"><b>¿Gestionas decenas de extractos bancarios al mes en tu despacho?</b> Deja una carpeta vigilada en tu ordenador: cualquier extracto bancario que guardes se convertirá a Excel automáticamente en segundo plano:</p>
{code_block("lote-sh", term, "Terminal")}
<p class="muted small">Windows (PowerShell): <code>irm {SITE['url']}/lote.ps1 | iex</code></p></div>

<div class="faq" style="margin-top:40px"><h2 class="h3" style="margin-bottom:20px">Preguntas frecuentes sobre Norma 43 a Excel</h2>{faq_html(faq)}</div>
</div></section>
<script defer src="/assets/lote.js?v={VERSION}"></script>"""
    return page("/norma43-a-excel/", "Convertir extractos Norma 43 (.n43, .c43) a Excel online · Flint by KeyFlint",
                "Convierte ficheros bancarios Norma 43 a Excel (.csv delimitado por punto y coma) gratis y al instante. Cuadre bancario matemático según cuaderno AEB 43.",
                body, [faq_ld(faq)])


N43_TARGETS = {
    "contasol": {
        "path": "/norma43-a-contasol/", "program": "ContaSol (DELSOL)", "short": "ContaSol", "file": "APU.ods",
        "import": "En ContaSol: <b>Utilidades &gt; Importaciones</b>, importación Excel/Calc de <b>Apuntes</b>, y eliges el fichero APU.ods.",
        "title": "Pasar extractos Norma 43 a ContaSol (APU.ods) · Flint by KeyFlint",
        "desc": "Convierte extractos bancarios Norma 43 (.n43, .c43) en el fichero de apuntes APU.ods que importa ContaSol, con la subcuenta 572 de tu banco y sin picar asientos.",
        "faq_extra": ("¿Qué fichero genera para ContaSol?", "Un APU.ods con el formato de importación Excel/Calc de apuntes de ContaSol (columnas A a Q). Se importa en Utilidades > Importaciones. Antes de pasarlo a una empresa real, haz una primera importación en una empresa de pruebas."),
    },
    "a3": {
        "path": "/norma43-a-a3/", "program": "a3ASESOR, a3ECO y a3CON", "short": "A3", "file": "SUENLACE.DAT",
        "import": "En a3: <b>Utilidades &gt; Enlace contable / Importar</b> el fichero SUENLACE.DAT (apuntes tipo 0, formato de 5 dígitos por defecto).",
        "title": "Importar extractos Norma 43 en a3 (SUENLACE.DAT) · Flint by KeyFlint",
        "desc": "Convierte extractos bancarios Norma 43 (.n43, .c43) en un SUENLACE.DAT listo para importar en a3ASESOR, a3ECO o a3CON, con la subcuenta 572 del banco.",
        "faq_extra": ("¿Qué fichero genera para a3?", "Un SUENLACE.DAT con apuntes tipo 0, el formato estándar de enlace contable de a3ASESOR, a3ECO y a3CON. Por defecto usa el código de empresa 00001; si tu empresa en a3 tiene otro código, cámbialo antes de importar."),
    },
    "contaplus_ascii": {
        "path": "/norma43-a-contaplus/", "program": "Sage ContaPlus y Sage 50", "short": "ContaPlus", "file": "XDiario.txt",
        "import": "En ContaPlus: <b>Útiles &gt; Importación de ficheros ASCII</b>, eliges Diario y el fichero XDiario.txt.",
        "title": "Pasar extractos Norma 43 a ContaPlus (XDiario) · Flint by KeyFlint",
        "desc": "Convierte extractos bancarios Norma 43 (.n43, .c43) en un diario XDiario.txt para importar en Sage ContaPlus, con la subcuenta 572 del banco.",
        "faq_extra": ("¿Qué fichero genera para ContaPlus?", "Un XDiario.txt de ancho fijo, el formato de importación ASCII de diario de Sage ContaPlus. Si usas Sage 50 con importación CSV, Flint también puede generar el diario en CSV desde Claude o Cursor."),
    },
}


def norma43_target_page(target: str) -> str:
    """Landing SEO + conversor real: Norma 43 -> fichero de importación del programa contable (contabridge bank_to_journal)."""
    t = N43_TARGETS[target]
    short, prog, fname = t["short"], t["program"], t["file"]
    faq = [
        (f"¿Cómo se importan los extractos bancarios en {short}?",
         f"Flint convierte cada movimiento del extracto en un asiento: abono, Debe banco / Haber contrapartida; cargo, al revés. Descargas {fname} y lo importas. {t['import'].replace('<b>', '').replace('</b>', '').replace('&gt;', '>')}"),
        t["faq_extra"],
        ("¿Qué pasa con los movimientos que no sabe a qué cuenta van?",
         "Van a la 555 (partidas pendientes de aplicación) y se marcan para revisión. Flint nunca adivina una contrapartida. Desde Claude o Cursor puedes darle reglas (por ejemplo, IBERDROLA a la 628) y se aplican siempre igual."),
        ("¿Cuánto cuesta?",
         f"Convertir un extracto son 3 créditos (unos 0,15 €). Si el fichero falla, no se cobra. Con la prueba gratis tienes {SITE['free_credits']} créditos y el Plan Despacho empieza en 49 €/mes."),
        ("¿Puedo procesar todas las empresas del despacho a la vez?",
         "Sí. Arrastra todos los extractos del mes: los asientos se numeran seguidos y descargas un ZIP con un fichero por extracto. La carpeta vigilada hace lo mismo sin abrir el navegador."),
    ]
    body = f"""
<section class="hero"><div class="glow" aria-hidden="true"></div><div class="wrap narrow">
<nav class="crumbs" aria-label="Ruta"><a href="/">Inicio</a>{icon("chevron-right")}<span aria-current="page">Norma 43 a {e(short)}</span></nav>
<h1>Importar extractos Norma 43 en {e(short)} sin picar asientos</h1>
<p class="lead">Arrastra los extractos bancarios (.n43, .c43) de cualquier banco español y descarga el {e(fname)} para {e(prog)}. Saldos comprobados como lo hace el banco, la subcuenta 572 que tú elijas y lo dudoso a la 555 para revisar.</p>
</div></section>

<section class="section tight"><div class="wrap narrow" data-batch data-batch-target="{target}">
<form class="saldo-form glass batch" data-batch-form novalidate>
<label class="lic"><span class="lic-label">{icon("key")}Tu correo o licencia</span>
<span class="lic-field"><input type="text" name="license" autocomplete="email" spellcheck="false" placeholder="tu@correo.com o LIC-…" required aria-describedby="t-help" data-batch-lic></span>
<span id="t-help" class="lic-help">Escribe tu correo para activar <b>{SITE['free_credits']} créditos gratis</b> al instante (o cargar tu licencia activa), o pega tu clave LIC-….</span></label>
<label class="lic"><span class="lic-label">{icon("landmark")}Subcuenta del banco</span>
<span class="lic-field"><input type="text" name="bank" inputmode="numeric" autocomplete="off" value="57200001" pattern="57[0-9]{{2,10}}" required data-batch-bank aria-describedby="b-help"></span>
<span id="b-help" class="lic-help">La 572 de la cuenta bancaria en {e(short)} (con los dígitos de tu plan de cuentas).</span></label>

<label class="drop" data-batch-drop><input type="file" multiple accept=".n43,.c43,.q43,.csv,.pdf" class="sr-only" data-batch-input>
<span class="tile">{icon("download")}</span><b>Arrastra aquí tus extractos Norma 43 (.n43, .c43), CSV bancarios (.csv) o PDF digitales</b>
<span class="muted small">Vista previa instantánea de movimientos · De cualquier banco o pasarela · hasta 10 MB</span></label>
<div class="sample-bar"><button type="button" class="btn-sample" data-batch-sample>{icon("refresh")}<span>Cargar extracto de prueba</span></button></div>

<div class="tw batch-list" data-batch-list hidden><table class="uso-t"><thead><tr><th>Fichero</th><th>Tipo</th><th>Estado</th><th>Detalle</th><th class="num"></th></tr></thead><tbody data-batch-rows></tbody></table></div>
<div class="batch-actions"><button class="btn btn-primary btn-lg" type="submit" data-batch-go disabled>{icon("refresh")}<span>Convertir para {e(short)}</span></button>
<button class="btn btn-ghost" type="button" data-batch-stop hidden>Detener</button>
<button class="btn btn-quiet" type="button" data-batch-clear hidden>Vaciar lista</button>
<span class="muted small tabnum" data-batch-cost aria-live="polite"></span></div>
<p class="note" data-batch-msg aria-live="polite" hidden>{icon("info")}<span></span></p>

<div class="batch-out" data-batch-out hidden><h2 class="h4">{icon("check")}Asientos generados</h2>
<p class="muted small">Un extracto: descargas {e(fname)}. Varios: un ZIP con un fichero por extracto, con los asientos numerados seguidos. Revisa los marcados como REVISAR_555 antes de cerrar.</p>
<div class="cta-row"><button class="btn btn-primary" type="button" data-batch-csv>{icon("download")}Descargar {e(fname)}</button>
<button class="btn btn-ghost" type="button" data-batch-zip>{icon("table")}Todo con resumen (.zip)</button>
<a class="btn btn-quiet" href="/precios/#despacho">Plan Despacho</a></div></div>
</form>

<div class="install-grid batch-info">
<div><h2 class="h3">Cómo importarlo en {e(short)}</h2>
<ol class="steps" style="margin-top:14px">
<li class="step"><span class="tile tile-sm">{icon("download")}</span><div><h3><span class="step-n">1</span>Arrastra los extractos</h3><p>Los .n43 o .c43 que descargas de la banca online de cada cliente.</p></div></li>
<li class="step"><span class="tile tile-sm">{icon("refresh")}</span><div><h3><span class="step-n">2</span>Descarga {e(fname)}</h3><p>Flint comprueba los saldos del extracto y genera un asiento por movimiento.</p></div></li>
<li class="step"><span class="tile tile-sm">{icon("landmark")}</span><div><h3><span class="step-n">3</span>Impórtalo</h3><p>{t['import']} La primera vez, pruébalo en una empresa de pruebas.</p></div></li>
</ol></div>
<div><h2 class="h3">Qué cuesta</h2>
<div class="tw uso"><table class="uso-t"><thead><tr><th>Concepto</th><th class="num">Créditos</th></tr></thead>
<tbody><tr><td>Convertir un extracto a {e(short)}</td><td class="num">3 cr</td></tr>
<tr><td>Fichero que falla</td><td class="num">0 cr</td></tr></tbody></table></div>
<p class="muted small">Con la instalación local, los extractos no salen del despacho. <a href="/confianza/">Cómo tratamos los datos (art. 28)</a>.</p></div>
</div>

<div class="faq" style="margin-top:40px"><h2 class="h3" style="margin-bottom:20px">Preguntas frecuentes sobre Norma 43 en {e(short)}</h2>{faq_html(faq)}</div>
{bank_links_section() if target == "contasol" else ""}
</div></section>
<script defer src="/assets/lote.js?v={VERSION}"></script>"""
    return page(t["path"], t["title"], t["desc"], body, [faq_ld(faq)])


def norma43_contasol_page() -> str:
    return norma43_target_page("contasol")


# --- pSEO bancos y pasarelas -> ContaSol --------------------------------------------------------------------
# Texto verificado contra contabridge bank.movements_from_csv: el CSV necesita cabeceras Fecha/Date (o Fecha
# operación, Fecha valor, Booking date, Transaction date) + Importe/Amount (o Cargo y Abono) y Concepto/Description.
# Las cabeceras de Revolut, Stripe y PayPal no se reconocen tal cual: cada página dice qué columna renombrar.
BANK_PAGES = {
    "revolut": {
        "path": "/revolut-a-contasol/", "name": "Revolut", "kind": "pasarela", "csv": True,
        "h1": "Convertir extracto Revolut (CSV) a ContaSol APU.ods",
        "desc": "Pasa el extracto CSV de Revolut Business o Revolut personal a un APU.ods para ContaSol: un asiento por movimiento contra tu 572, sin OCR y con lo dudoso en la 555.",
        "lead": "Revolut no da Norma 43, pero sí un extracto en CSV. Flint lo convierte en el fichero de apuntes APU.ods que importa ContaSol, con la subcuenta 572 que uses para Revolut.",
        "export": [
            "En la app o en la web de Revolut abre la cuenta en euros y pide el extracto del periodo.",
            "Elige el formato Excel/CSV (no PDF) y descárgalo.",
            "Si tienes varias divisas, descarga un extracto por divisa y convierte solo el de euros.",
        ],
        "cols": [("Completed Date (o Date completed)", "Fecha"), ("Amount", "Importe"), ("Description", "Concepto (ya se reconoce)")],
        "cols_note": "Flint aún no reconoce las cabeceras en inglés de Revolut. Renombra la fecha y el importe en Excel o LibreOffice, guarda como CSV y arrástralo. Usa la fecha de completado: es la del cargo real en la cuenta.",
        "tips": [
            ("Una subcuenta por cuenta Revolut", "Da de alta en ContaSol una 572 propia (por ejemplo 57200005 Revolut EUR) para que el saldo cuadre con el de la app."),
            ("Sin conversión de divisas", "Flint no convierte importes ni inventa tipos de cambio. Un CSV en USD o GBP se contabilizaría tal cual: no lo mezcles con el de euros."),
            ("Comisiones", "Si la columna Fee trae importes, el Amount ya es el movimiento real de la cuenta. Las comisiones que Revolut cobra como fila aparte salen como otro apunte que puedes llevar a la 626."),
        ],
        "faq": [
            ("¿Sirve para Revolut Business y para Revolut personal?", "Sí, mientras el CSV tenga una fecha, un importe con signo y una descripción por fila. Las dos versiones traen esas columnas; solo hay que renombrarlas a Fecha, Importe y Concepto."),
            ("¿Por qué no aceptáis el PDF de Revolut?", "Esta página trabaja con CSV, que trae los importes exactos sin leer un documento impreso. Así no hay errores de lectura ni céntimos perdidos."),
            ("¿Qué pasa con las transferencias entre mis cuentas Revolut?", "Cada movimiento sin regla va a la 555 para revisar. Así ves los traspasos entre bolsillos o divisas y los llevas a mano a la 572 que corresponda, sin que Flint adivine nada."),
        ],
        "kw": "revolut a contasol, extracto revolut contasol, importar revolut business contasol, revolut csv apu.ods, contabilizar revolut contasol",
    },
    "stripe": {
        "path": "/stripe-a-contasol/", "name": "Stripe", "kind": "pasarela", "csv": True,
        "h1": "Contabilizar Stripe (CSV) en ContaSol y A3 sin picar asientos",
        "desc": "Convierte el informe CSV de saldo de Stripe en apuntes para ContaSol (APU.ods) o A3 (SUENLACE.DAT): cobros, comisiones y transferencias al banco, cada uno a su sitio y sin picar asientos.",
        "lead": "Stripe junta cobros, comisiones, reembolsos y transferencias a tu banco. Flint convierte el CSV de saldo en un asiento por fila contra la subcuenta que uses para Stripe, listo para ContaSol o A3.",
        "export": [
            "En el panel de Stripe abre los informes de saldo y elige el periodo (un mes cerrado).",
            "Descarga las transacciones del saldo en CSV, en la moneda de tu cuenta (EUR).",
            "Si te interesa separar la comisión, descarga la versión con columnas de importe bruto, comisión y neto.",
        ],
        "cols": [("Created (UTC) o Available On", "Fecha"), ("Net (neto) o Amount (bruto)", "Importe"), ("Description", "Concepto (ya se reconoce)")],
        "cols_note": "Flint aún no reconoce las cabeceras en inglés de Stripe. Renombra la fecha y el importe, guarda como CSV y arrástralo. Deja una sola columna llamada Importe: si dejas Amount y Net a la vez, se usaría la primera que aparezca.",
        "tips": [
            ("Stripe es una cuenta, no un cliente", "Trata el saldo de Stripe como una 572 aparte (por ejemplo 57200009 Stripe). Las transferencias (payouts) son un traspaso de esa 572 a la de tu banco."),
            ("Neto o bruto", "Con Net, cada cobro entra ya sin comisión y el saldo cuadra con lo que llega al banco; la comisión la apuntas a la 626 en un asiento resumen del mes. Con Amount, la comisión debe venir como fila propia."),
            ("Lo dudoso a la 555", "Flint no sabe qué cliente pagó cada cargo. Todo lo que no tenga regla va a la 555 para que lo apliques a la 430 o a ventas, sin cuentas inventadas."),
        ],
        "faq": [
            ("¿Sirve también para A3?", "Sí. Esta página genera el APU.ods de ContaSol; el mismo CSV en la página CSV a A3 genera el SUENLACE.DAT para a3ASESOR, a3ECO y a3CON."),
            ("¿Contabiliza el IVA de cada venta?", "No. Desde el extracto solo se conoce el dinero que se mueve. El IVA sale de las facturas: desde Claude o Cursor, la herramienta invoices_to_journal las contabiliza con IVA y luego casa los cobros de Stripe con ellas."),
            ("¿Y los reembolsos y disputas?", "Son filas con importe negativo y salen como cargos en la cuenta de Stripe. Van a la 555 para que decidas si anulan una venta o son un gasto."),
        ],
        "kw": "contabilizar stripe contasol, stripe a contasol, stripe a3, importar stripe contabilidad, csv stripe asientos, comisiones stripe contabilidad",
    },
    "paypal": {
        "path": "/paypal-a-contasol/", "name": "PayPal", "kind": "pasarela", "csv": True,
        "h1": "Convertir movimientos PayPal (CSV) a ContaSol y A3",
        "desc": "Pasa el informe de actividad CSV de PayPal a apuntes para ContaSol (APU.ods) o A3 (SUENLACE.DAT): cobros, pagos y retiradas al banco con su 572, sin picar asientos.",
        "lead": "El informe de actividad de PayPal trae cada cobro, pago y retirada. Flint lo convierte en apuntes contra la subcuenta que uses para PayPal y te da el APU.ods para ContaSol.",
        "export": [
            "En PayPal abre Actividad y busca la opción de descargar el informe de actividad.",
            "Elige el periodo, el tipo de transacciones (todas o solo las que afectan al saldo) y el formato CSV.",
            "Descarga el fichero en euros; si cobras en otras divisas, filtra o separa esas filas.",
        ],
        "cols": [("Fecha (o Date)", "Fecha (ya se reconoce)"), ("Neto o Bruto (Net o Gross)", "Importe"), ("Nombre o Asunto", "Concepto")],
        "cols_note": "La fecha de PayPal ya se reconoce. El importe no: renombra la columna que quieras usar a Importe y deja solo una. Si el fichero trae las cifras entre comillas con coma decimal, no hace falta tocarlas.",
        "tips": [
            ("Una 572 para PayPal", "Da de alta una subcuenta propia (por ejemplo 57200008 PayPal) para que el saldo de ContaSol cuadre con el de PayPal."),
            ("Filas que no mueven saldo", "El informe completo incluye retenciones y autorizaciones que no son dinero real. Descarga solo las transacciones que afectan al saldo para no duplicar movimientos."),
            ("Retiradas al banco", "Cada retirada es un traspaso a la 572 del banco. Flint la deja en la 555 para que la casas con el abono del extracto bancario."),
        ],
        "faq": [
            ("¿Sirve también para A3?", "Sí. Con el mismo CSV, la página CSV a A3 genera el SUENLACE.DAT. ContaPlus también tiene su página."),
            ("¿Qué columna de importe uso, Bruto o Neto?", "Neto si quieres que el saldo cuadre con el dinero que queda en PayPal; Bruto si vas a apuntar la tarifa de PayPal aparte a la 626. Deja solo una columna llamada Importe."),
            ("¿Detecta qué cliente pagó?", "No lo adivina. Los cobros sin regla van a la 555. Desde Claude o Cursor puedes pasar las facturas pendientes y Flint casa cada cobro con la 430 cuando importe y referencia coinciden."),
        ],
        "kw": "paypal a contasol, contabilizar paypal contasol, paypal a3, informe actividad paypal csv contabilidad, importar paypal apu.ods",
    },
    "caixabank": {
        "path": "/caixabank-a-contasol/", "name": "CaixaBank", "kind": "banco", "csv": False,
        "h1": "Importar extracto CaixaBank (Norma 43 o CSV) en ContaSol",
        "desc": "Convierte el extracto de CaixaBank (Norma 43 o CSV) en el APU.ods de ContaSol con la 572 del banco. Norma 43 con saldos comprobados; lo dudoso a la 555.",
        "lead": "CaixaBank permite descargar los movimientos en Norma 43 (cuaderno 43) desde la banca de empresas. Es el formato más fiable: Flint comprueba los saldos del fichero antes de generar el APU.ods para ContaSol.",
        "export": [
            "En CaixaBankNow (empresas) busca la descarga de movimientos de cuentas en formato Norma 43 o cuaderno 43.",
            "Elige la cuenta y el periodo y descarga el fichero (suele tener extensión .txt, .n43 o .aeb).",
            "Si solo tienes la exportación a Excel, guárdala como CSV y revisa las columnas (abajo).",
        ],
        "cols": [("Fecha", "Fecha (ya se reconoce)"), ("Importe", "Importe (ya se reconoce)"), ("Movimiento", "Concepto")],
        "cols_note": "Si tu exportación trae una columna Movimiento con el texto del apunte antes de Importe, renómbrala a Concepto: si no, Flint la tomaría como importe y rechazaría el fichero sin cobrarlo.",
        "tips": [
            ("Mejor Norma 43 que CSV", "El fichero Norma 43 trae saldo inicial, final y totales de control: Flint verifica que saldo inicial + abonos - cargos = saldo final. El CSV no permite esa comprobación."),
            ("Extensión del fichero", "Si CaixaBank lo descarga como .txt, cámbiale la extensión a .n43 antes de arrastrarlo."),
            ("Varias cuentas", "Un mismo Norma 43 puede traer varias cuentas. Si tienen subcuentas 572 distintas, conviértelas desde Claude o Cursor con bank_accounts; aquí todas van a la 572 del formulario."),
        ],
        "faq": [
            ("¿Qué formato me conviene descargar de CaixaBank?", "Norma 43. Es el estándar de la banca española, trae los importes exactos y los saldos de control, y Flint los comprueba antes de generar nada."),
            ("¿Funciona con CaixaBankNow de particulares?", "Si tu acceso solo ofrece Excel o CSV, también vale: guárdalo como CSV con columnas de fecha, importe y concepto."),
            ("¿Qué hace con los recibos y transferencias?", "Un asiento por movimiento contra la 572. Lo que no tiene regla va a la 555 para revisar. Desde Claude o Cursor puedes añadir reglas (por ejemplo, ENDESA a la 628)."),
        ],
        "kw": "caixabank contasol, importar extracto caixabank contasol, norma 43 caixabank, caixabanknow norma 43, extracto caixabank apu.ods",
    },
    "bbva": {
        "path": "/bbva-a-contasol/", "name": "BBVA", "kind": "banco", "csv": False,
        "h1": "Importar extracto BBVA (Norma 43 o CSV) en ContaSol",
        "desc": "Convierte el extracto de BBVA (Norma 43 o CSV) en el APU.ods de ContaSol con la 572 del banco, comprobando los saldos del fichero y sin picar asientos.",
        "lead": "BBVA ofrece los movimientos en Norma 43 en la banca de empresas y en Excel en la web. Flint convierte cualquiera de los dos en el APU.ods de ContaSol, y con Norma 43 además cuadra los saldos.",
        "export": [
            "En BBVA net cash (empresas) busca la descarga de movimientos en formato Norma 43 o AEB 43.",
            "En la web de particulares o autónomos, descarga los movimientos en Excel y guárdalos como CSV.",
            "Descarga un mes cerrado por cuenta para que la numeración de asientos sea limpia.",
        ],
        "cols": [("Fecha", "Fecha (ya se reconoce)"), ("Importe", "Importe (ya se reconoce)"), ("Concepto", "Concepto (ya se reconoce)")],
        "cols_note": "Si tu exportación trae también una columna Movimiento con texto antes de Importe, renómbrala o bórrala: si no, Flint la tomaría como importe y rechazaría el fichero sin cobrarlo.",
        "tips": [
            ("Norma 43 con cuadre", "Con el Norma 43, Flint comprueba los totales del registro 33 y que saldo inicial + movimientos = saldo final antes de generar los apuntes."),
            ("Quita las filas de cabecera", "No hace falta: Flint busca la fila de títulos en las primeras 40 filas y salta los totales del final."),
            ("Cuenta de valores o tarjeta", "Convierte solo la cuenta corriente. Las liquidaciones de tarjeta de crédito suelen llevar otra 52x en tu plan de cuentas."),
        ],
        "faq": [
            ("¿Qué formato me conviene descargar de BBVA?", "Norma 43 si tienes acceso a la banca de empresas: trae los saldos de control. Si no, el Excel de movimientos guardado como CSV."),
            ("¿Acepta el Excel (.xlsx) directamente?", "No: guárdalo como CSV desde Excel o LibreOffice (separador punto y coma o coma, los dos valen)."),
            ("¿Cuánto cuesta?", "3 créditos por fichero convertido, unos 0,15 €. Si el fichero no se puede leer, no se cobra."),
        ],
        "kw": "bbva contasol, importar extracto bbva contasol, norma 43 bbva, bbva net cash norma 43, extracto bbva apu.ods",
    },
    "santander": {
        "path": "/santander-a-contasol/", "name": "Banco Santander", "kind": "banco", "csv": False,
        "h1": "Importar extracto Banco Santander (Norma 43 o CSV) en ContaSol",
        "desc": "Convierte el extracto de Banco Santander (Norma 43 o CSV) en el APU.ods de ContaSol con la 572 del banco. Saldos comprobados y lo dudoso a la 555.",
        "lead": "Banco Santander permite descargar los movimientos en Norma 43 desde la banca de empresas y en Excel desde la web. Flint convierte los dos en el APU.ods que importa ContaSol.",
        "export": [
            "En la banca de empresas de Santander busca la descarga de movimientos en cuaderno 43 o Norma 43.",
            "En la web de particulares, descarga los movimientos en Excel y guárdalos como CSV.",
            "Descarga un fichero por cuenta y por mes para cuadrar con el extracto en papel.",
        ],
        "cols": [("Fecha Operación", "Fecha (ya se reconoce)"), ("Importe", "Importe (ya se reconoce)"), ("Concepto", "Concepto (ya se reconoce)")],
        "cols_note": "Con las columnas Fecha Operación, Fecha Valor, Concepto, Importe y Saldo no hay que tocar nada. Si tu descarga usa otros títulos, renómbralos a Fecha, Importe y Concepto.",
        "tips": [
            ("Fecha de operación o valor", "Flint usa la fecha de operación para el asiento. Desde Claude o Cursor puedes pedir la fecha valor (use_value_date)."),
            ("Norma 43 con cuadre", "Con el Norma 43, Flint comprueba que saldo inicial + abonos - cargos = saldo final y marca el fichero si no cuadra."),
            ("Mezcla de bancos", "Puedes arrastrar a la vez el Santander y los de otros bancos del cliente. Los asientos se numeran seguidos; cambia la 572 del formulario entre lotes si cada banco tiene la suya."),
        ],
        "faq": [
            ("¿Qué formato me conviene descargar de Santander?", "Norma 43 si lo tienes: trae los saldos de control. Si no, el Excel de movimientos guardado como CSV funciona igual."),
            ("¿Sirve para Santander Empresas y Particulares?", "Sí. El formato Norma 43 es el mismo en todos los bancos españoles, y el CSV vale si tiene fecha, importe y concepto."),
            ("¿Sube mis datos a algún sitio?", "En esta página cada fichero viaja cifrado a nuestro servidor, se procesa en memoria y no se guarda. Con la instalación local, los extractos no salen del despacho hacia nosotros: solo viajan la licencia y el crédito."),
        ],
        "kw": "santander contasol, importar extracto santander contasol, norma 43 santander, cuaderno 43 santander empresas, extracto santander apu.ods",
    },
}
SEO_KEYWORDS.update({b["path"]: b["kw"] for b in BANK_PAGES.values()})


def bank_links_section() -> str:
    """Enlaces cruzados a las páginas pSEO de BANK_PAGES (solo en las páginas en español)."""
    cards = "".join(f'<li><a href="{b["path"]}">{icon("landmark" if b["kind"] == "banco" else "refresh")}<span><b>{e(b["name"])}</b>'
                    f'<span class="muted small"> · {"Norma 43 o CSV" if b["kind"] == "banco" else "CSV"}</span></span></a></li>'
                    for b in BANK_PAGES.values())
    return (f'<div class="bank-links" style="margin-top:40px"><h2 class="h3">Bancos y pasarelas compatibles</h2>'
            f'<p class="muted small">Guías paso a paso para llevar el extracto de cada uno a ContaSol.</p>'
            f'<ul class="checks" style="columns:2;margin-top:12px">{cards}</ul></div>')


def bank_page(key: str) -> str:
    b = BANK_PAGES[key]
    t = N43_TARGETS["contasol"]
    csv = b["csv"]
    accept = ".csv" if csv else ".n43,.c43,.q43,.csv"
    drop = (f"Suelta aquí el CSV de {b['name']} (.csv)" if csv
            else f"Suelta aquí el Norma 43 (.n43, .c43) o el CSV de {b['name']}")
    steps = "".join(f'<li class="step"><span class="tile tile-sm">{icon(ic)}</span><div><h3><span class="step-n">{i}</span>{e(h)}</h3><p>{e(s)}</p></div></li>'
                    for i, (s, ic, h) in enumerate(zip(b["export"], ("landmark", "download", "check"),
                                                       (f"Entra en {b['name']}", "Descarga el fichero", "Antes de convertir")), 1))
    cols = "".join(f'<tr><td style="white-space:normal">{e(a)}</td><td style="white-space:normal">{e(c)}</td></tr>' for a, c in b["cols"])
    tips = "".join(f'<li>{icon("check")}<span><b>{e(h)}:</b> {e(x)}</span></li>' for h, x in b["tips"])
    others = " · ".join(f'<a href="{o["path"]}">{e(o["name"])}</a>' for k, o in BANK_PAGES.items() if k != key)
    a3 = ' ¿Usas A3? Con el mismo CSV, <a href="/csv-a-a3/">CSV a A3 (SUENLACE.DAT)</a>.' if b["kind"] == "pasarela" else ""
    faq = list(b["faq"])
    if not any("cuesta" in q for q, _ in faq):
        faq.append(("¿Cuánto cuesta y hay suscripción?",
                    f"Cada fichero convertido son 3 créditos (unos 0,15 €) y si falla no se cobra. Con tu correo tienes {SITE['free_credits']} créditos gratis sin tarjeta; después recargas desde 5 € o usas el Plan Despacho."))
    body = f"""
<section class="hero"><div class="glow" aria-hidden="true"></div><div class="wrap narrow">
<nav class="crumbs" aria-label="Ruta"><a href="/">Inicio</a>{icon("chevron-right")}<a href="/norma43-a-contasol/">ContaSol</a>{icon("chevron-right")}<span aria-current="page">{e(b["name"])}</span></nav>
<h1>{e(b["h1"])}</h1>
<p class="lead">{e(b["lead"])}</p>
</div></section>

<section class="section tight"><div class="wrap narrow" data-batch data-batch-target="contasol"{' data-batch-csv-mode="1"' if csv else ""}>
<form class="saldo-form glass batch" data-batch-form novalidate>
<label class="lic"><span class="lic-label">{icon("key")}Tu correo o licencia</span>
<span class="lic-field"><input type="text" name="license" autocomplete="email" spellcheck="false" placeholder="tu@correo.com o LIC-…" required aria-describedby="bk-help" data-batch-lic></span>
<span id="bk-help" class="lic-help">Escribe tu correo para activar <b>{SITE['free_credits']} créditos gratis</b> al instante (sin tarjeta) o pega tu clave LIC-….</span></label>
<label class="lic"><span class="lic-label">{icon("landmark")}Subcuenta de {e(b["name"])}</span>
<span class="lic-field"><input type="text" name="bank" inputmode="numeric" autocomplete="off" value="57200001" pattern="57[0-9]{{2,10}}" required data-batch-bank aria-describedby="bkb-help"></span>
<span id="bkb-help" class="lic-help">La 572 que usas para {e(b["name"])} en ContaSol. Los apuntes sin regla van a la 555 para revisar.</span></label>

<label class="drop" data-batch-drop><input type="file" multiple accept="{accept}" class="sr-only" data-batch-input>
<span class="tile">{icon("download")}</span><b>{e(drop)}</b>
<span class="muted small">Vista previa instantánea · Sin OCR · hasta 10 MB</span></label>
<div class="sample-bar"><button type="button" class="btn-sample" data-batch-sample>{icon("refresh")}<span>Cargar extracto de prueba (demo en 1 clic)</span></button></div>

<div class="tw batch-list" data-batch-list hidden><table class="uso-t"><thead><tr><th>Fichero</th><th>Tipo</th><th>Estado</th><th>Detalle</th><th class="num"></th></tr></thead><tbody data-batch-rows></tbody></table></div>
<div class="batch-actions"><button class="btn btn-primary btn-lg" type="submit" data-batch-go disabled>{icon("refresh")}<span>Convertir para ContaSol</span></button>
<button class="btn btn-ghost" type="button" data-batch-stop hidden>Detener</button>
<button class="btn btn-quiet" type="button" data-batch-clear hidden>Vaciar lista</button>
<span class="muted small tabnum" data-batch-cost aria-live="polite"></span></div>
<p class="note" data-batch-msg aria-live="polite" hidden>{icon("info")}<span></span></p>

<div class="batch-out" data-batch-out hidden><h2 class="h4">{icon("check")}APU.ods generado</h2>
<p class="muted small">Un fichero: descargas APU.ods. Varios: un ZIP con todos, con los asientos numerados seguidos. Revisa los marcados como REVISAR_555 antes de cerrar.</p>
<div class="cta-row"><button class="btn btn-primary" type="button" data-batch-csv>{icon("download")}Descargar APU.ods</button>
<button class="btn btn-ghost" type="button" data-batch-zip>{icon("table")}Todo con resumen (.zip)</button>
<a class="btn btn-quiet" href="/precios/#despacho">Ver tarifas y recargas</a></div></div>
</form>

<div class="install-grid batch-info">
<div><h2 class="h3">Cómo descargar el extracto de {e(b["name"])}</h2>
<ol class="steps" style="margin-top:14px">{steps}</ol></div>
<div><h2 class="h3">Columnas que necesita Flint</h2>
<div class="tw uso"><table class="uso-t"><thead><tr><th style="white-space:normal">En tu fichero de {e(b["name"])}</th><th>Llámala</th></tr></thead><tbody>{cols}</tbody></table></div>
<p class="muted small">{e(b["cols_note"])}</p></div>
</div>

<div style="margin-top:32px"><h2 class="h3">Contabilizar {e(b["name"])} en ContaSol sin sorpresas</h2>
<ul class="checks" style="margin-top:12px">{tips}</ul>
<p class="muted small">Importación: {t["import"]} La primera vez, pruébalo en una empresa de pruebas.{a3}</p></div>

<div class="faq" style="margin-top:40px"><h2 class="h3" style="margin-bottom:20px">Preguntas frecuentes sobre {e(b["name"])} y ContaSol</h2>{faq_html(faq)}</div>
<p class="muted small" style="margin-top:24px">Otros bancos y pasarelas: {others} · <a href="/csv-a-contasol/">Cualquier CSV</a> · <a href="/norma43-a-contasol/">Cualquier Norma 43</a></p>
</div></section>
<script defer src="/assets/lote.js?v={VERSION}"></script>"""
    return page(b["path"], f"{b['h1']} · Flint by KeyFlint", b["desc"], body, [faq_ld(faq)])


def csv_target_page(target: str) -> str:
    """Landing SEO directa para competir en Convertir CSV a ContaSol / A3 / ContaPlus."""
    t = N43_TARGETS[target]
    short, prog, fname = t["short"], t["program"], t["file"]
    slug_map = {"contasol": "/csv-a-contasol/", "a3": "/csv-a-a3/", "contaplus_ascii": "/csv-a-contaplus/"}
    path = slug_map[target]
    title = f"Convertir CSV a {short} ({fname}) online · Sin OCR · Flint by KeyFlint"
    desc = f"Prepara movimientos CSV bancarios (Revolut, Stripe, PayPal, CaixaBank, BBVA, Santander) directamente para {prog} ({fname}). Vista previa instantánea y 25 créditos gratis."
    faq = [
        ("¿Qué datos necesita el archivo CSV?",
         "Solo necesita una columna de fecha (Fecha, Date, Fecha operación), una de importe (o columnas separadas de Cargo/Debe y Abono/Haber) y una de concepto o descripción. Flint detecta automáticamente el delimitador (; , tabulador) y salta las filas de cabeceras o totales."),
        (f"¿Cómo se importa el archivo resultante en {short}?",
         f"Flint transforma cada fila del CSV en un asiento cuadrado contra la subcuenta 572 que indiques (y lleva lo pendiente a la 555 sin inventar cuentas). Descargas {fname} listo para importar. {t['import'].replace('<b>', '').replace('</b>', '').replace('&gt;', '>')}"),
        ("¿Sirve para Revolut, Wise, Stripe, PayPal y bancos españoles?",
         "Sí, si el CSV tiene columnas de fecha, importe y concepto. Los bancos españoles suelen traerlas con esos nombres; en Revolut, Stripe y PayPal hay que renombrar alguna columna antes. Cada guía explica cuál: Revolut, Stripe, PayPal, CaixaBank, BBVA y Santander."),
        ("¿Hay suscripción obligatoria?",
         f"No. Al escribir tu correo tienes {SITE['free_credits']} créditos gratis al instante sin tarjeta (8 extractos convertidos gratis). Después puedes recargar desde 5 € pago por uso sin suscripción, o usar el Plan Despacho."),
    ]
    n43_link = "contaplus" if target == "contaplus_ascii" else target
    body = f"""
<section class="hero"><div class="glow" aria-hidden="true"></div><div class="wrap narrow">
<nav class="crumbs" aria-label="Ruta"><a href="/">Inicio</a>{icon("chevron-right")}<span aria-current="page">CSV a {e(short)}</span></nav>
<h1>Convertir CSV a {e(short)} ({e(fname)})</h1>
<p class="lead">Prepara movimientos CSV bancarios o de pasarelas (Revolut, Stripe, PayPal, CaixaBank, BBVA, Santander) directamente para {e(prog)}, sin extracción PDF ni OCR. Vista previa inmediata y lotes en ZIP.</p>
</div></section>

<section class="section tight"><div class="wrap narrow" data-batch data-batch-target="{target}" data-batch-csv-mode="1">
<form class="saldo-form glass batch" data-batch-form novalidate>
<label class="lic"><span class="lic-label">{icon("key")}Tu correo o licencia</span>
<span class="lic-field"><input type="text" name="license" autocomplete="email" spellcheck="false" placeholder="tu@correo.com o LIC-…" required aria-describedby="c-help" data-batch-lic></span>
<span id="c-help" class="lic-help">Escribe tu correo para activar <b>{SITE['free_credits']} créditos gratis</b> al instante (sin tarjeta) o pega tu clave LIC-….</span></label>
<label class="lic"><span class="lic-label">{icon("landmark")}Subcuenta del banco</span>
<span class="lic-field"><input type="text" name="bank" inputmode="numeric" autocomplete="off" value="57200001" pattern="57[0-9]{{2,10}}" required data-batch-bank aria-describedby="cb-help"></span>
<span id="cb-help" class="lic-help">La subcuenta 572 en {e(short)} (p. ej. 57200001). Los apuntes sin regla van a la 555 para revisar.</span></label>

<label class="drop" data-batch-drop><input type="file" multiple accept=".csv,.n43,.c43,.q43,.pdf" class="sr-only" data-batch-input>
<span class="tile">{icon("download")}</span><b>Suelta aquí tus archivos CSV, Norma 43 o PDF digitales (.csv, .n43, .pdf)</b>
<span class="muted small">Vista previa automática de filas verificadas · Sin suscripción</span></label>
<div class="sample-bar"><button type="button" class="btn-sample" data-batch-sample>{icon("refresh")}<span>Cargar CSV bancario de prueba (demo en 1 clic)</span></button></div>

<div class="tw batch-list" data-batch-list hidden><table class="uso-t"><thead><tr><th>Fichero</th><th>Tipo</th><th>Estado</th><th>Detalle</th><th class="num"></th></tr></thead><tbody data-batch-rows></tbody></table></div>
<div class="batch-actions"><button class="btn btn-primary btn-lg" type="submit" data-batch-go disabled>{icon("refresh")}<span>Convertir para {e(short)}</span></button>
<button class="btn btn-ghost" type="button" data-batch-stop hidden>Detener</button>
<button class="btn btn-quiet" type="button" data-batch-clear hidden>Vaciar lista</button>
<span class="muted small tabnum" data-batch-cost aria-live="polite"></span></div>
<p class="note" data-batch-msg aria-live="polite" hidden>{icon("info")}<span></span></p>

<div class="batch-out" data-batch-out hidden><h2 class="h4">{icon("check")}Fichero {e(fname)} generado</h2>
<p class="muted small">Un archivo: descargas {e(fname)} directo. Varios archivos: descargas un ZIP con todos los lotes numerados seguidos.</p>
<div class="cta-row"><button class="btn btn-primary" type="button" data-batch-csv>{icon("download")}Descargar {e(fname)}</button>
<button class="btn btn-ghost" type="button" data-batch-zip>{icon("table")}Todo con resumen (.zip)</button>
<a class="btn btn-quiet" href="/precios/#despacho">Ver tarifas y recargas</a></div></div>
</form>

<div class="install-grid batch-info">
<div><h2 class="h3">¿Qué datos necesita el CSV?</h2>
<ul class="checks">
<li>{icon("check")}<span><b>Fecha e importe:</b> detecta automáticamente columnas de Fecha e Importe (o Cargo y Abono separados).</span></li>
<li>{icon("check")}<span><b>Cualquier formato europeo o anglosajón:</b> coma o punto decimal, fechas DD/MM/AAAA o AAAA-MM-DD.</span></li>
<li>{icon("check")}<span><b>Flujo CSV directo sin OCR:</b> conversión determinista al 100%, sin errores de lectura óptica ni cuentas inventadas.</span></li>
<li>{icon("check")}<span><b>También acepta Norma 43 (.n43, .c43):</b> puedes mezclar archivos CSV y cuadernos 43 en el mismo lote.</span></li>
</ul></div>
<div><h2 class="h3">{e(short)} ({e(fname)})</h2>
<p class="muted small">{t["import"]}</p>
<div class="tw uso" style="margin-top:12px"><table class="uso-t"><thead><tr><th>Concepto</th><th class="num">Créditos</th></tr></thead>
<tbody><tr><td>Convertir un CSV o extracto a {e(short)}</td><td class="num">3 cr (≈ 0,15 €)</td></tr>
<tr><td>Archivo con error de formato</td><td class="num">0 cr (gratis)</td></tr></tbody></table></div>
<p class="muted small">También disponible como conector directo en Claude (<code>https://mcp.keyflint.dev/despacho/mcp</code>). <a href="/norma43-a-{n43_link}/">Ver conversor Norma 43 a {e(short)}</a>.</p></div>
</div>

<div class="faq" style="margin-top:40px"><h2 class="h3" style="margin-bottom:20px">Preguntas frecuentes sobre convertir CSV a {e(short)}</h2>{faq_html(faq)}</div>
{bank_links_section() if target == "contasol" else ""}
</div></section>
<script defer src="/assets/lote.js?v={VERSION}"></script>"""
    return page(path, title, desc, body, [faq_ld(faq)])



def start() -> str:
    mail = (f"{SITE['contact']}?subject=" + urllib.parse.quote("Licencia gratuita KeyFlint MCP")
            + "&body=" + urllib.parse.quote("Hola, quiero probar los servidores MCP.\n\nLo usaré para: \nCliente (Claude, Cursor…): "))
    body = f"""
<section class="hero hero-sm"><div class="glow" aria-hidden="true"></div><div class="wrap narrow">
<nav class="crumbs" aria-label="Ruta"><a href="/">Inicio</a>{icon("chevron-right")}<span aria-current="page">Guía</span></nav>
<h1>Empieza en tres pasos</h1>
<p class="lead">De cero a tu primera herramienta funcionando en unos dos minutos. No hace falta saber programar.</p>
</div></section>
<section class="section tight"><div class="wrap narrow">
<ol class="guide">
<li class="g-step" id="licencia"><span class="g-n">1</span><div class="g-body">
<h2>Consigue tu licencia</h2>
<p>Tu licencia tiene la forma <code>LIC-…</code>, llega por correo y sirve para todos los servidores.</p>
<div class="choice">
<a class="choice-card" href="/probar/"><span class="tile tile-sm">{icon("key")}</span><span class="cc-text"><b>Gratis · {SITE['free_credits']} créditos</b><span class="muted small">Al momento, sin tarjeta.</span></span>{icon("arrow-right")}</a>
<a class="choice-card" href="/precios/"><span class="tile tile-sm">{icon("card")}</span><span class="cc-text"><b>Plan de pago</b><span class="muted small">Licencia inmediata tras el pago.</span></span>{icon("arrow-right")}</a>
</div></div></li>
<li class="g-step" id="uv"><span class="g-n">2</span><div class="g-body">
<h2>Instala uv, una sola vez</h2>
<p><a href="https://docs.astral.sh/uv/" rel="noopener">uv</a> descarga y ejecuta los servidores de forma aislada en tu equipo. Abre una terminal y ejecuta el comando de tu sistema:</p>
{code_block("uv-mac", "curl -LsSf https://astral.sh/uv/install.sh | sh", "macOS y Linux · Terminal")}
{code_block("uv-win", 'powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"', "Windows · PowerShell")}
<p class="note">{icon("info")}<span>Después, cierra y vuelve a abrir tu cliente para que encuentre <code>uvx</code>.</span></p>
</div></li>
<li class="g-step"><span class="g-n">3</span><div class="g-body">
<h2>Añade los servidores a tu cliente</h2>
<p>Pega tu licencia y copia la configuración con los {len(MCPS)} servidores a la vez. Si prefieres uno solo, cada servidor del <a href="/#catalogo">catálogo</a> tiene su instalador con un clic para Cursor y VS Code.</p>
<div class="install-card glass">{installer(ALL)}</div>
</div></li>
<li class="g-step"><span class="g-n g-ok">{icon("check")}</span><div class="g-body">
<h2>Compruébalo</h2>
<p>Pregunta a tu agente: <q>¿cuántos créditos me quedan?</q> Usará la herramienta gratuita <code>credits_balance</code> y te dirá tu saldo.</p>
<div class="faq">{faq_html([
        ("No aparecen las herramientas", "Reinicia el cliente por completo (en Windows, ciérralo también desde la bandeja del sistema). Comprueba que uvx --version funciona en una terminal nueva."),
        ("Dice que la licencia no es válida", f"Revisa que copiaste la licencia completa, sin espacios, en KEYFLINT_LICENSE. Si sigue fallando, escríbenos a {CONTACT}."),
        ("Me he quedado sin créditos", "La herramienta te devuelve un enlace de recarga. Los créditos se suman a tu misma licencia, así que no tienes que cambiar nada en la configuración."),
    ])}</div>
</div></li>
</ol>
</div></section>"""
    ld = [{"@context": "https://schema.org", "@type": "HowTo", "name": "Instalar un servidor MCP de KeyFlint",
           "totalTime": "PT2M",
           "step": [{"@type": "HowToStep", "name": n} for n in
                    ["Consigue tu licencia", "Instala uv", "Añade el servidor a tu cliente MCP", "Compruébalo con tu agente"]]}]
    return page("/empezar/", "Cómo instalar un servidor MCP en Claude, Cursor o VS Code · Flint by KeyFlint",
                "Guía paso a paso para instalar servidores MCP en Claude Desktop, Claude Code, Cursor, VS Code, Codex, Antigravity y Windsurf con una licencia gratuita.",
                body, ld)


def balance_page() -> str:
    tp = SITE["topup"]
    pro = next(p for p in SITE["packs"] if p["id"] == "pro")
    presets = "".join(f'<button type="button" class="preset" data-preset="{a}" data-tier-min="{a}" aria-pressed="false" title="{e(n)}: {tp["rate"] * (100 + b) // 100} {L("créditos por euro", "credits per euro")}">'
                      f'<b class="tabnum">{L(f"{a} €", f"€{a}")}</b><span class="preset-bonus{" base" if not b else ""}">{(L(f"+{b} %", f"+{b}%")) if b else "base"}</span></button>'
                      for a, b, n in tp["tiers"])
    topup_cfg = e(json.dumps({"min": tp["min"], "max": tp["max"], "rate": tp["rate"],
                              "tiers": [[a, b] for a, b, _ in tp["tiers"]]}))
    body = f"""
<section class="hero hero-sm"><div class="glow" aria-hidden="true"></div><div class="wrap narrow">
<nav class="crumbs" aria-label="{L("Ruta", "Breadcrumb")}"><a href="{U("home")}">{L("Inicio", "Home")}</a>{icon("chevron-right")}<span aria-current="page">{L("Mi saldo", "My balance")}</span></nav>
<h1>{L("Consulta tu saldo", "Check your balance")}</h1>
<p class="lead">{L("Pega tu licencia para ver tu plan, los créditos que te quedan y los que has usado.", "Paste your license to see your plan, the credits you have left and the ones you have used.")}</p>
</div></section>
<section class="section tight"><div class="wrap narrow">
<form class="saldo-form glass" data-balance-form novalidate>
<label class="lic"><span class="lic-label">{icon("key")}{L("Tu licencia", "Your license")}</span>
<span class="lic-field"><input type="text" name="license" autocomplete="off" spellcheck="false" placeholder="LIC-…" required aria-describedby="saldo-help"></span>
<span id="saldo-help" class="lic-help">{L('Se consulta a KeyFlint en el momento. ¿Aún sin licencia? <a href="/probar/">Pide 25 créditos gratis</a>.', 'Checked live with KeyFlint. No license yet? <a href="/en/try/">Get 25 free credits</a>.')}</span></label>
<button class="btn btn-primary btn-lg" type="submit">{icon("gauge")}{L("Consultar saldo", "Check balance")}</button>
</form>
<div class="note ok-note" data-topup-done aria-live="polite" hidden><img src="/assets/flint-icon.svg" width="20" height="20" alt=""><span></span></div>
<div class="saldo-out" data-balance-out aria-live="polite" hidden>
<div class="saldo-card">
<div class="saldo-head"><span class="eyebrow" data-f="tier"></span><span class="status" data-f="status"></span></div>
<p class="saldo-num"><b class="tabnum" data-f="balance"></b><span class="muted"> {L("créditos disponibles", "credits available")}</span></p>
<div class="meter" role="meter" aria-valuemin="0" data-meter><span></span></div>
<dl class="saldo-dl"><div><dt>{L("Usados", "Used")}</dt><dd class="tabnum" data-f="consumed"></dd></div><div><dt>{L("Total del plan", "Plan total")}</dt><dd class="tabnum" data-f="allowance"></dd></div></dl>
<div class="recharge topup" id="recargar" data-topup='{topup_cfg}'><h3 class="h4">{icon("card")}{L("Recargar créditos", "Top up credits")}</h3>
<p class="muted small">{L("Elige cuánto pagar. Los créditos se suman a <b>esta misma licencia</b>: no cambias nada en Claude, Cursor ni VS Code. No caducan.", "Choose how much to pay. Credits are added to <b>this same license</b>: nothing changes in Claude, Cursor or VS Code. They never expire.")}</p>
<div class="topup-presets" role="group" aria-label="{L("Importes rápidos", "Quick amounts")}">{presets}</div>
<div class="topup-amt"><input type="range" min="{tp['min']}" max="{tp['slider_max']}" step="1" value="{tp['default']}" aria-label="{L("Importe en euros", "Amount in euros")}" data-topup-range>
<label class="topup-num"><span class="sr-only">{L("Importe exacto", "Exact amount")}</span><input type="number" inputmode="numeric" min="{tp['min']}" max="{tp['max']}" step="1" value="{tp['default']}" data-topup-amount><span>€</span></label></div>
<div class="topup-result" aria-live="polite">
<div class="topup-sum"><span class="eyebrow">{L("Recibes", "You get")}</span><p><b class="tabnum" data-topup-credits></b><span class="topup-unit">{L("créditos", "credits")}</span><span class="topup-badge" data-topup-bonus hidden></span></p></div>
<ul class="topup-eq" data-topup-eqs><li><b class="tabnum" data-eq="4"></b><span>{L("extractos Norma 43 leídos y conciliados", "Norma 43 statements parsed and reconciled")}</span></li><li><b class="tabnum" data-eq="2"></b><span>{L("diarios A3 convertidos a ContaPlus", "journals converted (e.g. A3 to Xero)")}</span></li><li><b class="tabnum" data-eq="1"></b><span>{L("webs leídas", "web pages read")}</span></li></ul>
<p class="muted small" data-topup-eq hidden></p>
<p class="topup-next small" data-topup-next></p></div>
<label class="topup-waiver"><input type="checkbox" data-topup-waiver> <span>{L("Quiero los créditos ya. Acepto que, al empezar a usarlos, pierdo el derecho de desistimiento de 14 días sobre la parte usada.", "I want the credits now. I accept that once I start using them I lose the 14-day right of withdrawal on the used part.")}</span></label>
<button class="btn btn-primary" type="button" data-topup-go disabled>{icon("card")}<span data-topup-label>{L("Recargar", "Top up")}</span></button>
<p class="muted small">{L(f"Pago seguro con Stripe, IVA incluido. De {tp['min']} € a {tp['max']} € por pago.", f"Secure payment with Stripe, VAT included. From €{tp['min']} to €{tp['max']} per payment.")} {L("¿Lo usas a diario?", "Use it daily?")} <a href="{e(pro['checkout'])}" rel="nofollow">{L(f"Pro: {money(pro['credits'])} créditos al mes por {money(pro['price'])} $", f"Pro: {pro['credits']:,} credits a month for ${pro['price']}")}</a>.</p>
<p class="saldo-err note" data-topup-err hidden>{icon("info")}<span></span></p></div>
<div class="cta-row"><a class="btn btn-ghost" href="{U("pricing")}">{L("Comparar planes", "Compare plans")}</a><a class="btn btn-quiet" href="{U("install")}">{L("Instalar servidores", "Install the tools")}</a></div>
</div>
<div class="saldo-card uso" data-usage hidden><h3>{L("Uso en los últimos 30 días", "Usage in the last 30 days")}</h3>
<div class="tw"><table class="uso-t"><thead><tr><th>{L("Servidor", "Server")}</th><th>{L("Herramienta", "Tool")}</th><th class="num">{L("Llamadas", "Calls")}</th><th class="num">{L("Créditos", "Credits")}</th><th class="num">{L("Errores", "Errors")}</th></tr></thead><tbody data-usage-tools></tbody></table></div>
<h4>{L("Últimas llamadas", "Recent calls")}</h4>
<div class="tw"><table class="uso-t"><thead><tr><th>{L("Cuándo", "When")}</th><th>{L("Servidor", "Server")}</th><th>{L("Herramienta", "Tool")}</th><th class="num">{L("Créditos", "Credits")}</th><th>{L("Estado", "Status")}</th></tr></thead><tbody data-usage-recent></tbody></table></div>
<p class="muted small">{L("Se registra servidor, herramienta, resultado y créditos de cada llamada por URL. Nunca el contenido. Se borra a los 180 días.", "We log server, tool, result and credits for each remote call. Never the content. Deleted after 180 days.")}</p>
</div></div>
<p class="saldo-err note" data-balance-err hidden>{icon("info")}<span></span></p>
<form class="recover glass" id="recuperar" data-recover-form novalidate style="margin-top:28px">
<div><h2 class="h3">{L("¿Perdiste tu licencia?", "Lost your license?")}</h2>
<p class="muted small">{L("Escribe tu correo y te enviaremos un enlace de acceso de un solo uso con tus licencias activas.", "Enter your email and we will send you a one-time access link with your active licenses.")}</p></div>
<div class="recover-row"><input type="email" name="email" autocomplete="email" placeholder="{L("tu@correo.com", "you@company.com")}" required aria-label="{L("Correo electrónico", "Email address")}">
<button class="btn btn-ghost" type="submit">{L("Enviar enlace", "Send link")}</button></div>
<p class="lic-help" data-recover-msg aria-live="polite"></p>
</form>
<div class="faq saldo-faq">{faq_html(L([
        ("¿Perdiste tu licencia?", "Escribe tu correo en la página de confirmación del pago o en el portal de KeyFlint y te enviamos un enlace de acceso de un solo uso."),
        ("¿Por qué no veo el detalle por servidor?", "Las llamadas remotas por URL aparecen arriba en la tabla de uso. En instalación local tus ficheros no pasan por nuestros servidores, así que solo registramos el saldo."),
        ("¿Cómo añado créditos?", "Consulta tu saldo, elige el importe en Recargar créditos y paga con Stripe. En unos segundos se suman a la misma licencia, sin cambiar nada en tu configuración."),
        ("¿Hay descuento por volumen?", "Sí: desde 20 € recibes un 10 % más de créditos, desde 50 € un 25 % y desde 100 € un 40 %."),
        ("¿Y si me arrepiento?", "Si no has usado los créditos de una recarga, escríbenos en los 14 días siguientes y te devolvemos el importe. Al devolverla se retiran esos créditos."),
    ], [
        ("Lost your license?", "Enter your email on the payment confirmation page or in the KeyFlint portal and we send you a one-time access link."),
        ("Why no per-tool breakdown?", "KeyFlint tracks the license balance. Remote calls show up in the usage table; each tool tells your AI its cost before running."),
        ("How do I add credits?", "Check your balance, pick an amount under Top up credits and pay with Stripe. Within seconds they are added to the same license, with no config changes."),
        ("Is there a volume discount?", "Yes: from €20 you get 10% more credits, from €50 25% more and from €100 40% more."),
        ("What if I change my mind?", "If you have not used the credits from a top-up, email us within 14 days and we refund it. The refunded credits are removed."),
    ]))}</div>
</div></section>"""
    return page(U("balance"), L("Consulta tu saldo de créditos · Flint by KeyFlint", "Check your credit balance · Flint by KeyFlint"),
                L("Consulta los créditos que te quedan en tu licencia de KeyFlint MCP.", "Check the credits left on your Flint license and top up."),
                body, noindex=True, lang=_LANG[-1])


def thanks() -> str:
    body = f"""
<section class="hero hero-sm center"><div class="glow" aria-hidden="true"></div><div class="wrap narrow">
<img class="brand-mark-lg" src="/assets/flint-icon.svg" width="96" height="96" alt="Flint">
<h1>Pago completado</h1>
<p class="lead" data-reveal-lead>Tu licencia <code>LIC-…</code> está de camino a tu correo. Suele llegar en menos de un minuto.</p>
</div></section>
<section class="section tight"><div class="wrap narrow">
<div class="reveal glass" data-reveal hidden>
<div class="reveal-head"><span class="tile tile-sm">{icon("key")}</span><div><h2 class="h3">Tu licencia</h2>
<p class="muted small" data-reveal-meta aria-live="polite">Buscando tu licencia…</p></div></div>
<div data-reveal-box hidden>{code_block("lic-reveal", "LIC-…", "KEYFLINT_LICENSE")}
<p class="lic-help good">Guardada en este navegador: el instalador ya la tiene puesta. También te llega por correo.</p></div>
</div>
<ol class="steps steps-row">
<li class="step"><span class="tile tile-sm">{icon("mail")}</span><div><h3><span class="step-n">1</span>Abre el correo</h3><p>Copia la licencia. Revisa spam si no aparece.</p></div></li>
<li class="step"><span class="tile tile-sm">{icon("download")}</span><div><h3><span class="step-n">2</span>Instala un servidor</h3><p>Pega la licencia en el instalador y elige tu cliente.</p></div></li>
<li class="step"><span class="tile tile-sm">{icon("chat")}</span><div><h3><span class="step-n">3</span>Úsalo</h3><p>Pide la tarea a tu agente en lenguaje natural.</p></div></li>
</ol>
<div class="cta-row center"><a class="btn btn-primary btn-lg" href="/#instalar">Ir al instalador</a><a class="btn btn-ghost btn-lg" href="/empezar/">Ver la guía</a></div>
<form class="recover glass" data-recover-form novalidate>
<div><h2 class="h3">¿No te ha llegado en unos minutos?</h2>
<p class="muted small">Escribe el correo que usaste al pagar y te enviaremos un enlace de acceso de un solo uso con tu licencia.</p></div>
<div class="recover-row"><input type="email" name="email" autocomplete="email" placeholder="tu@correo.com" required aria-label="Correo electrónico">
<button class="btn btn-ghost" type="submit">{icon("mail")}Enviar enlace</button></div>
<p class="lic-help" data-recover-msg aria-live="polite"></p>
</form>
<p class="muted small center">¿Sigue sin llegar? Escribe a <a href="{SITE['contact']}">{e(CONTACT)}</a>.</p>
</div></section>"""
    return page("/gracias/", "Pago completado · Flint by KeyFlint", "Tu licencia está de camino.", body, noindex=True)


def not_found() -> str:
    return page("/404", "Página no encontrada · Flint by KeyFlint", "Página no encontrada.",
                f'<section class="hero hero-sm center"><div class="glow" aria-hidden="true"></div><div class="wrap narrow"><p class="eyebrow">Error 404</p>'
                f'<h1>Esta página no existe</h1><p class="lead">Puede que el enlace haya cambiado.</p>'
                f'<div class="cta-row center"><a class="btn btn-primary btn-lg" href="/">Ir al inicio</a>'
                f'<a class="btn btn-ghost btn-lg" href="/#catalogo">Ver catálogo</a></div></div></section>', noindex=True)


# ---------------------------------------------------------------- english

EN_TOOLS = [
    ("web", "web-intel", "Flint Web", "web-intel-mcp", "uvx web-intel-mcp",
     "Turn any web page into clean Markdown and audit its SEO.",
     "Clean Markdown, metadata and links from any page, the site's tech stack, and an SEO score from 0 to 100 with the 5 fixes that matter most."),
    ("data", "dataclean", "Flint Data", "dataclean-mcp", "uvx dataclean-mcp",
     "Clean and validate messy CSV and Excel files without losing a row.",
     "Real column types, European and US amounts and dates, mojibake and odd spaces removed, phones in E.164, duplicates and schema checks. Ambiguous values are flagged, never dropped."),
    ("bank", "norma43", "Flint Bank", "norma43-mcp", "uvx norma43-mcp",
     "Parse Spanish Norma 43 bank statements and reconcile them with invoices.",
     "Reads Cuaderno 43 files with the same checks a bank runs and matches movements to invoices (1:1, one transfer for several invoices, partial payments), each with a score and a reason."),
    ("ledger", "contabridge", "Flint Ledger", "contabridge-mcp", "uvx contabridge-mcp",
     "Move journal entries between A3, ContaPlus, QuickBooks and Xero.",
     "Converts entries between a3, Sage ContaPlus / Sage 50, QuickBooks (IIF and CSV), Xero and Holded, adjusts sub-account lengths and checks that every entry balances."),
    ("fiscal", "verifactu", "Flint Fiscal", "verifactu-keyflint-mcp", "uvx --from verifactu-keyflint-mcp verifactu-mcp",
     "Check VeriFactu records and Facturae e-invoices before you send them.",
     "Verifies VERI*FACTU fingerprints and chaining, validates the XML against the AEAT schema, builds the tax QR and creates or validates Facturae 3.2.2. It reviews files: it is not a certified invoicing system."),
]
EN_PACKS = {
    "despacho-basico": ("Small accounting firms & solo advisors", "2,500 credits/mo, 3 seats, cancel anytime", "/mo"),
    "despacho-pro": ("Growing accounting firms & gestorías", "6,000 credits/mo, 10 seats, cancel anytime", "/mo"),
    "despacho-empresa": ("Enterprise accounting practices", "15,000 credits/mo, unlimited seats, high availability", "/mo"),
    "pro": ("For developers and single users", "1,000 new credits every month, cancel anytime", "/mo"),
}


def en_code(id_: str, text: str, label: str = "") -> str:
    return code_block(id_, text, label).replace("<span>Copiar</span>", "<span>Copy</span>")


def en_tool_card(t) -> str:
    glyph, slug, name, pkg, _, one, desc = t
    return f"""<div class="card mcp-card en-tool">
<div class="card-top"><img class="flint-glyph" src="/assets/flint/{glyph}.svg" alt="" width="44" height="44"><code class="muted small">{e(pkg)}</code></div>
<h3>{e(name)}</h3>
<p><b>{e(one)}</b></p>
<p class="muted small">{e(desc)}</p>
<span class="card-foot"><a class="link-arrow" href="https://github.com/ArceeDev/{'verifactu-mcp' if slug == 'verifactu' else pkg}" rel="noopener">GitHub{icon("arrow-right")}</a>
<a class="link-arrow" href="https://pypi.org/project/{pkg}/" rel="noopener">PyPI{icon("arrow-right")}</a></span>
</div>"""


EN_PACK_NAMES = {"pro": "Pro (Developer)"}


def en_plans() -> str:
    free = f"""<div class="plan">
<div class="plan-head"><h3 class="h3">Free</h3><p class="muted small">Try it on your own files</p></div>
<p class="price">€0</p><p class="credits">{SITE['free_credits']} credits</p>
<a class="btn btn-ghost btn-block" href="/en/try/">Get a free license</a>
<ul class="checks"><li>{icon("check")}All 5 tools</li><li>{icon("check")}No card</li><li>{icon("check")}1 device</li></ul></div>"""
    tp = SITE["topup"]
    tiers = "".join(f'<li>{icon("check")}€{a}+: {tp["rate"] * (100 + b) // 100} credits/€{f" (+{b}%)" if b else ""}</li>' for a, b, _ in tp["tiers"])
    topup = f"""<div class="plan featured"><span class="badge">No subscription</span>
<div class="plan-head"><h3 class="h3">Pay as you go</h3><p class="muted small">Pay only for what you use</p></div>
<p class="price">from €{tp['min']}</p><p class="credits">{tp['rate']} credits per euro · up to +40%</p>
<a class="btn btn-primary btn-block" href="/en/balance/#recargar">Top up</a>
<ul class="checks">{tiers}<li>{icon("check")}Adds to the same license</li><li>{icon("check")}Credits never expire</li></ul></div>"""
    out = [free, topup]
    for p in (p for p in SITE["packs"] if not p["id"].startswith("despacho")):
        who, billing, per = EN_PACKS.get(p["id"], ("", "", ""))
        feat, badge = "", ""
        name = EN_PACK_NAMES.get(p["id"], p["name"])
        out.append(f"""<div class="plan{feat}">{badge}
<div class="plan-head"><h3 class="h3">{e(name)}</h3><p class="muted small">{e(who)}</p></div>
<p class="price">${p['price']:,}<span class="muted small">{per}</span></p><p class="credits">{p['credits']:,} credits</p>
<a class="btn {'btn-primary' if p.get('featured') else 'btn-ghost'} btn-block" href="{e(p['checkout'])}" rel="noopener" data-checkout>Buy {e(name)}</a>
<ul class="checks"><li>{icon("check")}{e(billing)}</li><li>{icon("check")}{p.get('seats', 3)} devices</li><li>{icon("check")}Failed calls are free</li></ul></div>""")
    return "".join(out)


EN_USAGE = [("web-intel", "Read a web page as Markdown", 1), ("web-intel", "Full SEO audit", 3),
            ("norma43", "Parse a Norma 43 bank statement", 1), ("norma43", "Reconcile a statement with invoices", 3),
            ("contabridge", "Convert a journal (e.g. A3 to Xero)", 2), ("contabridge", "Validate a journal before import", 1),
            ("norma43", "Validate an IBAN or Spanish tax ID", 0)]


def en_usage_rows() -> str:
    by = {m["slug"]: m for m in MCPS}
    return "".join(f'<tr><td><span class="row"><span class="row-ic">{icon(by[s]["icon"])}</span>{e(t)}</span></td>'
                   f'<td class="r"><span class="credit{" free" if c == 0 else ""}">{"Free" if c == 0 else f"{c} cr"}</span></td></tr>'
                   for s, t, c in EN_USAGE)


def en_balance() -> str:
    with lang_ctx("en"):
        return balance_page()


def en_start() -> str:
    with lang_ctx("en"):
        ins = installer(ALL)
        uv_mac = code_block("uv-mac", "curl -LsSf https://astral.sh/uv/install.sh | sh", "macOS and Linux · Terminal")
        uv_win = code_block("uv-win", 'powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"', "Windows · PowerShell")
    faq = [("The tools don't show up", "Fully restart the client (on Windows, also quit it from the system tray). Check that uvx --version works in a new terminal."),
           ("It says the license is not valid", f"Make sure you copied the whole license, with no spaces, into KEYFLINT_LICENSE. Still failing? Email {CONTACT}."),
           ("I ran out of credits", "The tool returns a top-up link. Top-ups are added to the same license, so you don't change any config.")]
    body = f"""
<section class="hero hero-sm"><div class="glow" aria-hidden="true"></div><div class="wrap narrow">
<nav class="crumbs" aria-label="Breadcrumb"><a href="/en/">Home</a>{icon("chevron-right")}<span aria-current="page">Guide</span></nav>
<h1>Get started in three steps</h1>
<p class="lead">From zero to your first working tool in about two minutes. No coding needed.</p>
</div></section>
<section class="section tight"><div class="wrap narrow">
<ol class="guide">
<li class="g-step" id="license"><span class="g-n">1</span><div class="g-body">
<h2>Get your license</h2>
<p>Your license looks like <code>LIC-…</code>, arrives by email and works with every tool.</p>
<div class="choice">
<a class="choice-card" href="/en/try/"><span class="tile tile-sm">{icon("key")}</span><span class="cc-text"><b>Free · {SITE['free_credits']} credits</b><span class="muted small">Instant, no card.</span></span>{icon("arrow-right")}</a>
<a class="choice-card" href="/en/#pricing"><span class="tile tile-sm">{icon("card")}</span><span class="cc-text"><b>Paid plan</b><span class="muted small">License right after payment.</span></span>{icon("arrow-right")}</a>
</div></div></li>
<li class="g-step" id="uv"><span class="g-n">2</span><div class="g-body">
<h2>Install uv, once</h2>
<p><a href="https://docs.astral.sh/uv/" rel="noopener">uv</a> downloads and runs the tools in isolation on your machine. Only needed for local mode; the remote connector needs nothing. Open a terminal and run the command for your system:</p>
{uv_mac}
{uv_win}
<p class="note">{icon("info")}<span>Then close and reopen your client so it finds <code>uvx</code>.</span></p>
</div></li>
<li class="g-step"><span class="g-n">3</span><div class="g-body">
<h2>Add the tools to your client</h2>
<p>Paste your license and copy the config with all {len(MCPS)} tools at once. For a single tool with one-click install, use the picker on the <a href="/en/#install">home page</a>.</p>
<div class="install-card glass">{ins}</div>
</div></li>
<li class="g-step"><span class="g-n g-ok">{icon("check")}</span><div class="g-body">
<h2>Check it</h2>
<p>Ask your agent: <q>how many credits do I have left?</q> It uses the free <code>credits_balance</code> tool and tells you your balance.</p>
<div class="faq">{faq_html(faq)}</div>
</div></li>
</ol>
</div></section>"""
    ld = [{"@context": "https://schema.org", "@type": "HowTo", "name": "Install a Flint MCP server", "totalTime": "PT2M", "inLanguage": "en",
           "step": [{"@type": "HowToStep", "name": n} for n in ["Get your license", "Install uv", "Add the server to your MCP client", "Check it with your agent"]]}]
    return page("/en/start/", "How to install an MCP server in Claude, Cursor or VS Code · Flint by KeyFlint",
                "Step-by-step guide to install MCP servers in Claude Desktop, Claude Code, Cursor, VS Code, Codex, Antigravity and Windsurf with a free license.",
                body, ld, lang="en")


def en_home() -> str:
    clients = "".join(f'<li>{brand(ic)}<span>{e(n)}</span></li>' for _, n, ic in MARQUEE) + \
        f'<li>{icon("plug")}<span>Any MCP client</span></li>'
    cards = "".join(en_tool_card(t) for t in EN_TOOLS)
    feats = [
        ("target", "Deterministic", "Same file in, same result out. Run it twice and the SHA-256 of the output matches."),
        ("refund", "Pay only when it works", "Each tool has a fixed credit cost. Invalid files are rejected before charging, and failed calls are refunded automatically."),
        ("shield", "Flags, never guesses", "Anything uncertain is marked for review instead of being invented."),
        ("lock", "Your files stay with you", "Run locally with uvx and your files never leave your machine, or use the remote connector with OAuth."),
        ("key", "One license, every tool", "Signed Ed25519 license tokens, verified locally in under a millisecond."),
        ("ledger", "Source on GitHub", "Plain, tested Python under the Business Source License 1.1. Read exactly what your AI runs."),
    ]
    feat_html = "".join(f'<div class="feat"><span class="tile tile-sm">{icon(i)}</span><h3>{t}</h3><p>{d}</p></div>' for i, t, d in feats)
    with lang_ctx("en"):
        picker, installers = install_picker()
        quick, demo, sealed, roi = quick_install(), live_demo(), seal(compact=True), roi_calc()
    faq = [
        ("What is MCP?", "The Model Context Protocol is the open standard that lets AI clients such as Claude, ChatGPT, Cursor and VS Code call external tools. Flint is a set of MCP servers your AI can call when it needs an exact answer."),
        ("Is it open source?", "The code is public on GitHub under the Business Source License 1.1: you can read it, run it and audit it. Commercial use goes through a license with credits."),
        ("Where are my files processed?", "Locally, if you run the servers with uvx: only the license check and the credit count reach our servers. With the remote connector, files are processed to answer the call and are not stored."),
        ("Is Flint Fiscal a certified invoicing system?", "No. It reviews VeriFactu and Facturae files before you send them. It does not send anything to the Spanish tax agency and does not certify compliance."),
        ("Why so many Spanish formats?", "That is where AI fails most and nobody else covers it: Norma 43 statements, a3 and ContaPlus exports, VeriFactu. Flint Web and Flint Data work for any country."),
        ("What if I run out of credits or want a refund?", "Tools tell your AI when credits run out and nothing is charged. Top up from €5 and the credits land on the same license, with no config changes. Within 14 days we refund a top-up or your first Pro month if you used less than 20% of its credits; failed calls are never charged."),
    ]
    body = f"""
<section class="hero"><div class="glow" aria-hidden="true"></div><div class="wrap hero-grid">
<div class="hero-copy">
<div class="kicker"><span class="pill"><span class="pill-dot"></span><span>Deterministic Accounting Tools &amp; MCP Servers</span></span></div>
<h1>Deterministic tools your AI can trust with numbers</h1>
<p class="lead">AI is great at writing and bad at numbers. Flint gives Claude, ChatGPT, Cursor and VS Code tools that compute instead of guess: bank reconciliation, accounting exports, e-invoicing checks, data cleaning and web audits.</p>
<div class="doors-wrap">
<div class="doors-head"><p class="doors-title">Choose your entry path</p><span class="doors-hint">Direct path tailored to your workflow</span></div>
<nav class="doors" aria-label="Choose your profile">
<a class="door door-main" href="/en/batch/">
  <span class="door-icon">{icon("table")}</span>
  <span class="door-body">
    <span class="door-badge">For Accounting &amp; Finance Teams</span>
    <strong>Batch Statement &amp; Invoice Processing</strong>
    <small>Convert bank statements (Norma 43) to Excel and audit XML invoices online with zero setup.</small>
  </span>
  <span class="door-arr">{icon("arrow-right")}</span>
</a>
<a class="door door-tech" href="#install">
  <span class="door-icon">{icon("terminal")}</span>
  <span class="door-body">
    <span class="door-badge">For AI Engineers &amp; Developers</span>
    <strong>Deterministic MCP Servers for Claude &amp; Cursor</strong>
    <small>Run local tools via uvx with Ed25519 verified licenses. 0% calculation hallucinations.</small>
  </span>
  <span class="door-arr">{icon("arrow-right")}</span>
</a>
</nav>
</div>
<div class="cta-row"><a class="btn btn-primary btn-lg" href="/en/try/">{icon("key")}Get {SITE['free_credits']} free credits</a>
<a class="btn btn-ghost btn-lg" href="#live">{icon("arrow-right")}Try it live, no install</a></div>
<ul class="assure"><li>{icon("check")}No card</li><li>{icon("check")}Pay per successful call</li><li>{icon("check")}Source on GitHub</li></ul>
</div>
<figure class="demo glass en-video"><video controls preload="none" playsinline poster="/assets/video/flint-launch-en.webp" width="1280" height="720">
<source src="/assets/video/flint-launch-en.mp4" type="video/mp4"></video>
<figcaption class="demo-foot"><span>{icon("shield")}Real output from Flint Bank, run twice: same hash</span><span class="tabnum">63 s</span></figcaption></figure>
</div></section>

<section class="clients" aria-label="Works with"><div class="wrap clients-in">
<p class="clients-title">Works with</p><div class="marquee"><div class="marquee-track"><ul class="client-list">{clients}</ul><ul class="client-list" aria-hidden="true">{clients}</ul></div></div></div></section>

<section class="section" id="tools"><div class="wrap">
<div class="section-head"><p class="eyebrow">Five tools, one account</p><h2>The AI proposes. Flint checks.</h2>
<p class="lead-sm">Each tool does one exact job end to end and validates data the way the destination software does.</p></div>
<div class="grid-3">{cards}</div>
</div></section>
{demo}
<section class="section"><div class="wrap">
<div class="section-head"><p class="eyebrow">Why Flint</p><h2>Built for work where "almost right" fails</h2></div>
<div class="feat-grid">{feat_html}</div>
</div></section>
{sealed}
<section class="section" id="install"><div class="wrap install-grid">
<div class="section-head left"><p class="eyebrow">How it works</p><h2>Connected in two minutes</h2>
<ol class="steps">
<li class="step"><span class="tile tile-sm">{icon("key")}</span><div><h3><span class="step-n">1</span>Get a license</h3><p>{SITE['free_credits']} free credits or a paid plan. You see it on screen and get it by email.</p></div></li>
<li class="step"><span class="tile tile-sm">{icon("plug")}</span><div><h3><span class="step-n">2</span>Connect your AI</h3><p>Add the remote connector URL in Claude or ChatGPT and sign in with your license, or run it locally with uvx in Cursor, VS Code or Claude Desktop.</p></div></li>
<li class="step"><span class="tile tile-sm">{icon("chat")}</span><div><h3><span class="step-n">3</span>Just ask</h3><p>"Reconcile October's statement with invoices.csv". Your AI picks the tool and shows the cost.</p></div></li>
</ol></div>
<div class="install-card glass">{quick}<p class="quick-or muted small">or pick a tool and a client</p><div class="picker" role="group" aria-label="Pick a tool">{picker}</div>{installers}</div>
</div></section>

<section class="section alt" id="pricing"><div class="wrap">
<div class="section-head"><p class="eyebrow">Pricing</p><h2>One credit balance for every tool</h2>
<p class="lead-sm">A €{SITE["topup"]["min"]} top-up ({SITE["topup"]["min"] * SITE["topup"]["rate"]} credits) reads and reconciles 25 Norma 43 statements at 4 credits each.</p></div>
<div class="plans">{en_plans()}</div>
<p class="muted small center">Accounting firm? <a href="/en/batch/">Process a month of Norma 43 and VERI*FACTU files in your browser</a>: drop, paste your license, download the Excel summary.</p>
<p class="muted small center fine">{icon("lock")}Secure checkout with Stripe. Top-ups in euros with VAT included; Pro in USD plus local taxes. You receive an invoice with NIF/VAT. By purchasing you accept the <a href="/terminos/">terms</a>, the <a href="https://keyflint.dev/privacy.html">privacy policy</a>, and the <a href="/reembolsos/">refund policy</a>.</p>
</div></section>
<section class="section"><div class="wrap usage-grid">
<div class="section-head left"><p class="eyebrow">How far it goes</p><h2>Cost of common tasks</h2>
<p class="lead-sm">Each tool tells your AI its cost before it runs. Validations and utilities are free.</p></div>
<div class="table-wrap card-flat"><table><thead><tr><th scope="col">Task</th><th scope="col" class="r">Cost</th></tr></thead><tbody>{en_usage_rows()}</tbody></table></div>
</div></section>
{roi}

<section class="section"><div class="wrap faq-grid">
<div class="section-head left"><p class="eyebrow">FAQ</p><h2>Questions</h2>
<p class="lead-sm">Anything else? Email <a href="{SITE['contact']}">{e(CONTACT)}</a>. A real person answers within one business day.</p></div>
<div class="faq">{faq_html(faq)}</div>
</div></section>

<section class="section"><div class="wrap"><div class="cta-band">
<div><h2>Try it on your own files</h2><p class="lead-sm">{SITE['free_credits']} free credits, no card. Built solo from Spain.</p></div>
<div class="cta-row"><a class="btn btn-primary btn-lg" href="/en/try/">Get a free license</a><a class="btn btn-ghost btn-lg" href="https://github.com/ArceeDev" rel="noopener">See the code</a></div>
</div></div></section>"""
    ld = [{"@context": "https://schema.org", "@type": "SoftwareApplication", "name": "Flint by KeyFlint", "alternateName": "Flint", "applicationCategory": "BusinessApplication",
           "publisher": {"@type": "Organization", "name": "KeyFlint", "url": "https://keyflint.dev"},
           "operatingSystem": "Windows, macOS, Linux", "url": SITE["url"] + "/en/", "inLanguage": "en",
           "offers": {"@type": "Offer", "price": 0, "priceCurrency": "USD"}},
          faq_ld(faq)]
    return page("/en/", "Flint: deterministic MCP tools for bank files, accounting and CSVs",
                "MCP tools for Claude, ChatGPT, Cursor and VS Code that compute instead of guess: Norma 43 reconciliation, A3/ContaPlus/QuickBooks/Xero exports, VeriFactu checks, CSV cleaning and SEO audits.",
                body, ld, lang="en")


def en_try() -> str:
    remotes = "".join(f'<li><b>{e(t[2])}</b> <code>https://mcp.keyflint.dev/{t[1]}/mcp</code></li>' for t in EN_TOOLS)
    with lang_ctx("en"):
        picker, installers = install_picker()
        quick = quick_install()
    body = f"""
<section class="hero hero-sm"><div class="glow" aria-hidden="true"></div><div class="wrap narrow">
<nav class="crumbs" aria-label="Breadcrumb"><a href="/en/">Home</a>{icon("chevron-right")}<span aria-current="page">Free trial</span></nav>
<h1>{SITE['free_credits']} free credits, no card</h1>
<p class="lead">Enter your email and get a license right away. It works with all 5 tools.</p>
</div></section>
<section class="section tight"><div class="wrap narrow">
<form class="recover glass" data-trial-form novalidate>
<div><h2 class="h3">Your trial license</h2>
<p class="muted small">One per email. No newsletter.</p></div>
<div class="recover-row"><input type="email" name="email" autocomplete="email" placeholder="you@company.com" required aria-label="Email">
<button class="btn btn-primary" type="submit">{icon("key")}Get my license</button></div>
<p class="lic-help" data-trial-msg aria-live="polite"></p>
</form>
<div class="reveal glass" data-trial-out hidden>
<div class="reveal-head"><span class="tile tile-sm">{icon("check")}</span><div><h2 class="h3">Ready: {SITE['free_credits']} credits</h2>
<p class="muted small">Saved in this browser. Keep it like a password.</p></div></div>
{en_code("lic-trial", "LIC-…", "KEYFLINT_LICENSE")}
</div>
</div></section>
<section class="section" id="install"><div class="wrap install-grid">
<div class="section-head left"><p class="eyebrow">Next step</p><h2>Install it in your client</h2>
<p class="lead-sm">Claude, ChatGPT, Claude Code, Cursor, VS Code and more. Your license fills in every snippet. Remote URLs: </p><ul class="muted small">{remotes}</ul>
<p class="muted small">By getting a license you accept the <a href="/terminos/">terms</a> (in Spanish, summarised in the <a href="/en/#pricing">FAQ</a>).</p></div>
<div class="install-card glass">{quick}<p class="quick-or muted small">or pick a tool and a client</p><div class="picker" role="group" aria-label="Pick a tool">{picker}</div>{installers}</div>
</div></section>"""
    return page("/en/try/", f"Try Flint free: {SITE['free_credits']} credits, no card",
                f"Get a free Flint license with {SITE['free_credits']} credits for all 5 MCP tools. No card.", body, lang="en")


def foot_en() -> str:
    tools = "".join(f'<li><a href="https://github.com/ArceeDev/{"verifactu-mcp" if t[1] == "verifactu" else t[3]}" rel="noopener">{e(t[2])}</a></li>' for t in EN_TOOLS)
    return f"""<footer class="foot"><div class="wrap">
<div class="foot-grid">
<div class="foot-brand"><a class="brand" href="/en/">{flint()}<span>Flint</span><span class="brand-tag">by KeyFlint</span></a>
<p class="muted small">Deterministic MCP tools for AI agents, with signed licenses and pay-per-use credits. Built in Spain.</p></div>
<div><h3>Tools</h3><ul>{tools}</ul></div>
<div><h3>Resources</h3><ul><li><a href="/en/try/">Free trial</a></li><li><a href="/en/start/">Install guide</a></li><li><a href="/en/#pricing">Pricing</a></li><li><a href="/en/balance/">Check balance</a></li><li><a href="/en/batch/">Batch processor</a></li><li><a href="https://github.com/ArceeDev" rel="noopener">GitHub</a></li><li><a href="/estado/">Status</a></li></ul></div>
<div><h3>Legal &amp; support</h3><ul><li><a href="/terminos/">Terms (ES)</a></li><li><a href="/reembolsos/">Refunds (ES)</a></li><li><a href="/aviso-legal/">Legal notice (ES)</a></li><li><a href="https://keyflint.dev/privacy.html">Privacy</a></li><li><a href="{SITE['contact']}">{e(CONTACT)}</a></li></ul></div>
</div>
<div class="foot-base">
<p class="muted small">© {dt.date.today().year} KeyFlint · Source on GitHub under BSL 1.1.</p>
<div class="badges">
<a class="badge-pill" href="https://stripe.com" rel="noopener"><span class="muted">Payments by</span>{brand("stripe")}<b>Stripe</b></a>
<a class="badge-pill kf" href="https://keyflint.dev"><span class="muted">Licensing</span><span class="kf-mark">{icon("logo", "logo")}by&nbsp;KeyFlint</span></a>
</div></div>
</div></footer>"""


ALT_LANG = {"/": "/en/", "/probar/": "/en/try/", "/saldo/": "/en/balance/", "/empezar/": "/en/start/", "/lote/": "/en/batch/"}


def status_page() -> str:
    rows = [("licenses", "Licencias y créditos", "licenses.keyflint.dev")] + [(t[1], t[2], f"/{t[1]}/mcp") for t in EN_TOOLS] + [("despacho", "Flint Despacho (Norma 43 + ContaBridge)", "/despacho/mcp")]
    lis = "".join(f'<li class="st-row"><div><b>{e(n)}</b><span class="muted small"> · <code>{e(d)}</code></span></div>'
                  f'<span class="st" data-st="{k}">Comprobando…</span></li>' for k, n, d in rows)
    body = f"""
<section class="hero hero-sm"><div class="glow" aria-hidden="true"></div><div class="wrap narrow">
<nav class="crumbs" aria-label="Ruta"><a href="/">Inicio</a>{icon("chevron-right")}<span aria-current="page">Estado</span></nav>
<h1>Estado del servicio</h1>
<p class="lead">Comprobamos en directo el servidor de licencias y las cinco herramientas en modo remoto. <span lang="en">Live status of licensing and the five remote tools.</span></p>
</div></section>
<section class="section tight"><div class="wrap narrow">
<ul class="st-list glass" data-status>{lis}</ul>
<p class="muted small">Última comprobación: <span data-st-time>…</span>. Los servidores locales (<code>uvx</code>) solo dependen de las licencias. ¿Algo raro? Escribe a <a href="{SITE['contact']}">{e(CONTACT)}</a>.</p>
</div></section>"""
    return page("/estado/", "Estado del servicio · Flint by KeyFlint", "Estado en directo de las licencias y de las herramientas remotas de Flint.", body)


# ---------------------------------------------------------------- legal

LEGAL = SITE["legal"]


def _ld(key: str, label: str) -> str:
    """Holder data from catalog.json; a visible placeholder until it is filled in."""
    v = LEGAL.get(key, "").strip()
    return e(v) if v else f'<mark class="todo">[PENDIENTE: {e(label)}]</mark>'


def legal_missing() -> list[str]:
    return [k for k in ("holder", "nif", "address") if not LEGAL.get(k, "").strip()]


def legal_page(path: str, crumb: str, title: str, lead: str, sections: list[tuple[str, str]]) -> str:
    toc = "".join(f'<li><a href="#s{i}">{e(h)}</a></li>' for i, (h, _) in enumerate(sections, 1))
    secs = "".join(f'<h2 id="s{i}">{e(h)}</h2>{b}' for i, (h, b) in enumerate(sections, 1))
    body = f"""
<section class="hero hero-sm"><div class="glow" aria-hidden="true"></div><div class="wrap narrow">
<nav class="crumbs" aria-label="Ruta"><a href="/">Inicio</a>{icon("chevron-right")}<span aria-current="page">{e(crumb)}</span></nav>
<h1>{e(title)}</h1>
<p class="lead">{lead}</p>
<p class="muted small">Última actualización: {e(LEGAL.get("updated", TODAY))}</p>
</div></section>
<section class="section tight"><div class="wrap narrow legal">
<nav class="legal-toc" aria-label="En esta página"><ol>{toc}</ol></nav>
{secs}
</div></section>"""
    return page(path, f"{title} · Flint by KeyFlint", re.sub(r"<[^>]+>", "", lead)[:158], body)


def terms_page() -> str:
    mail = e(LEGAL["email"])
    support = e(CONTACT)
    s = [
        ("Quién presta el servicio",
         f'<p>Flint (mcp.keyflint.dev) es un servicio de {_ld("holder", "nombre y apellidos")}, NIF {_ld("nif", "NIF")}, '
         f'con domicilio en {_ld("address", "domicilio")}. Contacto: <a href="mailto:{support}">{support}</a>. Más datos en el <a href="/aviso-legal/">aviso legal</a>.</p>'),
        ("Qué contratas",
         "<p>Acceso a los servidores MCP del catálogo (Flint Web, Data, Bank, Ledger y Fiscal), en tu equipo o en modo remoto, mediante una "
         "licencia con un saldo de créditos. Cada llamada correcta descuenta los créditos que indica la página de <a href=\"/precios/\">precios</a>; "
         "las llamadas que fallan no descuentan nada.</p>"),
        ("Tu licencia",
         "<ul><li>La licencia es una clave personal. Quien la tenga puede gastar sus créditos: guárdala como una contraseña.</li>"
         "<li>Cada licencia permite un número de equipos: 1 en la prueba gratis y 3 en Pro.</li>"
         "<li>Si la pierdes, puedes recuperarla con un enlace a tu email desde <a href=\"/saldo/\">Mi saldo</a>.</li>"
         "<li>No puedes revender, alquilar ni compartir públicamente licencias o créditos.</li></ul>"),
        ("Planes, créditos y vigencia",
         "<ul><li><b>Prueba gratis:</b> 25 créditos, una por persona, sin tarjeta. Válida 12 meses.</li>"
         "<li><b>Recarga libre:</b> pagas el importe que eliges (de 5 € a 500 €) y los créditos se suman a tu misma licencia, con más créditos por euro a partir de 20 €. No caducan mientras el servicio exista.</li>"
         "<li><b>Pro:</b> suscripción mensual con 1.000 créditos nuevos cada mes, que se gastan antes que los de tus recargas. Los créditos mensuales que no uses no pasan al mes siguiente; los recargados se conservan. Puedes cancelar cuando quieras y no se te cobrará el mes siguiente.</li></ul>"),
        ("Precio y pago",
         "<p>Los precios están en la página de <a href=\"/precios/\">precios</a>. Las recargas se pagan en euros con el IVA incluido; Pro, en dólares (USD) más los impuestos de tu país. "
         "El pago lo procesa Stripe, que te muestra el importe final y te envía la factura, en la que puedes añadir tu NIF o número de IVA. Si en tu compra aparece Stripe como vendedor, "
         "Stripe gestiona el cobro y los impuestos; el uso de las herramientas se rige por estos términos.</p>"),
        ("Desistimiento y reembolsos",
         "<p>Tienes 14 días para pedir el reembolso completo y, en muchos casos, también después de usar créditos. Lo explicamos en la "
         "<a href=\"/reembolsos/\">política de reembolso</a>.</p>"),
        ("Qué hacen y qué no hacen las herramientas",
         "<ul><li>Son deterministas: el mismo fichero da el mismo resultado. Aun así, revisa siempre el resultado antes de usarlo en tu contabilidad, en tus impuestos o ante terceros.</li>"
         "<li>No son asesoramiento contable, fiscal ni legal.</li>"
         "<li>Flint Fiscal revisa ficheros VeriFactu y Facturae, pero no es un sistema informático de facturación (SIF), no envía nada a la Agencia Tributaria y no certifica el cumplimiento.</li>"
         "<li>Lo que la herramienta no puede casar o validar con seguridad se marca para que lo revises, en lugar de adivinarlo.</li></ul>"),
        ("Tus datos y tus ficheros",
         "<p>En modo local, los servidores se ejecutan en tu equipo y tus ficheros no salen de él. En modo remoto, los ficheros se procesan para responder a la llamada y no se guardan. "
         "Solo registramos la licencia, el email asociado y el consumo de créditos. Más detalle en la <a href=\"https://keyflint.dev/privacy.html\">política de privacidad</a> "
         "y, si eres empresa, en el <a href=\"https://keyflint.dev/dpa.html\">encargo de tratamiento</a>.</p>"),
        ("Uso aceptable",
         "<p>No puedes usar el servicio para actividades ilegales, para atacar o sobrecargar la infraestructura, ni para saltarte los límites de la licencia o de la prueba gratis. "
         "Si lo haces, podemos suspender la licencia; si es de pago y no hubo abuso, te devolveremos la parte no usada.</p>"),
        ("Código y propiedad intelectual",
         "<p>El código de los servidores está publicado en GitHub con licencia Business Source License 1.1, que permite leerlo y usarlo según sus condiciones. "
         "Las marcas KeyFlint y Flint, la web y sus textos no se ceden.</p>"),
        ("Disponibilidad y responsabilidad",
         "<p>Trabajamos para que el servicio esté siempre disponible, pero no garantizamos un tiempo de actividad concreto. Responderemos de los daños causados por dolo o culpa grave "
         "y de lo que la ley no permita limitar. En lo demás, nuestra responsabilidad se limita al importe que hayas pagado en los 12 meses anteriores. "
         "Si eres consumidor, conservas todos los derechos que te reconoce la ley.</p>"),
        ("Cambios en estos términos",
         "<p>Si cambiamos algo importante, lo avisaremos por email con 15 días de antelación. Los cambios no afectan a los créditos que ya hayas comprado.</p>"),
        ("Ley aplicable y reclamaciones",
         f"<p>Se aplica la ley española. Escríbenos primero a <a href=\"mailto:{support}\">{support}</a> o a <a href=\"mailto:{mail}\">{mail}</a>; respondemos en menos de 48 horas laborables. "
         "Si eres consumidor, puedes reclamar ante los juzgados de tu domicilio.</p>"),
    ]
    return legal_page("/terminos/", "Términos", "Términos de uso",
                      "Las condiciones para usar los servidores MCP y comprar créditos, en lenguaje claro.", s)


def refunds_page() -> str:
    support = e(CONTACT)
    s = [
        ("Resumen",
         "<ul><li><b>Las llamadas que fallan no se cobran:</b> no tienes que pedir nada.</li>"
         "<li><b>14 días de garantía:</b> si no te convence una recarga o el primer mes de Pro, te devolvemos todo si has usado menos del 20 % de sus créditos.</li>"
         "<li><b>Pro:</b> cancelas cuando quieras y no se te vuelve a cobrar.</li></ul>"),
        ("Cómo pedir un reembolso",
         f"<p>Escribe a <a href=\"mailto:{support}\">{support}</a> desde el email de la compra, en los 14 días siguientes al pago. "
         "No hace falta que expliques el motivo. Lo tramitamos en un máximo de 3 días laborables y Stripe lo devuelve al mismo medio de pago, normalmente en 5 a 10 días.</p>"),
        ("Qué pasa con la licencia",
         "<p>Al devolver una recarga se retiran de tu licencia los créditos que aportó; el resto de tu saldo y tu licencia siguen igual. Al devolver Pro se cancela la suscripción.</p>"),
        ("Derecho de desistimiento",
         "<p>Si eres consumidor, la ley te da 14 días para desistir de la compra. Como los créditos son contenido digital que se entrega al momento, "
         "ese derecho se pierde sobre la parte que empiezas a usar con tu consentimiento (lo aceptas al recargar). Nuestra garantía va más allá: mientras hayas usado menos del 20 % de los créditos, te devolvemos todo igualmente.</p>"),
        ("Suscripción Pro",
         "<p>Puedes cancelar en cualquier momento desde el enlace de gestión del correo de Stripe o escribiéndonos. Conservas los créditos hasta el final del mes pagado y no se te cobra el siguiente. "
         "Si cancelas en los 14 días siguientes a un cobro y has usado menos del 20 % de los créditos de ese mes, te devolvemos ese mes.</p>"),
        ("Errores de cobro",
         "<p>Si te hemos cobrado dos veces o algo no cuadra, lo devolvemos siempre, sin plazo.</p>"),
    ]
    return legal_page("/reembolsos/", "Reembolsos", "Política de reembolso",
                      "Si algo no funciona, no pagas. Y si no te convence, te devolvemos el dinero.", s)


def trust_page() -> str:
    """/confianza/: qué datos salen del despacho en cada modo, subencargados y encargo de tratamiento (art. 28 RGPD)."""
    mail, support = e(LEGAL["email"]), e(CONTACT)
    s = [
        ("Qué sale de tu ordenador en cada modo",
         '<div class="table-wrap"><table><thead><tr><th>Cómo lo usas</th><th>Dónde se procesa el fichero</th><th>Qué recibe Flint</th></tr></thead><tbody>'
         '<tr><td><b>Modo local</b>: Claude Desktop (.mcpb), Cursor, VS Code o Claude Code con <code>uvx</code></td>'
         '<td>En tu ordenador. El fichero no sale del despacho.</td><td>La licencia y el número de créditos gastados.</td></tr>'
         '<tr><td><b>Modo remoto</b>: conector por URL, <a href="/lote/">procesador en el navegador</a> o carpeta vigilada</td>'
         '<td>Viaja cifrado (HTTPS) a <code>mcp.keyflint.dev</code>, se procesa en memoria y se descarta al responder. No se guarda.</td>'
         '<td>Además: un registro de uso con la huella SHA-256 truncada de la licencia, la herramienta, si salió bien, los créditos y la duración. Nunca el contenido.</td></tr>'
         '<tr><td><b>Tu asistente de IA</b> (Claude, ChatGPT, Cursor…)</td><td>Lo que escribas o pegues en el chat lo trata ese proveedor, según tu contrato con él.</td>'
         '<td>Nada. Las herramientas de Flint no usan IA ni envían datos a ningún modelo.</td></tr>'
         '</tbody></table></div>'
         '<p><b>Para datos sujetos a secreto profesional, usa el modo local.</b> Así el fichero del cliente no sale del despacho y solo viaja la licencia.</p>'),
        ("Garantías técnicas",
         '<ul><li><b>Sin IA en el cálculo:</b> las herramientas aplican reglas fijas. El mismo fichero da siempre el mismo resultado, y lo que no se puede casar con certeza queda marcado para que lo revises.</li>'
         '<li><b>Sin entrenamiento:</b> no usamos tus ficheros para entrenar nada, ni propio ni de terceros.</li>'
         '<li><b>Código a la vista:</b> los servidores están publicados en GitHub y PyPI, así que tu informático puede revisar qué hacen. También el <a href="/lote.py">script de la carpeta vigilada</a>.</li>'
         '<li><b>Cobro justo:</b> si una herramienta falla, los créditos se devuelven solos.</li>'
         '<li><b>Licencia verificada sin conexión</b> (firma Ed25519): el modo local funciona aunque nuestro servidor no responda en ese momento.</li></ul>'),
        ("Subencargados",
         '<div class="table-wrap"><table><thead><tr><th>Proveedor</th><th>Para qué</th><th>Dónde</th></tr></thead><tbody>'
         '<tr><td>Cloudflare, Inc.</td><td>Web, inicio de sesión de los conectores y ejecución remota de las herramientas (en memoria, sin guardar contenido); registro de uso sin contenido</td><td>Red de Cloudflare</td></tr>'
         '<tr><td>Fly.io, Inc.</td><td>Servidor de licencias y créditos</td><td>UE (París)</td></tr>'
         '<tr><td>Cloudflare R2</td><td>Copias de seguridad cifradas del servidor de licencias</td><td>UE</td></tr>'
         '<tr><td>Resend</td><td>Correos con la licencia y avisos de saldo</td><td>Transferencia con DPF / cláusulas tipo</td></tr>'
         '<tr><td>Stripe</td><td>Pagos con tarjeta. Flint nunca ve los datos de la tarjeta.</td><td>Stripe Payments Europe</td></tr>'
         '</tbody></table></div>'
         f'<p>Avisamos por correo antes de añadir o cambiar un subencargado. Si te opones, puedes dejar de usar el servicio y pedir el reembolso del saldo no consumido según los <a href="/reembolsos/">reembolsos</a>.</p>'),
        ("Encargo de tratamiento (art. 28 RGPD)",
         f'<p>Cuando usas el modo remoto con datos de tus clientes, tu despacho es el responsable (o encargado) y Flint actúa como encargado (o subencargado) del tratamiento. '
         f'El modelo de contrato está en <a href="https://keyflint.dev/dpa.html">keyflint.dev/dpa.html</a>. Si tu despacho usa su propio modelo, envíalo a <a href="mailto:{mail}">{mail}</a> y lo firmamos.</p>'
         '<p>En modo local Flint no accede a los datos de tus clientes, así que no hace falta encargo para el contenido de los ficheros.</p>'),
        ("Contacto",
         f'<p>Protección de datos: <a href="mailto:{mail}">{mail}</a>. Soporte: <a href="mailto:{support}">{support}</a>. '
         'Titular y datos fiscales en el <a href="/aviso-legal/">aviso legal</a>.</p>'),
    ]
    return legal_page("/confianza/", "Confianza", "Confianza y protección de datos para despachos",
                      "Qué sale de tu despacho en cada modo, quién lo trata y cómo firmamos el encargo de tratamiento. Para datos con secreto profesional, el modo local procesa todo en tu ordenador.",
                      s)


def notice_page() -> str:
    mail = e(LEGAL["email"])
    support = e(CONTACT)
    s = [
        ("Titular",
         f'<ul><li><b>Titular:</b> {_ld("holder", "nombre y apellidos")}</li>'
         f'<li><b>NIF:</b> {_ld("nif", "NIF")}</li>'
         f'<li><b>Domicilio:</b> {_ld("address", "domicilio")}</li>'
         f'<li><b>Email:</b> <a href="mailto:{support}">{support}</a> y <a href="mailto:{mail}">{mail}</a></li>'
         "<li><b>Actividad:</b> desarrollo y venta de software (servidores MCP) con licencia de uso por créditos.</li></ul>"
         "<p>Este aviso cumple el artículo 10 de la Ley 34/2002 de servicios de la sociedad de la información (LSSI).</p>"),
        ("Condiciones de uso de la web",
         "<p>Puedes navegar por esta web libremente. Las condiciones de compra y uso de los servidores están en los <a href=\"/terminos/\">términos de uso</a> "
         "y en la <a href=\"/reembolsos/\">política de reembolso</a>.</p>"),
        ("Cookies y almacenamiento",
         "<p>Esta web no usa cookies de publicidad ni de seguimiento. Si compras o pides la prueba gratis, tu navegador guarda tu licencia (localStorage) para mostrártela; "
         "puedes borrarla cuando quieras desde el navegador. Las estadísticas de visitas, si las hay, son anónimas y sin cookies.</p>"),
        ("Propiedad intelectual",
         "<p>Los textos, el diseño y las marcas KeyFlint y Flint pertenecen al titular. El código de los servidores se publica en GitHub con licencia Business Source License 1.1. "
         "Los logotipos de terceros (Claude, ChatGPT, Cursor, VS Code, Stripe y otros) pertenecen a sus dueños y solo indican compatibilidad.</p>"),
        ("Enlaces",
         "<p>No respondemos del contenido de las webs de terceros a las que enlazamos.</p>"),
        ("Ley aplicable",
         "<p>Se aplica la ley española.</p>"),
    ]
    return legal_page("/aviso-legal/", "Aviso legal", "Aviso legal",
                      "Quién está detrás de mcp.keyflint.dev y cómo contactar.", s)


# ---------------------------------------------------------------- output

N43_GUIDES = {
    "santander": {"name": "Santander", "app": "Santander Empresas (Online Banking)",
                  "route": ["Entra en Santander Empresas y abre Cuentas.", "Elige la cuenta y el periodo en Movimientos o Extractos.", "Pulsa Descargar y escoge el formato Cuaderno 43 (también llamado Norma 43 o AEB43).", "Guarda el fichero: suele ser .txt, .n43 o .c43."]},
    "bbva": {"name": "BBVA", "app": "BBVA Net Cash / BBVA Net",
             "route": ["Entra en BBVA Net Cash y abre Cuentas > Consulta de movimientos.", "Filtra por cuenta y fechas.", "Elige Exportar y el formato Norma 43 (AEB43).", "Guarda el fichero resultante."]},
    "caixabank": {"name": "CaixaBank", "app": "CaixaBankNow Empresas",
                  "route": ["Entra en CaixaBankNow Empresas y abre Cuentas > Extractos o Movimientos.", "Selecciona cuenta y rango de fechas.", "Pulsa Descargar y elige Cuaderno 43.", "Guarda el fichero (suele ser .txt o .q43)."]},
    "sabadell": {"name": "Banco Sabadell", "app": "Sabadell Professional",
                 "route": ["Entra en Sabadell Professional y abre Cuentas > Movimientos.", "Elige cuenta y periodo.", "Usa Descargar o Exportar y selecciona Norma 43.", "Guarda el fichero."]},
}


def n43_guide_page(key: str) -> str:
    g = N43_GUIDES[key]
    n = g["name"]
    path = f"/descargar-norma-43-{key}/"
    steps = "".join(f'<li class="step"><span class="tile tile-sm">{icon(ic)}</span><div><h3><span class="step-n">{i}</span>{e(txt)}</h3></div></li>'
                    for i, (txt, ic) in enumerate(zip(g["route"], ("landmark", "table", "download", "check")), 1))
    others = " · ".join(f'<a href="/descargar-norma-43-{k}/">{e(v["name"])}</a>' for k, v in N43_GUIDES.items() if k != key)
    faq = [
        (f"¿Dónde descargo el Norma 43 de {n}?", f"En la banca online para empresas de {n} ({g['app']}), en el apartado de movimientos o extractos de la cuenta, con la opción de descarga en formato Cuaderno 43 o Norma 43. La ruta exacta cambia con las versiones; si no ves la opción, pídesela a tu gestor de {n} o a su soporte."),
        ("¿Cómo sé que el fichero es correcto?", "Ábrelo en el visor gratuito de Norma 43: comprueba que saldo inicial más movimientos da el saldo final y que los totales del registro 33 cuadran. Todo ocurre en tu navegador."),
        (f"¿Qué extensión tiene el fichero de {n}?", "Suele ser .n43, .c43, .q43 o .txt. Flint los lee igual: lo importante es que cada línea tenga 80 caracteres y empiece por registros 11, 22, 23, 33 y 88."),
        ("¿Cómo lo llevo a ContaSol, A3 o ContaPlus?", "Con el conversor de Norma 43: genera el fichero que importa tu programa, con un asiento por movimiento contra la subcuenta 572 y lo dudoso en la 555 para revisión."),
    ]
    body = f"""<section class="hero hero-sub"><div class="wrap narrow">
<p class="eyebrow">Guía · {e(n)}</p>
<h1>Cómo descargar el extracto Norma 43 de {e(n)}</h1>
<p class="lead">Ruta habitual en {e(g["app"])} para bajar el Cuaderno 43 y comprobarlo antes de contabilizarlo. Los menús de cada banco cambian: si algo no coincide, usa la ayuda del banco.</p>
</div></section>
<section class="section tight"><div class="wrap narrow">
<ol class="steps">{steps}</ol>
<div class="card-flat" style="margin-top:28px"><h2 class="h4">Después de descargarlo</h2>
<ul class="checks" style="margin-top:12px"><li>{icon("check")}<span><a href="/visor-norma-43/">Revísalo en el visor gratuito</a>: saldos y totales, sin subirlo a ningún sitio.</span></li>
<li>{icon("check")}<span>Conviértelo: <a href="/norma43-a-contasol/?utm_source=guia-{key}&amp;utm_medium=web&amp;utm_campaign=guias-n43">ContaSol</a> · <a href="/norma43-a-a3/?utm_source=guia-{key}&amp;utm_medium=web&amp;utm_campaign=guias-n43">A3</a> · <a href="/norma43-a-contaplus/?utm_source=guia-{key}&amp;utm_medium=web&amp;utm_campaign=guias-n43">ContaPlus</a> · <a href="/norma43-a-excel/?utm_source=guia-{key}&amp;utm_medium=web&amp;utm_campaign=guias-n43">Excel</a>.</span></li></ul>
<div class="cta-row" style="margin-top:12px"><a class="btn btn-primary" href="/probar/?utm_source=guia-{key}&amp;utm_medium=web&amp;utm_campaign=guias-n43">{icon("key")}<span>Probar gratis (25 créditos)</span></a></div></div>
{newsletter_box(f"guia-{key}", "Boletín del cierre: trucos mensuales para tu despacho", "Un correo al mes con guías reales de Norma 43, ContaSol, a3 y cambios de bancos. Sin spam y con baja en 1 clic.")}
<div class="faq" style="margin-top:40px"><h2 class="h3" style="margin-bottom:20px">Preguntas frecuentes</h2>{faq_html(faq)}</div>
<p class="muted small" style="margin-top:24px">Otros bancos: {others} · <a href="/que-es-norma-43/">Qué es el Norma 43</a> · <a href="/visor-norma-43/">Visor Norma 43</a></p>
</div></section>"""
    return page(path, f"Descargar Norma 43 de {n}: guía paso a paso · Flint by KeyFlint",
                f"Cómo descargar el extracto Norma 43 (Cuaderno 43) de {n}, comprobarlo gratis y pasarlo a ContaSol, A3 o ContaPlus.", body, [faq_ld(faq)])


def visor_page() -> str:
    """Visor Norma 43 gratuito: el análisis ocurre en el navegador, sin enviar el fichero."""
    faq = [
        ("¿Se sube mi extracto a algún servidor?", "No. El visor lee el fichero con JavaScript en tu navegador: no se envía ni a KeyFlint ni a nadie. Puedes comprobarlo con la pestaña Red de las herramientas de desarrollo o desconectando internet después de cargar la página."),
        ("¿Qué comprueba?", "Que saldo inicial más movimientos da el saldo final, que los totales de debe y haber del registro 33 coinciden con la suma de los apuntes y que el número de apuntes cuadra. Si algo no cuadra, lo marca."),
        ("¿Qué es un fichero Norma 43?", "El Cuaderno 43 de la AEB: un fichero de texto de 80 caracteres por línea que cada banco español ofrece como extracto electrónico, con registros 11 (cuenta), 22 (movimiento), 23 (concepto), 33 (totales) y 88 (fin)."),
        ("¿Y si mi banco solo da CSV o PDF?", "Este visor solo abre Norma 43. Para CSV y PDF usa el conversor a ContaSol, A3 o ContaPlus, que sí los interpreta."),
        ("¿Pasar el extracto a ContaSol, A3 o ContaPlus?", "Una vez revisado, conviértelo a un fichero que importe tu programa contable, con una prueba gratis de 25 créditos sin tarjeta."),
    ]
    body = f"""<section class="hero hero-sub"><div class="wrap narrow">
<p class="eyebrow">Herramienta gratuita</p>
<h1>Visor de Norma 43 online</h1>
<p class="lead">Abre un fichero .n43, .c43 o .q43 y comprueba al instante cuentas, saldos y movimientos. Se procesa en tu navegador: el extracto no sale de tu equipo.</p>
</div></section>
<section class="section tight"><div class="wrap narrow">
<div class="saldo-form glass batch">
<label class="drop" data-visor-drop><input type="file" accept=".n43,.c43,.q43,.txt,.aeb" class="sr-only" data-visor-input>
<span class="tile">{icon("download")}</span><b>Arrastra aquí tu Norma 43 o haz clic para elegirlo</b>
<span class="muted small">.n43 · .c43 · .q43 · .txt · hasta 10 MB · no se sube a ningún sitio</span></label>
<p class="note" data-visor-msg hidden>{icon("info")}<span></span></p>
</div>
<div data-visor-out hidden style="margin-top:24px"></div>
<div class="card-flat" style="margin-top:32px"><h2 class="h4">¿Y ahora qué?</h2>
<p class="muted small">Si el extracto cuadra, llévalo a tu programa contable sin teclear: <a href="/norma43-a-contasol/">Norma 43 a ContaSol</a> · <a href="/norma43-a-a3/">a A3</a> · <a href="/norma43-a-contaplus/">a ContaPlus</a> · <a href="/norma43-a-excel/">a Excel</a>. ¿Cómo lo descargo? {" · ".join(f'<a href="/descargar-norma-43-{k}/">{v["name"]}</a>' for k, v in N43_GUIDES.items())} · <a href="/que-es-norma-43/">Estructura Norma 43</a></p>
<div class="cta-row" style="margin-top:12px"><a class="btn btn-primary" href="/probar/?utm_source=visor&amp;utm_medium=web&amp;utm_campaign=visor-n43">{icon("key")}<span>Probar gratis (25 créditos)</span></a><a class="btn btn-quiet" href="/validar-iban-cif/">Validador IBAN y CIF</a></div></div>
{newsletter_box("visor-n43", "Recibe el Boletín del cierre (1 correo al mes)", "Trucos reales de conciliación bancaria, errores de la 555 y fechas clave de cierre sin publicidad. Doble confirmación.")}
<div class="faq" style="margin-top:40px"><h2 class="h3" style="margin-bottom:20px">Preguntas frecuentes</h2>{faq_html(faq)}</div>
</div></section>
<script defer src="/assets/visor.js?v={VERSION}"></script>"""
    return page("/visor-norma-43/", "Visor de Norma 43 online gratis (n43, c43) · Flint by KeyFlint",
                "Abre un fichero Norma 43 (Cuaderno 43) en el navegador y comprueba saldos, totales y movimientos. Gratis, sin subir el fichero.",
                body, [faq_ld(faq)])


def newsletter_box(source: str, title: str = "Boletín del cierre", lead: str = "Un correo al mes con casos reales de ContaSol, a3, Norma 43 y fechas de cierre. Sin spam.") -> str:
    """Caja reutilizable de captura por doble opt-in (/api/boletin/alta)."""
    return f"""<form class="recover glass" data-news-form data-news-source="{e(source)}" style="margin-top:28px" novalidate>
<div><h2 class="h4">{e(title)}</h2>
<p class="muted small">{e(lead)}</p></div>
<div class="recover-row"><input type="email" name="email" autocomplete="email" placeholder="tu@despacho.es" required aria-label="Correo para el boletín">
<button class="btn btn-ghost" type="submit">{icon("arrow-right")}Apuntarme (doble confirmación)</button></div>
<p class="lic-help" data-news-msg aria-live="polite">Solo te daremos de alta cuando pulses el enlace que enviaremos a tu correo.</p>
</form>"""


def newsletter_page() -> str:
    faq = [
        ("¿Con qué frecuencia escribís?", "Una vez al mes, antes del cierre o del trimestre, con trucos prácticos para despachos y novedades reales de Flint."),
        ("¿Cómo funciona la doble confirmación?", "Al apuntarte te enviamos un enlace a tu correo. No guardamos tu dirección en la lista hasta que pulsas ese enlace (LSSI y RGPD)."),
        ("¿Cómo me doy de baja?", "Cada correo lleva un enlace directo de baja en 1 clic sin contraseñas."),
    ]
    body = f"""<section class="hero hero-sub"><div class="wrap narrow">
<nav class="crumbs" aria-label="Ruta"><a href="/">Inicio</a>{icon("chevron-right")}<span aria-current="page">Boletín</span></nav>
<p class="eyebrow">Lista de despachos</p>
<h1>Boletín del cierre: 1 correo al mes</h1>
<p class="lead">Soluciones reales a errores de conciliación (cuenta 555, cuadre Norma 43, enlaces a ContaSol y a3) y herramientas gratuitas para asesorías.</p>
</div></section>
<section class="section tight"><div class="wrap narrow">
{newsletter_box("boletin", "Apúntate al Boletín del cierre", "Sin envíos comerciales ni correo diario. Doble confirmación y baja en 1 clic.")}
<div class="card-flat" style="margin-top:24px"><h2 class="h4">Herramientas gratuitas ya disponibles</h2>
<ul class="checks" style="margin-top:12px">
<li>{icon("check")}<span><a href="/visor-norma-43/">Visor Norma 43 online</a>: comprueba saldos y registro 33 sin subir el fichero.</span></li>
<li>{icon("check")}<span><a href="/validar-iban-cif/">Validador de IBAN, NIF, NIE, CIF y acreedor SEPA</a>: valida lotes desde Excel en el navegador.</span></li>
<li>{icon("check")}<span><a href="/probar/">25 créditos gratis</a> para probar la conversión real a ContaSol, a3, ContaPlus o Excel.</span></li>
</ul></div>
<div class="faq" style="margin-top:40px"><h2 class="h3" style="margin-bottom:20px">Preguntas frecuentes</h2>{faq_html(faq)}</div>
</div></section>"""
    return page("/boletin/", "Boletín del cierre para asesorías · Flint by KeyFlint",
                "Boletín mensual gratuito para despachos sobre Norma 43, ContaSol, a3 y herramientas contables deterministas. Doble confirmación.", body, [faq_ld(faq)])


def newsletter_confirm_page() -> str:
    body = f"""<section class="hero hero-sub"><div class="wrap narrow">
<h1>Confirmación del boletín</h1>
<p class="lead">Validando tu enlace de doble confirmación…</p>
</div></section>
<section class="section tight"><div class="wrap narrow" data-news-confirm>
<div class="card-flat"><p class="note" data-news-status aria-live="polite">Comprobando enlace…</p>
<div class="cta-row" style="margin-top:20px">
<a class="btn btn-primary" href="/visor-norma-43/">Abrir visor Norma 43</a>
<a class="btn btn-ghost" href="/validar-iban-cif/">Validador IBAN y CIF</a>
<a class="btn btn-quiet" href="/probar/">Activar 25 créditos gratis</a>
</div></div></div></section>"""
    return page("/boletin/confirmar/", "Confirmar suscripción · Flint by KeyFlint", "Confirmación del Boletín del cierre.", body, noindex=True)


def newsletter_unsub_page() -> str:
    body = """<section class="hero hero-sub"><div class="wrap narrow">
<h1>Baja del boletín</h1>
<p class="lead">Tramitando tu baja en un clic…</p>
</div></section>
<section class="section tight"><div class="wrap narrow" data-news-unsub>
<div class="card-flat"><p class="note" data-news-status aria-live="polite">Procesando baja…</p>
<div class="cta-row" style="margin-top:20px"><a class="btn btn-quiet" href="/">Volver al inicio</a></div></div>
</div></section>"""
    return page("/boletin/baja/", "Baja del boletín · Flint by KeyFlint", "Baja en un clic del Boletín del cierre.", body, noindex=True)


def validator_page() -> str:
    """Herramienta gratuita B2: validador IBAN / NIF / NIE / CIF / acreedor SEPA 100 % en navegador."""
    faq = [
        ("¿Los datos de clientes se suben a algún servidor?", "No. Todo el cálculo matemático (mod 97, CCC español, letra de NIF/NIE y dígito de control de CIF) ocurre en JavaScript en tu navegador. No hay llamadas de red."),
        ("¿Puedo pegar una columna entera desde Excel?", "Sí. Pega hasta 500 valores separados por saltos de línea, comas o punto y coma y se validan al instante."),
        ("¿Qué valida exactamente en un IBAN español?", "Comprueba la longitud (24 caracteres), el algoritmo ISO 13616 (mod 97) y además verifica los dos dígitos de control internos del Código Cuenta Cliente (entidad, oficina y cuenta)."),
        ("¿Cómo valida un identificador de acreedor SEPA (AT-02)?", "Elimina el sufijo de 3 caracteres del esquema (ej. 000), verifica el mod 97 ISO 13616 y, si el código nacional empieza por ES con 9 caracteres, valida también el NIF o CIF contenido."),
    ]
    body = f"""<section class="hero hero-sub"><div class="wrap narrow">
<nav class="crumbs" aria-label="Ruta"><a href="/">Inicio</a>{icon("chevron-right")}<span aria-current="page">Validador IBAN y CIF</span></nav>
<p class="eyebrow">Herramienta gratuita</p>
<h1>Validador gratuito de IBAN, NIF, NIE, CIF y acreedor SEPA</h1>
<p class="lead">Comprueba códigos individuales o pega una columna desde Excel (hasta 500 filas). Se calcula al instante en tu navegador, sin enviar datos de tus clientes.</p>
</div></section>
<section class="section tight"><div class="wrap narrow">
<form class="saldo-form glass" data-val-form novalidate>
<label class="demo-field"><span>Pega uno o varios códigos (uno por línea, coma o punto y coma)</span>
<textarea rows="6" spellcheck="false" placeholder="ES9121000418450200051332&#10;B84372291&#10;12345678Z&#10;ES14000B84372291" data-val-input></textarea></label>
<div class="cta-row"><button class="btn btn-primary" type="submit">{icon("check")}Validar ahora</button>
<button class="btn btn-ghost" type="button" data-val-sample>{icon("refresh")}Cargar ejemplos válidos</button></div>
<div data-val-out hidden style="margin-top:8px"></div>
</form>
<div class="card-flat" style="margin-top:28px"><h2 class="h4">¿Necesitas también conciliar extractos o generar remesas?</h2>
<p class="muted small">Si además limpias remesas SEPA o pasas extractos Norma 43 y CSV a ContaSol, A3 o ContaPlus, prueba Flint gratis con 25 créditos (o verifica ficheros gratis en el <a href="/visor-norma-43/">visor Norma 43</a>).</p>
<div class="cta-row" style="margin-top:12px"><a class="btn btn-primary" href="/probar/?utm_source=validador&amp;utm_medium=web&amp;utm_campaign=validador-iban-cif">{icon("key")}<span>Probar gratis (25 créditos)</span></a><a class="btn btn-ghost" href="/lote/">Procesador por lotes</a></div></div>
{newsletter_box("validador-iban", "Boletín del cierre para despachos", "Un correo al mes con herramientas gratuitas, trucos de Norma 43 y validaciones AEAT/SEPA.")}
<div class="faq" style="margin-top:40px"><h2 class="h3" style="margin-bottom:20px">Preguntas frecuentes</h2>{faq_html(faq)}</div>
</div></section>
<script defer src="/assets/validador.js?v={VERSION}"></script>"""
    return page("/validar-iban-cif/", "Validador IBAN, NIF, NIE, CIF y acreedor SEPA gratis · Flint by KeyFlint",
                "Comprueba online y gratis códigos IBAN (ES con DC bancario), NIF, NIE, CIF y acreedor SEPA por lotes sin enviar datos.", body, [faq_ld(faq)])


def n43_what_page() -> str:
    """Guía A6: estructura de un fichero Norma 43 (registros 11, 22, 23, 33 y 88)."""
    faq = [
        ("¿Por qué cada línea del Norma 43 mide exactamente 80 caracteres?", "Es el estándar clásico del Cuaderno 43 de la Asociación Española de Banca (AEB) de ancho fijo, pensado para garantizar el mismo esquema posicional en todos los bancos españoles."),
        ("¿Cómo sé si falta un registro o no cuadra el archivo?", "Compruébalo gratis en el Visor de Norma 43: verifica saldo inicial más movimientos igual al saldo final y los contadores de registro 33."),
        ("¿Qué hago si mi banco ya solo da CSV o PDF?", "Para bancos o pasarelas sin Cuaderno 43 (como Revolut, Stripe o cuentas particulares), usa los conversores de CSV/PDF a ContaSol, A3 o ContaPlus."),
    ]
    rows = "".join(
        f"<tr><td><code>{e(c)}</code></td><td>{e(n)}</td><td style='white-space:normal'>{e(d)}</td></tr>"
        for c, n, d in [
            ("11", "Cabecera de cuenta", "Código de banco, oficina, cuenta, fecha inicio/fin, signo y saldo inicial, divisa (978 = EUR) y titular."),
            ("22", "Movimiento principal", "Fecha operación y fecha valor (AAMMDD), concepto común y propio, signo debe/haber (1 cargo, 2 abono), importe en céntimos y referencias."),
            ("23", "Concepto complementario", "Hasta 5 líneas de detalle del movimiento anterior (texto del recibo, factura, ordenante o concepto ampliado)."),
            ("33", "Fin de cuenta", "Número y suma total de cargos (debe), número y suma total de abonos (haber) y saldo final para auditoría matemática."),
            ("88", "Fin de fichero", "Cierre del Cuaderno 43 con el recuento total de registros incluidos."),
        ]
    )
    body = f"""<section class="hero hero-sub"><div class="wrap narrow">
<nav class="crumbs" aria-label="Ruta"><a href="/">Inicio</a>{icon("chevron-right")}<span aria-current="page">Qué es Norma 43</span></nav>
<p class="eyebrow">Guía de referencia · Cuaderno 43</p>
<h1>Qué es el fichero Norma 43 y cómo leer sus registros</h1>
<p class="lead">Todo sobre el formato AEB Cuaderno 43 (extensiones .n43, .c43, .q43 o .txt): para qué sirve, qué contiene cada línea de 80 caracteres y cómo validarlo o contabilizarlo.</p>
</div></section>
<section class="section tight"><div class="wrap narrow">
<h2 class="h3">Estructura de registros del Cuaderno 43</h2>
<div class="tw uso" style="margin-top:12px"><table class="uso-t"><thead><tr><th>Registro</th><th>Nombre</th><th>Qué contiene</th></tr></thead><tbody>{rows}</tbody></table></div>
<div class="card-flat" style="margin-top:28px"><h2 class="h4">Errores habituales al abrir un Norma 43</h2>
<ul class="checks" style="margin-top:12px">
<li>{icon("check")}<span><b>Acentos cortados o símbolos raros:</b> muchos bancos exportan en Windows-1252 o CP850 en lugar de UTF-8. El visor y el conversor de Flint prueban ambos sin romper caracteres.</span></li>
<li>{icon("check")}<span><b>Descuadre por filtro parcial:</b> si descargas movimientos filtrados manualmente en vez de extracto cerrado, el registro 33 puede no coincidir con la suma real.</span></li>
<li>{icon("check")}<span><b>Saltos de línea alterados al abrir en Excel:</b> nunca guardes un .n43 con Excel (recorta ceros a la izquierda y rompe los 80 caracteres fijos).</span></li>
</ul>
<div class="cta-row" style="margin-top:14px"><a class="btn btn-primary" href="/visor-norma-43/">Abrir en el visor gratuito</a><a class="btn btn-ghost" href="/norma43-a-contasol/">Pasar a ContaSol</a><a class="btn btn-quiet" href="/norma43-a-a3/">Pasar a A3</a></div></div>
{newsletter_box("guia-n43", "Boletín del cierre (1 correo al mes)", "Guías técnicas contables, calendarios de cierre y herramientas gratis para tu despacho.")}
<div class="faq" style="margin-top:40px"><h2 class="h3" style="margin-bottom:20px">Preguntas frecuentes</h2>{faq_html(faq)}</div>
</div></section>"""
    return page("/que-es-norma-43/", "Qué es el fichero Norma 43 (Cuaderno 43): registros 11, 22, 23, 33 y 88 · Flint",
                "Guía clara de la estructura Norma 43 (AEB43): qué significa cada registro, errores comunes al abrirlo y visor gratuito online.", body, [faq_ld(faq)])


BANK_TARGET_COMBOS = [
    ("santander", "a3"), ("bbva", "a3"), ("caixabank", "a3"),
    ("santander", "contaplus_ascii"), ("bbva", "contaplus_ascii"), ("caixabank", "contaplus_ascii"),
]
for _bk, _tk in BANK_TARGET_COMBOS:
    _bname = BANK_PAGES[_bk]["name"]
    _slug_t = "contaplus" if _tk == "contaplus_ascii" else _tk
    SEO_KEYWORDS[f"/{_bk}-a-{_slug_t}/"] = (
        f"{_bk} {_slug_t}, importar extracto {_bk} {_slug_t}, norma 43 {_bk} {_slug_t}, csv {_bk} {N43_TARGETS[_tk]['file'].lower()}"
    )


def bank_target_page(bank_key: str, target_key: str) -> str:
    """Páginas A2: llevar extracto de banco español concreto a A3 (SUENLACE.DAT) o ContaPlus (XDiario.txt)."""
    b = BANK_PAGES[bank_key]
    t = N43_TARGETS[target_key]
    short, prog, fname = t["short"], t["program"], t["file"]
    slug_t = "contaplus" if target_key == "contaplus_ascii" else target_key
    path = f"/{bank_key}-a-{slug_t}/"
    steps = "".join(
        f'<li class="step"><span class="tile tile-sm">{icon(ic)}</span><div><h3><span class="step-n">{i}</span>{e(s)}</h3></div></li>'
        for i, (s, ic) in enumerate(zip(b["export"], ("landmark", "download", "check")), 1)
    )
    cols = "".join(f'<tr><td style="white-space:normal">{e(a)}</td><td style="white-space:normal">{e(c)}</td></tr>' for a, c in b["cols"])
    faq = [
        (f"¿Cómo importar el extracto de {b['name']} en {short}?",
         f"Descarga el Norma 43 (.n43/.c43) desde la banca de empresas o el CSV desde la web, súbelo aquí y descarga {fname} para {prog}. {t['import'].replace('<b>', '').replace('</b>', '').replace('&gt;', '>')}"),
        ("¿Qué subcuentas utiliza?", "Asienta cada movimiento contra la 572 que indiques y lleva lo no clasificado a la 555 para revisión sin adivinar cuentas."),
        ("¿Cuánto cuesta probarlo?", f"Tienes {SITE['free_credits']} créditos gratis al instante con tu correo (8 extractos), sin tarjeta; si un archivo falla no se descuenta nada."),
    ]
    body = f"""<section class="hero"><div class="glow" aria-hidden="true"></div><div class="wrap narrow">
<nav class="crumbs" aria-label="Ruta"><a href="/">Inicio</a>{icon("chevron-right")}<a href="{t['path']}">Norma 43 a {e(short)}</a>{icon("chevron-right")}<span aria-current="page">{e(b['name'])}</span></nav>
<h1>Importar extracto {e(b['name'])} (Norma 43 o CSV) en {e(short)}</h1>
<p class="lead">Convierte el fichero de {e(b['name'])} al formato {e(fname)} de {e(prog)}, comprobando saldos antes de importar y marcando en la 555 los movimientos sin regla.</p>
</div></section>
<section class="section tight"><div class="wrap narrow" data-batch data-batch-target="{target_key}">
<form class="saldo-form glass batch" data-batch-form novalidate>
<label class="lic"><span class="lic-label">{icon("key")}Tu correo o licencia</span>
<span class="lic-field"><input type="text" name="license" autocomplete="email" spellcheck="false" placeholder="tu@correo.com o LIC-…" required data-batch-lic></span>
<span class="lic-help">Escribe tu correo para activar <b>{SITE['free_credits']} créditos gratis</b> al instante o pega tu clave LIC-….</span></label>
<label class="lic"><span class="lic-label">{icon("landmark")}Subcuenta 572 de {e(b['name'])}</span>
<span class="lic-field"><input type="text" name="bank" inputmode="numeric" autocomplete="off" value="57200001" pattern="57[0-9]{{2,10}}" required data-batch-bank></span>
<span class="lic-help">La cuenta contable de {e(b['name'])} en {e(short)}.</span></label>
<label class="drop" data-batch-drop><input type="file" multiple accept=".n43,.c43,.q43,.csv,.pdf" class="sr-only" data-batch-input>
<span class="tile">{icon("download")}</span><b>Suelta aquí el Norma 43, CSV o PDF digital de {e(b['name'])}</b>
<span class="muted small">Vista previa inmediata · Cuadre verificado · hasta 10 MB</span></label>
<div class="sample-bar"><button type="button" class="btn-sample" data-batch-sample>{icon("refresh")}<span>Cargar extracto de prueba</span></button></div>
<div class="tw batch-list" data-batch-list hidden><table class="uso-t"><thead><tr><th>Fichero</th><th>Tipo</th><th>Estado</th><th>Detalle</th><th class="num"></th></tr></thead><tbody data-batch-rows></tbody></table></div>
<div class="batch-actions"><button class="btn btn-primary btn-lg" type="submit" data-batch-go disabled>{icon("refresh")}<span>Convertir a {e(fname)}</span></button>
<button class="btn btn-ghost" type="button" data-batch-stop hidden>Detener</button>
<button class="btn btn-quiet" type="button" data-batch-clear hidden>Vaciar lista</button>
<span class="muted small tabnum" data-batch-cost aria-live="polite"></span></div>
<p class="note" data-batch-msg aria-live="polite" hidden>{icon("info")}<span></span></p>
<div class="batch-out" data-batch-out hidden><h2 class="h4">{icon("check")}Fichero {e(fname)} generado</h2>
<div class="cta-row"><button class="btn btn-primary" type="button" data-batch-csv>{icon("download")}Descargar {e(fname)}</button>
<button class="btn btn-ghost" type="button" data-batch-zip>{icon("table")}Todo con resumen (.zip)</button></div></div>
</form>
<div class="install-grid batch-info">
<div><h2 class="h3">Cómo bajar el fichero de {e(b['name'])}</h2><ol class="steps" style="margin-top:14px">{steps}</ol></div>
<div><h2 class="h3">Columnas si usas CSV</h2><div class="tw uso"><table class="uso-t"><thead><tr><th>En {e(b['name'])}</th><th>Llámala</th></tr></thead><tbody>{cols}</tbody></table></div><p class="muted small">{e(b['cols_note'])}</p></div>
</div>
<div class="faq" style="margin-top:40px"><h2 class="h3" style="margin-bottom:20px">Preguntas frecuentes</h2>{faq_html(faq)}</div>
<p class="muted small" style="margin-top:24px">Otras rutas de {e(b['name'])}: <a href="{e(b['path'])}">a ContaSol</a> · <a href="/descargar-norma-43-{bank_key}/">cómo descargar el Norma 43</a> · <a href="/visor-norma-43/">visor gratis</a></p>
</div></section>
<script defer src="/assets/lote.js?v={VERSION}"></script>"""
    return page(path, f"Importar extracto {b['name']} en {short} ({fname}) · Flint by KeyFlint",
                f"Convierte el extracto Norma 43 o CSV de {b['name']} al formato {fname} de {prog}. 25 créditos gratis.", body, [faq_ld(faq)])


def write(rel: str, text: str) -> None:
    p = OUT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def main() -> None:
    shutil.rmtree(OUT, ignore_errors=True)
    shutil.copytree(ROOT / "assets", OUT / "assets")
    shutil.copy(ROOT / "_headers", OUT / "_headers")
    for fname in ["favicon.ico", "favicon.svg", "apple-touch-icon.png", "icon-48.png", "icon-192.png"]:
        src = ROOT / "assets" / fname
        if src.exists():
            shutil.copy(src, OUT / fname)
    write("index.html", home())
    write("precios/index.html", pricing())
    write("empezar/index.html", start())
    write("gracias/index.html", thanks())
    write("saldo/index.html", balance_page())
    write("probar/index.html", trial_page())
    write("404.html", not_found())
    write("terminos/index.html", terms_page())
    write("en/index.html", en_home())
    write("estado/index.html", status_page())
    write("en/try/index.html", en_try())
    write("en/balance/index.html", en_balance())
    write("en/start/index.html", en_start())
    write("reembolsos/index.html", refunds_page())
    write("aviso-legal/index.html", notice_page())
    write("confianza/index.html", trust_page())
    write("asesorias/index.html", advisors_page())
    write("lote/index.html", batch_page())
    write("en/batch/index.html", en_batch())
    write("norma43-a-excel/index.html", norma43_excel_page())
    write("norma43-a-contasol/index.html", norma43_contasol_page())
    write("norma43-a-a3/index.html", norma43_target_page("a3"))
    write("norma43-a-contaplus/index.html", norma43_target_page("contaplus_ascii"))
    write("csv-a-contasol/index.html", csv_target_page("contasol"))
    write("csv-a-a3/index.html", csv_target_page("a3"))
    write("csv-a-contaplus/index.html", csv_target_page("contaplus_ascii"))
    write("visor-norma-43/index.html", visor_page())
    write("validar-iban-cif/index.html", validator_page())
    write("que-es-norma-43/index.html", n43_what_page())
    write("boletin/index.html", newsletter_page())
    write("boletin/confirmar/index.html", newsletter_confirm_page())
    write("boletin/baja/index.html", newsletter_unsub_page())
    for _g in N43_GUIDES:
        write(f"descargar-norma-43-{_g}/index.html", n43_guide_page(_g))
    for _k, _b in BANK_PAGES.items():
        write(_b["path"].strip("/") + "/index.html", bank_page(_k))
    bank_target_paths = []
    for _bk, _tk in BANK_TARGET_COMBOS:
        _st = "contaplus" if _tk == "contaplus_ascii" else _tk
        _p = f"/{_bk}-a-{_st}/"
        bank_target_paths.append(_p)
        write(_p.strip("/") + "/index.html", bank_target_page(_bk, _tk))
    installer_files()
    try:
        import subprocess
        local_bin = ROOT / "node_modules" / ".bin" / ("esbuild.cmd" if shutil.which("cmd") and not shutil.which("esbuild") else "esbuild")
        esbuild_bin = str(local_bin) if local_bin.exists() else shutil.which("esbuild")
        npx_bin = shutil.which("npx")
        if esbuild_bin or npx_bin:
            base_cmd = [esbuild_bin] if esbuild_bin else [npx_bin, "--no-install", "esbuild"]
            for _f in [OUT / "assets" / "app.js", OUT / "assets" / "lote.js", OUT / "assets" / "visor.js", OUT / "assets" / "validador.js", OUT / "assets" / "style.css"]:
                if _f.exists():
                    subprocess.run([*base_cmd, str(_f), "--minify", f"--outfile={_f}", "--allow-overwrite"],
                                   check=True, shell=False, capture_output=True, timeout=30)
    except Exception as _e:
        print(f"Aviso esbuild: {_e}")
    if legal_missing():
        print("AVISO: faltan datos del titular en data/catalog.json -> site.legal:", ", ".join(legal_missing()))
    for m in MCPS:
        write(f"{m['slug']}/index.html", mcp_page(m))
    paths = [
        "/", "/visor-norma-43/", "/validar-iban-cif/", "/que-es-norma-43/", "/boletin/",
        *[f"/descargar-norma-43-{_g}/" for _g in N43_GUIDES],
        *bank_target_paths,
        "/probar/", "/empezar/", "/precios/", "/terminos/", "/reembolsos/", "/aviso-legal/", "/confianza/",
        "/norma43-a-excel/", "/norma43-a-contasol/", "/norma43-a-a3/", "/norma43-a-contaplus/",
        "/csv-a-contasol/", "/csv-a-a3/", "/csv-a-contaplus/",
    ] + [b["path"] for b in BANK_PAGES.values()] + ["/en/", "/en/try/", "/en/start/", "/estado/", "/asesorias/", "/lote/", "/en/batch/"] + [f"/{m['slug']}/" for m in MCPS]
    write("sitemap.xml", '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
          + "".join(f"<url><loc>{SITE['url']}{p}</loc><lastmod>{TODAY}</lastmod></url>\n" for p in paths) + "</urlset>\n")
    indexnow_key = "8f4e2a9c1b7d3e5f6a0c8b2d4e6f1a3b"
    write(f"{indexnow_key}.txt", f"{indexnow_key}\n")
    write("indexnow-urls.json", json.dumps([f"{SITE['url']}{p}" for p in paths], ensure_ascii=False))
    from email.utils import formatdate
    rfc_date = formatdate(usegmt=True)
    rss_items = [
        ("Visor Norma 43 y Validador IBAN/NIF/CIF/SEPA gratuitos en el navegador", f"{SITE['url']}/visor-norma-43/", "Herramientas gratuitas en el navegador para comprobar extractos Norma 43 y validar lotes de IBAN, NIF, NIE, CIF e identificadores SEPA."),
        ("Conector único /despacho/mcp para Claude (17 herramientas contables y bancarias)", f"{SITE['url']}/asesorias/#conector", "Norma 43 + ContaBridge en una sola URL con OAuth 2.1 y código de 6 dígitos por correo."),
        ("Convertir extractos bancarios PDF y CSV a ContaSol, A3 y ContaPlus", f"{SITE['url']}/csv-a-contasol/", "Lectura determinista de extractos bancarios PDF digitales, CSV y Norma 43 con cuadre al céntimo y vista previa inmediata."),
        ("Extractos de Santander, BBVA y CaixaBank a A3, ContaSol y ContaPlus", f"{SITE['url']}/santander-a-a3/", "Guías paso a paso y conversor directo a SUENLACE.DAT, APU.ods y XDiario.txt."),
    ] + [(f"{m['name']} MCP ({m['slug']})", f"{SITE['url']}/{m['slug']}/", m["headline"]) for m in MCPS]
    write("feed.xml", '<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0">\n<channel>\n'
          f'<title>{e(SITE["name"])}</title>\n<link>{SITE["url"]}/</link>\n'
          f'<description>{e(SITE["description"])}</description>\n<language>es</language>\n<lastBuildDate>{rfc_date}</lastBuildDate>\n'
          + "".join(f'<item><title>{e(t)}</title><link>{u}</link><guid isPermaLink="true">{u}</guid><pubDate>{rfc_date}</pubDate><description>{e(d)}</description></item>\n' for t, u, d in rss_items)
          + "</channel>\n</rss>\n")
    write("robots.txt", f"User-agent: *\nAllow: /\nDisallow: /gracias/\nDisallow: /saldo/\nDisallow: /en/balance/\nDisallow: /boletin/confirmar/\nDisallow: /boletin/baja/\nDisallow: /api/\n\nSitemap: {SITE['url']}/sitemap.xml\n")
    write("llms.txt", f"# {SITE['name']}\n\n> {SITE['description']}\n\n## Conector único y servidores MCP\n\n"
          f"- [Conector único Despacho (/despacho/mcp)]({SITE['url']}/asesorias/#conector): 17 herramientas de Norma 43 y ContaBridge en una URL OAuth.\n"
          + "".join(f"- [{m['name']}]({SITE['url']}/{m['slug']}/): {m['headline']}\n" for m in MCPS)
          + f"\n## Conversores web sin instalación\n\n"
          + f"- [Procesador por lotes (/lote/)]({SITE['url']}/lote/)\n"
          + f"- [CSV y PDF a ContaSol]({SITE['url']}/csv-a-contasol/)\n"
          + f"- [Norma 43 a Excel]({SITE['url']}/norma43-a-excel/)\n"
          + f"\n## Más\n\n- [Precios]({SITE['url']}/precios/)\n- [Guía de instalación]({SITE['url']}/empezar/)\n")
    # Descubrimiento MCP (server card, SEP-1649): los escáneres lo piden y antes recibían 404.
    write(".well-known/mcp/server-card.json", json.dumps({
        "serverInfo": {"name": "flint-despacho", "title": "Flint Despacho (Norma 43 + ContaBridge)", "version": "1.0.0"},
        "description": SITE["description"],
        "transport": {"type": "streamable-http", "endpoint": f"{SITE['url']}/despacho/mcp"},
        "authentication": {"required": True, "schemes": ["oauth2"]},
        "servers": [{"name": m["slug"], "title": m["name"], "endpoint": f"{SITE['url']}/{m['slug']}/mcp"} for m in MCPS],
        "documentation": f"{SITE['url']}/empezar/",
    }, ensure_ascii=False, indent=2) + "\n")
    write(".well-known/security.txt", f"Contact: mailto:{CONTACT}\nExpires: {(dt.datetime.now(dt.timezone.utc) + dt.timedelta(days=365)).strftime('%Y-%m-%dT00:00:00Z')}\n"
          f"Preferred-Languages: es, en\nCanonical: {SITE['url']}/.well-known/security.txt\n")
    print(f"OK: {len(paths)} páginas indexables en {OUT}")


if __name__ == "__main__":
    main()

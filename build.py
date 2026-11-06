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
            f'<button type="button" class="copy" data-copy="{id_}">{icon("copy")}<span>Copiar</span></button></div>'
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
    ("windsurf", "Windsurf", "windsurf"),
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
    key_line = ("Si ya tienes servidores, copia solo los bloques de dentro de <code>mcpServers</code>." if multi
                else f'Si ya tienes servidores, añade solo <code>"{s}"</code> dentro de <code>mcpServers</code>.')
    uv_note = (f'<p class="note">{icon("info")}<span>Necesita <a href="/empezar/#uv">uv</a> instalado: '
               'un comando, una sola vez.</span></p>')
    cards = (f'<p class="note">{icon("card")}<span>Los resultados se ven como <b>tarjetas visuales</b> en el chat: '
             'saldo de créditos, cifras clave e incidencias.</span></p>')
    panels = {
        "desktop": (f"""<a class="btn btn-primary btn-block" href="{m['repo']}/releases/latest" rel="noopener">{brand("claude")}Descargar extensión para Claude Desktop</a>
<p class="muted small center gap">Abre el archivo <code>.mcpb</code> descargado, pulsa <b>Instalar</b> y pega tu licencia. Sin terminal.</p>
<details class="manual"><summary><span>Instalación manual</span>{icon("chevron")}</summary>""" if m.get("mcpb") else "") + f"""<ol class="mini-steps">
<li>Abre Claude Desktop › <b>Ajustes</b> › <b>Desarrollador</b> › <b>Editar configuración</b>.</li>
<li>Pega el bloque en <code>claude_desktop_config.json</code>. {key_line}</li>
<li>Guarda y reinicia Claude Desktop por completo.</li></ol>
{code_block(f"sn-{s}-desktop", sn["desktop"], "claude_desktop_config.json")}
<p class="path">macOS <code>~/Library/Application Support/Claude/</code><br>Windows <code>%APPDATA%\\Claude\\</code></p>""" + ("</details>" if m.get("mcpb") else "") + cards + uv_note,
        "code": f"""<ol class="mini-steps"><li>Ejecuta {"los comandos" if multi else "el comando"} en tu terminal. Queda{"n" if multi else ""} disponible{"s" if multi else ""} en todos tus proyectos.</li>
<li>Compruébalo con <code>claude mcp list</code>.</li></ol>
{code_block(f"sn-{s}-code", sn["code"], "Terminal")}{uv_note}""",
        "cursor": (f"""<p class="muted small">Pega el bloque en <code>~/.cursor/mcp.json</code>. Para instalar con un clic, elige un solo servidor.</p>
{code_block(f"sn-{s}-cursor", sn["cursor"], "mcp.json")}{uv_note}""" if multi else
                   f"""<a class="btn btn-primary btn-block" data-deeplink="cursor" href="#">{brand("cursor")}Añadir a Cursor</a>
<p class="muted small center gap">Cursor se abre y te pide confirmar la instalación.</p>
<details class="manual"><summary><span>Instalación manual</span>{icon("chevron")}</summary>
<p>Pega el bloque en <code>~/.cursor/mcp.json</code> (todos los proyectos) o en <code>.cursor/mcp.json</code> (solo este).</p>
{code_block(f"sn-{s}-cursor", sn["cursor"], "mcp.json")}</details>{uv_note}"""),
        "vscode": (f"""<p class="muted small">Pega el bloque en <code>.vscode/mcp.json</code>. Para instalar con un clic, elige un solo servidor.</p>
{code_block(f"sn-{s}-vscode", sn["vscode"], ".vscode/mcp.json")}{uv_note}""" if multi else
                   f"""<a class="btn btn-primary btn-block" data-deeplink="vscode" href="#">{brand("vscode")}Añadir a VS Code</a>
<p class="muted small center gap">Para VS Code 1.102 o superior, con el chat de Copilot en modo agente.</p>
<details class="manual"><summary><span>Instalación manual</span>{icon("chevron")}</summary>
<p>Pega el bloque en <code>.vscode/mcp.json</code> de tu proyecto.</p>
{code_block(f"sn-{s}-vscode", sn["vscode"], ".vscode/mcp.json")}</details>{cards}{uv_note}"""),
        "codex": f"""<ol class="mini-steps"><li>Ejecuta {"los comandos" if multi else "el comando"} en tu terminal. Sirve{"n" if multi else ""} para la CLI, la app y la extensión de Codex, que comparten configuración.</li>
<li>Compruébalo con <code>codex mcp list</code> o con <code>/mcp</code> dentro de Codex.</li></ol>
{code_block(f"sn-{s}-codex", sn["codex"], "Terminal")}
<details class="manual"><summary><span>Instalación manual</span>{icon("chevron")}</summary>
<p>Pega el bloque en <code>~/.codex/config.toml</code>.</p>
{code_block(f"sn-{s}-codex-toml", sn["codex_toml"], "config.toml")}</details>{uv_note}""",
        "antigravity": f"""<ol class="mini-steps"><li>Antigravity › panel del agente › menú <b>…</b> › <b>MCP Servers</b> › <b>Manage MCP Servers</b> › <b>View raw config</b>.</li>
<li>Pega el bloque, guarda y pulsa <b>Refresh</b>. {key_line}</li></ol>
{code_block(f"sn-{s}-antigravity", sn["antigravity"], "mcp_config.json")}
<p class="path"><code>~/.gemini/antigravity/mcp_config.json</code></p>{uv_note}""",
        "windsurf": f"""<ol class="mini-steps"><li>Windsurf › <b>Settings</b> › <b>Cascade</b> › <b>MCP Servers</b> › <b>View raw config</b>.</li>
<li>Pega el bloque, guarda y pulsa <b>Refresh</b>.</li></ol>
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
            f'{brand(ic)}<span>{e(name)}</span></button>'
            for i, (cid, name, ic) in enumerate(clients))
    body = "".join(
        f'<div role="tabpanel" id="pan-{s}-{cid}" aria-labelledby="tab-{s}-{cid}" class="panel"'
        f'{"" if i == 0 else " data-hidden"}><h4 class="panel-title">{e(name)}</h4>{panels[cid]}</div>'
        for i, (cid, name, _) in enumerate(clients))
    cfg_json = e(json.dumps({"slug": s, "server": server}, ensure_ascii=False))
    return f"""<div class="installer" data-installer="{cfg_json}">
<label class="lic"><span class="lic-label">{icon("key")}Tu licencia <span class="muted">· opcional</span></span>
<span class="lic-field"><input type="text" autocomplete="off" spellcheck="false" placeholder="Pega aquí tu LIC-…" data-license aria-describedby="lic-help-{s}"><span class="lic-state" data-license-state aria-live="polite"></span></span>
<span id="lic-help-{s}" class="lic-help">Se rellena en todos los fragmentos. No sale de tu navegador.</span></label>
<div class="tabs" role="tablist" aria-label="Elige tu cliente">{tabs}</div>
<div class="panels">{body}</div>
</div>"""


def remote_panels(m: dict, local_desktop: str, cards: str) -> dict[str, str]:
    s, sn, multi = m["slug"], remote_snippets(m), bool(m.get("all"))
    pl = "s" if multi else ""
    oauth = ('<p class="note">' + icon("key") + '<span>La primera vez se abre una página de KeyFlint: pega tu licencia y '
             'pulsa <b>Conectar</b>. No hay que instalar nada.</span></p>')
    url_block = code_block(f"sn-{s}-url", sn["url"], "URL" + ("s" if multi else ""))
    one_click = lambda cid, label, note: (
        f'<p class="muted small">Pega el bloque. Para instalar con un clic, elige un solo servidor.</p>' if multi else
        f'<a class="btn btn-primary btn-block" data-deeplink="{cid}" href="#">{brand(cid)}{label}</a>'
        f'<p class="muted small center gap">{note}</p><details class="manual"><summary><span>Instalación manual</span>{icon("chevron")}</summary>')
    end = "" if multi else "</details>"
    return {
        "desktop": f"""<ol class="mini-steps"><li>En Claude (web, escritorio o móvil): <b>Ajustes</b> › <b>Conectores</b> › <b>Añadir conector personalizado</b>.</li>
<li>Ponle nombre y pega la URL{pl}. {"Repite con cada una." if multi else ""}</li><li>Pulsa <b>Conectar</b> e inicia sesión con tu licencia.</li></ol>
{url_block}<a class="btn btn-block" href="https://claude.ai/settings/connectors" target="_blank" rel="noopener">{brand("claude")}Abrir conectores de Claude</a>
{oauth}{cards}<details class="manual"><summary><span>Instalación local (.mcpb o configuración)</span>{icon("chevron")}</summary>{local_desktop}</details>""",
        "chatgpt": f"""<ol class="mini-steps"><li>ChatGPT › <b>Ajustes</b> › <b>Apps y conectores</b> › <b>Avanzado</b>: activa el <b>modo desarrollador</b>.</li>
<li><b>Crear</b> conector: pega la URL{pl}, autenticación <b>OAuth</b>.</li><li>Conecta e inicia sesión con tu licencia.</li></ol>
{url_block}{oauth}""",
        "code": f"""<ol class="mini-steps"><li>Ejecuta {"los comandos" if multi else "el comando"} en tu terminal.</li>
<li>Abre Claude Code, escribe <code>/mcp</code> y elige <b>Authenticate</b> para pegar tu licencia.</li></ol>
{code_block(f"sn-{s}-code", sn["code"], "Terminal")}{oauth}""",
        "cursor": one_click("cursor", "Añadir a Cursor", "Cursor se abre, confirma y pulsa <b>Connect</b> para pegar tu licencia.")
        + f"""<p>Pega el bloque en <code>~/.cursor/mcp.json</code>.</p>{code_block(f"sn-{s}-cursor", sn["cursor"], "mcp.json")}{end}{oauth}""",
        "vscode": one_click("vscode", "Añadir a VS Code", "VS Code 1.102 o superior. Te pedirá iniciar sesión con tu licencia.")
        + f"""<p>Pega el bloque en <code>.vscode/mcp.json</code>.</p>{code_block(f"sn-{s}-vscode", sn["vscode"], ".vscode/mcp.json")}{end}{cards}{oauth}""",
        "codex": f"""<ol class="mini-steps"><li>Ejecuta {"los comandos" if multi else "el comando"}: añade{"n" if multi else ""} el servidor{"es" if multi else ""} e inicia sesión con tu licencia.</li>
<li>Sirve para la CLI, la app y la extensión de Codex.</li></ol>
{code_block(f"sn-{s}-codex", sn["codex"], "Terminal")}
<details class="manual"><summary><span>Sin OAuth: licencia en config.toml</span>{icon("chevron")}</summary>
<p>Pega el bloque en <code>~/.codex/config.toml</code>.</p>{code_block(f"sn-{s}-codex-toml", sn["codex_toml"], "config.toml")}</details>""",
        "antigravity": f"""<ol class="mini-steps"><li>Antigravity › panel del agente › <b>…</b> › <b>MCP Servers</b> › <b>Manage MCP Servers</b> › <b>View raw config</b>.</li>
<li>Pega el bloque (lleva tu licencia), guarda y pulsa <b>Refresh</b>.</li></ol>
{code_block(f"sn-{s}-antigravity", sn["headers"], "mcp_config.json")}<p class="path"><code>~/.gemini/antigravity/mcp_config.json</code></p>""",
        "windsurf": f"""<ol class="mini-steps"><li>Windsurf › <b>Settings</b> › <b>Cascade</b> › <b>MCP Servers</b> › <b>View raw config</b>.</li>
<li>Pega el bloque (lleva tu licencia), guarda y pulsa <b>Refresh</b>.</li></ol>
{code_block(f"sn-{s}-windsurf", sn["headers"], "mcp_config.json")}<p class="path"><code>~/.codeium/windsurf/mcp_config.json</code></p>""",
    }


# ---------------------------------------------------------------- layout

def page(path: str, title: str, desc: str, body: str, ld: list | None = None, noindex: bool = False) -> str:
    url = SITE["url"] + path
    lds = "".join(jsonld(x) for x in (ld or []))
    robots = '<meta name="robots" content="noindex">\n' if noindex else ""
    nav = [("/#catalogo", "Catálogo"), ("/#instalar", "Instalar"), ("/precios/", "Precios"), ("/empezar/", "Guía"), ("/saldo/", "Mi saldo")]
    navh = "".join(f'<a href="{h}"' + (' aria-current="page"' if h == path else "") + f">{t}</a>" for h, t in nav)
    return f"""<!doctype html>
<html lang="{SITE['lang']}" class="no-js">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
{robots}<link rel="canonical" href="{url}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="{e(SITE['name'])}">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{SITE['url']}/assets/og.png">
<meta property="og:locale" content="es_ES">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#0B0D17" media="(prefers-color-scheme: dark)">
<meta name="theme-color" content="#F7F8FA" media="(prefers-color-scheme: light)">
<script>document.documentElement.className="js"</script>
<link rel="icon" href="/favicon.ico" sizes="any">
<link rel="icon" type="image/svg+xml" href="/favicon.svg">
<link rel="icon" type="image/png" sizes="48x48" href="/icon-48.png">
<link rel="icon" type="image/png" sizes="192x192" href="/icon-192.png">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<link rel="preload" href="/assets/fonts/inter-400.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="/assets/fonts/interdisplay-600.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="/assets/style.css?v={VERSION}">
<script defer src="/assets/app.js?v={VERSION}"></script>
{lds}
</head>
<body>
<a class="skip" href="#main">Saltar al contenido</a>
<header class="top"><div class="wrap top-in">
<a class="brand" href="/" aria-label="KeyFlint MCP, inicio">{icon("logo", "logo")}<span>KeyFlint</span><span class="brand-tag">MCP</span></a>
<nav class="nav" aria-label="Principal">{navh}</nav>
<a class="btn btn-primary btn-sm top-cta" href="/probar/">Probar gratis</a>
</div></header>
<main id="main">
{body}
</main>
<footer class="foot"><div class="wrap">
<div class="foot-grid">
<div class="foot-brand"><a class="brand" href="/">{icon("logo", "logo")}<span>KeyFlint</span><span class="brand-tag">MCP</span></a>
<p class="muted small">Servidores MCP deterministas para agentes de IA, con licencias criptográficas y pago por uso.</p></div>
<div><h3>Servidores</h3><ul>{''.join(f'<li><a href="/{m["slug"]}/">{e(m["name"])}</a></li>' for m in MCPS)}</ul></div>
<div><h3>Recursos</h3><ul><li><a href="/empezar/">Guía de instalación</a></li><li><a href="/saldo/">Consultar saldo</a></li><li><a href="/precios/">Precios</a></li><li><a href="https://keyflint.dev">KeyFlint</a></li></ul></div>
<div><h3>Legal y soporte</h3><ul><li><a href="https://keyflint.dev/privacy.html">Privacidad</a></li><li><a href="https://keyflint.dev/dpa.html">Encargo de tratamiento</a></li><li><a href="{SITE['contact']}">{e(CONTACT)}</a></li></ul></div>
</div>
<div class="foot-base">
<p class="muted small">© {dt.date.today().year} KeyFlint · Los servidores se ejecutan en tu equipo y no guardan tus datos.</p>
<div class="badges">
<a class="badge-pill" href="https://stripe.com" rel="noopener"><span class="muted">Pagos con</span>{brand("stripe")}<b>Stripe</b></a>
<a class="badge-pill kf" href="https://keyflint.dev"><span class="muted">Licencias</span><span class="kf-mark">{icon("logo", "logo")}by&nbsp;KeyFlint</span></a>
</div></div>
</div></footer>
</body>
</html>
"""


# ---------------------------------------------------------------- sections

def mcp_card(m: dict) -> str:
    chips = "".join(f'<li><code>{e(t[0].split(",")[0])}</code></li>' for t in m["tools"][:3])
    return f"""<a class="card mcp-card" href="/{m['slug']}/">
<div class="card-top"><span class="tile">{icon(m['icon'])}</span><span class="eyebrow">{e(m['category'])}</span></div>
<h3>{e(m['name'])}</h3>
<p>{e(m['headline'])}</p>
<ul class="chips">{chips}</ul>
<span class="card-foot"><span class="muted small">{len(m['tools'])} herramientas</span><span class="link-arrow">Ver servidor{icon("arrow-right")}</span></span>
</a>"""


def hero_demo() -> str:
    return f"""<figure class="demo glass" aria-label="Ejemplo: un agente usa tres herramientas">
<div class="demo-bar"><span class="dots" aria-hidden="true"><i></i><i></i><i></i></span><span class="demo-title">Agente · Norma 43 + ContaBridge</span></div>
<div class="demo-body">
<div class="msg user"><span class="who">Tú</span><p>Concilia el extracto de octubre con las facturas pendientes y pásame los asientos a A3.</p></div>
<ul class="calls">
<li class="call"><span class="call-ic">{icon("plug")}</span><code>parse_norma43</code><span class="call-res">142 movimientos</span><span class="cr">1 cr</span></li>
<li class="call"><span class="call-ic">{icon("plug")}</span><code>reconcile_movements</code><span class="call-res">131 conciliados · 3 a revisar</span><span class="cr">3 cr</span></li>
<li class="call"><span class="call-ic">{icon("plug")}</span><code>bank_to_journal</code><span class="call-res">SUENLACE.DAT listo</span><span class="cr">3 cr</span></li>
</ul>
<div class="msg bot"><span class="who">Agente</span><p>Listo: 131 de 142 movimientos conciliados. Te dejo 3 casos para revisar y el fichero para importar en A3.</p></div>
</div>
<figcaption class="demo-foot"><span>{icon("shield")}Licencia verificada en local</span><span class="tabnum">7 créditos</span></figcaption>
</figure>"""


def install_picker() -> tuple[str, str]:
    """Selector de servidor + instalador de cada uno (inicio y /probar/)."""
    opts = MCPS + [ALL]
    picker = "".join(
        f'<button type="button" class="pick" aria-pressed="{"true" if i == 0 else "false"}" data-pick="{m["slug"]}">'
        f'{icon(m["icon"])}<span>{e(m["name"])}</span></button>' for i, m in enumerate(opts))
    installers = "".join(f'<div class="pick-panel" data-pick-panel="{m["slug"]}"{"" if i == 0 else " data-hidden"}>'
                         f'<h3 class="panel-title">{e(m["name"])}</h3>{installer(m)}</div>'
                         for i, m in enumerate(opts))
    return picker, installers


DEMO_N43 = "112100041802000513322610012610312000000001500009783ACME SOLUCIONES SL           \n22    0418261003261003020002000000001250000000000000000000000000                \n2301CLIENTE DEMO SL                                                             \n2303        FACTURA 2026-104                                                    \n22    0418261015261015030001000000000042350000012345000000000000                \n3321000418020005133200001000000000042350000100000000125000200000000270765978    \n88999999999999999999000006                                                      \n"
DEMO_CSV = ("Asiento;Fecha;Cuenta;Concepto;Debe;Haber\n"
            "1;02/11/2026;4300001;Factura 104 Cliente Demo;1.210,00;\n1;02/11/2026;7000001;Factura 104 Cliente Demo;;1.000,00\n"
            "1;02/11/2026;4770001;IVA 21% factura 104;;210,00\n"
            "2;05/11/2026;5720001;Cobro factura 104;1.210,00;\n2;05/11/2026;4300001;Cobro factura 104;;1.210,00\n")


def demo_block(m: dict) -> str:
    """Prueba sin instalar en la ficha (usa créditos del hub, no del visitante). Solo para los servidores con demo."""
    s = m["slug"]
    if s == "web-intel":
        field = ('<label class="demo-field"><span>URL</span><input type="url" name="url" inputmode="url" '
                 'placeholder="https://tu-web.com" value="https://keyflint.dev" required></label>')
        btn, tool = "Ver Markdown limpio", "read_url"
    elif s == "norma43":
        field = (f'<label class="demo-field"><span>Extracto Norma 43 (ejemplo)</span><textarea name="content" rows="7" '
                 f'spellcheck="false" required>{e(DEMO_N43)}</textarea></label>')
        btn, tool = "Validar y leer", "parse_norma43"
    elif s == "contabridge":
        opts = "".join(f'<option value="{v}">{t}</option>' for v, t in
                       [("a3", "A3 (SUENLACE.DAT)"), ("contaplus_csv", "ContaPlus / Sage 50"), ("xero_csv", "Xero"), ("quickbooks_csv", "QuickBooks Online")])
        field = (f'<label class="demo-field"><span>Dos asientos de ejemplo (CSV)</span><textarea name="content" rows="6" '
                 f'spellcheck="false" required>{e(DEMO_CSV)}</textarea></label>'
                 f'<label class="demo-field demo-inline"><span>Convertir a</span><select name="target">{opts}</select></label>')
        btn, tool = "Convertir", "convert_journal"
    else:
        return ""
    return f"""<div class="block demo-try" id="probar-aqui"><h2>Pruébalo aquí, sin instalar</h2>
<p class="muted">Es el servidor real (<code>{tool}</code>). La demo corre de nuestra cuenta: no gastas créditos ni necesitas licencia.</p>
<form class="glass demo-form" data-demo="{s}" novalidate>{field}
<div class="demo-actions"><button class="btn btn-primary" type="submit">{icon("arrow-right")}{btn}</button>
<span class="muted small">5 pruebas al día. Para tus propios ficheros, <a href="/probar/">licencia gratis</a>.</span></div>
<p class="lic-help" data-demo-msg aria-live="polite"></p>
<div class="demo-out" data-demo-out hidden></div>
</form></div>
"""


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
<p class="muted small">Una por correo. No te suscribimos a nada.</p></div>
<div class="recover-row"><input type="email" name="email" autocomplete="email" placeholder="tu@correo.com" required aria-label="Correo electrónico">
<button class="btn btn-primary" type="submit">{icon("key")}Darme la licencia</button></div>
<p class="lic-help" data-trial-msg aria-live="polite"></p>
</form>
<div class="reveal glass" data-trial-out hidden>
<div class="reveal-head"><span class="tile tile-sm">{icon("check")}</span><div><h2 class="h3">Lista: {SITE['free_credits']} créditos</h2>
<p class="muted small">Guardada en este navegador: los fragmentos de abajo ya la llevan puesta.</p></div></div>
{code_block("lic-trial", "LIC-…", "KEYFLINT_LICENSE")}
</div>
</div></section>
<section class="section" id="instalar"><div class="wrap install-grid">
<div class="section-head left"><p class="eyebrow">Siguiente paso</p><h2>Instálalo en tu cliente</h2>
<p class="lead-sm">Claude Desktop (extensión .mcpb), Claude Code, Cursor, VS Code y más. Elige servidor y copia.</p></div>
<div class="install-card glass"><div class="picker" role="group" aria-label="Elige servidor">{picker}</div>{installers}</div>
</div></section>"""
    return page("/probar/", f"Prueba gratis los servidores MCP: {SITE['free_credits']} créditos · KeyFlint MCP",
                f"Licencia gratis al momento con {SITE['free_credits']} créditos para todos los servidores MCP de KeyFlint. Sin tarjeta.", body)


def home() -> str:
    cards = "\n".join(mcp_card(m) for m in MCPS)
    clients = "".join(f'<li>{brand(ic)}<span>{e(n)}</span></li>' for _, n, ic in CLIENTS) + \
        f'<li>{icon("plug")}<span>Cualquier cliente MCP</span></li>'
    feats = [
        ("key", "Una licencia para todo", "La misma clave funciona en todos los servidores. Sin cuentas ni contraseñas que recordar."),
        ("gauge", "Pagas por uso", "Cada herramienta tiene un coste fijo en créditos. Validaciones y utilidades, gratis."),
        ("refund", "Lo que falla no se cobra", "Los ficheros no válidos se rechazan antes de cobrar y, si algo falla después, se reembolsa solo."),
        ("lock", "Tus ficheros no salen de tu equipo", "El servidor se ejecuta en tu ordenador. Solo se comunica con KeyFlint para la licencia y el saldo."),
        ("target", "Resultados deterministas", "La misma entrada da siempre la misma salida, sin IA intermedia. Cada resultado es auditable."),
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
<p class="kicker"><a class="pill" href="/contabridge/"><span class="pill-dot" aria-hidden="true"></span>Nuevo: ContaBridge para gestorías{icon("arrow-right")}</a></p>
<h1>Herramientas MCP fiables para tu agente de IA</h1>
<p class="lead">{e(SITE['tagline'])} Funcionan en Claude, Cursor, VS Code, Codex, Antigravity y cualquier cliente compatible, con resultados en tarjetas visuales.</p>
<div class="cta-row"><a class="btn btn-primary btn-lg" href="#instalar">{icon("download")}Instalar en 2 minutos</a>
<a class="btn btn-ghost btn-lg" href="/precios/">Ver precios</a></div>
<ul class="assure">
<li>{icon("check")}{SITE['free_credits']} créditos gratis</li><li>{icon("check")}Sin permanencia</li><li>{icon("check")}Se ejecuta en tu equipo</li></ul>
</div>
{hero_demo()}
</div></section>

<section class="clients" aria-label="Clientes compatibles"><div class="wrap clients-in">
<p class="clients-title">Compatible con</p><ul class="client-list">{clients}</ul></div></section>

<section class="section" id="catalogo"><div class="wrap">
<div class="section-head"><p class="eyebrow">Catálogo</p><h2>Servidores listos para trabajo real</h2>
<p class="lead-sm">Cada servidor resuelve una tarea de principio a fin y valida los datos igual que el programa de destino.</p></div>
<div class="grid-3">{cards}</div>
</div></section>

<section class="section alt"><div class="wrap">
<div class="section-head"><p class="eyebrow">Por qué KeyFlint MCP</p><h2>Pensados para producción, no para demos</h2></div>
<div class="feat-grid">{feat_html}</div>
</div></section>

<section class="section" id="instalar"><div class="wrap install-grid">
<div class="section-head left"><p class="eyebrow">Instalación</p><h2>Elige servidor y cliente. Copia. Listo.</h2>
<p class="lead-sm">Pega tu licencia y todos los fragmentos se rellenan solos. En Claude Desktop, Cursor y VS Code basta un clic.</p>
<ol class="steps">{steps_html}</ol></div>
<div class="install-card glass"><div class="picker" role="group" aria-label="Elige servidor">{picker}</div>{installers}</div>
</div></section>

<section class="section alt"><div class="wrap faq-grid">
<div class="section-head left"><p class="eyebrow">Preguntas frecuentes</p><h2>Lo que suelen preguntarnos</h2>
<p class="lead-sm">¿Otra duda? Escríbenos a <a href="{SITE['contact']}">{e(CONTACT)}</a> y te respondemos en un día laborable.</p></div>
<div class="faq">{faq_html(faq)}</div>
</div></section>

<section class="section"><div class="wrap"><div class="cta-band">
<div><h2>Empieza gratis hoy</h2><p class="lead-sm">{SITE['free_credits']} créditos para probar cualquier servidor. Planes desde {money(min_price)} $.</p></div>
<div class="cta-row"><a class="btn btn-primary btn-lg" href="/precios/">Ver planes</a><a class="btn btn-ghost btn-lg" href="/empezar/">Leer la guía</a></div>
</div></div></section>"""
    ld = [
        {"@context": "https://schema.org", "@type": "WebSite", "name": SITE["name"], "url": SITE["url"] + "/",
         "description": SITE["description"], "inLanguage": "es"},
        {"@context": "https://schema.org", "@type": "Organization", "name": "KeyFlint", "url": "https://keyflint.dev",
         "logo": SITE["url"] + "/assets/icon.svg", "email": CONTACT},
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


def pricing() -> str:
    common = ["Todos los servidores del catálogo", "Reembolso automático si algo falla", "Factura con NIF/VAT"]
    cards = [f"""<div class="plan">
<div class="plan-head"><h2 class="h3">Gratis</h2><p class="muted small">Para probar sin compromiso</p></div>
<p class="price">0 $</p><p class="credits">{SITE['free_credits']} créditos</p>
<a class="btn btn-ghost btn-block" href="/probar/">Pedir licencia gratis</a>
<ul class="checks"><li>{icon("check")}1 equipo</li><li>{icon("check")}Todos los servidores</li><li>{icon("check")}Sin tarjeta</li></ul></div>"""]
    for p in SITE["packs"]:
        per100 = money(round(p["price"] / p["credits"] * 100, 2))
        feats = [p["billing"], f"{p['seats']} equipos"] + common
        badge = '<span class="badge">Más elegido</span>' if p.get("featured") else ""
        cards.append(f"""<div class="plan{' featured' if p.get('featured') else ''}">{badge}
<div class="plan-head"><h2 class="h3">{e(p['name'])}</h2><p class="muted small">{e(p['who'])}</p></div>
<p class="price">{money(p['price'])} $<span class="per">{e(p.get('period', ''))}</span></p>
<p class="credits">{money(p['credits'])} créditos{' al mes' if p.get('period') else ''}<span class="muted"> · {per100} $ / 100</span></p>
<a class="btn {'btn-primary' if p.get('featured') else 'btn-ghost'} btn-block" href="{p['checkout']}" rel="nofollow">Comprar {e(p['name'])}</a>
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
        ("¿Qué pasa si se me acaban los créditos?", "La herramienta te avisa con el enlace de compra y no se cobra nada. El plan Pro se recarga cada mes; Indie y Agency son de pago único."),
        ("¿Qué es un equipo?", "Cada ordenador o servidor donde usas la licencia. Pro e Indie permiten 3; Agency, 25."),
        ("¿Puedo cancelar Pro?", "Sí, cuando quieras y sin permanencia, desde el enlace de gestión del correo de Stripe o escribiéndonos."),
        ("¿Por qué en dólares?", "Es la moneda de todos los planes de KeyFlint. Stripe te muestra el importe en tu moneda y calcula los impuestos de tu país."),
        ("¿Qué datos guardáis?", "Ninguno de tus ficheros: los servidores se ejecutan en tu equipo. Solo registramos la licencia y el consumo de créditos."),
    ]
    body = f"""
<section class="hero hero-sm center"><div class="glow" aria-hidden="true"></div><div class="wrap narrow">
<p class="eyebrow">Precios</p>
<h1>Un saldo para todos los servidores</h1>
<p class="lead">Una licencia, un saldo de créditos y un coste fijo por herramienta. Lo que falla no se cobra.</p>
</div></section>
<section class="section tight"><div class="wrap">
<div class="plans">{''.join(cards)}</div>
<p class="muted small center fine">{icon("lock")}Pago seguro con Stripe. Precios en USD, impuestos según tu país. Recibes factura y puedes añadir tu NIF/VAT.</p>
</div></section>
<section class="section alt"><div class="wrap usage-grid">
<div class="section-head left"><p class="eyebrow">Cuánto da de sí</p><h2>Coste de las tareas más habituales</h2>
<p class="lead-sm">Con el plan Indie, una gestoría concilia y pasa a asientos unos 2.000 extractos (5 créditos cada uno).</p></div>
<div class="table-wrap card-flat"><table><thead><tr><th scope="col">Tarea</th><th scope="col" class="r">Coste</th></tr></thead><tbody>{urows}</tbody></table></div>
</div></section>
<section class="section"><div class="wrap faq-grid">
<div class="section-head left"><p class="eyebrow">Preguntas frecuentes</p><h2>Pagos y licencias</h2></div>
<div class="faq">{faq_html(faq)}</div></div></section>"""
    ld = [{"@context": "https://schema.org", "@type": "Product", "name": "Créditos KeyFlint MCP",
           "description": "Créditos de uso para todos los servidores MCP de KeyFlint.",
           "brand": {"@type": "Brand", "name": "KeyFlint"},
           "offers": [{"@type": "Offer", "name": p["name"], "price": p["price"], "priceCurrency": "USD",
                       "url": f"{SITE['url']}/precios/", "availability": "https://schema.org/InStock"} for p in SITE["packs"]]},
          faq_ld(faq)]
    return page("/precios/", "Precios de los servidores MCP · KeyFlint MCP",
                f"Un saldo de créditos para todos los servidores MCP de KeyFlint. Desde {money(min(p['price'] for p in SITE['packs']))} $ o gratis con {SITE['free_credits']} créditos.",
                body, ld)


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
        ("Me he quedado sin créditos", "La herramienta te devuelve el enlace de compra. Al comprar recibes una licencia nueva: sustitúyela en la configuración."),
    ])}</div>
</div></li>
</ol>
</div></section>"""
    ld = [{"@context": "https://schema.org", "@type": "HowTo", "name": "Instalar un servidor MCP de KeyFlint",
           "totalTime": "PT2M",
           "step": [{"@type": "HowToStep", "name": n} for n in
                    ["Consigue tu licencia", "Instala uv", "Añade el servidor a tu cliente MCP", "Compruébalo con tu agente"]]}]
    return page("/empezar/", "Cómo instalar un servidor MCP en Claude, Cursor o VS Code · KeyFlint MCP",
                "Guía paso a paso para instalar servidores MCP en Claude Desktop, Claude Code, Cursor, VS Code, Codex, Antigravity y Windsurf con una licencia gratuita.",
                body, ld)


def balance_page() -> str:
    recharge = "".join(
        f'<a class="btn {"btn-primary" if p.get("featured") else "btn-ghost"}" href="{e(p["checkout"])}" rel="noopener" data-checkout>'
        f'<b>{e(p["name"])}</b><span class="tabnum">{p["credits"]:,} cr · {money(p["price"])} ${e(p.get("period", ""))}</span></a>'
        .replace(f'{p["credits"]:,} cr', f'{p["credits"]:,}'.replace(",", ".") + " cr")
        for p in SITE["packs"])
    body = f"""
<section class="hero hero-sm"><div class="glow" aria-hidden="true"></div><div class="wrap narrow">
<nav class="crumbs" aria-label="Ruta"><a href="/">Inicio</a>{icon("chevron-right")}<span aria-current="page">Mi saldo</span></nav>
<h1>Consulta tu saldo</h1>
<p class="lead">Pega tu licencia para ver tu plan, los créditos que te quedan y los que has usado.</p>
</div></section>
<section class="section tight"><div class="wrap narrow">
<form class="saldo-form glass" data-balance-form novalidate>
<label class="lic"><span class="lic-label">{icon("key")}Tu licencia</span>
<span class="lic-field"><input type="text" name="license" autocomplete="off" spellcheck="false" placeholder="LIC-…" required aria-describedby="saldo-help"></span>
<span id="saldo-help" class="lic-help">Se consulta a KeyFlint en el momento. Este sitio no la guarda.</span></label>
<button class="btn btn-primary btn-lg" type="submit">{icon("gauge")}Consultar saldo</button>
</form>
<div class="saldo-out" data-balance-out aria-live="polite" hidden>
<div class="saldo-card">
<div class="saldo-head"><span class="eyebrow" data-f="tier"></span><span class="status" data-f="status"></span></div>
<p class="saldo-num"><b class="tabnum" data-f="balance"></b><span class="muted"> créditos disponibles</span></p>
<div class="meter" role="meter" aria-valuemin="0" data-meter><span></span></div>
<dl class="saldo-dl"><div><dt>Usados</dt><dd class="tabnum" data-f="consumed"></dd></div><div><dt>Total del plan</dt><dd class="tabnum" data-f="allowance"></dd></div></dl>
<div class="recharge"><h3 class="h4">{icon("card")}Recargar créditos</h3>
<div class="recharge-row">{recharge}</div>
<p class="muted small" data-recharge-note>Pago seguro con Stripe. Si tienes la licencia gratis y pagas con el mismo correo, se amplía la misma clave. Con un plan de pago recibes una licencia nueva con su saldo.</p></div>
<div class="cta-row"><a class="btn btn-ghost" href="/precios/">Comparar planes</a><a class="btn btn-quiet" href="/#instalar">Instalar servidores</a></div>
</div>
<div class="saldo-card uso" data-usage hidden><h3>Uso en los últimos 30 días</h3>
<div class="tw"><table class="uso-t"><thead><tr><th>Servidor</th><th>Herramienta</th><th class="num">Llamadas</th><th class="num">Créditos</th><th class="num">Errores</th></tr></thead><tbody data-usage-tools></tbody></table></div>
<h4>Últimas llamadas</h4>
<div class="tw"><table class="uso-t"><thead><tr><th>Cuándo</th><th>Servidor</th><th>Herramienta</th><th class="num">Créditos</th><th>Estado</th></tr></thead><tbody data-usage-recent></tbody></table></div>
<p class="muted small">Se registra servidor, herramienta, resultado y créditos de cada llamada por URL. Nunca el contenido. Se borra a los 180 días.</p>
</div></div>
<p class="saldo-err note" data-balance-err hidden>{icon("info")}<span></span></p>
<div class="faq saldo-faq">{faq_html([
        ("¿Perdiste tu licencia?", "Escribe tu correo en la página de confirmación del pago o en el portal de KeyFlint y te enviamos un enlace de acceso de un solo uso."),
        ("¿Por qué no veo el detalle por servidor?", "KeyFlint registra el saldo de la licencia, no el uso por herramienta. Cada servidor te dice lo que cuesta antes de usarlo."),
        ("¿Cómo añado créditos?", "Compra un plan y recibirás una licencia nueva con su saldo. Sustitúyela en tu configuración."),
    ])}</div>
</div></section>"""
    return page("/saldo/", "Consulta tu saldo de créditos · KeyFlint MCP",
                "Consulta los créditos que te quedan en tu licencia de KeyFlint MCP.", body, noindex=True)


def thanks() -> str:
    body = f"""
<section class="hero hero-sm center"><div class="glow" aria-hidden="true"></div><div class="wrap narrow">
<span class="tile tile-lg ok-tile">{icon("check")}</span>
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
    return page("/gracias/", "Pago completado · KeyFlint MCP", "Tu licencia está de camino.", body, noindex=True)


def not_found() -> str:
    return page("/404", "Página no encontrada · KeyFlint MCP", "Página no encontrada.",
                f'<section class="hero hero-sm center"><div class="glow" aria-hidden="true"></div><div class="wrap narrow"><p class="eyebrow">Error 404</p>'
                f'<h1>Esta página no existe</h1><p class="lead">Puede que el enlace haya cambiado.</p>'
                f'<div class="cta-row center"><a class="btn btn-primary btn-lg" href="/">Ir al inicio</a>'
                f'<a class="btn btn-ghost btn-lg" href="/#catalogo">Ver catálogo</a></div></div></section>', noindex=True)


# ---------------------------------------------------------------- output

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
    for m in MCPS:
        write(f"{m['slug']}/index.html", mcp_page(m))
    paths = ["/", "/probar/", "/empezar/", "/precios/"] + [f"/{m['slug']}/" for m in MCPS]
    write("sitemap.xml", '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
          + "".join(f"<url><loc>{SITE['url']}{p}</loc><lastmod>{TODAY}</lastmod></url>\n" for p in paths) + "</urlset>\n")
    write("robots.txt", f"User-agent: *\nAllow: /\nDisallow: /gracias/\nDisallow: /saldo/\nDisallow: /api/\n\nSitemap: {SITE['url']}/sitemap.xml\n")
    write("llms.txt", f"# {SITE['name']}\n\n> {SITE['description']}\n\n## Servidores\n\n"
          + "".join(f"- [{m['name']}]({SITE['url']}/{m['slug']}/): {m['headline']}\n" for m in MCPS)
          + f"\n## Más\n\n- [Precios]({SITE['url']}/precios/)\n- [Guía de instalación]({SITE['url']}/empezar/)\n")
    print(f"OK: {len(paths)} páginas indexables en {OUT}")


if __name__ == "__main__":
    main()

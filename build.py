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
import urllib.request
from pathlib import Path

ROOT = Path(__file__).parent
OUT = ROOT / "public"
DATA = json.loads((ROOT / "data" / "catalog.json").read_text(encoding="utf-8"))
SITE = DATA["site"]
KEY_RE = r"[0-9a-f]{64}(,[0-9a-f]{64})*|[\w.-]+=[0-9a-f]{64}(,[\w.-]+=[0-9a-f]{64})*"


def _gateway_keyring() -> str:
    """Lee la clave pública actual del gateway (sigue las rotaciones de clave en cada build)."""
    url = SITE["keyflint_url"].rstrip("/") + "/api/v1/licenses/public-key"
    try:
        with urllib.request.urlopen(url, timeout=15) as r:
            return str(json.load(r)["data"]["keyring"]).strip()
    except Exception as exc:  # noqa: BLE001
        print(f"aviso: no se pudo leer {url}: {exc}")
        return ""


SITE["public_keys"] = (os.environ.get("KEYFLINT_PUBLIC_KEYS", "").strip()
                       or (SITE["public_keys"] if re.fullmatch(KEY_RE, SITE["public_keys"]) else "")
                       or _gateway_keyring())
if not re.fullmatch(KEY_RE, SITE["public_keys"]):
    raise SystemExit("ERROR: falta la clave pública del gateway. Pon KEYFLINT_PUBLIC_KEYS (hex de "
                     "https://licenses.keyflint.dev/api/v1/licenses/public-key) en data/catalog.json o como variable de entorno.")
MCPS = DATA["mcps"]
TODAY = dt.date.today().isoformat()
e = html.escape


def jsonld(obj) -> str:
    return f'<script type="application/ld+json">{json.dumps(obj, ensure_ascii=False)}</script>'


def page(path: str, title: str, desc: str, body: str, ld: list | None = None) -> str:
    url = SITE["url"] + path
    lds = "".join(jsonld(x) for x in (ld or []))
    return f"""<!doctype html>
<html lang="{SITE['lang']}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<link rel="canonical" href="{url}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="{e(SITE['name'])}">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:url" content="{url}">
<meta property="og:locale" content="es_ES">
<meta name="twitter:card" content="summary">
<meta name="theme-color" content="#0f172a">
<link rel="icon" href="/assets/icon.svg" type="image/svg+xml">
<link rel="stylesheet" href="/assets/style.css">
{lds}
</head>
<body>
<header class="top"><div class="wrap">
<a class="brand" href="/">KeyFlint <b>MCP</b></a>
<nav><a href="/#catalogo">Catálogo</a><a href="/empezar/">Empezar</a><a href="/precios/">Precios</a></nav>
</div></header>
<main class="wrap">
{body}
</main>
<footer class="foot"><div class="wrap">
<p>{e(SITE['name'])} · Licencias y créditos con <a href="https://keyflint.dev">KeyFlint</a> · <a href="{SITE['contact']}">Contacto</a></p>
<p class="muted">Los servidores no guardan tus datos entre llamadas. Una llamada que falla se reembolsa.</p>
</div></footer>
<script>document.addEventListener('click',function(ev){{var b=ev.target.closest('[data-copy]');if(!b)return;var t=document.getElementById(b.dataset.copy).innerText;navigator.clipboard&&navigator.clipboard.writeText(t).then(function(){{b.textContent='Copiado';setTimeout(function(){{b.textContent='Copiar'}},1500)}})}});</script>
</body>
</html>
"""


def code(id_: str, text: str, lang: str = "") -> str:
    return (f'<div class="code"><button type="button" data-copy="{id_}">Copiar</button>'
            f'<pre id="{id_}"><code>{e(text)}</code></pre></div>')


def claude_config(m: dict) -> str:
    cfg = {"mcpServers": {m["slug"]: {
        "command": "uvx",
        "args": ["--from", f"git+{m['repo']}", m["package"]],
        "env": {"KEYFLINT_LICENSE": "LIC-tu-licencia",
                "KEYFLINT_URL": SITE["keyflint_url"],
                "KEYFLINT_PUBLIC_KEYS": SITE["public_keys"]},
    }}}
    return json.dumps(cfg, indent=2, ensure_ascii=False)


def claude_code_cmd(m: dict) -> str:
    return (f"claude mcp add {m['slug']} \\\n  -e KEYFLINT_LICENSE=LIC-tu-licencia \\\n"
            f"  -e KEYFLINT_URL={SITE['keyflint_url']} \\\n"
            f"  -e KEYFLINT_PUBLIC_KEYS={SITE['public_keys']} \\\n"
            f"  -- uvx --from git+{m['repo']} {m['package']}")


def card(m: dict) -> str:
    return f"""<a class="card" href="/{m['slug']}/">
<span class="tag">{e(m['category'])}</span>
<h3>{e(m['name'])}</h3>
<p>{e(m['headline'])}</p>
<span class="muted small">{len(m['tools'])} herramientas · {e(m['audience'])}</span>
</a>"""


def home() -> str:
    cards = "\n".join(card(m) for m in MCPS)
    body = f"""
<section class="hero">
<h1>Herramientas MCP que tu agente puede usar hoy</h1>
<p class="lead">{e(SITE['tagline'])} Funcionan en Claude, Cursor, Claude Code y cualquier cliente MCP.</p>
<p><a class="btn" href="/empezar/">Empieza gratis con {SITE['free_credits']} créditos</a> <a class="btn ghost" href="/precios/">Ver precios</a></p>
<ul class="points">
<li><b>Una licencia para todo.</b> La misma clave funciona en todos los servidores del catálogo.</li>
<li><b>Pagas por uso.</b> Cada herramienta cuesta créditos fijos; las utilidades son gratis.</li>
<li><b>Sin sorpresas.</b> Lo que falla o se rechaza no se cobra. Resultados deterministas, sin IA intermedia.</li>
<li><b>Privado.</b> No guardamos tus ficheros ni tus datos entre llamadas.</li>
</ul>
</section>
<section id="catalogo">
<h2>Catálogo</h2>
<div class="grid">{cards}</div>
</section>
<section>
<h2>Cómo funciona</h2>
<ol class="steps">
<li><b>Consigue tu licencia</b> gratuita o compra un pack de créditos.</li>
<li><b>Copia la configuración</b> del servidor que quieras en tu cliente MCP.</li>
<li><b>Pídeselo a tu agente</b> en lenguaje natural: «concilia este extracto con estas facturas».</li>
</ol>
</section>"""
    ld = [
        {"@context": "https://schema.org", "@type": "WebSite", "name": SITE["name"], "url": SITE["url"] + "/",
         "description": SITE["description"], "inLanguage": "es"},
        {"@context": "https://schema.org", "@type": "Organization", "name": "KeyFlint", "url": "https://keyflint.dev"},
        {"@context": "https://schema.org", "@type": "ItemList", "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "url": f"{SITE['url']}/{m['slug']}/", "name": m["name"]}
            for i, m in enumerate(MCPS)]},
    ]
    return page("/", f"{SITE['name']}: servidores MCP para agentes de IA", SITE["description"], body, ld)


def mcp_page(m: dict) -> str:
    rows = "".join(f"<tr><td><code>{e(t)}</code></td><td>{e(c)}</td><td>{e(d)}</td></tr>" for t, c, d in m["tools"])
    faq = "".join(f"<details><summary>{e(q)}</summary><p>{e(a)}</p></details>" for q, a in m["faq"])
    s = m["slug"]
    body = f"""
<nav class="crumbs"><a href="/">Inicio</a> › {e(m['name'])}</nav>
<section class="hero">
<span class="tag">{e(m['category'])}</span>
<h1>{e(m['headline'])}</h1>
<p class="lead">{e(m['summary'])}</p>
<p><a class="btn" href="#instalar">Instalar</a> <a class="btn ghost" href="/precios/">Comprar créditos</a> <a class="btn ghost" href="{m['repo']}">Código</a></p>
</section>
<section>
<h2>Herramientas y coste</h2>
<div class="table"><table><thead><tr><th>Herramienta</th><th>Créditos</th><th>Qué hace</th></tr></thead><tbody>{rows}</tbody></table></div>
</section>
<section id="instalar">
<h2>Instalar</h2>
<h3>Claude Desktop, Cursor y otros clientes</h3>
<p>Añade esto a la configuración MCP de tu cliente (en Claude Desktop: Ajustes › Desarrollador › Editar configuración). Necesitas <a href="https://docs.astral.sh/uv/">uv</a>.</p>
{code(f'cfg-{s}', claude_config(m))}
<h3>Claude Code</h3>
{code(f'cc-{s}', claude_code_cmd(m))}
<p class="muted">¿No tienes licencia? <a href="/empezar/">Consigue {SITE['free_credits']} créditos gratis</a>.</p>
</section>
<section>
<h2>Preguntas frecuentes</h2>
{faq}
</section>"""
    ld = [
        {"@context": "https://schema.org", "@type": "SoftwareApplication", "name": f"{m['name']} MCP",
         "applicationCategory": "DeveloperApplication", "operatingSystem": "Windows, macOS, Linux",
         "description": m["summary"], "url": f"{SITE['url']}/{s}/", "codeRepository": m["repo"],
         "keywords": ", ".join(m["keywords"]),
         "offers": {"@type": "AggregateOffer", "priceCurrency": "USD",
                    "lowPrice": 0, "highPrice": max(p["price"] for p in SITE["packs"])}},
        {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
            {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in m["faq"]]},
        {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Inicio", "item": SITE["url"] + "/"},
            {"@type": "ListItem", "position": 2, "name": m["name"], "item": f"{SITE['url']}/{s}/"}]},
    ]
    title = f"{m['name']} MCP: {m['headline'].lower()}"
    return page(f"/{s}/", title, m["summary"][:158], body, ld)


def money(n: float) -> str:
    return f"{n:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".").removesuffix(",00")


def pricing() -> str:
    cards = []
    for p in SITE["packs"]:
        per100 = p["price"] / p["credits"] * 100
        cards.append(f"""<div class="pack{' featured' if p.get('featured') else ''}">
<h3>{e(p['name'])}</h3><p class="price">{money(p['price'])} $<span class="per">{e(p.get('period', ''))}</span></p>
<p>{money(p['credits'])} créditos</p><p class="muted small">{e(p['note'])}<br>{money(round(per100, 2))} $ por cada 100 créditos</p>
<a class="btn" href="{p['checkout']}" rel="nofollow">Comprar {e(p['name'])}</a></div>""")
    body = f"""
<section class="hero">
<h1>Precios: un saldo para todos los MCPs</h1>
<p class="lead">Una sola licencia y un solo saldo de créditos para todos los servidores del catálogo. Cada herramienta tiene un coste fijo en créditos y lo que falla no se cobra.</p>
</section>
<div class="packs">
<div class="pack"><h3>Gratis</h3><p class="price">0 $</p><p>{SITE['free_credits']} créditos</p><p class="muted small">Para probar cualquier servidor</p><a class="btn ghost" href="/empezar/">Pedir licencia gratis</a></div>
{''.join(cards)}
</div>
<p class="muted small">Precios en dólares (USD). Los impuestos se calculan en el pago según tu país. El pago lo procesa Stripe y recibes factura. Si tienes NIF/VAT, puedes introducirlo en el pago.</p>
<section>
<h2>¿Cuánto da de sí?</h2>
<ul>
<li>Leer una web: 1 crédito. Auditoría SEO completa: 3.</li>
<li>Leer un extracto Norma 43: 1. Conciliarlo con facturas: 3.</li>
<li>Convertir un libro diario de A3 a ContaPlus: 2. Validarlo: 1.</li>
<li>Validar IBAN, NIF o detectar formatos: gratis.</li>
</ul>
<p>Ejemplo: con el plan Indie (10.000 créditos), una gestoría puede conciliar y convertir unos 2.000 extractos (5 créditos cada uno).</p>
</section>
<section>
<h2>Preguntas frecuentes</h2>
<details><summary>¿Cómo recibo la licencia?</summary><p>Por correo, en el email que uses al pagar, unos segundos después del pago. Revisa la carpeta de spam si no la ves.</p></details>
<details><summary>¿Qué pasa si se me acaban los créditos?</summary><p>La herramienta te avisa con el enlace de compra. El plan Pro se recarga cada mes; Indie y Agency son de pago único.</p></details>
<details><summary>¿Qué es un equipo?</summary><p>Cada ordenador o servidor donde usas la licencia. Indie y Pro permiten 3; Agency, 25.</p></details>
<details><summary>¿Puedo cancelar Pro?</summary><p>Sí, cuando quieras, sin permanencia: desde el enlace de gestión del correo de Stripe o escribiéndonos.</p></details>
<details><summary>¿Qué datos guardáis?</summary><p>Ninguno de tus ficheros: los servidores procesan cada llamada y no guardan nada. Ver <a href="https://keyflint.dev/privacy.html">privacidad</a> y <a href="https://keyflint.dev/dpa.html">encargo de tratamiento</a>.</p></details>
</section>"""
    ld = [{"@context": "https://schema.org", "@type": "Product", "name": "Créditos KeyFlint MCP",
           "description": "Créditos de uso para todos los servidores MCP de KeyFlint.",
           "brand": {"@type": "Brand", "name": "KeyFlint"},
           "offers": [{"@type": "Offer", "name": p["name"], "price": p["price"], "priceCurrency": "USD",
                       "url": f"{SITE['url']}/precios/", "availability": "https://schema.org/InStock"} for p in SITE["packs"]]}]
    return page("/precios/", "Precios de los servidores MCP · KeyFlint MCP",
                f"Un saldo de créditos para todos los servidores MCP de KeyFlint. Desde 29 $/mes o pago único. {SITE['free_credits']} créditos gratis para probar.",
                body, ld)


def thanks() -> str:
    body = f"""
<section class="hero">
<h1>¡Gracias por tu compra!</h1>
<p class="lead">Tu licencia <code>LIC-…</code> está de camino a tu correo. Suele llegar en menos de un minuto.</p>
</section>
<section>
<h2>Siguiente paso</h2>
<ol class="steps">
<li>Copia la licencia del correo (revisa spam si no aparece).</li>
<li>Elige un servidor del <a href="/#catalogo">catálogo</a> y copia su configuración.</li>
<li>Sustituye <code>LIC-tu-licencia</code> por tu licencia y reinicia tu cliente.</li>
</ol>
<p>¿No te ha llegado en 10 minutos? Escribe a <a href="{SITE['contact']}">{e(SITE['contact'].removeprefix('mailto:'))}</a> con el correo que usaste al pagar.</p>
<p><a class="btn" href="/empezar/">Ver la guía de instalación</a></p>
</section>"""
    return page("/gracias/", "Gracias por tu compra · KeyFlint MCP", "Tu licencia está de camino.", body).replace(
        '<meta name="description"', '<meta name="robots" content="noindex">\n<meta name="description"', 1)


def start() -> str:
    m = MCPS[0]
    body = f"""
<section class="hero">
<h1>Empieza en 3 minutos</h1>
<p class="lead">Instala un servidor MCP en Claude, Cursor o Claude Code con una licencia gratuita de {SITE['free_credits']} créditos.</p>
</section>
<section>
<h2>1. Consigue tu licencia</h2>
<p>Escríbenos a <a href="{SITE['contact']}">{e(SITE['contact'].removeprefix('mailto:'))}</a> para una licencia gratuita, o <a href="/precios/">compra un plan</a> y la recibirás por correo. Tiene la forma <code>LIC-…</code> y sirve para todos los servidores.</p>
<h2>2. Instala uv</h2>
{code('uv', 'curl -LsSf https://astral.sh/uv/install.sh | sh   # macOS / Linux' + chr(10) + 'powershell -c "irm https://astral.sh/uv/install.ps1 | iex"   # Windows')}
<h2>3. Añade el servidor a tu cliente</h2>
<p>Ejemplo con {e(m['name'])}. Cada página del <a href="/#catalogo">catálogo</a> tiene su configuración lista para copiar.</p>
{code('cfg', claude_config(m))}
<h2>4. Úsalo</h2>
<p>Reinicia el cliente y pídeselo a tu agente. Para ver tu saldo: «¿cuántos créditos me quedan?» (herramienta <code>credits_balance</code>, gratis).</p>
</section>"""
    ld = [{"@context": "https://schema.org", "@type": "HowTo", "name": "Instalar un servidor MCP de KeyFlint",
           "step": [{"@type": "HowToStep", "name": n} for n in
                    ["Consigue tu licencia", "Instala uv", "Añade el servidor a tu cliente MCP", "Úsalo desde tu agente"]]}]
    return page("/empezar/", "Cómo instalar un servidor MCP en Claude o Cursor · KeyFlint MCP",
                "Guía para instalar servidores MCP en Claude Desktop, Cursor y Claude Code con una licencia gratuita.", body, ld)


def not_found() -> str:
    return page("/404", "Página no encontrada · KeyFlint MCP", "Página no encontrada.",
                '<section class="hero"><h1>Esta página no existe</h1><p><a class="btn" href="/">Ir al catálogo</a></p></section>')


def write(rel: str, text: str) -> None:
    p = OUT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def main() -> None:
    shutil.rmtree(OUT, ignore_errors=True)
    shutil.copytree(ROOT / "assets", OUT / "assets")
    shutil.copy(ROOT / "_headers", OUT / "_headers")
    write("index.html", home())
    write("precios/index.html", pricing())
    write("empezar/index.html", start())
    write("404.html", not_found())
    write("gracias/index.html", thanks())
    for m in MCPS:
        write(f"{m['slug']}/index.html", mcp_page(m))
    paths = ["/", "/empezar/", "/precios/"] + [f"/{m['slug']}/" for m in MCPS]
    write("sitemap.xml", '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
          + "".join(f"<url><loc>{SITE['url']}{p}</loc><lastmod>{TODAY}</lastmod></url>\n" for p in paths) + "</urlset>\n")
    write("robots.txt", f"User-agent: *\nAllow: /\n\nSitemap: {SITE['url']}/sitemap.xml\n")
    write("llms.txt", f"# {SITE['name']}\n\n> {SITE['description']}\n\n"
          + "".join(f"- [{m['name']}]({SITE['url']}/{m['slug']}/): {m['headline']}\n" for m in MCPS)
          + f"- [Precios]({SITE['url']}/precios/)\n- [Empezar]({SITE['url']}/empezar/)\n")
    print(f"OK: {len(paths)} páginas en {OUT}")


if __name__ == "__main__":
    main()

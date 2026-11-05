"""Todos los MCP de KeyFlint en un solo proceso HTTP: /<slug>/mcp (Streamable HTTP, sin estado).

Corre dentro de un Cloudflare Container. El Worker de mcp.keyflint.dev valida el token OAuth y reenvía cada petición
con la licencia del usuario en `X-License-Key`; cada servidor cobra los créditos con esa licencia (modo hosted).
"""

from __future__ import annotations

import contextlib
import importlib
import os

from mcp.server.transport_security import TransportSecuritySettings
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Mount, Route

SERVERS = {
    "web-intel": "web_intel_mcp.server",
    "norma43": "norma43_mcp.server",
    "contabridge": "contabridge_mcp.server",
    "verifactu": "verifactu_mcp.server",
    "dataclean": "dataclean_mcp.server",
}
MAX_BODY = int(os.environ.get("MCP_MAX_BODY", 40_000_000))  # base64 de un Excel de 20 MB + margen

# El Worker es el único que llega aquí; el Host es el del Worker, así que no aplica la protección DNS-rebinding.
OPEN = TransportSecuritySettings(enable_dns_rebinding_protection=False)

apps = {}
for slug, module in SERVERS.items():
    srv = importlib.import_module(module)
    srv.billing.hosted = True  # licencia por petición, nunca la del entorno
    apps[slug] = srv.mcp.streamable_http_app(stateless_http=True, json_response=True, transport_security=OPEN,
                                             max_request_body_size=MAX_BODY)


@contextlib.asynccontextmanager
async def lifespan(_app):
    async with contextlib.AsyncExitStack() as stack:
        for sub in apps.values():
            await stack.enter_async_context(sub.router.lifespan_context(sub))
        yield


async def health(_request):
    return JSONResponse({"ok": True, "servers": sorted(apps)})


app = Starlette(routes=[Route("/healthz", health), *(Mount(f"/{s}", app=a) for s, a in apps.items())],
                lifespan=lifespan)

"""Conector /despacho/mcp: herramientas de Norma 43 + ContaBridge en una URL, misma facturación. Imprime 'despacho OK'."""
import asyncio
import json
import os
import sys

os.environ.setdefault("NORMA43_TRANSPORT", "http")
os.environ.setdefault("CONTABRIDGE_TRANSPORT", "http")
os.environ.setdefault("KEYFLINT_PUBLIC_KEYS", "test")  # sin red: no descarga el llavero
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "container"))

try:
    import httpx
    from mcp.server.transport_security import TransportSecuritySettings
    import norma43_mcp.server as n43
    import contabridge_mcp.server as cb
except ImportError:
    print("despacho SKIP (faltan paquetes)")
    sys.exit(0)

import despacho

H = {"content-type": "application/json", "accept": "application/json, text/event-stream"}


async def main():
    for m in (n43, cb):
        m.billing.hosted = True
    app = despacho.build({"norma43": n43, "contabridge": cb}).streamable_http_app(
        stateless_http=True, json_response=True,
        transport_security=TransportSecuritySettings(enable_dns_rebinding_protection=False))
    async with app.router.lifespan_context(app):
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://mcp") as c:
            async def rpc(method, params=None, headers=None):
                r = await c.post("/mcp", headers={**H, **(headers or {})},
                                 json={"jsonrpc": "2.0", "id": 1, "method": method, "params": params or {}})
                assert r.status_code == 200, (r.status_code, r.text[:300])
                return r.json()

            init = await rpc("initialize", {"protocolVersion": "2025-06-18", "capabilities": {},
                                            "clientInfo": {"name": "t", "version": "1"}})
            assert init["result"]["serverInfo"]["name"] == "flint-despacho", init
            names = [t["name"] for t in (await rpc("tools/list"))["result"]["tools"]]
            assert len(names) == len(set(names)), names
            want = set(n43.mcp._tool_manager._tools) | set(cb.mcp._tool_manager._tools)
            assert set(names) == want, sorted(want ^ set(names))
            for t in ("reconcile_movements", "invoices_to_journal", "sepa_direct_debits", "convert_journal"):
                assert t in names, t
            uris = {r["uri"] for r in (await rpc("resources/list"))["result"]["resources"]}
            assert {"ui://norma43/card.html", "ui://contabridge/card.html"} <= uris, uris

            pr = (await rpc("tools/call", {"name": "pricing", "arguments": {}}))["result"]
            data = pr.get("structuredContent") or json.loads(pr["content"][0]["text"])
            data = data.get("result", data)
            assert set(data) == {"norma43", "contabridge"}, data
            assert "reconcile_movements" in json.dumps(data["norma43"]) and "invoices_to_journal" in json.dumps(data["contabridge"])

            ok = (await rpc("tools/call", {"name": "validate_identifier", "arguments": {"value": "ES9121000418450200051332"}}))["result"]
            assert not ok.get("isError"), ok

            # De pago sin licencia: se rechaza (modo hosted), nunca usa una licencia del entorno.
            paid = await rpc("tools/call", {"name": "parse_norma43", "arguments": {"content": "x"}})
            assert "error" in paid or paid["result"].get("isError"), paid
            assert "license" in json.dumps(paid).lower(), paid
    print("despacho OK", len(names), "herramientas")


asyncio.run(main())

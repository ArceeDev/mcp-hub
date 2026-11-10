"""Conector único para despachos: ContaBridge + Norma 43 en una sola URL (/despacho/mcp).

No reimplementa nada: copia las herramientas y tarjetas (ui://) de cada servidor. Cada herramienta sigue cobrando con
el `billing` de su paquete y la licencia de la petición (X-License-Key), así que precios, reembolsos y validaciones son
exactamente los mismos que en /norma43/mcp y /contabridge/mcp.

Nombres repetidos: `credits_balance` es el mismo saldo (una licencia), se queda uno; `pricing` se fusiona por producto.
"""

from __future__ import annotations

from typing import Any

from mcp.server.mcpserver import MCPServer
from mcp.types import ToolAnnotations

PARTS = ("norma43", "contabridge")
MERGED = {"pricing"}

INSTRUCTIONS = (
    "Flint para despachos: un solo conector con todo lo de Norma 43 y ContaBridge. Flujo típico: `parse_norma43` lee "
    "el extracto; `reconcile_movements` lo casa con facturas o apuntes (los empates salen como `ambiguous`, nunca se "
    "adivina); `bank_to_journal` e `invoices_to_journal` generan el diario y `convert_journal` lo exporta a a3, "
    "ContaPlus, Sage 50, ContaSol o CSV; `sepa_direct_debits` / `sepa_credit_transfers` preparan remesas para el banco. "
    "Importes en texto con 2 decimales. Gratis: `validate_identifier`, `sepa_creditor_id`, `resize_account`, "
    "`detect_format`, `pricing`, `credits_balance`. Lo ilegible no se cobra y los fallos se reembolsan.\n\n"
)


def build(modules: dict[str, Any]) -> MCPServer:
    """`modules`: slug -> módulo `*.server` ya importado (con `mcp`, `billing` y `pricing`)."""
    srv = MCPServer(
        "flint-despacho",
        title="Flint Despacho",
        website_url="https://mcp.keyflint.dev/asesorias/",
        instructions=INSTRUCTIONS + "\n\n".join(f"[{s}] {m.mcp.instructions or ''}" for s, m in modules.items()),
    )
    tools, resources = srv._tool_manager._tools, srv._resource_manager._resources
    for slug, mod in modules.items():
        for name, tool in mod.mcp._tool_manager._tools.items():
            if name in MERGED or name in tools:
                continue  # credits_balance: misma licencia, mismo saldo
            tools[name] = tool
        for uri, res in mod.mcp._resource_manager._resources.items():
            resources.setdefault(uri, res)

    @srv.tool(title="Show tool prices", annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=False))
    def pricing() -> dict[str, Any]:
        """Credit price of every tool (Norma 43 and ContaBridge) and where to buy credits. Free."""
        return {slug: mod.pricing() for slug, mod in modules.items()}

    return srv

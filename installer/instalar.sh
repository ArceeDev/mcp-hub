#!/bin/sh
# Flint · instala los servidores MCP en Claude Desktop, Cursor, VS Code, Windsurf y Claude Code.
#   curl -LsSf https://mcp.keyflint.dev/instalar.sh | sh -s -- LIC-tu-licencia
set -eu
if ! command -v uv >/dev/null 2>&1; then
  echo "Instalando uv (una sola vez)..."
  curl -LsSf https://astral.sh/uv/install.sh | sh
fi
PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"; export PATH
tmp="$(mktemp)"; trap 'rm -f "$tmp"' EXIT
curl -fsSL __SITE__/instalar.py -o "$tmp"
if [ -r /dev/tty ] && [ -w /dev/tty ]; then
  uv run --no-project --python 3.12 --quiet "$tmp" "$@" </dev/tty
else
  uv run --no-project --python 3.12 --quiet "$tmp" "$@"
fi

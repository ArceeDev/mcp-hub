#!/bin/sh
# Flint · Procesa en lote o vigila una carpeta de extractos Norma 43 (.n43/.c43) y Facturae (.xml).
#   curl -LsSf __SITE__/lote.sh | sh -s -- ./mis-extractos
#   curl -LsSf __SITE__/lote.sh | sh -s -- ./mis-extractos --vigilar
set -eu
tmp="$(mktemp)"; trap 'rm -f "$tmp"' EXIT
curl -fsSL __SITE__/lote.py -o "$tmp"
if [ -r /dev/tty ] && [ -w /dev/tty ]; then
  python3 "$tmp" "$@" </dev/tty
else
  python3 "$tmp" "$@"
fi

#!/bin/sh
# Flint · Procesa en lote o vigila una carpeta de extractos Norma 43 (.n43/.c43) y Facturae/VeriFactu (.xml/.xsig).
#   curl -LsSf __SITE__/lote.sh | sh -s -- ./mis-extractos
#   curl -LsSf __SITE__/lote.sh | sh -s -- ./mis-extractos --vigilar
set -eu
tmp="$(mktemp)"; trap 'rm -f "$tmp"' EXIT
curl -fsSL __SITE__/lote.py -o "$tmp"
if command -v python3 >/dev/null 2>&1; then
  RUN="python3"
else
  if ! command -v uv >/dev/null 2>&1; then
    echo "Instalando motor ligero uv (una sola vez)..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
  fi
  PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"; export PATH
  RUN="uv run --no-project --python 3.12 --quiet"
fi
if [ -r /dev/tty ] && [ -w /dev/tty ]; then
  $RUN "$tmp" "$@" </dev/tty
else
  $RUN "$tmp" "$@"
fi

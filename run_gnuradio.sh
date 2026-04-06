#!/usr/bin/env sh
set -eu

PYTHON_BIN="python"
if [ -x ".venv/bin/python" ]; then
  PYTHON_BIN=".venv/bin/python"
fi

exec "$PYTHON_BIN" main.py --config configs/default.yaml --override configs/scenario_gnuradio.yaml "$@"

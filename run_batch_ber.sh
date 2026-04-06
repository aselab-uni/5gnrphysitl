#!/usr/bin/env sh
set -eu

PYTHON_BIN="python"
if [ -x ".venv/bin/python" ]; then
  PYTHON_BIN=".venv/bin/python"
fi

exec "$PYTHON_BIN" run_experiments.py --experiment ber_vs_snr --config configs/default.yaml --output-dir outputs "$@"

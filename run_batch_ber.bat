@echo off
setlocal
set "PYTHON_BIN=python"
if exist ".venv\Scripts\python.exe" set "PYTHON_BIN=.venv\Scripts\python.exe"

"%PYTHON_BIN%" run_experiments.py --experiment ber_vs_snr --config configs/default.yaml --output-dir outputs %*

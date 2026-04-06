@echo off
setlocal
set "PYTHON_BIN=python"
if exist ".venv\Scripts\python.exe" set "PYTHON_BIN=.venv\Scripts\python.exe"

"%PYTHON_BIN%" run_showcases.py --config configs/default.yaml --output-dir outputs\showcases %*

@echo off
rem Abre a Calculadora RESMAT sem precisar do VS Code
cd /d "%~dp0"
if exist ".venv\Scripts\pythonw.exe" (
    start "" ".venv\Scripts\pythonw.exe" main.py
) else (
    echo Ainda nao existe o ambiente .venv nesta pasta.
    echo Abra o main.py no VS Code e de play UMA vez para cria-lo, depois use este atalho.
    pause
)

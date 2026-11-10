import importlib
import importlib.util
import os
import subprocess
import sys

BIBLIOTECAS = ("numpy", "matplotlib")
PASTA = os.path.dirname(os.path.abspath(__file__))
VENV = os.path.join(PASTA, ".venv")
PYTHON_VENV = os.path.join(VENV, "Scripts", "python.exe") if os.name == "nt" \
    else os.path.join(VENV, "bin", "python")


def faltando():
    return [m for m in BIBLIOTECAS if importlib.util.find_spec(m) is None]


def mesmo_arquivo(a, b):
    return os.path.normcase(os.path.abspath(a)) == os.path.normcase(os.path.abspath(b))


if faltando():
    if not mesmo_arquivo(sys.executable, PYTHON_VENV):
        if not os.path.exists(PYTHON_VENV):
            print("Criando o ambiente do projeto (.venv) - so na primeira vez...")
            subprocess.check_call([sys.executable, "-m", "venv", VENV])
        sys.exit(subprocess.call([PYTHON_VENV, os.path.abspath(__file__)]))

    print("Instalando", ", ".join(faltando()), "- aguarde 1 ou 2 minutos...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", *faltando()])
    importlib.invalidate_caches()
    print("Instalado! Abrindo a calculadora...")

from app import ResmatCalculatorApp

if __name__ == "__main__":
    app = ResmatCalculatorApp()
    app.mainloop()
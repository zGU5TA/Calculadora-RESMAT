# ==============================================================================
# A3 - Calculadora Estrutural Interativa | Resistência dos Materiais I
# Para rodar pelo código: dê play neste arquivo (ou: python main.py).
# Para rodar sem Python: use o CalculadoraRESMAT.exe (veja o README).
# ==============================================================================
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
RODANDO_COMO_EXE = getattr(sys, "frozen", False)   # True dentro do .exe


def faltando():
    return [m for m in BIBLIOTECAS if importlib.util.find_spec(m) is None]


def mesmo_arquivo(a, b):
    return os.path.normcase(os.path.abspath(a)) == os.path.normcase(os.path.abspath(b))


# Rodando pelo código, na primeira vez: cria um ambiente próprio do projeto
# (pasta .venv) e instala numpy + matplotlib nele. Não mexe no Python do PC.
# No .exe as bibliotecas já vêm dentro, então isso é pulado.
if not RODANDO_COMO_EXE and faltando():
    if not mesmo_arquivo(sys.executable, PYTHON_VENV):
        if not os.path.exists(PYTHON_VENV):
            print("Criando o ambiente do projeto (.venv) - só na primeira vez...")
            subprocess.check_call([sys.executable, "-m", "venv", VENV])
        # Roda este mesmo arquivo de novo, agora com o Python do .venv
        sys.exit(subprocess.call([PYTHON_VENV, os.path.abspath(__file__)]))

    print("Instalando", ", ".join(faltando()), "- aguarde 1 ou 2 minutos...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", *faltando()])
    importlib.invalidate_caches()
    print("Instalado! Abrindo a calculadora...")

from calculadora.interface.app import ResmatCalculatorApp  # noqa: E402

if __name__ == "__main__":
    app = ResmatCalculatorApp()
    app.mainloop()
    sys.exit(app.codigo_saida)

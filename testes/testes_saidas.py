# ==============================================================================
# TESTES DAS SAÍDAS (não abre janela): memória, CSV, PNG, leitor do mouse, deformada.
# Rodar da pasta principal:  python testes/testes_saidas.py
# ==============================================================================
import os
import sys
import tempfile

import matplotlib
matplotlib.use("Agg")

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from testes_calculos import calc, dados  # noqa: E402
from calculadora.calculo.memoria import gerar_memoria, texto_plano  # noqa: E402
from calculadora.interface import diagramas, saidas  # noqa: E402

UNID = ("kN", "m")


def teste_memoria():
    d = dados(P=20e3, xP=1.2)
    txt = texto_plano(gerar_memoria(d, calc.calcular(d), UNID))
    assert "Flambagem" in txt or "flambagem" in txt
    assert "FS" in txt


def teste_exportar_tudo():
    d = dados(P=20e3, xP=1.2)
    r = calc.calcular(d)
    with tempfile.TemporaryDirectory() as pasta:
        arquivos = saidas.exportar_tudo(pasta, d, r, UNID)
        for a in arquivos:
            assert os.path.getsize(a) > 500, a
        with open(arquivos[2], encoding="utf-8-sig") as f:
            assert "Coeficientes de segurança" in f.read()
        with open(arquivos[3], encoding="utf-8-sig") as f:
            assert len(f.readlines()) == len(r.x) + 1


def teste_leitor_e_deformada():
    d = dados(P=20e3, xP=1.2)
    r = calc.calcular(d)
    fig, axes, leitor = diagramas.nova_figura_diagramas()
    diagramas.desenhar_com_cursor(fig, axes, leitor, d, r, UNID)
    i, texto = leitor.texto_em(0.8)
    assert abs(leitor.x[i] - 0.8) < 0.01 and "M =" in texto and "V =" in texto
    leitor.esconder()
    fig2, ax = diagramas.criar_figura_deformada()
    for f in (1, diagramas.fator_automatico(d, r), 500):
        diagramas.desenhar_deformada(ax, d, r, UNID, f)
    assert diagramas.fator_automatico(d, r) >= 1


if __name__ == "__main__":
    for nome, f in list(globals().items()):
        if nome.startswith("teste_"):
            f()
            print("ok ", nome)
    print("Todos os testes de saída passaram.")

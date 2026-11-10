# ==============================================================================
# TESTES DOS CÁLCULOS (não abre janela).
# Compara a calculadora com fórmulas conhecidas de Resistência dos Materiais.
# Rodar da pasta principal:  python testes/testes_calculos.py
# ==============================================================================
import dataclasses
import json
import math
import os
import sys

import numpy as np

# Terminal do Windows nem sempre aceita δ, ³ etc.: força UTF-8 na saída
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Permite rodar de qualquer lugar: python testes/testes_calculos.py
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from calculadora.calculo.calculos import CalculadoraEstrutural  # noqa: E402
from calculadora.calculo.modelos import DadosEntrada, Ligacao, Material, Secao  # noqa: E402

ACO = Material("Aço Estrutural A36", E=200e9, sigma_y=250e6, tau_adm=145e6)
calc = CalculadoraEstrutural()


def dados(**mudancas):
    base = dict(P=100e3, xP=0.0, L=2.0, xB=0.8, xC=2.0, LA=1.0, LB=1.0,
                secao_viga=Secao("Retangular", b=0.05, h=0.10),
                secao_barraA=Secao("Circular", d=0.02),
                secao_barraB=Secao("Circular", d=0.02),
                mat_viga=ACO, mat_barraA=ACO, mat_barraB=ACO,
                lig_B=Ligacao(0.012, 2, ACO), lig_C=Ligacao(0.012, 2, ACO))
    base.update(mudancas)
    return DadosEntrada(**base)


def perto(a, b, tol=1e-6):
    return abs(a - b) <= tol * max(1.0, abs(a), abs(b))


def valor_em(r, x):
    return float(np.interp(x, r.x, r.deflexao))


def teste_equilibrio():
    rng = np.random.default_rng(0)
    for _ in range(200):
        L = rng.uniform(0.5, 5)
        xB, xC, xP = rng.uniform(0, L, 3)
        if abs(xB - xC) < 1e-3:
            continue
        d = dados(L=L, xB=xB, xC=xC, xP=xP, P=rng.uniform(-5e4, 5e4))
        assert not calc.validar(d)
        r = calc.calcular(d)
        assert perto(r.FA + r.FB, d.P)                                   # ΣFy = 0
        assert perto(r.FA * xB + r.FB * xC, d.P * xP)                    # ΣM_A = 0
        assert abs(r.V[-1]) < 1e-6 * abs(d.P) + 1e-9                     # V fecha em 0
        assert abs(r.M[-1]) < 1e-6 * abs(d.P) * L + 1e-9                 # M fecha em 0
        assert perto(valor_em(r, xB), r.desloc_B, 1e-9)                  # linha elástica passa
        assert perto(valor_em(r, xC), r.desloc_C, 1e-9)                  # por B e por C
    print("OK  equilíbrio, diagramas fechando em zero e linha elástica passando por B e C")


def teste_sinal_barra_CE():
    # Caso padrão: P na ponta A, barra B (CE, embaixo) puxa a viga para BAIXO -> TRAÇÃO
    r = calc.calcular(dados())
    assert r.FB < 0 and r.barraB.estado == "TRAÇÃO" and r.barraB.alongamento > 0
    assert r.FA > 0 and r.barraA.estado == "TRAÇÃO"
    # P entre as barras: a barra CE empurra a viga para cima -> COMPRESSÃO
    r2 = calc.calcular(dados(xP=1.4))
    assert r2.FB > 0 and r2.barraB.estado == "COMPRESSÃO" and r2.barraB.alongamento < 0
    print("OK  tração/compressão da barra CE (que fica ABAIXO da viga)")


def teste_balanco():
    # Ponta em balanço: flecha de flexão = P a² (a + l) / (3 E I)
    d = dados()
    r = calc.calcular(d)
    a, l = d.xB, d.xC - d.xB
    EI = ACO.E * d.secao_viga.inercia
    flexao = d.P * a ** 2 * (a + l) / (3 * EI)
    rigida = r.desloc_B + (r.desloc_C - r.desloc_B) * (0 - d.xB) / (d.xC - d.xB)
    assert perto(r.desloc_A, rigida - flexao, 1e-9)
    print(f"OK  balanço: δ_A = {r.desloc_A * 1000:.4f} mm (fórmula: {(rigida - flexao) * 1000:.4f} mm)")


def teste_biapoiada():
    # Barras quase indeformáveis + P no meio do vão = viga biapoiada: δ = P L³ / (48 E I)
    rigido = Material("rígido", E=1e20, sigma_y=None, tau_adm=None)
    d = dados(xB=0.0, xC=2.0, xP=1.0, mat_barraA=rigido, mat_barraB=rigido)
    r = calc.calcular(d)
    EI = ACO.E * d.secao_viga.inercia
    esperado = -d.P * d.L ** 3 / (48 * EI)
    assert perto(valor_em(r, 1.0), esperado, 1e-9)
    assert perto(r.M_max, d.P * d.L / 4, 1e-9)
    print(f"OK  biapoiada: δ_meio = {valor_em(r, 1.0) * 1000:.4f} mm (PL³/48EI = {esperado * 1000:.4f} mm)")


def teste_barra_A_depois_da_barra_B():
    # Antes (linha 530) o gráfico zerava quando xB > xC. Agora tem que funcionar.
    r = calc.calcular(dados(xB=1.6, xC=0.4, xP=1.0))
    assert np.max(np.abs(r.deflexao)) > 0
    assert perto(valor_em(r, 1.6), r.desloc_B, 1e-9)
    assert perto(valor_em(r, 0.4), r.desloc_C, 1e-9)
    print("OK  barra A à direita da barra B (xB > xC)")


def teste_pinos():
    d = dados()
    r = calc.calcular(d)
    area = math.pi * 0.006 ** 2
    assert perto(r.pinoB.tau, abs(r.FA) / (2 * area))
    r1 = calc.calcular(dados(lig_B=Ligacao(0.012, 1, ACO)))
    assert perto(r1.pinoB.tau, 2 * r.pinoB.tau)
    print("OK  cisalhamento simples/duplo nos pinos/rebites")


def teste_varios_pinos():
    # A força se divide entre os pinos: 2 pinos = metade da tensão de 1 pino
    um = calc.calcular(dados(lig_B=Ligacao(0.012, 2, ACO, n_pinos=1)))
    tres = calc.calcular(dados(lig_B=Ligacao(0.012, 2, ACO, n_pinos=3)))
    assert perto(tres.pinoB.tau, um.pinoB.tau / 3)
    assert tres.pinoB.n_pinos == 3
    assert calc.validar(dados(lig_C=Ligacao(0.012, 2, ACO, n_pinos=0)))
    print("OK  quantidade de pinos/rebites divide a força entre eles")


def teste_esforco_normal_e_posicoes_dos_maximos():
    r = calc.calcular(dados(xP=1.2))
    assert np.all(r.N == 0) and len(r.N) == len(r.x)     # N(x) = 0 em toda a viga
    assert perto(abs(r.V[np.argmax(np.abs(r.V))]), abs(r.V_max))
    assert perto(abs(r.M_max), abs(r.M[np.argmin(np.abs(r.x - r.x_M_max))]))
    assert perto(r.sigma_flex_max,
                 abs(r.M_max) * dados().secao_viga.y_max / dados().secao_viga.inercia)
    assert 0 <= r.x_V_max <= 2.0 and 0 <= r.x_sigma_flex_max <= 2.0
    print("OK  N(x) = 0 e posições de V, M e σ máximos")


def teste_validacao():
    assert calc.validar(dados(xP=3.0))                 # P fora da viga
    assert calc.validar(dados(xB=1.0, xC=1.0))         # barras na mesma posição
    assert calc.validar(dados(xC=2.5))                 # barra fora da viga
    assert calc.validar(dados(mat_viga=Material("Personalizado", E=None)))
    assert calc.validar(dados(P=float("nan")))         # "nan" digitado no campo
    assert calc.validar(dados(L=float("inf")))         # "inf" digitado no campo
    assert not calc.validar(dados())
    print("OK  validação das posições, dos materiais e de nan/inf")


def teste_caso_de_teste_manual():
    """Compara a calculadora com as contas feitas à mão (testes/caso_de_teste.json)."""
    pasta = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(pasta, "caso_de_teste.json"), encoding="utf-8") as f:
        caso = json.load(f)
    e, esp = caso["entradas"], caso["esperado_manual"]

    d = DadosEntrada(
        P=e["P_kN"] * 1e3, xP=e["xP_m"], L=e["L_m"], xB=e["xB_m"], xC=e["xC_m"],
        LA=e["LA_m"], LB=e["LB_m"],
        secao_viga=Secao("Retangular", b=e["viga"]["b_mm"] / 1e3, h=e["viga"]["h_mm"] / 1e3),
        secao_barraA=Secao("Circular", d=e["barraA"]["d_mm"] / 1e3),
        secao_barraB=Secao("Circular", d=e["barraB"]["d_mm"] / 1e3),
        mat_viga=ACO, mat_barraA=ACO, mat_barraB=ACO,
        lig_B=Ligacao(e["pino_B"]["d_mm"] / 1e3, 2, ACO, n_pinos=e["pino_B"]["quantidade"]),
        lig_C=Ligacao(e["pino_C"]["d_mm"] / 1e3, 2, ACO, n_pinos=e["pino_C"]["quantidade"]))
    assert not calc.validar(d)
    r = calc.calcular(d)

    linhas = [  # (nome, unidade, valor do programa, valor manual)
        ("Força da barra A na viga (FA)", "kN", r.FA / 1e3, esp["FA_kN"]),
        ("Força da barra B na viga (FB)", "kN", r.FB / 1e3, esp["FB_kN"]),
        ("Esforço normal barra A", "kN", r.barraA.forca_normal / 1e3, esp["N_barraA_kN"]),
        ("Esforço normal barra B", "kN", r.barraB.forca_normal / 1e3, esp["N_barraB_kN"]),
        ("Tensão normal barra A", "MPa", r.barraA.tensao / 1e6, esp["sigma_barraA_MPa"]),
        ("Tensão normal barra B", "MPa", r.barraB.tensao / 1e6, esp["sigma_barraB_MPa"]),
        ("Cisalhamento pino B", "MPa", r.pinoB.tau / 1e6, esp["tau_pinoB_MPa"]),
        ("Cisalhamento pino C", "MPa", r.pinoC.tau / 1e6, esp["tau_pinoC_MPa"]),
        ("Cortante máximo |V|", "kN", abs(r.V_max) / 1e3, esp["V_max_kN"]),
        ("Momento máximo |M|", "kN·m", abs(r.M_max) / 1e3, esp["M_max_kNm"]),
        ("Posição do momento máximo", "m", r.x_M_max, esp["x_M_max_m"]),
        ("Tensão de flexão máxima", "MPa", r.sigma_flex_max / 1e6, esp["sigma_flexao_MPa"]),
        ("Alongamento barra A", "mm", r.barraA.alongamento * 1e3, esp["alongamento_barraA_mm"]),
        ("Alongamento barra B", "mm", r.barraB.alongamento * 1e3, esp["alongamento_barraB_mm"]),
    ]
    print("\n  CASO DE TESTE (programa x cálculo manual)")
    print(f"  {'Grandeza':<32}{'Programa':>12}{'Manual':>12}{'Dif. abs.':>12}{'Dif. %':>9}")
    for nome, un, prog, manual in linhas:
        dif = prog - manual
        pct = abs(dif) / abs(manual) * 100 if manual else 0.0
        print(f"  {nome:<32}{prog:>12.4f}{manual:>12.4f}{dif:>+12.4f}{pct:>8.4f}%  {un}")
        assert pct < 0.01, f"{nome}: diferença de {pct:.4f}% em relação ao cálculo manual"
    assert r.barraA.estado == esp["estado_barraA"] and r.barraB.estado == esp["estado_barraB"]

    # Alterar uma entrada tem que alterar o resultado (requisito de interatividade)
    r2 = calc.calcular(dataclasses.replace(d, P=2 * d.P))
    assert perto(r2.barraA.tensao, 2 * r.barraA.tensao)
    print("OK  caso de teste manual (diferenças < 0,01 %) e resultados mudam com a entrada")


if __name__ == "__main__":
    teste_equilibrio()
    teste_sinal_barra_CE()
    teste_balanco()
    teste_biapoiada()
    teste_barra_A_depois_da_barra_B()
    teste_pinos()
    teste_varios_pinos()
    teste_esforco_normal_e_posicoes_dos_maximos()
    teste_validacao()
    teste_caso_de_teste_manual()
    print("\nTodos os testes passaram.")

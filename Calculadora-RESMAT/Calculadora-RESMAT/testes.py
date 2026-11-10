# ==============================================================================
# TESTES DOS CÁLCULOS (não abre janela).  Rodar:  python testes.py
# Compara a calculadora com fórmulas conhecidas de Resistência dos Materiais.
# ==============================================================================
import math

import numpy as np

from calculos import CalculadoraEstrutural
from modelos import DadosEntrada, Ligacao, Material, Secao

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


def teste_validacao():
    assert calc.validar(dados(xP=3.0))                 # P fora da viga
    assert calc.validar(dados(xB=1.0, xC=1.0))         # barras na mesma posição
    assert calc.validar(dados(xC=2.5))                 # barra fora da viga
    assert calc.validar(dados(mat_viga=Material("Personalizado", E=None)))
    assert not calc.validar(dados())
    print("OK  validação das posições e dos materiais")


if __name__ == "__main__":
    teste_equilibrio()
    teste_sinal_barra_CE()
    teste_balanco()
    teste_biapoiada()
    teste_barra_A_depois_da_barra_B()
    teste_pinos()
    teste_validacao()
    print("\nTodos os testes passaram.")

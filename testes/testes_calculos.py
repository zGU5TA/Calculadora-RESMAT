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
    # Viga FLEXÍVEL em balanço: flecha de flexão = P a² (a + l) / (3 E I)
    d = dados()
    r = calc.calcular(d)
    a, l = d.xB, d.xC - d.xB
    EI = ACO.E * d.secao_viga.inercia
    flexao = d.P * a ** 2 * (a + l) / (3 * EI)
    rigida = r.desloc_B + (r.desloc_C - r.desloc_B) * (0 - d.xB) / (d.xC - d.xB)
    assert perto(r.deflexao[0], rigida - flexao, 1e-9)         # referência flexível
    assert perto(r.desloc_A, rigida, 1e-9)                      # viga rígida (professor)
    print(f"OK  balanço: flexível δ_A = {r.deflexao[0] * 1000:.4f} mm "
          f"(fórmula: {(rigida - flexao) * 1000:.4f} mm); rígida δ_A = {r.desloc_A * 1000:.4f} mm")


def teste_viga_rigida():
    # Desenho do professor: reta por B' e C'; δA por semelhança de triângulos
    d = dados()
    r = calc.calcular(d)
    assert perto(r.desloc_B, -r.barraA.alongamento) and perto(r.desloc_C, r.barraB.alongamento)
    for xi, vi in ((d.xB, r.desloc_B), (d.xC, r.desloc_C), (0.0, r.desloc_A), (d.xP, r.desloc_P)):
        assert perto(float(np.interp(xi, r.x, r.deflexao_rigida)), vi, 1e-9)
    # semelhança de triângulos: (δC - δB)/(xC - xB) = (δB - δA)/(xB - xA)
    assert perto((r.desloc_C - r.desloc_B) / (d.xC - d.xB),
                 (r.desloc_B - r.desloc_A) / (d.xB - 0.0), 1e-9)
    # a viga rígida é uma reta: diferenças de inclinação nulas
    inclin = np.diff(r.deflexao_rigida) / np.maximum(np.diff(r.x), 1e-12)
    assert np.allclose(inclin[np.diff(r.x) > 0], r.rotacao, rtol=1e-6, atol=1e-12)
    # barras iguais e viga bem rígida: a flexão ignorada é pequena perto dos deslocamentos
    assert r.flexao_extra_max >= 0
    print(f"OK  viga rígida: δA = {r.desloc_A * 1000:+.4f} mm, δB = {r.desloc_B * 1000:+.4f} mm, "
          f"δC = {r.desloc_C * 1000:+.4f} mm (reta por B' e C')")


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


def teste_flambagem():
    # P entre as barras (xP = 1,2 m): a barra B (CE) fica COMPRIMIDA
    r = calc.calcular(dados(P=20e3, xP=1.2))
    assert r.barraA.flambagem is None                      # barra A tracionada: não flamba
    fl = r.barraB.flambagem
    assert fl is not None and r.barraB.estado == "COMPRESSÃO"
    # Conta à mão: d = 20 mm, L = 1 m, A36 (E = 200 GPa), articulada nas duas pontas
    I = math.pi * 0.02 ** 4 / 64
    P_cr = math.pi ** 2 * 200e9 * I / 1.0 ** 2
    assert fl.regime == "Euler" and perto(fl.esbeltez, 200.0)
    assert perto(fl.carga_critica, P_cr), (fl.carga_critica, P_cr)
    assert perto(fl.fs, P_cr / (20e3 * (1.2 - 0.8) / (2.0 - 0.8)))   # N_B = F_B = P·(xP−xB)/(xC−xB)
    assert any(v.chave == "barraB_flambagem" for v in r.verificacoes)

    # Barra curta e grossa: λ < λc  ->  parábola de Johnson (e não Euler)
    r2 = calc.calcular(dados(P=20e3, xP=1.2, LB=0.3,
                             secao_barraB=Secao("Circular", d=0.06)))
    fl2 = r2.barraB.flambagem
    assert fl2.regime == "Johnson" and fl2.esbeltez < fl2.esbeltez_limite
    sy, E = 250e6, 200e9
    assert perto(fl2.tensao_critica, sy * (1 - sy * fl2.esbeltez ** 2 / (4 * math.pi ** 2 * E)))
    assert fl2.tensao_critica < sy                          # nunca passa do escoamento

    # Seção retangular: flamba em torno do eixo de MENOR inércia
    s = Secao("Retangular", b=0.01, h=0.03)
    assert perto(s.inercia_min, 0.03 * 0.01 ** 3 / 12)
    print(f"OK  flambagem: Euler P_cr = {P_cr / 1e3:.3f} kN (FS = {fl.fs:.3f}) e Johnson")


def teste_coeficientes_de_seguranca():
    # Mesmo caso do JSON: P = 20 kN, pinos de 16 mm (com pinos de 12 mm o pino B falharia)
    pinos16 = dict(lig_B=Ligacao(0.016, 2, ACO), lig_C=Ligacao(0.016, 2, ACO))
    r = calc.calcular(dados(P=20e3, **pinos16))
    por = {v.chave: v for v in r.verificacoes}
    esperado = {"barraA_escoamento": 250e6 / abs(r.barraA.tensao),
                "barraB_escoamento": 250e6 / abs(r.barraB.tensao),
                "pinoB_cisalhamento": 145e6 / r.pinoB.tau,
                "pinoC_cisalhamento": 145e6 / r.pinoC.tau,
                "viga_flexao": 250e6 / r.sigma_flex_max}
    for chave, fs in esperado.items():
        assert perto(por[chave].fs, fs), chave
    assert perto(r.fs_minimo, min(esperado.values()))
    assert perto(por["viga_flexao"].utilizacao, 1 / por["viga_flexao"].fs)

    # Níveis: FS >= 1,5 verde; 1 <= FS < 1,5 amarelo; FS < 1 vermelho
    assert por["barraA_escoamento"].nivel == "ok"
    assert por["viga_flexao"].nivel == "atencao"      # σ = 192 MPa, FS = 1,30
    assert r.nivel_geral == "atencao"
    r_falha = calc.calcular(dados(P=100e3))             # barra A passa do escoamento
    assert {v.chave: v.nivel for v in r_falha.verificacoes}["barraA_escoamento"] == "falha"
    assert r_falha.nivel_geral == "falha"
    r_ok = calc.calcular(dados(P=5e3))
    assert r_ok.nivel_geral == "ok"

    # Sem σ_esc informado: não verifica, em vez de inventar um limite
    r_sem = calc.calcular(dados(P=20e3, mat_barraA=Material("Personalizado", E=200e9)))
    assert {v.chave: v.nivel for v in r_sem.verificacoes}["barraA_escoamento"] == "sem_limite"
    # Sem carga atuando numa barra (P = 0): FS infinito e "ok"
    r_zero = calc.calcular(dados(P=0.0))
    assert all(v.nivel == "ok" for v in r_zero.verificacoes)
    print(f"OK  coeficientes de segurança (menor FS = {r.fs_minimo:.3f} na flexão da viga)")


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

    fs = {v.chave: v.fs for v in r.verificacoes}
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
        ("Deslocamento de B (rígida)", "mm", r.desloc_B * 1e3, esp["desloc_B_mm"]),
        ("Deslocamento de C (rígida)", "mm", r.desloc_C * 1e3, esp["desloc_C_mm"]),
        ("Deslocamento de A (rígida)", "mm", r.desloc_A * 1e3, esp["desloc_A_mm_viga_rigida"]),
        ("FS barra A (escoamento)", "", fs["barraA_escoamento"], esp["FS_barraA_escoamento"]),
        ("FS barra B (escoamento)", "", fs["barraB_escoamento"], esp["FS_barraB_escoamento"]),
        ("FS pino B", "", fs["pinoB_cisalhamento"], esp["FS_pinoB"]),
        ("FS pino C", "", fs["pinoC_cisalhamento"], esp["FS_pinoC"]),
        ("FS viga (flexão)", "", fs["viga_flexao"], esp["FS_viga_flexao"]),
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
    teste_viga_rigida()
    teste_biapoiada()
    teste_barra_A_depois_da_barra_B()
    teste_pinos()
    teste_varios_pinos()
    teste_esforco_normal_e_posicoes_dos_maximos()
    teste_flambagem()
    teste_coeficientes_de_seguranca()
    teste_validacao()
    teste_caso_de_teste_manual()
    print("\nTodos os testes passaram.")

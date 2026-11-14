# ==============================================================================
# MEMÓRIA DE CÁLCULO: o passo a passo com as equações e os números substituídos
# (sem tkinter: a tela só mostra, e a exportação grava em .txt)
#
# Devolve uma lista de blocos (tipo, texto). Tipos:
#   "titulo", "subtitulo", "texto", "eq" (equação), "res" (resultado), "aviso"
# Todas as contas são feitas em N, m e Pa (SI); os resultados também aparecem
# nas unidades escolhidas na tela.
# ==============================================================================
import math

from calculadora.calculo.dados import UNITS
from calculadora.calculo.modelos import DadosEntrada, Resultados

TOL = 1e-9


def _g(v, digitos=6):
    """Número curto e legível: 166667 / 33333.3 / 1.061e-04."""
    if v is None:
        return "—"
    if v == 0:
        return "0"
    if math.isinf(v):
        return "∞"
    a = abs(v)
    if 1e-3 <= a < 1e7:
        return f"{v:.{digitos}g}"
    return f"{v:.4e}"


def _p(v):
    """Número entre parênteses se for negativo (para substituir nas equações)."""
    return f"({_g(v)})" if v < 0 else _g(v)


def _desc_secao(s):
    if s.forma == "Retangular":
        return f"retangular  b = {_g(s.b * 1000)} mm  ×  h = {_g(s.h * 1000)} mm"
    return f"circular  d = {_g(s.d * 1000)} mm"


def _desc_material(m):
    partes = [f"E = {_g(m.E / 1e9)} GPa" if m.E else "E não informado"]
    if m.sigma_y:
        partes.append(f"σ_esc = {_g(m.sigma_y / 1e6)} MPa")
    if m.tau_adm:
        partes.append(f"τ_adm = {_g(m.tau_adm / 1e6)} MPa")
    return f"{m.nome}: " + ", ".join(partes)


def _area_eq(s, nome="A"):
    """Linha com a fórmula da área da seção, já substituída."""
    if s.forma == "Retangular":
        return (f"{nome} = b·h = {_g(s.b)}·{_g(s.h)} = {_g(s.area)} m²")
    return (f"{nome} = π·d²/4 = π·({_g(s.d)})²/4 = {_g(s.area)} m²")


def _sentido(v, positivo, negativo):
    return positivo if v > 0 else (negativo if v < 0 else "nulo")


def gerar_memoria(d: DadosEntrada, r: Resultados, unidades) -> list:
    u_F, u_L = unidades
    kF = 1.0 / UNITS["force"][u_F]
    kL = 1.0 / UNITS["pos"][u_L]
    blocos = []

    def add(tipo, texto=""):
        blocos.append((tipo, texto))

    P, xP, xB, xC, L = d.P, d.xP, d.xB, d.xC, d.L
    FA, FB = r.FA, r.FB
    bA, bB = r.barraA, r.barraB

    # ---- 1. Dados ---------------------------------------------------------------
    add("titulo", "1. DADOS DE ENTRADA (as contas abaixo usam N, m e Pa)")
    add("texto", f"P = {_g(P)} N  ({_g(P * kF)} {u_F}), "
                 f"{'para baixo' if P >= 0 else 'para cima'}, aplicada em xP = {_g(xP)} m")
    add("texto", f"Viga AC: L = {_g(L)} m, seção {_desc_secao(d.secao_viga)}")
    add("texto", f"  {_desc_material(d.mat_viga)}")
    add("texto", f"Barra A (BD), acima da viga em xB = {_g(xB)} m: comprimento "
                 f"L_A = {_g(d.LA)} m, seção {_desc_secao(d.secao_barraA)}")
    add("texto", f"  {_desc_material(d.mat_barraA)}")
    add("texto", f"Barra B (CE), abaixo da viga em xC = {_g(xC)} m: comprimento "
                 f"L_B = {_g(d.LB)} m, seção {_desc_secao(d.secao_barraB)}")
    add("texto", f"  {_desc_material(d.mat_barraB)}")
    for nome, lig in (("B", d.lig_B), ("C", d.lig_C)):
        tipo = "duplo" if lig.n_planos == 2 else "simples"
        add("texto", f"Pino/rebite {nome}: {lig.n_pinos} unidade(s) de d = {_g(lig.d * 1000)} mm, "
                     f"cisalhamento {tipo} ({lig.n_planos} plano(s)); {_desc_material(lig.material)}")

    # ---- 2. Equilíbrio ----------------------------------------------------------
    add("titulo", "2. EQUILÍBRIO DA VIGA")
    add("texto", "Incógnitas: F_A (barra A, em B) e F_B (barra B, em C), positivas para cima.")
    add("eq", "ΣM_C = 0:   F_A·(xC − xB) − P·(xC − xP) = 0")
    add("eq", f"F_A = P·(xC − xP)/(xC − xB) = {_g(P)}·({_g(xC)} − {_g(xP)})"
              f"/({_g(xC)} − {_g(xB)}) = {_g(FA)} N")
    add("eq", "ΣF_y = 0:   F_A + F_B − P = 0")
    add("eq", f"F_B = P − F_A = {_g(P)} − {_p(FA)} = {_g(FB)} N")
    add("res", f"F_A = {_g(FA * kF)} {u_F} ({_sentido(FA, 'para cima', 'para baixo')})   |   "
               f"F_B = {_g(FB * kF)} {u_F} ({_sentido(FB, 'para cima', 'para baixo')})")

    # ---- 3. Esforço normal nas barras --------------------------------------------
    add("titulo", "3. ESFORÇO NORMAL NAS BARRAS (+ tração, − compressão)")
    add("texto", "A barra A fica ACIMA da viga: se puxa a viga para cima (F_A > 0), está "
                 "tracionada; se empurra para baixo (F_A < 0), está comprimida.")
    add("eq", f"N_A = +F_A = {_g(bA.forca_normal)} N   →   {bA.estado}")
    add("texto", "A barra B fica ABAIXO da viga: se puxa a viga para baixo (F_B < 0), está "
                 "tracionada; se empurra para cima (F_B > 0), está comprimida.")
    add("eq", f"N_B = −F_B = −{_p(FB)} = {_g(bB.forca_normal)} N   →   {bB.estado}")

    # ---- 4. Tensão normal --------------------------------------------------------
    add("titulo", "4. TENSÃO NORMAL NAS BARRAS:  σ = N / A")
    for nome, barra, secao in (("A", bA, d.secao_barraA), ("B", bB, d.secao_barraB)):
        add("subtitulo", f"Barra {nome}")
        add("eq", _area_eq(secao))
        add("eq", f"σ = N/A = {_p(barra.forca_normal)} / {_g(secao.area)} = {_g(barra.tensao)} Pa"
                  f" = {_g(barra.tensao / 1e6)} MPa")
        sy = barra.material.sigma_y
        if sy:
            add("texto", f"  σ_esc = {_g(sy / 1e6)} MPa  →  |σ|/σ_esc = "
                         f"{_g(abs(barra.tensao) / sy * 100, 4)} %")

    # ---- 5. Alongamento -----------------------------------------------------------
    add("titulo", "5. VARIAÇÃO DE COMPRIMENTO DAS BARRAS:  δ = N·L / (E·A)")
    for nome, barra, secao, comp, mat in (("A", bA, d.secao_barraA, d.LA, d.mat_barraA),
                                          ("B", bB, d.secao_barraB, d.LB, d.mat_barraB)):
        add("eq", f"δ_{nome} = {_p(barra.forca_normal)}·{_g(comp)} / ({_g(mat.E)}·{_g(secao.area)})"
                  f" = {_g(barra.alongamento)} m = {_g(barra.alongamento * 1000)} mm")
        add("res", f"Barra {nome}: {'alonga' if barra.alongamento > 0 else 'encurta'} "
                   f"{_g(abs(barra.alongamento) * 1000)} mm")

    # ---- 6. Pinos / rebites ---------------------------------------------------------
    add("titulo", "6. PINOS/REBITES (cisalhamento):  τ = F / (n·m·A_pino)")
    add("texto", "n = quantidade de pinos (a força se divide igualmente), m = planos de corte "
                 "(1 simples, 2 duplo).")
    for nome, pino, lig in (("B", r.pinoB, d.lig_B), ("C", r.pinoC, d.lig_C)):
        add("subtitulo", f"Pino/rebite {nome}")
        add("eq", f"A_pino = π·d²/4 = π·({_g(lig.d)})²/4 = {_g(lig.area)} m²")
        add("eq", f"τ = {_g(pino.forca)} / ({lig.n_pinos}·{lig.n_planos}·{_g(lig.area)}) = "
                  f"{_g(pino.tau)} Pa = {_g(pino.tau / 1e6)} MPa")
        if lig.material.tau_adm:
            add("texto", f"  τ_adm = {_g(lig.material.tau_adm / 1e6)} MPa  →  τ/τ_adm = "
                         f"{_g(pino.tau / lig.material.tau_adm * 100, 4)} %")

    # ---- 7. Esforços na viga --------------------------------------------------------
    add("titulo", "7. ESFORÇOS INTERNOS NA VIGA AC")
    add("texto", "Forças verticais na viga (+ para cima):  −P em xP,  F_A em xB,  F_B em xC.")
    add("texto", "Como todas são verticais, N(x) = 0 em toda a viga.")
    add("texto", "V(x) = soma das forças à esquerda de x;  M(x) = soma de F·(x − x_força).")
    forcas = [(xP, -P), (xB, FA), (xC, FB)]
    pontos = sorted({round(v, 12) for v in (0.0, xP, xB, xC, L)})
    for x in pontos:
        v_antes = sum(f for xi, f in forcas if xi < x - TOL)
        v_depois = sum(f for xi, f in forcas if xi <= x + TOL)
        m = sum(f * (x - xi) for xi, f in forcas if xi < x - TOL)
        add("eq", f"x = {_g(x)} m:  V(x⁻) = {_g(v_antes)} N,  V(x⁺) = {_g(v_depois)} N,  "
                  f"M = {_g(m)} N·m")
    add("res", f"|V|máx = {_g(abs(r.V_max))} N (em x = {_g(r.x_V_max)} m)   |   "
               f"|M|máx = {_g(abs(r.M_max))} N·m (em x = {_g(r.x_M_max)} m)")
    s = d.secao_viga
    add("subtitulo", "Tensão de flexão:  σ = |M|·c / I")
    if s.forma == "Retangular":
        add("eq", f"I = b·h³/12 = {_g(s.b)}·({_g(s.h)})³/12 = {_g(s.inercia)} m⁴;   "
                  f"c = h/2 = {_g(s.y_max)} m")
    else:
        add("eq", f"I = π·d⁴/64 = π·({_g(s.d)})⁴/64 = {_g(s.inercia)} m⁴;   c = d/2 = {_g(s.y_max)} m")
    add("eq", f"σ_máx = {_g(abs(r.M_max))}·{_g(s.y_max)} / {_g(s.inercia)} = "
              f"{_g(r.sigma_flex_max)} Pa = {_g(r.sigma_flex_max / 1e6)} MPa")

    # ---- 8. Deformação (viga rígida) -------------------------------------------------
    add("titulo", "8. DEFORMAÇÃO COM VIGA RÍGIDA (hipótese do professor)")
    add("texto", "A viga não flete: só desloca e gira. As barras deslocam B e C; os outros "
                 "pontos saem por semelhança de triângulos.")
    add("eq", f"v_B = −δ_A = {_g(r.desloc_B * 1000)} mm   (D fixo em cima: se BD alonga, B desce)")
    add("eq", f"v_C = +δ_B = {_g(r.desloc_C * 1000)} mm   (E fixo embaixo: se CE alonga, C sobe)")
    add("eq", f"θ = (v_C − v_B)/(xC − xB) = ({_g(r.desloc_C)} − {_p(r.desloc_B)})"
              f"/({_g(xC)} − {_g(xB)}) = {_g(r.rotacao * 1000)} mrad")
    add("eq", "v(x) = v_B + θ·(x − xB)")
    add("eq", f"v_A = v_B + θ·(0 − xB) = {_g(r.desloc_A * 1000)} mm")
    if abs(xP) > TOL:
        add("eq", f"v_P = v_B + θ·(xP − xB) = {_g(r.desloc_P * 1000)} mm")
    add("res", f"δ_A = {_g(r.desloc_A * 1000)} mm ({_sentido(r.desloc_A, 'sobe', 'desce')})   |   "
               f"δ_B = {_g(r.desloc_B * 1000)} mm ({_sentido(r.desloc_B, 'sobe', 'desce')})   |   "
               f"δ_C = {_g(r.desloc_C * 1000)} mm ({_sentido(r.desloc_C, 'sobe', 'desce')})")
    add("texto", f"Flexão ignorada (viga flexível − rígida): até {_g(r.flexao_extra_max * 1000)} mm.")

    # ---- 9. Flambagem -----------------------------------------------------------------
    add("titulo", "9. FLAMBAGEM DAS BARRAS COMPRIMIDAS")
    add("texto", "Só barras comprimidas flambam. Hipótese: articuladas nas duas pontas (K = 1).")
    for nome, barra, comp in (("A", bA, d.LA), ("B", bB, d.LB)):
        add("subtitulo", f"Barra {nome}")
        fl = barra.flambagem
        if fl is None:
            add("texto", "  Não está comprimida: não há flambagem.")
            continue
        mat = barra.material
        add("eq", f"L_e = K·L = 1·{_g(comp)} = {_g(fl.comprimento_efetivo)} m")
        add("eq", f"I_min = {_g(fl.inercia_min)} m⁴;   r = √(I_min/A) = {_g(fl.raio_giracao)} m")
        add("eq", f"λ = L_e/r = {_g(fl.comprimento_efetivo)}/{_g(fl.raio_giracao)} = {_g(fl.esbeltez, 5)}")
        if fl.esbeltez_limite is not None:
            add("eq", f"λ_c = π·√(2E/σ_esc) = {_g(fl.esbeltez_limite, 5)}")
            if fl.regime == "Euler":
                add("texto", "  λ ≥ λ_c  →  coluna esbelta: vale a fórmula de Euler.")
            else:
                add("texto", "  λ < λ_c  →  coluna intermediária: usa a parábola de Johnson.")
        else:
            add("aviso", "  σ_esc não informado: usando Euler sem verificar a validade.")
        if fl.regime == "Euler":
            add("eq", f"σ_cr = π²·E/λ² = {_g(fl.tensao_critica)} Pa = {_g(fl.tensao_critica / 1e6)} MPa")
        else:
            add("eq", "σ_cr = σ_esc·[1 − σ_esc·λ²/(4·π²·E)] = "
                      f"{_g(fl.tensao_critica)} Pa = {_g(fl.tensao_critica / 1e6)} MPa")
        add("eq", f"P_cr = σ_cr·A = {_g(fl.carga_critica)} N;   FS = P_cr/|N| = "
                  f"{_g(fl.carga_critica)}/{_g(fl.carga_aplicada)} = {_g(fl.fs, 4)}")

    # ---- 10. Verificações ----------------------------------------------------------------
    add("titulo", "10. COEFICIENTES DE SEGURANÇA  (FS = limite / valor atuante)")
    add("texto", "FS ≥ 1,5 → SEGURO   |   1,0 ≤ FS < 1,5 → ATENÇÃO   |   FS < 1,0 → FALHA")
    for v in r.verificacoes:
        un = "MPa" if v.grandeza == "tensao" else u_F
        fator = 1e-6 if v.grandeza == "tensao" else kF
        if v.limite is None:
            add("aviso", f"{v.titulo}: sem {v.simbolo_limite} informado — sem verificação.")
            continue
        valor = _g(v.valor * fator)
        limite = _g(v.limite * fator)
        status = {"ok": "SEGURO", "atencao": "ATENÇÃO", "falha": v.rotulo_falha}[v.nivel]
        add("eq", f"{v.titulo}: {v.simbolo_valor} = {valor} {un}, {v.simbolo_limite} = {limite} {un}"
                  f"  →  FS = {_g(v.fs, 4)}  ({_g(v.utilizacao * 100, 4)} % do limite)  →  {status}")
    return blocos


def texto_plano(blocos) -> str:
    """Junta os blocos num texto só (para salvar em .txt)."""
    linhas = ["MEMÓRIA DE CÁLCULO — A3 RESMAT I", ""]
    for tipo, texto in blocos:
        if tipo == "titulo":
            linhas += ["", texto, "=" * len(texto)]
        elif tipo == "subtitulo":
            linhas += ["", texto]
        elif tipo == "eq":
            linhas.append("    " + texto)
        elif tipo == "res":
            linhas.append("  >> " + texto)
        elif tipo == "aviso":
            linhas.append("  ! " + texto.strip())
        else:
            linhas.append(texto)
    return "\n".join(linhas) + "\n"

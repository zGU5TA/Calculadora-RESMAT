# ==============================================================================
# EXPORTAÇÃO: tabelas e arquivos de texto/CSV (sem tkinter)
#
# Os CSV usam ";" como separador e vírgula decimal, com acentos (UTF-8 com BOM):
# é o formato que o Excel em português abre direto, com um clique duplo.
# ==============================================================================
import csv
import math

from calculadora.calculo.dados import UNIDADE_TENSAO, UNITS
from calculadora.calculo.modelos import DadosEntrada, Resultados


def tabela_resultados(d: DadosEntrada, r: Resultados, unidades) -> list:
    """Linhas (seção, grandeza, valor, unidade). Valor é número ou texto."""
    u_F, u_L = unidades
    kF = 1.0 / UNITS["force"][u_F]
    kL = 1.0 / UNITS["pos"][u_L]
    kS = 1.0 / UNITS["stress"][UNIDADE_TENSAO]
    uS = UNIDADE_TENSAO
    t = []

    def add(secao, nome, valor, unidade=""):
        t.append((secao, nome, valor, unidade))

    s = "Equilíbrio"
    add(s, "Carga P", d.P * kF, u_F)
    add(s, "Força da barra A na viga (F_A, + para cima)", r.FA * kF, u_F)
    add(s, "Força da barra B na viga (F_B, + para cima)", r.FB * kF, u_F)
    add(s, "Reação no apoio D", abs(r.barraA.forca_normal) * kF, u_F)
    add(s, "Reação no apoio E", abs(r.barraB.forca_normal) * kF, u_F)

    for barra, nome, comp in ((r.barraA, "Barra A (BD)", d.LA), (r.barraB, "Barra B (CE)", d.LB)):
        add(nome, "Material", barra.material.nome)
        add(nome, "Esforço normal N (+ tração)", barra.forca_normal * kF, u_F)
        add(nome, "Estado", barra.estado)
        add(nome, "Tensão normal σ", barra.tensao * kS, uS)
        add(nome, "Variação de comprimento δ", barra.alongamento * 1000, "mm")
        if barra.flambagem is not None:
            fl = barra.flambagem
            add(nome, "Esbeltez λ", fl.esbeltez)
            add(nome, "Regime de flambagem", fl.regime)
            add(nome, "Tensão crítica σ_cr", fl.tensao_critica * kS, uS)
            add(nome, "Carga crítica P_cr", fl.carga_critica * kF, u_F)

    for pino, nome in ((r.pinoB, "Pino/rebite B"), (r.pinoC, "Pino/rebite C")):
        add(nome, "Quantidade de pinos", pino.n_pinos)
        add(nome, "Planos de cisalhamento", pino.n_planos)
        add(nome, "Força transmitida", pino.forca * kF, u_F)
        add(nome, "Tensão de cisalhamento τ", pino.tau * kS, uS)

    s = "Viga AC"
    add(s, "Material", d.mat_viga.nome)
    add(s, "Esforço normal N(x)", 0.0, u_F)
    add(s, "Cortante máximo |V|", abs(r.V_max) * kF, u_F)
    add(s, "Posição do cortante máximo", r.x_V_max * kL, u_L)
    add(s, "Momento fletor máximo |M|", abs(r.M_max) * kF * kL, f"{u_F}·{u_L}")
    add(s, "Posição do momento máximo", r.x_M_max * kL, u_L)
    add(s, "Tensão de flexão máxima σ", r.sigma_flex_max * kS, uS)
    add(s, "Posição da tensão máxima", r.x_sigma_flex_max * kL, u_L)

    s = "Deformação (viga rígida)"
    add(s, "δ_A (x = 0, + sobe)", r.desloc_A * 1000, "mm")
    add(s, "δ_B", r.desloc_B * 1000, "mm")
    add(s, "δ_C", r.desloc_C * 1000, "mm")
    add(s, "δ sob a carga P", r.desloc_P * 1000, "mm")
    add(s, "Rotação da viga (+ anti-horário)", r.rotacao * 1000, "mrad")
    add(s, "Flexão ignorada (máx.)", r.flexao_extra_max * 1000, "mm")

    s = "Coeficientes de segurança"
    for v in r.verificacoes:
        if v.fs is None:
            add(s, v.titulo, "sem limite informado")
            continue
        add(s, v.titulo + " — FS", v.fs)
        add(s, v.titulo + " — utilização", v.utilizacao * 100, "%")
        add(s, v.titulo + " — situação",
            {"ok": "SEGURO", "atencao": "ATENÇÃO", "falha": v.rotulo_falha}[v.nivel])
    return t


def tabela_diagramas(r: Resultados, unidades):
    """(cabeçalho, linhas) com os diagramas ponto a ponto ao longo da viga."""
    u_F, u_L = unidades
    kF = 1.0 / UNITS["force"][u_F]
    kL = 1.0 / UNITS["pos"][u_L]
    kS = 1.0 / UNITS["stress"][UNIDADE_TENSAO]
    cab = [f"x ({u_L})", f"N ({u_F})", f"V ({u_F})", f"M ({u_F}·{u_L})",
           f"σ flexão ({UNIDADE_TENSAO})", "δ viga rígida (mm)", "δ viga flexível (mm)"]
    linhas = [(r.x[i] * kL, r.N[i] * kF, r.V[i] * kF, r.M[i] * kF * kL,
               r.sigma_flex[i] * kS, r.deflexao_rigida[i] * 1000, r.deflexao[i] * 1000)
              for i in range(len(r.x))]
    return cab, linhas


def _celula(v):
    """Número com vírgula decimal (Excel pt-BR); texto fica como está."""
    if isinstance(v, bool):
        return str(v)
    if isinstance(v, int):
        return str(v)
    if isinstance(v, float):
        if math.isinf(v):
            return "∞"
        return f"{v:.8g}".replace(".", ",")
    return "" if v is None else str(v)


def salvar_csv(caminho, cabecalho, linhas):
    with open(caminho, "w", newline="", encoding="utf-8-sig") as f:
        escritor = csv.writer(f, delimiter=";")
        escritor.writerow(cabecalho)
        for linha in linhas:
            escritor.writerow([_celula(v) for v in linha])


def salvar_csv_resultados(caminho, d, r, unidades):
    salvar_csv(caminho, ["Seção", "Grandeza", "Valor", "Unidade"],
               tabela_resultados(d, r, unidades))


def salvar_csv_diagramas(caminho, r, unidades):
    cab, linhas = tabela_diagramas(r, unidades)
    salvar_csv(caminho, cab, linhas)


def salvar_texto(caminho, texto):
    with open(caminho, "w", encoding="utf-8") as f:
        f.write(texto)

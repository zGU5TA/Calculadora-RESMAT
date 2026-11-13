# ==============================================================================
# GRÁFICOS: DEN, DEC, DMF, tensão de flexão e deformação (viga rígida) (matplotlib)
# ==============================================================================
import tkinter as tk

import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from calculadora.calculo.dados import UNIDADE_TENSAO, UNITS
from calculadora.interface.tema import CORES


def criar_figura():
    """Figura com 5 gráficos empilhados (mesmo eixo x)."""
    try:
        fig = Figure(figsize=(7, 10), facecolor=CORES["painel"], layout="constrained")
    except TypeError:   # matplotlib antigo (< 3.5)
        fig = Figure(figsize=(7, 10), facecolor=CORES["painel"])
        fig.set_tight_layout(True)
    axes = fig.subplots(5, 1, sharex=True)
    return fig, axes


def desenhar_diagramas(axes, d, r, unidades):
    """Desenha os 5 diagramas. Não depende do tkinter (dá para testar sozinho)."""
    u_F, u_L = unidades
    kF = 1.0 / UNITS["force"][u_F]
    kL = 1.0 / UNITS["pos"][u_L]
    kS = 1.0 / UNITS["stress"][UNIDADE_TENSAO]
    x = r.x * kL

    for ax in axes:
        ax.clear()
        ax.set_facecolor(CORES["fundo"])
        ax.tick_params(colors=CORES["texto"], labelsize=8)
        ax.grid(True, linestyle="--", alpha=0.3)
        ax.axhline(0, color=CORES["cinza"], linewidth=0.8)
        for spine in ax.spines.values():
            spine.set_color(CORES["separador"])
        # Linhas verticais finas nas barras (B e C) e na carga (P)
        for x_m in (d.xB, d.xC):
            ax.axvline(x_m * kL, color=CORES["cinza"], linewidth=0.8, linestyle=":", alpha=0.6)
        ax.axvline(d.xP * kL, color=CORES["vermelho"], linewidth=0.8, linestyle=":", alpha=0.6)

    def titulo(ax, texto, espaco=6):
        ax.set_title(texto, color=CORES["texto"], fontsize=9, fontweight="bold", pad=espaco)

    def eixo_y(ax, texto):
        ax.set_ylabel(texto, fontsize=8, color=CORES["texto"])

    # Letras B, C e P no topo do primeiro gráfico
    ax0 = axes[0]
    letras = {}
    for x_m, letra, cor in ((d.xB, "B", CORES["laranja"]), (d.xC, "C", CORES["verde"]),
                            (d.xP, "P", CORES["vermelho"])):
        texto, cor0 = letras.get(round(x_m, 12), ("", cor))
        letras[round(x_m, 12)] = (f"{texto}={letra}" if texto else letra, cor0)
    for x_m, (letra, cor) in letras.items():
        ax0.annotate(letra, (x_m * kL, 1.0), xycoords=("data", "axes fraction"),
                     xytext=(0, 2), textcoords="offset points", ha="center", va="bottom",
                     color=cor, fontsize=8, fontweight="bold")

    # 1) DEN: esforço normal (a viga só recebe forças verticais, então N(x) = 0)
    N = r.N * kF
    axes[0].plot(x, N, color=CORES["amarelo"], linewidth=2)
    axes[0].set_ylim(-1, 1)
    axes[0].annotate("N(x) = 0  (sem força axial na viga: todas as forças são verticais)",
                     (0.5, 0.5), xycoords="axes fraction", ha="center", va="bottom",
                     xytext=(0, 6), textcoords="offset points",
                     color=CORES["texto_suave"], fontsize=8)
    eixo_y(axes[0], f"N ({u_F})")
    titulo(axes[0], "Diagrama de Esforço Normal (DEN)", espaco=16)   # espaço p/ letras

    # 2) DEC
    V = r.V * kF
    axes[1].plot(x, V, color=CORES["azul"], linewidth=2)
    axes[1].fill_between(x, V, color=CORES["azul"], alpha=0.2)
    eixo_y(axes[1], f"V ({u_F})")
    titulo(axes[1], "Diagrama de Esforço Cortante (DEC)")

    # 3) DMF
    M = r.M * kF * kL
    axes[2].plot(x, M, color=CORES["laranja"], linewidth=2)
    axes[2].fill_between(x, M, color=CORES["laranja"], alpha=0.2)
    eixo_y(axes[2], f"M ({u_F}·{u_L})")
    titulo(axes[2], "Diagrama de Momento Fletor (DMF)")

    # 4) Tensão de flexão
    S = r.sigma_flex * kS
    axes[3].plot(x, S, color=CORES["verde"], linewidth=2)
    axes[3].fill_between(x, S, color=CORES["verde"], alpha=0.2)
    eixo_y(axes[3], f"σ ({UNIDADE_TENSAO})")
    titulo(axes[3], "Tensão de Flexão Máxima")

    # 5) Deformação com VIGA RÍGIDA (sempre em mm), como no desenho do professor:
    #    as barras deslocam B e C; a viga é uma reta que passa por B' e C'.
    ax = axes[4]
    v = r.deflexao_rigida * 1000
    ax.plot(x, np.zeros_like(x), color=CORES["texto_suave"], linewidth=1.4,
            linestyle=(0, (5, 4)), label="Posição original")
    ax.plot(x, v, color=CORES["vermelho"], linewidth=2.2, label="Viga deformada (rígida)")

    # Cotas: δ de cada ponto, medido na vertical a partir da posição original
    pontos = [("A", 0.0, r.desloc_A, CORES["vermelho"]),
              ("B", d.xB, r.desloc_B, CORES["laranja"]),
              ("C", d.xC, r.desloc_C, CORES["verde"])]
    if all(abs(d.xP - xp) > 1e-9 for _, xp, _, _ in pontos):
        pontos.append(("P", d.xP, r.desloc_P, CORES["azul"]))
    pico = max(abs(dv) * 1000 for _, _, dv, _ in pontos) or 1e-3
    for nome, xp, dv, cor in pontos:
        dv_mm = dv * 1000
        ax.plot([xp * kL], [dv_mm], "o", color=cor, markersize=6, zorder=5)
        if abs(dv_mm) > 1e-9 * max(pico, 1.0):
            ax.annotate("", (xp * kL, dv_mm), (xp * kL, 0.0),
                        arrowprops=dict(arrowstyle="<->", color=cor, linewidth=1.2,
                                        shrinkA=0, shrinkB=0))
        sentido = "↑" if dv_mm > 0 else ("↓" if dv_mm < 0 else "")
        ax.annotate(f"δ{nome} = {dv_mm:+.3f} mm {sentido}", (xp * kL, dv_mm),
                    xytext=(6, 8 if dv_mm >= 0 else -14), textcoords="offset points",
                    ha="left" if xp * kL < 0.7 * x[-1] else "right",
                    color=cor, fontsize=8, fontweight="bold")

    # Eixo y sempre incluindo o zero (posição original da viga) e folga para os textos
    todos = np.concatenate([v, [0.0]])
    lo, hi = float(todos.min()), float(todos.max())
    folga = max((hi - lo) * 0.25, 1e-3)
    ax.set_ylim(lo - folga, hi + folga)
    ax.legend(loc="best", fontsize=7, facecolor=CORES["painel"], edgecolor=CORES["separador"],
              labelcolor=CORES["texto"])

    eixo_y(ax, "δ (mm)  + sobe / − desce")
    ax.set_xlabel(f"Posição x ({u_L})", fontsize=8, color=CORES["texto"])
    titulo(ax, "Deformação da Viga (viga rígida: δB e δC vêm do alongamento das barras)")

    axes[-1].set_xlim(x[0], x[-1])


class GraficosDEIS:
    """Aba com os gráficos, dentro da janela tkinter."""

    def __init__(self, parent):
        self.fig, self.axes = criar_figura()
        self.canvas = FigureCanvasTkAgg(self.fig, master=parent)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def atualizar(self, d, r, unidades):
        desenhar_diagramas(self.axes, d, r, unidades)
        self.canvas.draw_idle()

    def limpar(self):
        for ax in self.axes:
            ax.clear()
            ax.set_facecolor(CORES["fundo"])
        self.canvas.draw_idle()

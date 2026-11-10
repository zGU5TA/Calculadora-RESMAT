# ==============================================================================
# GRÁFICOS: DEC, DMF, tensão de flexão e linha elástica (matplotlib)
# ==============================================================================
import tkinter as tk

import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from dados import CORES, UNIDADE_TENSAO, UNITS


def criar_figura():
    """Figura com 4 gráficos empilhados (mesmo eixo x)."""
    try:
        fig = Figure(figsize=(7, 9), facecolor=CORES["painel"], layout="constrained")
    except TypeError:   # matplotlib antigo (< 3.5)
        fig = Figure(figsize=(7, 9), facecolor=CORES["painel"])
        fig.set_tight_layout(True)
    axes = fig.subplots(4, 1, sharex=True)
    return fig, axes


def desenhar_diagramas(axes, d, r, unidades):
    """Desenha os 4 diagramas. Não depende do tkinter (dá para testar sozinho)."""
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

    # 1) DEC
    V = r.V * kF
    axes[0].plot(x, V, color=CORES["azul"], linewidth=2)
    axes[0].fill_between(x, V, color=CORES["azul"], alpha=0.2)
    eixo_y(axes[0], f"V ({u_F})")
    titulo(axes[0], "Diagrama de Esforço Cortante (DEC)", espaco=16)   # espaço p/ letras

    # 2) DMF
    M = r.M * kF * kL
    axes[1].plot(x, M, color=CORES["laranja"], linewidth=2)
    axes[1].fill_between(x, M, color=CORES["laranja"], alpha=0.2)
    eixo_y(axes[1], f"M ({u_F}·{u_L})")
    titulo(axes[1], "Diagrama de Momento Fletor (DMF)")

    # 3) Tensão de flexão
    S = r.sigma_flex * kS
    axes[2].plot(x, S, color=CORES["verde"], linewidth=2)
    axes[2].fill_between(x, S, color=CORES["verde"], alpha=0.2)
    eixo_y(axes[2], f"σ ({UNIDADE_TENSAO})")
    titulo(axes[2], "Tensão de Flexão Máxima")

    # 4) Linha elástica (sempre em mm)
    ax = axes[3]
    v = r.deflexao * 1000
    ax.plot(x, v, color=CORES["vermelho"], linewidth=2)
    ax.fill_between(x, v, color=CORES["vermelho"], alpha=0.15)
    # Pontos B e C (onde as barras seguram a viga)
    ax.plot([d.xB * kL, d.xC * kL], [r.desloc_B * 1000, r.desloc_C * 1000], "o",
            color=CORES["amarelo"], markersize=5)

    # Flecha máxima marcada no gráfico
    x_max, v_max = r.x_deflexao_max * kL, r.deflexao_max * 1000
    ax.plot([x_max], [v_max], "o", color=CORES["vermelho"], markersize=5)
    perto_da_direita = x_max > 0.6 * x[-1]
    ax.annotate(f"δmáx = {v_max:.3f} mm", (x_max, v_max),
                xytext=(-8 if perto_da_direita else 8, -12 if v_max < 0 else 8),
                textcoords="offset points", ha="right" if perto_da_direita else "left",
                color=CORES["texto"], fontsize=8)

    # Eixo y sempre incluindo o zero (posição original da viga)
    todos = np.concatenate([v, [0.0]])
    lo, hi = float(todos.min()), float(todos.max())
    folga = max((hi - lo) * 0.15, 1e-3)
    ax.set_ylim(lo - folga, hi + folga)

    eixo_y(ax, "δ (mm)")
    ax.set_xlabel(f"Posição x ({u_L})", fontsize=8, color=CORES["texto"])
    titulo(ax, "Linha Elástica (Deformação da Viga)")

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
# ==============================================================================
# DIAGRAMAS (matplotlib puro, SEM tkinter): DEN, DEC, DMF, tensão, deformação,
# leitor de valores ao passar o mouse e desenho da estrutura deformada.
# Fica separado da janela para poder ser testado e exportado (PNG) sozinho.
# ==============================================================================
import numpy as np
from matplotlib.figure import Figure
from matplotlib.patches import Polygon

from calculadora.calculo.dados import UNIDADE_TENSAO, UNITS
from calculadora.interface.tema import CORES


def criar_figura():
    """Figura com 5 gráficos empilhados (mesmo eixo x).
    Margens fixas (subplots_adjust): o layout automático é bem mais lento."""
    fig = Figure(figsize=(7, 10), facecolor=CORES["painel"])
    axes = fig.subplots(5, 1, sharex=True)
    fig.subplots_adjust(left=0.11, right=0.97, top=0.965, bottom=0.05, hspace=0.62)
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


# ==============================================================================
# Leitor de valores: passe o mouse sobre qualquer diagrama
# ==============================================================================
class LeitorCursor:
    """Linha vertical que acompanha o mouse nos 5 gráficos + caixa com os valores."""

    def __init__(self, fig, axes):
        self.fig, self.axes = fig, list(axes)
        self.x = self.series = self.rotulos = None
        self.linhas, self.caixa = [], None
        self._cid = None
        self._fundo = None          # imagem do gráfico sem o cursor (para blit)

    def definir(self, x, series, rotulos):
        """x: posições (já na unidade de exibição). series/rotulos: um por gráfico."""
        self.x, self.series, self.rotulos = np.asarray(x), series, rotulos
        # clear() dos eixos remove os artistas antigos; recria
        self.linhas = [ax.axvline(self.x[0], color=CORES["amarelo"], linewidth=1,
                                  alpha=0.9, visible=False, animated=True) for ax in self.axes]
        self.caixa = self.axes[0].annotate(
            "", (0, 1), xycoords="axes fraction", xytext=(8, -8), textcoords="offset points",
            va="top", ha="left", fontsize=8, color=CORES["texto"], visible=False, zorder=20, animated=True,
            bbox=dict(boxstyle="round,pad=0.4", fc=CORES["painel"], ec=CORES["amarelo"], alpha=0.95))

    def ligar(self):
        if self._cid is None:
            self._cid = self.fig.canvas.mpl_connect("motion_notify_event", self._mover)
            self.fig.canvas.mpl_connect("figure_leave_event", lambda e: self.esconder(True))
            self.fig.canvas.mpl_connect("draw_event", self._guardar_fundo)

    def _guardar_fundo(self, _ev=None):
        try:
            self._fundo = self.fig.canvas.copy_from_bbox(self.fig.bbox)
        except Exception:
            self._fundo = None

    def _mostrar_rapido(self):
        """Redesenha só o cursor (blit) em vez de refazer os 5 gráficos."""
        c = self.fig.canvas
        if self.caixa is None:
            return
        if self._fundo is None:
            return c.draw_idle()
        c.restore_region(self._fundo)
        for ln, ax in zip(self.linhas, self.axes):
            if ln.get_visible():
                ax.draw_artist(ln)
        if self.caixa.get_visible():
            self.axes[0].draw_artist(self.caixa)
        c.blit(self.fig.bbox)

    def texto_em(self, x_cursor):
        """Texto com os valores no ponto mais próximo de x_cursor (testável sem mouse)."""
        i = int(np.argmin(np.abs(self.x - x_cursor)))
        linhas = [f"x = {self.x[i]:.4g} {self.rotulos['x']}"]
        for nome, (valores, unid) in self.series.items():
            linhas.append(f"{nome} = {valores[i]:+.4g} {unid}")
        return i, "\n".join(linhas)

    def _mover(self, ev):
        if self.x is None or ev.inaxes not in self.axes or ev.xdata is None:
            return self.esconder(True)
        i, texto = self.texto_em(ev.xdata)
        for ln in self.linhas:
            ln.set_xdata([self.x[i], self.x[i]])
            ln.set_visible(True)
        self.caixa.set_text(texto)
        self.caixa.set_visible(True)
        self._mostrar_rapido()

    def esconder(self, redesenhar=False):
        for ln in self.linhas:
            ln.set_visible(False)
        if self.caixa is not None:
            self.caixa.set_visible(False)
        if redesenhar:
            self._mostrar_rapido()


def series_do_cursor(d, r, unidades):
    """Valores que o leitor mostra (mesmas unidades dos gráficos)."""
    u_F, u_L = unidades
    kF = 1.0 / UNITS["force"][u_F]
    kL = 1.0 / UNITS["pos"][u_L]
    kS = 1.0 / UNITS["stress"][UNIDADE_TENSAO]
    series = {"N": (r.N * kF, u_F), "V": (r.V * kF, u_F), "M": (r.M * kF * kL, f"{u_F}·{u_L}"),
              "σ": (r.sigma_flex * kS, UNIDADE_TENSAO), "δ": (r.deflexao_rigida * 1000, "mm")}
    return r.x * kL, series, {"x": u_L}


def nova_figura_diagramas():
    """Figura dos diagramas já com o leitor de cursor. Retorna (fig, axes, leitor)."""
    fig, axes = criar_figura()
    return fig, axes, LeitorCursor(fig, axes)


def desenhar_com_cursor(fig, axes, leitor, d, r, unidades):
    desenhar_diagramas(axes, d, r, unidades)
    x, series, rot = series_do_cursor(d, r, unidades)
    leitor.definir(x, series, rot)


# ==============================================================================
# Estrutura deformada com fator de ampliação
# ==============================================================================
def fator_automatico(d, r):
    """Fator que deixa o maior deslocamento com ~8 % do comprimento da viga."""
    pico = max(abs(r.desloc_A), abs(r.desloc_B), abs(r.desloc_C), 1e-12)
    return max(1.0, round(0.08 * d.L / pico, -1) or 1.0)


def criar_figura_deformada():
    fig = Figure(figsize=(8, 5), facecolor=CORES["painel"])
    ax = fig.add_subplot(111)
    fig.subplots_adjust(left=0.03, right=0.98, top=0.92, bottom=0.1)
    return fig, ax


def desenhar_deformada(ax, d, r, unidades, fator):
    """Desenha a viga e as barras antes (tracejado) e depois (cheio) da deformação."""
    u_L = unidades[1]
    kL = 1.0 / UNITS["pos"][u_L]
    ax.clear()
    ax.set_facecolor(CORES["fundo_escuro"])
    for s in ax.spines.values():
        s.set_color(CORES["separador"])
    ax.tick_params(colors=CORES["texto"], labelsize=8)
    ax.grid(True, linestyle=":", alpha=0.25)

    L = d.L
    esp = 0.05 * L                  # espessura desenhada da viga (esquemática)
    alt = 0.22 * L                  # comprimento desenhado das barras (esquemático)

    def v(x):                       # deslocamento vertical da viga, ampliado
        return np.interp(x, r.x, r.deflexao_rigida) * fator

    def viga(y_func, **kw):
        xs = np.linspace(0, L, 40)
        topo = [(x * kL, (y_func(x) + esp / 2) * kL) for x in xs]
        base = [(x * kL, (y_func(x) - esp / 2) * kL) for x in xs[::-1]]
        ax.add_patch(Polygon(topo + base, closed=True, **kw))

    # Posição original (fantasma)
    viga(lambda x: 0.0, fc="none", ec=CORES["cinza"], linestyle="--", linewidth=1, zorder=2)
    for xb, sinal in ((d.xB, 1), (d.xC, -1)):
        ax.plot([xb * kL] * 2, [0, sinal * alt * kL], color=CORES["cinza"], linestyle="--",
                linewidth=1, zorder=1)
    # Deformada
    viga(v, fc=CORES["azul"], ec=CORES["texto"], alpha=0.85, linewidth=1.2, zorder=4)
    ax.plot([d.xB * kL] * 2, [alt * kL, v(d.xB) * kL], color=CORES["laranja"], linewidth=4,
            solid_capstyle="round", zorder=5)
    ax.plot([d.xC * kL] * 2, [-alt * kL, v(d.xC) * kL], color=CORES["verde"], linewidth=4,
            solid_capstyle="round", zorder=5)
    # Pinos e apoios fixos D (em cima) e E (embaixo)
    for xb, yb, nome, cor in ((d.xB, v(d.xB), "B", CORES["laranja"]),
                              (d.xC, v(d.xC), "C", CORES["verde"])):
        ax.plot([xb * kL], [yb * kL], "o", color=cor, markeredgecolor="white", markersize=8, zorder=6)
        ax.annotate(nome, (xb * kL, yb * kL), xytext=(8, 8), textcoords="offset points",
                    color=cor, fontweight="bold", fontsize=9)
    for xb, y, nome in ((d.xB, alt, "D"), (d.xC, -alt, "E")):
        ax.plot([xb * kL], [y * kL], "s", color=CORES["cinza"], markersize=9, zorder=6)
        ax.annotate(nome + " (fixo)", (xb * kL, y * kL), xytext=(8, 6 if y > 0 else -14),
                    textcoords="offset points", color=CORES["cinza"], fontsize=8)
    # Carga P
    yp = v(d.xP) + esp / 2
    ax.annotate("", (d.xP * kL, yp * kL), (d.xP * kL, (yp + 0.16 * L) * kL),
                arrowprops=dict(arrowstyle="-|>", color=CORES["vermelho"], linewidth=2.5), zorder=7)
    ax.annotate("P", (d.xP * kL, (yp + 0.16 * L) * kL), xytext=(0, 4), textcoords="offset points",
                ha="center", color=CORES["vermelho"], fontweight="bold")

    ax.set_aspect("equal", adjustable="box")
    ax.set_xlim(-0.06 * L * kL, 1.06 * L * kL)
    ax.set_ylim(-0.38 * L * kL, 0.42 * L * kL)
    ax.set_xlabel(f"x ({u_L})", fontsize=8, color=CORES["texto"])
    ax.set_yticks([])
    ax.set_title(f"Estrutura deformada — deslocamentos ampliados {fator:g}×  "
                 f"(δA={r.desloc_A*1000:+.3f}, δB={r.desloc_B*1000:+.3f}, δC={r.desloc_C*1000:+.3f} mm reais)",
                 color=CORES["texto"], fontsize=9, fontweight="bold")

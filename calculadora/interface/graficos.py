# ==============================================================================
# GRÁFICOS NA JANELA (tkinter): abas dos diagramas e da estrutura deformada
# O desenho em si está em diagramas.py (sem tkinter).
# ==============================================================================
import tkinter as tk
from tkinter import ttk

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from calculadora.interface import diagramas
from calculadora.interface.diagramas import desenhar_diagramas   # noqa: F401 (compatibilidade)
from calculadora.interface.tema import CORES


class GraficosDEIS:
    """Aba com DEN, DEC, DMF, tensão e deformação; mostra valores ao passar o mouse."""

    def __init__(self, parent):
        self.fig, self.axes, self.leitor = diagramas.nova_figura_diagramas()
        self.canvas = FigureCanvasTkAgg(self.fig, master=parent)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self.leitor.ligar()

    def atualizar(self, d, r, unidades):
        diagramas.desenhar_com_cursor(self.fig, self.axes, self.leitor, d, r, unidades)
        self.canvas.draw_idle()

    def limpar(self):
        for ax in self.axes:
            ax.clear()
            ax.set_facecolor(CORES["fundo"])
        self.leitor.x = None
        self.canvas.draw_idle()


class GraficoDeformada:
    """Aba com a estrutura deformada e um controle do fator de ampliação."""

    def __init__(self, parent):
        topo = tk.Frame(parent, bg=CORES["painel"])
        topo.pack(fill=tk.X, padx=8, pady=(6, 0))
        tk.Label(topo, text="Ampliação:", bg=CORES["painel"], fg=CORES["texto"],
                 font=("Helvetica", 9, "bold")).pack(side=tk.LEFT)
        self.fator = tk.DoubleVar(value=1.0)
        self.rotulo = tk.Label(topo, text="", width=9, bg=CORES["painel"], fg=CORES["amarelo"],
                               font=("Helvetica", 9, "bold"))
        self.escala = tk.Scale(topo, variable=self.fator, orient="horizontal", showvalue=False,
                               from_=1, to=1000, resolution=1, length=260,
                               bg=CORES["painel"], fg=CORES["texto"], troughcolor=CORES["campo"],
                               highlightthickness=0, command=lambda *_: self._redesenhar())
        self.escala.pack(side=tk.LEFT, padx=6)
        self.rotulo.pack(side=tk.LEFT)
        tk.Button(topo, text="Automático", bg=CORES["botao"], fg=CORES["texto"],
                  relief="flat", command=self.automatico).pack(side=tk.LEFT, padx=8)
        tk.Button(topo, text="1× (real)", bg=CORES["botao"], fg=CORES["texto"],
                  relief="flat", command=lambda: self.fator.set(1)).pack(side=tk.LEFT)
        self.fig, self.ax = diagramas.criar_figura_deformada()
        self.canvas = FigureCanvasTkAgg(self.fig, master=parent)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self._dados = None
        self._ajustar = True      # na 1ª vez, usa o fator automático

    def atualizar(self, d, r, unidades):
        self._dados = (d, r, unidades)
        auto = diagramas.fator_automatico(d, r)
        self.escala.config(to=max(10 * auto, 100))
        if self._ajustar:
            self.fator.set(auto)
            self._ajustar = False
        self._redesenhar()

    def automatico(self):
        if self._dados:
            self.fator.set(diagramas.fator_automatico(*self._dados[:2]))

    def _redesenhar(self):
        f = self.fator.get()
        self.rotulo.config(text=f"{f:g}×")
        if self._dados:
            d, r, u = self._dados
            diagramas.desenhar_deformada(self.ax, d, r, u, f)
            self.canvas.draw_idle()

    def limpar(self):
        self.ax.clear()
        self.canvas.draw_idle()

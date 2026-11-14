# ==============================================================================
# ABA "MEMÓRIA DE CÁLCULO": mostra o passo a passo gerado em calculo/memoria.py
# ==============================================================================
import tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk

from calculadora.calculo.memoria import gerar_memoria
from calculadora.interface.tema import CORES


class MemoriaView:

    def __init__(self, parent):
        mono = tkfont.nametofont("TkFixedFont").copy()
        mono.configure(size=10)
        negrito = mono.copy()
        negrito.configure(weight="bold")
        barra = ttk.Scrollbar(parent)
        barra.pack(side=tk.RIGHT, fill=tk.Y)
        self.texto = tk.Text(parent, bg=CORES["fundo"], fg=CORES["texto"], font=mono, wrap=tk.WORD,
                             yscrollcommand=barra.set, borderwidth=0, padx=14, pady=8,
                             state=tk.DISABLED)
        self.texto.pack(fill=tk.BOTH, expand=True)
        barra.config(command=self.texto.yview)
        t = self.texto
        t.tag_config("titulo", foreground=CORES["azul"], font=negrito, spacing1=14, spacing3=4)
        t.tag_config("subtitulo", foreground=CORES["amarelo"], font=negrito, spacing1=6)
        t.tag_config("texto", foreground=CORES["texto_suave"])
        t.tag_config("eq", foreground=CORES["texto"], lmargin1=24, lmargin2=24)
        t.tag_config("res", foreground=CORES["verde"], font=negrito, lmargin1=24, lmargin2=24)
        t.tag_config("aviso", foreground=CORES["laranja"])

    def mostrar(self, d, r, unidades):
        t = self.texto
        t.config(state=tk.NORMAL)
        t.delete("1.0", tk.END)
        for tipo, texto in gerar_memoria(d, r, unidades):
            t.insert(tk.END, texto + "\n", tipo)
        t.config(state=tk.DISABLED)

    def mostrar_erros(self, erros):
        t = self.texto
        t.config(state=tk.NORMAL)
        t.delete("1.0", tk.END)
        t.insert(tk.END, "Corrija os dados de entrada:\n" + "\n".join("• " + e for e in erros), "aviso")
        t.config(state=tk.DISABLED)

# ==============================================================================
# SAÍDAS: gera PNG/CSV/TXT dos resultados (sem tkinter, funciona em qualquer sistema)
# ==============================================================================
import os

from matplotlib.backends.backend_agg import FigureCanvasAgg

from calculadora.calculo import exportacao
from calculadora.calculo.memoria import gerar_memoria, texto_plano
from calculadora.interface import diagramas


def salvar_png_diagramas(caminho, d, r, unidades):
    fig, axes = diagramas.criar_figura()
    FigureCanvasAgg(fig)
    diagramas.desenhar_diagramas(axes, d, r, unidades)
    fig.savefig(caminho, dpi=150, facecolor=fig.get_facecolor())


def salvar_png_deformada(caminho, d, r, unidades, fator=None):
    fig, ax = diagramas.criar_figura_deformada()
    FigureCanvasAgg(fig)
    fator = fator or diagramas.fator_automatico(d, r)
    diagramas.desenhar_deformada(ax, d, r, unidades, fator)
    fig.savefig(caminho, dpi=150, facecolor=fig.get_facecolor())


def salvar_memoria(caminho, d, r, unidades):
    exportacao.salvar_texto(caminho, texto_plano(gerar_memoria(d, r, unidades)))


def exportar_tudo(pasta, d, r, unidades, fator=None):
    """Grava os 5 arquivos na pasta e devolve a lista de caminhos."""
    os.makedirs(pasta, exist_ok=True)
    j = lambda nome: os.path.join(pasta, nome)
    salvar_png_diagramas(j("diagramas_DEIS.png"), d, r, unidades)
    salvar_png_deformada(j("estrutura_deformada.png"), d, r, unidades, fator)
    exportacao.salvar_csv_resultados(j("resultados.csv"), d, r, unidades)
    exportacao.salvar_csv_diagramas(j("diagramas_pontos.csv"), r, unidades)
    salvar_memoria(j("memoria_de_calculo.txt"), d, r, unidades)
    return [j(n) for n in ("diagramas_DEIS.png", "estrutura_deformada.png", "resultados.csv",
                           "diagramas_pontos.csv", "memoria_de_calculo.txt")]

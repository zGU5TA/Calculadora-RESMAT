# ==============================================================================
# JANELA PRINCIPAL: monta a tela e liga as partes (entradas -> cálculo -> saídas)
# ==============================================================================
import tkinter as tk
from tkinter import simpledialog, ttk

from calculos import CalculadoraEstrutural
from dados import CORES
from esquema import EsquemaEstrutural
from graficos import GraficosDEIS
from painel_entradas import PainelEntradas
from painel_resultados import PainelResultados


class ResmatCalculatorApp(tk.Tk):
    ATRASO_RECALCULO_MS = 60   # espera o usuário parar de digitar para recalcular

    def __init__(self):
        super().__init__()
        self.title("A3 - Calculadora Estrutural Interativa | Resistência dos Materiais I")
        self.configure(bg=CORES["fundo"])
        self._maximizar()

        self.calculadora = CalculadoraEstrutural()
        self._recalculo_agendado = None

        self._montar_tela()
        self.agendar_recalculo()

    # --------------------------------------------------------------------------
    def _maximizar(self):
        self.geometry(f"{self.winfo_screenwidth()}x{self.winfo_screenheight()}")
        try:
            self.state("zoomed")                 # Windows
        except tk.TclError:
            try:
                self.attributes("-zoomed", True)  # Linux
            except tk.TclError:
                self.attributes("-fullscreen", True)

    def _montar_tela(self):
        cabecalho = tk.Frame(self, bg=CORES["painel"], height=50)
        cabecalho.pack(fill=tk.X, side=tk.TOP)
        tk.Label(cabecalho, text="A3 RESMAT I — CALCULADORA ESTRUTURAL INTERATIVA",
                 font=("Helvetica", 14, "bold"), fg=CORES["texto"], bg=CORES["painel"],
                 pady=10).pack()

        principal = tk.Frame(self, bg=CORES["fundo"])
        principal.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        esquerda = tk.Frame(principal, bg=CORES["painel"])
        esquerda.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
        direita = tk.Frame(principal, bg=CORES["painel"])
        direita.pack(side=tk.RIGHT, fill=tk.Y, padx=5, pady=5)
        centro = tk.Frame(principal, bg=CORES["fundo"])
        centro.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Coluna da esquerda: entradas
        self.entradas = PainelEntradas(esquerda, ao_mudar=self.agendar_recalculo)

        # Centro: abas com o esquema e os gráficos
        abas = ttk.Notebook(centro)
        abas.pack(fill=tk.BOTH, expand=True)
        aba_esquema = tk.Frame(abas, bg=CORES["painel"])
        abas.add(aba_esquema, text="📐 Esquema Estrutural (Clique Duplo P/ Editar P)")
        aba_deis = tk.Frame(abas, bg=CORES["painel"])
        abas.add(aba_deis, text="📊 DEIS e Deformação")
        abas.bind("<<NotebookTabChanged>>", lambda e: self.agendar_recalculo())

        self.esquema = EsquemaEstrutural(aba_esquema,
                                         ao_clicar_duas_vezes=self.editar_P,
                                         ao_redimensionar=self.agendar_recalculo)
        self.graficos = GraficosDEIS(aba_deis)

        # Coluna da direita: resultados
        self.resultados = PainelResultados(direita)

    # --------------------------------------------------------------------------
    def agendar_recalculo(self, *_):
        """Junta várias mudanças seguidas (digitação, redimensionar) em 1 cálculo."""
        if self._recalculo_agendado is not None:
            self.after_cancel(self._recalculo_agendado)
        self._recalculo_agendado = self.after(self.ATRASO_RECALCULO_MS, self.recalcular)

    def recalcular(self):
        self._recalculo_agendado = None
        dados = self.entradas.ler_dados()

        erros = self.calculadora.validar(dados)
        if not erros:
            try:
                resultados = self.calculadora.calcular(dados)
            except (ArithmeticError, ValueError) as err:
                erros = [f"Erro no cálculo: {err}"]

        if erros:
            self.esquema.mostrar_erros(erros)
            self.graficos.limpar()
            self.resultados.mostrar_erros(erros)
            return

        unidades = self.entradas.unidades_saida()
        self.esquema.desenhar(dados, resultados, unidades)
        self.graficos.atualizar(dados, resultados, unidades)
        self.resultados.mostrar(dados, resultados, unidades)

    def editar_P(self):
        novo = simpledialog.askfloat(
            "Editar Carga P", f"Digite o novo valor de P ({self.entradas.unidade('P')}):",
            initialvalue=self.entradas.valor("P"), parent=self)
        if novo is not None:
            self.entradas.definir_valor("P", novo)

# ==============================================================================
# JANELA PRINCIPAL: monta a tela e liga as partes (entradas -> cálculo -> saídas)
#
# Layout (pensado para telas pequenas, a partir do dashboard):
#   ┌ cabeçalho: ☰ Variáveis | título | 📋 Resultados | 💾 Exportar ┐
#   │ barra lateral   │  abas: Esquema · DEIS · Deformada · Memória  │ resultados │
# As duas colunas laterais podem ser recolhidas para dar espaço aos gráficos.
# ==============================================================================
import base64
import os
import tempfile
import tkinter as tk
import traceback
from tkinter import filedialog, messagebox, simpledialog, ttk

from calculadora.calculo import exportacao
from calculadora.calculo.calculos import CalculadoraEstrutural
from calculadora.interface import saidas
from calculadora.interface.esquema import EsquemaEstrutural
from calculadora.interface.graficos import GraficoDeformada, GraficosDEIS
from calculadora.interface.memoria_view import MemoriaView
from calculadora.interface.painel_entradas import PainelEntradas
from calculadora.interface.painel_resultados import PainelResultados
from calculadora.interface.tema import CORES

LARGURA_PARA_RESULTADOS_FIXOS = 1500   # abaixo disso o painel de resultados começa recolhido


class ResmatCalculatorApp(tk.Tk):
    ATRASO_RECALCULO_MS = 60   # espera o usuário parar de digitar para recalcular
    codigo_saida = 0           # 1 se o teste rápido falhar (usado na geração do .exe)

    def __init__(self):
        super().__init__()
        self.title("A3 - Calculadora Estrutural Interativa | Resistência dos Materiais I")
        self.configure(bg=CORES["fundo"])
        self._icone()
        self._estilo()
        self._maximizar()

        self.calculadora = CalculadoraEstrutural()
        self._recalculo_agendado = None
        self._ultimo = None          # (dados, resultados, unidades) do último cálculo válido

        self._montar_tela()
        self.agendar_recalculo()

        # Teste rápido usado pelo GitHub Actions: abre, calcula, desenha e fecha
        if os.environ.get("RESMAT_TESTE_RAPIDO"):
            self.after(1500, self._teste_rapido)

    # --------------------------------------------------------------------------
    def _icone(self):
        try:
            from calculadora.interface.icone_dados import ICONE_PNG_BASE64
            self._img_icone = tk.PhotoImage(data=base64.b64decode(ICONE_PNG_BASE64))
            self.iconphoto(True, self._img_icone)
        except Exception:   # ícone é enfeite: nunca pode impedir o programa de abrir
            pass

    def _estilo(self):
        st = ttk.Style(self)
        try:
            st.theme_use("clam")
        except tk.TclError:
            pass
        st.configure("TNotebook", background=CORES["fundo"], borderwidth=0)
        st.configure("TNotebook.Tab", background=CORES["painel"], foreground=CORES["cinza"],
                     padding=(14, 6), borderwidth=0, font=("Helvetica", 10, "bold"))
        st.map("TNotebook.Tab", background=[("selected", CORES["campo"])],
               foreground=[("selected", CORES["texto"])])
        st.configure("TCombobox", fieldbackground=CORES["campo"], background=CORES["botao"],
                     foreground=CORES["texto"], arrowcolor=CORES["texto"])
        st.configure("Vertical.TScrollbar", background=CORES["botao"], troughcolor=CORES["fundo"],
                     arrowcolor=CORES["texto"], borderwidth=0)

    def _maximizar(self):
        w, h = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"{min(w, 1280)}x{min(h - 60, 760)}+0+0")   # tamanho seguro se não maximizar
        try:
            self.state("zoomed")                  # Windows
        except tk.TclError:
            try:
                self.attributes("-zoomed", True)  # Linux
            except tk.TclError:
                self.geometry(f"{w}x{h - 80}+0+0")  # macOS: janela grande, sem tela cheia

    # --------------------------------------------------------------------------
    def _botao(self, parent, texto, comando, **kw):
        return tk.Button(parent, text=texto, command=comando, bg=CORES["botao"], fg=CORES["texto"],
                         activebackground=CORES["botao_ativo"], activeforeground=CORES["texto"],
                         relief="flat", font=("Helvetica", 10, "bold"), padx=10, pady=3, **kw)

    def _montar_tela(self):
        cab = tk.Frame(self, bg=CORES["painel"])
        cab.pack(fill=tk.X, side=tk.TOP)
        self._botao(cab, "☰ Variáveis", lambda: self._alternar("esq")).pack(side=tk.LEFT, padx=8, pady=6)
        tk.Label(cab, text="A3 RESMAT I — CALCULADORA ESTRUTURAL", font=("Helvetica", 12, "bold"),
                 fg=CORES["texto"], bg=CORES["painel"]).pack(side=tk.LEFT, padx=10)
        self._botao(cab, "📋 Resultados", lambda: self._alternar("dir")).pack(side=tk.RIGHT, padx=8)
        mb = tk.Menubutton(cab, text="💾 Exportar ▾", bg=CORES["botao"], fg=CORES["texto"],
                           activebackground=CORES["botao_ativo"], activeforeground=CORES["texto"],
                           relief="flat", font=("Helvetica", 10, "bold"), padx=10, pady=3)
        menu = tk.Menu(mb, tearoff=0, bg=CORES["painel"], fg=CORES["texto"],
                       activebackground=CORES["campo"], activeforeground=CORES["texto"])
        menu.add_command(label="Diagramas DEIS (PNG)…", command=lambda: self.exportar("deis"))
        menu.add_command(label="Estrutura deformada (PNG)…", command=lambda: self.exportar("def"))
        menu.add_command(label="Resultados (CSV para Excel)…", command=lambda: self.exportar("csv_res"))
        menu.add_command(label="Pontos dos diagramas (CSV)…", command=lambda: self.exportar("csv_diag"))
        menu.add_command(label="Memória de cálculo (TXT)…", command=lambda: self.exportar("txt"))
        menu.add_separator()
        menu.add_command(label="Tudo em uma pasta…", command=lambda: self.exportar("tudo"))
        mb.config(menu=menu)
        mb.pack(side=tk.RIGHT, padx=4)

        corpo = tk.Frame(self, bg=CORES["fundo"])
        corpo.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)
        self._corpo = corpo
        self._laterais = {}
        self.esq = tk.Frame(corpo, bg=CORES["painel"])
        self.dir = tk.Frame(corpo, bg=CORES["painel"])
        self.centro = tk.Frame(corpo, bg=CORES["fundo"])
        self._visivel = {"esq": True, "dir": self.winfo_screenwidth() >= LARGURA_PARA_RESULTADOS_FIXOS}
        self._empacotar()

        self.entradas = PainelEntradas(self.esq, ao_mudar=self.agendar_recalculo)

        self.abas = ttk.Notebook(self.centro)
        self.abas.pack(fill=tk.BOTH, expand=True)
        quadros = {}
        for chave, titulo in (("esq", "📐 Esquema"), ("deis", "📊 Diagramas"),
                              ("def", "〰 Deformada"), ("mem", "🧮 Memória de cálculo")):
            quadros[chave] = tk.Frame(self.abas, bg=CORES["painel"])
            self.abas.add(quadros[chave], text=titulo)
        self.abas.bind("<<NotebookTabChanged>>", lambda e: self.agendar_recalculo())

        self.esquema = EsquemaEstrutural(quadros["esq"], ao_clicar_duas_vezes=self.editar_P,
                                         ao_redimensionar=self.agendar_recalculo)
        self.graficos = GraficosDEIS(quadros["deis"])
        self.deformada = GraficoDeformada(quadros["def"])
        self.memoria = MemoriaView(quadros["mem"])
        self.resultados = PainelResultados(self.dir)

    def _empacotar(self):
        for f in (self.esq, self.dir, self.centro):
            f.pack_forget()
        if self._visivel["esq"]:
            self.esq.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 6))
        if self._visivel["dir"]:
            self.dir.pack(side=tk.RIGHT, fill=tk.Y, padx=(6, 0))
        self.centro.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    def _alternar(self, lado):
        self._visivel[lado] = not self._visivel[lado]
        self._empacotar()
        self.agendar_recalculo()

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
            self._ultimo = None
            self.esquema.mostrar_erros(erros)
            self.graficos.limpar()
            self.deformada.limpar()
            self.memoria.mostrar_erros(erros)
            self.resultados.mostrar_erros(erros)
            return

        unidades = self.entradas.unidades_saida()
        self._ultimo = (dados, resultados, unidades)
        self.esquema.desenhar(dados, resultados, unidades)
        self.graficos.atualizar(dados, resultados, unidades)
        self.deformada.atualizar(dados, resultados, unidades)
        self.memoria.mostrar(dados, resultados, unidades)
        self.resultados.mostrar(dados, resultados, unidades)

    # --------------------------------------------------------------------------
    def exportar(self, tipo):
        if self._ultimo is None:
            messagebox.showwarning("Exportar", "Corrija os dados de entrada antes de exportar.",
                                   parent=self)
            return
        d, r, u = self._ultimo
        fator = self.deformada.fator.get()
        png, csv, txt = ([("PNG", "*.png")], [("CSV", "*.csv")], [("Texto", "*.txt")])
        try:
            if tipo == "tudo":
                pasta = filedialog.askdirectory(title="Escolha a pasta de destino", parent=self)
                if not pasta:
                    return
                saidas.exportar_tudo(pasta, d, r, u, fator)
                messagebox.showinfo("Exportar", f"5 arquivos gravados em:\n{pasta}", parent=self)
                return
            nomes = {"deis": ("diagramas_DEIS.png", ".png", png),
                     "def": ("estrutura_deformada.png", ".png", png),
                     "csv_res": ("resultados.csv", ".csv", csv),
                     "csv_diag": ("diagramas_pontos.csv", ".csv", csv),
                     "txt": ("memoria_de_calculo.txt", ".txt", txt)}
            nome, ext, tipos = nomes[tipo]
            caminho = filedialog.asksaveasfilename(initialfile=nome, defaultextension=ext,
                                                   filetypes=tipos, parent=self)
            if not caminho:
                return
            {"deis": lambda: saidas.salvar_png_diagramas(caminho, d, r, u),
             "def": lambda: saidas.salvar_png_deformada(caminho, d, r, u, fator),
             "csv_res": lambda: exportacao.salvar_csv_resultados(caminho, d, r, u),
             "csv_diag": lambda: exportacao.salvar_csv_diagramas(caminho, r, u),
             "txt": lambda: saidas.salvar_memoria(caminho, d, r, u)}[tipo]()
            messagebox.showinfo("Exportar", f"Arquivo gravado:\n{caminho}", parent=self)
        except OSError as err:
            messagebox.showerror("Exportar", f"Não foi possível gravar o arquivo:\n{err}", parent=self)

    # --------------------------------------------------------------------------
    def _teste_rapido(self):
        try:
            self.recalcular()
            self.update()
            if self._ultimo is None:
                raise RuntimeError("os dados padrão não passaram na validação")
            capturas = os.environ.get("RESMAT_CAPTURAS")
            if capturas:   # diagnóstico: se travar, mostra onde
                import faulthandler
                faulthandler.dump_traceback_later(60, exit=True)
            for i, aba in enumerate(self.abas.tabs()):          # percorre todas as abas
                self.abas.select(aba)
                self.update()
                self.graficos.canvas.draw()
                self.deformada.canvas.draw()
                if capturas:
                    self._capturar(os.path.join(capturas, f"aba{i + 1}.png"))
            if capturas:                                         # com e sem resultados
                self._visivel["dir"] = True
                self._empacotar()
                self.abas.select(0)
                self.update()
                self._capturar(os.path.join(capturas, "com_resultados.png"))
            with tempfile.TemporaryDirectory() as pasta:         # exportação de ponta a ponta
                d, r, u = self._ultimo
                for arq in saidas.exportar_tudo(pasta, d, r, u, self.deformada.fator.get()):
                    if os.path.getsize(arq) < 500:
                        raise RuntimeError(f"arquivo exportado vazio: {arq}")
            mensagem = "OK"
        except Exception:
            self.codigo_saida = 1
            mensagem = traceback.format_exc()
        try:
            import faulthandler
            faulthandler.cancel_dump_traceback_later()
        except Exception:
            pass
        with open("resmat_teste.log", "w", encoding="utf-8") as arquivo:
            arquivo.write(mensagem + "\n")
        self.destroy()

    def _capturar(self, caminho):
        from PIL import ImageGrab   # só no teste; o Pillow vem junto do matplotlib
        os.makedirs(os.path.dirname(caminho), exist_ok=True)
        self.update()
        x, y = self.winfo_rootx(), self.winfo_rooty()
        ImageGrab.grab(bbox=(x, y, x + self.winfo_width(), y + self.winfo_height())).save(caminho)

    def editar_P(self):
        novo = simpledialog.askfloat(
            "Editar Carga P", f"Digite o novo valor de P ({self.entradas.unidade('P')}):",
            initialvalue=self.entradas.valor("P"), parent=self)
        if novo is not None:
            self.entradas.definir_valor("P", novo)

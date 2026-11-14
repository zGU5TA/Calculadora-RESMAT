# ==============================================================================
# PAINEL DE ENTRADAS (coluna da esquerda)
# ==============================================================================
import tkinter as tk
from tkinter import ttk

from calculadora.calculo.dados import MATERIALS_DB, PERSONALIZADO, UNITS
from calculadora.calculo.modelos import DadosEntrada, Ligacao, Material, Secao
from calculadora.interface.tema import CORES

FONTE = "Helvetica"
LARGURA_ROTULO = 22   # em caracteres (antes era 19 e cortava alguns textos)


def _ler_numero(texto):
    """Aceita '0.8' e também '0,8'. Lança ValueError se não for número."""
    return float(texto.strip().replace(",", "."))


class CampoNumerico:
    """Uma linha: rótulo + caixa de texto + botão de unidade.

    Cada campo guarda a SUA unidade; clicar no botão converte só este campo.
    """

    def __init__(self, parent, rotulo, valor, tipo_unidade, unidade, ao_mudar):
        self.tipo = tipo_unidade
        self.unidade = unidade
        self.valor = float(valor)
        self._ao_mudar = ao_mudar
        self._silencioso = False

        linha = tk.Frame(parent, bg=CORES["painel"])
        linha.pack(fill=tk.X, padx=8, pady=2)

        tk.Label(linha, text=rotulo, font=(FONTE, 9), fg=CORES["texto"], bg=CORES["painel"],
                 width=LARGURA_ROTULO, anchor="w").pack(side=tk.LEFT)

        self.var = tk.StringVar(value=self._formatar(self.valor))
        self.entry = tk.Entry(linha, textvariable=self.var, width=9, bg=CORES["campo"],
                              fg=CORES["texto"], insertbackground="white",
                              disabledbackground=CORES["fundo"],
                              disabledforeground=CORES["cinza"])
        self.entry.pack(side=tk.LEFT, padx=4)

        self.botao = tk.Button(linha, text=unidade, font=(FONTE, 8, "bold"), width=5,
                               bg=CORES["botao"], fg=CORES["verde"],
                               activebackground=CORES["botao_ativo"],
                               activeforeground=CORES["verde"],
                               command=self.trocar_unidade)
        self.botao.pack(side=tk.LEFT, padx=2)

        self.var.trace_add("write", self._digitou)

    # ---- valor -------------------------------------------------------------
    def si(self):
        """Valor convertido para o SI (N ou m)."""
        return self.valor * UNITS[self.tipo][self.unidade]

    def definir_valor(self, valor):
        self.valor = float(valor)
        self._mostrar(self.valor)
        self._ao_mudar()

    def trocar_unidade(self):
        unidades = list(UNITS[self.tipo])
        nova = unidades[(unidades.index(self.unidade) + 1) % len(unidades)]
        self.valor = self.si() / UNITS[self.tipo][nova]
        self.unidade = nova
        self._mostrar(self.valor)
        self.botao.config(text=nova)
        self._ao_mudar()

    def habilitar(self, sim):
        self.entry.config(state="normal" if sim else "disabled")

    # ---- interno -----------------------------------------------------------
    def _digitou(self, *_):
        if self._silencioso:
            return
        try:
            self.valor = _ler_numero(self.var.get())
        except ValueError:
            self.entry.config(bg=CORES["erro_campo"])   # deixa a caixa avermelhada
            return
        self.entry.config(bg=CORES["campo"])
        self._ao_mudar()

    def _mostrar(self, valor):
        """Escreve na caixa sem disparar o recálculo no meio."""
        self._silencioso = True
        self.var.set(self._formatar(valor))
        self._silencioso = False
        self.entry.config(bg=CORES["campo"])

    @staticmethod
    def _formatar(valor):
        return f"{valor:.6g}"


class SeletorMaterial:
    """Lista de materiais + opção 'Personalizado'.

    tipo = "estrutural" -> Personalizado pede E (GPa) e σ de escoamento (MPa)
    tipo = "ligacao"    -> Personalizado pede τ admissível (MPa) do pino/rebite
    """

    def __init__(self, parent, rotulo, tipo, ao_mudar, padrao="Aço Estrutural A36"):
        self.tipo = tipo
        self._ao_mudar = ao_mudar
        self._campos = {}

        quadro = tk.Frame(parent, bg=CORES["painel"])
        quadro.pack(fill=tk.X, padx=8, pady=3)
        tk.Label(quadro, text=rotulo, font=(FONTE, 9), fg=CORES["texto"],
                 bg=CORES["painel"]).pack(anchor="w")

        self.var = tk.StringVar(value=padrao)
        ttk.Combobox(quadro, textvariable=self.var, state="readonly",
                     values=list(MATERIALS_DB) + [PERSONALIZADO]).pack(fill=tk.X, pady=2)

        self._quadro_custom = tk.Frame(quadro, bg=CORES["painel"])
        if tipo == "estrutural":
            self._campo_custom("E", "↳ Elasticidade E (GPa):", "200")
            self._campo_custom("sigma_y", "↳ σ escoamento (MPa):", "250")
        else:
            self._campo_custom("tau_adm", "↳ τ admissível (MPa):", "145")

        self.var.trace_add("write", self._trocou_material)
        self._trocou_material(avisar=False)

    def material(self) -> Material:
        nome = self.var.get()
        if nome != PERSONALIZADO:
            p = MATERIALS_DB[nome]
            return Material(nome, E=p["E"], sigma_y=p["sigma_y"], tau_adm=p["tau_adm"])
        if self.tipo == "estrutural":
            return Material(nome, E=self._ler("E", 1e9), sigma_y=self._ler("sigma_y", 1e6))
        return Material(nome, tau_adm=self._ler("tau_adm", 1e6))

    # ---- interno -----------------------------------------------------------
    def _campo_custom(self, chave, rotulo, inicial):
        linha = tk.Frame(self._quadro_custom, bg=CORES["painel"])
        linha.pack(fill=tk.X, pady=1)
        tk.Label(linha, text=rotulo, font=(FONTE, 8, "italic"), fg=CORES["texto_suave"],
                 bg=CORES["painel"], width=LARGURA_ROTULO, anchor="w").pack(side=tk.LEFT)
        var = tk.StringVar(value=inicial)
        tk.Entry(linha, textvariable=var, width=9, bg=CORES["campo"], fg=CORES["amarelo"],
                 insertbackground="white").pack(side=tk.LEFT, padx=4)
        var.trace_add("write", lambda *_: self._ao_mudar())
        self._campos[chave] = var

    def _ler(self, chave, escala):
        """Valor digitado já no SI; None se estiver vazio/inválido/<= 0."""
        try:
            valor = _ler_numero(self._campos[chave].get())
        except ValueError:
            return None
        return valor * escala if valor > 0 else None

    def _trocou_material(self, *_, avisar=True):
        if self.var.get() == PERSONALIZADO:
            self._quadro_custom.pack(fill=tk.X, pady=2)
        else:
            self._quadro_custom.pack_forget()
        if avisar:
            self._ao_mudar()


class PainelEntradas:
    """Monta todos os campos de entrada e entrega os dados prontos (no SI)."""

    def __init__(self, parent, ao_mudar):
        self._ao_mudar = ao_mudar
        self.campos = {}        # nome -> CampoNumerico
        self.formas = {}        # "viga"/"barraA"/"barraB" -> StringVar
        self.materiais = {}     # nome -> SeletorMaterial
        self.cisalhamento = {}  # "B"/"C" -> StringVar ("Simples"/"Duplo")
        self.n_pinos = {}       # "B"/"C" -> StringVar ("1" a "10")

        self.quadro = self._criar_area_rolavel(parent)
        self._montar()

    # ---- leitura -----------------------------------------------------------
    def ler_dados(self) -> DadosEntrada:
        si = self._si
        return DadosEntrada(
            P=si("P"), xP=si("xP"), L=si("L"), xB=si("xB"), xC=si("xC"),
            LA=si("LA"), LB=si("LB"),
            secao_viga=self._secao("viga"),
            secao_barraA=self._secao("barraA"),
            secao_barraB=self._secao("barraB"),
            mat_viga=self.materiais["viga"].material(),
            mat_barraA=self.materiais["barraA"].material(),
            mat_barraB=self.materiais["barraB"].material(),
            lig_B=self._ligacao("B"),
            lig_C=self._ligacao("C"),
        )

    def unidades_saida(self):
        """Unidades dos resultados/gráficos: as mesmas dos campos P e L."""
        return self.campos["P"].unidade, self.campos["L"].unidade

    def unidade(self, nome):
        return self.campos[nome].unidade

    def valor(self, nome):
        return self.campos[nome].valor

    def definir_valor(self, nome, valor):
        self.campos[nome].definir_valor(valor)

    # ---- montagem da tela --------------------------------------------------
    def _montar(self):
        # 1. CARREGAMENTO E GEOMETRIA
        self._titulo("1. Carregamento e Geometria")
        self._dica("Posições medidas a partir de A (x = 0) até a ponta da viga (x = L).")
        self._campo("P", "Força P (↓):", 100.0, "force", "kN")
        self._campo("xP", "Posição de P (xP):", 0.0, "pos", "m")
        self._campo("L", "Comprimento viga (L):", 2.0, "pos", "m")
        self._campo("xB", "Posição barra A (xB):", 0.8, "pos", "m")
        self._campo("xC", "Posição barra B (xC):", 2.0, "pos", "m")
        self._campo("LA", "Comprimento barra A:", 1.0, "pos", "m")
        self._campo("LB", "Comprimento barra B:", 1.0, "pos", "m")

        # 2. SEÇÕES TRANSVERSAIS
        self._secao_transversal("2.1 Seção Viga Principal (AC)", "viga", "Retangular", 50, 100, 50)
        self._secao_transversal("2.2 Seção Barra A (BD)", "barraA", "Circular", 20, 20, 20)
        self._secao_transversal("2.3 Seção Barra B (CE)", "barraB", "Circular", 20, 20, 20)

        # 3. PINOS / REBITES
        self._titulo("3. Pinos/Rebites e Ligações")
        self._ligacao_campos("B", "Pino/Rebite B (viga ↔ barra A)")
        self._ligacao_campos("C", "Pino/Rebite C (viga ↔ barra B)")

        # 4. MATERIAIS DA ESTRUTURA
        self._titulo("4. Materiais da Estrutura")
        self.materiais["viga"] = SeletorMaterial(self.quadro, "Material da Viga AC:",
                                                 "estrutural", self._ao_mudar)
        self.materiais["barraA"] = SeletorMaterial(self.quadro, "Material da Barra A (BD):",
                                                   "estrutural", self._ao_mudar)
        self.materiais["barraB"] = SeletorMaterial(self.quadro, "Material da Barra B (CE):",
                                                   "estrutural", self._ao_mudar)

    def _secao_transversal(self, titulo, prefixo, forma, b, h, d):
        self._titulo(titulo)
        linha = tk.Frame(self.quadro, bg=CORES["painel"])
        linha.pack(fill=tk.X, padx=8, pady=2)
        tk.Label(linha, text="Tipo de seção:", font=(FONTE, 9), fg=CORES["texto"],
                 bg=CORES["painel"], width=LARGURA_ROTULO, anchor="w").pack(side=tk.LEFT)

        var = tk.StringVar(value=forma)
        ttk.Combobox(linha, textvariable=var, values=["Retangular", "Circular"],
                     state="readonly", width=10).pack(side=tk.LEFT)
        self.formas[prefixo] = var

        campo_b = self._campo(f"{prefixo}_b", "Largura (b):", b, "dim", "mm")
        campo_h = self._campo(f"{prefixo}_h", "Altura (h):", h, "dim", "mm")
        campo_d = self._campo(f"{prefixo}_d", "Diâmetro (d):", d, "dim", "mm")

        def trocou_forma(*_):
            retangular = var.get() == "Retangular"
            campo_b.habilitar(retangular)
            campo_h.habilitar(retangular)
            campo_d.habilitar(not retangular)
            self._ao_mudar()

        var.trace_add("write", trocou_forma)
        trocou_forma()

    def _ligacao_campos(self, letra, titulo):
        tk.Label(self.quadro, text=titulo, font=(FONTE, 9, "bold"), fg=CORES["amarelo"],
                 bg=CORES["painel"], anchor="w").pack(fill=tk.X, padx=8, pady=(6, 0))
        self._campo(f"pino{letra}_d", "Diâmetro:", 12.0, "dim", "mm")

        linha = tk.Frame(self.quadro, bg=CORES["painel"])
        linha.pack(fill=tk.X, padx=8, pady=2)
        tk.Label(linha, text="Cisalhamento:", font=(FONTE, 9), fg=CORES["texto"],
                 bg=CORES["painel"], width=LARGURA_ROTULO, anchor="w").pack(side=tk.LEFT)
        var = tk.StringVar(value="Duplo")
        ttk.Combobox(linha, textvariable=var, values=["Simples", "Duplo"],
                     state="readonly", width=10).pack(side=tk.LEFT)
        var.trace_add("write", lambda *_: self._ao_mudar())
        self.cisalhamento[letra] = var

        linha = tk.Frame(self.quadro, bg=CORES["painel"])
        linha.pack(fill=tk.X, padx=8, pady=2)
        tk.Label(linha, text="Qtd. de pinos/rebites:", font=(FONTE, 9), fg=CORES["texto"],
                 bg=CORES["painel"], width=LARGURA_ROTULO, anchor="w").pack(side=tk.LEFT)
        var_n = tk.StringVar(value="1")
        ttk.Combobox(linha, textvariable=var_n, values=[str(n) for n in range(1, 11)],
                     state="readonly", width=10).pack(side=tk.LEFT)
        var_n.trace_add("write", lambda *_: self._ao_mudar())
        self.n_pinos[letra] = var_n

        self.materiais[f"pino{letra}"] = SeletorMaterial(
            self.quadro, "Material do pino/rebite:", "ligacao", self._ao_mudar)

    # ---- peças pequenas ----------------------------------------------------
    def _campo(self, nome, rotulo, valor, tipo_unidade, unidade):
        campo = CampoNumerico(self.quadro, rotulo, valor, tipo_unidade, unidade, self._ao_mudar)
        self.campos[nome] = campo
        return campo

    def _titulo(self, texto):
        tk.Label(self.quadro, text=texto, font=(FONTE, 10, "bold"), fg=CORES["azul"],
                 bg=CORES["painel"], anchor="w").pack(fill=tk.X, pady=(12, 4), padx=8)

    def _dica(self, texto):
        tk.Label(self.quadro, text=texto, font=(FONTE, 8, "italic"), fg=CORES["cinza"],
                 bg=CORES["painel"], anchor="w", justify="left",
                 wraplength=320).pack(fill=tk.X, padx=8, pady=(0, 4))

    def _si(self, nome):
        return self.campos[nome].si()

    def _secao(self, prefixo):
        si = self._si
        return Secao(self.formas[prefixo].get(),
                     b=si(f"{prefixo}_b"), h=si(f"{prefixo}_h"), d=si(f"{prefixo}_d"))

    def _ligacao(self, letra):
        n_planos = 2 if self.cisalhamento[letra].get() == "Duplo" else 1
        return Ligacao(self._si(f"pino{letra}_d"), n_planos,
                       self.materiais[f"pino{letra}"].material(),
                       n_pinos=int(self.n_pinos[letra].get()))

    @staticmethod
    def _criar_area_rolavel(parent):
        canvas = tk.Canvas(parent, bg=CORES["painel"], highlightthickness=0, width=330)
        barra = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        quadro = tk.Frame(canvas, bg=CORES["painel"])
        quadro.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=quadro, anchor="nw")
        canvas.configure(yscrollcommand=barra.set)

        def rolar(ev):                      # roda do mouse (Windows/Mac/Linux)
            passo = -1 if (ev.num == 4 or ev.delta > 0) else 1
            canvas.yview_scroll(passo, "units")
        canvas.bind("<Enter>", lambda e: (canvas.bind_all("<MouseWheel>", rolar),
                                          canvas.bind_all("<Button-4>", rolar),
                                          canvas.bind_all("<Button-5>", rolar)))
        canvas.bind("<Leave>", lambda e: (canvas.unbind_all("<MouseWheel>"),
                                          canvas.unbind_all("<Button-4>"),
                                          canvas.unbind_all("<Button-5>")))
        canvas.pack(side="left", fill="both", expand=True)
        barra.pack(side="right", fill="y")
        return quadro

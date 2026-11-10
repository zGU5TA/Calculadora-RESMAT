# ==============================================================================
# PAINEL DE RESULTADOS (coluna da direita)
# ==============================================================================
import tkinter as tk
from tkinter import ttk

from calculadora.calculo.dados import UNIDADE_TENSAO, UNITS
from calculadora.interface.tema import CORES

LARGURA_ROTULO = 30
SEPARADOR = "-" * 56 + "\n"


class PainelResultados:

    def __init__(self, parent):
        tk.Label(parent, text="📋 RESULTADOS EM TEMPO REAL", font=("Helvetica", 12, "bold"),
                 fg=CORES["verde"], bg=CORES["painel"], pady=8).pack(fill=tk.X)

        quadro = tk.Frame(parent, bg=CORES["fundo"])
        quadro.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        barra = ttk.Scrollbar(quadro)
        barra.pack(side=tk.RIGHT, fill=tk.Y)

        self.texto = tk.Text(quadro, bg=CORES["fundo"], fg=CORES["texto"], font=("Consolas", 10),
                             wrap=tk.WORD, yscrollcommand=barra.set, borderwidth=0,
                             state=tk.DISABLED, width=58)
        self.texto.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        barra.config(command=self.texto.yview)

        t = self.texto
        t.tag_config("titulo", foreground=CORES["azul"], font=("Consolas", 11, "bold"),
                     spacing1=10, spacing3=5)
        t.tag_config("rotulo", foreground=CORES["texto_suave"], font=("Consolas", 10))
        t.tag_config("valor", foreground=CORES["amarelo"], font=("Consolas", 10, "bold"))
        t.tag_config("ok", foreground=CORES["verde"], font=("Consolas", 10, "bold"))
        t.tag_config("alerta", foreground=CORES["vermelho"], font=("Consolas", 10, "bold"))
        t.tag_config("aviso", foreground=CORES["laranja"], font=("Consolas", 10, "italic"))
        t.tag_config("separador", foreground=CORES["separador"])

    # --------------------------------------------------------------------------
    def mostrar(self, d, r, unidades):
        u_F, u_L = unidades
        kF = 1.0 / UNITS["force"][u_F]
        kL = 1.0 / UNITS["pos"][u_L]
        kS = 1.0 / UNITS["stress"][UNIDADE_TENSAO]
        uS = UNIDADE_TENSAO

        self._comecar()

        # ---- Equilíbrio ---------------------------------------------------
        self._titulo("▶ EQUILÍBRIO ESTRUTURAL")
        self._linha("Carga aplicada (P):", f"{d.P * kF:.2f} {u_F}")
        self._linha("Força da barra A na viga:", self._forca_com_sentido(r.FA * kF, u_F))
        self._linha("Força da barra B na viga:", self._forca_com_sentido(r.FB * kF, u_F))
        # Cada barra transmite ao apoio a mesma força axial que recebe da viga
        self._linha("Reação no apoio D:", f"{abs(r.barraA.forca_normal) * kF:.2f} {u_F} "
                                          f"(barra BD em {r.barraA.estado})")
        self._linha("Reação no apoio E:", f"{abs(r.barraB.forca_normal) * kF:.2f} {u_F} "
                                          f"(barra CE em {r.barraB.estado})")
        self._separador()

        # ---- Barras -------------------------------------------------------
        self._titulo("▶ TENSÕES NAS BARRAS VERTICAIS")
        for i, barra in enumerate((r.barraA, r.barraB)):
            if i:
                self._quebra()
            self._subtitulo(f"{barra.nome}:")
            self._linha("  Material:", barra.material.nome)
            self._linha("  Esforço normal:",
                        f"{abs(barra.forca_normal) * kF:.2f} {u_F} ({barra.estado})")
            self._linha("  Tensão normal (σ):", f"{abs(barra.tensao) * kS:.2f} {uS}")
            self._verificar("  Limite (σ_esc):", "  Status:", abs(barra.tensao),
                            barra.material.sigma_y, kS, uS, "ESCOAMENTO", "σ_esc")
        self._separador()

        # ---- Pinos / rebites ---------------------------------------------
        self._titulo("▶ PINOS/REBITES (CISALHAMENTO)")
        for i, pino in enumerate((r.pinoB, r.pinoC)):
            if i:
                self._quebra()
            tipo = "duplo" if pino.n_planos == 2 else "simples"
            self._subtitulo(f"{pino.nome} (cisalhamento {tipo}):")
            self._linha("  Material:", pino.material.nome)
            self._linha("  Qtd. de pinos/rebites:", f"{pino.n_pinos}")
            self._linha("  Força transmitida:", f"{pino.forca * kF:.2f} {u_F}")
            self._linha("  Tensão cisalhamento (τ):", f"{pino.tau * kS:.2f} {uS}")
            self._verificar("  Limite admissível (τ_adm):", "  Status:", pino.tau,
                            pino.material.tau_adm, kS, uS, "FALHA", "τ_adm")
        self._separador()

        # ---- Deformações --------------------------------------------------
        self._titulo("▶ DEFORMAÇÕES (mm)")
        bA, bB = r.barraA, r.barraB
        self._linha("Barra BD:", f"{bA.alongamento * 1000:+.4f} mm ({self._alonga(bA.alongamento)})")
        self._linha("Barra CE:", f"{bB.alongamento * 1000:+.4f} mm ({self._alonga(bB.alongamento)})")
        self._linha("Deslocamento de B:", f"{r.desloc_B * 1000:+.4f} mm ({self._sobe(r.desloc_B)})")
        self._linha("Deslocamento de C:", f"{r.desloc_C * 1000:+.4f} mm ({self._sobe(r.desloc_C)})")
        self._linha("Deslocamento de A (x=0):", f"{r.desloc_A * 1000:+.4f} mm")
        self._linha("Flecha máxima (viga AC):",
                    f"{r.deflexao_max * 1000:+.4f} mm em x = {r.x_deflexao_max * kL:.3f} {u_L}")
        self._separador()

        # ---- Flexão -------------------------------------------------------
        self._titulo("▶ FLEXÃO NA VIGA AC")
        self._linha("Material:", d.mat_viga.nome)
        self._linha("Esforço normal N(x):", f"0 {u_F} (só há cargas verticais)")
        self._linha("Momento máximo |M|:",
                    f"{abs(r.M_max) * kF * kL:.2f} {u_F}·{u_L} (x = {r.x_M_max * kL:.3f} {u_L})")
        self._linha("Cortante máximo |V|:",
                    f"{abs(r.V_max) * kF:.2f} {u_F} (x = {r.x_V_max * kL:.3f} {u_L})")
        self._linha("Tensão de flexão (σ_max):",
                    f"{r.sigma_flex_max * kS:.2f} {uS} (x = {r.x_sigma_flex_max * kL:.3f} {u_L})")
        self._verificar("Limite (σ_esc):", "Status viga:", r.sigma_flex_max,
                        d.mat_viga.sigma_y, kS, uS, "ESCOAMENTO", "σ_esc")

        self._terminar()

    def mostrar_erros(self, erros):
        self._comecar()
        self._titulo("⚠ DADOS INVÁLIDOS")
        for erro in erros:
            self.texto.insert(tk.END, f"• {erro}\n\n", "alerta")
        self._terminar()

    # --------------------------------------------------------------------------
    def _verificar(self, rotulo_limite, rotulo_status, valor, limite, kS, uS, falha, simbolo):
        """Compara a tensão com o limite do material (se o limite existir)."""
        if limite is None:
            self._linha(rotulo_limite, f"N/A (informe {simbolo})")
            self._linha(rotulo_status, "— sem verificação", "aviso")
            return
        self._linha(rotulo_limite, f"{limite * kS:.2f} {uS}")
        if valor <= limite:
            self._linha(rotulo_status, "✅ SEGURO", "ok")
        else:
            self._linha(rotulo_status, f"❌ {falha}", "alerta")

    @staticmethod
    def _forca_com_sentido(valor, unidade):
        if valor > 0:
            return f"{abs(valor):.2f} {unidade} (↑)"
        if valor < 0:
            return f"{abs(valor):.2f} {unidade} (↓)"
        return f"0.00 {unidade}"

    @staticmethod
    def _alonga(delta):
        return "alonga" if delta > 0 else ("encurta" if delta < 0 else "sem variação")

    @staticmethod
    def _sobe(v):
        return "sobe" if v > 0 else ("desce" if v < 0 else "parado")

    def _comecar(self):
        self.texto.config(state=tk.NORMAL)
        self.texto.delete("1.0", tk.END)

    def _terminar(self):
        self.texto.config(state=tk.DISABLED)

    def _titulo(self, texto):
        self.texto.insert(tk.END, texto + "\n", "titulo")

    def _subtitulo(self, texto):
        self.texto.insert(tk.END, texto + "\n", "rotulo")

    def _linha(self, rotulo, valor, tag="valor"):
        self.texto.insert(tk.END, f"{rotulo:<{LARGURA_ROTULO}}", "rotulo")
        self.texto.insert(tk.END, f"{valor}\n", tag)

    def _quebra(self):
        self.texto.insert(tk.END, "\n")

    def _separador(self):
        self.texto.insert(tk.END, SEPARADOR, "separador")

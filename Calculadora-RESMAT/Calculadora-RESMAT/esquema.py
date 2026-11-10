# ==============================================================================
# ESQUEMA ESTRUTURAL (desenho da viga, barras, carga e cotas)
# ==============================================================================
import tkinter as tk

from dados import CORES, UNITS

FONTE = "Helvetica"


def _fmt(valor):
    """Número curto para o desenho: 0.8 / 1.2 / 166.7 / 800."""
    return f"{valor:.4g}"


class EsquemaEstrutural:
    MARGEM_X = 110
    ALTURA_BARRA_MAX = 120

    def __init__(self, parent, ao_clicar_duas_vezes, ao_redimensionar):
        self.canvas = tk.Canvas(parent, bg=CORES["painel"], highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.bind("<Double-Button-1>", lambda e: ao_clicar_duas_vezes())
        self.canvas.bind("<Configure>", lambda e: ao_redimensionar())

    # --------------------------------------------------------------------------
    def desenhar(self, d, r, unidades):
        c = self.canvas
        c.delete("all")
        w, h = c.winfo_width(), c.winfo_height()
        if w < 200 or h < 200:
            return

        u_F, u_L = unidades
        kF = 1.0 / UNITS["force"][u_F]
        kL = 1.0 / UNITS["pos"][u_L]

        escala = (w - 2 * self.MARGEM_X) / d.L

        def px(x_m):
            return self.MARGEM_X + x_m * escala

        # Alturas das barras: proporcionais aos comprimentos (só para dar noção)
        alt_max = max(50, min(self.ALTURA_BARRA_MAX, (h - 320) / 2))
        maior = max(d.LA, d.LB)
        alt_A = alt_max * max(d.LA / maior, 0.35)
        alt_B = alt_max * max(d.LB / maior, 0.35)

        # Distribuição vertical: título | barra A + carga | viga | barra B | cotas
        acima = max(alt_A + 30, 95)
        abaixo = alt_B + 20 + 50 + 34 + 20
        sobra = max(0, h - 60 - acima - abaixo)
        y_viga = 60 + sobra / 2 + acima
        y_D = y_viga - alt_A
        y_E = y_viga + alt_B

        xA, xB, xC, xP, xL = px(0), px(d.xB), px(d.xC), px(d.xP), px(d.L)

        self._titulo(f"Viga principal AC  —  L = {_fmt(d.L * kL)} {u_L}")

        # Cotas primeiro (ficam por baixo do resto)
        self._cotas(d, px, y_viga, y_E, kL, u_L)

        # Barras verticais com apoio fixo na ponta
        c.create_line(xB, y_viga, xB, y_D, fill=CORES["laranja"], width=6)
        self._apoio(xB, y_D, para_cima=True)
        c.create_line(xC, y_viga, xC, y_E, fill=CORES["verde"], width=6)
        self._apoio(xC, y_E, para_cima=False)

        # Viga AC (de A até a ponta x = L)
        c.create_line(xA, y_viga, xL, y_viga, fill=CORES["azul"], width=8, capstyle=tk.ROUND)

        # Carga P
        self._carga(xP, y_viga, d.P * kF, u_F)

        # Rótulos das barras (devolvem o lado usado: +1 direita, -1 esquerda)
        bA, bB = r.barraA, r.barraB
        lado_A = self._rotulo_barra(xB, y_D + 14, w, CORES["laranja"],
                                    f"Barra A (BD)  ·  {_fmt(d.LA * kL)} {u_L}\n"
                                    f"N = {abs(bA.forca_normal) * kF:.2f} {u_F} ({bA.estado})")
        lado_B = self._rotulo_barra(xC, y_E - 14, w, CORES["verde"],
                                    f"Barra B (CE)  ·  {_fmt(d.LB * kL)} {u_L}\n"
                                    f"N = {abs(bB.forca_normal) * kF:.2f} {u_F} ({bB.estado})")

        # Pontos e letras (posições escolhidas para não ficar em cima das barras)
        amarelo = CORES["amarelo"]
        fonte = (FONTE, 10, "bold")
        for x, y in ((xA, y_viga), (xB, y_viga), (xC, y_viga), (xB, y_D), (xC, y_E)):
            c.create_oval(x - 6, y - 6, x + 6, y + 6, fill=amarelo, outline="black")
        c.create_text(xA - 12, y_viga, text="A", anchor="e", fill=amarelo, font=fonte)
        c.create_text(xB - 10, y_viga + 10, text="B", anchor="ne", fill=amarelo, font=fonte)
        c.create_text(xC + 10, y_viga - 10, text="C", anchor="sw", fill=amarelo, font=fonte)
        # D e E ficam do lado oposto ao texto da barra
        c.create_text(xB - 22 * lado_A, y_D - 5, text="D", anchor="e" if lado_A > 0 else "w",
                      fill=amarelo, font=fonte)
        c.create_text(xC - 22 * lado_B, y_E + 5, text="E", anchor="e" if lado_B > 0 else "w",
                      fill=amarelo, font=fonte)

    def mostrar_erros(self, erros):
        c = self.canvas
        c.delete("all")
        w, h = c.winfo_width(), c.winfo_height()
        if w < 200 or h < 200:
            return
        self._titulo("Viga principal AC")
        texto = "⚠ Não dá para desenhar/calcular com esses dados:\n\n" + \
                "\n".join(f"•  {e}" for e in erros)
        c.create_text(w / 2, h / 2, text=texto, fill=CORES["vermelho"], width=w - 160,
                      font=(FONTE, 11, "bold"), justify="left")

    # --------------------------------------------------------------------------
    def _titulo(self, texto):
        c = self.canvas
        c.create_text(16, 14, anchor="nw", text=texto, fill=CORES["texto"],
                      font=(FONTE, 11, "bold"))
        c.create_text(16, 36, anchor="nw", fill=CORES["cinza"], font=(FONTE, 8),
                      text="Clique duas vezes para editar P  ·  desenho fora de escala na vertical")

    def _apoio(self, x, y, para_cima):
        """Apoio fixo (retângulo com hachura) na ponta da barra."""
        c = self.canvas
        if para_cima:
            y0, y1 = y - 10, y
            hachura = [(x - 18 + 8 * i, y0, x - 10 + 8 * i, y0 - 8) for i in range(5)]
        else:
            y0, y1 = y, y + 10
            hachura = [(x - 18 + 8 * i, y1 + 8, x - 10 + 8 * i, y1) for i in range(5)]
        c.create_rectangle(x - 18, y0, x + 18, y1, fill=CORES["cinza"], outline="")
        for linha in hachura:
            c.create_line(*linha, fill=CORES["cinza"], width=1)

    def _carga(self, x, y_viga, P, u_F):
        c = self.canvas
        topo, base = y_viga - 62, y_viga - 6
        if P >= 0:   # para baixo
            c.create_line(x, topo, x, base, fill=CORES["vermelho"], width=4,
                          arrow=tk.LAST, arrowshape=(10, 12, 5))
        else:        # P negativo = para cima
            c.create_line(x, base, x, topo, fill=CORES["vermelho"], width=4,
                          arrow=tk.LAST, arrowshape=(10, 12, 5))
        sentido = "" if P >= 0 else " (para cima)"
        c.create_text(x, topo - 6, text=f"P = {abs(P):.2f} {u_F}{sentido}", anchor="s",
                      fill=CORES["vermelho"], font=(FONTE, 9, "bold"))

    def _rotulo_barra(self, x, y, w, cor, texto):
        """Texto ao lado da barra; vai para a esquerda se não couber na direita."""
        if x + 230 < w:
            self.canvas.create_text(x + 14, y, text=texto, anchor="w", fill=cor,
                                    font=(FONTE, 8, "bold"), justify="left")
            return 1
        self.canvas.create_text(x - 14, y, text=texto, anchor="e", fill=cor,
                                font=(FONTE, 8, "bold"), justify="right")
        return -1

    def _cotas(self, d, px, y_viga, y_E, kL, u_L):
        """Cotas horizontais: cada trecho entre A, P, B, C e a ponta, e o total L."""
        c = self.canvas
        cor = CORES["cinza"]
        y1 = y_E + 50        # linha dos trechos
        y2 = y1 + 34         # linha do comprimento total

        pontos = sorted({round(v, 12) for v in (0.0, d.xP, d.xB, d.xC, d.L)})

        # Linhas de chamada (tracejadas) saindo de cada ponto da viga
        for x_m in pontos:
            c.create_line(px(x_m), y_viga + 8, px(x_m), y2 + 6, fill=cor, dash=(3, 3))

        # Trechos
        for i, (a, b) in enumerate(zip(pontos[:-1], pontos[1:])):
            if b - a < 1e-12:
                continue
            xa, xb = px(a), px(b)
            c.create_line(xa, y1, xb, y1, fill=cor, arrow=tk.BOTH, arrowshape=(7, 8, 3))
            curto = (xb - xa) < 55
            y_txt = y1 - 4 if not curto or i % 2 == 0 else y1 + 16
            c.create_text((xa + xb) / 2, y_txt, text=f"{_fmt((b - a) * kL)} {u_L}",
                          anchor="s", fill=CORES["texto"], font=(FONTE, 8 if curto else 9))

        # Total
        c.create_line(px(0), y2, px(d.L), y2, fill=cor, arrow=tk.BOTH, arrowshape=(7, 8, 3))
        c.create_text((px(0) + px(d.L)) / 2, y2 - 4, text=f"L = {_fmt(d.L * kL)} {u_L}",
                      anchor="s", fill=CORES["texto"], font=(FONTE, 9, "bold"))

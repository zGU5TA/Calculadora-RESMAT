# ==============================================================================
# CÁLCULOS: só matemática (não usa tkinter), tudo no SI (N, m, Pa)
# ==============================================================================
import numpy as np

from calculadora.calculo.modelos import (DadosEntrada, ResultadoBarra,
                                         ResultadoLigacao, Resultados)


class CalculadoraEstrutural:
    """Viga AC apoiada em duas barras verticais e carregada por uma força P.

    Convenções:
      * x medido a partir de A (x = 0) até a ponta da viga (x = L);
      * P positivo = para baixo; FA e FB = forças das barras na viga, + para cima;
      * barra A (BD) sai de B para CIMA  -> D é o apoio fixo de cima;
      * barra B (CE) sai de C para BAIXO -> E é o apoio fixo de baixo;
      * deflexão positiva = para cima.
    """

    N_PONTOS = 801
    TOL = 1e-9

    # --------------------------------------------------------------------------
    def validar(self, d: DadosEntrada) -> list:
        """Devolve uma lista de mensagens de erro (vazia = dados OK)."""
        erros = []

        if d.L <= 0:
            erros.append("O comprimento da viga (L) deve ser maior que zero.")
        else:
            for nome, x in (("da carga P (xP)", d.xP),
                            ("da barra A (xB)", d.xB),
                            ("da barra B (xC)", d.xC)):
                if x < -self.TOL or x > d.L + self.TOL:
                    erros.append(f"A posição {nome} está fora da viga: "
                                 f"tem que ficar entre 0 (ponto A) e L.")

        if abs(d.xC - d.xB) < self.TOL:
            erros.append("As barras A e B não podem estar na mesma posição "
                         "(xB = xC): não há equilíbrio de momentos.")

        if d.LA <= 0 or d.LB <= 0:
            erros.append("Os comprimentos das barras A e B devem ser maiores que zero.")

        for nome, secao in (("viga AC", d.secao_viga),
                            ("barra A", d.secao_barraA),
                            ("barra B", d.secao_barraB)):
            if secao.area <= 0:
                erros.append(f"As dimensões da seção da {nome} devem ser maiores que zero.")

        for nome, lig in (("pino/rebite B", d.lig_B), ("pino/rebite C", d.lig_C)):
            if lig.d <= 0:
                erros.append(f"O diâmetro do {nome} deve ser maior que zero.")

        for nome, mat in (("viga AC", d.mat_viga),
                          ("barra A", d.mat_barraA),
                          ("barra B", d.mat_barraB)):
            if mat.E is None or mat.E <= 0:
                erros.append(f"Informe um módulo de elasticidade E > 0 "
                             f"para o material da {nome}.")
        return erros

    # --------------------------------------------------------------------------
    def calcular(self, d: DadosEntrada) -> Resultados:
        P, xP, xB, xC, L = d.P, d.xP, d.xB, d.xC, d.L

        # 1) Equilíbrio: soma de momentos em C e soma de forças verticais
        FA = P * (xC - xP) / (xC - xB)
        FB = P - FA

        # Forças que atuam na viga (+ para cima) e onde atuam
        forcas = np.array([-P, FA, FB])
        posicoes = np.array([xP, xB, xC])

        # 2) Barras: esforço normal (+ tração)
        #    Barra A fica ACIMA da viga: puxar a viga para cima = TRAÇÃO
        #    Barra B fica ABAIXO da viga: empurrar a viga para cima = COMPRESSÃO
        N_A = FA
        N_B = -FB

        A_A = d.secao_barraA.area
        A_B = d.secao_barraB.area
        delta_A = N_A * d.LA / (d.mat_barraA.E * A_A)   # + alonga
        delta_B = N_B * d.LB / (d.mat_barraB.E * A_B)

        barraA = ResultadoBarra("BARRA A (BD)", N_A, N_A / A_A, delta_A, d.mat_barraA)
        barraB = ResultadoBarra("BARRA B (CE)", N_B, N_B / A_B, delta_B, d.mat_barraB)

        # Deslocamento vertical dos pontos B e C (+ para cima)
        #   D está fixo em cima: se BD alonga, B desce
        #   E está fixo embaixo: se CE alonga, C sobe
        v_B = -delta_A
        v_C = delta_B

        # 3) Pinos / rebites: tau = F / (n_planos * área)
        pinoB = ResultadoLigacao("PINO/REBITE B", abs(FA),
                                 abs(FA) / (d.lig_B.n_planos * d.lig_B.area),
                                 d.lig_B.n_planos, d.lig_B.material)
        pinoC = ResultadoLigacao("PINO/REBITE C", abs(FB),
                                 abs(FB) / (d.lig_C.n_planos * d.lig_C.area),
                                 d.lig_C.n_planos, d.lig_C.material)

        # 4) Diagramas (funções de singularidade / Macaulay)
        x, a_esquerda = self._malha(L, posicoes)
        dist = x[:, None] - posicoes[None, :]                  # x - x_i
        degrau = (dist > 0) | ((dist == 0) & ~a_esquerda[:, None])
        V = (forcas * degrau).sum(axis=1)                      # V = Σ F_i <x - x_i>^0
        M = (forcas * np.clip(dist, 0, None)).sum(axis=1)      # M = Σ F_i <x - x_i>^1

        I = d.secao_viga.inercia
        sigma_flex = np.abs(M) * d.secao_viga.y_max / I

        # 5) Linha elástica EXATA:  E I v'' = M(x)
        #    v(x) = Σ F_i <x - x_i>^3 / (6 E I) + C1 x + C2
        #    C1 e C2 saem de v(xB) = v_B e v(xC) = v_C (deslocamento das barras)
        EI = d.mat_viga.E * I

        def v_particular(xx):
            xx = np.atleast_1d(np.asarray(xx, dtype=float))
            return (forcas * np.clip(xx[:, None] - posicoes, 0, None) ** 3).sum(axis=1) / (6 * EI)

        vp_B = v_particular(xB)[0]
        vp_C = v_particular(xC)[0]
        C1 = ((v_C - vp_C) - (v_B - vp_B)) / (xC - xB)   # vale para xB < xC e xB > xC
        C2 = (v_B - vp_B) - C1 * xB
        deflexao = v_particular(x) + C1 * x + C2

        i_V = int(np.argmax(np.abs(V)))
        i_M = int(np.argmax(np.abs(M)))
        i_s = int(np.argmax(sigma_flex))
        i_d = int(np.argmax(np.abs(deflexao)))

        return Resultados(
            FA=FA, FB=FB,
            barraA=barraA, barraB=barraB,
            pinoB=pinoB, pinoC=pinoC,
            x=x, V=V, M=M, sigma_flex=sigma_flex,
            deflexao=deflexao,
            V_max=V[i_V],
            M_max=M[i_M], x_M_max=x[i_M],
            sigma_flex_max=sigma_flex[i_s],
            deflexao_max=deflexao[i_d], x_deflexao_max=x[i_d],
            desloc_B=v_B, desloc_C=v_C, desloc_A=deflexao[0],
        )

    # --------------------------------------------------------------------------
    def _malha(self, L, posicoes):
        """Pontos ao longo da viga, incluindo EXATAMENTE os pontos de carga.

        Cada ponto de carga aparece duas vezes (valor logo antes e logo depois),
        para o diagrama de cortante mostrar o "degrau" na vertical.
        Devolve (x, a_esquerda), onde a_esquerda marca a cópia "logo antes".
        """
        chave = np.clip(np.unique(posicoes), 0.0, L)
        base = np.unique(np.concatenate([np.linspace(0.0, L, self.N_PONTOS), chave]))
        x = np.sort(np.concatenate([base, chave]))
        a_esquerda = np.zeros(len(x), dtype=bool)
        _, primeiro, contagem = np.unique(x, return_index=True, return_counts=True)
        a_esquerda[primeiro[contagem > 1]] = True
        return x, a_esquerda

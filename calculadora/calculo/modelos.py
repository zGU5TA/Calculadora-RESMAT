# ==============================================================================
# MODELOS: as "peças" da estrutura e os resultados (tudo no SI: N, m, Pa)
# ==============================================================================
import math
from dataclasses import dataclass
from typing import Optional

import numpy as np


@dataclass
class Secao:
    """Seção transversal retangular (b x h) ou circular (diâmetro d)."""
    forma: str          # "Retangular" ou "Circular"
    b: float = 0.0      # largura (m)
    h: float = 0.0      # altura (m)
    d: float = 0.0      # diâmetro (m)

    @property
    def area(self) -> float:
        if self.forma == "Retangular":
            return self.b * self.h
        return math.pi * (self.d / 2) ** 2

    @property
    def inercia(self) -> float:
        """Momento de inércia em relação ao eixo horizontal (flexão vertical)."""
        if self.forma == "Retangular":
            return self.b * self.h ** 3 / 12.0
        return math.pi * self.d ** 4 / 64.0

    @property
    def y_max(self) -> float:
        """Distância da linha neutra até a fibra mais afastada."""
        if self.forma == "Retangular":
            return self.h / 2.0
        return self.d / 2.0


@dataclass
class Material:
    """Propriedades do material. None = valor não informado (Personalizado em branco)."""
    nome: str
    E: Optional[float] = None         # Pa
    sigma_y: Optional[float] = None   # Pa
    tau_adm: Optional[float] = None   # Pa


@dataclass
class Ligacao:
    """Pino ou rebite que liga a viga a uma barra."""
    d: float              # diâmetro (m)
    n_planos: int         # 1 = cisalhamento simples, 2 = duplo
    material: Material

    @property
    def area(self) -> float:
        return math.pi * (self.d / 2) ** 2


@dataclass
class DadosEntrada:
    """Tudo o que o usuário digitou, já convertido para o SI.

    Posições (xP, xB, xC) são medidas a partir de A (x = 0), ao longo da viga AC.
    A barra A (BD) sai de B para CIMA; a barra B (CE) sai de C para BAIXO.
    """
    P: float
    xP: float
    L: float
    xB: float
    xC: float
    LA: float
    LB: float
    secao_viga: Secao
    secao_barraA: Secao
    secao_barraB: Secao
    mat_viga: Material
    mat_barraA: Material
    mat_barraB: Material
    lig_B: Ligacao
    lig_C: Ligacao


@dataclass
class ResultadoBarra:
    nome: str
    forca_normal: float     # N (+ tração, - compressão)
    tensao: float           # Pa (com sinal)
    alongamento: float      # m (+ alonga, - encurta)
    material: Material

    @property
    def estado(self) -> str:
        if self.forca_normal > 0:
            return "TRAÇÃO"
        if self.forca_normal < 0:
            return "COMPRESSÃO"
        return "NEUTRO"


@dataclass
class ResultadoLigacao:
    nome: str
    forca: float            # N (módulo)
    tau: float              # Pa
    n_planos: int
    material: Material


@dataclass
class Resultados:
    # Equilíbrio (forças que as barras fazem na viga; + para cima)
    FA: float
    FB: float
    barraA: ResultadoBarra
    barraB: ResultadoBarra
    pinoB: ResultadoLigacao
    pinoC: ResultadoLigacao
    # Diagramas ao longo da viga
    x: np.ndarray
    V: np.ndarray
    M: np.ndarray
    sigma_flex: np.ndarray
    deflexao: np.ndarray          # viga flexível + barras (m, + para cima)
    # Valores máximos
    V_max: float
    M_max: float
    x_M_max: float
    sigma_flex_max: float
    deflexao_max: float
    x_deflexao_max: float
    desloc_B: float
    desloc_C: float
    desloc_A: float

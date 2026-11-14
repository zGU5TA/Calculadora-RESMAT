# ==============================================================================
# MODELOS: as "peças" da estrutura e os resultados (tudo no SI: N, m, Pa)
# ==============================================================================
import math
from dataclasses import dataclass, field
from typing import List, Optional

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
    def inercia_min(self) -> float:
        """Menor momento de inércia da seção (é em torno dele que a barra flamba)."""
        if self.forma == "Retangular":
            return min(self.b * self.h ** 3, self.h * self.b ** 3) / 12.0
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
    n_pinos: int = 1      # quantidade de pinos/rebites na ligação

    @property
    def area(self) -> float:
        """Área da seção transversal de UM pino."""
        return math.pi * (self.d / 2) ** 2

    @property
    def area_resistente(self) -> float:
        """Área total que resiste ao cisalhamento: pinos x planos x área de um pino."""
        return self.n_pinos * self.n_planos * self.area


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
class ResultadoFlambagem:
    """Flambagem de uma barra COMPRIMIDA (extremidades articuladas pelos pinos, K = 1)."""
    comprimento_efetivo: float          # Le = K·L (m)
    inercia_min: float                  # m⁴
    raio_giracao: float                 # r = √(I/A) (m)
    esbeltez: float                     # λ = Le / r
    esbeltez_limite: Optional[float]    # λc = π·√(2E/σ_esc); None se σ_esc não informado
    regime: str                         # "Euler" (esbelta) ou "Johnson" (intermediária)
    tensao_critica: float               # σ_cr (Pa)
    carga_critica: float                # P_cr = σ_cr·A (N)
    carga_aplicada: float               # |N| (N)
    fs: float                           # P_cr / |N|


@dataclass
class Verificacao:
    """Uma comparação "o que atua" x "o que o material aguenta" (vira um cartão verde,
    amarelo ou vermelho na tela)."""
    chave: str
    titulo: str                   # "Barra A (BD) — escoamento"
    grandeza: str                 # "tensao" (Pa) ou "forca" (N)
    simbolo_valor: str            # "σ"
    valor: float
    simbolo_limite: str           # "σ_esc"
    limite: Optional[float]       # None = material sem esse dado
    rotulo_falha: str             # "ESCOAMENTO", "FLAMBAGEM", "FALHA"
    fs: Optional[float] = None    # coeficiente de segurança = limite / valor
    nivel: str = "sem_limite"     # "ok", "atencao", "falha" ou "sem_limite"

    @property
    def utilizacao(self) -> Optional[float]:
        """Quanto do limite está sendo usado (1.0 = 100 %)."""
        if self.limite is None or self.limite <= 0:
            return None
        return self.valor / self.limite


@dataclass
class ResultadoBarra:
    nome: str
    forca_normal: float     # N (+ tração, - compressão)
    tensao: float           # Pa (com sinal)
    alongamento: float      # m (+ alonga, - encurta)
    material: Material
    flambagem: Optional[ResultadoFlambagem] = None   # só existe se a barra está comprimida

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
    n_pinos: int = 1


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
    N: np.ndarray                 # esforço normal na viga (zero: só há cargas verticais)
    V: np.ndarray
    M: np.ndarray
    sigma_flex: np.ndarray
    deflexao: np.ndarray          # viga flexível + barras (m, + para cima) - só referência
    deflexao_rigida: np.ndarray   # VIGA RÍGIDA: reta que passa por B' e C' (m, + para cima)
    # Valores máximos
    V_max: float
    x_V_max: float
    M_max: float
    x_M_max: float
    sigma_flex_max: float
    x_sigma_flex_max: float
    deflexao_max: float
    x_deflexao_max: float
    desloc_B: float               # = alongamento da barra em B (viga rígida)
    desloc_C: float               # = alongamento da barra em C (viga rígida)
    desloc_A: float               # em x = 0, por semelhança de triângulos (viga rígida)
    desloc_P: float               # sob a carga P, por semelhança de triângulos
    rotacao: float                # rotação da viga rígida (rad, + anti-horário)
    flexao_extra_max: float       # máx |viga flexível - viga rígida| (m): erro da hipótese
    # Verificações de segurança (coeficientes de segurança)
    verificacoes: List[Verificacao] = field(default_factory=list)
    fs_minimo: Optional[float] = None      # menor FS entre todas as verificações
    nivel_geral: str = "ok"                # pior nível: "falha" > "atencao" > "ok"

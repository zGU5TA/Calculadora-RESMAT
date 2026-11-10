# A3 — Calculadora Estrutural Interativa (Resistência dos Materiais I)

Viga principal AC apoiada em duas barras verticais (BD para cima, CE para baixo),
com uma carga P. Calcula equilíbrio, tensões nas barras, cisalhamento nos
pinos/rebites, DEC, DMF, tensão de flexão e linha elástica.

## Como rodar

```bash
pip install numpy matplotlib
python main.py        # de dentro desta pasta
python testes.py      # confere os cálculos (não abre janela)
```

## Arquivos

| Arquivo | Classe principal | O que faz |
|---|---|---|
| `main.py` | — | Ponto de entrada: abre a janela |
| `app.py` | `ResmatCalculatorApp` | Monta a janela e liga entradas → cálculo → saídas |
| `dados.py` | — | Banco de materiais, unidades e cores |
| `modelos.py` | `Secao`, `Material`, `Ligacao`, `DadosEntrada`, `Resultados` | "Peças" da estrutura e resultados (tudo no SI) |
| `calculos.py` | `CalculadoraEstrutural` | Toda a matemática (não usa tkinter) |
| `painel_entradas.py` | `PainelEntradas`, `CampoNumerico`, `SeletorMaterial` | Coluna da esquerda (campos, unidades, materiais) |
| `esquema.py` | `EsquemaEstrutural` | Desenho da estrutura com cotas |
| `graficos.py` | `GraficosDEIS` | DEC, DMF, tensão de flexão e linha elástica |
| `painel_resultados.py` | `PainelResultados` | Coluna da direita (texto dos resultados) |
| `testes.py` | — | Testes dos cálculos contra fórmulas conhecidas |

## Convenções

- `x` medido a partir de A (x = 0) até a ponta da viga (x = L); `xP`, `xB` e `xC` têm que ficar entre 0 e L.
- P positivo = para baixo. Forças das barras na viga: positivo = para cima.
- Barra A (BD) fica **acima** da viga; barra B (CE) fica **abaixo**. Por isso, se a barra CE
  empurra a viga para cima ela está em **compressão**; se puxa para baixo, em **tração**.
- Deflexão positiva = para cima. A linha elástica é exata (funções de singularidade):
  `E·I·v(x) = Σ Fᵢ⟨x − xᵢ⟩³/6 + C₁x + C₂`, com C₁ e C₂ tirados dos deslocamentos de B e C
  causados pelo alongamento das barras.
- Material "Personalizado": nas barras/viga pede E e σ de escoamento; nos pinos/rebites pede τ admissível.

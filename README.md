# A3 — Calculadora Estrutural Interativa (Resistência dos Materiais I)

Viga principal AC apoiada em duas barras verticais (BD para cima, CE para baixo),
com uma carga P. Calcula equilíbrio, tensões nas barras, cisalhamento nos
pinos/rebites, DEC, DMF, tensão de flexão e linha elástica.

## Como abrir

**Sem Python (mais fácil):** baixe o `CalculadoraRESMAT.exe` em
[Releases](../../releases/latest) e dê dois cliques.
Na primeira vez o Windows pode mostrar "O Windows protegeu o computador":
clique em **Mais informações → Executar assim mesmo** (o .exe não é assinado).

**Pelo código (VS Code):** abra a pasta do projeto e dê play no `main.py`.
Na primeira vez ele cria a pasta `.venv` e instala numpy e matplotlib sozinho.
Depois disso dá para abrir com dois cliques em `Abrir Calculadora.bat`.

## Pastas

```
main.py                     ponto de entrada (é nele que se dá play)
Abrir Calculadora.bat       abre sem VS Code (depois do 1º play)
requirements.txt            bibliotecas: numpy, matplotlib
calculadora/
  calculo/                  só matemática (não usa tkinter)
    dados.py                materiais e unidades
    modelos.py              Secao, Material, Ligacao, DadosEntrada, Resultados
    calculos.py             CalculadoraEstrutural (equilíbrio, tensões, diagramas, linha elástica)
  interface/                parte visual (tkinter + matplotlib)
    app.py                  ResmatCalculatorApp: monta a janela e liga tudo
    painel_entradas.py      coluna da esquerda (campos, unidades, materiais)
    esquema.py              desenho da estrutura com cotas
    graficos.py             DEC, DMF, tensão de flexão e linha elástica
    painel_resultados.py    coluna da direita (resultados)
    tema.py                 cores
testes/
  testes_calculos.py        confere os cálculos com fórmulas conhecidas
versao_antiga/
  RSMC.py                   versão antiga, tudo em um arquivo só (referência)
.github/workflows/
  gerar-executavel.yml      gera o .exe automaticamente no GitHub
```

Para conferir os cálculos: `python testes/testes_calculos.py`.

## Como o .exe é gerado

A cada push na `main`, o GitHub Actions (aba **Actions**) instala o Python num
Windows, roda os testes, gera o `.exe` com PyInstaller, abre o `.exe` para
testar e publica em **Releases**. Em pull requests o `.exe` fica em
**Actions → (execução) → Artifacts**.

## Convenções

- `x` medido a partir de A (x = 0) até a ponta da viga (x = L); `xP`, `xB` e `xC` têm que ficar entre 0 e L.
- P positivo = para baixo. Forças das barras na viga: positivo = para cima.
- Barra A (BD) fica **acima** da viga; barra B (CE) fica **abaixo**. Por isso, se a barra CE
  empurra a viga para cima ela está em **compressão**; se puxa para baixo, em **tração**.
- Deflexão positiva = para cima. A linha elástica é exata (funções de singularidade):
  `E·I·v(x) = Σ Fᵢ⟨x − xᵢ⟩³/6 + C₁x + C₂`, com C₁ e C₂ tirados dos deslocamentos de B e C
  causados pelo alongamento das barras.
- Material "Personalizado": nas barras/viga pede E e σ de escoamento; nos pinos/rebites pede τ admissível.

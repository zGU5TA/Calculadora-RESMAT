# A3 — Calculadora Estrutural Interativa (Resistência dos Materiais I)

Viga principal AC apoiada em duas barras verticais (BD para cima, CE para baixo),
com uma carga P. Calcula equilíbrio, tensões nas barras, cisalhamento nos
pinos/rebites (com quantidade de pinos e cisalhamento simples/duplo), DEN, DEC,
DMF, tensão de flexão e a deformação da viga (tratada como rígida, veja abaixo).

## Como abrir

**Sem Python (mais fácil):** baixe o arquivo do seu sistema em
[Releases](../../releases/latest) e abra.

| Sistema | Arquivo | Como abrir |
|---|---|---|
| Windows | [`CalculadoraRESMAT.exe`](https://github.com/zGU5TA/Calculadora-RESMAT/releases/latest/download/CalculadoraRESMAT.exe) | Dois cliques. Se aparecer "O Windows protegeu o computador": **Mais informações → Executar assim mesmo** (o .exe não é assinado). |
| Mac com chip Apple (M1, M2, M3, M4...) | [`CalculadoraRESMAT-mac-apple-silicon.zip`](https://github.com/zGU5TA/Calculadora-RESMAT/releases/latest/download/CalculadoraRESMAT-mac-apple-silicon.zip) | Dê dois cliques no .zip, arraste o app para a pasta Aplicativos e siga o aviso do Mac abaixo. |
| Mac com processador Intel | [`CalculadoraRESMAT-mac-intel.zip`](https://github.com/zGU5TA/Calculadora-RESMAT/releases/latest/download/CalculadoraRESMAT-mac-intel.zip) | Igual ao anterior. |
| Linux | [`CalculadoraRESMAT-linux.tar.gz`](https://github.com/zGU5TA/Calculadora-RESMAT/releases/latest/download/CalculadoraRESMAT-linux.tar.gz) | `tar -xzf CalculadoraRESMAT-linux.tar.gz` e depois `./CalculadoraRESMAT` |

Não sabe qual Mac tem? Menu da maçã → **Sobre Este Mac**: "Chip Apple M..." ou "Processador Intel".

**Aviso do Mac:** o app não é assinado pela Apple, então na primeira vez o Mac diz que
ele "não pode ser aberto" ou está "danificado". Isso é esperado. Resolva de um destes jeitos:

1. Abra o **Terminal** e rode (ajuste o caminho se o app estiver em outra pasta):
   `xattr -dr com.apple.quarantine /Applications/CalculadoraRESMAT.app`
   Depois é só abrir normalmente. (Funciona em qualquer versão do macOS.)
2. Ou tente abrir o app, vá em **Ajustes do Sistema → Privacidade e Segurança**, role até o
   aviso sobre o CalculadoraRESMAT e clique em **Abrir Mesmo Assim**.

**Pelo código (VS Code, Windows, Mac ou Linux):** abra a pasta do projeto e dê play no `main.py`
(ou `python3 main.py`). Na primeira vez ele cria a pasta `.venv` e instala numpy e matplotlib
sozinho. No Mac, use o Python de python.org (o do Homebrew precisa de `brew install python-tk`);
no Linux, instale o Tk (`sudo apt install python3-tk`).

## Pastas

```
main.py                     ponto de entrada (é nele que se dá play)
requirements.txt            bibliotecas: numpy, matplotlib
calculadora/
  calculo/                  só matemática (não usa tkinter)
    dados.py                materiais e unidades
    modelos.py              Secao, Material, Ligacao, DadosEntrada, Resultados
    calculos.py             CalculadoraEstrutural (equilíbrio, tensões, diagramas, deformação da viga rígida)
  interface/                parte visual (tkinter + matplotlib)
    app.py                  ResmatCalculatorApp: monta a janela e liga tudo
    painel_entradas.py      coluna da esquerda (campos, unidades, materiais)
    esquema.py              desenho da estrutura com cotas
    graficos.py             DEN, DEC, DMF, tensão de flexão e deformação (viga rígida)
    painel_resultados.py    coluna da direita (resultados)
    tema.py                 cores
testes/
  testes_calculos.py        confere os cálculos com fórmulas conhecidas e com o caso manual
  caso_de_teste.json        dados do caso de teste e resultados calculados à mão
.github/workflows/
  gerar-executaveis.yml     gera os executáveis (Windows, Linux e Mac) automaticamente no GitHub
```

Para conferir os cálculos: `python testes/testes_calculos.py` (imprime a tabela
programa × cálculo manual, com diferença absoluta e percentual).

## Caso de teste (cálculo manual)

Entradas: P = 20 kN em A (xP = 0), L = 2 m, B em 0,8 m, C em 2,0 m, barras de 1 m
com Ø 20 mm, viga 50 × 100 mm, pinos Ø 16 mm em cisalhamento duplo (1 pino por
ligação), tudo em aço A36 (E = 200 GPa).

| Grandeza | Conta | Resultado |
|---|---|---|
| Barra A (BD) | F_A = P(x_C − x_P)/(x_C − x_B) = 20·2/1,2 | 33,333 kN (tração) |
| Barra B (CE) | F_B = P − F_A = 20 − 33,333 | 13,333 kN (tração) |
| σ barra A | 33 333 / (π·0,01²) | 106,10 MPa |
| σ barra B | 13 333 / (π·0,01²) | 42,44 MPa |
| τ pino B | 33 333 / (2·π·0,008²) | 82,89 MPa |
| τ pino C | 13 333 / (2·π·0,008²) | 33,16 MPa |
| M máx (em B) | P·x_B = 20·0,8 | 16 kN·m |
| σ flexão | M·y/I = 16 000·0,05 / (0,05·0,1³/12) | 192 MPa |
| δ barra A | N·L/(E·A) = 33 333·1 / (200e9·π·0,01²) | 0,5305 mm |
| δ barra B | 13 333·1 / (200e9·π·0,01²) | 0,2122 mm |
| δB (viga rígida) | a barra BD alonga e B desce | −0,5305 mm (↓) |
| δC (viga rígida) | a barra CE alonga e C sobe | +0,2122 mm (↑) |
| δA (viga rígida) | semelhança de triângulos: δB + (δC − δB)·(0 − x_B)/(x_C − x_B) | −1,0257 mm (↓) |

N(x) = 0 em toda a viga, pois todas as forças que atuam nela são verticais.

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

## Deformação: hipótese da viga rígida

Como pediu o professor, a viga AC é tratada como **rígida**: ela não flete, só desloca e gira.
Quem se deforma são as barras:

- δB e δC são os deslocamentos verticais de B e C, iguais ao alongamento (ou encurtamento)
  das barras. A barra BD fica acima da viga: se alonga, B desce. A barra CE fica abaixo:
  se alonga, C sobe.
- A viga deformada é a **reta** que passa por B' e C'.
- Qualquer outro ponto (A, ponto da carga P) sai por semelhança de triângulos:
  `δ(x) = δB + (δC − δB)·(x − x_B)/(x_C − x_B)`.

O gráfico mostra a posição original (tracejada), a reta deformada e as cotas δA, δB e δC
(+ sobe, − desce). O painel de resultados também informa a rotação da viga e quanto a flexão
ignorada valeria (a flecha da viga flexível menos a da rígida), que mostra o tamanho do erro
da hipótese.

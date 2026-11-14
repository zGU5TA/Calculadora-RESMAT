# ==============================================================================
# Gera os ícones do programa a partir da logo (assets/logo_original.png):
#   assets/icone.ico   -> Windows (vários tamanhos dentro do mesmo arquivo)
#   assets/icone.icns  -> macOS
#   assets/icone.png   -> 256 px (Linux e uso geral)
#   calculadora/interface/icone_dados.py -> PNG pequeno embutido no código, usado
#                                           como ícone da janela em qualquer sistema
# Para refazer (por exemplo, se trocar a logo):  python ferramentas/gerar_icones.py
# ==============================================================================
import base64
import io
import os

from PIL import Image, ImageDraw

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGO = os.path.join(RAIZ, "assets", "logo_original.png")

CORTE = 0.84          # fração central da logo que é usada (tira a sobra do fundo)
RAIO = 0.2237         # canto arredondado no estilo dos ícones do macOS/Windows 11


def quadrado_arredondado(logo: Image.Image, lado: int) -> Image.Image:
    """Logo cortada no centro, com cantos arredondados e fundo transparente."""
    w, h = logo.size
    c = int(min(w, h) * CORTE)
    x0, y0 = (w - c) // 2, (h - c) // 2
    arte = logo.convert("RGBA").crop((x0, y0, x0 + c, y0 + c))

    # Máscara desenhada em 4x e reduzida: borda suave, sem serrilhado
    sup = lado * 4
    mascara = Image.new("L", (sup, sup), 0)
    ImageDraw.Draw(mascara).rounded_rectangle((0, 0, sup - 1, sup - 1),
                                              radius=int(sup * RAIO), fill=255)
    mascara = mascara.resize((lado, lado), Image.LANCZOS)

    arte = arte.resize((lado, lado), Image.LANCZOS)
    saida = Image.new("RGBA", (lado, lado), (0, 0, 0, 0))
    saida.paste(arte, (0, 0), mascara)
    return saida


def main():
    logo = Image.open(LOGO)
    mestre = quadrado_arredondado(logo, 1024)

    pasta = os.path.join(RAIZ, "assets")
    mestre.resize((256, 256), Image.LANCZOS).save(os.path.join(pasta, "icone.png"))

    tamanhos = [16, 24, 32, 48, 64, 128, 256]
    mestre.save(os.path.join(pasta, "icone.ico"), format="ICO",
                sizes=[(t, t) for t in tamanhos])
    mestre.save(os.path.join(pasta, "icone.icns"), format="ICNS")

    # PNG pequeno em texto, para a janela (não depende de arquivos soltos no .exe)
    buf = io.BytesIO()
    mestre.resize((128, 128), Image.LANCZOS).save(buf, format="PNG", optimize=True)
    b64 = base64.b64encode(buf.getvalue()).decode("ascii")
    linhas = [b64[i:i + 100] for i in range(0, len(b64), 100)]
    codigo = ('# Gerado por ferramentas/gerar_icones.py - não edite à mão.\n'
              '# Ícone da janela (PNG 128 x 128 em base64).\n'
              'ICONE_PNG_BASE64 = (\n' +
              "\n".join(f'    "{l}"' for l in linhas) + "\n)\n")
    with open(os.path.join(RAIZ, "calculadora", "interface", "icone_dados.py"),
              "w", encoding="utf-8") as f:
        f.write(codigo)
    print("Ícones gerados em assets/ e calculadora/interface/icone_dados.py")


if __name__ == "__main__":
    main()

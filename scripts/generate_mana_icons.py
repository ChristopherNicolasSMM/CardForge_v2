"""
Gera assets/icons_png/ compondo os símbolos de mana a partir dos glifos
vendorizados em assets/mana-src/glyphs/ (projeto Mana, SIL OFL 1.1 —
ver assets/mana-src/ATTRIBUTION.md) + a paleta oficial de cores do mesmo
projeto (ver PALETTE abaixo, extraída de sass/_variables.scss do pacote
`mana-font`).

Por quê compor em vez de só rasterizar os SVGs do Mana direto: os SVGs
individuais do Mana (`w.svg`, `u.svg` etc.) contêm só o contorno do
símbolo — o círculo colorido de fundo característico dos símbolos de mana
é aplicado via CSS (`background-color` na classe `.ms-cost`), não faz
parte do arquivo SVG. Sem um navegador de verdade pra rodar essa CSS (não
disponível neste ambiente — ver docs/tech/doc-tecnico-mtg-symbols-frames.md,
seção 13), este script reproduz a composição (círculo + glifo, incluindo
o split diagonal usado em híbridos) diretamente em PIL, usando as cores
oficiais do projeto.

Rodar (requer cairosvg só pra rasterizar os glifos-fonte, PIL já é
dependência do projeto):
    pip install cairosvg
    python scripts/generate_mana_icons.py
"""
from __future__ import annotations

import io
import re
from pathlib import Path

try:
    import cairosvg
except ImportError:
    raise SystemExit(
        "cairosvg não encontrado. Instale com: pip install cairosvg\n"
        "(dependência apenas deste script — não é necessária para rodar o CardForge.)"
    )

from PIL import Image, ImageDraw
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent.parent
GLYPHS_DIR = ROOT / "assets" / "mana-src" / "glyphs"
DST = ROOT / "assets" / "icons_png"

SIZE = 256           # px do canvas final de cada ícone
GLYPH_RASTER = 512   # px de rasterização do glifo antes de reamostrar (nitidez)

# Paleta oficial do projeto Mana (sass/_variables.scss, pacote `mana-font`
# no npm — ver assets/mana-src/ATTRIBUTION.md).
PALETTE = {
    "w": "#f0f2c0", "u": "#b5cde3", "b": "#aca29a", "r": "#db8664", "g": "#93b483",
    "colorless": "#beb9b2",
}
BORDER = "#010101"
GLYPH_DARK = "#111111"
GLYPH_LIGHT = "#f5f5f5"


def _hex_rgba(h: str, alpha: int = 255) -> tuple[int, int, int, int]:
    h = h.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), alpha)


def _load_glyph(name: str, color: str) -> Image.Image:
    """Rasteriza um glifo vendorizado, recolorido, com padding transparente
    numa tela quadrada (preserva a proporção original do glifo)."""
    svg_path = GLYPHS_DIR / f"{name}.svg"
    raw = svg_path.read_text()
    # Os glifos do Mana usam um único fill sólido (ex: fill="#444") — troca
    # direta de string é suficiente e evita depender de parser CSS.
    recolored = re.sub(r'fill="#[0-9a-fA-F]{3,6}"', f'fill="{color}"', raw)

    root = ET.fromstring(raw)
    vb = root.get("viewBox", "0 0 32 32").split()
    vb_w, vb_h = float(vb[2]), float(vb[3])

    tmp_svg = DST / f"_tmp_{name}.svg"
    tmp_svg.parent.mkdir(parents=True, exist_ok=True)
    tmp_svg.write_text(recolored)
    try:
        # Rasteriza mantendo a proporção original do glifo (não força quadrado).
        if vb_w >= vb_h:
            out_w, out_h = GLYPH_RASTER, int(GLYPH_RASTER * vb_h / vb_w)
        else:
            out_h, out_w = GLYPH_RASTER, int(GLYPH_RASTER * vb_w / vb_h)
        png_bytes = cairosvg.svg2png(url=str(tmp_svg), output_width=out_w, output_height=out_h)
    finally:
        tmp_svg.unlink(missing_ok=True)

    glyph_img = Image.open(io.BytesIO(png_bytes)).convert("RGBA")
    # Centraliza numa tela quadrada — simplifica o posicionamento depois.
    canvas = Image.new("RGBA", (GLYPH_RASTER, GLYPH_RASTER), (0, 0, 0, 0))
    canvas.paste(glyph_img, ((GLYPH_RASTER - glyph_img.width) // 2,
                              (GLYPH_RASTER - glyph_img.height) // 2), glyph_img)
    return canvas


_glyph_cache: dict[tuple[str, str], Image.Image] = {}


def glyph(name: str, color: str) -> Image.Image:
    key = (name, color)
    if key not in _glyph_cache:
        _glyph_cache[key] = _load_glyph(name, color)
    return _glyph_cache[key]


def _circle_mask(size: int) -> Image.Image:
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, size - 1, size - 1), fill=255)
    return mask


def circle_bg(color_hex: str) -> Image.Image:
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse((2, 2, SIZE - 3, SIZE - 3), fill=_hex_rgba(color_hex))
    draw.ellipse((2, 2, SIZE - 3, SIZE - 3), outline=_hex_rgba(BORDER), width=4)
    return img


def split_circle_bg(color_a: str, color_b: str) -> Image.Image:
    """Círculo dividido na diagonal (canto superior-esquerdo / inferior-
    direito) — aproxima o linear-gradient(135deg) usado pelo Mana pros
    símbolos híbridos, sem precisar de um motor CSS de verdade."""
    square = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(square)
    draw.polygon([(0, 0), (SIZE, 0), (0, SIZE)], fill=_hex_rgba(color_a))
    draw.polygon([(SIZE, 0), (SIZE, SIZE), (0, SIZE)], fill=_hex_rgba(color_b))
    mask = _circle_mask(SIZE)
    out = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    out.paste(square, (0, 0), mask)
    draw_out = ImageDraw.Draw(out)
    draw_out.ellipse((2, 2, SIZE - 3, SIZE - 3), outline=_hex_rgba(BORDER), width=4)
    return out


def paste_scaled(base: Image.Image, glyph_img: Image.Image, scale: float,
                  center: tuple[float, float]) -> None:
    """Cola glyph_img em base, redimensionado pra `scale` * SIZE e
    centralizado na posição relativa `center` (0..1, 0..1)."""
    target = max(1, int(SIZE * scale))
    ratio = glyph_img.height / glyph_img.width
    w, h = target, int(target * ratio)
    if ratio > 1:
        h, w = target, int(target / ratio)
    resized = glyph_img.resize((w, h), Image.LANCZOS)
    cx, cy = int(SIZE * center[0]), int(SIZE * center[1])
    base.paste(resized, (cx - w // 2, cy - h // 2), resized)


def save(name_relpath: str, img: Image.Image) -> None:
    dest = DST / name_relpath
    dest.parent.mkdir(parents=True, exist_ok=True)
    img.save(dest)


def build_simple(letter_upper: str, glyph_name: str, color_hex: str) -> None:
    img = circle_bg(color_hex)
    paste_scaled(img, glyph(glyph_name, GLYPH_DARK), 0.56, (0.5, 0.5))
    save(f"{letter_upper}.png", img)


def build_number(n: int) -> None:
    img = circle_bg(PALETTE["colorless"])
    scale = 0.56 if n < 10 else (0.68 if n < 100 else 0.8)
    paste_scaled(img, glyph(str(n), GLYPH_DARK), scale, (0.5, 0.5))
    save(f"{n}.png", img)


def build_x() -> None:
    img = circle_bg(PALETTE["colorless"])
    paste_scaled(img, glyph("x", GLYPH_DARK), 0.56, (0.5, 0.5))
    save("x.png", img)


def build_tap_untap() -> None:
    for fname, glyph_name in [("tap", "tap"), ("untap", "untap")]:
        img = circle_bg("#1a1a1a")
        paste_scaled(img, glyph(glyph_name, GLYPH_LIGHT), 0.6, (0.5, 0.5))
        save(f"{fname}.png", img)


def build_energy() -> None:
    img = circle_bg(PALETTE["colorless"])
    paste_scaled(img, glyph("e", GLYPH_DARK), 0.5, (0.5, 0.5))
    save("energy.png", img)


def build_snow() -> None:
    # Mana não tem um glifo dedicado de "neve" no nosso subconjunto vendorizado
    # -- usa o símbolo incolor como base visual (mesma family de "genérico").
    img = circle_bg(PALETTE["colorless"])
    paste_scaled(img, glyph("c", GLYPH_DARK), 0.56, (0.5, 0.5))
    save("snow.png", img)


def build_colorless() -> None:
    img = circle_bg(PALETTE["colorless"])
    paste_scaled(img, glyph("c", GLYPH_DARK), 0.56, (0.5, 0.5))
    save("colorless.png", img)


COLOR_LETTERS = {"w": "W", "u": "U", "b": "B", "r": "R", "g": "G"}
FULL_NAMES = {"w": "white", "u": "blue", "b": "black", "r": "red", "g": "green"}


def full_name(c: str) -> str:
    return FULL_NAMES[c]


def build_hybrid(a: str, b: str) -> None:
    img = split_circle_bg(PALETTE[a], PALETTE[b])
    paste_scaled(img, glyph(a, GLYPH_DARK), 0.34, (0.28, 0.28))
    paste_scaled(img, glyph(b, GLYPH_DARK), 0.34, (0.72, 0.72))
    save(f"hybrid/{full_name(a)}-{full_name(b)}.png", img)


def build_twobrid(c: str) -> None:
    img = split_circle_bg(PALETTE["colorless"], PALETTE[c])
    paste_scaled(img, glyph("2", GLYPH_DARK), 0.34, (0.28, 0.28))
    paste_scaled(img, glyph(c, GLYPH_DARK), 0.34, (0.72, 0.72))
    save(f"hybrid/2-{full_name(c)}.png", img)


def build_phyrexian(c: str) -> None:
    img = circle_bg(PALETTE[c])
    paste_scaled(img, glyph("p", GLYPH_DARK), 0.56, (0.5, 0.5))
    save(f"phyrexian/{full_name(c)}.png", img)


def build_phyrexian_colorless() -> None:
    img = circle_bg(PALETTE["colorless"])
    paste_scaled(img, glyph("p", GLYPH_DARK), 0.56, (0.5, 0.5))
    save("phyrexian/colorless.png", img)


def build_phyrexian_hybrid(a: str, b: str) -> None:
    img = split_circle_bg(PALETTE[a], PALETTE[b])
    paste_scaled(img, glyph("p", GLYPH_DARK), 0.5, (0.5, 0.5))
    save(f"phyrexian/{full_name(a)}-{full_name(b)}.png", img)


def main() -> None:
    DST.mkdir(parents=True, exist_ok=True)

    for letter, color in PALETTE.items():
        if letter == "colorless":
            continue
        build_simple(COLOR_LETTERS[letter], letter, color)
    build_colorless()
    build_snow()
    for n in list(range(0, 21)) + [100]:
        build_number(n)
    build_x()
    build_tap_untap()
    build_energy()

    colors = ["w", "u", "b", "r", "g"]
    for a in colors:
        for b in colors:
            if a == b:
                continue
            build_hybrid(a, b)  # gera as duas ordens (a-b e b-a)
    for c in colors:
        build_twobrid(c)
    for c in colors:
        build_phyrexian(c)
    build_phyrexian_colorless()
    for i, a in enumerate(colors):
        for b in colors[i + 1:]:
            build_phyrexian_hybrid(a, b)
            build_phyrexian_hybrid(b, a)

    count = len(list(DST.rglob("*.png")))
    print(f"{count} ícones gerados em {DST}")


if __name__ == "__main__":
    main()

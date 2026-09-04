"""
Gera assets/icons_png/ a partir dos SVGs em assets/icons/, espelhando a
mesma estrutura de pastas (incluindo hybrid/ e phyrexian/).

Rodar uma única vez, ou sempre que os SVGs de origem em assets/icons/
mudarem (por exemplo, ao trocar os placeholders atuais pelos ícones do
projeto Mana — ver docs/tech/doc-tecnico-mtg-symbols-frames.md):

    pip install cairosvg
    python scripts/generate_mana_icons.py

cairosvg é dependência apenas deste script de geração — não é necessário
em tempo de execução do CardForge (por isso não está em requirements.txt).
Os PNGs gerados são versionados no repositório; ver seção 2.1 do
documento técnico sobre a decisão de rasterizar uma vez em vez de
depender de rasterização em runtime (o projeto não usa nenhuma lib de
SVG-para-raster em produção).
"""
from __future__ import annotations
from pathlib import Path

try:
    import cairosvg
except ImportError:
    raise SystemExit(
        "cairosvg não encontrado. Instale com: pip install cairosvg\n"
        "(dependência apenas deste script — não é necessária para rodar o CardForge.)"
    )

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "assets" / "icons"
DST = ROOT / "assets" / "icons_png"
SIZE = 128  # px — redimensionado depois, em tempo de render, pro tamanho da linha


def main() -> None:
    if not SRC.is_dir():
        raise SystemExit(f"Pasta de origem não encontrada: {SRC}")

    count = 0
    for svg_path in sorted(SRC.rglob("*.svg")):
        rel = svg_path.relative_to(SRC)
        png_path = DST / rel.with_suffix(".png")
        png_path.parent.mkdir(parents=True, exist_ok=True)
        cairosvg.svg2png(
            url=str(svg_path),
            write_to=str(png_path),
            output_width=SIZE,
            output_height=SIZE,
        )
        count += 1

    print(f"{count} ícones rasterizados em {DST}")


if __name__ == "__main__":
    main()

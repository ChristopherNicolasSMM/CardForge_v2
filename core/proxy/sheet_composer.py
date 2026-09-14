"""
Proxy Sheet Composer + PDF Writer.

Fluxo:
  1. Recebe lista de PIL.Image (cards já renderizados)
  2. Compõe páginas (N×M por folha)
  3. Adiciona marcas de corte (opcional)
  4. Gera PDF pronto para impressão

Formatos de página suportados: A4, A3, Letter
Layout padrão: 3×3 = 9 cards por A4
"""
from __future__ import annotations

import io
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from PIL import Image, ImageDraw

# ── Definições de página (mm) ───────────────────────────────────────────────
PAGE_FORMATS = {
    "A4":     (210.0, 297.0),
    "A3":     (297.0, 420.0),
    "LETTER": (215.9, 279.4),
}

CARD_W_MM = 63.0
CARD_H_MM = 88.0
BLEED_MM  = 3.0      # sangria ao redor de cada card nas marcas de corte
MARGIN_MM = 10.0     # margem da folha

MM_PER_INCH = 25.4
SHEET_DPI   = 300


def _mm_to_px(mm: float) -> int:
    return int(round(mm * SHEET_DPI / MM_PER_INCH))


@dataclass
class ProxyConfig:
    page_format:     str   = "A4"       # A4 | A3 | LETTER
    cols:            int   = 3
    rows:            int   = 3
    margin_mm:       float = MARGIN_MM
    gap_mm:          float = 2.0        # espaço entre cards
    crop_marks:      bool  = True       # marcas de corte
    crop_mark_mm:    float = 3.0        # comprimento das marcas
    include_back:    bool  = False      # gerar folha de verso
    back_image:      str   = ""         # caminho para imagem do verso
    output_dpi:      int   = SHEET_DPI


@dataclass
class SheetPage:
    image: Image.Image
    page_num: int
    is_back: bool = False


def compose_proxy(
    card_images: list[Image.Image],
    config: ProxyConfig,
    back_source: Optional[Path] = None,
) -> list[SheetPage]:
    """
    Compõe cards em páginas de folha.
    Retorna lista de SheetPage (frente + verso se solicitado).
    """
    pw_mm, ph_mm = PAGE_FORMATS.get(config.page_format.upper(), PAGE_FORMATS["A4"])
    pw = _mm_to_px(pw_mm)
    ph = _mm_to_px(ph_mm)

    card_w = _mm_to_px(CARD_W_MM)
    card_h = _mm_to_px(CARD_H_MM)
    gap    = _mm_to_px(config.gap_mm)
    margin = _mm_to_px(config.margin_mm)

    # Redimensiona cards para tamanho de impressão
    cards_resized = [c.resize((card_w, card_h), Image.LANCZOS) for c in card_images]

    cards_per_page = config.cols * config.rows
    pages: list[SheetPage] = []

    for page_idx in range(math.ceil(len(cards_resized) / cards_per_page)):
        page_img = Image.new("RGB", (pw, ph), (255, 255, 255))
        draw     = ImageDraw.Draw(page_img)

        batch = cards_resized[page_idx * cards_per_page:(page_idx + 1) * cards_per_page]

        for card_idx, card in enumerate(batch):
            col = card_idx % config.cols
            row = card_idx // config.cols
            x   = margin + col * (card_w + gap)
            y   = margin + row * (card_h + gap)
            page_img.paste(card.convert("RGB"), (x, y))

            if config.crop_marks:
                _draw_crop_marks(draw, x, y, card_w, card_h,
                                  _mm_to_px(config.crop_mark_mm))

        pages.append(SheetPage(image=page_img, page_num=page_idx + 1, is_back=False))

    # Folha(s) de verso
    if config.include_back:
        back_img = _load_back(back_source, card_w, card_h)
        back_pages = math.ceil(len(cards_resized) / cards_per_page)
        for page_idx in range(back_pages):
            page_img = Image.new("RGB", (pw, ph), (255, 255, 255))
            draw     = ImageDraw.Draw(page_img)
            batch    = cards_resized[page_idx * cards_per_page:(page_idx + 1) * cards_per_page]

            for card_idx in range(len(batch)):
                # Espelha horizontalmente para impressão frente-e-verso
                col_back = (config.cols - 1) - (card_idx % config.cols)
                row_back = card_idx // config.cols
                x = margin + col_back * (card_w + gap)
                y = margin + row_back * (card_h + gap)
                page_img.paste(back_img.convert("RGB"), (x, y))
                if config.crop_marks:
                    _draw_crop_marks(draw, x, y, card_w, card_h,
                                      _mm_to_px(config.crop_mark_mm))

            pages.append(SheetPage(image=page_img, page_num=page_idx + 1, is_back=True))

    return pages


def _load_back(path: Optional[Path], w: int, h: int) -> Image.Image:
    if path and path.exists():
        try:
            # Le os bytes em memoria (BytesIO) em vez de abrir o caminho
            # direto — evita segurar o arquivo aberto no Windows.
            with open(path, "rb") as f:
                data = f.read()
            img = Image.open(io.BytesIO(data))
            img.load()
            img = img.convert("RGBA")
            return img.resize((w, h), Image.LANCZOS)
        except Exception:
            pass
    # Fallback: verso genérico branco com borda
    img  = Image.new("RGBA", (w, h), (240, 240, 240, 255))
    draw = ImageDraw.Draw(img)
    draw.rectangle([4, 4, w - 5, h - 5], outline=(100, 100, 100), width=3)
    return img


def _draw_crop_marks(draw: ImageDraw.Draw,
                      x: int, y: int, w: int, h: int, length: int) -> None:
    """Desenha 4 marcas de corte nos cantos do card."""
    gap = 4
    color = (150, 150, 150)
    lw    = 1
    # Canto superior-esquerdo
    draw.line([(x - gap - length, y), (x - gap, y)], fill=color, width=lw)
    draw.line([(x, y - gap - length), (x, y - gap)], fill=color, width=lw)
    # Canto superior-direito
    draw.line([(x + w + gap, y), (x + w + gap + length, y)], fill=color, width=lw)
    draw.line([(x + w, y - gap - length), (x + w, y - gap)], fill=color, width=lw)
    # Canto inferior-esquerdo
    draw.line([(x - gap - length, y + h), (x - gap, y + h)], fill=color, width=lw)
    draw.line([(x, y + h + gap), (x, y + h + gap + length)], fill=color, width=lw)
    # Canto inferior-direito
    draw.line([(x + w + gap, y + h), (x + w + gap + length, y + h)], fill=color, width=lw)
    draw.line([(x + w, y + h + gap), (x + w, y + h + gap + length)], fill=color, width=lw)


# ── PDF Writer ───────────────────────────────────────────────────────────────

def save_pdf(pages: list[SheetPage], output_path: Path,
             dpi: int = SHEET_DPI) -> Path:
    """
    Salva lista de SheetPage como PDF multi-página.
    Tenta reportlab primeiro; fallback para PIL.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        return _save_pdf_reportlab(pages, output_path, dpi)
    except ImportError:
        return _save_pdf_pil(pages, output_path)


def _save_pdf_reportlab(pages: list[SheetPage], path: Path, dpi: int) -> Path:
    from reportlab.lib.units import mm
    from reportlab.pdfgen import canvas as rl_canvas
    import io

    if not pages:
        raise ValueError("Nenhuma página para gerar PDF")

    first     = pages[0].image
    pw_pt     = first.width  / dpi * 72   # pixels → pontos (72 pt = 1 inch)
    ph_pt     = first.height / dpi * 72

    c = rl_canvas.Canvas(str(path), pagesize=(pw_pt, ph_pt))

    for page in pages:
        buf = io.BytesIO()
        page.image.convert("RGB").save(buf, "JPEG", quality=95)
        buf.seek(0)
        from reportlab.lib.utils import ImageReader
        c.drawImage(ImageReader(buf), 0, 0, width=pw_pt, height=ph_pt)
        c.showPage()

    c.save()
    return path


def _save_pdf_pil(pages: list[SheetPage], path: Path) -> Path:
    """Fallback sem reportlab — usa PIL para gerar PDF."""
    if not pages:
        raise ValueError("Nenhuma página para gerar PDF")
    imgs = [p.image.convert("RGB") for p in pages]
    imgs[0].save(str(path), "PDF", save_all=True, append_images=imgs[1:])
    return path

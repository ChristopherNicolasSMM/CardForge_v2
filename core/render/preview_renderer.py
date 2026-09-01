"""
Preview Renderer — renderiza card como PIL.Image para exibição na UI.

Usa PIL diretamente (sem CairoSVG) para ser rápido na UI.
A renderização final em SVG fica em svg_builder.py.

Lógica de rendering:
  1. Cria canvas em branco (card_width_px × card_height_px)
  2. Renderiza layers em ordem de z_index
  3. Retorna PIL.Image RGBA
"""
from __future__ import annotations

import re
import textwrap
from pathlib import Path
from typing import Optional

from PIL import Image, ImageDraw, ImageFont

from ..template.models import ResolvedTemplate, Layer, LayerStyle, DEFAULT_DPI
from .font_paths import find_font_file

ROOT = Path(__file__).resolve().parent.parent.parent

# Aliases legados — nomes de fonte que não seguem "<nome_do_arquivo_sem_ttf>"
FONT_FILES = {
    "Beleren": "Beleren-Bold",
}

_font_cache: dict[tuple, ImageFont.FreeTypeFont] = {}


def _load_font(family: str, size_pt: float, weight: str = "normal", style: str = "normal",
                template_dir: Optional[Path] = None) -> ImageFont.FreeTypeFont:
    # pt → px para PIL (96 dpi de tela)
    size_px = max(8, int(size_pt * 96 / 72))
    key = (family, size_px, weight, style, str(template_dir))
    if key in _font_cache:
        return _font_cache[key]

    candidates = [family]
    if style == "italic" and "Italic" not in family:
        candidates.insert(0, family + "-Italic")
    if weight == "bold" and "Bold" not in family:
        candidates.insert(0, family + "-Bold")

    for name in candidates:
        resolved_name = FONT_FILES.get(name, name)
        fpath = find_font_file(resolved_name, template_dir)
        if fpath:
            try:
                font = ImageFont.truetype(str(fpath), size_px)
                _font_cache[key] = font
                return font
            except Exception:
                pass

    font = ImageFont.load_default()
    _font_cache[key] = font
    return font


def _hex_to_rgba(hex_color: str, alpha: int = 255) -> tuple:
    h = hex_color.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    try:
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        return (r, g, b, alpha)
    except Exception:
        return (0, 0, 0, alpha)


def _fit_image(img: Image.Image, w: int, h: int, fit: str) -> Image.Image:
    """Redimensiona imagem conforme fit: cover | contain | stretch."""
    iw, ih = img.size
    if fit == "stretch":
        return img.resize((w, h), Image.LANCZOS)
    ratio_w = w / iw
    ratio_h = h / ih
    if fit == "cover":
        ratio = max(ratio_w, ratio_h)
    else:  # contain
        ratio = min(ratio_w, ratio_h)
    new_w = int(iw * ratio)
    new_h = int(ih * ratio)
    img = img.resize((new_w, new_h), Image.LANCZOS)
    # Crop centralizado para cover
    if fit == "cover" and (new_w != w or new_h != h):
        ox = (new_w - w) // 2
        oy = (new_h - h) // 2
        img = img.crop((ox, oy, ox + w, oy + h))
    return img


def _wrap_text(text: str, font, max_width: int) -> list[str]:
    """Quebra texto respeitando largura máxima em pixels."""
    words  = text.split()
    lines: list[str] = []
    current = ""
    draw = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    for word in words:
        test = (current + " " + word).strip()
        try:
            tw = draw.textlength(test, font=font)
        except Exception:
            tw = len(test) * (getattr(font, "size", 8) * 0.6)
        if tw <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines or [""]


class PreviewRenderer:
    """
    Renderiza um único card como PIL.Image.
    Instância reutilizável por template — recria background apenas quando
    o template muda.
    """

    def __init__(self, template: ResolvedTemplate, template_dir: Path,
                 preview_dpi: int = 96) -> None:
        self.template     = template
        self.template_dir = Path(template_dir)
        self.preview_dpi  = preview_dpi
        self._bg_cache:   Optional[Image.Image] = None

    # ── Coordenadas mm → px de preview ─────────────────────────────────────

    def _px(self, mm: float) -> int:
        return int(round(mm * self.preview_dpi / 25.4))

    @property
    def card_w(self) -> int:
        return self._px(self.template.dimensions.width_mm)

    @property
    def card_h(self) -> int:
        return self._px(self.template.dimensions.height_mm)

    # ── Render principal ────────────────────────────────────────────────────

    def render(self, row: dict, color_key: str = "colorless") -> Image.Image:
        """Renderiza um card. row = dict com os campos do card."""
        # Determina cor para gradiente
        color = row.get("color", color_key) or color_key

        img  = Image.new("RGBA", (self.card_w, self.card_h), (200, 200, 200, 255))
        draw = ImageDraw.Draw(img)

        for layer in self.template.sorted_layers():
            if not layer.visible:
                continue
            try:
                self._render_layer(img, draw, layer, row, color)
            except Exception as e:
                print(f"[preview] layer '{layer.id}' erro: {e}")

        return img

    # ── Render por tipo de layer ────────────────────────────────────────────

    def _render_layer(self, img: Image.Image, draw: ImageDraw.Draw,
                      layer: Layer, row: dict, color: str) -> None:
        x = self._px(layer.x_mm)
        y = self._px(layer.y_mm)
        w = self._px(layer.width_mm)
        h = self._px(layer.height_mm)

        if layer.type == "background":
            self._draw_background(img, layer, x, y, w, h, color)
        elif layer.type == "image":
            self._draw_image(img, layer, row, x, y, w, h)
        elif layer.type in ("text", "mana"):
            value = self._get_value(layer, row)
            if value:
                self._draw_text(draw, layer, value, x, y, w, h)

    def _draw_background(self, img: Image.Image, layer: Layer,
                          x, y, w, h, color: str) -> None:
        # Tenta imagem
        if layer.source_image:
            bg_path = self.template_dir / layer.source_image
            if bg_path.exists():
                try:
                    bg = Image.open(bg_path).convert("RGBA")
                    bg = _fit_image(bg, w, h, layer.fit)
                    img.paste(bg, (x, y), bg)
                    return
                except Exception as e:
                    print(f"[preview] bg image erro: {e}")

        # Fallback: gradiente sólido
        grad = self.template.gradients.get(color) or \
               self.template.gradients.get("colorless")
        if grad and grad.stops:
            top_color   = _hex_to_rgba(grad.stops[0].color)
            bot_color   = _hex_to_rgba(grad.stops[-1].color)
            self._draw_gradient_rect(img, x, y, w, h, top_color, bot_color)
        else:
            ImageDraw.Draw(img).rectangle([x, y, x+w, y+h], fill=(180, 180, 180, 255))

    def _draw_gradient_rect(self, img, x, y, w, h, top, bot) -> None:
        for row_idx in range(h):
            t = row_idx / max(h - 1, 1)
            r = int(top[0] + (bot[0] - top[0]) * t)
            g = int(top[1] + (bot[1] - top[1]) * t)
            b = int(top[2] + (bot[2] - top[2]) * t)
            ImageDraw.Draw(img).line([(x, y + row_idx), (x + w, y + row_idx)],
                                      fill=(r, g, b, 255))

    def _draw_image(self, img: Image.Image, layer: Layer, row: dict,
                    x, y, w, h) -> None:
        art_path_str = self._get_value(layer, row)
        if not art_path_str:
            return
        # Busca relativo ao template e ao diretório de dados
        for base in (self.template_dir, Path(".")):
            p = base / art_path_str
            if p.exists():
                try:
                    art = Image.open(p).convert("RGBA")
                    art = _fit_image(art, w, h, layer.fit)
                    img.paste(art, (x, y), art)
                except Exception as e:
                    print(f"[preview] art erro: {e}")
                return

    def _draw_text(self, draw: ImageDraw.Draw, layer: Layer,
                   text: str, x, y, w, h) -> None:
        s    = layer.style
        size_px = max(6, int(s.font_size_pt * self.preview_dpi / 72))
        font = _load_font(s.font_family, s.font_size_pt, s.font_weight, s.font_style,
                           template_dir=self.template_dir)
        lh   = max(size_px + 2, int(s.line_height_resolved * self.preview_dpi / 72))
        color = _hex_to_rgba(s.color)

        lines = text.split("\n") if layer.multiline else [text]
        if layer.multiline:
            wrapped: list[str] = []
            for line in lines:
                wrapped.extend(_wrap_text(line, font, w) if line.strip() else [""])
            lines = wrapped

        y_off = y
        for line in lines:
            if y_off + lh > y + h + lh:
                break
            if not line.strip():
                y_off += lh
                continue
            try:
                tw = draw.textlength(line, font=font)
            except Exception:
                tw = len(line) * size_px * 0.6

            if s.align == "center":
                tx = x + (w - tw) // 2
            elif s.align == "right":
                tx = x + w - int(tw)
            else:
                tx = x

            draw.text((tx, y_off), line, font=font, fill=color)
            y_off += lh

    @staticmethod
    def _get_value(layer: Layer, row: dict) -> str:
        if layer.field == "" or layer.field == "static":
            return layer.static_text
        # Busca direta
        if layer.field in row:
            return row[layer.field]
        # Case-insensitive fallback
        lf = layer.field.lower()
        for k, v in row.items():
            if k.lower() == lf:
                return v
        return ""

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

import io
import re
import textwrap
from pathlib import Path
from typing import Optional

from PIL import Image, ImageDraw, ImageFont

from ..template.models import ResolvedTemplate, Layer, LayerStyle, DEFAULT_DPI
from .font_paths import find_font_file
from . import mana_symbols

ROOT = Path(__file__).resolve().parent.parent.parent

# Aliases legados — nomes de fonte que não seguem "<nome_do_arquivo_sem_ttf>"
FONT_FILES = {
    "Beleren": "Beleren-Bold",
}

_font_cache: dict[tuple, ImageFont.FreeTypeFont] = {}
_icon_cache: dict[tuple, Optional[Image.Image]] = {}


def clear_font_cache() -> None:
    """Esvazia o cache de fontes carregadas.

    Chamado antes de operações que apagam pastas de fontes em disco (ex:
    excluir uma coleção). Na prática, como _load_font já lê o .ttf pra
    memória (BytesIO) em vez de manter o arquivo aberto, isso não é mais
    estritamente necessário pra liberar o arquivo no Windows — mas mantém o
    cache limpo caso a mesma fonte seja recriada com conteúdo diferente
    logo em seguida."""
    _font_cache.clear()


def _load_font(family: str, size_px: int, weight: str = "normal", style: str = "normal",
                template_dir: Optional[Path] = None) -> ImageFont.FreeTypeFont:
    """Carrega a fonte já no tamanho em pixels correto pro DPI da renderização
    atual. Importante: quem chama define size_px (normalmente
    `font_size_pt * dpi_real / 72`) — esta função NÃO faz sua própria
    conversão pt→px, pra não divergir do DPI real usado pela imagem (esse foi,
    por muito tempo, o motivo do texto sair menor do que o esperado: a fonte
    era carregada assumindo 96 DPI fixo, enquanto a imagem podia estar sendo
    gerada a 110/180/300 DPI — a caixa do texto ficava no tamanho certo, mas a
    fonte dentro dela vinha desproporcionalmente pequena)."""
    size_px = max(6, int(size_px))
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
                # Importante: carrega os bytes e fecha o arquivo imediatamente,
                # em vez de passar o caminho direto pro Pillow. ImageFont.truetype(path)
                # mantém o arquivo aberto (via FreeType) pelo tempo de vida do
                # objeto de fonte — no Windows isso trava o arquivo (e a pasta
                # que o contém) até o processo terminar, impedindo excluir a
                # coleção depois. Carregando de um BytesIO, o arquivo em disco
                # fica livre assim que a leitura termina.
                data = fpath.read_bytes()
                font = ImageFont.truetype(io.BytesIO(data), size_px)
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


def _measure_text(draw: ImageDraw.Draw, text: str, font, spacing_px: int = 0) -> float:
    """Largura do texto em pixels, já considerando espaçamento extra entre letras."""
    if not text:
        return 0
    if spacing_px == 0:
        try:
            return draw.textlength(text, font=font)
        except Exception:
            return len(text) * getattr(font, "size", 8) * 0.6
    total = 0.0
    for ch in text:
        try:
            total += draw.textlength(ch, font=font)
        except Exception:
            total += getattr(font, "size", 8) * 0.6
        total += spacing_px
    return max(0.0, total - spacing_px)  # sem espaçamento depois do último caractere


def _draw_text_spaced(draw: ImageDraw.Draw, x, y, text: str, font, fill, spacing_px: int = 0) -> None:
    """Desenha uma linha de texto, opcionalmente com espaçamento extra entre letras.
    PIL não tem tracking nativo — sem espaçamento, desenha a linha inteira de
    uma vez (mais rápido); com espaçamento, desenha caractere por caractere."""
    if spacing_px == 0:
        draw.text((x, y), text, font=font, fill=fill)
        return
    cx = x
    for ch in text:
        draw.text((cx, y), ch, font=font, fill=fill)
        try:
            cw = draw.textlength(ch, font=font)
        except Exception:
            cw = getattr(font, "size", 8) * 0.6
        cx += cw + spacing_px


def _wrap_text(text: str, font, max_width: int, spacing_px: int = 0) -> list[str]:
    """Quebra texto respeitando largura máxima em pixels."""
    words  = text.split()
    lines: list[str] = []
    current = ""
    draw = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    for word in words:
        test = (current + " " + word).strip()
        tw = _measure_text(draw, test, font, spacing_px)
        if tw <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines or [""]


def _icon_image(png_path: Path, size_px: int) -> Optional[Image.Image]:
    """Ícone de símbolo (mana etc.) já redimensionado, com cache em memória.
    Reaproveita _open_image (leitura via BytesIO), então não trava arquivo
    no Windows — mesmo cuidado já adotado no resto deste módulo."""
    key = (str(png_path), size_px)
    if key in _icon_cache:
        return _icon_cache[key]
    try:
        img = _open_image(png_path).convert("RGBA")
        img = img.resize((size_px, size_px), Image.LANCZOS)
    except Exception:
        img = None
    _icon_cache[key] = img
    return img


def _wrap_rich_text(text: str, font, max_width: int, spacing_px: int,
                     icon_size: int) -> list[list[tuple[str, str]]]:
    """Quebra texto em linhas respeitando largura máxima em pixels, tratando
    notação de símbolo `{X}` (estilo MTG) como uma unidade atômica do
    tamanho de um ícone — igual uma palavra, só que com largura fixa
    (icon_size) em vez de largura medida por fonte."""
    units = mana_symbols.tokenize(text)
    draw = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    try:
        space_w = draw.textlength(" ", font=font)
    except Exception:
        space_w = getattr(font, "size", 8) * 0.3

    lines: list[list[tuple[str, str]]] = []
    current: list[tuple[str, str]] = []
    current_w = 0.0
    for kind, val in units:
        uw = float(icon_size) if kind == "symbol" else _measure_text(draw, val, font, spacing_px)
        add_w = uw + (space_w if current else 0)
        if current and current_w + add_w > max_width:
            lines.append(current)
            current = [(kind, val)]
            current_w = uw
        else:
            current.append((kind, val))
            current_w += add_w
    lines.append(current)
    return lines or [[]]


def _measure_rich_line(draw: ImageDraw.Draw, units: list[tuple[str, str]], font,
                        spacing_px: int, icon_size: int, space_w: float) -> float:
    total = 0.0
    for i, (kind, val) in enumerate(units):
        total += float(icon_size) if kind == "symbol" else _measure_text(draw, val, font, spacing_px)
        if i < len(units) - 1:
            total += space_w
    return total


def _draw_rich_line(draw: ImageDraw.Draw, img: Image.Image, x: float, y: float,
                     units: list[tuple[str, str]], font, fill, spacing_px: int,
                     icon_size: int, icon_y: float, space_w: float) -> None:
    """Desenha uma linha mista de texto e ícones lado a lado. Símbolo sem
    PNG resolvido (não deveria acontecer — tokenize() já filtra — mas fica
    como rede de segurança) simplesmente não desenha nada nesse trecho, em
    vez de quebrar o card inteiro."""
    cx = x
    for kind, val in units:
        if kind == "symbol":
            png = mana_symbols.resolve_icon_png(val)
            icon = _icon_image(png, icon_size) if png else None
            if icon:
                img.paste(icon, (int(cx), int(icon_y)), icon)
            cx += icon_size
        else:
            _draw_text_spaced(draw, cx, y, val, font, fill, spacing_px)
            cx += _measure_text(draw, val, font, spacing_px)
        cx += space_w


def _open_image(path: Path) -> Image.Image:
    """Abre uma imagem a partir dos bytes em memória, não do caminho direto.

    Mesmo motivo do BytesIO em _load_font: evita manter um handle aberto pro
    arquivo no disco (o que trava exclusão de pastas no Windows)."""
    with open(path, "rb") as f:
        data = f.read()
    img = Image.open(io.BytesIO(data))
    img.load()
    return img


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
                self._draw_text(img, draw, layer, value, x, y, w, h)

    def _draw_background(self, img: Image.Image, layer: Layer,
                          x, y, w, h, color: str) -> None:
        # Tenta imagem
        if layer.source_image:
            bg_path = self._resolve_asset_path(layer.source_image)
            if bg_path:
                try:
                    bg = _open_image(bg_path).convert("RGBA")
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

    def _resolve_asset_path(self, value: str) -> Optional[Path]:
        """Procura um arquivo de imagem em todos os lugares onde ele pode
        estar: dentro da pasta do template, na biblioteca de imagens da
        coleção ativa (assets/library/, onde a tela de Dados salva os
        uploads), e por fim no diretório de trabalho do processo."""
        candidates = [self.template_dir / value]
        # collections/<coleção>/templates/<nome> -> collections/<coleção>/assets/library
        try:
            collection_dir = self.template_dir.parent.parent
            candidates.append(collection_dir / "assets" / "library" / value)
        except Exception:
            pass
        candidates.append(Path(".") / value)
        for p in candidates:
            if p.exists():
                return p
        return None

    def _draw_image(self, img: Image.Image, layer: Layer, row: dict,
                    x, y, w, h) -> None:
        # Imagem fixa: quando o campo do dataset está vazio, a camada usa uma
        # imagem fixa (definida no editor) em vez de buscar um valor por card —
        # útil pra ícones, selos ou marcas d'água iguais em todo card.
        if layer.field in ("", "static"):
            if not layer.source_image:
                return
            p = self._resolve_asset_path(layer.source_image)
            if p:
                try:
                    art = _open_image(p).convert("RGBA")
                    art = _fit_image(art, w, h, layer.fit)
                    img.paste(art, (x, y), art)
                except Exception as e:
                    print(f"[preview] imagem fixa erro: {e}")
            return

        art_path_str = self._get_value(layer, row)
        if not art_path_str:
            return
        p = self._resolve_asset_path(art_path_str)
        if p:
            try:
                art = _open_image(p).convert("RGBA")
                art = _fit_image(art, w, h, layer.fit)
                img.paste(art, (x, y), art)
            except Exception as e:
                print(f"[preview] art erro: {e}")

    def _draw_text(self, img: Image.Image, draw: ImageDraw.Draw, layer: Layer,
                   text: str, x, y, w, h) -> None:
        s    = layer.style
        size_px = max(6, int(s.font_size_pt * self.preview_dpi / 72))
        font = _load_font(s.font_family, size_px, s.font_weight, s.font_style,
                           template_dir=self.template_dir)
        lh   = max(size_px + 2, int(s.line_height_resolved * self.preview_dpi / 72))
        color = _hex_to_rgba(s.color)
        spacing_px = int(round(s.letter_spacing_pt * self.preview_dpi / 72))
        # Ícone de símbolo (notação {X}) desenhado um pouco menor que a
        # altura da linha, pra não colar na linha de cima/baixo.
        icon_size = max(8, int(lh * 0.85))

        raw_lines = text.split("\n") if layer.multiline else [text]
        all_lines: list[list[tuple[str, str]]] = []
        for line in raw_lines:
            if not line.strip():
                all_lines.append([])
                continue
            if layer.multiline:
                all_lines.extend(_wrap_rich_text(line, font, w, spacing_px, icon_size))
            else:
                all_lines.append(mana_symbols.tokenize(line))

        try:
            space_w = draw.textlength(" ", font=font)
        except Exception:
            space_w = getattr(font, "size", 8) * 0.3

        # Alinhamento vertical: posiciona o bloco de texto (todas as linhas)
        # dentro da caixa da camada, conforme "topo" (padrão) / "centro" / "base".
        total_h = len(all_lines) * lh
        if s.vertical_align == "middle":
            y_off = y + max(0, (h - total_h) // 2)
        elif s.vertical_align == "bottom":
            y_off = y + max(0, h - total_h)
        else:
            y_off = y

        for units in all_lines:
            if y_off + lh > y + h + lh:
                break
            if not units:
                y_off += lh
                continue
            tw = _measure_rich_line(draw, units, font, spacing_px, icon_size, space_w)

            if s.align == "center":
                tx = x + (w - tw) // 2
            elif s.align == "right":
                tx = x + w - int(tw)
            else:
                tx = x

            icon_y = y_off + max(0, (lh - icon_size) // 2)
            _draw_rich_line(draw, img, tx, y_off, units, font, color,
                             spacing_px, icon_size, icon_y, space_w)
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

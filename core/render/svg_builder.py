"""
SVG Builder — gera um SVG completo por card.

Cada layer vira um elemento SVG adequado:
  background → <image> ou <rect> com gradiente
  image      → <image>
  text       → <text> com <tspan> por linha
  mana       → <text> simples (ícones são inline base64)
"""
from __future__ import annotations

import base64
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional

from PIL import Image, ImageDraw

from ..template.models import ResolvedTemplate, Layer, LayerStyle, DEFAULT_DPI
from .font_paths import resolve_font_dirs
from .preview_renderer import _load_font
from . import mana_symbols
from ..paths import resource_root

ROOT       = resource_root()
FONTS_DIR  = ROOT / "assets" / "fonts"


def _measure_mm(text: str, font) -> float:
    """Largura de um texto em mm, usando as métricas reais da fonte (via
    PIL) só para posicionar os elementos — o desenho em si continua sendo
    vetorial (<text>), o PIL entra aqui apenas como régua."""
    if not text:
        return 0.0
    draw = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    try:
        px = draw.textlength(text, font=font)
    except Exception:
        px = len(text) * getattr(font, "size", 8) * 0.6
    return px * 25.4 / DEFAULT_DPI


def _merge_word_runs(units: list[tuple[str, str]]) -> list[tuple[str, str]]:
    """Agrupa unidades ('word', ...) consecutivas de tokenize() num único
    trecho de texto corrido, unidas por espaço — pra virar um <text> só em
    vez de um por palavra. Unidades ('symbol', ...) continuam separadas.
    Ex: [('word','Add'), ('word','your')] -> [('word','Add your')]."""
    runs: list[tuple[str, str]] = []
    buf: list[str] = []
    for kind, val in units:
        if kind == "word":
            buf.append(val)
        else:
            if buf:
                runs.append(("word", " ".join(buf)))
                buf = []
            runs.append((kind, val))
    if buf:
        runs.append(("word", " ".join(buf)))
    return runs


def _escape(text: str) -> str:
    return (text
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;"))


def _b64_file(path: Path) -> str:
    return base64.b64encode(path.read_bytes()).decode()


def _font_css(fonts_dirs: list[Path]) -> str:
    rules = []
    seen: set[str] = set()
    for fonts_dir in fonts_dirs:
        for ttf in sorted(fonts_dir.glob("*.ttf")):
            if ttf.stat().st_size == 0 or ttf.stem in seen:
                continue
            seen.add(ttf.stem)
            b64   = _b64_file(ttf)
            name  = ttf.stem
            style = "italic" if "italic" in name.lower() else "normal"
            rules.append(
                f"@font-face {{\n"
                f"  font-family: '{name}';\n"
                f"  font-style: {style};\n"
                f"  src: url(data:font/truetype;base64,{b64}) format('truetype');\n"
                f"}}"
            )
    return "\n".join(rules)


def _mm(val: float) -> str:
    """Tamanho físico com sufixo de unidade — usar SOMENTE para o
    width/height do elemento <svg> raiz (que define o tamanho real de
    impressão do documento)."""
    return f"{round(val, 3)}mm"


PT_TO_MM = 25.4 / 72


def _u(val: float) -> str:
    """Coordenada em 'unidade de usuário' do SVG — um número puro, SEM
    sufixo de unidade.

    Importante: o viewBox deste documento é declarado com números que
    numericamente equivalem aos milímetros do card (ex:
    viewBox="0 0 63.0 88.0" para um card de 63×88mm) — ou seja, 1 unidade
    de usuário == 1mm, por convenção deste projeto, não por regra do SVG.

    Um valor com sufixo de unidade explícito (ex: "10mm" ou "10pt") NÃO
    respeita essa convenção: o SVG resolve unidades absolutas (mm, pt, in,
    cm) usando a referência fixa de 96 px por polegada, independente do
    viewBox — então "10mm" vira ~37.8 unidades de usuário (10 × 96/25.4),
    não 10. Isso deslocava qualquer elemento posicionado a mais de ~15mm
    da origem para fora da área visível do card (confirmado
    empiricamente — ver docs/tech/doc-tecnico-mtg-symbols-frames.md,
    seção 11.3/12). A correção é sempre emitir número puro aqui."""
    return str(round(val, 3))


class SVGBuilder:
    """Constrói o SVG de um card a partir de template + row de dados."""

    def __init__(self, template: ResolvedTemplate, template_dir: Path) -> None:
        self.template     = template
        self.template_dir = Path(template_dir)
        self._font_css    = _font_css(resolve_font_dirs(self.template_dir))
        self._icon_cache: dict[str, str] = {}

    def _resolve_asset_path(self, value: str) -> Optional[Path]:
        """Mesma lógica de busca do PreviewRenderer — pasta do template,
        biblioteca de imagens da coleção ativa, depois diretório de trabalho."""
        candidates = [self.template_dir / value]
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

    def build(self, row: dict, color_key: str = "colorless") -> str:
        """Retorna string SVG completo para o card."""
        dims  = self.template.dimensions
        W     = _mm(dims.width_mm)
        H     = _mm(dims.height_mm)
        color = row.get("color") or color_key

        svg = ET.Element("svg", {
            "xmlns":      "http://www.w3.org/2000/svg",
            "xmlns:xlink":"http://www.w3.org/1999/xlink",
            "width":  W, "height": H,
            "viewBox": f"0 0 {dims.width_mm} {dims.height_mm}",
        })

        # <defs>
        defs = ET.SubElement(svg, "defs")
        style_el = ET.SubElement(defs, "style")
        style_el.text = self._font_css

        # Gradientes
        for gid, gdef in self.template.gradients.items():
            grad = ET.SubElement(defs, "linearGradient", {
                "id": f"grad_{gid}", "x1": "0", "y1": "0", "x2": "0", "y2": "1",
            })
            for stop in gdef.stops:
                ET.SubElement(grad, "stop", {
                    "offset": stop.offset, "stop-color": stop.color,
                })

        # Layers
        for layer in self.template.sorted_layers():
            if not layer.visible:
                continue
            if not self._check_condition(layer, row):
                continue
            try:
                self._add_layer(svg, layer, row, color)
            except Exception as e:
                print(f"[svg] layer '{layer.id}': {e}")

        return '<?xml version="1.0" encoding="UTF-8"?>\n' + \
               ET.tostring(svg, encoding="unicode")

    # ── Layers ──────────────────────────────────────────────────────────────

    def _add_layer(self, svg: ET.Element, layer: Layer,
                   row: dict, color: str) -> None:
        x  = _u(layer.x_mm)
        y  = _u(layer.y_mm)
        w  = _u(layer.width_mm)
        h  = _u(layer.height_mm)

        if layer.type == "background":
            self._add_background(svg, layer, x, y, w, h, color)
        elif layer.type == "image":
            self._add_image(svg, layer, row, x, y, w, h)
        elif layer.type in ("text", "mana"):
            value = self._get_value(layer, row)
            if value:
                self._add_text(svg, layer, value, layer.x_mm, layer.y_mm,
                                layer.width_mm, layer.height_mm)

    def _add_background(self, svg, layer, x, y, w, h, color) -> None:
        # Tenta imagem
        if layer.source_image:
            bg_path = self._resolve_asset_path(layer.source_image)
            if bg_path and bg_path.stat().st_size > 0:
                b64  = _b64_file(bg_path)
                mime = self._mime(bg_path)
                ET.SubElement(svg, "image", {
                    "id": layer.id,
                    "x": x, "y": y, "width": w, "height": h,
                    "href": f"data:{mime};base64,{b64}",
                    "preserveAspectRatio": "xMidYMid slice",
                })
                return

        # Fallback: gradiente SVG
        fill = f"url(#grad_{color})"
        if color not in self.template.gradients:
            fill = f"url(#grad_colorless)"
        ET.SubElement(svg, "rect", {
            "id": layer.id,
            "x": x, "y": y, "width": w, "height": h,
            "fill": fill,
        })

    def _add_image(self, svg, layer, row, x, y, w, h) -> None:
        # Imagem fixa: campo vazio = usa layer.source_image em vez de buscar
        # no dataset (mesma convenção do PreviewRenderer).
        if layer.field in ("", "static"):
            val = layer.source_image
        else:
            val = self._get_value(layer, row)
        if not val:
            return
        p = self._resolve_asset_path(val)
        if p:
            b64  = _b64_file(p)
            mime = self._mime(p)
            ET.SubElement(svg, "image", {
                "id": layer.id,
                "x": x, "y": y, "width": w, "height": h,
                "href": f"data:{mime};base64,{b64}",
                "preserveAspectRatio":
                    "xMidYMid slice" if layer.fit == "cover" else "xMidYMid meet",
            })
            return

    def _add_text(self, svg, layer, text, x_mm, y_mm, w_mm, h_mm) -> None:
        s = layer.style
        lines = text.split("\n") if layer.multiline else [text]

        # Alinhamento vertical: desloca a linha de base da primeira linha
        # conforme "topo" (padrão, mesmo comportamento de sempre) / "centro" / "base".
        pt_to_mm = PT_TO_MM
        lh_mm = s.line_height_resolved * pt_to_mm
        total_h_mm = len(lines) * lh_mm
        if s.vertical_align == "middle":
            start_y_mm = y_mm + max(0.0, (h_mm - total_h_mm) / 2)
        elif s.vertical_align == "bottom":
            start_y_mm = y_mm + max(0.0, h_mm - total_h_mm)
        else:
            start_y_mm = y_mm

        # Linhas sem nenhuma notação de símbolo reconhecida seguem o
        # caminho original — um <text> com <tspan> por linha. Zero mudança
        # de comportamento pra templates que não usam símbolos.
        if not any(mana_symbols.has_symbols(line) for line in lines):
            self._add_plain_text(svg, layer, lines, x_mm, start_y_mm, lh_mm)
            return

        self._add_rich_text(svg, layer, lines, x_mm, start_y_mm, w_mm, lh_mm)

    def _add_plain_text(self, svg, layer, lines, x_mm, start_y_mm, lh_mm) -> None:
        s = layer.style
        anchor = {"left": "start", "center": "middle", "right": "end"}.get(s.align, "start")
        attrs = {
            "id":          layer.id,
            "x":           _u(x_mm),
            "y":           _u(start_y_mm),
            "font-family": s.font_family,
            "font-size":   _u(s.font_size_pt * PT_TO_MM),
            "font-weight": s.font_weight,
            "font-style":  s.font_style,
            "fill":        s.color,
            "text-anchor": anchor,
        }
        if s.letter_spacing_pt:
            attrs["letter-spacing"] = _u(s.letter_spacing_pt * PT_TO_MM)

        text_el = ET.SubElement(svg, "text", attrs)

        dy = "0"
        for line in lines:
            tspan = ET.SubElement(text_el, "tspan", {"x": _u(x_mm), "dy": dy})
            tspan.text = _escape(line)
            dy = _u(lh_mm)

    def _add_rich_text(self, svg, layer, lines, x_mm, start_y_mm, w_mm, lh_mm) -> None:
        """Variante usada quando a(s) linha(s) contêm notação `{X}` de
        símbolo. SVG <tspan> não suporta intercalar imagens no meio do
        fluxo de texto, então a linha é quebrada em "trechos": sequências
        de palavras (desenhadas como um único <text> corrido — o próprio
        visualizador SVG cuida do espaçamento interno, então o resultado
        não depende de nossa medição bater exatamente com a fonte que
        efetivamente for usada pra render) intercaladas com símbolos
        (<image>, tamanho fixo em mm, não depende de fonte nenhuma).

        Nota: só a posição INICIAL de cada trecho de texto é calculada por
        estimativa (via PIL, usada como régua — ver _measure_mm). Se a
        fonte real do visualizador tiver métricas um pouco diferentes da
        usada pra medir, o pior caso é um trecho começar um pouco cedo ou
        tarde — não sobreposição de palavra em palavra, porque dentro de
        um mesmo trecho quem posiciona letra a letra é o próprio
        visualizador, com a fonte que ele de fato carregou."""
        s = layer.style
        font = _load_font(s.font_family, max(6, int(s.font_size_pt * DEFAULT_DPI / 72)),
                           s.font_weight, s.font_style)
        icon_size_mm = lh_mm * 0.85
        space_mm = _measure_mm(" ", font)

        dy_mm = 0.0
        for li, line in enumerate(lines):
            line_y_mm = start_y_mm + dy_mm
            runs = _merge_word_runs(mana_symbols.tokenize(line))
            widths_mm = [icon_size_mm if k == "symbol" else _measure_mm(v, font)
                         for k, v in runs]
            total_line_mm = sum(widths_mm) + space_mm * max(0, len(runs) - 1)

            if s.align == "center":
                cursor = x_mm + (w_mm - total_line_mm) / 2
            elif s.align == "right":
                cursor = x_mm + w_mm - total_line_mm
            else:
                cursor = x_mm

            for ri, ((kind, val), width_mm) in enumerate(zip(runs, widths_mm)):
                if kind == "symbol":
                    png = mana_symbols.resolve_icon_png(val)
                    if png:
                        b64 = _b64_file(png)
                        # Aproxima o topo do ícone à linha de base do texto —
                        # heurística simples, não uma medida tipográfica exata.
                        icon_y_mm = line_y_mm - icon_size_mm * 0.78
                        ET.SubElement(svg, "image", {
                            "id": f"{layer.id}_sym{li}_{ri}",
                            "x": _u(cursor), "y": _u(icon_y_mm),
                            "width": _u(icon_size_mm), "height": _u(icon_size_mm),
                            "href": f"data:image/png;base64,{b64}",
                        })
                else:
                    t = ET.SubElement(svg, "text", {
                        "id":          f"{layer.id}_w{li}_{ri}",
                        "x":           _u(cursor),
                        "y":           _u(line_y_mm),
                        "font-family": s.font_family,
                        "font-size":   _u(s.font_size_pt * PT_TO_MM),
                        "font-weight": s.font_weight,
                        "font-style":  s.font_style,
                        "fill":        s.color,
                    })
                    t.text = _escape(val)
                cursor += width_mm + space_mm

            dy_mm += lh_mm

    # ── Helpers ─────────────────────────────────────────────────────────────

    @staticmethod
    def _get_value(layer: Layer, row: dict) -> str:
        if not layer.field or layer.field == "static":
            return layer.static_text
        if layer.field in row:
            return row[layer.field]
        lf = layer.field.lower()
        for k, v in row.items():
            if k.lower() == lf:
                return v
        return ""

    @staticmethod
    def _check_condition(layer: Layer, row: dict) -> bool:
        c = layer.condition
        if not c:
            return True
        if c == "has_pt":
            return bool(row.get("power") and row.get("toughness"))
        if c == "has_flavor":
            return bool(row.get("flavor_text"))
        return True

    @staticmethod
    def _mime(path: Path) -> str:
        ext = path.suffix.lower()
        return {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg",
                "webp": "image/webp", "svg": "image/svg+xml"}.get(ext.lstrip("."), "image/png")


# ── Exportação em lote ───────────────────────────────────────────────────────

def build_svg(template: ResolvedTemplate, template_dir: Path,
              row: dict, color_key: str = "colorless") -> str:
    return SVGBuilder(template, template_dir).build(row, color_key)


def save_svg(svg_str: str, name: str, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    safe = re.sub(r'[^\w\-]', '_', name)
    dest = output_dir / f"{safe}.svg"
    dest.write_text(svg_str, encoding="utf-8")
    return dest

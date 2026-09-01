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

from ..template.models import ResolvedTemplate, Layer, LayerStyle, DEFAULT_DPI
from .font_paths import resolve_font_dirs

ROOT       = Path(__file__).resolve().parent.parent.parent
FONTS_DIR  = ROOT / "assets" / "fonts"
ICONS_DIR  = ROOT / "assets" / "icons"


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
    return f"{round(val, 3)}mm"


class SVGBuilder:
    """Constrói o SVG de um card a partir de template + row de dados."""

    def __init__(self, template: ResolvedTemplate, template_dir: Path) -> None:
        self.template     = template
        self.template_dir = Path(template_dir)
        self._font_css    = _font_css(resolve_font_dirs(self.template_dir))
        self._icon_cache: dict[str, str] = {}

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
        x  = _mm(layer.x_mm)
        y  = _mm(layer.y_mm)
        w  = _mm(layer.width_mm)
        h  = _mm(layer.height_mm)

        if layer.type == "background":
            self._add_background(svg, layer, x, y, w, h, color)
        elif layer.type == "image":
            self._add_image(svg, layer, row, x, y, w, h)
        elif layer.type in ("text", "mana"):
            value = self._get_value(layer, row)
            if value:
                self._add_text(svg, layer, value, x, y, w, h)

    def _add_background(self, svg, layer, x, y, w, h, color) -> None:
        # Tenta imagem
        if layer.source_image:
            bg_path = self.template_dir / layer.source_image
            if bg_path.exists() and bg_path.stat().st_size > 0:
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
        val = self._get_value(layer, row)
        if not val:
            return
        for base in (self.template_dir, Path(".")):
            p = Path(base) / val
            if p.exists():
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

    def _add_text(self, svg, layer, text, x, y, w, h) -> None:
        s = layer.style
        font_size = f"{s.font_size_pt}pt"
        anchor = {"left": "start", "center": "middle", "right": "end"}.get(s.align, "start")

        text_el = ET.SubElement(svg, "text", {
            "id":          layer.id,
            "x":           x,
            "y":           y,
            "font-family": s.font_family,
            "font-size":   font_size,
            "font-weight": s.font_weight,
            "font-style":  s.font_style,
            "fill":        s.color,
            "text-anchor": anchor,
        })

        lines = text.split("\n") if layer.multiline else [text]
        lh    = _mm(s.line_height_resolved)
        dy    = "0"
        for line in lines:
            tspan = ET.SubElement(text_el, "tspan", {"x": x, "dy": dy})
            tspan.text = _escape(line)
            dy = lh

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

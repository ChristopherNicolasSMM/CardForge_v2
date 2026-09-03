"""
Modelos de dados do sistema de templates.

Hierarquia:
  ResolvedTemplate  ← resultado final após herança resolvida
    CardDimensions
    GradientDef (dicionário de gradientes por cor)
    Layer  (N camadas ordenadas por z_index)
      LayerStyle  (tipografia e visual)
"""
from __future__ import annotations
from dataclasses import dataclass, field as dc_field
from typing import Optional, Any

# ── Constantes de conversão ─────────────────────────────────────────────────
MM_PER_INCH  = 25.4
DEFAULT_DPI  = 300

def mm_to_px(mm: float, dpi: int = DEFAULT_DPI) -> int:
    return int(round(mm * dpi / MM_PER_INCH))

def px_to_mm(px: int, dpi: int = DEFAULT_DPI) -> float:
    return round(px * MM_PER_INCH / dpi, 3)


@dataclass
class CardDimensions:
    width_mm:  float = 63.0
    height_mm: float = 88.0
    dpi:       int   = DEFAULT_DPI

    @property
    def width_px(self)  -> int: return mm_to_px(self.width_mm,  self.dpi)
    @property
    def height_px(self) -> int: return mm_to_px(self.height_mm, self.dpi)

    def to_dict(self) -> dict:
        return {"width_mm": self.width_mm, "height_mm": self.height_mm, "dpi": self.dpi}

    @classmethod
    def from_dict(cls, d: dict) -> "CardDimensions":
        return cls(
            width_mm  = float(d.get("width_mm",  d.get("card_width_mm",  63))),
            height_mm = float(d.get("height_mm", d.get("card_height_mm", 88))),
            dpi       = int(d.get("dpi", DEFAULT_DPI)),
        )


@dataclass
class GradientStop:
    offset: str   # "0%", "50%", "100%"
    color:  str   # "#RRGGBB"

    def to_dict(self) -> dict:
        return {"offset": self.offset, "color": self.color}

    @classmethod
    def from_raw(cls, raw) -> "GradientStop":
        if isinstance(raw, (list, tuple)):
            return cls(offset=raw[0], color=raw[1])
        return cls(**raw)


@dataclass
class GradientDef:
    id:    str
    stops: list[GradientStop] = dc_field(default_factory=list)

    def to_dict(self) -> dict:
        return {"id": self.id, "stops": [s.to_dict() for s in self.stops]}


@dataclass
class LayerStyle:
    font_family: str   = "Beleren-Bold"
    font_size_pt: float = 10.0
    font_weight:  str  = "normal"   # "normal" | "bold"
    font_style:   str  = "normal"   # "normal" | "italic"
    color:        str  = "#111111"
    align:        str  = "left"     # "left" | "center" | "right"
    vertical_align: str = "top"     # "top" | "middle" | "bottom" — posição do bloco de texto dentro da caixa
    letter_spacing_pt: float = 0.0  # espaço extra entre letras, em pt (0 = padrão da fonte)
    line_height_pt: float = 0.0     # 0 = auto (font_size * 1.35)

    @property
    def line_height_resolved(self) -> float:
        return self.line_height_pt if self.line_height_pt > 0 else self.font_size_pt * 1.35

    def to_dict(self) -> dict:
        return {
            "font_family":    self.font_family,
            "font_size_pt":   self.font_size_pt,
            "font_weight":    self.font_weight,
            "font_style":     self.font_style,
            "color":          self.color,
            "align":          self.align,
            "vertical_align": self.vertical_align,
            "letter_spacing_pt": self.letter_spacing_pt,
            "line_height_pt": self.line_height_pt,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "LayerStyle":
        """
        Lê o estilo de um dict JSON.

        Regras de conversão de font_size:
        • "font_size_pt" presente e entre 3–60 → usa diretamente (formato novo)
        • "font_size_pt" presente mas fora da faixa → pode ser pixel legado → converte
        • Só "font_size" presente (pixels legado) → converte px→pt (× 0.75)
        • Fallback seguro: 9pt
        """
        # Prioridade: font_size_pt (novo) > font_size (legado em px)
        if "font_size_pt" in d:
            size = float(d["font_size_pt"])
            # Se já está em faixa razoável para pt (3..60), usa diretamente
            if 3.0 <= size <= 60.0:
                pass   # ok
            elif size > 60:
                # Provavelmente era px; converte
                size = round(size * 0.75, 1)
            # size < 3 → pode ser erro de edição → usa fallback
            else:
                size = 9.0
        elif "font_size" in d:
            # Formato antigo: tamanho em pixels
            size = round(float(d["font_size"]) * 0.75, 1)
        else:
            size = 9.0

        # line_height
        lh_raw = d.get("line_height_pt", d.get("line_height", 0))
        lh = float(lh_raw)
        if lh > 60:
            lh = round(lh * 0.75, 1)  # converte px legado

        return cls(
            font_family    = d.get("font_family", "Beleren-Bold"),
            font_size_pt   = size,
            font_weight    = d.get("font_weight", "normal"),
            font_style     = d.get("font_style",  "normal"),
            color          = d.get("color",        "#111111"),
            align          = d.get("align",        d.get("text_align", "left")),
            vertical_align = d.get("vertical_align", "top"),
            letter_spacing_pt = float(d.get("letter_spacing_pt", 0.0)),
            line_height_pt = lh,
        )


@dataclass
class Layer:
    """Uma camada do card. Posições SEMPRE em mm internamente."""
    id:          str
    type:        str        # "background" | "image" | "text" | "mana" | "shape"
    label:       str        = ""
    field:       str        = ""     # coluna do dataset
    static_text: str        = ""     # para type="text" com field=""
    condition:   str        = ""     # "has_pt", "has_flavor", etc.

    # Posição em mm
    x_mm:      float = 0.0
    y_mm:      float = 0.0
    width_mm:  float = 63.0
    height_mm: float = 10.0

    z_index:   int   = 0
    visible:   bool  = True
    multiline: bool  = False
    locked:    bool  = False   # trava a camada contra clique/arraste no editor (não afeta a renderização)

    # Para layers de imagem
    fit:             str = "cover"   # "cover" | "contain" | "stretch"
    source_image:    str = ""        # caminho relativo ao template
    source_gradient: str = ""        # id do gradiente (bg dinâmico)

    style: LayerStyle = dc_field(default_factory=lambda: LayerStyle())

    # Propriedades em px (calculadas a partir de mm + dpi)
    def x_px(self, dpi=DEFAULT_DPI)      -> int: return mm_to_px(self.x_mm,      dpi)
    def y_px(self, dpi=DEFAULT_DPI)      -> int: return mm_to_px(self.y_mm,      dpi)
    def width_px(self, dpi=DEFAULT_DPI)  -> int: return mm_to_px(self.width_mm,  dpi)
    def height_px(self, dpi=DEFAULT_DPI) -> int: return mm_to_px(self.height_mm, dpi)

    def to_dict(self) -> dict:
        return {
            "id": self.id, "type": self.type, "label": self.label,
            "field": self.field, "static_text": self.static_text,
            "condition": self.condition,
            "x_mm": self.x_mm, "y_mm": self.y_mm,
            "width_mm": self.width_mm, "height_mm": self.height_mm,
            "z_index": self.z_index, "visible": self.visible,
            "multiline": self.multiline, "locked": self.locked, "fit": self.fit,
            "source_image": self.source_image,
            "source_gradient": self.source_gradient,
            "style": self.style.to_dict(),
        }

    @classmethod
    def from_dict(cls, d: dict, dpi: int = DEFAULT_DPI) -> "Layer":
        """Aceita tanto mm quanto px (legado). Converte px → mm se necessário."""
        def _mm(key_mm, key_px, default_mm):
            if key_mm in d:
                return float(d[key_mm])
            if key_px in d:
                return px_to_mm(int(d[key_px]), dpi)
            return float(default_mm)

        style_raw = d.get("style", d)   # legado: estilo inline no objeto
        return cls(
            id           = d.get("id",    d.get("label", "layer")),
            type         = d.get("type",  "text"),
            label        = d.get("label", d.get("id", "")),
            field        = d.get("field", ""),
            static_text  = d.get("static_text", ""),
            condition    = d.get("condition", ""),
            x_mm         = _mm("x_mm", "x", 0),
            y_mm         = _mm("y_mm", "y", 0),
            width_mm     = _mm("width_mm",  "width",  63),
            height_mm    = _mm("height_mm", "height", 10),
            z_index      = int(d.get("z_index",  0)),
            visible      = bool(d.get("visible", True)),
            multiline    = bool(d.get("multiline", False)),
            locked       = bool(d.get("locked", False)),
            fit          = d.get("fit", "cover"),
            source_image = d.get("source_image", d.get("background", "")),
            source_gradient = d.get("source_gradient", ""),
            style        = LayerStyle.from_dict(style_raw),
        )


@dataclass
class ResolvedTemplate:
    """Template completamente resolvido (herança já aplicada)."""
    name:       str
    path:       str          = ""    # caminho da pasta do template
    parent:     str          = ""    # nome do template pai (informativo)
    dimensions: CardDimensions = dc_field(default_factory=CardDimensions)
    gradients:  dict[str, GradientDef] = dc_field(default_factory=dict)
    layers:     list[Layer]  = dc_field(default_factory=list)
    back_image: str          = ""    # imagem do verso (relativa a assets/backs/)
    metadata:   dict         = dc_field(default_factory=dict)

    def sorted_layers(self) -> list[Layer]:
        return sorted(self.layers, key=lambda l: l.z_index)

    def layer_by_id(self, lid: str) -> Optional[Layer]:
        return next((l for l in self.layers if l.id == lid), None)

    def to_dict(self) -> dict:
        return {
            "meta": {
                "name":   self.name,
                "parent": self.parent,
            },
            "card": self.dimensions.to_dict(),
            "gradients": {k: v.to_dict() for k, v in self.gradients.items()},
            "layers": [l.to_dict() for l in self.layers],
            "back_image": self.back_image,
        }

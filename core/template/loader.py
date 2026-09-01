"""
Template Loader — descobre, carrega e resolve herança de templates.

Formato suportado (novo):
  templates/
    magic/
      base.json           ← template pai
      magic-m15/
        override.json     ← filho (inherits: "magic/base")
        assets/...

Formato legado (existente):
  templates/
    fang/
      fang.json           ← formato antigo (elements[] com px)
      fang.png

O loader detecta o formato automaticamente e converte legado → novo.
"""
from __future__ import annotations

import json
import copy
from pathlib import Path
from typing import Optional

from .models import (
    ResolvedTemplate, CardDimensions, Layer,
    GradientDef, GradientStop, DEFAULT_DPI, px_to_mm
)
from .merger import deep_merge

# Gradientes padrão MTG (usados quando o template não define os seus)
DEFAULT_GRADIENTS = {
    "white":     {"stops": [["0%","#F5F5DC"],["100%","#E8E6D0"]]},
    "blue":      {"stops": [["0%","#B0C4DE"],["100%","#7B9EB0"]]},
    "black":     {"stops": [["0%","#3A3A3A"],["100%","#1A1A1A"]]},
    "red":       {"stops": [["0%","#E34234"],["100%","#B22222"]]},
    "green":     {"stops": [["0%","#6B8E23"],["100%","#4A7023"]]},
    "gold":      {"stops": [["0%","#D4AF37"],["100%","#B8860B"]]},
    "colorless": {"stops": [["0%","#D0D0D0"],["100%","#A9A9A9"]]},
    "artifact":  {"stops": [["0%","#C8C8C8"],["100%","#909090"]]},
}

ROOT = Path(__file__).resolve().parent.parent.parent   # cardforge/


def templates_root() -> Path:
    p = ROOT / "templates"
    p.mkdir(parents=True, exist_ok=True)
    return p


def list_templates() -> list[str]:
    """
    Retorna lista de nomes de templates disponíveis.
    Um template válido é uma pasta com um .json dentro (qualquer nome).
    """
    root  = templates_root()
    names = []
    for d in sorted(root.rglob("*")):
        if d.is_dir():
            jsons = list(d.glob("*.json"))
            if jsons:
                rel = d.relative_to(root)
                names.append(str(rel).replace("\\", "/"))
    return names


def template_dir(name: str) -> Path:
    return templates_root() / name


def _find_json(folder: Path) -> Optional[Path]:
    """Encontra o primeiro .json na pasta (prioriza override.json, depois base.json)."""
    for preferred in ("override.json", "base.json"):
        p = folder / preferred
        if p.exists():
            return p
    candidates = list(folder.glob("*.json"))
    return candidates[0] if candidates else None


def _load_raw(folder: Path) -> Optional[dict]:
    json_file = _find_json(folder)
    if not json_file:
        return None
    with open(json_file, encoding="utf-8") as f:
        return json.load(f)


def _resolve_inherits(raw: dict, name: str) -> dict:
    """
    Resolve herança recursivamente.
    raw["meta"]["inherits"] contém o caminho relativo ao pai.
    """
    parent_path = (raw.get("meta") or {}).get("inherits") or \
                  raw.get("inherits")   # compat legado
    if not parent_path:
        return raw

    parent_folder = templates_root() / parent_path
    parent_raw    = _load_raw(parent_folder)
    if not parent_raw:
        return raw   # pai não encontrado: usa filho como está

    # Resolve o pai recursivamente (suporta cadeia)
    parent_resolved = _resolve_inherits(parent_raw, parent_path)
    return deep_merge(parent_resolved, raw)


# ── Conversão do formato legado ─────────────────────────────────────────────

def _convert_legacy(raw: dict, folder: Path) -> dict:
    """
    Converte o formato antigo (elements[] com px) para o formato novo.
    Detectado pela presença de "elements" no JSON.
    """
    dpi = DEFAULT_DPI
    dims = CardDimensions.from_dict(raw)

    new_layers = []
    for el in raw.get("elements", []):
        layer: dict = {
            "id":         el.get("id",    el.get("label", "layer")),
            "type":       "text",
            "label":      el.get("label", ""),
            "field":      el.get("field", ""),
            "static_text": el.get("static_text", ""),
            "x_mm":       px_to_mm(int(el.get("x", 0)),     dpi),
            "y_mm":       px_to_mm(int(el.get("y", 0)),     dpi),
            "width_mm":   px_to_mm(int(el.get("width",  100)), dpi),
            "height_mm":  px_to_mm(int(el.get("height",  20)), dpi),
            "z_index":    int(el.get("z_index", 0)),
            "visible":    bool(el.get("visible", True)),
            "multiline":  bool(el.get("multiline", False)),
            "style": {
                "font_family":   el.get("font_family", "Beleren-Bold"),
                "font_size_pt":  round(float(el.get("font_size", 10)) * 0.75, 1),
                "font_weight":   el.get("font_weight", "normal"),
                "font_style":    el.get("font_style",  "normal"),
                "color":         el.get("color",       "#111111"),
                "align":         el.get("text_align",  "left"),
                "line_height_pt": round(float(el.get("line_height", 0)) * 0.75, 1),
            }
        }
        new_layers.append(layer)

    # Adiciona layer de background se houver imagem
    bg = raw.get("background", "")
    if bg:
        new_layers.insert(0, {
            "id":           "background",
            "type":         "background",
            "label":        "Background",
            "field":        "",
            "source_image": bg,
            "x_mm": 0, "y_mm": 0,
            "width_mm":  dims.width_mm,
            "height_mm": dims.height_mm,
            "z_index":   -1,
            "visible":   True,
            "style":     {}
        })

    return {
        "meta": {"name": raw.get("name", folder.name), "inherits": None},
        "card": dims.to_dict(),
        "gradients": DEFAULT_GRADIENTS,
        "layers": new_layers,
        "back_image": "",
    }


# ── API pública ──────────────────────────────────────────────────────────────

def load_template(name: str) -> ResolvedTemplate:
    folder  = template_dir(name)
    raw     = _load_raw(folder)
    if raw is None:
        raise FileNotFoundError(f"Template '{name}' não encontrado em {folder}")

    # Detecta formato legado
    if "elements" in raw:
        raw = _convert_legacy(raw, folder)
    
    # Resolve herança
    resolved_raw = _resolve_inherits(raw, name)
    return _build(resolved_raw, name, str(folder))


def save_template(template: ResolvedTemplate) -> Path:
    folder = template_dir(template.name)
    folder.mkdir(parents=True, exist_ok=True)
    # Salva sempre no novo formato
    out_path = folder / "base.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(template.to_dict(), f, ensure_ascii=False, indent=2)
    return out_path


def create_template(name: str, background_src: Optional[str] = None,
                    parent: Optional[str] = None) -> ResolvedTemplate:
    """Cria um novo template (pasta + JSON)."""
    import shutil
    folder = template_dir(name)
    folder.mkdir(parents=True, exist_ok=True)

    bg_filename = ""
    if background_src:
        src = Path(background_src)
        if src.exists():
            dest = (folder / src.name).resolve()
            if src.resolve() != dest:
                shutil.copy2(str(src), str(dest))
            bg_filename = src.name

    # Template base com posições padrão
    t = _default_template(name, bg_filename, parent)
    save_template(t)
    return t


def set_background(name: str, image_src: str) -> str:
    """Copia imagem de fundo para a pasta do template. Retorna filename."""
    import shutil
    src    = Path(image_src).resolve()
    folder = template_dir(name)
    folder.mkdir(parents=True, exist_ok=True)
    dest   = (folder / src.name).resolve()
    if src != dest:
        shutil.copy2(str(src), str(dest))
    return src.name


def delete_template(name: str) -> None:
    import shutil
    d = template_dir(name)
    if d.exists():
        shutil.rmtree(d)


# ── Construtores internos ────────────────────────────────────────────────────

def _build(raw: dict, name: str, path: str) -> ResolvedTemplate:
    meta      = raw.get("meta", {})
    card_raw  = raw.get("card", raw)          # compat legado
    dims      = CardDimensions.from_dict(card_raw)
    dpi       = dims.dpi

    # Gradientes
    grads: dict[str, GradientDef] = {}
    for gid, gdata in {**DEFAULT_GRADIENTS, **raw.get("gradients", {})}.items():
        stops = [GradientStop.from_raw(s) for s in gdata.get("stops", [])]
        grads[gid] = GradientDef(id=gid, stops=stops)

    # Layers
    layers = [Layer.from_dict(l, dpi) for l in raw.get("layers", [])]

    return ResolvedTemplate(
        name       = meta.get("name", name),
        path       = path,
        parent     = meta.get("inherits", "") or "",
        dimensions = dims,
        gradients  = grads,
        layers     = layers,
        back_image = raw.get("back_image", ""),
        metadata   = meta,
    )


def _default_template(name: str, bg: str, parent: Optional[str]) -> ResolvedTemplate:
    """Template padrão com 9 elementos nas posições clássicas MTG."""
    dims = CardDimensions()
    W, H = dims.width_mm, dims.height_mm

    layers: list[Layer] = []

    if bg:
        layers.append(Layer(
            id="background", type="background", label="Background",
            source_image=bg, x_mm=0, y_mm=0,
            width_mm=W, height_mm=H, z_index=-1,
        ))

    def mm_layer(id_, label, field, x, y, w, h, z=0,
                 size=10, weight="bold", align="left", multi=False, lh=0, color="#111111"):
        return Layer(
            id=id_, type="text", label=label, field=field,
            x_mm=x, y_mm=y, width_mm=w, height_mm=h,
            z_index=z, multiline=multi,
            style=LayerStyle(
                font_family="Beleren-Bold", font_size_pt=size,
                font_weight=weight, align=align,
                color=color, line_height_pt=lh,
            )
        )

    from .models import LayerStyle

    layers += [
        mm_layer("card_name",   "Nome",       "name",       x=3.5, y=3.5, w=46, h=5.5, size=10, weight="bold"),
        mm_layer("mana_cost",   "Custo Mana", "mana_cost",  x=49,  y=3.5, w=11, h=5.5, size=8,  align="right"),
        mm_layer("type_line",   "Tipo",       "type_line",  x=3.5, y=51,  w=56, h=4.5, size=7.5,weight="bold"),
        mm_layer("rules_text",  "Regras",     "rules_text", x=3.5, y=56,  w=56, h=20,  size=7,  multi=True, lh=9.5, z=1),
        mm_layer("flavor_text", "Flavor",     "flavor_text",x=3.5, y=77,  w=56, h=7,   size=6.5,color="#444444", multi=True, lh=8.5, z=1),
        mm_layer("power",       "Poder",      "power",      x=47,  y=79,  w=7,  h=5.5, size=10, align="center"),
        mm_layer("toughness",   "Resistência","toughness",  x=55,  y=79,  w=7,  h=5.5, size=10, align="center"),
        mm_layer("artist",      "Artista",    "artist",     x=3.5, y=84,  w=38, h=3.5, size=5,  color="#333333"),
        mm_layer("set_info",    "Set",        "set_info",   x=48,  y=84,  w=14, h=3.5, size=4.5,color="#333333", align="right"),
    ]

    from .models import GradientDef, GradientStop
    grads = {}
    for gid, gdata in DEFAULT_GRADIENTS.items():
        stops = [GradientStop.from_raw(s) for s in gdata["stops"]]
        grads[gid] = GradientDef(id=gid, stops=stops)

    return ResolvedTemplate(
        name=name, path=str(template_dir(name)),
        parent=parent or "",
        dimensions=dims, gradients=grads,
        layers=layers,
    )

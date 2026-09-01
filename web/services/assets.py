"""Upload e listagem de assets: imagens de arte/fundo e fontes customizadas.

Tudo aqui é escopado pela coleção ativa — a biblioteca de imagens e as fontes
customizadas de uma coleção não aparecem em outra."""
from __future__ import annotations

import re
import uuid
from pathlib import Path

from werkzeug.datastructures import FileStorage

from web.services import collections
from core.render.font_paths import list_available_fonts

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp"}
FONT_EXTS = {".ttf"}


def _safe_stem(name: str) -> str:
    stem = Path(name).stem
    stem = re.sub(r"[^\w\-]+", "_", stem).strip("_") or "arquivo"
    return stem


def save_library_image(file: FileStorage, collection_slug: str) -> str:
    """Salva imagem na biblioteca da coleção. Retorna o nome do arquivo salvo."""
    ext = Path(file.filename or "").suffix.lower()
    if ext not in IMAGE_EXTS:
        raise ValueError(f"Formato de imagem não suportado: {ext or '(sem extensão)'}")
    fname = f"{_safe_stem(file.filename)}-{uuid.uuid4().hex[:6]}{ext}"
    dest = collections.library_dir(collection_slug) / fname
    file.save(dest)
    return fname


def list_library_images(collection_slug: str) -> list[str]:
    lib = collections.library_dir(collection_slug)
    if not lib.exists():
        return []
    return sorted(p.name for p in lib.iterdir() if p.suffix.lower() in IMAGE_EXTS)


def save_font(file: FileStorage, collection_slug: str, template_dir: Path | None = None) -> str:
    """
    Salva uma fonte .ttf.
    Se template_dir for informado, a fonte fica específica daquele template
    (templates/<nome>/fonts/); senão vai para a biblioteca de fontes da coleção.
    Retorna o nome da família (sem extensão) para usar em font_family.
    """
    ext = Path(file.filename or "").suffix.lower()
    if ext not in FONT_EXTS:
        raise ValueError("Envie um arquivo .ttf")
    family = _safe_stem(file.filename)
    target_dir = Path(template_dir) / "fonts" if template_dir else collections.custom_fonts_dir(collection_slug)
    target_dir.mkdir(parents=True, exist_ok=True)
    file.save(target_dir / f"{family}.ttf")
    return family


def all_font_choices(template_dir: Path | None = None) -> list[str]:
    return list_available_fonts(template_dir)

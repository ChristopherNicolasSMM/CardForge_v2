"""Upload e listagem de assets: imagens de arte/fundo e fontes customizadas.

Tudo aqui é escopado pela coleção ativa — a biblioteca de imagens e as fontes
customizadas de uma coleção não aparecem em outra."""
from __future__ import annotations

import re
from pathlib import Path

from werkzeug.datastructures import FileStorage

from web.services import collections
from core.render.font_paths import list_available_fonts
from core.asset_paths import asset_reference_basename, normalize_asset_reference

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
    lib = collections.library_dir(collection_slug)
    stem = _safe_stem(file.filename)
    fname = f"{stem}{ext}"
    number = 2
    while (lib / fname).exists():
        fname = f"{stem}-{number}{ext}"
        number += 1
    dest = lib / fname
    file.save(dest)
    return fname


def list_library_images(collection_slug: str) -> list[str]:
    lib = collections.library_dir(collection_slug)
    if not lib.exists():
        return []
    return sorted(p.name for p in lib.iterdir() if p.suffix.lower() in IMAGE_EXTS)


def library_image_path(collection_slug: str, filename: str) -> Path:
    """Resolve somente nomes de arquivos pertencentes à biblioteca ativa."""
    normalized = normalize_asset_reference(filename)
    if not normalized or "/" in normalized:
        raise ValueError("Nome de imagem inválido.")
    path = collections.library_dir(collection_slug) / normalized
    if path.suffix.lower() not in IMAGE_EXTS:
        raise ValueError("Formato de imagem não suportado.")
    return path


def replace_library_image(file: FileStorage, collection_slug: str, filename: str) -> str:
    """Substitui o conteúdo mantendo o nome/caminho já usado pelos cards."""
    target = library_image_path(collection_slug, filename)
    if not target.exists():
        raise FileNotFoundError(filename)
    source_ext = Path(file.filename or "").suffix.lower()
    if source_ext not in IMAGE_EXTS:
        raise ValueError(f"Formato de imagem não suportado: {source_ext or '(sem extensão)'}")

    # Extensões iguais podem ser copiadas sem perda. Com extensões diferentes,
    # o Pillow converte o conteúdo para o formato do nome antigo, preservando
    # tanto a URL quanto o MIME correto servido pelo Flask.
    if source_ext == target.suffix.lower() or {source_ext, target.suffix.lower()} <= {".jpg", ".jpeg"}:
        file.save(target)
    else:
        from PIL import Image
        with Image.open(file.stream) as image:
            fmt = {".jpg": "JPEG", ".jpeg": "JPEG", ".png": "PNG", ".webp": "WEBP"}[target.suffix.lower()]
            if fmt == "JPEG" and image.mode not in ("RGB", "L"):
                background = Image.new("RGB", image.size, "white")
                if image.mode == "RGBA":
                    background.paste(image, mask=image.getchannel("A"))
                else:
                    background.paste(image.convert("RGB"))
                image = background
            image.save(target, fmt)
    return target.name


def image_reference_matches(value: object, filename: str) -> bool:
    """Reconhece o nome canônico e referências legadas library/imgs com barras mistas."""
    normalized = normalize_asset_reference(value)
    if not normalized:
        return False
    if normalized == filename:
        return True
    parts = normalized.split("/")
    return asset_reference_basename(normalized) == filename and any(
        part.lower() in {"library", "imgs"} for part in parts[:-1]
    )


def find_image_references(dataset: dict, filename: str) -> list[dict]:
    matches = []
    for row_index, row in enumerate(dataset.get("rows") or []):
        for field, value in row.items():
            if image_reference_matches(value, filename):
                matches.append({"row": row_index, "field": field})
    return matches


def rename_image_references(dataset: dict, old_name: str, new_name: str) -> int:
    changed = 0
    for row in dataset.get("rows") or []:
        for field, value in list(row.items()):
            if image_reference_matches(value, old_name):
                row[field] = new_name
                changed += 1
    return changed


def rename_library_image(collection_slug: str, old_name: str, requested_name: str) -> str:
    source = library_image_path(collection_slug, old_name)
    if not source.exists():
        raise FileNotFoundError(old_name)
    requested = Path(requested_name.strip()).name
    stem = _safe_stem(requested)
    requested_ext = Path(requested).suffix.lower()
    if requested_ext and requested_ext != source.suffix.lower():
        raise ValueError("Para renomear, mantenha a extensão original da imagem.")
    new_name = f"{stem}{source.suffix.lower()}"
    target = library_image_path(collection_slug, new_name)
    if target != source and target.exists():
        raise ValueError("Já existe uma imagem com esse nome.")
    source.rename(target)
    return new_name


def delete_library_image(collection_slug: str, filename: str) -> None:
    path = library_image_path(collection_slug, filename)
    if not path.exists():
        raise FileNotFoundError(filename)
    path.unlink()


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
